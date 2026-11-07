"""Central configuration. MOCK_LLM is deliberately deterministic and offline."""
from pathlib import Path
import os
ROOT = Path(__file__).resolve().parent
MOCK_LLM = os.getenv("MOCK_LLM", "true").lower() in {"1", "true", "yes"}
MAX_REQUEST_TOKENS = int(os.getenv("MAX_REQUEST_TOKENS", "1800"))
ESCALATION_THRESHOLD = float(os.getenv("ESCALATION_THRESHOLD", "0.75"))
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "4"))
SIMILARITY_THRESHOLD_FILE = ROOT / "rag" / "threshold.json"
CHROMA_PATH = ROOT / "storage" / "chroma"
LOG_PATH = ROOT / "logs" / "requests.jsonl"
