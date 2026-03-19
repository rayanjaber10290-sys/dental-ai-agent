# 🏥 Dental Clinic AI Agent

نظام ذكي لإدارة بيانات المرضى في عيادة أسنان باستخدام AI Agent مع Google Gemini و Google Sheets Persistent Memory.

## ✨ المميزات

- 🤖 AI Agent ذكي يفهم اللغة الطبيعية العربية (Google Gemini)
- 💾 **Persistent Memory** - المحادثات محفوظة دائماً في Google Sheets
- 📊 تكامل كامل مع Google Sheets
- 🔧 4 أدوات: إضافة، تعديل، حذف، استعلام
- 🌐 Flask API للربط مع n8n و WhatsApp
- 📝 تسجيل تلقائي للأخطاء والعمليات
- ✅ معالجة متقدمة للأخطاء
- 🧠 يتذكر آخر 10 رسائل لكل مستخدم
- 🚫 لا يجيب على الأسئلة الطبية (يحول للعيادة)

## 📋 المتطلبات

- Python 3.8+
- Google Cloud Project مع Sheets API مفعّل
- Google Gemini API Key (مجاني)
- n8n (اختياري للربط مع WhatsApp)

## 🚀 التنصيب على Replit

### 1. إنشاء Repl

1. روح على https://replit.com
2. Create Repl → Python
3. Title: dental-ai-agent

### 2. رفع الملفات

Upload جميع الملفات:
- config.py
- sheets_manager.py
- tools.py
- agent.py
- api_server.py
- requirements.txt
- .env.example
- README.md
- credentials.json (من Google Cloud)

### 3. إعداد Secrets

في Replit → Secrets (🔒):

```
GOOGLE_CREDENTIALS_PATH=credentials.json
SPREADSHEET_ID=your-sheet-id-here
GOOGLE_API_KEY=AIzaSy...your-gemini-key
GEMINI_MODEL=gemini-1.5-flash
LLM_TEMPERATURE=0.3
FLASK_PORT=5000
FLASK_HOST=0.0.0.0
MEMORY_ENABLED=True
MEMORY_MAX_MESSAGES=10
```

### 4. الحصول على Google Gemini API Key

1. روح على: https://aistudio.google.com/app/apikey
2. Sign in مع Google account
3. اضغط "Create API Key"
4. انسخ المفتاح (AIzaSy...)

### 5. تنصيب المكتبات

```bash
pip install -r requirements.txt
```

### 6. تشغيل الـ API

```bash
python api_server.py
```

## 📡 API Endpoints

### 1. AI Chat (ذكي مع Memory)

```bash
POST /chat
Content-Type: application/json

{
  "query": "بدي أحجز موعد",
  "phone": "+962798633226"
}

Response:
{
  "success": true,
  "response": "تمام! بدك الموعد لأي يوم؟",
  "messages_in_history": 2
}
```

### 2. Add Patient (مباشر)

```bash
POST /add-patient

{
  "full_name": "أحمد محمد",
  "phone": "+962798633226",
  "email": "ahmad@email.com",
  "city": "عمان"
}
```

### 3. Update Patient

```bash
POST /update-patient

{
  "identifier": "+962798633226",
  "updates": {
    "city": "إربد"
  }
}
```

### 4. Delete Patient

```bash
POST /delete-patient

{
  "identifier": "+962798633226",
  "force": false
}
```

### 5. Get Patient Info

```bash
POST /get-patient

{
  "action": "get_one",
  "identifier": "+962798633226"
}
```

### 6. Clear Memory (جديد)

```bash
POST /clear-memory

{
  "phone": "+962798633226"
}

Response:
{
  "success": true,
  "message": "تم مسح 8 رسالة من Google Sheets",
  "deleted_count": 8
}
```

### 7. Memory Stats (جديد)

```bash
GET /memory-stats

Response:
{
  "total_messages": 156,
  "total_users": 12,
  "users": [
    {
      "phone": "+962798633226",
      "message_count": 14,
      "last_message_time": "2026-03-19T14:30:00"
    }
  ]
}
```

## 🔗 الربط مع n8n

### Workflow URL

استخدم URL من Replit:
```
https://your-username.repl.co/chat
```

### WhatsApp Integration

1. إنشاء Workflow في n8n
2. Webhook لاستقبال رسائل WhatsApp
3. HTTP Request لـ Replit API
4. إرسال الرد عبر WhatsApp API

مثال n8n HTTP Request Node:
```
Method: POST
URL: https://your-repl.repl.co/chat
Body:
{
  "query": "={{ $json.message }}",
  "phone": "={{ $json.phone }}"
}
```

## 📊 Google Sheets Structure

### Sheet: patients

