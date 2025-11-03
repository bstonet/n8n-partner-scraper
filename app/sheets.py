import os
import json
from typing import Dict

import gspread
from google.oauth2.service_account import Credentials


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def _gspread_client():
    raw = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not raw:
        raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON not set")
    data = json.loads(raw)
    creds = Credentials.from_service_account_info(data, scopes=SCOPES)
    return gspread.authorize(creds)


def _open_sheet(spreadsheet_id: str):
    gc = _gspread_client()
    return gc.open_by_key(spreadsheet_id)


def ensure_tabs(sh, names=("Enterprise", "MidMarket", "SMB")):
    existing = {ws.title for ws in sh.worksheets()}
    for n in names:
        if n not in existing:
            sh.add_worksheet(title=n, rows=100, cols=20)


def append_row(sheet_name: str, row: Dict):
    spreadsheet_id = os.getenv("SHEETS_SPREADSHEET_ID")
    if not spreadsheet_id:
        raise RuntimeError("SHEETS_SPREADSHEET_ID not set")
    sh = _open_sheet(spreadsheet_id)
    ensure_tabs(sh)
    ws = sh.worksheet(sheet_name)
    # Column order
    values = [
        row.get("timestamp", ""),
        row.get("name", ""),
        row.get("domain", ""),
        row.get("size_signals", 0),
        row.get("enterprise_security", 0),
        row.get("tech_stack", 0),
        row.get("regulated_verticals", 0),
        row.get("delivery_maturity", 0),
        row.get("marketing_assets", 0),
        row.get("score_total", 0),
        row.get("tier", ""),
        row.get("sources", ""),
    ]
    ws.append_row(values, value_input_option="USER_ENTERED")


