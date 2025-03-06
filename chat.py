import os
from dotenv import load_dotenv

from langchain.chat_models import init_chat_model
from langchain import hub
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_pymupdf4llm import PyMuPDF4LLMLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langgraph.graph import START, StateGraph

from typing_extensions import TypedDict, List, Annotated
from typing import Literal

load_dotenv()

TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
vector_store = InMemoryVectorStore(embeddings)

# init chat model
llm = init_chat_model("meta-llama/Llama-3.3-70B-Instruct-Turbo", model_provider="together")

# schema search
class Search(TypedDict):
    query: Annotated[str, ..., "Search query to run."]
    section: Annotated[
        Literal["beginning", "middle", "end"],
        ...,
        "Section of the document to search."
    ]

prompt = hub.pull('rlm/rag-prompt')

class State(TypedDict):
    question: str
    query: Search
    context: List[Document]
    answer: str

def analyze_query(state: State):
    structured_llm = llm.with_structured_output(Search)
    query = structured_llm.invoke(state["question"])
    return {"query": query}

def retrieve(state: State):
    query = state["query"]
    retrieved_docs = vector_store.similarity_search(
        query["query"],
        filter=lambda doc: doc.metadata.get("section") == query["section"],
    )
    return {"context": retrieved_docs}

def generate(state: State):
    docs_content = "\n\n".join(doc.page_content for doc in state["context"])
    messages = prompt.invoke({
        "question": state["question"],
        "context": docs_content
    })
    response = llm.invoke(messages)
    return {"answer": response.content}

# for value in graph.stream(
#     {"question": "What is the purpose of this document??"},
#     stream_mode="updates",
# ):
#     if "answer" in value:
#         print(value["answer"])
    # print(f"{step}\n\n----------------\n")




def get_graph(file_path):
    # file_path = "./assets/Manual.pdf"
    loader = PyMuPDF4LLMLoader(file_path)
    docs = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    all_splits = text_splitter.split_documents(docs)
    total_documents = len(all_splits)
    third = total_documents // 3

    for i, document in enumerate(all_splits):
        if i < third:
            document.metadata['section'] = 'beginning'
        elif i < 2 * third:
            document.metadata['section'] = 'middle'
        else:
            document.metadata['section'] = 'end'

    _ = vector_store.add_documents(all_splits)

    graph_builder = StateGraph(State).add_sequence([analyze_query, retrieve, generate])
    graph_builder.add_edge(START, "analyze_query")
    graph = graph_builder.compile()
    
    return graph

# graph = get_graph()
# test = graph.invoke({"question": "what is stepper motors"})
# print(test)