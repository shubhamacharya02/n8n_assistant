import json
import os
import time
import uuid
from datetime import datetime
import requests
import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="n8n Assistant & Workflow Runner",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    code, pre, .stCodeBlock {
        font-family: 'JetBrains Mono', monospace !important;
    }
    
    .app-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 4px 0 16px 0;
        border-bottom: 1px solid rgba(128, 128, 128, 0.2);
        margin-bottom: 20px;
    }
    
    .app-header h1 {
        margin: 0;
        font-size: 1.75rem;
        font-weight: 700;
        background: linear-gradient(135deg, #FF6D5A 0%, #FF9E6D 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .badge-status {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.8rem;
        font-family: 'JetBrains Mono', monospace;
    }
    
    .status-success {
        background-color: rgba(34, 197, 94, 0.15);
        color: #22c55e;
        border: 1px solid rgba(34, 197, 94, 0.3);
    }
    
    .status-error {
        background-color: rgba(239, 68, 68, 0.15);
        color: #ef4444;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }
    
    .status-latency {
        background-color: rgba(59, 130, 246, 0.15);
        color: #3b82f6;
        border: 1px solid rgba(59, 130, 246, 0.3);
    }
    
    .chat-session-badge {
        font-size: 0.75rem;
        background: rgba(128, 128, 128, 0.15);
        padding: 2px 8px;
        border-radius: 4px;
        color: gray;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize Session State
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())[:8]

if "execution_history" not in st.session_state:
    st.session_state.execution_history = []

if "payload_text" not in st.session_state:
    st.session_state.payload_text = json.dumps(
        {
            "action": "trigger",
            "message": "Hello from Streamlit UI!",
            "data": {
                "timestamp": datetime.now().isoformat(),
            },
        },
        indent=2,
    )

def extract_n8n_response_text(resp_data):
    """Smart parser to extract readable text/markdown from n8n response structures."""
    if isinstance(resp_data, str):
        return resp_data
    
    if isinstance(resp_data, dict):
        # Common n8n chat response keys
        for key in ["output", "text", "message", "response", "reply", "content", "data"]:
            if key in resp_data and isinstance(resp_data[key], (str, int, float)):
                return str(resp_data[key])
            elif key in resp_data and isinstance(resp_data[key], dict):
                # Nested structures e.g. { "data": { "text": "..." } }
                nested_text = extract_n8n_response_text(resp_data[key])
                if nested_text:
                    return nested_text
        return json.dumps(resp_data, indent=2)
    
    if isinstance(resp_data, list):
        if len(resp_data) == 1:
            return extract_n8n_response_text(resp_data[0])
        return json.dumps(resp_data, indent=2)
        
    return str(resp_data)

# --- Sidebar Configuration ---
with st.sidebar:
    st.markdown("### ⚙️ n8n Connection")
    
    default_webhook = os.getenv("N8N_WEBHOOK_URL", "")
    webhook_url = st.text_input(
        "Webhook / Chat URL",
        value=default_webhook,
        placeholder="https://your-n8n-instance/webhook/...",
        help="The URL of your n8n Webhook or Chat Trigger node.",
    )
    
    mode = st.radio(
        "Interface Mode",
        options=["💬 Chat Assistant", "⚡ Raw JSON Runner"],
        index=0,
    )
    
    st.markdown("---")
    
    if mode == "💬 Chat Assistant":
        st.markdown("### 💬 Chat Settings")
        
        input_key = st.text_input(
            "Payload Message Field Key",
            value="chatInput",
            help="Field key sent in JSON (standard n8n Chat Trigger uses 'chatInput').",
        )
        
        send_session_id = st.checkbox("Include Session ID in Payload", value=True)
        if send_session_id:
            st.caption(f"Current Session ID: `{st.session_state.session_id}`")
            if st.button("🔄 New Session / Reset Chat", use_container_width=True):
                st.session_state.session_id = str(uuid.uuid4())[:8]
                st.session_state.chat_messages = []
                st.rerun()
        
        if st.session_state.chat_messages:
            if st.button("🗑️ Clear Chat History", use_container_width=True):
                st.session_state.chat_messages = []
                st.rerun()
                
    else:
        st.markdown("### ⚡ Runner Settings")
        http_method = st.selectbox(
            "HTTP Method",
            options=["POST", "GET"],
            index=0,
        )
        
        st.markdown("### 📋 Sample Templates")
        presets = {
            "Simple Message": {
                "message": "Hello from Streamlit!",
                "timestamp": datetime.now().isoformat(),
            },
            "User Data Record": {
                "event": "user_signup",
                "email": "user@example.com",
                "name": "Alex",
            },
            "Query Task": {
                "query": "Summarize latest workflow metrics",
                "limit": 5,
            },
        }
        selected_preset = st.selectbox("Load Template", list(presets.keys()))
        if st.button("Apply Template", use_container_width=True):
            st.session_state.payload_text = json.dumps(presets[selected_preset], indent=2)
            st.rerun()

    timeout_sec = st.slider("Request Timeout (s)", min_value=5, max_value=600, value=180, step=5, help="Default: 180s (3 minutes)")

# --- Header ---
st.markdown(
    f"""
    <div class="app-header">
        <h1>{'💬 n8n AI Chat Assistant' if mode == '💬 Chat Assistant' else '⚡ n8n Workflow JSON Runner'}</h1>
        <span class="chat-session-badge">Session: {st.session_state.session_id}</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# ==============================================================================
# MODE 1: CHAT ASSISTANT INTERFACE
# ==============================================================================
if mode == "💬 Chat Assistant":
    if not webhook_url.strip():
        st.warning("⚠️ Please provide your n8n Webhook / Chat URL in the sidebar to start chatting.")
    
    # Display message history
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"], avatar="🧑‍💻" if msg["role"] == "user" else "🤖"):
            st.markdown(msg["content"])
            if "latency" in msg and msg["latency"]:
                st.caption(f"⏱️ {msg['latency']}s")

    # Chat input box
    if user_prompt := st.chat_input("Type your message here to interact with n8n..."):
        if not webhook_url.strip():
            st.error("Please configure your n8n Webhook URL in the sidebar first.")
        else:
            # Add user message to state & display
            st.session_state.chat_messages.append({
                "role": "user",
                "content": user_prompt,
                "timestamp": datetime.now().strftime("%H:%M:%S"),
            })
            with st.chat_message("user", avatar="🧑‍💻"):
                st.markdown(user_prompt)

            # Send to n8n endpoint
            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner("Thinking & processing in n8n..."):
                    payload = {
                        input_key: user_prompt,
                        # Also include message key for compatibility with various workflows
                        "message": user_prompt,
                    }
                    if send_session_id:
                        payload["sessionId"] = st.session_state.session_id
                    
                    start_time = time.time()
                    try:
                        response = requests.post(
                            webhook_url.strip(),
                            json=payload,
                            headers={"Content-Type": "application/json"},
                            timeout=timeout_sec,
                        )
                        elapsed = round(time.time() - start_time, 2)
                        
                        if response.status_code == 200:
                            try:
                                resp_data = response.json()
                                reply_text = extract_n8n_response_text(resp_data)
                            except Exception:
                                reply_text = response.text or "*(Empty 200 OK response received from n8n)*"
                                
                            st.markdown(reply_text)
                            st.caption(f"⏱️ {elapsed}s | Status: 200 OK")
                            
                            st.session_state.chat_messages.append({
                                "role": "assistant",
                                "content": reply_text,
                                "latency": elapsed,
                                "raw": resp_data if 'resp_data' in locals() else response.text,
                                "timestamp": datetime.now().strftime("%H:%M:%S"),
                            })
                        else:
                            err_msg = f"❌ **Error ({response.status_code})**: {response.text}"
                            st.error(err_msg)
                            st.session_state.chat_messages.append({
                                "role": "assistant",
                                "content": err_msg,
                                "latency": elapsed,
                                "timestamp": datetime.now().strftime("%H:%M:%S"),
                            })
                    except requests.exceptions.Timeout:
                        elapsed = round(time.time() - start_time, 2)
                        err_msg = f"⏱️ Request timed out after {timeout_sec} seconds."
                        st.error(err_msg)
                        st.session_state.chat_messages.append({
                            "role": "assistant",
                            "content": err_msg,
                            "latency": elapsed,
                        })
                    except Exception as e:
                        elapsed = round(time.time() - start_time, 2)
                        err_msg = f"⚠️ Could not reach n8n endpoint: {str(e)}"
                        st.error(err_msg)
                        st.session_state.chat_messages.append({
                            "role": "assistant",
                            "content": err_msg,
                            "latency": elapsed,
                        })

# ==============================================================================
# MODE 2: RAW JSON / WEBHOOK RUNNER INTERFACE
# ==============================================================================
else:
    col_input, col_output = st.columns([1, 1], gap="large")

    with col_input:
        st.subheader("📤 Free-Form JSON Payload")
        
        tb_col1, tb_col2 = st.columns([1, 1])
        with tb_col1:
            if st.button("✨ Format JSON", use_container_width=True):
                try:
                    parsed = json.loads(st.session_state.payload_text)
                    st.session_state.payload_text = json.dumps(parsed, indent=2)
                    st.rerun()
                except Exception as e:
                    st.error(f"Invalid JSON: {str(e)}")
                    
        with tb_col2:
            if st.button("🧹 Clear", use_container_width=True):
                st.session_state.payload_text = "{\n  \n}"
                st.rerun()

        raw_payload_str = st.text_area(
            "Payload",
            value=st.session_state.payload_text,
            height=320,
            label_visibility="collapsed",
            key="json_editor_area",
        )
        st.session_state.payload_text = raw_payload_str

        is_valid = True
        parsed_json_body = None
        try:
            if raw_payload_str.strip():
                parsed_json_body = json.loads(raw_payload_str)
                st.caption("✅ Valid JSON syntax")
            else:
                st.caption("ℹ️ Empty payload")
        except json.JSONDecodeError as err:
            is_valid = False
            st.error(f"⚠️ JSON Syntax Error: {err.msg} (line {err.lineno}, col {err.colno})")

        run_clicked = st.button(
            "🚀 Run Workflow",
            type="primary",
            disabled=not is_valid,
            use_container_width=True,
        )

    # Handle JSON Runner Execution
    latest_result = None
    if run_clicked:
        if not webhook_url or not webhook_url.strip():
            st.error("Please enter a valid n8n Webhook URL in the sidebar.")
        else:
            with st.spinner("Executing workflow on n8n..."):
                start_time = time.time()
                try:
                    headers = {"Content-Type": "application/json"}
                    if http_method == "POST":
                        response = requests.post(
                            webhook_url.strip(),
                            json=parsed_json_body if parsed_json_body is not None else {},
                            headers=headers,
                            timeout=timeout_sec,
                        )
                    else:
                        response = requests.get(
                            webhook_url.strip(),
                            params=parsed_json_body if isinstance(parsed_json_body, dict) else {},
                            headers=headers,
                            timeout=timeout_sec,
                        )
                    
                    elapsed = round(time.time() - start_time, 3)
                    try:
                        response_json = response.json()
                    except Exception:
                        response_json = None

                    result_entry = {
                        "timestamp": datetime.now().strftime("%H:%M:%S"),
                        "status_code": response.status_code,
                        "elapsed_sec": elapsed,
                        "success": 200 <= response.status_code < 300,
                        "response_json": response_json,
                        "response_text": response.text,
                        "response_headers": dict(response.headers),
                        "request_payload": parsed_json_body,
                    }
                    st.session_state.execution_history.insert(0, result_entry)
                    latest_result = result_entry

                except Exception as e:
                    elapsed = round(time.time() - start_time, 3)
                    latest_result = {
                        "timestamp": datetime.now().strftime("%H:%M:%S"),
                        "status_code": 500,
                        "elapsed_sec": elapsed,
                        "success": False,
                        "response_json": None,
                        "response_text": f"Error: {str(e)}",
                        "response_headers": {},
                        "request_payload": parsed_json_body,
                    }
                    st.session_state.execution_history.insert(0, latest_result)

    with col_output:
        st.subheader("📥 Workflow Response")
        current_display = latest_result or (
            st.session_state.execution_history[0] if st.session_state.execution_history else None
        )

        if current_display:
            status_class = "status-success" if current_display["success"] else "status-error"
            status_icon = "🟢" if current_display["success"] else "🔴"
            
            st.markdown(
                f"""
                <div style="display: flex; gap: 10px; margin-bottom: 14px; align-items: center;">
                    <span class="badge-status {status_class}">
                        {status_icon} Status: {current_display['status_code']}
                    </span>
                    <span class="badge-status status-latency">
                        ⏱️ Latency: {current_display['elapsed_sec']}s
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            tab_json, tab_raw, tab_diag = st.tabs(["✨ Formatted Response", "📄 Raw Text", "🔍 Diagnostics"])

            with tab_json:
                if current_display["response_json"] is not None:
                    st.json(current_display["response_json"])
                    if isinstance(current_display["response_json"], list) and len(current_display["response_json"]) > 0:
                        if isinstance(current_display["response_json"][0], dict):
                            with st.expander("📊 View as Table"):
                                st.dataframe(current_display["response_json"], use_container_width=True)
                else:
                    st.code(current_display["response_text"] or "(Empty Response)")

            with tab_raw:
                st.code(current_display["response_text"] or "(Empty Response)")
                if current_display["response_text"]:
                    st.download_button(
                        label="💾 Download Response",
                        data=current_display["response_text"],
                        file_name=f"n8n_response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain",
                        use_container_width=True,
                    )

            with tab_diag:
                st.markdown("**Request Payload Sent:**")
                st.json(current_display["request_payload"] if current_display["request_payload"] is not None else {})
                st.markdown("**Response Headers:**")
                st.json(current_display["response_headers"])
        else:
            st.info("💡 Run a workflow to view the formatted response and execution details here.")
