import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from agent import get_agent
from sheets_manager import get_sheets_manager

app = Flask(__name__)
CORS(app)

agent = get_agent()
sheets_manager = get_sheets_manager()

@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "running", "agent": "Dental Clinic AI"})

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        message = data.get('message')
        phone = data.get('phone')
        
        if not message or not phone:
            return jsonify({"error": "Missing data"}), 400
        
        # جلب الذاكرة
        history = sheets_manager.get_conversation_history(phone)
        chat_history = [{"role": m['role'], "content": m['message']} for m in history]
        
        # استدعاء الذكاء الاصطناعي
        response = agent.invoke({"input": message, "chat_history": chat_history})
        ai_message = response['output']
        
        # حفظ في الاكسل
        sheets_manager.save_message(phone, "user", message)
        sheets_manager.save_message(phone, "assistant", ai_message)
        
        return jsonify({"response": ai_message})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
