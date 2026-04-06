// AUTO-GENERATED — do not edit


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


// --- Rules ---

sourcefile : packageclause ";" (importdecl ";")* (topleveldecl ";")*

string_lit : RAW_STRING_LIT | INTERPRETED_STRING_LIT

type : typename (typeargs)?
     | typelit
     | "(" type ")"

typename : IDENTIFIER
     | qualifiedident

typeargs : "[" typelist (",")? "]"

typelist : type ("," type)*

typelit : arraytype
     | structtype
     | pointertype
     | functiontype
     | interfacetype
     | slicetype
     | maptype
     | channeltype

arraytype : "[" arraylength "]" elementtype

arraylength : expression

elementtype : type

slicetype : "[" "]" elementtype

structtype : STRUCT "{" (fielddecl SEMI)* fielddecl? "}"

fielddecl : (identifierlist type
     | embeddedfield) (tag)?

embeddedfield : ("*")? typename (typeargs)?

tag : string_lit

pointertype : "*" basetype

basetype : type

functiontype : FUNC signature

signature : parameters (result)?

result : parameters
     | type

parameters : "(" (parameterlist (",")?)? ")"

parameterlist : parameterdecl ("," parameterdecl)*

parameterdecl : (identifierlist)? ("...")? type

interfacetype : INTERFACE "{" (interfaceelem SEMI)* interfaceelem? "}"

interfaceelem : methodelem
     | typeelem

methodelem : methodname signature

methodname : IDENTIFIER

typeelem : typeterm ("|" typeterm)*

typeterm : type
     | underlyingtype

underlyingtype : "~" type

maptype : MAP "[" keytype "]" elementtype

keytype : type

channeltype : (CHAN
     | CHAN "<-"
     | "<-" CHAN) elementtype

block : "{" statementlist "}"

statementlist : (statement SEMI)* statement?

declaration : constdecl
     | typedecl
     | vardecl

topleveldecl : declaration
     | functiondecl
     | methoddecl

constdecl : CONST (constspec | "(" (constspec SEMI)* constspec? ")")

constspec : identifierlist ((type)? "=" expressionlist)?

identifierlist : IDENTIFIER ("," IDENTIFIER)*

expressionlist : expression ("," expression)*

typedecl : TYPE (typespec | "(" (typespec SEMI)* typespec? ")")

typespec : aliasdecl
     | typedef

aliasdecl : IDENTIFIER (typeparameters)? "=" type

typedef : IDENTIFIER (typeparameters)? type

typeparameters : "[" typeparamlist (",")? "]"

typeparamlist : typeparamdecl ("," typeparamdecl)*

typeparamdecl : identifierlist typeconstraint

typeconstraint : typeelem

vardecl : VAR (varspec | "(" (varspec SEMI)* varspec? ")")

varspec : identifierlist (type ("=" expressionlist)?
     | "=" expressionlist)

shortvardecl : identifierlist ":=" expressionlist

functiondecl : FUNC functionname (typeparameters)? signature (functionbody)?

functionname : IDENTIFIER

functionbody : block

methoddecl : FUNC receiver methodname signature (functionbody)?

receiver : parameters

operand : literal
     | operandname (typeargs)?
     | "(" expression ")"

literal : basiclit
     | compositelit
     | functionlit

basiclit : INT_LIT
     | FLOAT_LIT
     | IMAGINARY_LIT
     | RUNE_LIT
     | string_lit

operandname : IDENTIFIER
     | qualifiedident

qualifiedident : packagename "." IDENTIFIER

compositelit : literaltype literalvalue

literaltype : structtype
     | arraytype
     | "[" "..." "]" elementtype
     | slicetype
     | maptype
     | typename (typeargs)?

literalvalue : "{" (elementlist (",")?)? "}"

elementlist : keyedelement ("," keyedelement)*

keyedelement : (key ":")? element

key : fieldname
     | expression
     | literalvalue

fieldname : IDENTIFIER

element : expression
     | literalvalue

