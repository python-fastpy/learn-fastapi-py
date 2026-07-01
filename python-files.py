# ╔══════════════════════════════════════════════════════════════════════╗
# ║           PYTHON FILE & JSON HANDLING — All Concepts Guide          ║
# ║                                                                     ║
# ║  File = data stored on disk (text, CSV, JSON, binary, etc.)         ║
# ║  Python has built-in tools to read, write, and manipulate files     ║
# ║                                                                     ║
# ║  Key rule: ALWAYS use "with open(...)" — it auto-closes the file    ║
# ║  even if an error occurs (context manager pattern)                  ║
# ╚══════════════════════════════════════════════════════════════════════╝

import os
import json
import csv
import shutil
import tempfile
from pathlib import Path


# ════════════════════════════════════════════════════
# 1. File modes — how to open a file
#
#  "r"  = read        (default, file MUST exist)
#  "w"  = write       (creates file, OVERWRITES if exists)
#  "a"  = append      (creates file, ADDS to end)
#  "x"  = exclusive   (creates file, ERROR if exists)
#  "r+" = read+write  (file MUST exist)
#  "w+" = write+read  (creates/overwrites)
#  "a+" = append+read (creates, pointer at end)
#
#  Add "b" for binary: "rb", "wb", "ab"
#  Add "t" for text (default): "rt" same as "r"
# ════════════════════════════════════════════════════

print("=" * 50)
print("1. File modes overview")
print("=" * 50)

modes = {
    "r":  "Read only (file must exist)",
    "w":  "Write only (creates/overwrites)",
    "a":  "Append only (creates/adds to end)",
    "x":  "Exclusive create (error if exists)",
    "r+": "Read + Write (file must exist)",
    "w+": "Write + Read (creates/overwrites)",
    "a+": "Append + Read (pointer at end)",
    "rb": "Read binary (images, PDFs, etc.)",
    "wb": "Write binary",
}
for mode, desc in modes.items():
    print(f"  '{mode}' → {desc}")

print("=" * 50)


# ════════════════════════════════════════════════════
# 2. Writing a text file — "w" mode
#
#  "w" creates the file if it doesn't exist
#  "w" OVERWRITES everything if file already exists
#  write() returns number of characters written
# ════════════════════════════════════════════════════

print("2. Writing a text file")

with open("sample.txt", "w") as f:
    f.write("Line 1: Hello World\n")       # write a string
    f.write("Line 2: Python is great\n")
    f.write("Line 3: File handling\n")
    chars = f.write("Line 4: Last line\n")
    print(f"  Last write wrote {chars} characters")

print("  sample.txt created with 4 lines")

# writelines() — write a list of strings (no newline added automatically)
lines = ["Apple\n", "Banana\n", "Cherry\n"]
with open("fruits.txt", "w") as f:
    f.writelines(lines)
print("  fruits.txt created with writelines()")

print("=" * 50)


# ════════════════════════════════════════════════════
# 3. Reading a text file — ALL methods
#
#  read()       → entire file as one string
#  readline()   → one line at a time
#  readlines()  → all lines as a list
#  for line in f → iterate line by line (best for large files)
# ════════════════════════════════════════════════════

print("3. Reading a text file — 4 methods")

# Method A: read() — entire file as one string
print("\n  Method A: read() — entire file")
with open("sample.txt", "r") as f:
    content = f.read()
    print(f"  {repr(content[:50])}...")   # first 50 chars

# Method B: read(n) — read N characters
print("\n  Method B: read(10) — first 10 chars")
with open("sample.txt", "r") as f:
    chunk = f.read(10)
    print(f"  Got: {repr(chunk)}")

# Method C: readline() — one line at a time
print("\n  Method C: readline() — one line")
with open("sample.txt", "r") as f:
    first_line = f.readline()      # reads line 1
    second_line = f.readline()     # reads line 2
    print(f"  Line 1: {first_line.strip()}")
    print(f"  Line 2: {second_line.strip()}")

# Method D: readlines() — all lines as a list
print("\n  Method D: readlines() — list of lines")
with open("sample.txt", "r") as f:
    all_lines = f.readlines()
    print(f"  Got {len(all_lines)} lines: {[l.strip() for l in all_lines]}")

# Method E: for loop — BEST for large files (memory efficient)
print("\n  Method E: for loop — line by line")
with open("sample.txt", "r") as f:
    for i, line in enumerate(f, 1):
        print(f"    Line {i}: {line.strip()}")

print("=" * 50)


# ════════════════════════════════════════════════════
# 4. Append to a file — "a" mode
#
#  Adds to the END of the file
#  Does NOT overwrite existing content
#  Creates the file if it doesn't exist
# ════════════════════════════════════════════════════

print("4. Append to file")

with open("sample.txt", "a") as f:
    f.write("Line 5: Appended line\n")
    f.write("Line 6: Another appended line\n")

with open("sample.txt", "r") as f:
    lines = f.readlines()
    print(f"  File now has {len(lines)} lines (was 4, added 2)")

print("=" * 50)


