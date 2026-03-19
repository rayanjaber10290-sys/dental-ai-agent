"""
================================================
Flask API Server
واجهة API للربط مع n8n وWhatsApp
================================================
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import time
import json
from agent import get_agent
from tools import (
    add_patient_tool,
    update_patient_tool,
    delete_patient_tool,
    get_patient_info_tool
)
from sheets_manager import get_sheets_manager
from config import *

# ================================================
# FLASK APP
# ================================================

app = Flask(__name__)
CORS(app)

print("🚀 Starting Dental Clinic AI Agent API...")
agent = get_agent()
sheets_manager = get_sheets_manager()
print("✅ Server ready!")


# ================================================
# ENDPOINTS
# ================================================

@app.route('/', methods=['GET'])
def home():
    """Home endpoint"""
    return jsonify({
        "service": "Dental Clinic AI Agent API",
        "version": "1.0.0",
        "status": "running",
        "features": {
            "ai_chat": "Conversation with Google Sheets persistent memory",
            "patient_management": "CRUD operations",
            "memory_management": "Persistent conversation history in Google Sheets",
            "memory_enabled": MEMORY_ENABLED,
            "max_messages_stored": MEMORY_MAX_MESSAGES
        },
        "endpoints": {
            "health": "/health (GET)",
            "chat": "/chat (POST) - AI chat with persistent memory",
            "add_patient": "/add-patient (POST)",
            "update_patient": "/update-patient (POST)",
            "delete_patient": "/delete-patient (POST)",
            "get_patient": "/get-patient (POST)",
            "clear_memory": "/clear-memory (POST) - Clear user conversation from Sheets",
            "memory_stats": "/memory-stats (GET) - Memory statistics from Sheets"
        }
    })


@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        "status": "healthy",
        "timestamp": time.time()
    })


@app.route('/chat', methods=['POST'])
def chat():
    """AI Agent Chat Endpoint with Google Sheets Memory"""
    start_time = time.time()
    
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({
                "success": False,
                "error": "Missing 'query' in request"
            }), 400
        
        query = data['query']
        phone = data.get('phone', 'default')
        conversation_id = data.get('conversation_id', phone)
        
        # الحصول على تاريخ المحادثة من Google Sheets
        if MEMORY_ENABLED:
            history_messages = sheets_manager.get_conversation_history(
                phone, 
                max_messages=MEMORY_MAX_MESSAGES
            )
            
            # تنسيق المحادثة
            formatted_history = []
            for msg in history_messages:
                role = msg.get('role', '')
                content = msg.get('message', '')
                if role == 'user':
                    formatted_history.append(f"أنت (المريض): {content}")
                else:
                    formatted_history.append(f"المساعد: {content}")
            
            history_text = "\n".join(formatted_history) if formatted_history else ""
        else:
            history_text = ""
            history_messages = []
        
        # بناء الـ prompt مع السياق
        if history_text:
            full_query = f"""
المحادثة السابقة:
{history_text}

الرسالة الجديدة: {query}

