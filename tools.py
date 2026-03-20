"""
================================================
AI Agent Tools
الأدوات الأربعة: إضافة، تعديل، حذف، استعلام
================================================
"""

import json
from datetime import datetime
from typing import Optional
from sheets_manager import get_sheets_manager
from config import *


# ================================================
# TOOL 1: ADD PATIENT
# ================================================

def add_patient_tool(input_json: str) -> str:
    """
    إضافة مريض جديد للنظام
    
    Args:
        input_json: JSON string يحتوي على بيانات المريض
    
    Returns:
        JSON string مع النتيجة
    """
    try:
        manager = get_sheets_manager()
        data = json.loads(input_json)
        
        # التحقق من الحقول المطلوبة
        if not data.get('full_name') or not data.get('phone'):
            return json.dumps({
                "success": False,
                "error": "الاسم الكامل ورقم الهاتف مطلوبان",
                "patient_id": None
            }, ensure_ascii=False)
        
        phone = data['phone'].strip()
        full_name = data.get('full_name', '').strip()
        
        # ✅ CRITICAL: Validate name
        if len(full_name) < 2:
            return json.dumps({
                "success": False,
                "error": "الاسم يجب أن يكون حرفين على الأقل",
                "patient_id": None
            }, ensure_ascii=False)
        
        if any(char.isdigit() for char in full_name):
            return json.dumps({
                "success": False,
                "error": "الاسم لا يجب أن يحتوي على أرقام",
                "patient_id": None
            }, ensure_ascii=False)
        
        # ✅ CRITICAL: Phone normalization and validation
        # Remove spaces, dashes, parentheses
        phone_clean = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        
        # Handle different formats
        if phone_clean.startswith('00962'):
            phone_clean = '+962' + phone_clean[5:]
        elif phone_clean.startswith('962'):
            phone_clean = '+962' + phone_clean[3:]
        elif phone_clean.startswith('07'):
            phone_clean = '+962' + phone_clean[1:]
        elif not phone_clean.startswith('+962'):
            return json.dumps({
                "success": False,
                "error": "رقم الهاتف يجب أن يكون أردني (يبدأ بـ 079/078/077)",
                "patient_id": None
            }, ensure_ascii=False)
        
        # Validate final format
        if len(phone_clean) != PHONE_LENGTH:
            return json.dumps({
                "success": False,
                "error": f"رقم الهاتف يجب أن يكون {PHONE_LENGTH} رقم (مع +962)",
                "patient_id": None
            }, ensure_ascii=False)
        
        # Validate it's actually numbers after +962
        if not phone_clean[4:].isdigit():
            return json.dumps({
                "success": False,
                "error": "رقم الهاتف يجب أن يحتوي على أرقام فقط",
                "patient_id": None
            }, ensure_ascii=False)
        
        # Validate Jordanian mobile prefixes
        mobile_prefix = phone_clean[4:6]
        if mobile_prefix not in ['79', '78', '77']:
            return json.dumps({
                "success": False,
                "error": "رقم الهاتف يجب أن يبدأ بـ 079 أو 078 أو 077",
                "patient_id": None
            }, ensure_ascii=False)
        
        # ✅ CRITICAL: Check for duplicates BEFORE adding
        existing_patient = manager.find_patient(phone_clean)
        if existing_patient:
            return json.dumps({
                "success": False,
                "error": f"⚠️ المريض {existing_patient.get('full_name')} موجود مسبقاً برقم {phone_clean}",
                "patient_id": existing_patient.get('patient_id'),
                "existing_patient": {
                    "patient_id": existing_patient.get('patient_id'),
                    "full_name": existing_patient.get('full_name'),
                    "phone": existing_patient.get('phone'),
                    "city": existing_patient.get('city', 'غير محدد')
                }
            }, ensure_ascii=False)
        
        # تحضير البيانات
        patients_sheet = manager.get_sheet(SHEET_PATIENTS)
        all_values = patients_sheet.get_all_values()
        
        if len(all_values) == 0:
            headers = [
                'patient_id', 'full_name', 'phone', 'email', 
                'city', 'specialty', 'patient_status', 
                'created_at', 'updated_at', 'notes'
            ]
            patients_sheet.append_row(headers)
            all_values = [headers]
        
        # إنشاء patient_id
        patient_count = len(all_values)
        patient_id = f"P{str(patient_count).zfill(6)}"
        
        now = datetime.now().isoformat()
        city = data.get('city', 'عمان')
        specialty = data.get('specialty', 'عام')
        patient_status = data.get('patient_status', 'new')
        
        if patient_status not in PATIENT_STATUS_OPTIONS:
            patient_status = 'new'
        
        new_row = [
            patient_id,
            full_name,
            phone_clean,  # Use cleaned phone
            data.get('email', '').strip(),
            city,
            specialty,
            patient_status,
            now,
            now,
            data.get('notes', '').strip()
        ]
        
        # الإضافة
        patients_sheet.append_row(new_row)
        
        return json.dumps({
            "success": True,
            "message": f"تم إضافة المريض {full_name} بنجاح ✅",
            "patient_id": patient_id,
            "patient_data": {
                "patient_id": patient_id,
                "full_name": full_name,
                "phone": phone_clean,
                "email": data.get('email', ''),
                "city": city,
                "specialty": specialty,
                "patient_status": patient_status,
                "created_at": now
            }
        }, ensure_ascii=False)
        
    except json.JSONDecodeError as e:
        manager = get_sheets_manager()
        manager.log_error('add_patient', e, input_json)
        return json.dumps({
            "success": False,
            "error": "صيغة JSON غير صالحة",
            "patient_id": None
        }, ensure_ascii=False)
        
    except Exception as e:
        manager = get_sheets_manager()
        manager.log_error('add_patient', e, input_json)
        return json.dumps({
            "success": False,
            "error": f"خطأ في إضافة المريض: {str(e)}",
            "patient_id": None
        }, ensure_ascii=False)


