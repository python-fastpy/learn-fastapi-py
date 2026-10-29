"""Lesson 01b extra -- How we calculate a byte (the simple way)
==============================================================

WHY THIS MATTERS:
  A tokenizer starts from BYTES. This small file shows, step by step, how
  a letter like "u" becomes the number 117 -- and which table to look in.
  Read it before (or next to) 01b_tokens_in_depth.py.

THE 6 STEPS:
  1. What a byte is            8 switches -> 256 values (0..255)
  2. The table to refer to     ASCII: every English letter's number
  3. Look a letter up          "unbelievable cats" -> 17 numbers
  4. Write a byte 3 ways       decimal 97 = binary 01100001 = hex 61
  5. Bigger characters         é, न, 你, 👍 -> 2 to 4 bytes (UTF-8)
  6. Check it yourself         ord, chr, encode, decode

PREREQUISITES: none. Pure Python, no packages.

Run:  uv run python 01b_extra_how_bytes_work.py
"""

LINE = "  " + "-" * 72


def header(title: str):
    print(f"\n######## {title} ########\n")


def step(title: str):
    print(f"{LINE}\n  {title}\n{LINE}")


# ============================================================================
#   IN ONE SENTENCE: a computer stores every letter as a NUMBER, and it finds
#   that number in a table everyone agrees on -- like a secret code book.
#
#   ------------------------------------------------------------------------
#   STEP 1: what a byte is -- 8 little switches
#   ------------------------------------------------------------------------
#   NEW WORD: bit = one switch, OFF (0) or ON (1).
#   NEW WORD: byte = 8 bits in a row.
#     1 switch   0 1                 =   2 patterns
#     2 switches 00 01 10 11         =   4 patterns
#     3 switches 000 001 ... 111     =   8 patterns
#     every extra switch DOUBLES it -> 8 switches = 2 x 2 x 2 x 2 x 2 x 2 x 2 x 2 = 256
#   We number them from 0:  00000000 = 0  ...  11111111 = 255
#   So one byte = one number from 0 to 255.
#
#   ------------------------------------------------------------------------
#   STEP 2: the table to refer to -- ASCII
#   ------------------------------------------------------------------------
#   NEW WORD: ASCII = the table that gives every English letter, digit and
#   symbol a number from 0 to 127. Remember just 4 starting points:
#     space = 32     "0".."9" = 48..57     "A".."Z" = 65..90     "a".."z" = 97..122
#   The full table is printed when you run this file.
#
#   ------------------------------------------------------------------------
#   STEP 3: look a letter up
#   ------------------------------------------------------------------------
#   Letters go in alphabet order, so count from the first one:
#     "a" = 97     "b" = 97 + 1 = 98     "u" (21st letter) = 97 + 20 = 117
#   The whole text, one number per character:
#     u   n   b   e   l   i   e   v   a   b   l   e   _   c   a   t   s
#     117 110 98  101 108 105 101 118 97  98  108 101 32  99  97  116 115
#   17 characters -> 17 bytes (every ASCII character is exactly 1 byte).
#
#   ------------------------------------------------------------------------
#   STEP 4: write a byte 3 ways -- decimal, binary, hex
#   ------------------------------------------------------------------------
#   Same number, three ways of writing it:
#     decimal  97                         (normal counting)
#     binary   97 = 64 + 32 + 1           -> switches for 64, 32 and 1 are ON
#              128 64 32 16  8  4  2  1
#                0  1  1  0  0  0  0  1   -> 01100001
#     hex      97 = 6 x 16 + 1            -> "61"   (hex digits: 0-9 then A-F)
#   NEW WORD: hex = counting in 16s. 2 hex digits = exactly 1 byte (00..FF).
#   That's why tools show bytes in hex: "a" = 61, "u" = 75, space = 20.
#
#   ------------------------------------------------------------------------
#   STEP 5: bigger characters -- é, न, 你, 👍
#   ------------------------------------------------------------------------
#   ASCII stops at 127. Every other character gets a bigger number from the
#   UNICODE table (the big book: ~150,000 characters, all languages, emoji).
#   NEW WORD: UTF-8 = the rule that splits a big number into 2 to 4 bytes.
#   How many bytes depends only on how big the number is:
#     Unicode number      bytes   example
#     0 .. 127              1     "a"  = 97      -> 61
#     128 .. 2,047          2     "é"  = 233     -> C3 A9
#     2,048 .. 65,535       3     "न"  = 2,344   -> E0 A4 A8     "你" = 20,320 -> E4 BD A0
#     65,536 and up         4     "👍" = 128,077 -> F0 9F 91 8D
#
#   ------------------------------------------------------------------------
#   STEP 6: check it yourself
#   ------------------------------------------------------------------------
#     ord("u")                    -> 117        letter -> its number
#     chr(117)                    -> "u"        number -> its letter
#     "é".encode("utf-8")         -> b'\xc3\xa9'  text -> bytes
#     b'\xc3\xa9'.decode("utf-8") -> "é"        bytes -> text
#   TABLES TO REFER TO: search "ASCII table" (0..127), and the Unicode
#   charts at unicode.org/charts for every other character.
#
#   WHAT YOU LEARNED
#   - a byte = 8 switches = a number 0..255
#   - English letters: look up ASCII, 1 byte each ("a" = 97)
#   - other characters: Unicode number, split by UTF-8 into 2-4 bytes
# ============================================================================

