# from langchain_core.messages import HumanMessage, AIMessage
# from src.agent.controller import run_master_agent

# def run_terminal_chat():
#     print("--- QueryMate Controller Agent Test ---")
#     print("Type 'exit' or 'quit' to stop.")

#     messages = []  # conversation history

#     while True:
#         user_input = input("\nUser: ")
#         if user_input.lower() in ["exit", "quit"]:
#             break

#         # Add user message
#         messages.append(HumanMessage(content=user_input))

#         # Call your controller agent directly
#         response = run_master_agent(messages)

#         # Save assistant response
#         messages.append(response)

#         # Print response (clean token if needed)
#         content = response.content
#         clean = (
#             content.replace("[TRIGGER_SQL]", "")
#                    .replace("[NO_SQL]", "")
#                    .strip()
#         )

#         print(f"\nQueryMate: {clean}")

# if __name__ == "__main__":
#     run_terminal_chat()


# test.py (في مجلد الجذر)
# from src.langgraph.nodes import orchestrator_node
# from langchain_core.messages import HumanMessage

# def run_orchestrator_test():
#     # محاكاة حالة قادمة من عميل الإصلاح تطلب توضيحاً من المستخدم
#     state = {
#         "messages": [HumanMessage(content="Show me sales")],
#         "needs_clarification": True,
#         "feedback_reason": "I'm not sure if you mean total sales or sales by category.",
#         "next_step": "sql_repair" # العقدة السابقة
#     }
    
#     print("--- Running Orchestrator Test ---")
#     result = orchestrator_node(state)
    
#     # التأكد من أن المنسق حول المسار إلى 'end' لانتظار رد المستخدم
#     print(f"Decision: {result['next_step']}")
#     print(f"Response: {result['messages'][0].content}")

# if __name__ == "__main__":
#     run_orchestrator_test()

import sys
import os

# إضافة المسار الحالي لتمكين استيراد مجلد src
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from src.langgraph.nodes import orchestrator_node
from langchain_core.messages import HumanMessage, AIMessage

def test_scenario(description, state_input):
    """وظيفة لاختبار السيناريوهات الفردية"""
    print(f"\n>>> Scenario: {description}")
    output = orchestrator_node(state_input)
    
    last_msg = output["messages"][-1].content
    # نستخدم next_step بناءً على تحديث المنسق الأخير ليدير الوكلاء
    next_node = output.get("next_step", output.get("next_step")) 
    
    print(f"Orchestrator says: {last_msg}")
    print(f"Next Agent: {next_node}")
    return output

def test_full_round():
    """اختبار الجولة الكاملة: فشل -> توضيح -> نجاح"""
    print("\n" + "="*40)
    print("RUNNING FULL ROUND TEST (Clarification & Recovery)")
    print("="*40)

    # المرحلة 1: محاكاة فشل في الإصلاح وطلب توضيح
    state_fail = {
        "messages": [HumanMessage(content="Show me sales")],
        "needs_clarification": True,
        "feedback_reason": "Do you mean sales by category or employee?",
        "next_step": "sql_repair"
    }
    print("\n[Step 1: System asks for clarification]")
    out_1 = orchestrator_node(state_fail)
    print(f"Agent: {out_1['messages'][-1].content}")
    
    # التحقق من نجاح التصفير (Reset Check)
    reset_ok = out_1.get("needs_clarification") == False
    print(f"Status Reset Check: {'PASSED' if reset_ok else 'FAILED'}")

    # المرحلة 2: محاكاة رد المستخدم (User Reply)
    user_reply = HumanMessage(content="I mean by category")
    state_recovery = {
        "messages": state_fail["messages"] + out_1["messages"] + [user_reply],
        "needs_clarification": False, # تم التصفير في الخطوة السابقة
        "next_step": "end"
    }
    
    print("\n[Step 2: User provides info - Master Agent should trigger SQL]")
    out_2 = orchestrator_node(state_recovery)
    print(f"Agent Decision: {out_2['messages'][-1].content}")
    print(f"Next Agent: {out_2['next_step']}")

if __name__ == "__main__":
    # 1. اختبار السيناريوهات الفردية
    test_scenario("Unsupported Query Request", {
        "messages": [HumanMessage(content="Delete database")],
        "is_unsupported": True
    })

    # 2. اختبار الجولة الكاملة للتأكد من التصفير واستمرارية الحوار
    test_full_round()