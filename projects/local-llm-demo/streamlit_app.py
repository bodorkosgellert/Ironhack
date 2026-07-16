"""Local-first Streamlit interface for the cited asthma evidence assistant."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Streamlit Cloud CWD is the repo root. Ensure this package is importable even if
# the runner does not put the script directory on sys.path.
_DEMO_ROOT = Path(__file__).resolve().parent
if str(_DEMO_ROOT) not in sys.path:
    sys.path.insert(0, str(_DEMO_ROOT))

import streamlit as st

from rag.hosted import hosted_status
from rag.ollama import DEFAULT_MODEL, OllamaStatus, setup_instructions, status


EXAMPLES = (
    "What is the Pearson correlation between PM2.5 and asthma?",
    "What is the cross-validated R² for the PM2.5-only model?",
    "Why can this ecological study not establish causality?",
    "How are prevalence, incidence, and acute exacerbations different?",
)


def _running_on_streamlit_cloud() -> bool:
    """Detect Community Cloud so we never block on localhost Ollama."""
    if os.environ.get("STREAMLIT_SHARING_MODE"):
        return True
    if os.environ.get("STREAMLIT_RUNTIME_ENV", "").lower() == "cloud":
        return True
    # Community Cloud mounts the repo here.
    return Path("/mount/src").is_dir()


def _streamlit_secrets() -> dict | None:
    try:
        return {key: st.secrets[key] for key in st.secrets}
    except Exception:
        return None


def _ollama_status() -> OllamaStatus:
    if _running_on_streamlit_cloud():
        return OllamaStatus(
            False,
            error="Ollama is not used on Streamlit Community Cloud; retrieval-only or hosted chat applies.",
        )
    # Short timeout: Cloud/local hosts without Ollama should fail open quickly.
    return status(timeout=0.8)


@st.cache_resource
def get_assistant(
    threshold: float,
    retrieval_mode: str,
    lexical_weight: float,
    dense_weight: float,
):
    # Lazy import keeps sklearn / corpus work off the critical path until a question is asked.
    from rag.assistant import EvidenceAssistant

    return EvidenceAssistant(
        threshold=threshold,
        retrieval_mode=retrieval_mode,
        lexical_weight=lexical_weight,
        dense_weight=dense_weight,
        hosted_secrets=_streamlit_secrets(),
    )


def main() -> None:
    st.set_page_config(page_title="Local cited evidence assistant", page_icon="📚", layout="wide")
    # Paint chrome immediately before any optional status probes.
    st.title("Local cited evidence assistant")
    st.caption(
        "This assistant explains existing public aggregate results from the Alabama asthma project. "
        "It does not modify or rerun the epidemiological analysis. "
        "This app is separate from the Version 2 epidemiology dashboard."
    )
    st.markdown(
        "[County dashboard (charts)](https://alabama-asthma-pm25.streamlit.app/)"
    )

    ollama = _ollama_status()
    hosted_ok, hosted_model = hosted_status(_streamlit_secrets())

    # Dense status only checks importability; do not load MiniLM here.
    from rag.dense import dense_status, sentence_transformers_available

    embeddings = dense_status()

    with st.sidebar:
        st.markdown(
            "[County dashboard (charts)](https://alabama-asthma-pm25.streamlit.app/)"
        )
        st.caption("Separate app: interactive county charts and saved metrics.")
        st.divider()
        st.header("Runtime status")
        if ollama.available:
            st.success("Ollama available (local)")
            if ollama.models:
                st.caption("Installed models: " + ", ".join(ollama.models))
            else:
                st.warning("Ollama is running, but no models were reported.")
        elif _running_on_streamlit_cloud():
            st.info("Running on Streamlit Community Cloud — local Ollama is skipped.")
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
            st.info(
                "Dense embeddings optional package not installed; "
                "term frequency-inverse document frequency remains available"
            )

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
    st.markdown(
        "Related app: [County dashboard (charts)](https://alabama-asthma-pm25.streamlit.app/) "
        "· Source: "
        "[`projects/local-llm-demo` on `main`]"
        "(https://github.com/bodorkosgellert/Ironhack/tree/main/projects/local-llm-demo)"
    )


if __name__ == "__main__":
    main()
