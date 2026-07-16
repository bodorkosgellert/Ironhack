"""Local-first Streamlit interface for the cited asthma evidence assistant."""

from __future__ import annotations

import streamlit as st

from rag.assistant import EvidenceAssistant
from rag.dense import dense_status, sentence_transformers_available
from rag.hosted import hosted_status
from rag.ollama import DEFAULT_MODEL, setup_instructions, status


EXAMPLES = (
    "What is the Pearson correlation between PM2.5 and asthma?",
    "What is the cross-validated R² for the PM2.5-only model?",
    "Why can this ecological study not establish causality?",
    "How are prevalence, incidence, and acute exacerbations different?",
)


def _streamlit_secrets() -> dict | None:
    try:
        return {key: st.secrets[key] for key in st.secrets}
    except Exception:
        return None


@st.cache_resource
def get_assistant(
    threshold: float,
    retrieval_mode: str,
    lexical_weight: float,
    dense_weight: float,
) -> EvidenceAssistant:
    return EvidenceAssistant(
        threshold=threshold,
        retrieval_mode=retrieval_mode,
        lexical_weight=lexical_weight,
        dense_weight=dense_weight,
        hosted_secrets=_streamlit_secrets(),
    )


def main() -> None:
    st.set_page_config(page_title="Local cited evidence assistant", page_icon="📚", layout="wide")
    st.title("Local cited evidence assistant")
    st.caption(
        "This assistant explains existing public aggregate results from the Alabama asthma project. "
        "It does not modify or rerun the epidemiological analysis. "
        "This app is separate from the Version 2 epidemiology dashboard."
    )

    ollama = status()
    hosted_ok, hosted_model = hosted_status(_streamlit_secrets())
    embeddings = dense_status()

    with st.sidebar:
        st.header("Runtime status")
        if ollama.available:
            st.success("Ollama available (local)")
            if ollama.models:
                st.caption("Installed models: " + ", ".join(ollama.models))
            else:
                st.warning("Ollama is running, but no models were reported.")
        else:
            st.warning("Ollama unavailable on this host")
            st.code(setup_instructions(), language="text")

        if hosted_ok:
            st.success(f"Hosted language model configured (`{hosted_model}`)")
        else:
            st.info("Hosted language model not configured")

        if embeddings.available:
            st.success(f"Dense embeddings package available (`{embeddings.model_name}`)")
        else:
            st.info("Dense embeddings optional package not installed; term frequency-inverse document frequency remains available")

        st.header("Settings")
        model = st.text_input("Ollama chat model", value=DEFAULT_MODEL)
        retrieval_mode = st.selectbox(
            "Retrieval mode",
            options=("tfidf", "hybrid", "dense"),
            index=0,
            help=(
                "tfidf is the default and works offline with no extra download. "
                "hybrid and dense use all-MiniLM-L6-v2 when sentence-transformers is installed."
            ),
        )
        lexical_weight = st.slider(
            "Lexical weight (hybrid)",
            min_value=0.0,
            max_value=1.0,
            value=0.55,
            step=0.05,
            disabled=retrieval_mode != "hybrid",
        )
        dense_weight = st.slider(
            "Dense weight (hybrid)",
            min_value=0.0,
            max_value=1.0,
            value=0.45,
            step=0.05,
            disabled=retrieval_mode != "hybrid",
        )
        top_k = st.slider("Retrieved passages", min_value=1, max_value=10, value=5)
        threshold = st.slider(
            "Low-score refusal threshold",
            min_value=0.0,
            max_value=0.5,
            value=0.12,
            step=0.01,
        )
        generation_available = (ollama.available and model in ollama.models) or hosted_ok
        retrieval_only = st.checkbox(
            "Retrieval only (no generation)",
            value=not generation_available,
            help=(
                "Returns cited passages and deterministic metrics without asking a language model "
                "to narrate them. Recommended on Streamlit Community Cloud unless hosted secrets are set."
            ),
        )
        if retrieval_mode in {"hybrid", "dense"} and not sentence_transformers_available():
            st.caption(
                "sentence-transformers is not installed here; the assistant will fall back to "
                "term frequency-inverse document frequency retrieval."
            )

    st.subheader("Example questions")
    columns = st.columns(2)
    selected: str | None = None
    for index, example in enumerate(EXAMPLES):
        if columns[index % 2].button(example, key=f"example-{index}", use_container_width=True):
            selected = example

    question = st.chat_input("Ask about the public Alabama asthma analysis")
    question = question or selected
    if not question:
        st.info("Choose an example or enter a question. Unsupported evidence is refused.")
        return

    with st.chat_message("user"):
        st.write(question)
    with st.spinner("Retrieving cited evidence…"):
        answer = get_assistant(
            threshold,
            retrieval_mode,
            lexical_weight,
            dense_weight,
        ).ask(
            question,
            top_k=top_k,
            retrieval_only=retrieval_only,
            model=model,
        )
    with st.chat_message("assistant"):
        if answer.refused:
            st.warning(answer.text)
        else:
            st.markdown(answer.text)
        if answer.notice:
            st.info(answer.notice)
        st.caption(f"Retrieval mode used: `{answer.retrieval_mode}`")

    st.subheader("Retrieved sources")
    if not answer.passages:
        st.caption("No source passage was returned.")
    for rank, passage in enumerate(answer.passages, start=1):
        with st.expander(f"{rank}. {passage.citation} · score {passage.score:.3f}"):
            st.write(passage.chunk.text)
            st.caption(f"Corpus type: {passage.chunk.kind}")

    st.divider()
    st.caption(
        "Safeguards: public allowlisted files only; exact JSON key paths for metrics; "
        "deterministic metric routing remains authoritative; no causal inference. "
        "Optional hosted generation uses Streamlit secrets or environment variables and is never committed."
    )


if __name__ == "__main__":
    main()