# ================================================
# TOOL 2: UPDATE PATIENT
# ================================================

def update_patient_tool(input_json: str) -> str:
    """تعديل بيانات مريض موجود"""
    try:
        manager = get_sheets_manager()
        data = json.loads(input_json)
        
        if not data.get('identifier'):
            return json.dumps({
                "success": False,
                "error": "identifier مطلوب (رقم الهاتف أو البريد الإلكتروني)"
            }, ensure_ascii=False)
        
        if not data.get('updates') or not isinstance(data['updates'], dict):
            return json.dumps({
                "success": False,
                "error": "updates مطلوب ويجب أن يكون dict"
            }, ensure_ascii=False)
        
        if len(data['updates']) == 0:
            return json.dumps({
                "success": False,
                "error": "لا توجد تحديثات للتطبيق"
            }, ensure_ascii=False)
        
        identifier = data['identifier'].strip()
        updates = data['updates']
        
        # البحث عن المريض
        patient = manager.find_patient(identifier)
        
        if not patient:
            return json.dumps({
                "success": False,
                "error": f"المريض غير موجود: {identifier}"
            }, ensure_ascii=False)
        
        patient_id = patient.get('patient_id')
        row_index = patient.get('_row_index')
        
        # تحضير التحديثات
        patients_sheet = manager.get_sheet(SHEET_PATIENTS)
        all_values = patients_sheet.get_all_values()
        headers = all_values[0]
        
        current_row = list(all_values[row_index - 1])
        
        updatable_fields = [
            'full_name', 'email', 'city', 
            'specialty', 'patient_status', 'notes'
        ]
        
        updated_fields = []
        
        for field, value in updates.items():
            if field in updatable_fields and field in headers:
                col_index = headers.index(field)
                current_row[col_index] = str(value).strip()
                updated_fields.append(field)
        
        # تحديث updated_at
        if 'updated_at' in headers:
            current_row[headers.index('updated_at')] = datetime.now().isoformat()
        
        # التحديث
        cell_range = f'A{row_index}:{chr(65 + len(current_row) - 1)}{row_index}'
        patients_sheet.update(cell_range, [current_row])
        
        return json.dumps({
            "success": True,
            "message": f"تم تحديث بيانات المريض {patient.get('full_name')} بنجاح ✅",
            "patient_id": patient_id,
            "updated_fields": updated_fields,
            "updates_applied": {k: v for k, v in updates.items() if k in updated_fields}
        }, ensure_ascii=False)
        
    except json.JSONDecodeError as e:
        manager = get_sheets_manager()
        manager.log_error('update_patient', e, input_json)
        return json.dumps({
            "success": False,
            "error": "صيغة JSON غير صالحة"
        }, ensure_ascii=False)
        
    except Exception as e:
        manager = get_sheets_manager()
        manager.log_error('update_patient', e, input_json)
        return json.dumps({
            "success": False,
            "error": f"خطأ في تحديث المريض: {str(e)}"
        }, ensure_ascii=False)


