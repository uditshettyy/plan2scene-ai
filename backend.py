import sys
from pathlib import Path
import uvicorn

# Ensure backend module is importable
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.main import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
