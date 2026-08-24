import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.db import init_db
from app.main import seed_demo


if __name__ == "__main__":
    init_db()
    seed_demo()
    print("Synthetic ImpactOS demo data is ready.")
