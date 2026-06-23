"""
PubMed Research Agent - Streamlit Frontend

A modern UI for AI-powered PubMed literature search and analysis.

Run:
    cd frontend
    streamlit run app.py
"""

from __future__ import annotations

import sys
import os
import textwrap
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import streamlit.components.v1 as components

from api_client import get_agent, run_research
from agents.research_agent import ResearchReport


# ---------------------------------------------------------------------------
# Page Config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="PubMed Research Agent",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------

CUSTOM_CSS = """
<style>
    /* ---- Global ---- */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    .stApp {
        background: linear-gradient(135deg, #0f1117 0%, #1a1d2e 100%);
    }

    /* ---- Main Title ---- */
    .main-title {
        font-size: 2.4rem;
        font-weight: 700;
        background: linear-gradient(135deg, #60a5fa, #a78bfa, #f472b6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .main-subtitle {
        color: #94a3b8;
        font-size: 0.95rem;
        margin-bottom: 1.5rem;
    }

    /* ---- Cards ---- */
    .result-card {
        background: linear-gradient(145deg, #1e2130, #252a3a);
        border: 1px solid #2d3348;
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 0.75rem;
        transition: all 0.2s ease;
    }
    .result-card:hover {
        border-color: #60a5fa;
        box-shadow: 0 4px 20px rgba(96,165,250,0.15);
    }
    .card-title {
        color: #e2e8f0;
        font-size: 1.05rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        line-height: 1.5;
    }
    .card-meta {
        color: #64748b;
        font-size: 0.8rem;
        display: flex;
        gap: 1rem;
        flex-wrap: wrap;
        margin-bottom: 0.5rem;
    }
    .card-meta span {
        display: inline-flex;
        align-items: center;
        gap: 4px;
    }
    .card-abstract {
        color: #cbd5e1;
        font-size: 0.9rem;
        line-height: 1.6;
    }
    .badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.72rem;
        font-weight: 500;
    }
    .badge-pmid { background: #1e3a5f; color: #60a5fa; }
    .badge-doi  { background: #2d1b4e; color: #a78bfa; }
    .badge-year { background: #1a3d2e; color: #4ade80; }

    /* ---- Section headers ---- */
    .section-header {
        color: #e2e8f0;
        font-size: 1.3rem;
        font-weight: 600;
        padding-bottom: 0.5rem;
        margin: 1.5rem 0 1rem 0;
        border-bottom: 2px solid;
        border-image: linear-gradient(90deg, #60a5fa, transparent) 1;
    }
    .section-icon { font-size: 1.2rem; margin-right: 0.4rem; }

    /* ---- Hotspot cards ---- */
    .hotspot-card {
        background: linear-gradient(145deg, #1a1f35, #21273f);
        border: 1px solid #2d3350;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.6rem;
    }
    .hotspot-title {
        color: #93c5fd;
        font-weight: 600;
        font-size: 0.95rem;
    }
    .hotspot-desc {
        color: #94a3b8;
        font-size: 0.85rem;
        margin: 0.3rem 0;
    }

    /* ---- Finding bullets ---- */
    .finding-item {
        display: flex;
        align-items: flex-start;
        gap: 0.5rem;
        padding: 0.4rem 0;
        color: #cbd5e1;
        font-size: 0.9rem;
    }
    .finding-bullet {
        color: #60a5fa;
        font-weight: 700;
        min-width: 1rem;
    }

    /* ---- Future direction ---- */
    .direction-card {
        background: linear-gradient(145deg, #1d1e30, #252840);
        border-left: 3px solid #f472b6;
        border-radius: 0 10px 10px 0;
        padding: 0.8rem 1.2rem;
        margin-bottom: 0.6rem;
    }
    .direction-title {
        color: #f9a8d4;
        font-weight: 600;
        font-size: 0.92rem;
    }
    .direction-rationale {
        color: #94a3b8;
        font-size: 0.82rem;
        margin-top: 0.3rem;
    }

    /* ---- Sidebar ---- */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #111318, #181b28);
    }
    .sidebar-section {
        color: #94a3b8;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-weight: 600;
        margin-top: 1.2rem;
        margin-bottom: 0.4rem;
    }

    /* ---- Buttons ---- */
    .stButton > button {
        background: linear-gradient(135deg, #3b82f6, #8b5cf6) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        padding: 0.5rem 2rem !important;
        transition: all 0.2s !important;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 24px rgba(96,165,250,0.3);
    }

    /* ---- Inputs ---- */
    .stTextInput > div > div > input {
        background: #1e2130 !important;
        border: 1px solid #2d3348 !important;
        border-radius: 8px !important;
        color: #e2e8f0 !important;
        padding: 0.7rem 1rem !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #60a5fa !important;
        box-shadow: 0 0 0 2px rgba(96,165,250,0.2) !important;
    }

    /* ---- Metrics ---- */
    .metric-box {
        background: linear-gradient(145deg, #1a1f35, #21273f);
        border-radius: 10px;
        padding: 1rem 1.3rem;
        text-align: center;
        border: 1px solid #2d3348;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #60a5fa;
    }
    .metric-label {
        font-size: 0.75rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* ---- Copy button ---- */
    .copy-btn {
        background: #2d3348;
        border: 1px solid #3d4560;
        color: #94a3b8;
        border-radius: 6px;
        padding: 0.3rem 0.8rem;
        font-size: 0.78rem;
        cursor: pointer;
        transition: all 0.2s;
    }
    .copy-btn:hover {
        background: #3d4560;
        color: #e2e8f0;
    }

    /* ---- Footer ---- */
    .footer {
        text-align: center;
        color: #475569;
        font-size: 0.75rem;
        margin-top: 3rem;
        padding: 1rem;
        border-top: 1px solid #1e2130;
    }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------------------------

DEFAULTS = {
    "pubmed_email": "user@example.com",
    "pubmed_api_key": "",
    "verify_ssl": False,
    "llm_api_base": "https://api.openai.com/v1",
    "llm_api_key": "",
    "llm_model": "gpt-4o-mini",
    "llm_temperature": 0.3,
    "max_articles": 10,
    "language": "zh",
    "last_report": None,
    "last_query": "",
    "is_searching": False,
}

for key, val in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = val


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

def render_sidebar():
    """Render left sidebar with API and model configuration."""
    with st.sidebar:
        st.markdown(
            '<div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:1rem;">'
            '<span style="font-size:1.3rem;">🔬</span>'
            '<span style="font-weight:700;font-size:1.1rem;color:#e2e8f0;">Settings</span>'
            '</div>',
            unsafe_allow_html=True,
        )

        # --- PubMed Configuration ---
        st.markdown('<p class="sidebar-section">📚 PubMed API</p>', unsafe_allow_html=True)
        st.session_state.pubmed_email = st.text_input(
            "Email",
            value=st.session_state.pubmed_email,
            key="cfg_email",
            help="Required by NCBI. Register at account.ncbi.nlm.nih.gov",
        )
        st.session_state.pubmed_api_key = st.text_input(
            "API Key (optional)",
            value=st.session_state.pubmed_api_key,
            type="password",
            key="cfg_pubmed_key",
            help="NCBI API key for higher rate limit (10 req/s)",
        )
        st.session_state.verify_ssl = st.checkbox(
            "Verify SSL",
            value=st.session_state.verify_ssl,
            key="cfg_ssl",
            help="Disable if behind corporate proxy with self-signed certs",
        )

        # --- LLM Configuration ---
        st.markdown('<p class="sidebar-section">🤖 LLM API</p>', unsafe_allow_html=True)
        st.session_state.llm_api_base = st.text_input(
            "Base URL",
            value=st.session_state.llm_api_base,
            key="cfg_base",
            help="OpenAI-compatible API endpoint",
        )
        st.session_state.llm_api_key = st.text_input(
            "API Key",
            value=st.session_state.llm_api_key,
            type="password",
            key="cfg_llm_key",
        )

        model_presets = [
            "gpt-4o", "gpt-4o-mini",
            "deepseek-chat", "deepseek-reasoner",
            "qwen-turbo", "qwen-plus", "qwen-max",
        ]
        model_idx = 0
        for i, m in enumerate(model_presets):
            if m == st.session_state.llm_model:
                model_idx = i
                break
        st.session_state.llm_model = st.selectbox(
            "Model",
            model_presets,
            index=model_idx,
            key="cfg_model",
        )

        col1, col2 = st.columns(2)
        with col1:
            st.session_state.max_articles = st.number_input(
                "Max Results",
                min_value=1,
                max_value=100,
                value=st.session_state.max_articles,
                key="cfg_max",
            )
        with col2:
            st.session_state.language = st.selectbox(
                "Language",
                ["en", "zh"],
                index=0 if st.session_state.language == "en" else 1,
                key="cfg_lang",
            )

        st.session_state.llm_temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=st.session_state.llm_temperature,
            step=0.1,
            key="cfg_temp",
        )

        # --- Divider ---
        st.markdown("<hr style='border-color:#2d3348;margin:1.2rem 0;'>", unsafe_allow_html=True)

        # --- About ---
        st.markdown(
            '<p style="color:#475569;font-size:0.75rem;">'
            '🔬 PubMed Research Agent v0.1<br>'
            'AI-powered literature analysis'
            '</p>',
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Main Content
# ---------------------------------------------------------------------------

def render_header():
    """Render the page title and subtitle."""
    st.markdown('<h1 class="main-title">PubMed Research Agent</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="main-subtitle">'
        '🧠 AI-powered PubMed literature search, analysis & insights'
        '</p>',
        unsafe_allow_html=True,
    )


def render_search_bar():
    """Render the query input and search button."""
    col1, col2 = st.columns([5, 1])
    with col1:
        query = st.text_input(
            "",
            placeholder="Enter a research question, e.g. SEC61G in Lung Cancer...",
            key="search_query",
            label_visibility="collapsed",
        )
    with col2:
        do_search = st.button("🔍 Search", use_container_width=True, key="btn_search")

    return query, do_search


def render_status_bar(status: str, elapsed: float, total: int):
    """Render status + metrics row."""
    c1, c2, c3, c4 = st.columns(4)
    color_map = {
        "completed": "#4ade80",
        "partial": "#fbbf24",
        "failed": "#f87171",
        "running": "#60a5fa",
    }
    color = color_map.get(status, "#64748b")

    with c1:
        st.markdown(
            f'<div class="metric-box">'
            f'<div class="metric-value" style="color:{color};">{status.upper()}</div>'
            f'<div class="metric-label">Status</div></div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f'<div class="metric-box">'
            f'<div class="metric-value">{total}</div>'
            f'<div class="metric-label">Articles</div></div>',
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f'<div class="metric-box">'
            f'<div class="metric-value">{elapsed:.1f}s</div>'
            f'<div class="metric-label">Duration</div></div>',
            unsafe_allow_html=True,
        )
    with c4:
        model = st.session_state.get("llm_model", "-")
        st.markdown(
            f'<div class="metric-box">'
            f'<div class="metric-value" style="font-size:1rem;">{model}</div>'
            f'<div class="metric-label">Model</div></div>',
            unsafe_allow_html=True,
        )


def render_articles(articles: list[dict]):
    """Render the article list with expandable abstracts."""
    if not articles:
        st.info("No articles found. Try adjusting your query.")
        return

    st.markdown(f'<div class="section-header"><span class="section-icon">📄</span>Literature Results ({len(articles)})</div>', unsafe_allow_html=True)

    for art in articles:
        pmid = art.get("pmid", "")
        title = art.get("title", "No Title")
        journal = art.get("journal", "")
        year = art.get("publish_date", "")[:4] if art.get("publish_date") else ""
        doi = art.get("doi", "")
        abstract = art.get("abstract", "")
        authors = art.get("authors", [])
        author_str = ", ".join(a["last_name"] + " " + a["fore_name"] for a in authors[:3])
        if len(authors) > 3:
            author_str += f" et al."

        st.markdown(
            f'<div class="result-card">'
            f'<div class="card-title">{title}</div>'
            f'<div class="card-meta">'
            f'<span class="badge badge-pmid">PMID:{pmid}</span>'
            + (f'<span class="badge badge-doi">DOI:{doi[:30]}</span>' if doi else '')
            + (f'<span class="badge badge-year">{year}</span>' if year else '')
            + f'<span style="color:#64748b;">{journal}</span>'
            f'<span style="color:#475569;">{author_str}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        with st.expander("Show Abstract"):
            st.markdown(f'<div class="card-abstract">{abstract or "No abstract available."}</div>', unsafe_allow_html=True)
            pubmed_url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            st.markdown(f'<a href="{pubmed_url}" target="_blank" style="color:#60a5fa;font-size:0.8rem;">🔗 View on PubMed</a>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)


def render_analysis(report):
    """Render the AI analysis sections."""
    if not report.research_background and not report.main_findings:
        return

    # --- Background ---
    if report.research_background:
        st.markdown(f'<div class="section-header"><span class="section-icon">📖</span>Research Background</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div style="color:#cbd5e1;line-height:1.8;font-size:0.92rem;">{report.research_background}</div>',
            unsafe_allow_html=True,
        )

    # --- Hotspots ---
    if report.current_hotspots:
        st.markdown(f'<div class="section-header"><span class="section-icon">🔥</span>Research Hotspots</div>', unsafe_allow_html=True)
        cols = st.columns(min(len(report.current_hotspots), 2))
        for i, hs in enumerate(report.current_hotspots):
            topic = hs.get("topic", "")
            desc = hs.get("description", "")
            evidence = hs.get("evidence", [])
            with cols[i % 2]:
                st.markdown(
                    f'<div class="hotspot-card">'
                    f'<div class="hotspot-title">{topic}</div>'
                    f'<div class="hotspot-desc">{desc}</div>'
                    f'<div style="color:#475569;font-size:0.72rem;margin-top:0.4rem;">'
                    f'📎 {" ".join(evidence)}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    # --- Main Findings ---
    if report.main_findings:
        st.markdown(f'<div class="section-header"><span class="section-icon">💡</span>Key Findings</div>', unsafe_allow_html=True)
        for finding in report.main_findings:
            st.markdown(
                f'<div class="finding-item">'
                f'<span class="finding-bullet">▸</span>'
                f'<span>{finding}</span></div>',
                unsafe_allow_html=True,
            )

    # --- Methods ---
    if report.experimental_methods:
        st.markdown(f'<div class="section-header"><span class="section-icon">🧪</span>Experimental Methods</div>', unsafe_allow_html=True)
        meth_cols = st.columns(min(len(report.experimental_methods), 3))
        for i, m in enumerate(report.experimental_methods):
            method = m.get("method", "")
            purpose = m.get("purpose", "")
            freq = m.get("frequency", 0)
            with meth_cols[i % 3]:
                st.markdown(
                    f'<div style="background:#1a1f35;border-radius:8px;padding:0.7rem 1rem;margin-bottom:0.5rem;text-align:center;">'
                    f'<div style="color:#60a5fa;font-weight:600;">{method}</div>'
                    f'<div style="color:#94a3b8;font-size:0.78rem;">{purpose}</div>'
                    f'<div style="color:#475569;font-size:0.7rem;">× {freq} papers</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    # --- Future Directions ---
    if report.future_directions:
        st.markdown(f'<div class="section-header"><span class="section-icon">🚀</span>Future Research Directions</div>', unsafe_allow_html=True)
        for fd in report.future_directions:
            direction = fd.get("direction", "")
            rationale = fd.get("rationale", "")
            challenges = fd.get("challenges", [])
            chall_str = " | ".join(challenges)
            st.markdown(
                f'<div class="direction-card">'
                f'<div class="direction-title">→ {direction}</div>'
                f'<div class="direction-rationale">{rationale}</div>'
                + (f'<div style="color:#475569;font-size:0.72rem;margin-top:0.4rem;">⚠️ {chall_str}</div>' if chall_str else '')
                + f'</div>',
                unsafe_allow_html=True,
            )


def render_export_buttons(report: ResearchReport):
    """Render copy and download buttons."""
    if not report:
        return

    json_str = report.to_json()

    c1, c2, c3 = st.columns([1, 1, 4])
    with c1:
        st.download_button(
            label="📥 JSON",
            data=json_str,
            file_name=f"research_{report.query[:30].replace(' ', '_')}.json",
            mime="application/json",
            use_container_width=True,
            key="dl_json",
        )
    with c2:
        # Markdown export
        md = _report_to_markdown(report)
        st.download_button(
            label="📄 Markdown",
            data=md,
            file_name=f"research_{report.query[:30].replace(' ', '_')}.md",
            mime="text/markdown",
            use_container_width=True,
            key="dl_md",
        )
    with c3:
        if st.button("📋 Copy JSON", use_container_width=True, key="copy_json"):
            st.code(json_str, language="json")
            st.toast("JSON displayed below — select & copy!", icon="✅")


def _report_to_markdown(report: ResearchReport) -> str:
    """Convert a ResearchReport to Markdown text."""
    lines = [
        f"# PubMed Research Report",
        f"",
        f"**Query:** {report.query}",
        f"**Model:** {report.model_used}",
        f"**Status:** {report.status}",
        f"**Articles:** {report.total_pubmed_hits}",
        f"**Duration:** {report.elapsed_seconds:.1f}s",
        f"",
    ]
    if report.research_background:
        lines += ["## Research Background", "", report.research_background, ""]
    if report.current_hotspots:
        lines += ["## Research Hotspots", ""]
        for hs in report.current_hotspots:
            lines.append(f"- **{hs['topic']}**: {hs['description']}")
        lines.append("")
    if report.main_findings:
        lines += ["## Key Findings", ""]
        for f in report.main_findings:
            lines.append(f"- {f}")
        lines.append("")
    if report.future_directions:
        lines += ["## Future Directions", ""]
        for fd in report.future_directions:
            lines.append(f"- **{fd['direction']}**: {fd['rationale']}")
        lines.append("")
    if report.articles:
        lines += ["## References", ""]
        for a in report.articles[:10]:
            lines.append(f"- PMID:{a['pmid']} — {a['title']}")
        lines.append("")
    return "\n".join(lines)


def render_footer():
    """Render page footer."""
    st.markdown(
        '<div class="footer">'
        '🔬 PubMed Research Agent &middot; Built with Streamlit &amp; LangChain &middot; 2026'
        '</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    render_header()
    render_sidebar()

    query, do_search = render_search_bar()

    # Show last result if available
    last = st.session_state.get("last_report")
    if last and not do_search:
        report = ResearchReport(**last) if isinstance(last, dict) else last
        render_status_bar(report.status, report.elapsed_seconds, report.total_pubmed_hits)
        st.markdown("---")
        render_articles(report.articles[:st.session_state.max_articles])
        st.markdown("---")
        render_analysis(report)
        st.markdown("---")
        render_export_buttons(report)

    if do_search and query.strip():
        st.session_state.last_query = query
        st.session_state.is_searching = True

        with st.spinner(f"Searching PubMed for: *{query}* ..."):
            try:
                agent = get_agent(
                    pubmed_email=st.session_state.pubmed_email,
                    pubmed_api_key=st.session_state.pubmed_api_key,
                    verify_ssl=st.session_state.verify_ssl,
                    llm_api_base=st.session_state.llm_api_base,
                    llm_api_key=st.session_state.llm_api_key,
                    llm_model=st.session_state.llm_model,
                    llm_temperature=st.session_state.llm_temperature,
                    max_articles=st.session_state.max_articles,
                    language=st.session_state.language,
                )
                report = run_research(
                    agent=agent,
                    query=query.strip(),
                    max_results=st.session_state.max_articles,
                    language=st.session_state.language,
                )
                st.session_state.last_report = report.model_dump()
                st.session_state.is_searching = False
                st.rerun()
            except Exception as e:
                st.error(f"Research failed: {e}")
                st.session_state.is_searching = False

    render_footer()


if __name__ == "__main__":
    main()
