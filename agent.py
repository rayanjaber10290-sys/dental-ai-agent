"""
================================================
LangChain AI Agent
الـ Agent الذكي مع Gemini
================================================
"""

from langchain.agents import Tool, AgentExecutor, create_tool_calling_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from tools import (
    add_patient_tool,
    update_patient_tool,
    delete_patient_tool,
    get_patient_info_tool
)
from config import *


# ================================================
# TOOLS DEFINITION
# ================================================

tools = [
    Tool(
        name="add_patient",
        func=add_patient_tool,
        description="""
        استخدم هذه الأداة لإضافة مريض جديد.
        
        Input: JSON string:
        {
            "full_name": "أحمد محمد",
            "phone": "+962798633226",
            "email": "ahmad@email.com",
            "city": "عمان",
            "specialty": "عام",
            "patient_status": "new",
            "notes": ""
        }
        
        Output: JSON مع success, message, patient_id
        """
    ),
    
    Tool(
        name="update_patient",
        func=update_patient_tool,
        description="""
        استخدم هذه الأداة لتعديل بيانات مريض موجود.
        
        Input: JSON string:
        {
            "identifier": "+962798633226",
            "updates": {
                "city": "إربد",
                "patient_status": "active"
            }
        }
        
        Output: JSON مع success, updated_fields
        """
    ),
    
    Tool(
        name="delete_patient",
        func=delete_patient_tool,
        description="""
        استخدم هذه الأداة لحذف مريض بشكل آمن.
        
        Input: JSON string:
        {
            "identifier": "+962798633226",
            "force": false
        }
        
        ملاحظة: البيانات المرتبطة (مواعيد/فواتير) لن تُحذف
        
        Output: JSON مع success, warnings
        """
    ),
    
    Tool(
        name="get_patient_info",
        func=get_patient_info_tool,
        description="""
        استخدم هذه الأداة للاستعلام عن المرضى.
        
        Scenarios:
        1. مريض واحد:
        {"action": "get_one", "identifier": "+962798633226"}
        
        2. جميع المرضى:
        {"action": "get_all"}
        
        3. بحث:
        {"action": "search", "filters": {"city": "عمان"}}
        
        Output: JSON مع patients list
        """
    )
]


# ================================================
# SYSTEM PROMPT
# ================================================

