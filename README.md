# n8n Workflow Runner UI ⚡

A clean, modern Python Streamlit interface to trigger and interact with your **n8n workflow webhooks** using free-form JSON payloads.

<p align="left">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Streamlit" />
  <img src="https://img.shields.io/badge/n8n-EA4B71?style=for-the-badge&logo=n8n&logoColor=white" alt="n8n" />
  <img src="https://img.shields.io/badge/JSON-000000?style=for-the-badge&logo=json&logoColor=white" alt="JSON" />
  <img src="https://img.shields.io/badge/Requests-2CA5E0?style=for-the-badge&logo=python&logoColor=white" alt="Requests" />
</p>

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
