import os
import shutil
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List


CHROMA_PATH = "./database/chroma"
DOCS_PATH = "./docs"


def main():
    """
    Main function to create and initialize the vector database.

    This function performs the following steps:
    - Loads the documents from the specified directory.
    - Splits the text into chunks.
    - Creates a Chroma database.

    Returns:
        None
    """
    documents_path = [
        f"{DOCS_PATH}/{file}"
        for file in os.listdir(DOCS_PATH)
        if file.endswith(".pdf")
    ]
    docs = load_documents(documents_path)
    splits = split_text(docs)
    create_chroma(splits)


def load_documents(documents_path):
    pages = []
    for path in documents_path:
        loader = PyPDFLoader(path)
        # loader.load_and_split() returns a list of Document objects, each representing a page.
        pages += loader.load_and_split()
        print(f"Loaded {len(loader.load_and_split())} pages from {path}")

    return pages


def split_text(docs: List[Document]):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(docs)
    print("Splitted documents.")
    return splits


def create_chroma(splits: List[Document]):
    print("Creating Chroma database...")
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)

    Chroma.from_documents(
        documents=splits,
        embedding=OpenAIEmbeddings(),
        persist_directory=CHROMA_PATH,
    )
    print(f"Saved {len(splits)} documents to {CHROMA_PATH}.")


if __name__ == "__main__":
    main()
