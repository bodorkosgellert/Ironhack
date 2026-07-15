"""One-time helper to apply the Option A folder layout locally."""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FINAL_SRC = ROOT.parent / "_final_project_src"

ARCHIVE = ROOT / "archive" / "bootcamp-original"
LABS_NB = ROOT / "labs" / "notebooks"
LABS_SQL = ROOT / "labs" / "sql"
PROJECT = ROOT / "projects" / "asthma-air-pollution"
V1 = PROJECT / "v1"
V2 = PROJECT / "v2"

CURATED_NOTEBOOKS = [
    "nlp_lab.ipynb",
    "computer vision lab.ipynb",
    "SQLPYBANK.ipynb",
    "Customer Analysis final.ipynb",
    "marketing_customer_analysis_3.ipynb",
    "errorhandling.ipynb",
    "string_operations.ipynb",
]

SQL_FILES = [
    "sql intro.sql",
    "sql_lab_8.sql",
    "SQL_QUERIES 7.sql",
    "class queries.sql",
    "lab_2.5.sql",
    "lab_2.6.sql",
]

SKIP_ARCHIVE = {
    ".git",
    "archive",
    "labs",
    "projects",
    "learning",
    "scripts",
    "requirements.txt",
    ".gitignore",
    "README.md",
}


def main() -> None:
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    LABS_NB.mkdir(parents=True, exist_ok=True)
    LABS_SQL.mkdir(parents=True, exist_ok=True)
    (V1 / "code").mkdir(parents=True, exist_ok=True)
    (V1 / "docs").mkdir(parents=True, exist_ok=True)
    V2.mkdir(parents=True, exist_ok=True)
    (ROOT / "learning").mkdir(parents=True, exist_ok=True)

    for item in ROOT.iterdir():
        if item.name in SKIP_ARCHIVE or item.name.startswith("_"):
            continue
        if item.is_file():
            dest = ARCHIVE / item.name
            if not dest.exists():
                shutil.move(str(item), dest)

    for name in CURATED_NOTEBOOKS:
        src = ARCHIVE / name
        if src.exists():
            dest_name = name.replace(" ", "_").lower()
            if name == "computer vision lab.ipynb":
                dest_name = "computer_vision_lab.ipynb"
            if name == "Customer Analysis final.ipynb":
                dest_name = "customer_analysis_final.ipynb"
            shutil.copy2(src, LABS_NB / dest_name)

    for name in SQL_FILES:
        src = ARCHIVE / name
        if src.exists():
            dest_name = name.replace(" ", "_")
            shutil.copy2(src, LABS_SQL / dest_name)

    if FINAL_SRC.exists():
        nb = FINAL_SRC / "code" / "asthma2.ipynb"
        if nb.exists():
            shutil.copy2(nb, V1 / "code" / "asthma2.ipynb")
        readme = FINAL_SRC / "README.md"
        if readme.exists():
            shutil.copy2(readme, V1 / "ORIGINAL_README.md")
        pptx = FINAL_SRC / "Asthma and air pollution.pptx"
        if pptx.exists():
            shutil.copy2(pptx, V1 / "docs" / pptx.name)

    print("Restructure complete.")


if __name__ == "__main__":
    main()
