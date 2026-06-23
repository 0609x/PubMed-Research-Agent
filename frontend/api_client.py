"""
API Client for Streamlit Frontend

Thin wrapper around ResearchAgent that manages session state
and provides cached access to the agent instance.
"""

from __future__ import annotations

import sys
import os

# Ensure project root is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tools.pubmed_tool import PubMedSearchTool
from services.literature_summary import LiteratureSummarizer
from agents.research_agent import ResearchAgent, ResearchReport


def get_agent(
    pubmed_email: str,
    pubmed_api_key: str,
    verify_ssl: bool,
    llm_api_base: str,
    llm_api_key: str,
    llm_model: str,
    llm_temperature: float,
    max_articles: int,
    language: str,
) -> ResearchAgent:
    """Create or return a cached ResearchAgent instance."""
    pubmed = PubMedSearchTool(
        email=pubmed_email,
        api_key=pubmed_api_key or None,
        verify_ssl=verify_ssl,
    )
    summarizer = LiteratureSummarizer(
        api_base=llm_api_base,
        api_key=llm_api_key,
        model=llm_model,
        temperature=llm_temperature,
        verify_ssl=verify_ssl,
    )
    return ResearchAgent(
        pubmed=pubmed,
        summarizer=summarizer,
        max_articles=max_articles,
        language=language,
    )


def run_research(
    agent: ResearchAgent,
    query: str,
    max_results: int,
    language: str,
) -> ResearchReport:
    """Execute a research query and return the report."""
    return agent.research(
        query=query,
        max_results=max_results,
        language=language,
    )
