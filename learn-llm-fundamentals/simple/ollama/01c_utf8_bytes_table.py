r"""01c -- The UTF-8 table: why 'P' is 80
=========================================

CONCEPT IN ONE LINE:
  Every character has a fixed NUMBER, the same on every computer. Text is stored as those
  numbers (BYTES), and the tokenizer (01b, step 2) cuts BYTES into tokens -- not letters.

  No Ollama needed for this file: it only uses Python.

FOUR KINDS OF NUMBER -- don't mix them up:

   "Paris" ─▶ characters ─▶ code points ─▶ UTF-8 bytes ─▶ token IDs (llama3.2)
               P a r i s     80 97 114     [80, 97, 114,   [60704]
                             105 115        105, 115]

   number        what it numbers           range            same everywhere?
   code point    one CHARACTER (Unicode)   0 - 1,114,111    yes -- a world standard
   byte          one piece of storage      0 - 255          yes -- UTF-8 is a world standard
   token ID      one TOKEN                 0 - 128,255      NO  -- each model has its own list
   weight        a learned number          any              NO  -- each model has its own (01b)

   For English letters, digits and symbols (0-127) the code point and the byte are the SAME
   number: 'P' = code point 80 = byte 80. Other characters need 2-4 bytes (see PART 3).

PART 1 -- THE ASCII TABLE: the 95 printable characters (32-126)

  ASCII (1963) gave every English character a number from 0 to 127. UTF-8 (1993) kept
  ALL of them unchanged, so this table is valid in UTF-8, Python, JSON, the web, everywhere.

   dec = normal number   hex = base 16 (0x50)   binary = the 8 bits actually stored

   dec hex  binary    char     dec hex  binary    char     dec hex  binary    char     dec hex  binary    char
    32  20  00100000  space     56  38  00111000  8         80  50  01010000  P        104  68  01101000  h
    33  21  00100001  !         57  39  00111001  9         81  51  01010001  Q        105  69  01101001  i
    34  22  00100010  "         58  3A  00111010  :         82  52  01010010  R        106  6A  01101010  j
    35  23  00100011  #         59  3B  00111011  ;         83  53  01010011  S        107  6B  01101011  k
    36  24  00100100  $         60  3C  00111100  <         84  54  01010100  T        108  6C  01101100  l
    37  25  00100101  %         61  3D  00111101  =         85  55  01010101  U        109  6D  01101101  m
    38  26  00100110  &         62  3E  00111110  >         86  56  01010110  V        110  6E  01101110  n
    39  27  00100111  '         63  3F  00111111  ?         87  57  01010111  W        111  6F  01101111  o
    40  28  00101000  (         64  40  01000000  @         88  58  01011000  X        112  70  01110000  p
    41  29  00101001  )         65  41  01000001  A         89  59  01011001  Y        113  71  01110001  q
    42  2A  00101010  *         66  42  01000010  B         90  5A  01011010  Z        114  72  01110010  r
    43  2B  00101011  +         67  43  01000011  C         91  5B  01011011  [        115  73  01110011  s
    44  2C  00101100  ,         68  44  01000100  D         92  5C  01011100  \        116  74  01110100  t
    45  2D  00101101  -         69  45  01000101  E         93  5D  01011101  ]        117  75  01110101  u
    46  2E  00101110  .         70  46  01000110  F         94  5E  01011110  ^        118  76  01110110  v
    47  2F  00101111  /         71  47  01000111  G         95  5F  01011111  _        119  77  01110111  w
    48  30  00110000  0         72  48  01001000  H         96  60  01100000  `        120  78  01111000  x
    49  31  00110001  1         73  49  01001001  I         97  61  01100001  a        121  79  01111001  y
    50  32  00110010  2         74  4A  01001010  J         98  62  01100010  b        122  7A  01111010  z
    51  33  00110011  3         75  4B  01001011  K         99  63  01100011  c        123  7B  01111011  {
    52  34  00110100  4         76  4C  01001100  L        100  64  01100100  d        124  7C  01111100  |
    53  35  00110101  5         77  4D  01001101  M        101  65  01100101  e        125  7D  01111101  }
    54  36  00110110  6         78  4E  01001110  N        102  66  01100110  f        126  7E  01111110  ~
    55  37  00110111  7         79  4F  01001111  O        103  67  01100111  g

  THE INVISIBLE ONES (0-31 and 127) -- control characters, no picture, but real bytes:

   dec hex  name              in Python   what it does
     0  00  NUL (null)        \x00        "nothing"
     9  09  TAB               \t          tab
    10  0A  LF (line feed)    \n          NEW LINE  (Linux/Mac, and in most LLM prompts)
    13  0D  CR (return)       \r          Windows line ends are \r\n = bytes [13, 10]
    27  1B  ESC (escape)      \x1b        starts terminal colour codes
   127  7F  DEL (delete)      \x7f        old "delete" key

  So "\n\n" in 01b's chat template = bytes [10, 10] = ONE llama3.2 token, ID 271.

PART 2 -- SHORTCUTS: you don't need to memorise the table

   A-Z = 65-90      a-z = 97-122      0-9 = 48-57      space = 32

   letter  = start + position in the alphabet - 1
             'P' = 16th letter  ->  65 + 15 = 80
             'r' = 18th letter  ->  97 + 17 = 114

   lowercase = UPPERCASE + 32      ('A' 65 -> 'a' 97,   'P' 80 -> 'p' 112)
     it's ONE bit:   A = 01000001
                     a = 01100001     <- only the 3rd bit from the left differs (= 32)

   the DIGIT '7' is NOT the number 7:    '7' = 48 + 7 = 55
     int("7") -> 7     ord("7") -> 55     (a model sees "2024" as text pieces, not a number)

   reading hex:     0x50 = 5 x 16 + 0  = 80
                    0x7A = 7 x 16 + 10 = 122  ('z')       (A=10 B=11 C=12 D=13 E=14 F=15)
   reading binary:  01010000 = 64 + 16 = 80
                    place values:  128  64  32  16   8   4   2   1
                    'P' = 80:        0   1   0   1   0   0   0   0

   Python:   ord("P")  -> 80          chr(80)  -> 'P'
             hex(80)   -> '0x50'      bin(80)  -> '0b1010000'

PART 3 -- BEYOND ENGLISH: 2, 3 or 4 bytes per character

  One byte holds only 0-255, but Unicode has over a million characters. UTF-8 solves this
  by using MORE bytes for bigger code points. The first bits of each byte say what it is:

   code points           bytes   bit pattern                              examples
   0 - 127               1       0xxxxxxx                                 A P a 7 space
   128 - 2,047           2       110xxxxx 10xxxxxx                        é ñ ü
   2,048 - 65,535        3       1110xxxx 10xxxxxx 10xxxxxx               ₹ € 你 अ
   65,536 - 1,114,111    4       11110xxx 10xxxxxx 10xxxxxx 10xxxxxx      🙂 👍

   - starts with 0       = a whole ASCII character on its own
   - starts with 110 / 1110 / 11110   = the FIRST byte of a 2 / 3 / 4-byte character
   - starts with 10      = a "continuation" byte, the middle or end of a character
   The x's are filled with the code point's bits, left to right.

  WORKED EXAMPLE -- 'é' = code point 233:

     233 in binary (11 bits):   000 1110 1001
     split 5 + 6 bits:          00011    101001
     put into 110xxxxx 10xxxxxx:
                                110 00011   10 101001
                                = 11000011  10101001
                                = 195       169            -> bytes [195, 169]

  MORE EXAMPLES (real values):

   char   code point          bytes (decimal)          bytes (binary)
   P      U+0050      80      [80]                     01010000
   é      U+00E9     233      [195, 169]               11000011 10101001
   ñ      U+00F1     241      [195, 177]               11000011 10110001
   ü      U+00FC     252      [195, 188]               11000011 10111100
   ₹      U+20B9   8,377      [226, 130, 185]          11100010 10000010 10111001
   €      U+20AC   8,364      [226, 130, 172]          11100010 10000010 10101100
   अ      U+0905   2,309      [224, 164, 133]          11100000 10100100 10000101
   你     U+4F60  20,320      [228, 189, 160]          11100100 10111101 10100000
   🙂     U+1F642 128,578     [240, 159, 153, 130]     11110000 10011111 10011001 10000010
   👍     U+1F44D 128,077     [240, 159, 145, 141]     11110000 10011111 10010001 10001101

   "U+00E9" is just the code point written in hex: 0xE9 = 14 x 16 + 9 = 233.

  Why this matters for LLMs:
   - len("é") is 1 character but 2 bytes; the tokenizer works on the BYTES
   - English text is mostly 1 byte per character, so it needs FEWER tokens than Hindi or
     Chinese saying the same thing -> those languages cost more tokens (lesson 02)
   - a model can output HALF a character: 🙂 can be split over 2 tokens. That's why Ollama
     sends "bytes" in logprobs (01b STEP 3) -- one token's bytes may not be valid text alone

PART 4 -- HOW llama3.2 SEES BYTES

  The vocabulary (llm/03_tokens.py) starts from all 256 possible bytes, then adds merged
  pieces on top. Inside the model file, invisible bytes are shown as visible stand-ins
  (the GPT-2 trick): printable bytes keep their own character ('P' stays 'P'), the 68
  invisible ones get the characters 256, 257, 258, ... in order. For bytes 0-32 that is
  simply byte + 256:

   byte   char        shown in the vocab as
   32     space       Ġ      (chr(256 + 32))    " Paris" is stored as "ĠParis", ID 12366
   10     \n          Ċ      (chr(256 + 10))    "\n\n"  is stored as "ĊĊ",     ID 271
   9      \t          ĉ      (chr(256 + 9))

   So when you see "Ġcapital" in a tokenizer, it means " capital" (with the space).

  Bytes never change; token IDs depend on the model:

   text         bytes                           llama3.2 token ID
   "Paris"      [80, 97, 114, 105, 115]         60704
   " Paris"     [32, 80, 97, 114, 105, 115]     12366      <- 1 extra byte, different token
   "paris"      [112, 97, 114, 105, 115]        (a different token or pieces)
   "PARIS"      [80, 65, 82, 73, 83]            (a different token or pieces)

SEE IT VISUALLY:
   https://www.asciitable.com/                     the full 0-127 table
   https://symbl.cc/en/unicode-table/              every Unicode character, with its UTF-8 bytes
   https://tiktokenizer.vercel.app/                text -> tokens, side by side
"""


