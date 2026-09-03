# n8n Workflow Runner UI ⚡

A clean, modern Python Streamlit interface to trigger and interact with your **n8n workflow webhooks** using free-form JSON payloads.

---

## 🚀 Features

- **Free-Form JSON Payload Editor**: Interactive text editor with real-time JSON syntax validation and auto-beautification.
- **Quick Preset Templates**: Easily switch between common payload patterns (simple messages, data records, search queries).
- **Interactive Output Viewer**:
  - **Formatted JSON View**: Collapsible tree viewer + automatic tabular view for list payloads.
  - **Raw Text / Download**: Download response data or inspect plain text responses.
  - **Diagnostics**: Inspect latency, HTTP status code, request payload, and response headers.
- **Environment Configuration**: Set your default n8n webhook URL via `.env` or adjust directly in the UI.

---

## 📦 Setup & Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/shubhamacharya02/n8n_assistant.git
   cd n8n_assistant
   ```

2. **Create and activate a virtual environment** (optional but recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure your n8n Webhook URL**:
   Copy `.env.example` to `.env` and set your endpoint:
   ```bash
   cp .env.example .env
   ```
   Open `.env` and update the URL:
   ```env
   N8N_WEBHOOK_URL=http://localhost:5678/webhook/your-workflow-webhook
   ```

---

## 🖥️ Running the Application

Launch the Streamlit app:
```bash
streamlit run app.py
```

The app will open automatically in your browser (typically at `http://localhost:8501`).
