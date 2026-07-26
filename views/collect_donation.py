"""
Collect Donation view.

Renders the donation form and saves each submission to Excel.
Warns with a confirmation popup if a matching entry already exists.
"""

import os
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

from utils.excel_manager import get_all_donations, save_donation

load_dotenv()

FOOD_RATE = 100  # Rs. per member

SOCIETY_NAME = os.getenv("SOCIETY_NAME", "PanchJyot CHS")

BUILDING_OPTIONS = ["G-27", "H-23", "F-24", "E-25", "E-26", "Other"]
FLAT_OPTIONS = [f"{floor}/{unit}" for floor in range(0, 4) for unit in range(1, 5)] + ["Other"]


def show() -> None:
    """Render the Collect Donation page."""

    # ── Page Header ───────────────────────────────────────────────────────────
    st.markdown(
        f"""
        <div style="text-align:center; padding:0.5rem 0 0.25rem;">
            <h2 style="color:#FF6600; margin-bottom:0.15rem;">{SOCIETY_NAME}</h2>
            <p style="color:#777; margin:0; font-size:1rem;">
                Ganesh Utsav 2026 &mdash; Donation Collection
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()

    # ── Donation Form ─────────────────────────────────────────────────────────
    with st.form("donation_form", clear_on_submit=True):
        st.subheader("Donor Details")

        col_left, col_right = st.columns(2)

        with col_left:
            donor_name = st.text_input(
                "Name *",
                placeholder="Full name",
            )
            building_choice = st.selectbox(
                "Building No. *",
                BUILDING_OPTIONS,
            )
            payment_mode = st.selectbox(
                "Cash or UPI *",
                ["Cash", "UPI"],
            )

        with col_right:
            flat_choice = st.selectbox(
                "Flat No. *",
                FLAT_OPTIONS,
            )
            amount = st.number_input(
                "Donation Amount (Rs.) *",
                min_value=0,
                step=100,
                value=0,
            )
            food_members = st.number_input(
                "Members for Food",
                min_value=0,
                step=1,
                value=0,
                help=f"Charged at Rs.{FOOD_RATE} per member",
            )

        submitted = st.form_submit_button(
            "Save Donation",
            use_container_width=True,
            type="primary",
        )

    # ── Process Submission ────────────────────────────────────────────────────
    if submitted:
        _process(
            donor_name,
            building_choice,
            flat_choice,
            payment_mode,
            amount,
            food_members,
        )

    # If the last submission looked like a duplicate, show the confirm popup.
    if st.session_state.get("pending_donation"):
        _confirm_duplicate(st.session_state["pending_donation"])


# ── Internal helpers ──────────────────────────────────────────────────────────

def _process(
    donor_name: str,
    building_no: str,
    flat_no: str,
    payment_mode: str,
    amount: int,
    food_members: int,
) -> None:
    """Validate inputs, compute food charge, and save (or flag as a possible duplicate)."""

    errors: list[str] = []

    if not donor_name.strip():
        errors.append("Name is required.")

    if amount <= 0 and food_members <= 0:
        errors.append("Enter a Donation Amount or Members for Food.")

    if errors:
        for err in errors:
            st.error(err)
        return

    food_amount = int(food_members) * FOOD_RATE
    total_amount = int(amount) + food_amount

    donation = {
        "Date & Time":      datetime.now().strftime("%d-%m-%Y %I:%M %p"),
        "Name":             donor_name.strip(),
        "Building No":      building_no,
        "Flat No":          flat_no,
        "Payment Mode":     payment_mode,
        "Donation Amount":  int(amount),
        "Food Members":     int(food_members),
        "Food Amount":      food_amount,
        "Total Amount":     total_amount,
    }

    if _is_duplicate(donation):
        st.session_state["pending_donation"] = donation
        return

    save_donation(donation)
    _show_success(donation)


def _is_duplicate(donation: dict) -> bool:
    """A record with the same Building No and Flat No already exists."""
    existing = get_all_donations()
    if existing.empty:
        return False

    match = (
        existing["Building No"].astype(str) == donation["Building No"]
    ) & (
        existing["Flat No"].astype(str) == donation["Flat No"]
    )
    return bool(match.any())


@st.dialog("Possible Duplicate Entry")
def _confirm_duplicate(donation: dict) -> None:
    st.warning(
        f"Building **{donation['Building No']}**, Flat **{donation['Flat No']}** "
        "already has an entry recorded.\n\n"
        "Do you still want to add this as a new entry?"
    )

    col1, col2 = st.columns(2)
    if col1.button("Save Anyway", type="primary", use_container_width=True):
        save_donation(donation)
        st.session_state.pop("pending_donation", None)
        st.rerun()

    if col2.button("Cancel", use_container_width=True):
        st.session_state.pop("pending_donation", None)
        st.rerun()


def _show_success(donation: dict) -> None:
    st.success("Donation saved successfully!")

    c1, c2, c3 = st.columns(3)
    c1.metric("Donation", f"Rs.{donation['Donation Amount']:,}")
    c2.metric("Food Charge", f"Rs.{donation['Food Amount']:,}")
    c3.metric("Total", f"Rs.{donation['Total Amount']:,}")

    st.info(
        f"**{donation['Name']}**  |  "
        f"Building {donation['Building No']} — Flat {donation['Flat No']}  |  "
        f"{donation['Payment Mode']}"
    )