# ================================================
# TOOL 3: DELETE PATIENT
# ================================================

def delete_patient_tool(input_json: str) -> str:
    """حذف مريض مع الحفاظ على السجلات"""
    try:
        manager = get_sheets_manager()
        data = json.loads(input_json)
        
        if not data.get('identifier'):
            return json.dumps({
                "success": False,
                "error": "identifier مطلوب"
            }, ensure_ascii=False)
        
        identifier = data['identifier'].strip()
        force = data.get('force', False)
        
        # البحث عن المريض
        patient = manager.find_patient(identifier)
        
        if not patient:
            return json.dumps({
                "success": False,
                "error": f"المريض غير موجود: {identifier}"
            }, ensure_ascii=False)
        
        patient_id = patient.get('patient_id')
        patient_name = patient.get('full_name')
        row_index = patient.get('_row_index')
        
        # فحص البيانات المرتبطة
        related_data = manager.check_related_data(patient_id)
        warnings = []
        
        if related_data['appointments_count'] > 0:
            warnings.append(f"{related_data['appointments_count']} مواعيد مرتبطة")
        
        if related_data['invoices_count'] > 0:
            warnings.append(f"{related_data['invoices_count']} فواتير مرتبطة")
        
        if warnings and not force:
            return json.dumps({
                "success": False,
                "error": "لا يمكن حذف مريض لديه بيانات مرتبطة",
                "warnings": warnings,
                "patient_id": patient_id,
                "message": "استخدم force=true للحذف رغم البيانات المرتبطة"
            }, ensure_ascii=False)
        
        # الحذف
        patients_sheet = manager.get_sheet(SHEET_PATIENTS)
        patients_sheet.delete_rows(row_index)
        
        result = {
            "success": True,
            "message": f"تم حذف المريض {patient_name} بنجاح ✅",
            "patient_id": patient_id,
            "deleted_row": row_index
        }
        
        if warnings:
            result["warnings"] = warnings
            result["note"] = "البيانات المرتبطة لم تُحذف"
        
        return json.dumps(result, ensure_ascii=False)
        
    except json.JSONDecodeError as e:
        manager = get_sheets_manager()
        manager.log_error('delete_patient', e, input_json)
        return json.dumps({
            "success": False,
            "error": "صيغة JSON غير صالحة"
        }, ensure_ascii=False)
        
    except Exception as e:
        manager = get_sheets_manager()
        manager.log_error('delete_patient', e, input_json)
        return json.dumps({
            "success": False,
            "error": f"خطأ في حذف المريض: {str(e)}"
        }, ensure_ascii=False)


# ================================================
# TOOL 4: GET PATIENT INFO
# ================================================

def get_patient_info_tool(input_json: str) -> str:
    """عرض معلومات مريض أو قائمة مرضى"""
    try:
        manager = get_sheets_manager()
        data = json.loads(input_json)
        
        action = data.get('action', 'get_all')
        
        # الحصول على مريض واحد
        if action == 'get_one':
            identifier = data.get('identifier')
            
            if not identifier:
                return json.dumps({
                    "success": False,
                    "error": "identifier مطلوب لعملية get_one"
                }, ensure_ascii=False)
            
            patient = manager.find_patient(identifier.strip())
            
            if not patient:
                return json.dumps({
                    "success": False,
                    "error": f"المريض غير موجود: {identifier}"
                }, ensure_ascii=False)
            
            if '_row_index' in patient:
                del patient['_row_index']
            
            return json.dumps({
                "success": True,
                "count": 1,
                "patient": patient
            }, ensure_ascii=False)
        
        # الحصول على جميع المرضى أو بحث
        filters = data.get('filters', {})
        patients = manager.get_all_patients(filters)
        
        for patient in patients:
            if '_row_index' in patient:
                del patient['_row_index']
        
        return json.dumps({
            "success": True,
            "count": len(patients),
            "patients": patients,
            "filters_applied": filters if filters else None
        }, ensure_ascii=False)
        
    except json.JSONDecodeError as e:
        manager = get_sheets_manager()
        manager.log_error('get_patient_info', e, input_json)
        return json.dumps({
            "success": False,
            "error": "صيغة JSON غير صالحة"
        }, ensure_ascii=False)
        
    except Exception as e:
        manager = get_sheets_manager()
        manager.log_error('get_patient_info', e, input_json)
        return json.dumps({
            "success": False,
            "error": f"خطأ في الاستعلام: {str(e)}"
        }, ensure_ascii=False)
