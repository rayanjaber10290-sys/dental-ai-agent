"""
================================================
Configuration Module
الإعدادات الأساسية للنظام
================================================
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ================================================
# GOOGLE SHEETS CONFIGURATION
# ================================================

GOOGLE_CREDENTIALS_PATH = os.getenv('GOOGLE_CREDENTIALS_PATH', 'credentials.json')
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID', '')

# Google Sheets API Scopes
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# ================================================
# LLM CONFIGURATION (Google Gemini)
# ================================================

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', '')
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')
# Available models (كلهم مجانيين):
# - gemini-1.5-flash (سريع، موصى به ⭐)
# - gemini-1.5-pro (أذكى، أبطأ شوي)
# - gemini-2.0-flash-exp (تجريبي، الأحدث)
LLM_TEMPERATURE = float(os.getenv('LLM_TEMPERATURE', '0.3'))

# ================================================
# FLASK API CONFIGURATION
# ================================================

FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

# ================================================
# GOOGLE SHEETS - SHEET NAMES
# ================================================

SHEET_PATIENTS = 'patients'
SHEET_APPOINTMENTS = 'appointments'
SHEET_INVOICES = 'invoices'
SHEET_ERROR_LOG = 'error_log'
SHEET_API_LOGS = 'api_logs'
SHEET_CONVERSATION_HISTORY = 'conversation_history'

# ================================================
# VALIDATION RULES
# ================================================

# Phone validation
PHONE_PREFIX = '+962'
PHONE_LENGTH = 13

# Patient status options
PATIENT_STATUS_OPTIONS = ['new', 'active', 'inactive', 'archived']

# Specialty options
SPECIALTY_OPTIONS = ['عام', 'تنظيف', 'تبييض', 'تقويم', 'زراعة', 'علاج عصب']

# Cities in Jordan
JORDAN_CITIES = [
    'عمان', 'إربد', 'الزرقاء', 'العقبة', 'السلط', 
    'المفرق', 'الكرك', 'معان', 'جرش', 'عجلون',
    'مادبا', 'الطفيلة'
]

# ================================================
# SYSTEM SETTINGS
# ================================================

# Logging
ENABLE_ERROR_LOGGING = True
ENABLE_API_LOGGING = True

# Agent settings
AGENT_MAX_ITERATIONS = 5
AGENT_VERBOSE = True

# Memory settings
MEMORY_MAX_MESSAGES = int(os.getenv('MEMORY_MAX_MESSAGES', '10'))
MEMORY_ENABLED = os.getenv('MEMORY_ENABLED', 'True').lower() == 'true'
