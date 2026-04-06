#!/usr/bin/env python3
"""
Go EBNF vs Official Parser Comparison Pipeline

Steps:
  1. Parse go.bnf with the meta-grammar → EBNF parse tree
  2. Translate EBNF productions → Lark grammar for Go source
  3. Pre-process Go source files (semicolon insertion)
  4. Parse a corpus (stdlib + optional GitHub) with both:
       a. gofmt -e (official parser, ground truth)
       b. Our Lark grammar
  5. Report success/failure rates and gap analysis
"""

import re, sys, subprocess, random, json
from pathlib import Path
from collections import defaultdict
from lark import Lark, UnexpectedInput, Tree, Token

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
GOROOT   = subprocess.check_output(["go", "env", "GOROOT"], text=True).strip()
BNF_PATH = Path(__file__).parent / "go.bnf"
OUT_DIR  = Path(__file__).parent
LARK_GRAMMAR_PATH = OUT_DIR / "go_lark.g"

# ---------------------------------------------------------------------------
# PART 1 — Parse go.bnf with the meta-grammar
# ---------------------------------------------------------------------------
META_GRAMMAR = r"""
start       : production*
production  : NAME "=" expression "."
            | NAME "=" "."
expression  : term ("|" term)*
term        : factor+
factor      : DQSTRING ELLIPSIS DQSTRING   -> range_tok
            | DQSTRING                     -> terminal
            | BQSTRING                     -> bterminal
            | PROSE                        -> prose
            | NAME                         -> nonterminal
            | "(" expression ")"           -> group
            | "[" expression "]"           -> option
            | "{" expression "}"           -> repetition
NAME     : /[a-zA-Z_][a-zA-Z0-9_]*/
DQSTRING : /"[^"]*"/
BQSTRING : /`[^`]*`/
ELLIPSIS : /\u2026/
PROSE    : /\/\*(?:[^*]|\*(?!\/))*\*\//
%ignore /[ \t\r\n]+/
%ignore /#[^\n]*/
"""
meta = Lark(META_GRAMMAR, parser="earley")
bnf_tree = meta.parse(BNF_PATH.read_text(encoding="utf-8"))
print(f"[1] Parsed go.bnf — {len(bnf_tree.children)} productions")

# ---------------------------------------------------------------------------
# PART 2 — Translate EBNF → Lark grammar
# ---------------------------------------------------------------------------

# Productions whose lexical structure is captured by manual terminal regex.
# When these names appear as references in syntactic rules they are
# rewritten to their TERMINAL counterpart.
TERM_MAP = {
    "identifier":             "IDENTIFIER",
    "int_lit":                "INT_LIT",
    "float_lit":              "FLOAT_LIT",
    "imaginary_lit":          "IMAGINARY_LIT",
    "rune_lit":               "RUNE_LIT",
    "raw_string_lit":         "RAW_STRING_LIT",
    "interpreted_string_lit": "INTERPRETED_STRING_LIT",
}

# Productions that are entirely sub-rules of the above terminals
# → skip them (don't emit Lark rules for them).
SKIP_PRODS = set(TERM_MAP) | {
    "newline", "unicode_char", "unicode_letter", "unicode_digit",
    "letter", "decimal_digit", "binary_digit", "octal_digit", "hex_digit",
    "decimal_digits", "binary_digits", "octal_digits", "hex_digits",
    "decimal_lit", "binary_lit", "octal_lit", "hex_lit",
    "decimal_float_lit", "hex_float_lit", "decimal_exponent",
    "hex_mantissa", "hex_exponent",
    "unicode_value", "byte_value", "octal_byte_value", "hex_byte_value",
    "little_u_value", "big_u_value", "escaped_char",
}

def _range_regex(lo: str, hi: str) -> str:
    """'a' … 'z' → /[a-z]/ (Lark inline regex)."""
    def esc(c):
        return "\\" + c if c in r"\]^-/" else c
    return f"/[{esc(lo)}-{esc(hi)}]/"