# ════════════════════════════════════════════════════
# 5. Exclusive create — "x" mode
#
#  Creates a NEW file
#  Raises FileExistsError if file already exists
#  Useful to prevent accidental overwrites
# ════════════════════════════════════════════════════

print("5. Exclusive create (x mode)")

try:
    with open("sample.txt", "x") as f:    # already exists!
        f.write("This won't work")
except FileExistsError:
    print("  FileExistsError: sample.txt already exists")

# Works for new files
with open("new_file.txt", "x") as f:
    f.write("Created with x mode\n")
    print("  new_file.txt created successfully")

print("=" * 50)


# ════════════════════════════════════════════════════
# 6. Read + Write mode — "r+"
#
#  Can both read and write
#  File MUST exist (doesn't create)
#  Pointer starts at beginning
# ════════════════════════════════════════════════════

print("6. Read + Write (r+ mode)")

with open("sample.txt", "r+") as f:
    content = f.read()                  # read everything
    print(f"  Read {len(content)} characters")
    f.write("Added at the end!\n")      # pointer is now at end, so writes at end

# w+ mode — write + read (creates/overwrites)
with open("temp_rw.txt", "w+") as f:
    f.write("Hello from w+ mode\n")
    f.seek(0)                           # move pointer back to start
    content = f.read()
    print(f"  w+ mode: {content.strip()}")

print("=" * 50)


# ════════════════════════════════════════════════════
# 7. File pointer — seek() and tell()
#
#  tell()    → current position (in bytes)
#  seek(n)   → move pointer to position n
#  seek(0)   → go back to beginning
#  seek(0,2) → go to end of file
# ════════════════════════════════════════════════════

print("7. File pointer — seek() and tell()")

with open("sample.txt", "r") as f:
    print(f"  Position at start: {f.tell()}")       # 0

    f.read(10)
    print(f"  After read(10): {f.tell()}")           # 10

    f.seek(0)                                        # go back to start
    print(f"  After seek(0): {f.tell()}")            # 0

    f.seek(0, 2)                                     # go to end (0 offset from end)
    print(f"  At end of file: {f.tell()} bytes")

    f.seek(5)
    partial = f.read(15)
    print(f"  Read from position 5: {repr(partial)}")

print("=" * 50)


# ════════════════════════════════════════════════════
# 8. File encoding — handling special characters
#
#  Default encoding varies by OS
#  Always specify encoding="utf-8" for consistency
#  Other encodings: "ascii", "latin-1", "utf-16"
# ════════════════════════════════════════════════════

print("8. File encoding")

# Write with encoding
with open("encoded.txt", "w", encoding="utf-8") as f:
    f.write("English: Hello\n")
    f.write("Japanese: こんにちは\n")
    f.write("Emoji: 🐍🎉\n")
    f.write("French: café résumé\n")

# Read with encoding
with open("encoded.txt", "r", encoding="utf-8") as f:
    for line in f:
        print(f"  {line.strip()}")

# Reading with wrong encoding → errors
try:
    with open("encoded.txt", "r", encoding="ascii") as f:
        f.read()
except UnicodeDecodeError as e:
    print(f"  Wrong encoding error: {type(e).__name__}")

# errors="ignore" — skip bad characters
with open("encoded.txt", "r", encoding="ascii", errors="ignore") as f:
    content = f.read()
    print(f"  With errors='ignore': {repr(content[:30])}...")

# errors="replace" — replace bad chars with ?
with open("encoded.txt", "r", encoding="ascii", errors="replace") as f:
    content = f.read()
    print(f"  With errors='replace': {repr(content[:30])}...")

print("=" * 50)


# ════════════════════════════════════════════════════
# 9. Binary files — "rb" / "wb"
#
#  Use for images, PDFs, executables, etc.
#  read/write bytes, not strings
#  No encoding parameter needed
# ════════════════════════════════════════════════════

print("9. Binary files")

# Write binary data
data = bytes([72, 101, 108, 108, 111])    # "Hello" in bytes
with open("binary.dat", "wb") as f:
    f.write(data)
    f.write(b"\x00\x01\x02\x03")          # raw bytes
print(f"  Wrote {len(data) + 4} bytes to binary.dat")

# Read binary data
with open("binary.dat", "rb") as f:
    content = f.read()
    print(f"  Read bytes: {content}")
    print(f"  As text: {content[:5].decode('utf-8')}")
    print(f"  As hex: {content.hex()}")

# Copy a file in binary mode (works for ANY file type)
with open("binary.dat", "rb") as src:
    with open("binary_copy.dat", "wb") as dst:
        dst.write(src.read())
print("  Copied binary.dat → binary_copy.dat")

# Read binary in chunks (for large files)
with open("binary.dat", "rb") as f:
    while True:
        chunk = f.read(4)    # read 4 bytes at a time
        if not chunk:
            break
        print(f"  Chunk: {chunk}")

print("=" * 50)


# ════════════════════════════════════════════════════
# 10. os module — file system operations
#
#  os.path   — check if file exists, get size, etc.
#  os.rename — rename a file
#  os.remove — delete a file
#  os.mkdir  — create directory
#  os.listdir — list files in directory
# ════════════════════════════════════════════════════

