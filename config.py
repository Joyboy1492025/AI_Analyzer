"""Central configuration for the AI Resume & Code Analyzer."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
CHROMA_DIR = BASE_DIR / "chroma_db"
REPORT_DIR = BASE_DIR / "reports"
REPORT_DIR.mkdir(exist_ok=True)

# Models
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
DEFAULT_LLM = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
LLM_CHOICES = ["llama3.2:3b", "llama3.1:8b", "mistral", "qwen2.5:7b", "gemma2:9b"]

# Chunking
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50
SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

# Guardrails
PDF_BANNED = ["password", "private key", "secret key", "credit card"]
INPUT_BANNED = ["hack", "exploit", "malware", "porn"]
OUTPUT_BLOCKLIST = ["password", "private key", "secret key"]

# Email (can be overridden from the UI)
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_EMAIL = os.getenv("SMTP_EMAIL", "")
SMTP_APP_PASSWORD = os.getenv("SMTP_APP_PASSWORD", "")

ANALYSIS_TYPES = ["Auto-detect", "Resume", "Code"]