def show(text):
    data = text.encode("utf-8")                          # characters -> bytes
    print(f"{text!r:12} {len(text)} chars  {len(data)} bytes  {list(data)}")


def main():
    print("PART 1: the printable ASCII table, built by Python")
    for code in range(32, 127):
        char = "space" if code == 32 else chr(code)
        print(f"{code:>3}  {code:02X}  {code:08b}  {char}")
    # ->  32  20  00100000  space
    #     33  21  00100001  !
    #     ...
    #     80  50  01010000  P
    #     ...
    #    126  7E  01111110  ~

    print("\nPART 2: character <-> number")
    print(ord("P"), chr(80), ord("p") - ord("P"), ord("7"), int("7"))
    # -> 80 P 32 55 7

    print("\nPART 3: text -> bytes")
    for text in ["Paris", " Paris", "paris", "PARIS", "\n\n", "é", "₹", "你", "🙂"]:
        show(text)
    # -> 'Paris'      5 chars  5 bytes  [80, 97, 114, 105, 115]
    #    ' Paris'     6 chars  6 bytes  [32, 80, 97, 114, 105, 115]
    #    'paris'      5 chars  5 bytes  [112, 97, 114, 105, 115]
    #    'PARIS'      5 chars  5 bytes  [80, 65, 82, 73, 83]
    #    '\n\n'       2 chars  2 bytes  [10, 10]
    #    'é'          1 chars  2 bytes  [195, 169]
    #    '₹'          1 chars  3 bytes  [226, 130, 185]
    #    '你'         1 chars  3 bytes  [228, 189, 160]
    #    '🙂'         1 chars  4 bytes  [240, 159, 153, 130]

    print("\nbytes -> text (what Ollama does with the logprobs 'bytes')")
    print(bytes([80, 97, 114, 105, 115]).decode("utf-8"))
    print(bytes([240, 159, 153]).decode("utf-8", errors="replace"))   # 3 of 4 bytes: broken
    # -> Paris
    #    �          <- half an emoji is not valid text yet

    print("\nPART 4: how the vocabulary shows invisible bytes")
    for code in [32, 10, 9]:
        print(code, repr(chr(code)), "->", chr(256 + code))
    # -> 32 ' ' -> Ġ
    #    10 '\n' -> Ċ
    #    9 '\t' -> ĉ


if __name__ == "__main__":
    main()

# Try: show("नमस्ते") and show("hello") -- same idea, very different byte counts.
