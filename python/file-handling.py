# ══════════════════════════════════════════════════════════════════
#  PYTHON FILE, JSON & CSV HANDLING — Condensed Guide
#  Always use "with open(...)" — auto-closes even on error
# ══════════════════════════════════════════════════════════════════

import os, json, csv, shutil, tempfile
from pathlib import Path
from datetime import datetime, date

# ╔══════════════════════════════════════════════════╗
# ║              BEGINNER                            ║
# ╚══════════════════════════════════════════════════╝

# ── 1. File Modes ──────────────────────────────────
#  "r"  = read (default, must exist)    "rb" = read binary
#  "w"  = write (creates/OVERWRITES)    "wb" = write binary
#  "a"  = append (creates/adds to end)  "x"  = exclusive create (error if exists)
#  "r+" = read+write (must exist)       "w+" = write+read (creates/overwrites)
#  Add "b" for binary (images, PDFs). Add "t" for text (default).

# ── 2. Writing Files ──────────────────────────────
with open("sample.txt", "w") as f:
    f.write("Line 1: Hello World\n")
    f.write("Line 2: Python is great\n")
    f.write("Line 3: File handling\n")
    chars = f.write("Line 4: Last line\n")  # returns char count
print(f"Wrote sample.txt ({chars} chars in last write)")

# writelines() — write a list (no auto-newline)
lines = ["Apple\n", "Banana\n", "Cherry\n"]
with open("fruits.txt", "w") as f:
    f.writelines(lines)

# ── 3. Reading Files (2 Best Methods) ─────────────
# Method A: read() — entire file as string (small files)
with open("sample.txt", "r") as f:
    content = f.read()
    print(f"read(): {repr(content[:40])}...")

# Method B: for loop — line by line (BEST for large files, memory efficient)
with open("sample.txt", "r") as f:
    for i, line in enumerate(f, 1):
        print(f"  Line {i}: {line.strip()}")

# Also: readlines() → list of lines, readline() → single line

# ── 4. Append — "a" Mode ─────────────────────────
with open("sample.txt", "a") as f:
    f.write("Line 5: Appended\n")
with open("sample.txt", "r") as f:
    print(f"File now has {len(f.readlines())} lines")  # 5

# ── 5. Exclusive Create — "x" Mode ───────────────
try:
    with open("sample.txt", "x") as f:  # already exists → error
        f.write("won't work")
except FileExistsError:
    print("FileExistsError: sample.txt already exists")

with open("new_file.txt", "x") as f:
    f.write("Created with x mode\n")

# ── 6. Read+Write & File Pointer ─────────────────
with open("temp_rw.txt", "w+") as f:
    f.write("Hello from w+ mode\n")
    f.seek(0)                 # move pointer back to start
    print(f"w+ read: {f.read().strip()}")

# seek(0) → beginning | seek(0,2) → end | tell() → current position
with open("sample.txt", "r") as f:
    f.read(10); print(f"After read(10): {f.tell()}")  # 10
    f.seek(0, 2); print(f"File size: {f.tell()} bytes")

