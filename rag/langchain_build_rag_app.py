"""
RAG test application as per https://python.langchain.com/docs/tutorials/rag/
"""
import getpass
import logging
import os
import sys
from typing import (
    List,
)

import bs4
from langchain import hub
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.documents import Document
from langgraph.graph import START, StateGraph
from typing_extensions import TypedDict
from langchain.chat_models import init_chat_model
from langchain_openai import OpenAIEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter


logger = logging.getLogger(__name__)
if not os.environ.get("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = getpass.getpass("Enter API key for OpenAI: ")


llm = init_chat_model("gpt-4o-mini", model_provider="openai")
embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
vector_store = InMemoryVectorStore(embeddings)
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,  # chunk size (characters)
    chunk_overlap=200,  # chunk overlap (characters)
    add_start_index=True,  # track index in original document
)


def get_document():
    # Load and chunk contents of the blog
    loader = WebBaseLoader(
        web_paths=("https://lilianweng.github.io/posts/2023-06-23-agent/",),
        bs_kwargs=dict(
            parse_only=bs4.SoupStrainer(
                class_=("post-content", "post-title", "post-header")
            )
        ),
    )
    docs = loader.load()
    assert len(docs) == 1

    logging.info(f"Total characters: {len(docs[0].page_content)}")
    print(docs[0].page_content[:500])

    return docs


# Define state for application
class State(TypedDict):
    question: str
    context: List[Document]
    answer: str


def chunk(docs):
    """
    Split long documents into chunks so that each chunk is less than the tokens
    that a model can handle.
    """
    chunks = text_splitter.split_documents(docs)
    return chunks


def vectorize(documents):
    document_ids = vector_store.add_documents(documents=documents)
    return document_ids


def get_prompt(query: str, context):
    """Generate prompt to send to LLM.
    Args:
        query: user query
        context: RAG context (retrieved context documents)
    Returns: prompt
    """
    # N.B. for non-US LangSmith endpoints, you may need to specify
    # api_url="https://api.smith.langchain.com" in hub.pull.
    prompt_template = hub.pull("rlm/rag-prompt")
    prompt = prompt_template.invoke({
        "question": query,
        "context": context
    })
    return prompt


# Define application steps
def retrieve(state: State):
    """Retrieve documents to augment the user query.
    """
    retrieved = vector_store.similarity_search(state["question"])
    return {"context": retrieved}


def generate(state: State):
    """Generate the answer from LLM"""
    context = "\n\n".join(doc.page_content for doc in state["context"])
    prompt = get_prompt(query=state["question"], context=context)
    response = llm.invoke(prompt)
    return {"answer": response.content}


def main():
    chunks = chunk(get_document())
    logger.info("Split blog post document into [%s] chunks.", len(chunks))

    document_ids = vectorize(documents=chunks)
    logger.info("vectorised chunks with first three ids=%s", document_ids[:3])

    sys.exit()

    # Compile application and test
    graph_builder = StateGraph(State).add_sequence([retrieve, generate])
    graph_builder.add_edge(START, "retrieve")
    graph = graph_builder.compile()

    response = graph.invoke({"question": "What is Task Decomposition?"})
    print(response["answer"])


if __name__ == "__main__":
    main()
