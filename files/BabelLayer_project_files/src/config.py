"""
Application settings for BabelLayer.

Loads from .env file with sensible defaults for local development.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# -- Paths --
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"
LOGS_DIR = ROOT_DIR / "logs"
SAMPLES_DIR = DATA_DIR / "samples"

LOGS_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

# -- Database --
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{ROOT_DIR / 'babellayer.db'}")

# -- Auth / JWT --
JWT_SECRET = os.getenv("JWT_SECRET_KEY", "dev-secret-CHANGE-ME")
JWT_ALGO = os.getenv("JWT_ALGORITHM", "HS256")
JWT_TTL_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

# -- Explanation service --
LLM_BACKEND = os.getenv("LLM_PROVIDER", "ollama")  # "ollama" or "openai"
LLM_MODEL = os.getenv("LLM_MODEL", "llama2")
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")

# -- Mapping and analytics --
EMBEDDING_MODEL = os.getenv("SENTENCE_TRANSFORMER_MODEL", "all-MiniLM-L6-v2")
USE_EMBEDDINGS = os.getenv("USE_EMBEDDINGS", "auto").strip().lower()
ANOMALY_CONTAMINATION = float(os.getenv("ANOMALY_CONTAMINATION", "0.1"))
MAPPING_MIN_CONFIDENCE = float(os.getenv("MAPPING_CONFIDENCE_THRESHOLD", "0.5"))

# -- Logging --
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = LOGS_DIR / "app.log"

# -- App identity --
APP_TITLE = "BabelLayer"
APP_VERSION = "2.0.0"