def main():
    header("How we calculate a byte -- the simple way")

    step("STEP 1: what a byte is -- 8 little switches")
    for n in range(1, 9):
        print(f"    {n} switch{'es' if n > 1 else '  '} -> 2**{n} = {2 ** n:>3} patterns")
    print(f"    lowest {0:08b} = 0      highest {255:08b} = 255")

    step("STEP 2: the table to refer to -- ASCII (32..126, the printable part)")
    for row in range(32, 127, 8):
        print("    " + "   ".join(f"{n:>3} {'_' if n == 32 else chr(n)}" for n in range(row, min(row + 8, 127))))
    print("    (_ = space; 0..31 and 127 are invisible control codes like newline = 10)")

    step("STEP 3: look a letter up")
    for ch in "abu":
        print(f"    {ch!r} = 97 + {ord(ch) - 97:<2} = {ord(ch)}")
    text = "unbelievable cats"
    print("    " + " ".join(f"{'_' if c == ' ' else c:<3}" for c in text))
    print("    " + " ".join(f"{b:<3}" for b in text.encode("utf-8")))
    print(f"    {len(text)} characters -> {len(text.encode('utf-8'))} bytes")

    step("STEP 4: write a byte 3 ways -- decimal, binary, hex")
    for ch in ["a", "u", " "]:
        n = ord(ch)
        on = [p for p in (128, 64, 32, 16, 8, 4, 2, 1) if n & p]
        print(f"    {ch!r:<4} decimal {n:<4} binary {n:08b} ({' + '.join(map(str, on))})"
              f"   hex {n // 16} x 16 + {n % 16} = {n:02X}")

    step("STEP 5: bigger characters -- UTF-8 uses 2 to 4 bytes")
    print(f"    {'char':<6}{'Unicode number':>15}  {'bytes':>5}  hex")
    for ch in ["a", "é", "न", "你", "👍"]:
        b = ch.encode("utf-8")
        print(f"    {ch:<6}{ord(ch):>15,}  {len(b):>5}  {' '.join(f'{x:02X}' for x in b)}")

    step("STEP 6: check it yourself")
    print(f"    ord('u') = {ord('u')}     chr(117) = {chr(117)!r}")
    print(f"    'é'.encode('utf-8') = {'é'.encode('utf-8')!r}     decode back = {'é'.encode('utf-8').decode('utf-8')!r}")


if __name__ == "__main__":
    main()

# Exercise: print the bytes of your own name, and of one word in another
# language you know. Which one needs more bytes per character?