functionlit : FUNC signature functionbody

primaryexpr : operand
     | conversion
     | methodexpr
     | primaryexpr selector
     | primaryexpr index
     | primaryexpr slice
     | primaryexpr typeassertion
     | primaryexpr arguments

selector : "." IDENTIFIER

index : "[" expression (",")? "]"

slice : "[" (expression)? ":" (expression)? "]"
     | "[" (expression)? ":" expression ":" expression "]"

typeassertion : "." "(" type ")"

arguments : "(" ((expressionlist
     | type ("," expressionlist)?) ("...")? (",")?)? ")"

methodexpr : receivertype "." methodname

receivertype : type

expression : unaryexpr
     | expression binary_op expression

unaryexpr : primaryexpr
     | unary_op unaryexpr

binary_op : "||"
     | "&&"
     | rel_op
     | add_op
     | mul_op

rel_op : "=="
     | "!="
     | "<"
     | "<="
     | ">"
     | ">="

add_op : "+"
     | "-"
     | "|"
     | "^"

mul_op : "*"
     | "/"
     | "%"
     | "<<"
     | ">>"
     | "&"
     | "&^"

unary_op : "+"
     | "-"
     | "!"
     | "^"
     | "*"
     | "&"
     | "<-"

conversion : type "(" expression (",")? ")"

statement : declaration
     | labeledstmt
     | simplestmt
     | gostmt
     | returnstmt
     | breakstmt
     | continuestmt
     | gotostmt
     | fallthroughstmt
     | block
     | ifstmt
     | switchstmt
     | selectstmt
     | forstmt
     | deferstmt

simplestmt : emptystmt
     | expressionstmt
     | sendstmt
     | incdecstmt
     | assignment
     | shortvardecl

emptystmt :

labeledstmt : label ":" statement

label : IDENTIFIER

expressionstmt : expression

sendstmt : channel "<-" expression

channel : expression

incdecstmt : expression ("++"
     | "--")

assignment : expressionlist assign_op expressionlist

assign_op : (add_op
     | mul_op)? "="

ifstmt : IF (simplestmt ";")? expression block (ELSE (ifstmt
     | block))?

switchstmt : exprswitchstmt
     | typeswitchstmt

exprswitchstmt : SWITCH (simplestmt ";")? (expression)? "{" (exprcaseclause)* "}"

exprcaseclause : exprswitchcase ":" statementlist

exprswitchcase : CASE expressionlist
     | DEFAULT

typeswitchstmt : SWITCH (simplestmt ";")? typeswitchguard "{" (typecaseclause)* "}"

typeswitchguard : (IDENTIFIER ":=")? primaryexpr "." "(" TYPE ")"

typecaseclause : typeswitchcase ":" statementlist

typeswitchcase : CASE typelist
     | DEFAULT

forstmt : FOR (condition
     | forclause
     | rangeclause)? block

condition : expression

forclause : (initstmt)? ";" (condition)? ";" (poststmt)?

initstmt : simplestmt

poststmt : simplestmt

rangeclause : (expressionlist "="
     | identifierlist ":=")? RANGE expression

gostmt : GO expression

selectstmt : SELECT "{" (commclause)* "}"

commclause : commcase ":" statementlist

commcase : CASE (sendstmt
     | recvstmt)
     | DEFAULT

recvstmt : (expressionlist "="
     | identifierlist ":=")? recvexpr

recvexpr : expression

returnstmt : RETURN (expressionlist)?

breakstmt : BREAK (label)?

continuestmt : CONTINUE (label)?

gotostmt : GOTO label

fallthroughstmt : FALLTHROUGH

deferstmt : DEFER expression

packageclause : PACKAGE packagename

packagename : IDENTIFIER

importdecl : IMPORT (importspec | "(" (importspec SEMI)* importspec? ")")

importspec : ("."
     | packagename)? importpath

importpath : string_lit

basic_lit : INT_LIT | FLOAT_LIT | IMAGINARY_LIT | RUNE_LIT | string_lit