_KW_TERMINAL = {k: k.upper() for k in {
    'break','case','chan','const','continue','default','defer',
    'else','fallthrough','for','func','go','goto','if','import',
    'interface','map','package','range','return','select','struct',
    'switch','type','var',
}}

def _factor(f) -> str | None:
    d = f.data
    if d == "nonterminal":
        name = str(f.children[0])
        return TERM_MAP.get(name, name.lower())
    elif d == "terminal":
        inner = str(f.children[0])[1:-1]      # string without surrounding quotes
        if inner in _KW_TERMINAL:
            return _KW_TERMINAL[inner]         # "type" → TYPE, "for" → FOR, …
        return str(f.children[0])             # keep quoted for operators / punctuation
    elif d == "bterminal":
        inner = str(f.children[0])[1:-1]           # strip backticks
        inner = inner.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{inner}"'
    elif d == "range_tok":
        lo = str(f.children[0])[1:-1]
        hi = str(f.children[2])[1:-1]
        return _range_regex(lo, hi)
    elif d == "prose":
        return None                  # prose-defined terminal — skip
    elif d == "group":
        inner = _expr(f.children[0])
        return f"({inner})" if inner else None
    elif d == "option":
        inner = _expr(f.children[0])
        return f"({inner})?" if inner else None
    elif d == "repetition":
        inner = _expr(f.children[0])
        return f"({inner})*" if inner else None
    return None

def _term(t) -> str | None:
    parts = [_factor(f) for f in t.children if isinstance(f, Tree)]
    parts = [p for p in parts if p]
    return " ".join(parts) if parts else None

def _expr(e) -> str | None:
    alts = [_term(t) for t in e.children if isinstance(t, Tree)]
    alts = [a for a in alts if a]
    if not alts:
        return None
    return "\n     | ".join(alts)

# Collect auto-translated rules
auto_rules: dict[str, str | None] = {}   # lark_name → body (None = empty rule)
for prod in bnf_tree.children:
    if not isinstance(prod, Tree):
        continue
    ebnf_name = str(prod.children[0])
    lname = ebnf_name.lower()
    if lname in SKIP_PRODS:
        continue
    if len(prod.children) == 1:           # Name = .  (empty production)
        auto_rules[lname] = None
        continue
    body = _expr(prod.children[1])
    auto_rules[lname] = body

print(f"[2] Translated {len(auto_rules)} EBNF productions → Lark rules")

# ---------------------------------------------------------------------------
# PART 3 — Assemble full Lark grammar
# ---------------------------------------------------------------------------