print("10. os module — file operations")

# Check if file exists
print(f"  sample.txt exists: {os.path.exists('sample.txt')}")
print(f"  fake.txt exists: {os.path.exists('fake.txt')}")

# File info
print(f"  Size of sample.txt: {os.path.getsize('sample.txt')} bytes")
print(f"  Is file: {os.path.isfile('sample.txt')}")
print(f"  Is directory: {os.path.isdir('sample.txt')}")
print(f"  Absolute path: {os.path.abspath('sample.txt')}")

# Get file extension
filename = "report.pdf"
name, ext = os.path.splitext(filename)
print(f"  '{filename}' → name='{name}', ext='{ext}'")

# Join paths (cross-platform)
full_path = os.path.join("folder", "subfolder", "file.txt")
print(f"  Joined path: {full_path}")

# Get directory and filename from path
path = "/home/user/documents/report.pdf"
print(f"  Directory: {os.path.dirname(path)}")
print(f"  Filename: {os.path.basename(path)}")

# List files in current directory
files = [f for f in os.listdir(".") if f.endswith(".txt")]
print(f"  .txt files in current dir: {files}")

# Rename a file
os.rename("new_file.txt", "renamed_file.txt")
print("  Renamed new_file.txt → renamed_file.txt")

# Create and remove directory
os.makedirs("test_dir/sub_dir", exist_ok=True)
print("  Created test_dir/sub_dir")

print("=" * 50)


# ════════════════════════════════════════════════════
# 11. pathlib — modern file path handling (Python 3.4+)
#
#  Path objects are cleaner than os.path strings
#  Use / operator to join paths
#  Has methods for everything os.path does
# ════════════════════════════════════════════════════

print("11. pathlib — modern path handling")

p = Path("sample.txt")

# File info
print(f"  Name: {p.name}")                # "sample.txt"
print(f"  Stem: {p.stem}")                # "sample" (without extension)
print(f"  Suffix: {p.suffix}")            # ".txt"
print(f"  Exists: {p.exists()}")          # True
print(f"  Is file: {p.is_file()}")        # True
print(f"  Absolute: {p.absolute()}")
print(f"  Size: {p.stat().st_size} bytes")

# Join paths with / operator (much cleaner than os.path.join)
data_path = Path("data") / "2024" / "report.csv"
print(f"  Joined: {data_path}")

# Parent directory
p2 = Path("/home/user/docs/file.txt")
print(f"  Parent: {p2.parent}")           # /home/user/docs
print(f"  Parents: {list(p2.parents)}")   # all parent dirs

# Read/write with pathlib (no need for open())
Path("pathlib_test.txt").write_text("Hello from pathlib!\nLine 2\n", encoding="utf-8")
content = Path("pathlib_test.txt").read_text(encoding="utf-8")
print(f"  pathlib read: {content.strip()}")

# Binary read/write
Path("pathlib_bin.dat").write_bytes(b"binary data here")
data = Path("pathlib_bin.dat").read_bytes()
print(f"  pathlib binary: {data}")

# Glob — find files by pattern
print("  .txt files (glob):")
for txt_file in Path(".").glob("*.txt"):
    print(f"    {txt_file}")

# Recursive glob
# for py_file in Path(".").rglob("*.py"):   # searches subdirectories too
#     print(f"    {py_file}")

# Create/change path parts
p3 = Path("report.txt")
print(f"  Change suffix: {p3.with_suffix('.pdf')}")     # report.pdf
print(f"  Change name: {p3.with_name('summary.txt')}")  # summary.txt

print("=" * 50)


# ════════════════════════════════════════════════════
# 12. Temporary files — tempfile module
#
#  Auto-deleted when closed (or on program exit)
#  Useful for intermediate data processing
# ════════════════════════════════════════════════════

print("12. Temporary files")

# Temporary file — auto-deleted when closed
with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tmp:
    tmp.write("Temporary data\n")
    tmp_name = tmp.name
    print(f"  Temp file: {tmp_name}")

# Read it back
with open(tmp_name, "r") as f:
    print(f"  Content: {f.read().strip()}")

os.unlink(tmp_name)    # manually delete since delete=False

# Temporary directory
with tempfile.TemporaryDirectory() as tmpdir:
    print(f"  Temp directory: {tmpdir}")
    # Write file inside temp dir
    temp_file = os.path.join(tmpdir, "data.txt")
    with open(temp_file, "w") as f:
        f.write("Data in temp dir")
    print(f"  File exists: {os.path.exists(temp_file)}")
# Directory and contents auto-deleted here
print(f"  Temp dir still exists: {os.path.exists(tmpdir)}")   # False

print("=" * 50)


# ════════════════════════════════════════════════════
# 13. shutil — copy, move, delete files and directories
# ════════════════════════════════════════════════════

print("13. shutil — copy, move, delete")

# Copy file
shutil.copy("sample.txt", "sample_backup.txt")
print("  Copied sample.txt → sample_backup.txt")

