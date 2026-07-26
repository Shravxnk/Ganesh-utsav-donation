"""
Ganesh Utsav 2026 — Donation Management App
============================================

Entry point. Two pages via sidebar nav:

  Collect Donation   →  Add a new entry  (default)
  Donation Records   →  View / search / export all entries

Run:
    streamlit run app.py
"""

import os

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ── Page Config (must be the first Streamlit call) ────────────────────────────
st.set_page_config(
    page_title="Ganesh Utsav 2026 — Donations",
    page_icon="🙏",
    layout="centered",
    initial_sidebar_state="auto",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
        /* Reduce top whitespace */
        .block-container { padding-top: 1.5rem; }

        /* Primary button — saffron */
        div.stButton > button[kind="primary"] {
            background-color: #FF6600 !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
        }
        div.stButton > button[kind="primary"]:hover {
            background-color: #e05500 !important;
        }

        /* Download button */
        div.stDownloadButton > button {
            background-color: #FF6600;
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            width: 100%;
        }
        div.stDownloadButton > button:hover {
            background-color: #e05500;
        }

        /* Metrics */
        [data-testid="stMetricValue"] {
            font-size: 1.1rem !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Main App ──────────────────────────────────────────────────────────────────
society_name = os.getenv("SOCIETY_NAME", "PanchJyot CHS")

with st.sidebar:
    st.markdown(
        f"""
        <div style="text-align:center; padding:0.75rem 0 1.25rem;">
            <div style="font-size:2.2rem;">🙏</div>
            <div style="font-weight:700; font-size:0.95rem; color:#FF6600; margin-top:0.25rem;">
                {society_name}
            </div>
            <div style="font-size:0.8rem; color:#888; margin-top:0.15rem;">
                Ganesh Utsav 2026
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    page = st.radio(
        "Navigation",
        ["Collect Donation", "Donation Records"],
        label_visibility="collapsed",
    )

if page == "Collect Donation":
    from views.collect_donation import show as show_collect
    show_collect()

elif page == "Donation Records":
    from views.donation_records import show as show_records
    show_records()