FIXED_HEADER = r"""
// ===================================================================
// Go Source Grammar — auto-generated from go.bnf
// ===================================================================

// --- Whitespace & comments ---
BLOCK_COMMENT : /\/\*(?:[^*]|\*(?!\/))*\*\//
LINE_COMMENT  : /\/\/[^\n]*/
WS            : /[ \t\r\n]+/

// --- Semicolons (inserted by pre-processor) ---
SEMI : ";"

// --- Keywords (priority 3): lookahead prevents matching inside identifiers ---
BREAK.3       : /break(?![a-zA-Z0-9_])/
CASE.3        : /case(?![a-zA-Z0-9_])/
CHAN.3        : /chan(?![a-zA-Z0-9_])/
CONST.3       : /const(?![a-zA-Z0-9_])/
CONTINUE.3    : /continue(?![a-zA-Z0-9_])/
DEFAULT.3     : /default(?![a-zA-Z0-9_])/
DEFER.3       : /defer(?![a-zA-Z0-9_])/
ELSE.3        : /else(?![a-zA-Z0-9_])/
FALLTHROUGH.3 : /fallthrough(?![a-zA-Z0-9_])/
FOR.3         : /for(?![a-zA-Z0-9_])/
FUNC.3        : /func(?![a-zA-Z0-9_])/
GO.3          : /go(?![a-zA-Z0-9_])/
GOTO.3        : /goto(?![a-zA-Z0-9_])/
IF.3          : /if(?![a-zA-Z0-9_])/
IMPORT.3      : /import(?![a-zA-Z0-9_])/
INTERFACE.3   : /interface(?![a-zA-Z0-9_])/
MAP.3         : /map(?![a-zA-Z0-9_])/
PACKAGE.3     : /package(?![a-zA-Z0-9_])/
RANGE.3       : /range(?![a-zA-Z0-9_])/
RETURN.3      : /return(?![a-zA-Z0-9_])/
SELECT.3      : /select(?![a-zA-Z0-9_])/
STRUCT.3      : /struct(?![a-zA-Z0-9_])/
SWITCH.3      : /switch(?![a-zA-Z0-9_])/
TYPE.3        : /type(?![a-zA-Z0-9_])/
VAR.3         : /var(?![a-zA-Z0-9_])/

// --- Identifier (priority 0 — keywords win on equal-length match) ---
IDENTIFIER    : /[a-zA-Z_][a-zA-Z0-9_]*/

// --- Literals (most-specific first) ---
IMAGINARY_LIT.5 : /(?:0[xX][0-9a-fA-F][0-9a-fA-F_]*(?:\.[0-9a-fA-F_]*)?(?:[pP][+-]?[0-9][0-9_]*)?|\d[0-9_]*\.?\d*(?:[eE][+-]?\d[0-9_]*)?)i/
FLOAT_LIT.4     : /0[xX][0-9a-fA-F][0-9a-fA-F_]*(?:\.[0-9a-fA-F_]*)?[pP][+-]?[0-9][0-9_]*|\d[0-9_]*\.\d*(?:[eE][+-]?\d[0-9_]*)?|\d[0-9_]*[eE][+-]?\d[0-9_]*|\.\d[0-9_]*(?:[eE][+-]?\d[0-9_]*)?/
INT_LIT.3       : /0[xX][0-9a-fA-F][0-9a-fA-F_]+|0[bB][01][01_]*|0[oO]?[0-7][0-7_]*|[1-9][0-9_]*|0/
RAW_STRING_LIT  : /`[^`]*`/
INTERPRETED_STRING_LIT : /"(?:[^"\\]|\\.)*"/
RUNE_LIT               : /'(?:[^'\\\n]|\\(?:[abfnrtv\\'"nrt]|[0-7]{3}|x[0-9a-fA-F]{2}|u[0-9a-fA-F]{4}|U[0-9a-fA-F]{8}))'/

%ignore BLOCK_COMMENT
%ignore LINE_COMMENT
%ignore WS
"""

# Manual rule overrides (replace or add to auto-translated rules)
#
# Go spec §Semicolons: "a semicolon may be omitted before a closing ) or }"
# The EBNF writes  { X ";" }  but real Go allows the last X to omit its ";".
# Fix: (X ";")* X?  — final item's semicolon is optional.
MANUAL_RULES = {
    # Literals
    "string_lit": "RAW_STRING_LIT | INTERPRETED_STRING_LIT",
    "basic_lit":  "INT_LIT | FLOAT_LIT | IMAGINARY_LIT | RUNE_LIT | string_lit",

    # Trailing-semicolon-optional patterns (Go spec §Semicolons)
    "statementlist":  "(statement SEMI)* statement?",
    "structtype":     'STRUCT "{" (fielddecl SEMI)* fielddecl? "}"',
    "interfacetype":  'INTERFACE "{" (interfaceelem SEMI)* interfaceelem? "}"',
    "constdecl":      'CONST (constspec | "(" (constspec SEMI)* constspec? ")")',
    "vardecl":        'VAR (varspec | "(" (varspec SEMI)* varspec? ")")',
    "typedecl":       'TYPE (typespec | "(" (typespec SEMI)* typespec? ")")',
    "importdecl":     'IMPORT (importspec | "(" (importspec SEMI)* importspec? ")")',
}
auto_rules.update(MANUAL_RULES)

def _emit_rule(name: str, body: str | None) -> str:
    if body is None:
        return f"{name} :\n"
    return f"{name} : {body}\n"

grammar_parts = ["// AUTO-GENERATED — do not edit\n", FIXED_HEADER, "\n// --- Rules ---\n"]
# Emit 'sourcefile' first (start symbol)
if "sourcefile" in auto_rules:
    grammar_parts.append(_emit_rule("sourcefile", auto_rules["sourcefile"]))
