from pathlib import Path

BASE_PATH = Path(__file__).parent

class utils():
    
    def load_query(filename):
        path = BASE_PATH / "queries" / filename
        with open(path, "r", encoding="utf-8") as f:
            return f.read()