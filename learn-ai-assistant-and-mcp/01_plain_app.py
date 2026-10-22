"""Step 1 -- The plain app, before any AI at all
===================================================

Nothing here is AI. This is an ordinary CLI over `reading_list.py`'s four
functions. The whole point of starting here: once you see step 2 and 3
add an assistant and then MCP on TOP of this, you'll see neither one
required touching a single line in this file or in reading_list.py.

Run:  uv run python 01_plain_app.py
"""

from reading_list import add_book, list_books, mark_status, remove_book

COMMANDS = """
Commands:
  add <title> / <author>        add a book (to_read)
  list [status]                 list all books, or just one status
  status <id> <status>          to_read | reading | read
  remove <id>
  quit
"""


def run_demo() -> None:
    """A scripted run, so this file proves itself with no typing required."""
    print("--- add two books ---")
    print(add_book("Dune", "Frank Herbert"))
    print(add_book("Klara and the Sun", "Kazuo Ishiguro"))

    print("\n--- list everything ---")
    for b in list_books():
        print(" ", b)

    print("\n--- start reading book 1 ---")
    print(mark_status(1, "reading"))

    print("\n--- list only 'reading' ---")
    for b in list_books(status="reading"):
        print(" ", b)

    print("\n--- remove book 2 ---")
    print(remove_book(2))

    print("\n--- final list ---")
    for b in list_books():
        print(" ", b)


if __name__ == "__main__":
    run_demo()
    print(COMMANDS)
    print("(this file just ran a scripted demo -- there's no AI in it yet)")

# Expected output:
#
# --- add two books ---
# {'id': 1, 'title': 'Dune', 'author': 'Frank Herbert', 'status': 'to_read'}
# {'id': 2, 'title': 'Klara and the Sun', 'author': 'Kazuo Ishiguro', 'status': 'to_read'}
#
# --- list everything ---
#   {'id': 1, 'title': 'Dune', ...}
#   {'id': 2, 'title': 'Klara and the Sun', ...}
#
# --- start reading book 1 ---
# {'id': 1, ..., 'status': 'reading'}
#
# --- list only 'reading' ---
#   {'id': 1, ..., 'status': 'reading'}
#
# --- remove book 2 ---
# {'id': 2, 'title': 'Klara and the Sun', ...}
#
# --- final list ---
#   {'id': 1, 'title': 'Dune', ..., 'status': 'reading'}
