# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Changed
- `cluster_embeddings_3d.py` — ongoing updates to 3-D embedding cluster visualisation

---

## [2026-04-05]

### Added
- `sdk/tutorial/litellm/level_100/response_api/litellm_response_api_get_started.ipynb`
  — Getting-started tutorial for the OpenAI Responses API via LiteLLM:
  structured output with `text.format.json_schema`, `web_search` tool,
  `tool_choice`, and `max_output_tokens`

---

## [2026-04-04]

### Added
- `sdk/tutorial/litellm/level_200/litellm_response_api_tool_calls.ipynb`
  — LangGraph agent using LiteLLM's Responses API (`litellm.responses()`)
  for tool calling; demonstrates `function_call` / `function_call_output`
  output items and LangGraph state accumulation via `input_items`

### Changed
- Refactored tool-calling tutorial from Chat Completion API (`litellm.completion()`)
  to Responses API (`litellm.responses()`):
  - Tool definition updated to flat `{"type": "function", "name": ...}` format
  - Loop logic rewritten to consume `function_call` output items and append
    `function_call_output` items back to `input_items`
  - LangGraph state updated to carry `input_items: list` instead of `messages`

---

## [2026-03-22]

### Added
- `sdk/tutorial/litellm/level_200/litellm_tool_calls_intelligent_filtering.ipynb`
  — LangGraph agent that reranks web-search results before passing them to
  the LLM, using shared reranking utilities from the `lib` submodule

### Changed
- `lib` submodule bumped twice to pull in reranking package and its
  updated requirements
- Cleaned up `litellm_tool_calls_intelligent_filtering.ipynb`: removed unused
  helpers (`messages_prompt`, `extract_tool_call_messages`) and two trailing
  empty cells; re-executed end-to-end via `nbconvert`

---

## [2026-03-15]

### Changed
- `sdk/tutorial/litellm/level_100/litellm_get_started.ipynb`
  — Expanded tool-call section; added `tool_call_flow.png` diagram illustrating
  the request/response cycle

---

## [2026-03-07]

### Added
- `cluster_embeddings_3d.py` — interactive 3-D scatter plot for visualising
  text-embedding clusters (PCA / t-SNE reduction)
- `sdk/tutorial/litellm/level_100/embedding_basics/L2-student.ipynb`
  — DeepLearning.AI L2 embedding basics tutorial adapted for LiteLLM
- `requirements_clustering.txt` — dependencies for clustering and 3-D visualisation

### Changed
- `sdk/tutorial/litellm/level_100/litellm_get_started.ipynb` — expanded with
  additional tool-call and embedding examples
- `sdk/tutorial/litellm/level_100/embedding_basics/search_visualise_embeddings.ipynb`
  — updated search and visualisation examples
- `lib` submodule updated

---

## [2026-01-04]

### Changed
- `sdk/tutorial/litellm/level_100/embedding_basics/chunk_and_validate.ipynb`
  — refined chunking and validation examples
- `sdk/tutorial/litellm/level_100/embedding_basics/search_visualise_embeddings.ipynb`
  — updated embedding search and visualisation examples
- `lib` submodule updated

---

## [2025-12-28]

### Added
- `sdk/tutorial/langgraph/level_200/langgraph_tool_litellm.ipynb`
  — LangGraph agent with LiteLLM tool calling (level 200)
- `sdk/tutorial/litellm/level_100/embedding_basics/chunk_and_validate.ipynb`
  — chunking strategies and schema validation for embedding pipelines

### Changed
- Various LangGraph level-100 and level-200 notebooks refined and re-executed

---

## [2025-12-21 – 2025-12-27]

### Added
- `sdk/tutorial/langgraph/level_100/` — LangGraph fundamentals series:
  - `01_langgraph_toy_graph.ipynb` — minimal graph construction
  - `02_langgraph_basics.ipynb` — nodes, edges, and state
  - `03_langgraph_basic_chatbot.ipynb` — stateful chatbot with memory
  - `04_langgraph_call_tool.ipynb` — tool-calling node
  - `05_langgraph_essey_writer.ipynb` — multi-step essay-writer agent
- `sdk/tutorial/langgraph/level_200/travel_customer_support/`
  — Travel customer-support agent and regulatory email processing agent

---

## [2025-10-06]

### Added
- LangGraph tutorial scaffolding based on Real Python LangGraph guide

---

## [2025-07-28]

### Added
- Initial project structure: `sdk/`, `lib` submodule, `requirements*.txt`
