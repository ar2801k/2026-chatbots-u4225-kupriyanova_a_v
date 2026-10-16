from pathlib import Path
import re

for n in (1, 2, 3):
    folder = Path(f"lab{n}")
    old = folder / "REPORT.md"
    new = folder / f"lab{n}_report.md"

    if not old.exists():
        print(f"SKIP: {old} not found")
        continue

    content = old.read_text(encoding="utf-8-sig")

    header = f"""# ITMO University — Laboratory Report {n}

| Field | Information |
|---|---|
| **University** | ITMO University |
| **Faculty** | FICT |
| **Course** | Vibe Coding for Business |
| **Academic year** | 2026/2027 |
| **Group** | U4225 |
| **Student** | Kupriyanova Arina Vladimirovna |
| **Laboratory work** | No. {n} |
| **Report prepared** | 16.10.2026 |
| **Defense date** | To be confirmed |

---

"""

    new.write_text(header + content, encoding="utf-8")
    old.unlink()

    print(f"FIXED: lab{n} - one report")

for n in (1, 2, 3):
    folder = Path(f"lab{n}")
    for name in ("README.md", "PROMPTS.md", "TESTING.md"):
        path = folder / name
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8-sig")
        text = re.sub(
            r"REPORT\.md",
            f"lab{n}_report.md",
            text
        )
        path.write_text(text, encoding="utf-8")

print("DONE: reports and local links updated")
