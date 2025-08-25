from pathlib import Path

DATA_DIR = Path(__file__).parent / 'data'
DB_PATH = DATA_DIR / 'primary.db'
DB_URL = f'sqlite:///{DB_PATH.resolve()}' 

CATEGORY_NAMES = ["math", "coding", "knowledge", "agent"]