# Copy with metadata (timestamps, permissions)
shutil.copy2("sample.txt", "sample_backup2.txt")
print("  Copied with metadata → sample_backup2.txt")

# Move/rename file
shutil.move("renamed_file.txt", "moved_file.txt")
print("  Moved renamed_file.txt → moved_file.txt")

# Copy entire directory
if os.path.exists("test_dir_copy"):
    shutil.rmtree("test_dir_copy")
shutil.copytree("test_dir", "test_dir_copy")
print("  Copied test_dir → test_dir_copy")

# Remove directory and all contents
shutil.rmtree("test_dir_copy")
print("  Removed test_dir_copy (and all contents)")

# Disk usage
total, used, free = shutil.disk_usage(".")
print(f"  Disk: total={total // (1024**3)}GB, used={used // (1024**3)}GB, free={free // (1024**3)}GB")

print("=" * 50)


# ════════════════════════════════════════════════════
# 14. Reading file with error handling
#
#  Always handle: FileNotFoundError, PermissionError,
#  IsADirectoryError, UnicodeDecodeError
# ════════════════════════════════════════════════════

print("14. Error handling for files")

def safe_read_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"  ERROR: File '{filepath}' not found")
    except PermissionError:
        print(f"  ERROR: No permission to read '{filepath}'")
    except IsADirectoryError:
        print(f"  ERROR: '{filepath}' is a directory, not a file")
    except UnicodeDecodeError:
        print(f"  ERROR: Cannot decode '{filepath}' as UTF-8")
    except OSError as e:
        print(f"  ERROR: OS error reading '{filepath}': {e}")
    return None

safe_read_file("sample.txt")          # works
safe_read_file("nonexistent.txt")     # FileNotFoundError
safe_read_file("test_dir")            # IsADirectoryError

print("=" * 50)


# ════════════════════════════════════════════════════════════════════
#                        JSON HANDLING
# ════════════════════════════════════════════════════════════════════


# ════════════════════════════════════════════════════
# 15. JSON basics — Python dict ↔ JSON string
#
#  json.dumps() = Python dict → JSON string (serialize)
#  json.loads() = JSON string → Python dict (deserialize)
#
#  Python           JSON
#  dict       →     object {}
#  list       →     array []
#  str        →     string ""
#  int/float  →     number
#  True/False →     true/false
#  None       →     null
# ════════════════════════════════════════════════════

print("15. JSON basics — dumps() and loads()")

# Python dict → JSON string
data = {
    "name": "Alice",
    "age": 30,
    "active": True,
    "scores": [95, 87, 92],
    "address": None,
}

json_string = json.dumps(data)
print(f"  json.dumps(): {json_string}")
# {"name": "Alice", "age": 30, "active": true, "scores": [95, 87, 92], "address": null}

# Pretty print with indent
json_pretty = json.dumps(data, indent=2)
print(f"  Pretty JSON:\n{json_pretty}")

# Sort keys alphabetically
json_sorted = json.dumps(data, sort_keys=True, indent=2)
print(f"  Sorted keys:\n{json_sorted}")

# JSON string → Python dict
json_input = '{"name": "Bob", "age": 25, "active": false}'
parsed = json.loads(json_input)
print(f"\n  json.loads(): {parsed}")
print(f"  Type: {type(parsed)}")           # <class 'dict'>
print(f"  Name: {parsed['name']}")         # "Bob"
print(f"  Active: {parsed['active']}")     # False (Python bool)

print("=" * 50)


# ════════════════════════════════════════════════════
# 16. JSON formatting options — dumps() parameters
#
#  indent       = pretty print with indentation
#  sort_keys    = alphabetical key order
#  separators   = control spacing
#  ensure_ascii = allow non-ASCII characters
#  default      = handle non-serializable types
# ════════════════════════════════════════════════════

print("16. JSON formatting options")

data = {"name": "Café", "price": 4.50, "available": True}

# Compact (no spaces) — for APIs/network
compact = json.dumps(data, separators=(",", ":"))
print(f"  Compact:  {compact}")
# {"name":"Café","price":4.5,"available":true}

# Default (with spaces)
default = json.dumps(data)
print(f"  Default:  {default}")
# {"name": "Café", "price": 4.5, "available": true}

# Allow non-ASCII characters (no \u escaping)
non_ascii = json.dumps(data, ensure_ascii=False)
print(f"  Non-ASCII: {non_ascii}")
# {"name": "Café", "price": 4.5, "available": true}

# Custom indent character
indented = json.dumps(data, indent=4)
print(f"  4-space indent:\n{indented}")

print("=" * 50)


# ════════════════════════════════════════════════════
# 17. Write JSON to file — json.dump()
#
#  json.dump()  = write dict to FILE
#  json.dumps() = convert dict to STRING
#  (dump vs dumps — "s" = string)
# ════════════════════════════════════════════════════

print("17. Write JSON to file — json.dump()")

users = [
    {"id": 1, "name": "Alice", "email": "alice@test.com", "active": True},
    {"id": 2, "name": "Bob", "email": "bob@test.com", "active": False},
    {"id": 3, "name": "Charlie", "email": "charlie@test.com", "active": True},
]

