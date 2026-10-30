"""01b extra -- How bytes work  (simple version)
===============================================

IN ONE LINE:
  A computer stores every letter as a NUMBER from 0 to 255 (a byte).
  English letters use 1 byte. Other languages and emoji use 2 to 4 bytes.

REAL USE CASE:
  A user sends "Café 👍" to your FastAPI app. Before the tokenizer can cut
  it into tokens, the text becomes bytes:

     "Café 👍"   (6 characters)
          │
          ▼  .encode("utf-8")
     ┌──────────────────────────────────────┐
     │ 67 97 102 195 169 32 240 159 145 141 │   (10 bytes)
     └──────────────────────────────────────┘
          │
          ▼
     tokenizer -> tokens -> model

WHAT AN ENGINEER MUST KNOW:
  1. A byte = 8 bits (8 on/off switches) = a number from 0 to 255.
  2. ASCII is the table for English: "a" = 97, "A" = 65, space = 32.
  3. UTF-8 is the rule for all other characters: 2 to 4 bytes each.
  4. More bytes usually means more tokens, so non-English text costs more.

Run:  uv run python simple/01b_extra_how_bytes_work.py
"""


# ----------------------------------------------------------------------------
# STEP 1: A BYTE = 8 switches = one number from 0 to 255
# ----------------------------------------------------------------------------
def show_byte(number):
    """Show one number as a byte: normal number, 8 switches, and hex."""
    binary = format(number, "08b")          # 97 -> "01100001" (8 switches)
    hex_text = format(number, "02X")        # 97 -> "61" (how tools show bytes)
    return "decimal " + str(number) + "  binary " + binary + "  hex " + hex_text


# ----------------------------------------------------------------------------
# STEP 2: ASCII = the table for English letters (1 byte each)
# ----------------------------------------------------------------------------
def letters_to_numbers(text):
    """ord() looks up a character's number in the table."""
    return [ord(char) for char in text]


# ----------------------------------------------------------------------------
# STEP 3: UTF-8 = bigger characters need more bytes
# ----------------------------------------------------------------------------
def utf8_bytes(char):
    """Return the list of bytes UTF-8 uses for one character."""
    return list(char.encode("utf-8"))       # bytes -> list of numbers 0..255


def main():
    print("STEP 1: a byte is 8 switches")
    print("  8 switches give 2 x 2 x 2 x 2 x 2 x 2 x 2 x 2 =", 2 ** 8, "patterns")
    print("  smallest:", show_byte(0))
    print("  biggest: ", show_byte(255))
    print("  letter a:", show_byte(97))

    print("\nSTEP 2: English letters use the ASCII table")
    print("  'a' =", ord("a"), "  'b' =", ord("b"), "  'A' =", ord("A"), "  space =", ord(" "))
    text = "cats"
    print("  'cats' ->", letters_to_numbers(text))
    print("  chr(99) turns the number back into the letter:", chr(99))

    print("\nSTEP 3: other characters use UTF-8 (2 to 4 bytes)")
    for char in ["a", "é", "न", "你", "👍"]:
        numbers = utf8_bytes(char)
        print("  " + char, "->", len(numbers), "byte(s):", numbers)

    print("\nSTEP 4: text -> bytes -> text (this is what a tokenizer starts from)")
    message = "Café 👍"
    data = message.encode("utf-8")          # text to bytes
    print("  text:      ", message, " (" + str(len(message)) + " characters)")
    print("  bytes:     ", list(data), " (" + str(len(data)) + " bytes)")
    print("  back again:", data.decode("utf-8"))


if __name__ == "__main__":
    main()

# Remember:
#   - Byte = number 0..255. Computers only store numbers.
#   - English letter = 1 byte. é = 2, Hindi/Chinese = 3, emoji = 4.
#   - encode() turns text into bytes, decode() turns bytes back into text.
# Try: print the bytes of your own name, and of one word in your own language.
#      Which one needs more bytes per character?