# ── 7. Error Handling ─────────────────────────────
def safe_read_file(filepath):
    """Handle FileNotFoundError, PermissionError, UnicodeDecodeError, etc."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"  ERROR: '{filepath}' not found")
    except PermissionError:
        print(f"  ERROR: No permission for '{filepath}'")
    except IsADirectoryError:
        print(f"  ERROR: '{filepath}' is a directory")
    except UnicodeDecodeError:
        print(f"  ERROR: Cannot decode '{filepath}' as UTF-8")
    return None

safe_read_file("sample.txt")       # works
safe_read_file("nonexistent.txt")  # FileNotFoundError

# ╔══════════════════════════════════════════════════╗
# ║            INTERMEDIATE                          ║
# ╚══════════════════════════════════════════════════╝

# ── 8. Encoding ───────────────────────────────────
# Always specify encoding="utf-8" for cross-platform consistency
with open("encoded.txt", "w", encoding="utf-8") as f:
    f.write("English: Hello\nJapanese: こんにちは\nEmoji: 🐍\n")
with open("encoded.txt", "r", encoding="utf-8") as f:
    content = f.read()  # works with all unicode
# errors="ignore" skips bad chars | errors="replace" uses ? for bad chars
try:
    with open("encoded.txt", "r", encoding="ascii") as f: f.read()
except UnicodeDecodeError: print("Wrong encoding → UnicodeDecodeError")

# ── 9. Binary Files — "rb"/"wb" ──────────────────
data = bytes([72, 101, 108, 108, 111])  # "Hello"
with open("binary.dat", "wb") as f:
    f.write(data)
    f.write(b"\x00\x01\x02\x03")

with open("binary.dat", "rb") as f:
    content = f.read()
    print(f"Bytes: {content}, as text: {content[:5].decode('utf-8')}")

# Copy any file in binary mode
with open("binary.dat", "rb") as src, open("binary_copy.dat", "wb") as dst:
    dst.write(src.read())

# ── 10. JSON Basics — dumps/loads/dump/load ───────
#  json.dumps(obj) → string   |  json.dump(obj, file)  → write to file
#  json.loads(str) → dict     |  json.load(file)       → read from file
#  Mnemonic: "s" = string
#
#  Python→JSON: dict→{}, list→[], str→"", int/float→number,
#               True→true, False→false, None→null

user = {"name": "Alice", "age": 30, "active": True, "scores": [95, 87], "address": None}

json_str = json.dumps(user)                          # dict → string
print(f"dumps: {json_str}")
json_pretty = json.dumps(user, indent=2)             # pretty-print
compact = json.dumps(user, separators=(",", ":"))    # no spaces (for APIs)

parsed = json.loads('{"name": "Bob", "age": 25}')   # string → dict
print(f"loads: {parsed['name']}, type={type(parsed)}")  # Bob, <class 'dict'>

# ── 11. JSON File Read/Write ─────────────────────
users = [
    {"id": 1, "name": "Alice", "email": "alice@test.com", "active": True},
    {"id": 2, "name": "Bob", "email": "bob@test.com", "active": False},
    {"id": 3, "name": "Charlie", "email": "charlie@test.com", "active": True},
]
with open("users.json", "w", encoding="utf-8") as f:
    json.dump(users, f, indent=2, ensure_ascii=False)  # dict → file

with open("users.json", "r", encoding="utf-8") as f:
    loaded = json.load(f)                               # file → dict
print(f"Loaded {len(loaded)} users from users.json")

# Common pattern: load → modify → save
with open("users.json", "r", encoding="utf-8") as f:
    users = json.load(f)
users.append({"id": 4, "name": "Diana", "email": "diana@test.com", "active": True})
users = [u for u in users if u["name"] != "Charlie"]  # remove Charlie
with open("users.json", "w", encoding="utf-8") as f:
    json.dump(users, f, indent=2)
print(f"Modified users.json: now {len(users)} users")

# ── 12. JSON Error Handling ──────────────────────
# Common invalid JSON: single quotes, trailing commas, unquoted keys
for bad in ["{'name': 'Alice'}", '{"name": "Alice",}', 'not json']:
    try: json.loads(bad)
    except json.JSONDecodeError as e: print(f"  Invalid: {repr(bad[:25])} → {e.msg}")

def safe_load_json(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"  File not found: {filepath}")
    except json.JSONDecodeError as e:
        print(f"  Invalid JSON in {filepath}: {e.msg} at line {e.lineno}")
    return None

# ── 13. Nested JSON Access ───────────────────────
api = {"data": {"user": {"profile": {"social": {"twitter": "@alice"}},
       "orders": [{"id": 1, "items": [{"name": "Laptop", "price": 999}]}]}}}

# Direct access (raises KeyError if missing)
print(f"Twitter: {api['data']['user']['profile']['social']['twitter']}")

# Safe deep access with .get() chains
twitter = api.get("data", {}).get("user", {}).get("profile", {}).get("social", {}).get("twitter", "N/A")
linkedin = api.get("data", {}).get("user", {}).get("profile", {}).get("social", {}).get("linkedin", "Not found")
print(f"Safe: twitter={twitter}, linkedin={linkedin}")

# ── 14. CSV Read/Write ───────────────────────────
# csv.writer / csv.reader — rows as lists
with open("employees.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Name", "Department", "Salary"])  # header
    writer.writerow(["Alice", "Engineering", 90000])
    writer.writerows([["Bob", "Marketing", 70000], ["Charlie", "Engineering", 85000]])

with open("employees.csv", "r", newline="", encoding="utf-8") as f:
    reader = csv.reader(f)
    header = next(reader)  # skip header
    for row in reader:
        print(f"  {row[0]}: {row[1]}, ${row[2]}")

# csv.DictReader / csv.DictWriter — rows as dicts (RECOMMENDED)
with open("products.csv", "w", newline="", encoding="utf-8") as f:
    fields = ["id", "name", "price"]
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerow({"id": 1, "name": "Laptop", "price": 999.99})
    writer.writerow({"id": 2, "name": "Mouse", "price": 24.99})

with open("products.csv", "r", newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        print(f"  {row['name']}: ${row['price']}")

# Custom delimiter (TSV)
with open("data.tsv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f, delimiter="\t")
    writer.writerow(["Name", "Score"])
    writer.writerows([["Alice", 95], ["Bob", 87]])

# ── 15. pathlib — Modern File Handling ────────────
# pathlib.Path vs os.path: Path objects use / operator, have cleaner API
p = Path("sample.txt")
print(f"name={p.name}, stem={p.stem}, suffix={p.suffix}")  # sample.txt, sample, .txt
print(f"exists={p.exists()}, is_file={p.is_file()}, size={p.stat().st_size}")

# Join paths:  Path("data") / "2024" / "report.csv"  vs  os.path.join("data","2024","report.csv")
data_path = Path("data") / "2024" / "report.csv"

# Read/write without open()
Path("pathlib_test.txt").write_text("Hello from pathlib!", encoding="utf-8")
content = Path("pathlib_test.txt").read_text(encoding="utf-8")
Path("pathlib_bin.dat").write_bytes(b"binary data")
data = Path("pathlib_bin.dat").read_bytes()

# Glob — find files by pattern
for txt_file in Path(".").glob("*.txt"):
    print(f"  Found: {txt_file}")
# Path(".").rglob("*.py")  — recursive search into subdirs

# Modify path parts
p3 = Path("report.txt")
print(f"Change ext: {p3.with_suffix('.pdf')}, change name: {p3.with_name('summary.txt')}")

# JSON with pathlib (one-liner read/write)
Path("fw.json").write_text(json.dumps({"name": "FastAPI"}, indent=2), encoding="utf-8")
loaded = json.loads(Path("fw.json").read_text(encoding="utf-8"))

# ── 16. os Module Essentials ─────────────────────
os.path.exists("sample.txt")                       # True/False
os.path.getsize("sample.txt")                      # bytes
os.path.isfile("sample.txt")                       # True
name, ext = os.path.splitext("report.pdf")         # ('report', '.pdf')
full = os.path.join("folder", "sub", "file.txt")   # folder/sub/file.txt
os.path.dirname("/home/user/f.txt")                # /home/user
os.path.basename("/home/user/f.txt")               # f.txt
txt_files = [f for f in os.listdir(".") if f.endswith(".txt")]
os.rename("new_file.txt", "renamed_file.txt")
os.makedirs("test_dir/sub_dir", exist_ok=True)

# ╔══════════════════════════════════════════════════╗
# ║              ADVANCED                            ║
# ╚══════════════════════════════════════════════════╝

# ── 17. tempfile — Auto-Cleanup Temp Files ────────
with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tmp:
    tmp.write("Temporary data\n")
    tmp_name = tmp.name                                  # get path before close
os.unlink(tmp_name)                                      # manual delete (delete=False)

with tempfile.TemporaryDirectory() as tmpdir:             # auto-deleted on exit
    Path(tmpdir, "data.txt").write_text("temp data")
print(f"Temp dir gone: {not os.path.exists(tmpdir)}")    # True

# ── 18. shutil — Copy, Move, Delete ──────────────
shutil.copy("sample.txt", "sample_backup.txt")     # copy file
shutil.copy2("sample.txt", "sample_backup2.txt")   # copy + metadata (timestamps)
shutil.move("renamed_file.txt", "moved_file.txt")  # move/rename
shutil.copytree("test_dir", "test_dir_copy")       # copy entire directory tree
shutil.rmtree("test_dir_copy")                     # delete dir + all contents

# ── 19. JSON Lines (JSONL) ───────────────────────
# One JSON object per line — ideal for logs, streaming, large datasets
events = [
    {"ts": "2024-01-01T10:00", "event": "login", "user": "alice"},
    {"ts": "2024-01-01T10:05", "event": "page_view", "user": "alice"},
]
# Write: one json.dumps() per line
with open("events.jsonl", "w", encoding="utf-8") as f:
    for event in events:
        f.write(json.dumps(event) + "\n")

# Append (just add a line — no need to rewrite entire file like JSON arrays)
with open("events.jsonl", "a", encoding="utf-8") as f:
    f.write(json.dumps({"ts": "2024-01-01T10:15", "event": "logout", "user": "alice"}) + "\n")

# Read: parse each line independently
with open("events.jsonl", "r", encoding="utf-8") as f:
    all_events = [json.loads(line) for line in f]

# ── 20. Large File Reading ───────────────────────
with open("large_demo.txt", "w") as f:
    for i in range(1000): f.write(f"Line {i}: test data\n")

# Line by line (BEST for text) — never loads entire file into memory
count = sum(1 for _ in open("large_demo.txt", "r"))

# Chunk-based (for binary or raw processing)
total_bytes = 0
with open("large_demo.txt", "rb") as f:
    while chunk := f.read(8192):  # 8KB chunks, walrus operator
        total_bytes += len(chunk)

# ── 21. JSON ↔ CSV Conversion ────────────────────
# JSON → CSV
json_data = [
    {"name": "Alice", "age": 30, "city": "NYC"},
    {"name": "Bob", "age": 25, "city": "LA"},
]
with open("people.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=json_data[0].keys())
    writer.writeheader()
    writer.writerows(json_data)

# CSV → JSON
with open("people.csv", "r", newline="", encoding="utf-8") as f:
    csv_as_json = list(csv.DictReader(f))
with open("people.json", "w", encoding="utf-8") as f:
    json.dump(csv_as_json, f, indent=2)

# ── 22. Custom JSON Serialization ────────────────
# JSON can't serialize: datetime, set, bytes → use default= or cls=
data_custom = {
    "event": "Meeting",
    "date": datetime(2024, 6, 15, 14, 30),
    "tags": {"python", "coding"},
    "raw": b"hello",
}

def json_serializer(obj):
    if isinstance(obj, (datetime, date)): return obj.isoformat()
    if isinstance(obj, set): return sorted(list(obj))
    if isinstance(obj, bytes): return obj.decode("utf-8")
    raise TypeError(f"Type {type(obj)} not serializable")

result = json.dumps(data_custom, default=json_serializer, indent=2)
print(f"Custom serialized:\n{result}")

# Reusable: subclass JSONEncoder
class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)): return obj.isoformat()
        if isinstance(obj, set): return sorted(list(obj))
        if isinstance(obj, bytes): return obj.decode("utf-8")
        return super().default(obj)

json.dumps(data_custom, cls=CustomEncoder, indent=2)

# ── 23. JSON Merge & Diff ────────────────────────
defaults = {"theme": "light", "lang": "en", "notify": True, "font": 14}
user_prefs = {"theme": "dark", "font": 16}

merged = {**defaults, **user_prefs}   # ** unpacking (3.5+), user_prefs wins
merged2 = defaults | user_prefs       # | operator (3.9+)
print(f"Merged: {merged}")

# Deep merge for nested dicts
def deep_merge(base, override):
    result = base.copy()
    for key, val in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(val, dict):
            result[key] = deep_merge(result[key], val)
        else:
            result[key] = val
    return result

cfg_base = {"db": {"host": "localhost", "port": 5432}, "debug": False}
cfg_prod = {"db": {"host": "prod-server"}, "debug": False}
print(f"Deep merged: {deep_merge(cfg_base, cfg_prod)}")
# {"db": {"host": "prod-server", "port": 5432}, "debug": False}

# Simple diff
def json_diff(old, new):
    changes = {}
    for key in set(list(old) + list(new)):
        if key not in old: changes[key] = {"added": new[key]}
        elif key not in new: changes[key] = {"removed": old[key]}
        elif old[key] != new[key]: changes[key] = {"old": old[key], "new": new[key]}
    return changes

diff = json_diff({"name": "Alice", "age": 30, "city": "NYC"}, {"name": "Alice", "age": 31, "country": "US"})
# {'age': {'old': 30, 'new': 31}, 'city': {'removed': 'NYC'}, 'country': {'added': 'US'}}

# ── CLEANUP ───────────────────────────────────────
for f in ["sample.txt", "fruits.txt", "encoded.txt", "binary.dat", "binary_copy.dat",
          "temp_rw.txt", "pathlib_test.txt", "pathlib_bin.dat", "sample_backup.txt",
          "sample_backup2.txt", "moved_file.txt", "users.json", "fw.json",
          "employees.csv", "products.csv", "data.tsv", "people.csv", "people.json",
          "large_demo.txt", "events.jsonl"]:
    if os.path.exists(f):
        os.remove(f)
if os.path.exists("test_dir"):
    shutil.rmtree("test_dir")

# ══════════════════════════════════════════════════════════════════
#                         CHEAT SHEET
# ══════════════════════════════════════════════════════════════════
#
#  FILE MODES:
#    "r" read | "w" write | "a" append | "x" exclusive
#    "r+" read+write | "rb"/"wb" binary | seek(0) reset pointer
#
#  TEXT FILES:
#    with open(path, "r", encoding="utf-8") as f:
#        content = f.read()          # whole file (small files)
#        for line in f: ...          # line-by-line (large files)
#    with open(path, "w") as f:
#        f.write(text)               # write string
#        f.writelines(list_of_str)   # write list (no auto-newline)
#
#  JSON:
#    json.dumps(obj)     → string    |  json.dump(obj, file)  → file
#    json.loads(string)  → dict      |  json.load(file)       → dict
#    indent=2            pretty      |  separators=(",",":")   compact
#    ensure_ascii=False  keep unicode|  default=func           custom types
#    sort_keys=True      alphabetical|  cls=CustomEncoder      reusable
#
#  CSV:
#    csv.writer(f)        → writerow([...])         rows as lists
#    csv.DictWriter(f, fieldnames) → writerow({})   rows as dicts
#    csv.reader(f)        → iterate lists           newline="" ALWAYS
#    csv.DictReader(f)    → iterate dicts            delimiter="\t" for TSV
#
#  PATHLIB vs OS:
#    Path("a")/"b"/"c"        vs  os.path.join("a","b","c")
#    p.exists() / p.is_file() vs  os.path.exists() / os.path.isfile()
#    p.read_text()            vs  open()+read()
#    p.write_text(s)          vs  open()+write()
#    p.glob("*.txt")          vs  os.listdir() + filter
#    p.name/stem/suffix       vs  os.path.basename/splitext
#
#  ADVANCED:
#    tempfile.NamedTemporaryFile/TemporaryDirectory  auto-cleanup
#    shutil.copy/copy2/move/copytree/rmtree          file ops
#    JSONL: json.dumps() per line, easy append, stream-friendly
#    Large: for line in f (text) or while chunk:=f.read(8192)
#    Merge: {**a,**b} or a|b | Deep: recursive merge function
#
#  ERRORS: FileNotFoundError, PermissionError, IsADirectoryError,
#          UnicodeDecodeError, json.JSONDecodeError, OSError
# ══════════════════════════════════════════════════════════════════