# Write to JSON file
with open("users.json", "w", encoding="utf-8") as f:
    json.dump(users, f, indent=2, ensure_ascii=False)
print("  Written users.json (list of 3 users)")

# Write single object
config = {
    "app_name": "MyApp",
    "version": "1.0.0",
    "debug": False,
    "database": {
        "host": "localhost",
        "port": 5432,
        "name": "mydb",
    },
    "allowed_origins": ["http://localhost:3000", "https://myapp.com"],
}

with open("config.json", "w", encoding="utf-8") as f:
    json.dump(config, f, indent=2)
print("  Written config.json (nested object)")

print("=" * 50)


# ════════════════════════════════════════════════════
# 18. Read JSON from file — json.load()
#
#  json.load()  = read FILE → Python dict/list
#  json.loads() = read STRING → Python dict/list
# ════════════════════════════════════════════════════

print("18. Read JSON from file — json.load()")

# Read list of users
with open("users.json", "r", encoding="utf-8") as f:
    users_loaded = json.load(f)

print(f"  Type: {type(users_loaded)}")     # <class 'list'>
print(f"  Count: {len(users_loaded)}")     # 3
for user in users_loaded:
    print(f"    {user['name']} ({user['email']}) — active: {user['active']}")

# Read nested config
with open("config.json", "r", encoding="utf-8") as f:
    config_loaded = json.load(f)

print(f"\n  App: {config_loaded['app_name']}")
print(f"  DB host: {config_loaded['database']['host']}")
print(f"  DB port: {config_loaded['database']['port']}")
print(f"  Origins: {config_loaded['allowed_origins']}")

print("=" * 50)


# ════════════════════════════════════════════════════
# 19. JSON error handling
#
#  json.JSONDecodeError — invalid JSON
#  KeyError — missing key in parsed data
#  TypeError — non-serializable type in dumps()
# ════════════════════════════════════════════════════

print("19. JSON error handling")

# Invalid JSON string
bad_json_strings = [
    "{'name': 'Alice'}",            # single quotes (invalid JSON)
    '{"name": "Alice",}',           # trailing comma
    '{name: "Alice"}',              # unquoted key
    'not json at all',              # not JSON
    '',                              # empty string
]

for bad in bad_json_strings:
    try:
        json.loads(bad)
    except json.JSONDecodeError as e:
        print(f"  Invalid: {repr(bad[:30])} → {e.msg}")

# Safe JSON loading function
def safe_load_json(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"  File not found: {filepath}")
    except json.JSONDecodeError as e:
        print(f"  Invalid JSON in {filepath}: {e.msg} at line {e.lineno}")
    except PermissionError:
        print(f"  No permission: {filepath}")
    return None

result = safe_load_json("users.json")
print(f"  Valid file: got {len(result)} users")

safe_load_json("nonexistent.json")    # file not found

# Write bad JSON and try to read it
Path("bad.json").write_text("{invalid json}", encoding="utf-8")
safe_load_json("bad.json")            # invalid JSON

print("=" * 50)


# ════════════════════════════════════════════════════
# 20. Handling non-serializable types
#
#  JSON can't serialize: datetime, set, bytes, custom objects
#  Solution 1: default= function
#  Solution 2: custom JSONEncoder class
# ════════════════════════════════════════════════════

print("20. Custom JSON serialization")

from datetime import datetime, date

# Problem: datetime is not JSON serializable
data_with_date = {
    "event": "Meeting",
    "date": datetime(2024, 6, 15, 14, 30),
    "tags": {"python", "coding"},     # set — not serializable
    "raw": b"hello",                   # bytes — not serializable
}

# Solution 1: default= function
def json_serializer(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, set):
        return list(obj)
    if isinstance(obj, bytes):
        return obj.decode("utf-8")
    raise TypeError(f"Type {type(obj)} not serializable")

result = json.dumps(data_with_date, default=json_serializer, indent=2)
print(f"  With default= function:\n{result}")

# Solution 2: custom JSONEncoder class
class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, set):
            return sorted(list(obj))
        if isinstance(obj, bytes):
            return obj.decode("utf-8")
        return super().default(obj)

result2 = json.dumps(data_with_date, cls=CustomEncoder, indent=2)
print(f"\n  With custom encoder:\n{result2}")

print("=" * 50)


# ════════════════════════════════════════════════════
# 21. Custom JSON deserialization — object_hook
#
#  object_hook = function called for every JSON object {}
#  Convert JSON back to custom Python objects
# ════════════════════════════════════════════════════

print("21. Custom deserialization — object_hook")

# JSON with dates as strings
json_with_dates = '''
{
    "event": "Meeting",
    "date": "2024-06-15T14:30:00",
    "attendees": [
        {"name": "Alice", "joined": "2024-01-01"},
        {"name": "Bob", "joined": "2023-06-15"}
    ]
}
'''

# Convert date strings back to datetime objects
def date_decoder(obj):
    for key, value in obj.items():
        if isinstance(value, str):
            # Try to parse as datetime
            for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
                try:
                    obj[key] = datetime.strptime(value, fmt)
                    break
                except ValueError:
                    continue
    return obj

