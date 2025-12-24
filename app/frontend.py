import os

import requests
import streamlit as st


# --- CONFIGURATION & STYLING ---
def apply_custom_style():
    st.markdown(
        """
        <style>
        /* Main background and text */
        .main {
            background-color: #ffffff;
            color: #1a1a1a;
        }
        
        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background-color: #ee0000;
            color: #ffffff;
        }
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
            color: #ffffff !important;
        }
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2 {
            color: #ffffff !important;
        }

        /* Buttons Styling (Main and Sidebar) */
        div.stButton > button {
            background-color: #ee0000 !important;
            color: #ffffff !important;
            border: 1px solid #ee0000 !important;
            font-weight: bold !important;
        }
        div.stButton > button:hover {
            background-color: #cc0000 !important;
            color: #ffffff !important;
        }

        /* Chat Message Styling */
        .stChatMessage {
            border-left: 5px solid #ee0000;
            background-color: #f9f9f9;
            border-radius: 5px;
            margin-bottom: 10px;
        }

        /* Titles and Headers */
        h1, h2, h3 {
            color: #333333;
        }
        
        /* Custom Red Header Class */
        .red-text {
            color: #ee0000;
        }

        /* Expander styling */
        .streamlit-expanderHeader {
            color: #ee0000 !important;
            font-weight: bold;
        }
        
        /* Mosaic Button Styling Override to look like tags */
        .mosaic-container div.stButton > button {
            padding: 2px 10px !important;
            font-size: 12px !important;
            border-radius: 20px !important;
            margin: 2px !important;
            background-color: #ffffff !important;
            color: #ee0000 !important;
            border: 1px solid #ee0000 !important;
        }
        .mosaic-container div.stButton > button:hover {
            background-color: #ee0000 !important;
            color: #ffffff !important;
        }
        </style>
    """,
        unsafe_allow_html=True,
    )


def init_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "suggested_query" not in st.session_state:
        st.session_state.suggested_query = None


# --- COMPONENTS ---
def sidebar_component():
    with st.sidebar:
        # Using local image provided by user
        logo_path = os.path.join(os.path.dirname(__file__), "download.png")
        if os.path.exists(logo_path):
            st.image(logo_path, width=200)
        else:
            st.image("https://www.redhat.com/cms/managed-files/RedHat-Logo-Hat-RGB.svg", width=150)

        st.title("Settings")
        api_url = st.text_input("API Endpoint", value="http://localhost:8000/query")

        st.divider()
        st.caption("v1.1.0 | Red Hat AI Consultant")
        return api_url


def display_source(src):
    with st.container(border=True):
        st.markdown(f"**Fonte:** 📄 `{src['source']}`")
        st.caption(f"**Score de Relevância:** {src['score']}")
        st.markdown(f"*{src['content_snippet']}...*")


def chat_message_ui(role, content, extra_data=None):
    with st.chat_message(role):
        st.markdown(content)
        if extra_data:
            with st.expander("📚 Fontes Consultadas"):
                for src in extra_data.get("sources", []):
                    display_source(src)


def handle_api_call(api_url, query):
    try:
        response = requests.post(api_url, json={"query": query}, timeout=30)
        if response.status_code == 200:
            data = response.json()
            extra_data = {
                "confidence": data["confidence"],
                "latency_ms": data["latency_ms"],
                "sources": data["sources"],
            }
            return data["answer"], extra_data
        else:
            return f"Erro na API ({response.status_code}): {response.text}", None
    except Exception as e:
        return f"Falha de conexão: {str(e)}", None


# --- MAIN APP ---
def main():
    st.set_page_config(page_title="RAG Consultant | Red Hat", page_icon="🟥", layout="wide")
    apply_custom_style()
    init_session_state()

    api_url = sidebar_component()

    # Main Header
    col_title, col_clear = st.columns([0.8, 0.2])
    with col_title:
        st.title("🟥 Red Hat AI Consultant")
        st.markdown("*Apoio técnico avançado para 2024-2025.*")

    with col_clear:
        if st.button("Limpar Histórico", use_container_width=True):
            st.session_state.messages = []
            st.session_state.suggested_query = None
            st.rerun()

    # Layout: Welcome Screen (Only if no messages)
    if not st.session_state.messages:
        st.divider()
        st.markdown("### 🏆 Temas Sugeridos")
        st.markdown("Clique em um tema para iniciar a consulta automática:")

        topics = [
            "Estratégias de Automação com Ansible",
            "Segurança e Conformidade no Kubernetes",
            "Benefícios do RHEL no AWS",
            "Modernização de Aplicações Legadas",
            "Governança de Dados e AI",
        ]

        # Display topics in a grid or simple list
        cols = st.columns(2)
        for i, topic in enumerate(topics):
            if cols[i % 2].button(topic, key=topic, use_container_width=True):
                st.session_state.suggested_query = topic
                st.rerun()

    # Process Suggested Query
    if st.session_state.suggested_query:
        prompt = st.session_state.suggested_query
        st.session_state.suggested_query = None
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("assistant"):
            with st.spinner("Analisando documentos técnicos..."):
                ans, extra = handle_api_call(api_url, prompt)
                st.session_state.messages.append({"role": "assistant", "content": ans, "extra_data": extra})
        st.rerun()

    # Display Chat History
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            chat_message_ui(message["role"], message["content"], message.get("extra_data"))

    # Chat Input
    if prompt := st.chat_input("Como posso ajudar?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()

    # Trigger processing
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        latest_query = st.session_state.messages[-1]["content"]
        with st.chat_message("assistant"):
            with st.spinner("Analisando documentos técnicos..."):
                ans, extra = handle_api_call(api_url, latest_query)
                st.session_state.messages.append({"role": "assistant", "content": ans, "extra_data": extra})
        st.rerun()


if __name__ == "__main__":
    main()
