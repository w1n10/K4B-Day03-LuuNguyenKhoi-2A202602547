"""
🖥️ STREAMLIT TEST UI (KHÔNG PHẢI PHẦN NỘP BÀI CHÍNH THỨC)
Giao diện trực quan để thử nghiệm ReAct Agent "Báo cáo Tình trạng Pin & Lốp xe VinFast GreenSM"
mà không cần gõ lệnh CLI. Chạy bằng: streamlit run src/ui_app.py
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import streamlit as st

from app import run_react_agent, load_test_cases, save_waterfall_trace
from mcp_server import MCPAcademicServer
from providers import get_llm_provider
from prompts import CHATBOT_BASELINE_PROMPT

st.set_page_config(page_title="VinFast GreenSM Assistant", page_icon="🔋", layout="centered")


@st.cache_resource
def init_backend():
    return get_llm_provider(), MCPAcademicServer()


provider, mcp_server = init_backend()

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.header("⚙️ Trạng thái hệ thống")
    st.write(f"**LLM Provider:** `{provider.__class__.__name__}`")
    st.write(f"**MCP Server:** `{mcp_server.server_name}`")

    tools = mcp_server.list_tools()
    st.write(f"**Tools công bố ({len(tools)}):**")
    for t in tools:
        with st.expander(f"🛠️ {t['name']}"):
            st.caption(t.get("description", ""))
            st.json(t.get("parameters", {}))

    st.divider()
    mode = st.radio("Chế độ trả lời", ["ReAct Agent (có Tool)", "Chatbot Baseline (không Tool)"])

    st.divider()
    st.write("**💡 Câu hỏi mẫu (Test Cases):**")
    try:
        for tc in load_test_cases():
            if st.button(f"{tc['id']}: {tc['question'][:40]}...", key=tc["id"], use_container_width=True):
                st.session_state.pending_query = tc["question"]
    except Exception as e:
        st.caption(f"Không tải được test_cases.json: {e}")

    if st.button("🗑️ Xoá lịch sử chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

st.title("🔋 VinFast GreenSM Assistant")
st.caption("Trợ lý báo cáo tình trạng Pin & Lốp xe điện VinFast GreenSM (ReAct Agent + MCP)")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("trace"):
            with st.expander("🧠 Xem quá trình suy luận (ReAct Trace)"):
                for step in msg["trace"]:
                    if step["action_type"] == "TOOL_EXECUTION":
                        st.markdown(f"**Bước {step['step']} · Action:** `{step['tool_name']}({step['arguments']})`")
                        st.json(step["observation"])
                        st.caption(f"⏱️ {step['latency_ms']} ms")
                    else:
                        st.markdown(f"**Bước {step['step']} · Thought:** {step['thought']}")
                        st.caption(f"⏱️ {step['latency_ms']} ms")
        st.write(msg["content"])

pending = st.session_state.pop("pending_query", None)
user_query = st.chat_input("Nhập câu hỏi về tình trạng xe hoặc yêu cầu bảo dưỡng...") or pending

if user_query:
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.write(user_query)

    with st.chat_message("assistant"):
        with st.spinner("Đang xử lý..."):
            if mode.startswith("ReAct"):
                trace = run_react_agent(user_query, provider, mcp_server)
                save_waterfall_trace(trace)
                final_step = next((s for s in reversed(trace) if s["action_type"] == "FINAL_ANSWER"), None)
                answer = final_step["output"] if final_step else "Không nhận được câu trả lời."

                with st.expander("🧠 Xem quá trình suy luận (ReAct Trace)"):
                    for step in trace:
                        if step["action_type"] == "TOOL_EXECUTION":
                            st.markdown(f"**Bước {step['step']} · Action:** `{step['tool_name']}({step['arguments']})`")
                            st.json(step["observation"])
                            st.caption(f"⏱️ {step['latency_ms']} ms")
                        else:
                            st.markdown(f"**Bước {step['step']} · Thought:** {step['thought']}")
                            st.caption(f"⏱️ {step['latency_ms']} ms")

                st.write(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer, "trace": trace})
            else:
                answer = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
                st.write(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer, "trace": None})
