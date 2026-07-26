"""
Excel manager for donation records.

All donation data lives in a single file: donations.xlsx
This module handles reading, writing, and querying that file.
"""

import os

import pandas as pd
from openpyxl import Workbook

EXCEL_FILE = "donations.xlsx"

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

def _init_excel() -> None:
    """Create donations.xlsx with the correct headers if it doesn't exist."""
    if not os.path.exists(EXCEL_FILE):
        wb = Workbook()
        ws = wb.active
        ws.title = "Donations"
        ws.append(COLUMNS)
        wb.save(EXCEL_FILE)


def _read_excel() -> pd.DataFrame:
    """Read the Excel file, returning an empty DataFrame on any error."""
    try:
        df = pd.read_excel(EXCEL_FILE)
    except Exception:
        return pd.DataFrame(columns=COLUMNS)

    if "ID" not in df.columns:
        # Older file saved before the ID column existed — backfill it.
        df.insert(0, "ID", range(1, len(df) + 1))
        df.to_excel(EXCEL_FILE, index=False)

    return df


def _write_excel(df: pd.DataFrame) -> None:
    """
    Persist a DataFrame to donations.xlsx, sorted by ID and renumbered
    sequentially (1, 2, 3, ...) so gaps left by deleted rows are closed.
    """
    df = df.sort_values("ID").reset_index(drop=True)
    df["ID"] = range(1, len(df) + 1)
    df.to_excel(EXCEL_FILE, index=False, columns=COLUMNS)


# ── Public API ────────────────────────────────────────────────────────────────

def save_donation(data: dict) -> None:
    """
    Append a single donation record to donations.xlsx.

    Args:
        data: A dict whose keys match COLUMNS exactly, except "ID"
              which is assigned automatically.
    """
    _init_excel()
    existing = _read_excel()

    next_id = int(existing["ID"].max()) + 1 if not existing.empty else 1
    new_row = pd.DataFrame([{**data, "ID": next_id}], columns=COLUMNS)

    updated = pd.concat([existing, new_row], ignore_index=True)
    _write_excel(updated)


def get_all_donations() -> pd.DataFrame:
    """Return all donation records as a DataFrame."""
    _init_excel()
    return _read_excel()


def save_all_donations(df: pd.DataFrame) -> None:
    """
    Overwrite the full donations table (used after inline edits/deletes
    made in the Donation Records page).
    """
    _init_excel()
    _write_excel(df)