for name, body in auto_rules.items():
    if name == "sourcefile":
        continue
    grammar_parts.append(_emit_rule(name, body))

lark_grammar = "\n".join(grammar_parts)
LARK_GRAMMAR_PATH.write_text(lark_grammar, encoding="utf-8")
print(f"[3] Wrote Lark grammar → {LARK_GRAMMAR_PATH}")

# ---------------------------------------------------------------------------
# PART 4 — Semicolon insertion (Go spec §Semicolons)
# ---------------------------------------------------------------------------
_TOK_RE = re.compile(
    r"(?P<BLOCK_COMMENT>/\*(?:[^*]|\*(?!/))*\*/)"
    r"|(?P<LINE_COMMENT>//[^\n]*)"
    r"|(?P<RAW_STRING>`[^`]*`)"
    r"|(?P<STRING>\"(?:[^\"\\]|\\.)*\")"
    r"|(?P<RUNE>'(?:[^'\\]|\\.)*')"
    r"|(?P<IMAGINARY>(?:\d[\d_]*\.?[\d_]*(?:[eE][+-]?\d[\d_]*)?|\.\d[\d_]*)i)"
    r"|(?P<FLOAT>\d[\d_]*\.[\d_]*(?:[eE][+-]?\d[\d_]*)?|\d[\d_]*[eE][+-]?\d[\d_]*|\.\d[\d_]*(?:[eE][+-]?\d[\d_]*)?)"
    r"|(?P<INT>0[xX][0-9a-fA-F][\w]*|0[bB][01][\w]*|0[oO]?[0-7][\w]*|\d[\d_]*)"
    r"|(?P<INC>\+\+)"
    r"|(?P<DEC>--)"
    r"|(?P<RPAREN>\))"
    r"|(?P<RBRACKET>\])"
    r"|(?P<RBRACE>\})"
    r"|(?P<IDENT>[a-zA-Z_]\w*)"
    r"|(?P<NEWLINE>\n)"
    r"|(?P<OTHER>.)",
    re.DOTALL,
)

_SEMI_AFTER = frozenset({
    "IDENT", "INT", "FLOAT", "IMAGINARY", "STRING", "RAW_STRING", "RUNE",
    "INC", "DEC", "RPAREN", "RBRACKET", "RBRACE",
})
_SEMI_KWORDS = frozenset({"break", "continue", "fallthrough", "return"})

def insert_semicolons(src: str) -> str:
    """Insert ';' after line-final tokens per Go spec §Semicolons."""
    out: list[str] = []
    last_kind: str | None = None
    last_text: str = ""

    for m in _TOK_RE.finditer(src):
        kind = m.lastgroup
        text = m.group()

        if kind == "NEWLINE":
            need = (
                last_kind in _SEMI_AFTER
                or (last_kind == "IDENT" and last_text in _SEMI_KWORDS)
            )
            if need:
                out.append(";")
            out.append("\n")
            last_kind = None
            last_text = ""
        elif kind in ("BLOCK_COMMENT", "LINE_COMMENT"):
            out.append(text)
            # Don't update last_kind — comments are transparent
        else:
            out.append(text)
            if kind != "OTHER" or text.strip():
                last_kind = kind
                last_text = text

    return "".join(out)

# ---------------------------------------------------------------------------
# PART 5 — Build Lark parser
# ---------------------------------------------------------------------------
print("[5] Compiling Lark grammar (Earley) …", end=" ", flush=True)
try:
    go_parser = Lark(lark_grammar, parser="earley", start="sourcefile",
                     lexer="standard", ambiguity="resolve")
    print("OK")
except Exception as exc:
    print(f"FAILED: {exc}")
    sys.exit(1)

def lark_parse(src: str) -> tuple[bool, str]:
    """Returns (success, error_message)."""
    try:
        go_parser.parse(insert_semicolons(src))
        return True, ""
    except UnexpectedInput as e:
        return False, str(e).splitlines()[0]
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"

