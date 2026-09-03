import json
import os
import time
from datetime import datetime
import requests
import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="n8n Workflow Runner",
    page_icon="⚡",
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
    
    /* Header styling */
    .app-header {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 8px 0 20px 0;
        border-bottom: 1px solid rgba(128, 128, 128, 0.2);
        margin-bottom: 24px;
    }
    
    .app-header h1 {
        margin: 0;
        font-size: 1.8rem;
        font-weight: 700;
        background: linear-gradient(135deg, #FF6D5A 0%, #FF9E6D 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .badge-status {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
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
    
    .run-btn-container {
        margin-top: 10px;
        margin-bottom: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize Session State
if "execution_history" not in st.session_state:
    st.session_state.execution_history = []

if "payload_text" not in st.session_state:
    st.session_state.payload_text = json.dumps(
        {
            "action": "trigger",
            "message": "Hello from Streamlit UI!",
            "data": {
                "user": "admin",
                "timestamp": datetime.now().isoformat(),
            },
        },
        indent=2,
    )

# Sample Presets
PRESETS = {
    "Default / Simple Message": {
        "message": "Hello from Streamlit!",
        "timestamp": datetime.now().isoformat(),
    },
    "Data Record Trigger": {
        "event": "user_signup",
        "email": "user@example.com",
        "name": "Jane Doe",
        "plan": "premium",
    },
    "Search / Query Task": {
        "query": "latest generative AI models",
        "limit": 5,
        "filter": {"status": "active"},
    },
    "Custom Key-Value": {
        "task": "process_items",
        "items": [101, 102, 103],
        "notify": True,
    },
}

# --- Sidebar Configuration ---
with st.sidebar:
    st.markdown("### ⚙️ Endpoint Settings")
    
    default_webhook = os.getenv("N8N_WEBHOOK_URL", "")
    webhook_url = st.text_input(
        "n8n Webhook URL",
        value=default_webhook,
        placeholder="https://your-n8n-instance/webhook/...",
        help="The URL of your n8n Webhook node (Test or Production URL).",
    )
    
    http_method = st.selectbox(
        "HTTP Method",
        options=["POST", "GET"],
        index=0,
        help="Select the HTTP method expected by your n8n Webhook node.",
    )
    
    timeout_sec = st.number_input(
        "Timeout (seconds)",
        min_value=1,
        max_value=300,
        value=60,
        step=5,
        help="Max time to wait for the workflow response before timing out.",
    )

    st.markdown("---")
    st.markdown("### 📋 Quick Templates")
    selected_preset = st.selectbox(
        "Load Sample Payload",
        options=list(PRESETS.keys()),
    )
    if st.button("Apply Template", use_container_width=True):
        st.session_state.payload_text = json.dumps(
            PRESETS[selected_preset], indent=2
        )
        st.rerun()

    if st.session_state.execution_history:
        st.markdown("---")
        st.markdown(f"### 🕒 Run History ({len(st.session_state.execution_history)})")
        if st.button("Clear History", use_container_width=True):
            st.session_state.execution_history = []
            st.rerun()

# --- Main Interface ---
st.markdown(
    """
    <div class="app-header">
        <h1>⚡ n8n Workflow Runner</h1>
    </div>
    """,
    unsafe_allow_html=True,
)

# Two-column layout: Input Payload on left, Output on right
col_input, col_output = st.columns([1, 1], gap="large")

with col_input:
    st.subheader("📤 Payload Input (JSON)")
    
    # JSON Editor Toolbar
    tb_col1, tb_col2 = st.columns([1, 1])
    with tb_col1:
        if st.button("✨ Format / Prettify JSON", use_container_width=True):
            try:
                parsed = json.loads(st.session_state.payload_text)
                st.session_state.payload_text = json.dumps(parsed, indent=2)
                st.rerun()
            except Exception as e:
                st.error(f"Cannot format invalid JSON: {str(e)}")
                
    with tb_col2:
        if st.button("🧹 Clear Payload", use_container_width=True):
            st.session_state.payload_text = "{\n  \n}"
            st.rerun()

    # JSON Text Area
    raw_payload_str = st.text_area(
        "Enter Free-Form JSON Payload",
        value=st.session_state.payload_text,
        height=320,
        label_visibility="collapsed",
        key="payload_editor",
    )
    st.session_state.payload_text = raw_payload_str

    # JSON Validation Check
    is_valid_json = True
    parsed_json_body = None
    try:
        if raw_payload_str.strip():
            parsed_json_body = json.loads(raw_payload_str)
            st.caption("✅ Valid JSON syntax")
        else:
            st.caption("ℹ️ Empty payload (will send empty body)")
    except json.JSONDecodeError as err:
        is_valid_json = False
        st.error(f"⚠️ JSON Syntax Error: {err.msg} (line {err.lineno}, col {err.colno})")

    # Run Workflow Button
    st.markdown("<div class='run-btn-container'>", unsafe_allow_html=True)
    run_clicked = st.button(
        "🚀 Run Workflow",
        type="primary",
        disabled=not is_valid_json,
        use_container_width=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

# Handle Workflow Execution
latest_result = None
if run_clicked:
    if not webhook_url or not webhook_url.strip():
        st.error("Please enter a valid n8n Webhook URL in the sidebar or in `.env`.")
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
                
                # Parse response body
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

            except requests.exceptions.Timeout:
                elapsed = round(time.time() - start_time, 3)
                latest_result = {
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "status_code": 408,
                    "elapsed_sec": elapsed,
                    "success": False,
                    "response_json": None,
                    "response_text": f"Request timed out after {timeout_sec} seconds.",
                    "response_headers": {},
                    "request_payload": parsed_json_body,
                }
                st.session_state.execution_history.insert(0, latest_result)
            except Exception as e:
                elapsed = round(time.time() - start_time, 3)
                latest_result = {
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "status_code": 500,
                    "elapsed_sec": elapsed,
                    "success": False,
                    "response_json": None,
                    "response_text": f"Error connecting to n8n webhook: {str(e)}",
                    "response_headers": {},
                    "request_payload": parsed_json_body,
                }
                st.session_state.execution_history.insert(0, latest_result)

# Output Column
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
                <span style="color: gray; font-size: 0.85rem;">
                    Triggered at {current_display['timestamp']}
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        tab_json, tab_raw, tab_headers = st.tabs(["✨ Formatted Response", "📄 Raw Text", "🔍 Diagnostics & Headers"])

        with tab_json:
            if current_display["response_json"] is not None:
                st.json(current_display["response_json"])
                
                # Check if JSON is a list of dicts to offer a table view as well
                if isinstance(current_display["response_json"], list) and len(current_display["response_json"]) > 0:
                    if isinstance(current_display["response_json"][0], dict):
                        with st.expander("📊 View as Table", expanded=False):
                            st.dataframe(current_display["response_json"], use_container_width=True)
            else:
                st.info("Response is not JSON formatted. Viewing raw text:")
                st.code(current_display["response_text"] or "(Empty Response)")

        with tab_raw:
            st.code(current_display["response_text"] or "(Empty Response)", language="text")
            if current_display["response_text"]:
                st.download_button(
                    label="💾 Download Response",
                    data=current_display["response_text"],
                    file_name=f"n8n_response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    use_container_width=True,
                )

        with tab_headers:
            st.markdown("**Request Payload Sent:**")
            st.json(current_display["request_payload"] if current_display["request_payload"] is not None else {})
            
            st.markdown("**Response Headers:**")
            st.json(current_display["response_headers"])

    else:
        st.info("💡 Set your Webhook URL, configure the JSON payload, and click **🚀 Run Workflow** to see the response here.")
