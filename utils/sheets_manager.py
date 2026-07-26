"""
Google Sheets manager for donation records.

All donation data lives in a Google Sheet, so records persist across
Streamlit Cloud restarts/redeploys (unlike a local donations.xlsx).
Reads/writes go through gspread, authenticated with a service account
configured in st.secrets.
"""

import gspread
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]

WORKSHEET_NAME = "Donations"

COLUMNS = [
    "ID",
    "Date & Time",
    "Name",
    "Building No",
    "Flat No",
    "Payment Mode",
    "Donation Amount",
    "Food Members",
    "Food Amount",
    "Total Amount",
]


# ── Internals ─────────────────────────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def _get_worksheet():
    """Open (creating if needed) the Donations worksheet. Cached for the app's lifetime."""
    creds = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]), scopes=SCOPES
    )
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(st.secrets["sheets"]["spreadsheet_id"])

    try:
        ws = spreadsheet.worksheet(WORKSHEET_NAME)
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(WORKSHEET_NAME, rows=1000, cols=len(COLUMNS))
        ws.append_row(COLUMNS)

    return ws


def _read_all() -> pd.DataFrame:
    """Read every row, returning an empty (but correctly-shaped) DataFrame if none exist."""
    records = _get_worksheet().get_all_records()
    if not records:
        return pd.DataFrame(columns=COLUMNS)

    df = pd.DataFrame(records)
    if "ID" not in df.columns:
        df.insert(0, "ID", range(1, len(df) + 1))

    return df[COLUMNS]


def _write_all(df: pd.DataFrame) -> None:
    """
    Overwrite the sheet with a DataFrame, sorted by ID and renumbered
    sequentially (1, 2, 3, ...) so gaps left by deleted rows are closed.
    """
    df = df.sort_values("ID").reset_index(drop=True)
    df["ID"] = range(1, len(df) + 1)

    ws = _get_worksheet()
    ws.clear()
    ws.append_row(COLUMNS)
    if not df.empty:
        ws.append_rows(df[COLUMNS].astype(object).values.tolist())


# ── Public API ────────────────────────────────────────────────────────────────

def save_donation(data: dict) -> None:
    """
    Append a single donation record to the sheet.

    Args:
        data: A dict whose keys match COLUMNS exactly, except "ID"
              which is assigned automatically.
    """
    existing = _read_all()
    next_id = int(existing["ID"].max()) + 1 if not existing.empty else 1
    row = {**data, "ID": next_id}
    _get_worksheet().append_row([row[c] for c in COLUMNS])


def get_all_donations() -> pd.DataFrame:
    """Return all donation records as a DataFrame."""
    return _read_all()


def save_all_donations(df: pd.DataFrame) -> None:
    """
    Overwrite the full donations table (used after inline edits/deletes
    made in the Donation Records page).
    """
    _write_all(df)
