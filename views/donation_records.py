"""
Donation Records view.

Displays summary statistics, a searchable + editable table of all
donations (edit cells or delete rows inline), and an Excel export button.
"""

import io

import pandas as pd
import streamlit as st

from utils.sheets_manager import COLUMNS, get_all_donations, save_all_donations

FOOD_RATE = 100  # Rs. per member


def show() -> None:
    """Render the Donation Records page."""

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown(
        """
        <div style="padding:0.5rem 0 0.25rem;">
            <h2 style="color:#FF6600; margin-bottom:0.15rem;">Donation Records</h2>
            <p style="color:#777; margin:0; font-size:1rem;">Ganesh Utsav 2026</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()

    df = get_all_donations()

    if df.empty:
        st.info("No donations recorded yet. Start collecting donations!")
        return

    # Normalise types
    for col in ["Donation Amount", "Food Amount", "Total Amount", "Food Members"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    # ── Summary Metrics ───────────────────────────────────────────────────────
    total_collection = df["Total Amount"].sum()
    total_count       = len(df)
    cash_total        = df.loc[df["Payment Mode"] == "Cash", "Total Amount"].sum()
    upi_total         = df.loc[df["Payment Mode"] == "UPI",  "Total Amount"].sum()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Collection", f"Rs.{total_collection:,}")
    c2.metric("No. of Entries",   total_count)
    c3.metric("Cash Total",       f"Rs.{cash_total:,}")
    c4.metric("UPI Total",        f"Rs.{upi_total:,}")

    st.markdown("---")

    # ── Search ────────────────────────────────────────────────────────────────
    search = st.text_input(
        "Search",
        placeholder="Name / Building No. / Flat No.",
        label_visibility="collapsed",
    )

    if search.strip():
        q = search.strip()
        mask = (
            df["Name"].astype(str).str.contains(q, case=False, na=False)
            | df["Building No"].astype(str).str.contains(q, case=False, na=False)
            | df["Flat No"].astype(str).str.contains(q, case=False, na=False)
        )
        filtered = df[mask]
    else:
        filtered = df

    st.caption(
        f"{len(filtered)} record(s) found — edit a cell to update it, or use the "
        "row checkbox + trash icon to delete an entry."
    )

    # Show most recent donations first
    display_df = filtered.iloc[::-1].reset_index(drop=True)

    # ── Editable Table ────────────────────────────────────────────────────────
    edited_df = st.data_editor(
        display_df,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        key="donations_editor",
        column_config={
            "ID": st.column_config.NumberColumn("ID", disabled=True),
            "Food Amount": st.column_config.NumberColumn(
                "Food (Rs.)", disabled=True, help="Auto-calculated: Members x Rs.100"
            ),
            "Total Amount": st.column_config.NumberColumn(
                "Total (Rs.)", disabled=True, help="Auto-calculated: Donation + Food"
            ),
            "Donation Amount": st.column_config.NumberColumn("Donation (Rs.)", min_value=0),
            "Food Members": st.column_config.NumberColumn("Food Members", min_value=0),
        },
    )

    if st.button("Save Changes", type="primary", use_container_width=True):
        _save_edits(df, display_df)

    # ── Export ────────────────────────────────────────────────────────────────
    st.markdown("---")
    st.download_button(
        label="Export to Excel",
        data=_to_excel_bytes(filtered),
        file_name="donations_export.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )


# ── Internal helpers ──────────────────────────────────────────────────────────

def _save_edits(full_df: pd.DataFrame, shown_df: pd.DataFrame) -> None:
    """
    Apply the pending edits/deletions/additions tracked by the data_editor
    widget (via its session_state diff) back into the full dataset, keyed
    by ID. Using the widget's own diff — rather than comparing dataframes —
    avoids mismatches when a row's ID is missing/duplicated.
    """
    diff = st.session_state.get("donations_editor", {})
    edited_rows = diff.get("edited_rows", {})
    added_rows = diff.get("added_rows", [])
    deleted_positions = diff.get("deleted_rows", [])

    full = full_df.set_index("ID", drop=False)

    # Deletions — by row ID, resolved from the on-screen position
    delete_ids = {shown_df.iloc[pos]["ID"] for pos in deleted_positions}
    full = full[~full["ID"].isin(delete_ids)]

    # Cell edits — by row ID, resolved from the on-screen position
    for pos, changes in edited_rows.items():
        row_id = shown_df.iloc[int(pos)]["ID"]
        if row_id in full.index:
            for col, val in changes.items():
                full.loc[row_id, col] = val

    full = full.reset_index(drop=True)

    # New rows added via the "+" row at the bottom of the editor
    next_id = int(full_df["ID"].max()) + 1 if not full_df.empty else 1
    new_rows = []
    for blank_row in added_rows:
        row = {col: blank_row.get(col, "") for col in COLUMNS}
        row["ID"] = next_id
        next_id += 1
        new_rows.append(row)

    if new_rows:
        full = pd.concat([full, pd.DataFrame(new_rows)], ignore_index=True)

    # Recompute derived amounts from source-of-truth inputs for every row
    full["Donation Amount"] = pd.to_numeric(full["Donation Amount"], errors="coerce").fillna(0).astype(int)
    full["Food Members"] = pd.to_numeric(full["Food Members"], errors="coerce").fillna(0).astype(int)
    full["Food Amount"] = full["Food Members"] * FOOD_RATE
    full["Total Amount"] = full["Donation Amount"] + full["Food Amount"]

    save_all_donations(full[COLUMNS])

    # Clear the widget's cached diff so a stale delete/edit can't resurface
    # (or get reapplied to the wrong row) on the next rerun.
    st.session_state.pop("donations_editor", None)

    st.success("Changes saved.")
    st.rerun()


def _to_excel_bytes(df: pd.DataFrame) -> bytes:
    """Serialise a DataFrame to an in-memory Excel file and return raw bytes."""
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Donations")
    return buf.getvalue()
