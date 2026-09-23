"""Quick inspection of the Navi-G8 graph database."""

import sqlite3
from pathlib import Path

db_path = Path.home() / ".navi-g8" / "field.db"

if not db_path.exists():
    print(f"No database found at {db_path}")
    print("Run the app and send a query first.")
    raise SystemExit(1)

conn = sqlite3.connect(db_path)

print("=== NODES BY TYPE ===")
rows = conn.execute("SELECT type, COUNT(*) FROM nodes GROUP BY type").fetchall()
for node_type, count in rows:
    print(f"  {node_type}: {count}")
if not rows:
    print("  (empty)")

print("\n=== EDGES BY TYPE ===")
rows = conn.execute("SELECT type, COUNT(*) FROM edges GROUP BY type").fetchall()
for edge_type, count in rows:
    print(f"  {edge_type}: {count}")
if not rows:
    print("  (empty)")

print("\n=== RECENT NODES ===")
rows = conn.execute(
    "SELECT type, description FROM nodes ORDER BY created_at DESC LIMIT 10"
).fetchall()
for node_type, desc in rows:
    short = (
        (desc[:60] + "...") if desc and len(desc) > 60 else (desc or "(no description)")
    )
    print(f"  [{node_type}] {short}")
