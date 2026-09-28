"""
pytest configuration and fixtures
"""

import os
import sys

import pytest

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def sample_financial_text():
    return """
    ACME CORPORATION Q3 FINANCIAL DISCLOSURE REPORT

    Executive Summary:
    Acme Corporation reports total gross revenue of $45.2 million for Q3 2026.
    This report has been prepared by the internal finance team.
    """


@pytest.fixture
def sample_esg_text():
    return """
    GLOBAL SUSTAINABILITY & ESG INITIATIVES REPORT 2026

    At EcoCorp, we are committed to a green initiative and a sustainable future.
    We are proud to announce our official commitment to achieve net-zero carbon emissions by 2040.
    """


@pytest.fixture
def sample_legal_text():
    return """
    MASTER SERVICES AGREEMENT

    This Agreement is entered into between Alpha Technologies ("Provider") and Beta Enterprises ("Client").
    1. Scope of Services: Provider shall deliver software development services.
    2. Confidentiality: Both parties agree to protect confidential information.
    """