```
patient_id | full_name | phone | email | city | specialty | patient_status | created_at | updated_at | notes
```

### Sheet: conversation_history (جديد!)

```
conversation_id | phone | role | message | timestamp
```

**مثال:**
```
+962798633226 | +962798633226 | user      | بدي موعد     | 2026-03-19T14:30:00
+962798633226 | +962798633226 | assistant | تمام! أي يوم؟ | 2026-03-19T14:30:02
```

### Sheet: error_log

```
timestamp | operation | error_type | error_message | input_data | stack_trace
```

### Sheet: api_logs

```
timestamp | endpoint | method | input_data | success | response | execution_time
```

## 🧠 Memory System

### كيف يشتغل Memory:

1. **Persistent Storage**: كل محادثة محفوظة في Google Sheets
2. **Per-User Memory**: كل مستخدم له ذاكرة منفصلة (حسب رقم الهاتف)
3. **Last N Messages**: يتذكر آخر 10 رسائل (قابل للتعديل)
4. **Context-Aware**: يستخدم المحادثات السابقة لفهم السياق

### مثال:

```
User: "أضف مريض أحمد"
AI: "تم إضافة أحمد ✅"

[محفوظ في Sheets]

User: "شو اسمه؟"
AI: "اسم المريض: أحمد"  ← يتذكر من المحادثة السابقة!
```

### إدارة Memory:

```bash
# مسح محادثة مستخدم معين
curl -X POST /clear-memory -d '{"phone": "+962..."}'

# إحصائيات
curl /memory-stats
```

## 🤖 AI Agent Behavior

### يجيب على:
✅ حجز وإدارة المواعيد  
✅ إضافة وتعديل بيانات المرضى  
✅ استفسارات إدارية (أوقات العمل، الموقع، الأسعار العامة)  

### لا يجيب على (يحول للعيادة):
❌ أسئلة طبية وعلاجية  
❌ تشخيص  
❌ نصائح علاجية  
❌ وصفات طبية  

**الرد الموحد للأسئلة الطبية:**
> "للاستشارات الطبية والعلاجية، يرجى الاتصال مباشرة بالعيادة على الرقم: 079-863-3226"

## 🧪 Testing

```bash
# Health check
curl https://your-repl.repl.co/health

# Add patient
curl -X POST https://your-repl.repl.co/add-patient \
  -H "Content-Type: application/json" \
  -d '{"full_name": "أحمد", "phone": "+962798633226"}'

# AI Chat مع Memory
curl -X POST https://your-repl.repl.co/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "أضف مريض أحمد", "phone": "+962799999999"}'

# رسالة ثانية (بيتذكر!)
curl -X POST https://your-repl.repl.co/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "شو اسمه؟", "phone": "+962799999999"}'
```

## 🔧 Configuration

### Environment Variables (Secrets)

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_API_KEY` | Google Gemini API Key | Required |
| `GEMINI_MODEL` | Gemini model name | gemini-1.5-flash |
| `LLM_TEMPERATURE` | AI creativity (0-1) | 0.3 |
| `MEMORY_ENABLED` | Enable/disable memory | True |
| `MEMORY_MAX_MESSAGES` | Max messages to remember | 10 |
| `SPREADSHEET_ID` | Google Sheets ID | Required |
| `GOOGLE_CREDENTIALS_PATH` | Path to credentials.json | credentials.json |

### Available Gemini Models

- `gemini-1.5-flash` - سريع، موصى به ⭐ (مجاني)
- `gemini-1.5-pro` - أذكى، أبطأ شوي (مجاني)
- `gemini-2.0-flash-exp` - تجريبي، الأحدث (مجاني)

## 📝 Notes

- رقم الهاتف يجب أن يكون: +962XXXXXXXXX (13 رقم)
- Google Gemini API مجاني (15 req/min)
- Memory محفوظ دائماً في Google Sheets
- WhatsApp Business API للـ n8n integration
- الـ Agent لا يجيب على الأسئلة الطبية

## 🔐 Security

- استخدم Replit Secrets للمفاتيح
- لا تشارك credentials.json
- لا تنشر API keys في الكود
- Memory في Google Sheets (آمن، private)

## 🚀 Future: Migration to Supabase

البنية الحالية جاهزة للهجرة إلى Supabase:

```
Google Sheets → Supabase PostgreSQL

المميزات:
✅ أسرع 100x
✅ SQL queries قوية
✅ Real-time subscriptions
✅ Auth built-in
✅ Free tier كافي
```

**متى تحول؟**
- 100+ مستخدم نشط
- Google Sheets بطيء
- محتاج features متقدمة

## 📄 License

MIT License

---

**Built with ❤️ for Nexify Dental Clinic Automation**
