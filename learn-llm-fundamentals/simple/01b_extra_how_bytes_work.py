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

WHERE BYTES LIVE IN A REAL APP:

  ┌──────────────┐  POST /chat   ┌──────────────────┐  HTTPS   ┌─────────────────────────────┐
  │   Browser    │ ────────────▶ │  YOUR FASTAPI    │ ───────▶ │        LLM PROVIDER         │
  │  "Café 👍"   │  JSON = UTF-8 │  str in Python   │  UTF-8   │  bytes ──▶ tokenizer        │
  │              │     bytes     │  (characters)    │  bytes   │        ──▶ token ids        │
  │              │ ◀──────────── │                  │ ◀─────── │        ──▶ model            │
  └──────────────┘               └──────────────────┘          └─────────────────────────────┘
  On the wire it is ALWAYS bytes. Python turns them into a str for you.

THE PIPELINE -- from a letter to bytes and back:

  ┌───────────┐  ord()   ┌──────────────┐  .encode("utf-8")  ┌───────────────────┐
  │ character │ ───────▶ │ char number  │ ─────────────────▶ │ 1 to 4 bytes      │
  │    "é"    │          │     233      │                    │ [195, 169]        │
  └───────────┘ ◀─────── └──────────────┘ ◀───────────────── └───────────────────┘
                 chr()                     .decode("utf-8")

  How many bytes does UTF-8 use?  It depends on the char number:
     char number 0 .. 127        ──▶ 1 byte    ("a" = 97)
     char number 128 .. 2047     ──▶ 2 bytes   ("é" = 233)
     char number 2048 .. 65535   ──▶ 3 bytes   ("न" = 2344, "你" = 20320)
     char number 65536 and up    ──▶ 4 bytes   ("👍" = 128077)

ONE FULL RUN, step by step (the real "Café 👍" printed by STEP 4):

   char    char number    bytes (UTF-8)          how many
   ────    ───────────    ───────────────────    ────────
   C       67             [67]                   1
   a       97             [97]                   1
   f       102            [102]                  1
   é       233            [195, 169]             2
   space   32             [32]                   1
   👍      128077         [240, 159, 145, 141]   4
                                                 ──
                          6 characters  ──▶      10 bytes

   The tokenizer gets 10 bytes, not 6 letters. More bytes = often more tokens.

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
#   number 97
#      │
#      ▼  format(97, "08b")  -> write it with 8 switches (0 = off, 1 = on)
#
#      switch value:   128   64   32   16    8    4    2    1
#      switch:           0    1    1    0    0    0    0    1
#                             │    │                        │
#                             64 + 32         +             1   = 97
#      │
#      ▼  format(97, "02X")  -> the same number in hex (base 16)
#   "decimal 97  binary 01100001  hex 61"
#
#   all off = 00000000 = 0        all on = 11111111 = 255   (256 patterns)
def show_byte(number):
    """Show one number as a byte: normal number, 8 switches, and hex."""
    binary = format(number, "08b")          # 97 -> "01100001" (8 switches)
    hex_text = format(number, "02X")        # 97 -> "61" (how tools show bytes)
    return "decimal " + str(number) + "  binary " + binary + "  hex " + hex_text


# ----------------------------------------------------------------------------
# STEP 2: ASCII = the table for English letters (1 byte each)
# ----------------------------------------------------------------------------
#   "cats"
#      │
#      ▼  for each character: ord(char) = look it up in the table
#    'c'   'a'   't'   's'
#     │     │     │     │
#     ▼     ▼     ▼     ▼
#    99    97   116   115        ──▶  [99, 97, 116, 115]
#
#   chr(99) goes the other way:  99 ──▶ 'c'
def letters_to_numbers(text):
    """ord() looks up a character's number in the table."""
    return [ord(char) for char in text]


# ----------------------------------------------------------------------------
# STEP 3: UTF-8 = bigger characters need more bytes
# ----------------------------------------------------------------------------
#   "é"
#    │
#    ▼  ord("é") = 233.  Too big for 1 byte in UTF-8 (1 byte only goes to 127).
#   233 in bits:  00011 101001      (cut into a 5-bit part and a 6-bit part)
#    │
#    ▼  put a "marker" in front of each part
#   byte 1:  110 + 00011   = 11000011 = 195     ("110" means: I start a 2-byte char)
#   byte 2:   10 + 101001  = 10101001 = 169     ("10"  means: I continue a char)
#    │
#    ▼
#   [195, 169]
#
#   The loop in main():
#   ┌─▶ next char from ["a", "é", "न", "你", "👍"]
#   │      │
#   │      ▼
#   │   char.encode("utf-8") ──▶ e.g. "न" -> [224, 164, 168]
#   │      │
#   │      ▼
#   │   print how many bytes and which ones
#   │      │
#   │   more chars? ── no ──▶ END
#   │      │ yes
#   └──────┘
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
        print("  " + char, "->", len(numbers), "byte(s):", numbers, "  (char number " + str(ord(char)) + ")")
    print("  inside 'é': char number", ord("é"), "-> 2 bytes:")
    for number in utf8_bytes("é"):
        print("    ", show_byte(number))

    print("\nSTEP 4: text -> bytes -> text (this is what a tokenizer starts from)")
    message = "Café 👍"
    data = message.encode("utf-8")          # text to bytes
    print("  text:      ", message, " (" + str(len(message)) + " characters)")
    for char in message:                    # one line per character
        print("    " + repr(char), "number", ord(char), "->", utf8_bytes(char))
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
