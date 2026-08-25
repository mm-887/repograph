import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("GITHUB_TOKEN")
REPOS_DIR = os.getenv("REPOS_DIR", "repositories")
if not TOKEN:
    raise ValueError("GITHUB_TOKEN not found in environment variables")