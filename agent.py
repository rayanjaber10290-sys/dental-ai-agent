"""
================================================
AI Agent Module - QA HARDENED
نظام الذكاء الاصطناعي لإدارة المرضى
================================================
"""

# التعديل الجوهري هنا لحل مشكلة الـ ImportError
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.tools import Tool  # استيراد Tool من المكان الصحيح
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import SystemMessage

# باقي الكود كما هو
from tools import (
    add_patient_tool,
    update_patient_tool,
    delete_patient_tool,
    get_patient_info_tool
)
from config import *

# ================================================
# SYSTEM PROMPT - BULLETPROOF (الكود اللي كتبته إنت ممتاز)
# ================================================

SYSTEM_PROMPT = """أنت نظام إداري ذكي لعيادة أسنان. مهمتك الوحيدة: إدارة بيانات المرضى بدقة ومنع الأخطاء... (باقي البرومبت تبعك)"""

# ================================================
# TOOLS
# ================================================

tools = [
    Tool(
        name="add_patient",
        func=add_patient_tool,
        description="إضافة مريض جديد. Input: JSON مع full_name, phone (إلزامي)"
    ),
    Tool(
        name="update_patient",
        func=update_patient_tool,
        description="تحديث بيانات مريض موجود. Input: JSON مع identifier, updates"
    ),
    Tool(
        name="delete_patient",
        func=delete_patient_tool,
        description="حذف مريض. Input: JSON مع identifier"
    ),
    Tool(
        name="get_patient_info",
        func=get_patient_info_tool,
        description="استعلام عن مريض. Input: JSON مع action (get_one/get_all/search), identifier"
    )
]

# ================================================
# CREATE AGENT
# ================================================

def create_patient_agent():
    """إنشاء AI Agent"""
    
    llm = ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        temperature=LLM_TEMPERATURE,
        google_api_key=GOOGLE_API_KEY
    )
    
    # تأكد أن المتغيرات chat_history و agent_scratchpad موجودة كما في الكود
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT), # تم تبسيطها لتكون أكثر استقراراً
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad")
    ])
    
    agent = create_openai_functions_agent(
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
# SINGLETON
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

# Export
agent = get_agent()
