import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from typing import List, Dict, Optional, Any
import json
import os
from config import *

class GoogleSheetsManager:
    def __init__(self, credentials_path: str, spreadsheet_id: str):
        try:
            creds_json = os.environ.get("GOOGLE_CREDENTIALS")
            if creds_json:
                info = json.loads(creds_json)
                self.creds = Credentials.from_service_account_info(info, scopes=SCOPES)
                print("✅ Connected to Google Sheets via Environment Variables")
            else:
                self.creds = Credentials.from_service_account_file(credentials_path, scopes=SCOPES)
                print("✅ Connected to Google Sheets via local file")
                
            self.client = gspread.authorize(self.creds)
            self.spreadsheet = self.client.open_by_key(spreadsheet_id)
        except Exception as e:
            print(f"❌ Connection Error: {e}")
            raise

    def get_sheet(self, sheet_name: str):
        try:
            return self.spreadsheet.worksheet(sheet_name)
        except gspread.WorksheetNotFound:
            worksheet = self.spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=20)
            self._add_headers(worksheet, sheet_name)
            return worksheet

    def _add_headers(self, worksheet, sheet_name: str):
        headers = {
            SHEET_PATIENTS: ['patient_id', 'full_name', 'phone', 'email', 'city', 'specialty', 'patient_status', 'created_at', 'updated_at', 'notes'],
            SHEET_APPOINTMENTS: ['appointment_id', 'patient_id', 'patient_phone', 'appointment_date', 'appointment_time', 'status', 'doctor', 'notes', 'created_at', 'updated_at'],
            SHEET_CONVERSATION_HISTORY: ['conversation_id', 'phone', 'role', 'message', 'timestamp'],
            SHEET_ERROR_LOG: ['timestamp', 'operation', 'error_type', 'error_message', 'input_data', 'stack_trace']
        }
        if sheet_name in headers:
            worksheet.append_row(headers[sheet_name])

    def save_message(self, phone: str, role: str, message: str):
        try:
            history_sheet = self.get_sheet(SHEET_CONVERSATION_HISTORY)
            history_sheet.append_row([phone, phone, role, message, datetime.now().isoformat()])
        except Exception as e:
            print(f"⚠️ Error saving message: {e}")

    def get_conversation_history(self, phone: str, max_messages: int = 10):
        try:
            history_sheet = self.get_sheet(SHEET_CONVERSATION_HISTORY)
            all_values = history_sheet.get_all_values()
            if len(all_values) < 2: return []
            headers = all_values[0]
            user_messages = [dict(zip(headers, row)) for row in all_values[1:] if len(row) > 1 and row[1] == phone]
            return user_messages[-max_messages:]
        except: return []

_sheets_manager_instance = None
def get_sheets_manager() -> GoogleSheetsManager:
    global _sheets_manager_instance
    if _sheets_manager_instance is None:
        _sheets_manager_instance = GoogleSheetsManager(GOOGLE_CREDENTIALS_PATH, SPREADSHEET_ID)
    return _sheets_manager_instance
