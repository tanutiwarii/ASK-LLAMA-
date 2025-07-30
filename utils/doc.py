from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
import hashlib
import os


def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text


def get_text_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    return text_splitter.split_text(text)


def get_documents_hash(pdf_docs):
    """Generate a unique hash for the uploaded documents"""
    hasher = hashlib.md5()
    for pdf in pdf_docs:
        hasher.update(pdf.getvalue())
    return hasher.hexdigest()


def build_vector_store(chunks, persist_dir="chroma_doc_store"):
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vector_store = Chroma.from_texts(
        texts=chunks,
        embedding=embeddings,
        persist_directory=persist_dir
    )
    return vector_store


def load_vector_store(persist_dir="chroma_doc_store"):
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    return Chroma(
        persist_directory=persist_dir,
        embedding_function=embeddings
    )


def get_context_from_docs(query, vector_store, previous_context=None):
    """
    Get context with special handling for follow-up questions
    """
    if previous_context:
        # For follow-up questions, include previous context in the search
        extended_query = f"{previous_context}\n\nFollow-up: {query}"
        docs = vector_store.similarity_search(extended_query, k=5)
    else:
        docs = vector_store.similarity_search(query, k=3)
    
    # Filter and format the context
    if not docs:
        return None
        
    min_similarity = 0.4  # Lower threshold for follow-ups
    if hasattr(docs[0], 'metadata') and 'score' in docs[0].metadata:
        if docs[0].metadata['score'] < min_similarity:
            return None
    
    return "\n\n".join([doc.page_content for doc in docs])