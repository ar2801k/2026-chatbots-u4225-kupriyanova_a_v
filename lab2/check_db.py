
import sqlite3
from pathlib import Path

db_path = Path(__file__).resolve().parent / "smartshop.db"

if not db_path.exists():
    raise FileNotFoundError("База данных не найдена")

connection = sqlite3.connect(db_path)
connection.row_factory = sqlite3.Row

try:
    tables = connection.execute(
        "SELECT name FROM sqlite_master "
        "WHERE type = 'table' "
        "AND name NOT LIKE 'sqlite_%'"
    ).fetchall()

    print("ТАБЛИЦЫ БАЗЫ ДАННЫХ:")

    for table in tables:
        name = table["name"]
        count = connection.execute(
            f'SELECT COUNT(*) FROM "{name}"'
        ).fetchone()[0]

        print(f" - {name}: {count} записей")

        if "order" in name.lower() or "заяв" in name.lower():
            columns = connection.execute(
                f'PRAGMA table_info("{name}")'
            ).fetchall()

            print(
                "   Поля:",
                ", ".join(col["name"] for col in columns)
            )

finally:
    connection.close()
