"""Create the local closed-alpha schema.

SQLite is the zero-setup development adapter. Set DATABASE_URL to a PostgreSQL
URL when running the same application against PostgreSQL.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.db import init_db


if __name__ == "__main__":
    init_db()
    print("ImpactOS database schema is ready.")
