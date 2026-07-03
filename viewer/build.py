"""
Parses all .py learning files from fastapi/ and python/ directories,
splits them into 3 sections (Content, Cheat Sheet, Detailed Reference),
and writes a data.js file for the HTML viewer.

Usage:
    cd learn-fastapi-py/viewer
    python build.py
"""

import json
import os
import re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "data.js")

FOLDERS = ["fastapi", "python"]

CHEAT_SHEET_MARKER = re.compile(r"^#\s*.*CHEAT\s*SHEET", re.IGNORECASE)
REFERENCE_MARKER = re.compile(r"^#\s*.*DETAILED\s*REFERENCE", re.IGNORECASE)
SECTION_DIVIDER = re.compile(r"^#\s*[═]{10,}")


def split_sections(text):
    lines = text.split("\n")
    cheat_start = None
    ref_start = None

    for i, line in enumerate(lines):
        if cheat_start is None and CHEAT_SHEET_MARKER.search(line):
            cheat_start = i
        elif ref_start is None and REFERENCE_MARKER.search(line):
            ref_start = i

    if cheat_start is not None:
        cs = cheat_start
        while cs > 0 and SECTION_DIVIDER.match(lines[cs - 1]):
            cs -= 1
        cheat_start = cs

    if ref_start is not None:
        rs = ref_start
        while rs > 0 and SECTION_DIVIDER.match(lines[rs - 1]):
            rs -= 1
        ref_start = rs

    if cheat_start is not None and ref_start is not None:
        content = "\n".join(lines[:cheat_start]).rstrip()
        cheat_sheet = "\n".join(lines[cheat_start:ref_start]).rstrip()
        reference = "\n".join(lines[ref_start:]).rstrip()
    elif cheat_start is not None:
        content = "\n".join(lines[:cheat_start]).rstrip()
        cheat_sheet = "\n".join(lines[cheat_start:]).rstrip()
        reference = ""
    else:
        content = text.rstrip()
        cheat_sheet = ""
        reference = ""

    return content, cheat_sheet, reference


def parse_files():
    data = {}
    for folder in FOLDERS:
        folder_path = os.path.join(BASE_DIR, folder)
        if not os.path.isdir(folder_path):
            continue

        files = sorted(f for f in os.listdir(folder_path) if f.endswith(".py"))
        folder_data = {}

        for filename in files:
            filepath = os.path.join(folder_path, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()

            if len(text.strip()) < 50:
                continue

            content, cheat_sheet, reference = split_sections(text)
            folder_data[filename] = {
                "content": content,
                "cheatSheet": cheat_sheet,
                "reference": reference,
            }
            print(f"  {folder}/{filename}: content={len(content)}  cheat={len(cheat_sheet)}  ref={len(reference)}")

        data[folder] = folder_data

    return data


def main():
    print("Parsing learning files...")
    data = parse_files()

    total = sum(len(files) for files in data.values())
    print(f"\nParsed {total} files across {len(data)} folders")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("const FILES = ")
        json.dump(data, f, ensure_ascii=False)
        f.write(";\n")

    size_kb = os.path.getsize(OUTPUT_FILE) / 1024
    print(f"Written to {OUTPUT_FILE} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