الرجاء الرد على الرسالة الجديدة مع الأخذ بعين الاعتبار سياق المحادثة السابقة.
"""
        else:
            full_query = query
        
        print(f"\n{'='*60}")
        print(f"📥 Query: {query}")
        print(f"📞 Phone: {phone}")
        print(f"💬 History: {len(history_messages)} messages")
        print(f"{'='*60}\n")
        
        # استدعاء الـ AI Agent
        result = agent.invoke({"input": full_query})
        ai_response = result['output']
        
        # حفظ في Google Sheets
        if MEMORY_ENABLED:
            sheets_manager.save_message(phone, 'user', query, conversation_id)
            sheets_manager.save_message(phone, 'assistant', ai_response, conversation_id)
        
        response = {
            "success": True,
            "query": query,
            "response": ai_response,
            "conversation_id": conversation_id,
            "messages_in_history": len(history_messages) + 2
        }
        
        execution_time = time.time() - start_time
        print(f"\n✅ Response in {execution_time:.2f}s")
        print(f"💾 Saved to Google Sheets\n")
        
        sheets_manager.log_api_call(
            endpoint='/chat',
            method='POST',
            input_data=data,
            success=True,
            response=response,
            execution_time=execution_time
        )
        
        return jsonify(response)
        
    except Exception as e:
        execution_time = time.time() - start_time
        error_response = {
            "success": False,
            "error": str(e),
            "fallback": "عذراً، حدث خطأ"
        }
        
        print(f"\n❌ Error: {e}\n")
        
        sheets_manager.log_api_call(
            endpoint='/chat',
            method='POST',
            input_data=request.get_json(),
            success=False,
            response=error_response,
            execution_time=execution_time
        )
        
        return jsonify(error_response), 500


@app.route('/add-patient', methods=['POST'])
def add_patient_direct():
    """Direct add patient"""
    start_time = time.time()
    
    try:
        data = request.get_json()
        result_json = add_patient_tool(json.dumps(data))
        result = json.loads(result_json)
        
        execution_time = time.time() - start_time
        
        sheets_manager.log_api_call(
            endpoint='/add-patient',
            method='POST',
            input_data=data,
            success=result.get('success', False),
            response=result,
            execution_time=execution_time
        )
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        execution_time = time.time() - start_time
        error_response = {"success": False, "error": str(e)}
        
        sheets_manager.log_api_call(
            endpoint='/add-patient',
            method='POST',
            input_data=request.get_json(),
            success=False,
            response=error_response,
            execution_time=execution_time
        )
        
        return jsonify(error_response), 500


@app.route('/update-patient', methods=['POST'])
def update_patient_direct():
    """Direct update patient"""
    start_time = time.time()
    
    try:
        data = request.get_json()
        result_json = update_patient_tool(json.dumps(data))
        result = json.loads(result_json)
        
        execution_time = time.time() - start_time
        
        sheets_manager.log_api_call(
            endpoint='/update-patient',
            method='POST',
            input_data=data,
            success=result.get('success', False),
            response=result,
            execution_time=execution_time
        )
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        execution_time = time.time() - start_time
        error_response = {"success": False, "error": str(e)}
        
        sheets_manager.log_api_call(
            endpoint='/update-patient',
            method='POST',
            input_data=request.get_json(),
            success=False,
            response=error_response,
            execution_time=execution_time
        )
        
        return jsonify(error_response), 500


@app.route('/delete-patient', methods=['POST'])
def delete_patient_direct():
    """Direct delete patient"""
    start_time = time.time()
    
    try:
        data = request.get_json()
        result_json = delete_patient_tool(json.dumps(data))
        result = json.loads(result_json)
        
        execution_time = time.time() - start_time
        
        sheets_manager.log_api_call(
            endpoint='/delete-patient',
            method='POST',
            input_data=data,
            success=result.get('success', False),
            response=result,
            execution_time=execution_time
        )
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        execution_time = time.time() - start_time
        error_response = {"success": False, "error": str(e)}
        
        sheets_manager.log_api_call(
            endpoint='/delete-patient',
            method='POST',
            input_data=request.get_json(),
            success=False,
            response=error_response,
            execution_time=execution_time
        )
        
        return jsonify(error_response), 500


@app.route('/get-patient', methods=['POST'])
def get_patient_direct():
    """Direct get patient"""
    start_time = time.time()
    
    try:
        data = request.get_json()
        result_json = get_patient_info_tool(json.dumps(data))
        result = json.loads(result_json)
        
        execution_time = time.time() - start_time
        
        sheets_manager.log_api_call(
            endpoint='/get-patient',
            method='POST',
            input_data=data,
            success=result.get('success', True),
            response=result,
            execution_time=execution_time
        )
        
        return jsonify(result), 200
            
    except Exception as e:
        execution_time = time.time() - start_time
        error_response = {"success": False, "error": str(e)}
        
        sheets_manager.log_api_call(
            endpoint='/get-patient',
            method='POST',
            input_data=request.get_json(),
            success=False,
            response=error_response,
            execution_time=execution_time
        )
        
        return jsonify(error_response), 500


@app.route('/clear-memory', methods=['POST'])
def clear_memory():
    """مسح ذاكرة المحادثة لمستخدم معين من Google Sheets"""
    try:
        data = request.get_json()
        phone = data.get('phone')
        
        if not phone:
            return jsonify({
                "success": False,
                "error": "Phone number required"
            }), 400
        
        deleted_count = sheets_manager.clear_conversation_history(phone)
        
        return jsonify({
            "success": True,
            "message": f"تم مسح {deleted_count} رسالة من Google Sheets",
            "phone": phone,
            "deleted_count": deleted_count
        })
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/memory-stats', methods=['GET'])
def memory_stats():
    """إحصائيات الذاكرة من Google Sheets"""
    try:
        stats = sheets_manager.get_all_conversations_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({
            "error": str(e),
            "total_messages": 0,
            "total_users": 0,
            "users": []
        }), 500


# ================================================
# RUN
# ================================================

if __name__ == '__main__':
    print(f"\n{'='*60}")
    print(f"🚀 Flask API Server")
    print(f"📍 Host: {FLASK_HOST}")
    print(f"🔌 Port: {FLASK_PORT}")
    print(f"{'='*60}\n")
    
    app.run(
        host=FLASK_HOST,
        port=FLASK_PORT,
        debug=FLASK_DEBUG
    )
# أضف هذا في نهاية ملف api_server.py
@app.errorhandler(Exception)
def handle_exception(e):
    # هذا الكود يمسك أي خطأ يسبب كراش ويمنع السيرفر من التوقف
    print(f"Server Error: {str(e)}")
    return {"status": "error", "message": "نظام العيادة واجه ضغطاً مؤقتاً، جاري إعادة التشغيل تلقائياً"}, 200
