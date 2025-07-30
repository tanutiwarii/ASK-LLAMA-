import os
import git
from queue import Queue
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

# Settings
allowed_extensions = ['.py', '.ipynb', '.md']
model_name = "sentence-transformers/all-MiniLM-L6-v2"
model_kwargs = {"device": "cpu"}


class GitCodeEmbedder:
    def __init__(self, git_link):
        self.git_link = git_link
        last_name = self.git_link.split('/')[-1]
        self.repo_name = last_name.split('.')[0]
        self.clone_path = self.repo_name
        self.vectorstore_path = f"chroma_git_store/{self.repo_name}"

        self.embedder = HuggingFaceEmbeddings(model_name=model_name, model_kwargs=model_kwargs)
        self.chat_history = Queue(maxsize=3)

    def clone_repo(self):
        if not os.path.exists(self.clone_path):
            git.Repo.clone_from(self.git_link, self.clone_path)

    def extract_and_chunk(self):
        docs = []
        for dirpath, _, filenames in os.walk(self.clone_path):
            for file in filenames:
                ext = os.path.splitext(file)[1]
                if ext in allowed_extensions:
                    try:
                        loader = TextLoader(os.path.join(dirpath, file), encoding="utf-8")
                        docs.extend(loader.load_and_split())
                    except Exception:
                        pass

        splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        self.texts = splitter.split_documents(docs)

    def build_vectorstore(self):
        db = Chroma.from_documents(
            documents=self.texts,
            embedding=self.embedder,
            persist_directory=self.vectorstore_path
        )
        self.delete_repo_clone()
        return db

    def delete_repo_clone(self):
        if os.path.exists(self.clone_path):
            for root, dirs, files in os.walk(self.clone_path, topdown=False):
                for f in files:
                    os.remove(os.path.join(root, f))
                for d in dirs:
                    os.rmdir(os.path.join(root, d))
            os.rmdir(self.clone_path)

    def load_or_create_db(self):
        if os.path.exists(self.vectorstore_path):
            self.db = Chroma(
                persist_directory=self.vectorstore_path,
                embedding_function=self.embedder
            )
        else:
            self.clone_repo()
            self.extract_and_chunk()
            self.db = self.build_vectorstore()

        self.retriever = self.db.as_retriever(search_type="similarity", search_kwargs={"k": 3})

    def get_context(self, query):
        if not hasattr(self, "retriever"):
            raise ValueError("Vectorstore not loaded. Run `load_or_create_db()` first.")

        docs = self.retriever.get_relevant_documents(query)

        # Strict check: empty or irrelevant docs
        if not docs or all(len(doc.page_content.strip()) == 0 for doc in docs):
            return None

        # Optional: Add similarity score threshold if available
        context = "\n\n".join([doc.page_content for doc in docs])
        return context
