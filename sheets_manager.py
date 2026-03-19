"""
================================================
Google Sheets Manager
إدارة جميع العمليات مع Google Sheets
================================================
"""

import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from typing import List, Dict, Optional, Any
import json
import traceback
from config import *


class GoogleSheetsManager:
    """
    مدير Google Sheets مع معالجة الأخطاء الكاملة
    يتعامل مع جميع العمليات: قراءة، كتابة، بحث، تحديث، حذف
    """
    
    def __init__(self, credentials_path: str, spreadsheet_id: str):
        """تهيئة الاتصال بـ Google Sheets"""
        try:
            # Check if credentials are in environment variable (Railway/Render)
            import os
            credentials_json = os.getenv('GOOGLE_CREDENTIALS')
            
            if credentials_json:
                # Parse JSON from environment
                import json
                credentials_dict = json.loads(credentials_json)
                self.creds = Credentials.from_service_account_info(
                    credentials_dict,
                    scopes=SCOPES
                )
                print("✅ Loaded credentials from environment variable")
            else:
                # Load from file (local development)
                self.creds = Credentials.from_service_account_file(
                    credentials_path,
                    scopes=SCOPES
                )
                print("✅ Loaded credentials from file")
            
            self.client = gspread.authorize(self.creds)
            self.spreadsheet = self.client.open_by_key(spreadsheet_id)
            print("✅ تم الاتصال بـ Google Sheets بنجاح")
            
        except FileNotFoundError:
            print(f"❌ ملف Credentials غير موجود: {credentials_path}")
            raise
        except Exception as e:
            print(f"❌ خطأ في الاتصال بـ Google Sheets: {e}")
            raise
    
    def get_sheet(self, sheet_name: str):
        """الحصول على ورقة عمل أو إنشائها"""
        try:
            return self.spreadsheet.worksheet(sheet_name)
        except gspread.WorksheetNotFound:
            print(f"⚠️ الورقة {sheet_name} غير موجودة. جاري الإنشاء...")
            worksheet = self.spreadsheet.add_worksheet(
                title=sheet_name,
                rows=1000,
                cols=20
            )
            self._add_headers(worksheet, sheet_name)
            print(f"✅ تم إنشاء الورقة {sheet_name}")
            return worksheet
    
    def _add_headers(self, worksheet, sheet_name: str):
        """إضافة headers للورقة الجديدة"""
        headers = {
            SHEET_PATIENTS: [
                'patient_id', 'full_name', 'phone', 'email', 
                'city', 'specialty', 'patient_status', 
                'created_at', 'updated_at', 'notes'
            ],
            SHEET_APPOINTMENTS: [
                'appointment_id', 'patient_id', 'patient_phone',
                'appointment_date', 'appointment_time', 'status',
                'doctor', 'notes', 'created_at', 'updated_at'
            ],
            SHEET_INVOICES: [
                'invoice_id', 'patient_id', 'patient_phone',
                'treatment', 'amount', 'status', 
                'created_at', 'paid_at', 'notes'
            ],
            SHEET_ERROR_LOG: [
                'timestamp', 'operation', 'error_type', 
                'error_message', 'input_data', 'stack_trace'
            ],
            SHEET_API_LOGS: [
                'timestamp', 'endpoint', 'method', 'input_data',
                'success', 'response', 'execution_time'
            ],
            SHEET_CONVERSATION_HISTORY: [
                'conversation_id', 'phone', 'role', 
                'message', 'timestamp'
            ]
        }
        
        if sheet_name in headers:
            worksheet.append_row(headers[sheet_name])
    
    def log_error(self, operation: str, error: Exception, input_data: Any = None):
        """تسجيل الأخطاء"""
        if not ENABLE_ERROR_LOGGING:
            return
            
        try:
            error_sheet = self.get_sheet(SHEET_ERROR_LOG)
            error_row = [
                datetime.now().isoformat(),
                operation,
                type(error).__name__,
                str(error),
                json.dumps(input_data, ensure_ascii=False) if input_data else '',
                traceback.format_exc()
            ]
            error_sheet.append_row(error_row)
            print(f"📝 تم تسجيل الخطأ في error_log")
        except Exception as log_error:
            print(f"⚠️ فشل تسجيل الخطأ: {log_error}")
    
    def log_api_call(self, endpoint: str, method: str, input_data: Any, 
                     success: bool, response: Any, execution_time: float):
        """تسجيل API calls"""
        if not ENABLE_API_LOGGING:
            return
            
        try:
            api_log_sheet = self.get_sheet(SHEET_API_LOGS)
            log_row = [
                datetime.now().isoformat(),
                endpoint,
                method,
                json.dumps(input_data, ensure_ascii=False) if input_data else '',
                str(success),
                json.dumps(response, ensure_ascii=False) if response else '',
                f"{execution_time:.3f}s"
            ]
            api_log_sheet.append_row(log_row)
        except Exception as log_error:
            print(f"⚠️ فشل تسجيل API call: {log_error}")
    
    def find_patient(self, identifier: str) -> Optional[Dict]:
        """البحث عن مريض"""
        try:
            patients_sheet = self.get_sheet(SHEET_PATIENTS)
            all_values = patients_sheet.get_all_values()
            
            if len(all_values) < 2:
                return None
            
            headers = all_values[0]
            
            for idx, row in enumerate(all_values[1:], start=2):
                if len(row) > 2:
                    if row[2] == identifier or (len(row) > 3 and row[3] == identifier):
                        patient_data = dict(zip(headers, row))
                        patient_data['_row_index'] = idx
                        return patient_data
            
            return None
            
        except Exception as e:
            self.log_error('find_patient', e, identifier)
            raise
    
    def get_all_patients(self, filters: Optional[Dict] = None) -> List[Dict]:
        """الحصول على قائمة المرضى مع فلترة"""
        try:
            patients_sheet = self.get_sheet(SHEET_PATIENTS)
            all_values = patients_sheet.get_all_values()
            
            if len(all_values) < 2:
                return []
            
            headers = all_values[0]
            patients = [dict(zip(headers, row)) for row in all_values[1:] if row]
            
            if filters:
                if 'city' in filters and filters['city']:
                    patients = [p for p in patients if p.get('city', '').lower() == filters['city'].lower()]
                
                if 'status' in filters and filters['status']:
                    patients = [p for p in patients if p.get('patient_status', '').lower() == filters['status'].lower()]
                
                if 'specialty' in filters and filters['specialty']:
                    patients = [p for p in patients if p.get('specialty', '').lower() == filters['specialty'].lower()]
                
                if 'name_contains' in filters and filters['name_contains']:
                    search_term = filters['name_contains'].lower()
                    patients = [p for p in patients if search_term in p.get('full_name', '').lower()]
            
            return patients
            
        except Exception as e:
            self.log_error('get_all_patients', e, filters)
            raise
    
    def check_related_data(self, patient_id: str) -> Dict[str, int]:
        """التحقق من البيانات المرتبطة"""
        related_data = {
            'appointments_count': 0,
            'invoices_count': 0
        }
        
        try:
            try:
                appointments_sheet = self.get_sheet(SHEET_APPOINTMENTS)
                appointments = appointments_sheet.get_all_values()
                related_data['appointments_count'] = sum(
                    1 for row in appointments[1:] 
                    if len(row) > 1 and row[1] == patient_id
                )
            except:
                pass
            
            try:
                invoices_sheet = self.get_sheet(SHEET_INVOICES)
                invoices = invoices_sheet.get_all_values()
                related_data['invoices_count'] = sum(
                    1 for row in invoices[1:] 
                    if len(row) > 1 and row[1] == patient_id
                )
            except:
                pass
            
            return related_data
            
        except Exception as e:
            self.log_error('check_related_data', e, patient_id)
            return related_data


    # ================================================
    # CONVERSATION MEMORY METHODS
    # ================================================
    
    def save_message(self, phone: str, role: str, message: str, conversation_id: str = None):
        """حفظ رسالة في conversation_history"""
        try:
            history_sheet = self.get_sheet(SHEET_CONVERSATION_HISTORY)
            
            if not conversation_id:
                conversation_id = phone
            
            new_row = [
                conversation_id,
                phone,
                role,
                message,
                datetime.now().isoformat()
            ]
            
            history_sheet.append_row(new_row)
            print(f"💾 Message saved: {role} - {phone}")
            
        except Exception as e:
            self.log_error('save_message', e, {
                'phone': phone,
                'role': role,
                'message': message
            })
    
    def get_conversation_history(self, phone: str, max_messages: int = 10) -> List[Dict]:
        """الحصول على آخر N رسالة للمستخدم"""
        try:
            history_sheet = self.get_sheet(SHEET_CONVERSATION_HISTORY)
            all_values = history_sheet.get_all_values()
            
            if len(all_values) < 2:
                return []
            
            headers = all_values[0]
            
            # فلترة الرسائل لهذا المستخدم
            user_messages = []
            for row in all_values[1:]:
                if len(row) > 1 and row[1] == phone:
                    message_dict = dict(zip(headers, row))
                    user_messages.append(message_dict)
            
            # آخر N رسالة
            recent_messages = user_messages[-max_messages:] if user_messages else []
            
            print(f"📖 Retrieved {len(recent_messages)} messages for {phone}")
            return recent_messages
            
        except Exception as e:
            self.log_error('get_conversation_history', e, phone)
            return []
    
    def clear_conversation_history(self, phone: str) -> int:
        """مسح تاريخ المحادثة لمستخدم معين"""
        try:
            history_sheet = self.get_sheet(SHEET_CONVERSATION_HISTORY)
            all_values = history_sheet.get_all_values()
            
            if len(all_values) < 2:
                return 0
            
            # إيجاد الصفوف المراد حذفها
            rows_to_delete = []
            for idx, row in enumerate(all_values[1:], start=2):
                if len(row) > 1 and row[1] == phone:
                    rows_to_delete.append(idx)
            
            # الحذف من الأسفل للأعلى
            deleted_count = 0
            for row_idx in sorted(rows_to_delete, reverse=True):
                history_sheet.delete_rows(row_idx)
                deleted_count += 1
            
            print(f"🗑️ Deleted {deleted_count} messages for {phone}")
            return deleted_count
            
        except Exception as e:
            self.log_error('clear_conversation_history', e, phone)
            return 0
    
    def get_all_conversations_stats(self) -> Dict:
        """إحصائيات جميع المحادثات"""
        try:
            history_sheet = self.get_sheet(SHEET_CONVERSATION_HISTORY)
            all_values = history_sheet.get_all_values()
            
            if len(all_values) < 2:
                return {
                    "total_messages": 0,
                    "total_users": 0,
                    "users": []
                }
            
            # إحصاء الرسائل لكل مستخدم
            user_stats = {}
            for row in all_values[1:]:
                if len(row) > 1:
                    phone = row[1]
                    if phone not in user_stats:
                        user_stats[phone] = {
                            "phone": phone,
                            "message_count": 0,
                            "last_message_time": None
                        }
                    user_stats[phone]["message_count"] += 1
                    if len(row) > 4:
                        user_stats[phone]["last_message_time"] = row[4]
            
            return {
                "total_messages": len(all_values) - 1,
                "total_users": len(user_stats),
                "users": list(user_stats.values())
            }
            
        except Exception as e:
            self.log_error('get_all_conversations_stats', e, None)
            return {
                "total_messages": 0,
                "total_users": 0,
                "users": []
            }


_sheets_manager_instance = None

def get_sheets_manager() -> GoogleSheetsManager:
    """Get singleton instance"""
    global _sheets_manager_instance
    if _sheets_manager_instance is None:
        _sheets_manager_instance = GoogleSheetsManager(
            GOOGLE_CREDENTIALS_PATH,
            SPREADSHEET_ID
        )
    return _sheets_manager_instance
