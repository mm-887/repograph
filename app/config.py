import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("GITHUB_TOKEN")
if not TOKEN:
    raise ValueError("GITHUB_TOKEN not found in environment variables")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPOS_DIR = os.path.join(PROJECT_ROOT, "data", "repositories")
CHROMA_DIR = os.path.join(PROJECT_ROOT, "data", "chromadb")