SYSTEM_PROMPT = """أنت مساعد إداري ذكي لعيادة أسنان متخصص في إدارة بيانات المرضى والمواعيد.

## معلومات العيادة
- الاسم: عيادة د. رايان جابر للأسنان
- الموقع: عمان، الأردن
- رقم الهاتف: 079-863-3226
- النظام: إدارة بيانات المرضى عبر Google Sheets

## مسؤولياتك (فقط!)
✅ إدارة بيانات المرضى (إضافة، تعديل، حذف، استعلام)
✅ حجز المواعيد وإدارتها
✅ الرد على الاستفسارات الإدارية (أوقات العمل، الموقع، الأسعار العامة)

❌ لا تجيب على الأسئلة الطبية أبداً!

## قواعد مهمة جداً
🚫 **قاعدة طبية صارمة:**
إذا سأل المريض أي سؤال طبي أو علاجي، رد فوراً:
"للاستشارات الطبية والعلاجية، يرجى الاتصال مباشرة بالعيادة على الرقم: 079-863-3226
سيكون الطبيب سعيداً بالإجابة على جميع استفساراتكم الطبية. 🩺"

## أمثلة الأسئلة الطبية (لا تجيب عليها):
❌ "عندي ألم في ضرسي، شو أعمل؟"
❌ "كم جلسة محتاج للتقويم؟"
❌ "التبييض بيضر الأسنان؟"
❌ "شو أفضل علاج للتسوس؟"
❌ "ممكن أعمل زراعة أسنان؟"
❌ "عندي التهاب باللثة"
❌ أي سؤال عن: الألم، العلاج، التشخيص، الأدوية، الإجراءات الطبية

→ كل هذه: اطلب منهم الاتصال بالعيادة!

## الأسئلة الإدارية (يمكنك الإجابة):
✅ "بدي أحجز موعد"
✅ "شو مواعيد العيادة؟"
✅ "وين موقع العيادة؟"
✅ "كم سعر التنظيف؟" (أسعار عامة فقط)
✅ "بدي ألغي موعدي"
✅ "بدي أعدل بياناتي"

## معلومات يمكنك مشاركتها:
📍 الموقع: عمان، الأردن
⏰ أوقات العمل: السبت-الخميس 9 صباحاً - 5 مساءً
💰 أسعار عامة:
   - تنظيف: 25 دينار
   - فحص: 15 دينار
   - (للأسعار التفصيلية: اتصل بالعيادة)

## قواعد تقنية
✅ رقم الهاتف: +962XXXXXXXXX (13 رقم)
✅ تحقق من البيانات قبل الإضافة
✅ قبل الحذف، تحقق من البيانات المرتبطة
✅ رد بالعربية دائماً

## الأدوات المتاحة
1. add_patient: إضافة مريض جديد
2. update_patient: تعديل بيانات مريض
3. delete_patient: حذف مريض
4. get_patient_info: استعلام

## أمثلة الاستخدام الصحيح

✅ مثال 1 - حجز (تجيب):
User: "بدي أحجز موعد"
Response: "تمام! بدك الموعد لأي يوم؟ عندنا مواعيد متاحة..."

✅ مثال 2 - إداري (تجيب):
User: "شو أوقات العيادة؟"
Response: "أوقات العيادة: السبت-الخميس من 9 صباحاً - 5 مساءً"

❌ مثال 3 - طبي (لا تجيب):
User: "عندي ألم في ضرسي، شو أسوي؟"
Response: "للاستشارات الطبية والعلاجية، يرجى الاتصال مباشرة بالعيادة على الرقم: 079-863-3226
سيكون الطبيب سعيداً بالإجابة على جميع استفساراتكم الطبية. 🩺"

❌ مثال 4 - طبي (لا تجيب):
User: "كم جلسة بدي للتقويم؟"
Response: "للاستشارات الطبية والعلاجية، يرجى الاتصال مباشرة بالعيادة على الرقم: 079-863-3226
سيكون الطبيب سعيداً بالإجابة على جميع استفساراتكم الطبية. 🩺"

كن مساعداً إدارياً دقيقاً ومحترفاً، ولا تتجاوز صلاحياتك أبداً!"""


# ================================================
# CREATE AGENT
# ================================================

def create_patient_agent():
    """إنشاء AI Agent"""
    
    # LLM (Google Gemini)
    llm = ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        temperature=LLM_TEMPERATURE,
        google_api_key=GOOGLE_API_KEY
    )
    
    # ✅ Fix 1: استخدام tuples بدل SystemMessage object
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad")
    ])
    
    # ✅ Fix 2: create_tool_calling_agent بدل create_openai_functions_agent
    agent = create_tool_calling_agent(
        llm=llm,
        tools=tools,
        prompt=prompt
    )
    
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=AGENT_VERBOSE,
        max_iterations=AGENT_MAX_ITERATIONS,
        handle_parsing_errors=True,
        return_intermediate_steps=False
    )
    
    return agent_executor


# ================================================
# GLOBAL INSTANCE
# ================================================

_agent_instance = None

def get_agent():
    """Get singleton agent instance"""
    global _agent_instance
    if _agent_instance is None:
        print("🤖 Initializing AI Agent...")
        _agent_instance = create_patient_agent()
        print("✅ AI Agent ready!")
    return _agent_instance


# ================================================
# TESTING
# ================================================

if __name__ == "__main__":
    print("="*60)
    print("🏥 Dental Clinic AI Agent - Test")
    print("="*60)
    
    agent = get_agent()
    
    test_queries = [
        "أضف مريض أحمد من عمان رقمه 0798633226",
        "اعرض معلومات المريض +962798633226"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"{'='*60}\n")
        
        try:
            result = agent.invoke({"input": query})
            print(f"✅ Response:\n{result['output']}\n")
        except Exception as e:
            print(f"❌ Error: {e}\n")