parsed = json.loads(json_with_dates, object_hook=date_decoder)
print(f"  Event: {parsed['event']}")
print(f"  Date type: {type(parsed['date'])}")     # <class 'datetime.datetime'>
print(f"  Date: {parsed['date']}")                # 2024-06-15 14:30:00

for a in parsed["attendees"]:
    print(f"  {a['name']} joined: {a['joined']} (type: {type(a['joined']).__name__})")

print("=" * 50)


# ════════════════════════════════════════════════════
# 22. Modify JSON file — read, change, write back
#
#  Common pattern: load → modify → save
# ════════════════════════════════════════════════════

print("22. Modify JSON file")

# Read
with open("users.json", "r", encoding="utf-8") as f:
    users = json.load(f)

print(f"  Before: {len(users)} users")

# Modify — add a user
users.append({"id": 4, "name": "Diana", "email": "diana@test.com", "active": True})

# Modify — update existing user
for user in users:
    if user["name"] == "Bob":
        user["active"] = True

# Modify — remove a user
users = [u for u in users if u["name"] != "Charlie"]

# Write back
with open("users.json", "w", encoding="utf-8") as f:
    json.dump(users, f, indent=2)

print(f"  After: {len(users)} users (added Diana, activated Bob, removed Charlie)")

# Verify
with open("users.json", "r", encoding="utf-8") as f:
    final = json.load(f)
    for u in final:
        print(f"    {u['name']}: active={u['active']}")

print("=" * 50)


# ════════════════════════════════════════════════════
# 23. Nested JSON — access and modify deep values
# ════════════════════════════════════════════════════

print("23. Nested JSON — deep access")

api_response = {
    "status": "success",
    "data": {
        "user": {
            "name": "Alice",
            "profile": {
                "bio": "Developer",
                "social": {
                    "twitter": "@alice",
                    "github": "alice-dev",
                },
            },
            "orders": [
                {"id": 1, "items": [{"name": "Laptop", "price": 999}]},
                {"id": 2, "items": [{"name": "Mouse", "price": 25}, {"name": "Keyboard", "price": 75}]},
            ],
        }
    },
}

# Deep access
print(f"  Twitter: {api_response['data']['user']['profile']['social']['twitter']}")
print(f"  First order item: {api_response['data']['user']['orders'][0]['items'][0]['name']}")

# Safe deep access with .get() — avoids KeyError
twitter = api_response.get("data", {}).get("user", {}).get("profile", {}).get("social", {}).get("twitter", "N/A")
print(f"  Safe access: {twitter}")

# Missing key with .get() — returns default
linkedin = api_response.get("data", {}).get("user", {}).get("profile", {}).get("social", {}).get("linkedin", "Not found")
print(f"  Missing key: {linkedin}")

# Calculate total of all order items
total = sum(
    item["price"]
    for order in api_response["data"]["user"]["orders"]
    for item in order["items"]
)
print(f"  Total order value: ${total}")

print("=" * 50)


# ════════════════════════════════════════════════════
# 24. JSON with pathlib — cleaner syntax
# ════════════════════════════════════════════════════

print("24. JSON with pathlib")

data = {"framework": "FastAPI", "version": "0.100.0", "features": ["async", "pydantic", "openapi"]}

# Write JSON
Path("framework.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
print("  Written framework.json")

# Read JSON
loaded = json.loads(Path("framework.json").read_text(encoding="utf-8"))
print(f"  Read: {loaded['framework']} v{loaded['version']}")

print("=" * 50)


# ════════════════════════════════════════════════════
# 25. CSV files — reading and writing
#
#  CSV = Comma-Separated Values
#  csv.reader  → read rows as lists
#  csv.writer  → write rows as lists
#  csv.DictReader → read rows as dicts (column names as keys)
#  csv.DictWriter → write dicts as rows
# ════════════════════════════════════════════════════

print("25. CSV files — read/write")

# Write CSV with csv.writer
with open("employees.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Name", "Department", "Salary"])    # header
    writer.writerow(["Alice", "Engineering", 90000])
    writer.writerow(["Bob", "Marketing", 70000])
    writer.writerow(["Charlie", "Engineering", 85000])
    writer.writerows([                                    # write multiple rows
        ["Diana", "HR", 75000],
        ["Eve", "Marketing", 72000],
    ])
print("  Written employees.csv")

# Read CSV with csv.reader
print("\n  csv.reader (rows as lists):")
with open("employees.csv", "r", newline="", encoding="utf-8") as f:
    reader = csv.reader(f)
    header = next(reader)    # skip header row
    print(f"    Header: {header}")
    for row in reader:
        print(f"    {row[0]}: {row[1]}, ${row[2]}")

