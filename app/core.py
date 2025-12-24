import os
import time

os.environ["CURL_CA_BUNDLE"] = ""
os.environ["REQUESTS_CA_BUNDLE"] = ""
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings

from app.observability import logger


class RAGService:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        # Note: Local path changed to match relative project structure if running locally,
        # but maintaining compatibility for the Docker target.
        persist_dir = os.getenv("CHROMA_DB_DIR", "chroma_db")
        self.vectorstore = Chroma(persist_directory=persist_dir, embedding_function=self.embeddings)
        self.llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.1)

    def process(self, query: str):
        t0 = time.time()
        # Retrieval
        docs = self.vectorstore.similarity_search_with_score(query, k=6)

        # Confiança baseada em distância L2 (Menor é melhor)
        avg_score = sum(d[1] for d in docs) / (len(docs) or 1)
        confidence = "High" if avg_score < 0.5 else "Medium" if avg_score < 0.8 else "Low"

        # Generation
        context = "\n".join([d.page_content for d, _ in docs])

        system_prompt = (
            "Você é um Arquiteto Especialista Sênior da Red Hat.\n\n"
            "SUA MISSÃO:\n"
            "Responder de forma técnica e consultiva, priorizando os DOCUMENTOS INTERNOS fornecidos.\n\n"
            "DIRETRIZES:\n"
            "1. Se o termo (ex: Kubernetes) for mencionado mas não definido nos documentos, use seu conhecimento prévio "
            "para dar uma breve explicação técnica, mas deixe claro como ele se relaciona com o contexto da Red Hat "
            "(ex: 'Conforme os documentos, a Red Hat utiliza Kubernetes no OpenShift...').\n"
            "2. Cite sempre o nome do documento e a página quando encontrar a informação.\n"
            "3. Se a informação for totalmente inexistente nos documentos e no seu conhecimento sobre Red Hat, "
            "informe que não foi encontrado.\n"
            "4. Mantenha o foco em: Segurança, Automação (Ansible), Hybrid Cloud e OpenShift.\n\n"
            "CONTEXTO DOS DOCUMENTOS:\n{context}\n\n"
            "PERGUNTA DO USUÁRIO: {question}"
        )

        chain = ChatPromptTemplate.from_template(system_prompt) | self.llm

        logger.info("Groq Invoked", extra={"props": {"query": query, "conf": confidence}})
        ans = chain.invoke({"context": context, "question": query})

        return {
            "answer": ans.content,
            "confidence": confidence,
            "latency_ms": round((time.time() - t0) * 1000, 2),
            "sources": [
                {
                    "source": f"{os.path.basename(d.metadata.get('source','?'))} pg.{d.metadata.get('page',0)+1}",
                    "content_snippet": d.page_content[:100],
                    "score": round(s, 3),
                }
                for d, s in docs
            ],
        }


engine = RAGService()
