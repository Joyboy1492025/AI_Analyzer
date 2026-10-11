"""PDF loading, chunking, embeddings and retriever."""

import hashlib
from functools import lru_cache

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import (
    CHROMA_DIR,
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    EMBEDDING_MODEL,
    SEPARATORS,
)
from tool.guardrails import pdf_guardrail


@lru_cache(maxsize=1)
def get_embeddings() -> HuggingFaceEmbeddings:
    """Load the embedding model once and reuse it."""
    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)


def _file_hash(path: str) -> str:
    sha = hashlib.sha1()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            sha.update(block)
    return sha.hexdigest()


def build_retriever(pdf_path: str, k: int = 6, block_sensitive: bool = True):
    """Load a PDF, index it in Chroma and return (retriever, chunk_count)."""
    documents = PyPDFLoader(pdf_path).load()

    if not any(d.page_content.strip() for d in documents):
        raise ValueError(
            "No extractable text found in this PDF (it may be a scanned image)."
        )

    if block_sensitive:
        documents = pdf_guardrail(documents)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=SEPARATORS,
    )
    chunks = splitter.split_documents(documents)

    # One collection per file hash: re-uploading the same file doesn't duplicate chunks.
    vectorstore = Chroma(
        collection_name=f"pdf_{_file_hash(pdf_path)[:16]}",
        embedding_function=get_embeddings(),
        persist_directory=str(CHROMA_DIR),
    )
    if vectorstore._collection.count() == 0:
        vectorstore.add_documents(chunks)

    retriever = vectorstore.as_retriever(
        search_type="similarity", search_kwargs={"k": k}
    )
    return retriever, len(chunks)