# Read CSV with DictReader (rows as dicts — RECOMMENDED)
print("\n  csv.DictReader (rows as dicts):")
with open("employees.csv", "r", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        print(f"    {row['Name']}: {row['Department']}, ${row['Salary']}")

# Write CSV with DictWriter
with open("products.csv", "w", newline="", encoding="utf-8") as f:
    fieldnames = ["id", "name", "price", "in_stock"]
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerow({"id": 1, "name": "Laptop", "price": 999.99, "in_stock": True})
    writer.writerow({"id": 2, "name": "Mouse", "price": 24.99, "in_stock": True})
    writer.writerow({"id": 3, "name": "Monitor", "price": 399.99, "in_stock": False})
print("  Written products.csv with DictWriter")

# Custom delimiter (TSV — tab separated)
with open("data.tsv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f, delimiter="\t")
    writer.writerow(["Name", "Score"])
    writer.writerow(["Alice", 95])
    writer.writerow(["Bob", 87])
print("  Written data.tsv (tab-separated)")

print("=" * 50)


# ════════════════════════════════════════════════════
# 26. Convert between JSON and CSV
# ════════════════════════════════════════════════════

print("26. JSON ↔ CSV conversion")

# JSON → CSV
json_data = [
    {"name": "Alice", "age": 30, "city": "NYC"},
    {"name": "Bob", "age": 25, "city": "LA"},
    {"name": "Charlie", "age": 35, "city": "Chicago"},
]

with open("people.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=json_data[0].keys())
    writer.writeheader()
    writer.writerows(json_data)
print("  JSON → CSV: people.csv")

# CSV → JSON
with open("people.csv", "r", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    csv_as_json = list(reader)    # list of OrderedDicts → list of dicts

with open("people.json", "w", encoding="utf-8") as f:
    json.dump(csv_as_json, f, indent=2)
print("  CSV → JSON: people.json")

# Verify
with open("people.json", "r", encoding="utf-8") as f:
    loaded = json.load(f)
    for person in loaded:
        print(f"    {person['name']}, age {person['age']}, {person['city']}")

print("=" * 50)


# ════════════════════════════════════════════════════
# 27. Reading large files efficiently
#
#  DON'T read() entire file if it's huge (GBs)
#  Use line-by-line or chunk-based reading
# ════════════════════════════════════════════════════

print("27. Large file handling")

# Create a somewhat large file for demo
with open("large_demo.txt", "w") as f:
    for i in range(1000):
        f.write(f"Line {i}: This is test data for large file demo\n")

# Method A: Line by line (BEST for text files)
line_count = 0
with open("large_demo.txt", "r") as f:
    for line in f:
        line_count += 1
print(f"  Line-by-line: {line_count} lines")

# Method B: Chunk-based reading (for binary or when you need raw chunks)
total_bytes = 0
with open("large_demo.txt", "rb") as f:
    while True:
        chunk = f.read(8192)    # 8KB chunks
        if not chunk:
            break
        total_bytes += len(chunk)
print(f"  Chunk-based: {total_bytes} bytes")

# Method C: Read first/last N lines
with open("large_demo.txt", "r") as f:
    first_5 = [next(f).strip() for _ in range(5)]
print(f"  First 5 lines: {first_5[:2]}...")

# Count specific pattern
word_count = 0
with open("large_demo.txt", "r") as f:
    for line in f:
        if "test data" in line:
            word_count += 1
print(f"  Lines containing 'test data': {word_count}")

print("=" * 50)


# ════════════════════════════════════════════════════
# 28. JSON Lines (JSONL) — one JSON object per line
#
#  Each line is a valid JSON object
#  Used for logs, streaming data, large datasets
#  Much easier to append to than regular JSON
# ════════════════════════════════════════════════════

print("28. JSON Lines (JSONL)")

# Write JSONL
events = [
    {"timestamp": "2024-01-01T10:00:00", "event": "login", "user": "alice"},
    {"timestamp": "2024-01-01T10:05:00", "event": "page_view", "user": "alice", "page": "/dashboard"},
    {"timestamp": "2024-01-01T10:10:00", "event": "click", "user": "bob", "button": "submit"},
]

with open("events.jsonl", "w", encoding="utf-8") as f:
    for event in events:
        f.write(json.dumps(event) + "\n")    # one JSON per line
print("  Written events.jsonl")

# Append to JSONL (easy — just add a line)
with open("events.jsonl", "a", encoding="utf-8") as f:
    f.write(json.dumps({"timestamp": "2024-01-01T10:15:00", "event": "logout", "user": "alice"}) + "\n")
print("  Appended 1 event")

# Read JSONL
print("  Reading events:")
with open("events.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        event = json.loads(line.strip())
        print(f"    [{event['timestamp']}] {event['event']} by {event['user']}")

# Filter JSONL
print("  Alice's events only:")
with open("events.jsonl", "r", encoding="utf-8") as f:
    alice_events = [json.loads(line) for line in f if '"alice"' in line]
    for e in alice_events:
        print(f"    {e['event']}")

print("=" * 50)


# ════════════════════════════════════════════════════
# 29. JSON Schema validation (manual)
#
#  Validate JSON structure before using it
#  Check required keys, types, value ranges
# ════════════════════════════════════════════════════

print("29. JSON validation (manual)")

def validate_user(data):
    errors = []

    # Required fields
    required = ["name", "email", "age"]
    for field in required:
        if field not in data:
            errors.append(f"Missing required field: {field}")

    # Type checks
    if "name" in data and not isinstance(data["name"], str):
        errors.append("'name' must be a string")
    if "age" in data and not isinstance(data["age"], int):
        errors.append("'age' must be an integer")
    if "age" in data and isinstance(data["age"], int) and not (0 < data["age"] < 150):
        errors.append("'age' must be between 1 and 149")
    if "email" in data and isinstance(data["email"], str) and "@" not in data["email"]:
        errors.append("'email' must contain @")

    return errors

# Valid
errors = validate_user({"name": "Alice", "email": "alice@test.com", "age": 30})
print(f"  Valid user: {len(errors)} errors")

# Invalid
errors = validate_user({"name": 123, "age": -5})
print(f"  Invalid user: {errors}")

print("=" * 50)


# ════════════════════════════════════════════════════
# 30. JSON merge and diff
# ════════════════════════════════════════════════════

print("30. JSON merge and diff")

# Merge two dicts (shallow)
defaults = {"theme": "light", "language": "en", "notifications": True, "font_size": 14}
user_prefs = {"theme": "dark", "font_size": 16}

# Method 1: ** unpacking (Python 3.5+)
merged = {**defaults, **user_prefs}     # user_prefs overrides defaults
print(f"  Merged (** method): {merged}")

# Method 2: | operator (Python 3.9+)
merged2 = defaults | user_prefs
print(f"  Merged (| method): {merged2}")

# Deep merge (nested dicts)
def deep_merge(base, override):
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result

config_default = {"db": {"host": "localhost", "port": 5432}, "debug": False}
config_prod = {"db": {"host": "prod-server"}, "debug": False}

deep_merged = deep_merge(config_default, config_prod)
print(f"  Deep merged: {deep_merged}")
# {"db": {"host": "prod-server", "port": 5432}, "debug": False}

# Simple diff — find what changed
def json_diff(old, new):
    changes = {}
    all_keys = set(list(old.keys()) + list(new.keys()))
    for key in all_keys:
        if key not in old:
            changes[key] = {"added": new[key]}
        elif key not in new:
            changes[key] = {"removed": old[key]}
        elif old[key] != new[key]:
            changes[key] = {"old": old[key], "new": new[key]}
    return changes

old_data = {"name": "Alice", "age": 30, "city": "NYC"}
new_data = {"name": "Alice", "age": 31, "country": "US"}

diff = json_diff(old_data, new_data)
print(f"  Diff: {json.dumps(diff, indent=2)}")

print("=" * 50)


# ════════════════════════════════════════════════════
# CLEANUP — remove demo files
# ════════════════════════════════════════════════════

print("CLEANUP — removing demo files")

demo_files = [
    "sample.txt", "fruits.txt", "encoded.txt", "binary.dat", "binary_copy.dat",
    "temp_rw.txt", "pathlib_test.txt", "pathlib_bin.dat", "sample_backup.txt",
    "sample_backup2.txt", "moved_file.txt", "bad.json", "users.json",
    "config.json", "framework.json", "employees.csv", "products.csv",
    "data.tsv", "people.csv", "people.json", "large_demo.txt", "events.jsonl",
]

for f in demo_files:
    if os.path.exists(f):
        os.remove(f)

if os.path.exists("test_dir"):
    shutil.rmtree("test_dir")

print(f"  Removed {len(demo_files)} demo files + test_dir")


# ════════════════════════════════════════════════════
# SUMMARY
#
#  TEXT FILES:
#    open(path, mode)    — "r", "w", "a", "x", "r+", "w+"
#    read(), readline(), readlines(), for line in f
#    write(), writelines()
#    seek(), tell()      — move/check file pointer
#    encoding="utf-8"    — ALWAYS specify for text files
#
#  BINARY FILES:
#    "rb", "wb"          — for images, PDFs, any non-text
#    read/write bytes, not strings
#
#  FILE SYSTEM:
#    os.path             — exists, isfile, getsize, join, split
#    pathlib.Path        — modern alternative (use / for paths)
#    shutil              — copy, move, remove files/dirs
#    tempfile            — auto-cleanup temp files/dirs
#
#  JSON:
#    json.dumps(obj)     — dict → JSON string
#    json.loads(str)     — JSON string → dict
#    json.dump(obj, f)   — dict → JSON file
#    json.load(f)        — JSON file → dict
#    default=func        — handle datetime, set, bytes
#    cls=CustomEncoder   — reusable custom serialization
#    object_hook=func    — custom deserialization
#
#  CSV:
#    csv.reader/writer        — lists
#    csv.DictReader/DictWriter — dicts (recommended)
#    newline=""               — ALWAYS use in open()
#
#  JSONL:
#    One JSON object per line — best for logs/streaming
#    Easy to append (just add a line)
#
#  BEST PRACTICES:
#    Always use "with open(...)" — auto-closes file
#    Always specify encoding="utf-8"
#    Handle errors: FileNotFoundError, JSONDecodeError
#    Use pathlib.Path for modern code
#    Read large files line-by-line, not read()
# ════════════════════════════════════════════════════