def gofmt_parse(path: Path) -> bool:
    """Returns True if gofmt -e accepts the file."""
    r = subprocess.run(
        ["gofmt", "-e", str(path)],
        capture_output=True, text=True
    )
    return r.returncode == 0 and not r.stderr

# ---------------------------------------------------------------------------
# PART 6 — Corpus: stdlib sample
# ---------------------------------------------------------------------------
stdlib_root = Path(GOROOT) / "src"
all_go = [
    p for p in stdlib_root.rglob("*.go")
    if "_test.go" not in p.name
    and "testdata" not in str(p)
    and "vendor" not in str(p)
]
random.seed(42)
sample = random.sample(all_go, min(300, len(all_go)))
print(f"[6] Corpus: {len(sample)} stdlib files sampled from {len(all_go)} total")

# ---------------------------------------------------------------------------
# PART 7 — Compare
# ---------------------------------------------------------------------------
results = []
failure_patterns: dict[str, int] = defaultdict(int)
rule_failures: dict[str, int] = defaultdict(int)

print(f"[7] Parsing corpus …")
for i, path in enumerate(sample, 1):
    src = path.read_text(encoding="utf-8", errors="replace")
    gofmt_ok   = gofmt_parse(path)
    lark_ok, err = lark_parse(src)
    results.append({
        "file":     str(path.relative_to(stdlib_root)),
        "gofmt":    gofmt_ok,
        "lark":     lark_ok,
        "error":    err,
        "bytes":    len(src),
    })
    if i % 50 == 0:
        print(f"  {i}/{len(sample)} …")

# ---------------------------------------------------------------------------
# PART 8 — Report
# ---------------------------------------------------------------------------
total        = len(results)
gofmt_pass   = sum(1 for r in results if r["gofmt"])
lark_pass    = sum(1 for r in results if r["lark"])
both_pass    = sum(1 for r in results if r["gofmt"] and r["lark"])
false_neg    = [r for r in results if r["gofmt"] and not r["lark"]]   # gofmt OK, Lark FAIL
false_pos    = [r for r in results if not r["gofmt"] and r["lark"]]   # gofmt FAIL, Lark OK

print("\n" + "="*60)
print("RESULTS")
print("="*60)
print(f"  Total files          : {total}")
print(f"  gofmt pass           : {gofmt_pass} ({100*gofmt_pass/total:.1f}%)")
print(f"  Lark  pass           : {lark_pass}  ({100*lark_pass/total:.1f}%)")
print(f"  Both  pass           : {both_pass}  ({100*both_pass/total:.1f}%)")
print(f"  False negatives      : {len(false_neg)} (gofmt OK, Lark FAIL)")
print(f"  False positives      : {len(false_pos)} (gofmt FAIL, Lark OK)")

# Aggregate error messages
for r in false_neg:
    # Keep token type, strip actual value and line/col numbers
    msg = re.sub(r"line \d+, col(?:umn)? \d+", "line X, col Y", r["error"])
    # Keep Token('TYPE', 'value') → Token('TYPE')
    msg = re.sub(r"Token\('([^']+)',\s*'[^']*'\)", r"Token('\1')", msg)
    msg = re.sub(r"'[^']{20,}'", "'...'", msg)  # only truncate long literals
    failure_patterns[msg[:120]] += 1

print(f"\n  Top failure patterns ({len(failure_patterns)} distinct):")
for msg, cnt in sorted(failure_patterns.items(), key=lambda x: -x[1])[:15]:
    print(f"    [{cnt:4d}x]  {msg}")

# Save detailed results
out_json = OUT_DIR / "comparison_results.json"
out_json.write_text(json.dumps({
    "summary": {
        "total": total, "gofmt_pass": gofmt_pass, "lark_pass": lark_pass,
        "both_pass": both_pass, "false_negatives": len(false_neg),
        "false_positives": len(false_pos),
    },
    "false_negatives": [{"file": r["file"], "error": r["error"]} for r in false_neg[:50]],
    "failure_patterns": dict(sorted(failure_patterns.items(), key=lambda x: -x[1])),
}, indent=2), encoding="utf-8")
print(f"\n  Full results saved → {out_json}")
