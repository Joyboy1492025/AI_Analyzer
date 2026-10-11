# AI Resume & Code Analyzer

Hybrid RAG (PDF + live web) analyzer with a Gradio UI, guardrails, PDF report and email delivery.

## Structure

```
resume_ai/
├── app.py          # Gradio UI (run this)
├── pipeline.py     # Orchestration: PDF -> RAG -> LLM -> guardrail -> report
├── chain.py        # Prompt + LCEL chain (Ollama)
├── rag.py          # PDF loading, chunking, embeddings, Chroma retriever
├── web_search.py   # DuckDuckGo tool
├── guardrails.py   # Input / PDF / output guardrails
├── report.py       # Markdown -> styled PDF (ReportLab)
├── emailer.py      # SMTP email with PDF attachment
├── config.py       # Constants and env settings
├── requirements.txt
└── .env.example
```

## Run

```bash
pip install -r requirements.txt
python app.py
```

Open the local URL printed in the terminal (usually http://127.0.0.1:7860).

## Gmail

Use a Google **App Password** (Account > Security > 2-Step Verification > App passwords).
Enter it in the UI or in `.env`. Do not hardcode credentials in source files.