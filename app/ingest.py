import os
import shutil

os.environ["CURL_CA_BUNDLE"] = ""
os.environ["REQUESTS_CA_BUNDLE"] = ""
from langchain_chroma import Chroma
from langchain_community.document_loaders import DirectoryLoader, PyMuPDFLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Path adjustments for local/Docker flexibility
# Points to redhat_rag/chroma_db and redhat_rag/data
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.getenv("CHROMA_DB_DIR", os.path.join(BASE_DIR, "chroma_db"))
DATA_PATH = os.getenv("DATA_DIR", os.path.join(BASE_DIR, "data"))


def run_ingest():
    if os.path.exists(DB_PATH):
        shutil.rmtree(DB_PATH)

    print(f">>> 1. Carregando PDFs de: {DATA_PATH}")
    loader = DirectoryLoader(DATA_PATH, glob="*.pdf", loader_cls=PyMuPDFLoader)
    docs = loader.load()
    if not docs:
        return print(f"!!! Nenhum PDF encontrado em: {os.path.abspath(DATA_PATH)}")

    print(f">>> 2. Chunking {len(docs)} páginas...")
    chunks = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100).split_documents(docs)

    print(">>> 3. Indexando vetores (isso usa CPU)...")
    Chroma.from_documents(
        chunks, HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2"), persist_directory=DB_PATH
    )
    print(">>> Concluído com sucesso.")


if __name__ == "__main__":
    run_ingest()
