# =============================================================================
# PYTHON DATA TYPES — COMPREHENSIVE REFERENCE (with input() & expected output)
# =============================================================================


# =============================================================================
# 1. NUMERIC TYPES
# =============================================================================

# --- 1.1 int (Integer) ---
# Whole numbers, positive or negative, no decimal point.
# Python integers have unlimited precision (no overflow).

a = 10              # positive integer
b = -5              # negative integer
c = 0               # zero
d = 1_000_000       # underscores for readability (still 1000000)
e = 0b1010          # binary literal => 10
f = 0o17            # octal literal => 15
g = 0xFF            # hexadecimal literal => 255
h = int("42")       # string to int
i = int("1010", 2)  # binary string to int => 10
j = int(3.9)        # float to int (truncates toward zero) => 3
k = int(-3.9)       # => -3 (truncates, does NOT round)
big = 10**100        # arbitrarily large integer — no overflow

print("--- int ---")
print(type(a), a)                          # OUTPUT: <class 'int'> 10
print(f"binary: {e}, octal: {f}, hex: {g}")  # OUTPUT: binary: 10, octal: 15, hex: 255
print(f"big int: {big}")                   # OUTPUT: big int: 10000000000...0 (101 digits)
print(f"int(-3.9) = {k}")                  # OUTPUT: int(-3.9) = -3

# --- input() for int ---
# num = int(input("Enter an integer: "))      # INPUT: 42     => num = 42
# num = int(input("Enter binary: "), 2)       # INPUT: 1010   => num = 10
# num = int(input("Enter hex: "), 16)         # INPUT: ff     => num = 255
# num = int(input("Enter octal: "), 8)        # INPUT: 17     => num = 15
# NOTE: input() ALWAYS returns str, so you must cast with int()
# If user enters "abc", int("abc") raises ValueError
print()


# --- 1.2 float (Floating Point) ---
# Real numbers with decimal point. Uses 64-bit IEEE 754 double precision.
# Has limited precision (~15-17 significant digits).

a_f = 3.14           # standard float
b_f = -0.001         # negative float
c_f = 1.0            # integer value as float
d_f = .5             # leading zero optional => 0.5
e_f = 5.             # trailing zero optional => 5.0
f_f = 3.14e2         # scientific notation => 314.0
g_f = 1.5e-3         # => 0.0015
h_f = float("3.14")  # string to float
i_f = float("inf")   # positive infinity
j_f = float("-inf")  # negative infinity
k_f = float("nan")   # Not a Number
l_f = float(7)       # int to float => 7.0

print("--- float ---")
print(type(a_f), a_f)                     # OUTPUT: <class 'float'> 3.14
print(f"scientific: {f_f}, small: {g_f}")  # OUTPUT: scientific: 314.0, small: 0.0015
print(f"inf: {i_f}, -inf: {j_f}, nan: {k_f}")  # OUTPUT: inf: inf, -inf: -inf, nan: nan
print(f"0.1 + 0.2 = {0.1 + 0.2}")         # OUTPUT: 0.1 + 0.2 = 0.30000000000000004
print(f"0.1 + 0.2 == 0.3 => {0.1 + 0.2 == 0.3}")  # OUTPUT: 0.1 + 0.2 == 0.3 => False
import math
print(f"math.isclose(0.1+0.2, 0.3) => {math.isclose(0.1 + 0.2, 0.3)}")  # OUTPUT: ... => True
print(f"math.isnan(k_f) => {math.isnan(k_f)}")   # OUTPUT: ... => True
print(f"math.isinf(i_f) => {math.isinf(i_f)}")   # OUTPUT: ... => True

# --- input() for float ---
# price = float(input("Enter price: "))        # INPUT: 19.99  => price = 19.99
# temp = float(input("Enter temperature: "))   # INPUT: -3.5   => temp = -3.5
# sci = float(input("Enter scientific: "))     # INPUT: 1.5e3  => sci = 1500.0
# NOTE: float("abc") raises ValueError
# NOTE: float("inf") is valid and returns infinity
print()


# --- 1.3 complex (Complex Numbers) ---
# Numbers with real and imaginary parts. j or J is the imaginary unit.

a_c = 3 + 4j        # complex literal
b_c = complex(3, 4)  # same as above
c_c = 2j             # pure imaginary
d_c = complex(5)     # (5+0j)
e_c = complex("3+4j")  # string to complex (NO spaces allowed inside!)

print("--- complex ---")
print(type(a_c), a_c)                        # OUTPUT: <class 'complex'> (3+4j)
print(f"real part: {a_c.real}, imaginary part: {a_c.imag}")  # OUTPUT: real part: 3.0, imaginary part: 4.0
print(f"conjugate: {a_c.conjugate()}")        # OUTPUT: conjugate: (3-4j)
print(f"abs (magnitude): {abs(a_c)}")         # OUTPUT: abs (magnitude): 5.0

# --- input() for complex ---
# z = complex(input("Enter complex (e.g. 3+4j): "))  # INPUT: 3+4j => z = (3+4j)
# NOTE: input must have NO spaces: "3+4j" works, "3 + 4j" raises ValueError
print()


# =============================================================================
# 2. BOOLEAN TYPE
# =============================================================================

# --- 2.1 bool ---
# Subclass of int. Only two values: True (1) and False (0).

a_b = True
b_b = False
c_b = bool(1)       # True (any non-zero number is True)
d_b = bool(0)       # False
e_b = bool("")      # False (empty string)
f_b = bool("hello") # True (non-empty string)
g_b = bool([])      # False (empty list)
h_b = bool([1])     # True (non-empty list)
i_b = bool(None)    # False
j_b = bool({})      # False (empty dict)
k_b = bool(0.0)     # False
l_b = bool(0j)      # False (zero complex)

print("--- bool ---")
print(type(a_b), a_b)                      # OUTPUT: <class 'bool'> True
print(f"bool(1)={c_b}, bool(0)={d_b}")     # OUTPUT: bool(1)=True, bool(0)=False
print(f"bool('')={e_b}, bool('hello')={f_b}")  # OUTPUT: bool('')=False, bool('hello')=True
print(f"bool([])={g_b}, bool([1])={h_b}")  # OUTPUT: bool([])=False, bool([1])=True
print(f"bool(None)={i_b}, bool({{}})={j_b}")  # OUTPUT: bool(None)=False, bool({})=False

# Bool is a subclass of int:
print(f"True + True = {True + True}")       # OUTPUT: True + True = 2
print(f"True * 10 = {True * 10}")           # OUTPUT: True * 10 = 10
print(f"isinstance(True, int) = {isinstance(True, int)}")  # OUTPUT: ... = True

# Falsy values: False, None, 0, 0.0, 0j, '', [], (), {}, set(), frozenset()
# Truthy values: everything else

# --- input() for bool ---
# NOTE: input() returns a string, so bool(input()) is almost ALWAYS True!
# bool("False") => True  (non-empty string!)
# bool("")      => False (only empty string is falsy)
#
# Correct way to get boolean from user:
# answer = input("Continue? (yes/no): ").strip().lower()  # INPUT: yes
# is_yes = answer in ("yes", "y", "true", "1")            # => True
# is_no = answer in ("no", "n", "false", "0")             # => False
#
# Or with match-case (Python 3.10+):
# match input("Enable? (y/n): ").strip().lower():
#     case "y" | "yes" | "1" | "true": enabled = True
#     case _: enabled = False
print()


# =============================================================================
# 3. STRING TYPE
# =============================================================================

# --- 3.1 str (String) ---
# Immutable sequence of Unicode characters.

# Creation
s1 = 'single quotes'
s2 = "double quotes"
s3 = '''triple single
quotes for multiline'''
s4 = """triple double
quotes for multiline"""
s5 = str(42)          # int to string => "42"
s6 = str(3.14)        # float to string => "3.14"
s7 = str(True)        # bool to string => "True"
s8 = str([1, 2, 3])   # list to string => "[1, 2, 3]"

print("--- str ---")
print(type(s1), s1)                        # OUTPUT: <class 'str'> single quotes

# Escape sequences
esc1 = "hello\nworld"     # newline
esc2 = "tab\there"        # tab
esc3 = "back\\slash"      # backslash
esc4 = "quote\"inside"    # escaped quote
esc5 = "null\0char"       # null character
esc6 = "A"           # unicode => 'A'
esc7 = "\U0001F600"       # unicode emoji => (smiley face)
esc8 = r"raw\nstring"     # raw string — no escape processing

print(f"newline: {repr(esc1)}")            # OUTPUT: newline: 'hello\nworld'
print(f"raw string: {esc8}")               # OUTPUT: raw string: raw\nstring

# String operations
word = "Hello, World!"
print(f"length: {len(word)}")              # OUTPUT: length: 13
print(f"upper: {word.upper()}")            # OUTPUT: upper: HELLO, WORLD!
print(f"lower: {word.lower()}")            # OUTPUT: lower: hello, world!
print(f"title: {word.title()}")            # OUTPUT: title: Hello, World!
print(f"strip: {'  hi  '.strip()}")        # OUTPUT: strip: hi
print(f"lstrip: {'  hi  '.lstrip()}")      # OUTPUT: lstrip: hi
print(f"rstrip: {'  hi  '.rstrip()}")      # OUTPUT: rstrip:   hi
print(f"replace: {word.replace('World', 'Python')}")  # OUTPUT: replace: Hello, Python!
print(f"split: {'a,b,c'.split(',')}")      # OUTPUT: split: ['a', 'b', 'c']
print(f"join: {'-'.join(['a', 'b', 'c'])}") # OUTPUT: join: a-b-c
print(f"find: {word.find('World')}")       # OUTPUT: find: 7
print(f"index: {word.index('World')}")     # OUTPUT: index: 7
print(f"count: {'banana'.count('a')}")     # OUTPUT: count: 3
print(f"startswith: {word.startswith('Hello')}")  # OUTPUT: startswith: True
print(f"endswith: {word.endswith('!')}")    # OUTPUT: endswith: True
print(f"isdigit: {'123'.isdigit()}")       # OUTPUT: isdigit: True
print(f"isalpha: {'abc'.isalpha()}")       # OUTPUT: isalpha: True
print(f"isalnum: {'abc123'.isalnum()}")    # OUTPUT: isalnum: True
print(f"isspace: {'   '.isspace()}")       # OUTPUT: isspace: True
print(f"center: {'hi'.center(10, '-')}")   # OUTPUT: center: ----hi----
print(f"ljust: {'hi'.ljust(10, '-')}")     # OUTPUT: ljust: hi--------
print(f"rjust: {'hi'.rjust(10, '-')}")     # OUTPUT: rjust: --------hi
print(f"zfill: {'42'.zfill(5)}")           # OUTPUT: zfill: 00042

# Indexing and slicing (strings are sequences)
text = "Python"
print(f"text[0] = {text[0]}")              # OUTPUT: text[0] = P
print(f"text[-1] = {text[-1]}")            # OUTPUT: text[-1] = n
print(f"text[0:3] = {text[0:3]}")          # OUTPUT: text[0:3] = Pyt
print(f"text[::2] = {text[::2]}")          # OUTPUT: text[::2] = Pto
print(f"text[::-1] = {text[::-1]}")        # OUTPUT: text[::-1] = nohtyP

# String formatting
name, age = "Alice", 30
print(f"f-string: {name} is {age}")        # OUTPUT: f-string: Alice is 30
print("format: {} is {}".format(name, age))  # OUTPUT: format: Alice is 30
print("percent: %s is %d" % (name, age))   # OUTPUT: percent: Alice is 30
print(f"f-string expr: {2 + 3 = }")        # OUTPUT: f-string expr: 2 + 3 = 5
print(f"padding: {'hi':>10}, {'hi':<10}, {'hi':^10}")  # OUTPUT: padding:         hi, hi        ,     hi
print(f"float format: {3.14159:.2f}")      # OUTPUT: float format: 3.14
print(f"thousands: {1000000:,}")           # OUTPUT: thousands: 1,000,000
print(f"binary: {255:08b}")               # OUTPUT: binary: 11111111
print(f"hex: {255:#x}")                   # OUTPUT: hex: 0xff

# String is IMMUTABLE
# text[0] = 'p'  # TypeError: 'str' object does not support item assignment

# --- input() for str ---
# input() returns str by default — no conversion needed!
# name = input("Enter your name: ")              # INPUT: Alice    => name = "Alice"
# line = input("Enter text: ")                   # INPUT: hi there => line = "hi there"
# char = input("Enter a single char: ")          # INPUT: A        => char = "A" (still a string)
# empty = input("Press enter: ")                 # INPUT: (enter)  => empty = "" (empty string)
# password = input("Password: ")                 # INPUT: secret   => password = "secret" (visible!)
#
# Multi-word input parsing:
# words = input("Enter words: ").split()          # INPUT: hello world => ['hello', 'world']
# first, last = input("First Last: ").split()     # INPUT: John Doe    => first="John", last="Doe"
# csv = input("Enter CSV: ").split(",")           # INPUT: a,b,c       => ['a', 'b', 'c']
#
# Stripping whitespace:
# clean = input("Enter: ").strip()                # INPUT: "  hi  "    => clean = "hi"
print()


# =============================================================================
# 4. BYTES TYPES
# =============================================================================

# --- 4.1 bytes (Immutable byte sequence) ---
# Each element is an integer 0-255.

b1 = b"hello"              # bytes literal (ASCII only)
b2 = b'\x48\x65\x6c\x6c\x6f'  # hex => b'Hello'
b3 = bytes([72, 101, 108, 108, 111])  # from list of ints => b'Hello'
b4 = bytes(5)               # 5 zero bytes => b'\x00\x00\x00\x00\x00'
b5 = "hello".encode("utf-8")  # string to bytes
b6 = b"hello".decode("utf-8")  # bytes to string

print("--- bytes ---")
print(type(b1), b1)                        # OUTPUT: <class 'bytes'> b'hello'
print(f"b1[0] = {b1[0]}")                  # OUTPUT: b1[0] = 104
print(f"encode: {b5}")                     # OUTPUT: encode: b'hello'
print(f"decode: {b6}")                     # OUTPUT: decode: hello
print(f"hex: {b1.hex()}")                  # OUTPUT: hex: 68656c6c6f
print(f"from hex: {bytes.fromhex('68656c6c6f')}")  # OUTPUT: from hex: b'hello'

# --- input() for bytes ---
# raw = input("Enter text: ").encode("utf-8")     # INPUT: hello => b'hello'
# raw = input("Enter text: ").encode("ascii")     # INPUT: hello => b'hello' (ASCII only)
# hex_input = bytes.fromhex(input("Enter hex: ")) # INPUT: 48656c6c6f => b'Hello'

# --- 4.2 bytearray (Mutable byte sequence) ---

ba1 = bytearray(b"hello")
ba1[0] = 72  # modify first byte to 'H'
print(f"\n--- bytearray ---")
print(type(ba1), ba1)                      # OUTPUT: <class 'bytearray'> bytearray(b'Hello')
ba1.append(33)  # append '!'
print(f"after append: {ba1}")              # OUTPUT: after append: bytearray(b'Hello!')
ba1.extend(b" world")
print(f"after extend: {ba1}")              # OUTPUT: after extend: bytearray(b'Hello! world')
print()

# --- 4.3 memoryview ---
# View into the buffer of a bytes/bytearray without copying.

data = bytearray(b"Hello World")
mv = memoryview(data)
print("--- memoryview ---")
print(type(mv), mv)                        # OUTPUT: <class 'memoryview'> <memory at 0x...>
print(f"mv[0] = {mv[0]}")                  # OUTPUT: mv[0] = 72
print(f"mv[0:5] = {bytes(mv[0:5])}")       # OUTPUT: mv[0:5] = b'Hello'
mv[6:11] = b"Earth"
print(f"data after mv edit: {data}")       # OUTPUT: data after mv edit: bytearray(b'Hello Earth')
mv.release()
print()


# =============================================================================
# 5. SEQUENCE TYPES
# =============================================================================

# --- 5.1 list (Mutable ordered sequence) ---
# Can contain mixed types. Ordered, indexed, allows duplicates.

l1 = [1, 2, 3, 4, 5]
l2 = ["a", 1, True, 3.14, None]  # mixed types
l3 = [[1, 2], [3, 4]]            # nested list
l4 = list("hello")               # => ['h', 'e', 'l', 'l', 'o']
l5 = list(range(5))              # => [0, 1, 2, 3, 4]
l6 = []                          # empty list
l7 = list()                      # empty list

print("--- list ---")
print(type(l1), l1)                        # OUTPUT: <class 'list'> [1, 2, 3, 4, 5]

# Indexing and slicing
print(f"l1[0] = {l1[0]}")                  # OUTPUT: l1[0] = 1
print(f"l1[-1] = {l1[-1]}")                # OUTPUT: l1[-1] = 5
print(f"l1[1:3] = {l1[1:3]}")              # OUTPUT: l1[1:3] = [2, 3]
print(f"l1[::-1] = {l1[::-1]}")            # OUTPUT: l1[::-1] = [5, 4, 3, 2, 1]

# List methods
lst = [3, 1, 4, 1, 5, 9]
lst.append(2)                    # add to end
print(f"append: {lst}")                    # OUTPUT: append: [3, 1, 4, 1, 5, 9, 2]
lst.insert(0, 0)                 # insert at index
print(f"insert: {lst}")                    # OUTPUT: insert: [0, 3, 1, 4, 1, 5, 9, 2]
lst.extend([6, 7])               # add multiple
print(f"extend: {lst}")                    # OUTPUT: extend: [0, 3, 1, 4, 1, 5, 9, 2, 6, 7]
popped = lst.pop()               # remove & return last
print(f"pop: {popped}, list: {lst}")       # OUTPUT: pop: 7, list: [0, 3, 1, 4, 1, 5, 9, 2, 6]
popped_idx = lst.pop(0)          # remove & return at index
print(f"pop(0): {popped_idx}, list: {lst}")  # OUTPUT: pop(0): 0, list: [3, 1, 4, 1, 5, 9, 2, 6]
lst.remove(1)                    # remove first occurrence of value
print(f"remove(1): {lst}")                 # OUTPUT: remove(1): [3, 4, 1, 5, 9, 2, 6]
print(f"count(1): {lst.count(1)}")         # OUTPUT: count(1): 1
print(f"index(4): {lst.index(4)}")         # OUTPUT: index(4): 1

lst2 = [3, 1, 4, 1, 5]
lst2.sort()                      # in-place sort
print(f"sort: {lst2}")                     # OUTPUT: sort: [1, 1, 3, 4, 5]
lst2.sort(reverse=True)          # descending
print(f"sort desc: {lst2}")                # OUTPUT: sort desc: [5, 4, 3, 1, 1]
lst2.reverse()                   # in-place reverse
print(f"reverse: {lst2}")                  # OUTPUT: reverse: [1, 1, 3, 4, 5]

# sorted() returns new list, does NOT modify original
original = [3, 1, 2]
new_sorted = sorted(original)
print(f"sorted (new): {new_sorted}, original unchanged: {original}")
# OUTPUT: sorted (new): [1, 2, 3], original unchanged: [3, 1, 2]

# List comprehension
squares = [x**2 for x in range(6)]
evens = [x for x in range(10) if x % 2 == 0]
matrix = [[i * j for j in range(3)] for i in range(3)]
print(f"squares: {squares}")               # OUTPUT: squares: [0, 1, 4, 9, 16, 25]
print(f"evens: {evens}")                   # OUTPUT: evens: [0, 2, 4, 6, 8]
print(f"matrix: {matrix}")                 # OUTPUT: matrix: [[0, 0, 0], [0, 1, 2], [0, 2, 4]]

# Copying
shallow = lst2.copy()            # shallow copy (same as lst2[:])
import copy
deep = copy.deepcopy(l3)         # deep copy (nested objects too)
print(f"shallow copy: {shallow}")          # OUTPUT: shallow copy: [1, 1, 3, 4, 5]

# List unpacking
first, *rest = [1, 2, 3, 4]
print(f"unpack: first={first}, rest={rest}")  # OUTPUT: unpack: first=1, rest=[2, 3, 4]

lst.clear()                      # remove all elements
print(f"clear: {lst}")                     # OUTPUT: clear: []

# --- input() for list ---
# nums = list(map(int, input("Enter numbers (space-sep): ").split()))
#   INPUT: 1 2 3 4 5          => [1, 2, 3, 4, 5]
#
# words = input("Enter words: ").split()
#   INPUT: hello world foo     => ['hello', 'world', 'foo']
#
# csv_list = input("Enter CSV: ").split(",")
#   INPUT: a,b,c               => ['a', 'b', 'c']
#
# n = int(input("How many? "))           # INPUT: 3
# items = [input(f"Item {i+1}: ") for i in range(n)]
#   INPUT: apple               => items[0] = 'apple'
#   INPUT: banana              => items[1] = 'banana'
#   INPUT: cherry              => items[2] = 'cherry'
#   Result: ['apple', 'banana', 'cherry']
#
# Mixed type list from input:
# parts = input("Enter int,float,str: ").split(",")   # INPUT: 5,3.14,hello
# mixed = [int(parts[0]), float(parts[1]), parts[2]]  # => [5, 3.14, 'hello']
print()


# --- 5.2 tuple (Immutable ordered sequence) ---
# Like list but cannot be modified after creation. Hashable if all elements are hashable.

t1 = (1, 2, 3)
t2 = ("a", 1, True, 3.14)       # mixed types
t3 = (1,)                       # single element tuple — COMMA IS REQUIRED
t4 = ()                         # empty tuple
t5 = tuple([1, 2, 3])           # list to tuple
t6 = tuple("hello")             # => ('h', 'e', 'l', 'l', 'o')
t7 = 1, 2, 3                    # parentheses are optional (tuple packing)

print("--- tuple ---")
print(type(t1), t1)                        # OUTPUT: <class 'tuple'> (1, 2, 3)
print(f"single element: {t3}, type: {type(t3)}")  # OUTPUT: single element: (1,), type: <class 'tuple'>
print(f"NOT a tuple: {type((1))}")         # OUTPUT: NOT a tuple: <class 'int'>

# Indexing and slicing (same as list)
print(f"t1[0] = {t1[0]}")                  # OUTPUT: t1[0] = 1
print(f"t1[-1] = {t1[-1]}")                # OUTPUT: t1[-1] = 3
print(f"t1[1:] = {t1[1:]}")                # OUTPUT: t1[1:] = (2, 3)

# Tuple methods (only 2!)
print(f"count(1): {t1.count(1)}")          # OUTPUT: count(1): 1
print(f"index(2): {t1.index(2)}")          # OUTPUT: index(2): 1

# Tuple unpacking
a_t, b_t, c_t = t1
print(f"unpacked: {a_t}, {b_t}, {c_t}")    # OUTPUT: unpacked: 1, 2, 3

# Swap values using tuple unpacking
x, y = 10, 20
x, y = y, x
print(f"swapped: x={x}, y={y}")            # OUTPUT: swapped: x=20, y=10

# Named tuple (from collections)
from collections import namedtuple
Point = namedtuple("Point", ["x", "y"])
p = Point(3, 4)
print(f"namedtuple: {p}, x={p.x}, y={p.y}")  # OUTPUT: namedtuple: Point(x=3, y=4), x=3, y=4

# Tuples are immutable:
# t1[0] = 10  # TypeError: 'tuple' object does not support item assignment
# But mutable objects INSIDE a tuple CAN be changed:
tricky = ([1, 2], [3, 4])
tricky[0].append(3)
print(f"mutable inside tuple: {tricky}")   # OUTPUT: mutable inside tuple: ([1, 2, 3], [3, 4])

# --- input() for tuple ---
# t = tuple(map(int, input("Enter numbers: ").split()))
#   INPUT: 1 2 3               => (1, 2, 3)
#
# x, y = map(float, input("Enter x y: ").split())
#   INPUT: 3.5 4.2             => x=3.5, y=4.2 (unpacked directly)
print()


# --- 5.3 range (Immutable sequence of numbers) ---

r1 = range(5)            # 0, 1, 2, 3, 4
r2 = range(2, 8)         # 2, 3, 4, 5, 6, 7
r3 = range(0, 10, 2)     # 0, 2, 4, 6, 8 (step=2)
r4 = range(10, 0, -1)    # 10, 9, 8, ..., 1 (countdown)

print("--- range ---")
print(type(r1), r1)                        # OUTPUT: <class 'range'> range(0, 5)
print(f"list(r1) = {list(r1)}")            # OUTPUT: list(r1) = [0, 1, 2, 3, 4]
print(f"list(r2) = {list(r2)}")            # OUTPUT: list(r2) = [2, 3, 4, 5, 6, 7]
print(f"list(r3) = {list(r3)}")            # OUTPUT: list(r3) = [0, 2, 4, 6, 8]
print(f"list(r4) = {list(r4)}")            # OUTPUT: list(r4) = [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
print(f"len(r1) = {len(r1)}")              # OUTPUT: len(r1) = 5
print(f"5 in range(10) = {5 in range(10)}")  # OUTPUT: 5 in range(10) = True
print(f"r3[2] = {r3[2]}")                  # OUTPUT: r3[2] = 4
print(f"r3[-1] = {r3[-1]}")                # OUTPUT: r3[-1] = 8

# --- input() for range ---
# n = int(input("Count to: "))              # INPUT: 5
# for i in range(n):                        # loops 0,1,2,3,4
#     print(i)
#
# start, stop, step = map(int, input("start stop step: ").split())
#   INPUT: 0 10 2              => range(0, 10, 2) => [0, 2, 4, 6, 8]
print()


# =============================================================================
# 6. SET TYPES
# =============================================================================

# --- 6.1 set (Mutable unordered collection of unique elements) ---
# No duplicates, no indexing, elements must be hashable.

s1 = {1, 2, 3, 4, 5}
s2 = {1, 2, 2, 3, 3}          # duplicates removed => {1, 2, 3}
s3 = set([1, 2, 3, 2, 1])     # from list => {1, 2, 3}
s4 = set("hello")             # => {'h', 'e', 'l', 'o'} (unique chars)
s5 = set()                    # empty set (NOT {} — that's a dict!)

print("--- set ---")
print(type(s1), s1)                        # OUTPUT: <class 'set'> {1, 2, 3, 4, 5}
print(f"duplicates removed: {s2}")         # OUTPUT: duplicates removed: {1, 2, 3}
print(f"from string: {s4}")               # OUTPUT: from string: {'h', 'o', 'l', 'e'} (order varies)
print(f"empty set: {s5}, type: {type(s5)}")  # OUTPUT: empty set: set(), type: <class 'set'>
print(f"empty braces: {type({})}")         # OUTPUT: empty braces: <class 'dict'>

# Set methods
s = {1, 2, 3}
s.add(4)                      # add single element
print(f"add: {s}")                         # OUTPUT: add: {1, 2, 3, 4}
s.update([5, 6, 7])           # add multiple
print(f"update: {s}")                      # OUTPUT: update: {1, 2, 3, 4, 5, 6, 7}
s.discard(7)                  # remove if present (no error if missing)
print(f"discard: {s}")                     # OUTPUT: discard: {1, 2, 3, 4, 5, 6}
s.remove(6)                   # remove (KeyError if missing!)
print(f"remove: {s}")                      # OUTPUT: remove: {1, 2, 3, 4, 5}
popped_s = s.pop()            # remove and return arbitrary element
print(f"pop: {popped_s}")                  # OUTPUT: pop: 1 (or any element — order not guaranteed)

# Set operations
a_s = {1, 2, 3, 4}
b_s = {3, 4, 5, 6}
print(f"union: {a_s | b_s}")              # OUTPUT: union: {1, 2, 3, 4, 5, 6}
print(f"union: {a_s.union(b_s)}")          # OUTPUT: union: {1, 2, 3, 4, 5, 6}
print(f"intersection: {a_s & b_s}")        # OUTPUT: intersection: {3, 4}
print(f"intersection: {a_s.intersection(b_s)}")  # OUTPUT: intersection: {3, 4}
print(f"difference: {a_s - b_s}")          # OUTPUT: difference: {1, 2}
print(f"difference: {a_s.difference(b_s)}")  # OUTPUT: difference: {1, 2}
print(f"symmetric_diff: {a_s ^ b_s}")      # OUTPUT: symmetric_diff: {1, 2, 5, 6}
print(f"issubset: {({1, 2}).issubset(a_s)}")  # OUTPUT: issubset: True
print(f"issuperset: {a_s.issuperset({1, 2})}")  # OUTPUT: issuperset: True
print(f"isdisjoint: {a_s.isdisjoint({7, 8})}")  # OUTPUT: isdisjoint: True

# Set comprehension
even_set = {x for x in range(10) if x % 2 == 0}
print(f"set comprehension: {even_set}")    # OUTPUT: set comprehension: {0, 2, 4, 6, 8}

# --- input() for set ---
# unique_nums = set(map(int, input("Enter numbers: ").split()))
#   INPUT: 1 2 3 2 1           => {1, 2, 3}
#
# unique_chars = set(input("Enter text: "))
#   INPUT: hello               => {'h', 'e', 'l', 'o'}
print()


# --- 6.2 frozenset (Immutable set) ---
# Same as set but cannot be modified. Can be used as dict key or set element.

fs1 = frozenset([1, 2, 3])
fs2 = frozenset("hello")

print("--- frozenset ---")
print(type(fs1), fs1)                      # OUTPUT: <class 'frozenset'> frozenset({1, 2, 3})
print(f"from string: {fs2}")              # OUTPUT: from string: frozenset({'h', 'o', 'l', 'e'})
print(f"union: {fs1 | frozenset([3, 4])}") # OUTPUT: union: frozenset({1, 2, 3, 4})
# fs1.add(4)  # AttributeError! frozenset is immutable

# frozenset can be used as dict key (because it's hashable)
d = {fs1: "value"}
print(f"as dict key: {d}")                 # OUTPUT: as dict key: {frozenset({1, 2, 3}): 'value'}
print()


# =============================================================================
# 7. MAPPING TYPE
# =============================================================================

# --- 7.1 dict (Dictionary — mutable key-value mapping) ---
# Keys must be hashable (immutable). Values can be anything.

d1 = {"name": "Alice", "age": 30}
d2 = dict(name="Alice", age=30)      # keyword args
d3 = dict([("a", 1), ("b", 2)])      # from list of tuples
d4 = dict(zip(["x", "y"], [1, 2]))   # from zip
d5 = {}                               # empty dict
d6 = dict()                           # empty dict
d7 = {i: i**2 for i in range(5)}     # dict comprehension

print("--- dict ---")
print(type(d1), d1)                        # OUTPUT: <class 'dict'> {'name': 'Alice', 'age': 30}
print(f"comprehension: {d7}")              # OUTPUT: comprehension: {0: 0, 1: 1, 2: 4, 3: 9, 4: 16}

# Accessing values
print(f"d1['name'] = {d1['name']}")        # OUTPUT: d1['name'] = Alice
# print(d1['missing'])  # KeyError: 'missing'
print(f"d1.get('name') = {d1.get('name')}")  # OUTPUT: d1.get('name') = Alice
print(f"d1.get('missing') = {d1.get('missing')}")  # OUTPUT: d1.get('missing') = None
print(f"d1.get('missing', 'default') = {d1.get('missing', 'default')}")  # OUTPUT: ... = default

# Modifying
d1["email"] = "alice@example.com"     # add/update key
print(f"after add: {d1}")                  # OUTPUT: after add: {'name': 'Alice', 'age': 30, 'email': 'alice@example.com'}
d1.update({"age": 31, "city": "NYC"}) # update multiple
print(f"after update: {d1}")               # OUTPUT: after update: {'name': 'Alice', 'age': 31, 'email': 'alice@example.com', 'city': 'NYC'}
d1.setdefault("country", "US")        # set only if key missing
print(f"setdefault: {d1}")                 # OUTPUT: ... 'country': 'US'}
d1.setdefault("country", "UK")        # key exists, no change
print(f"setdefault existing: {d1['country']}")  # OUTPUT: setdefault existing: US

# Removing
popped_d = d1.pop("email")            # remove and return
print(f"pop: {popped_d}")                  # OUTPUT: pop: alice@example.com
last = d1.popitem()                   # remove last inserted pair (3.7+)
print(f"popitem: {last}")                  # OUTPUT: popitem: ('country', 'US')
del d1["city"]                        # delete key
print(f"after del: {d1}")                  # OUTPUT: after del: {'name': 'Alice', 'age': 31}

# Views
print(f"keys: {list(d1.keys())}")          # OUTPUT: keys: ['name', 'age']
print(f"values: {list(d1.values())}")      # OUTPUT: values: ['Alice', 31]
print(f"items: {list(d1.items())}")        # OUTPUT: items: [('name', 'Alice'), ('age', 31)]

# Membership test (checks KEYS, not values)
print(f"'name' in d1: {'name' in d1}")     # OUTPUT: 'name' in d1: True
print(f"'Alice' in d1: {'Alice' in d1}")   # OUTPUT: 'Alice' in d1: False

# Iterating
for key, value in d1.items():
    print(f"  {key}: {value}")
# OUTPUT:
#   name: Alice
#   age: 31

# Merging (Python 3.9+)
d_a = {"a": 1, "b": 2}
d_b = {"b": 3, "c": 4}
merged = d_a | d_b      # => {'a': 1, 'b': 3, 'c': 4} (right wins)
print(f"merge |: {merged}")                # OUTPUT: merge |: {'a': 1, 'b': 3, 'c': 4}

# Nested dict
nested = {"user": {"name": "Bob", "scores": [90, 85, 92]}}
print(f"nested: {nested['user']['scores'][1]}")  # OUTPUT: nested: 85

d1.clear()
print(f"clear: {d1}")                      # OUTPUT: clear: {}

# --- input() for dict ---
# n = int(input("How many entries? "))       # INPUT: 2
# d = {}
# for _ in range(n):
#     key = input("Key: ")                   # INPUT: name
#     val = input("Value: ")                 # INPUT: Alice
#     d[key] = val
# Result: {'name': 'Alice', ...}
#
# One-liner dict from "key:value" pairs:
# pairs = input("Enter key:val pairs (space-sep): ").split()  # INPUT: name:Alice age:30
# d = dict(p.split(":") for p in pairs)     # => {'name': 'Alice', 'age': '30'}
#
# JSON-like input:
# import json
# d = json.loads(input("Enter JSON: "))     # INPUT: {"name": "Alice", "age": 30}
#                                           # => {'name': 'Alice', 'age': 30}
print()


# =============================================================================
# 8. NONE TYPE
# =============================================================================

# --- 8.1 NoneType ---
# Represents absence of value. Only one instance: None.

n = None
print("--- NoneType ---")
print(type(n), n)                          # OUTPUT: <class 'NoneType'> None
print(f"n is None: {n is None}")           # OUTPUT: n is None: True
print(f"n == None: {n == None}")           # OUTPUT: n == None: True (but use 'is' instead)
print(f"bool(None): {bool(None)}")         # OUTPUT: bool(None): False

def no_return():
    pass

result = no_return()
print(f"function with no return: {result}")  # OUTPUT: function with no return: None

# --- input() for None ---
# val = input("Enter something (or leave blank): ") or None
#   INPUT: (empty enter)       => val = None
#   INPUT: hello               => val = "hello"
print()


# =============================================================================
# 9. BINARY SEQUENCE — already covered in section 4
# =============================================================================


# =============================================================================
# 10. ENUM TYPE
# =============================================================================

from enum import Enum, IntEnum, Flag, auto

class Color(Enum):
    RED = 1
    GREEN = 2
    BLUE = 3

class Direction(Enum):
    NORTH = auto()   # auto-assigned values
    SOUTH = auto()
    EAST = auto()
    WEST = auto()

class Permission(IntEnum):  # can be compared with ints
    READ = 4
    WRITE = 2
    EXECUTE = 1

class FileFlag(Flag):
    READ = auto()
    WRITE = auto()
    EXECUTE = auto()

print("--- Enum ---")
print(f"Color.RED = {Color.RED}")          # OUTPUT: Color.RED = Color.RED
print(f"Color.RED.name = {Color.RED.name}")  # OUTPUT: Color.RED.name = RED
print(f"Color.RED.value = {Color.RED.value}")  # OUTPUT: Color.RED.value = 1
print(f"Color(1) = {Color(1)}")            # OUTPUT: Color(1) = Color.RED
print(f"Color['RED'] = {Color['RED']}")    # OUTPUT: Color['RED'] = Color.RED
print(f"list: {list(Color)}")              # OUTPUT: list: [<Color.RED: 1>, <Color.GREEN: 2>, <Color.BLUE: 3>]

print(f"\nDirection.NORTH.value = {Direction.NORTH.value}")  # OUTPUT: Direction.NORTH.value = 1

print(f"\nPermission.READ > Permission.WRITE = {Permission.READ > Permission.WRITE}")
# OUTPUT: Permission.READ > Permission.WRITE = True

combined = FileFlag.READ | FileFlag.WRITE
print(f"\nFlags combined: {combined}")     # OUTPUT: Flags combined: FileFlag.READ|WRITE
print(f"READ in combined: {FileFlag.READ in combined}")  # OUTPUT: READ in combined: True

# --- input() for Enum ---
# choice = input("Pick color (RED/GREEN/BLUE): ").upper()  # INPUT: red => "RED"
# color = Color[choice]                                     # => Color.RED
# Or by value:
# color = Color(int(input("Color number (1/2/3): ")))       # INPUT: 2 => Color.GREEN
print()


# =============================================================================
# 11. TYPE HINTS / ANNOTATIONS (not runtime types, but important)
# =============================================================================

from typing import (
    List, Dict, Tuple, Set, Optional, Union,
    Any, Callable, Iterator, Generator,
    TypeVar, Generic, Final, Literal,
)

# Basic type hints
name_hint: str = "Alice"
age_hint: int = 30
score_hint: float = 95.5
active_hint: bool = True

# Collection type hints (modern Python 3.9+ style)
numbers: list[int] = [1, 2, 3]
mapping: dict[str, int] = {"a": 1}
coordinates: tuple[float, float] = (1.0, 2.0)
unique: set[str] = {"a", "b"}

# Special type hints
maybe_name: Optional[str] = None       # str or None
flexible: Union[int, str] = "hello"    # int or str
anything: Any = [1, "two", 3.0]
constant: Final = 42                   # should not be reassigned
direction: Literal["north", "south"] = "north"

# Function type hints
def greet(name: str, times: int = 1) -> str:
    return f"Hello, {name}! " * times

# Callable type hint
def apply(func: Callable[[int, int], int], a: int, b: int) -> int:
    return func(a, b)

print("--- Type Hints ---")
print(f"greet('Bob', 2) = {greet('Bob', 2)}")  # OUTPUT: greet('Bob', 2) = Hello, Bob! Hello, Bob!
print(f"apply(lambda a,b: a+b, 3, 4) = {apply(lambda a, b: a + b, 3, 4)}")  # OUTPUT: ... = 7
print()


# =============================================================================
# 12. SPECIAL / ADVANCED TYPES
# =============================================================================

# --- 12.1 type (The type of types — metaclass) ---
print("--- type ---")
print(f"type(42) = {type(42)}")            # OUTPUT: type(42) = <class 'int'>
print(f"type(int) = {type(int)}")          # OUTPUT: type(int) = <class 'type'>
print(f"type(type) = {type(type)}")        # OUTPUT: type(type) = <class 'type'>

# Dynamic class creation with type()
MyClass = type("MyClass", (object,), {"x": 10, "greet": lambda self: "hi"})
obj = MyClass()
print(f"dynamic class: {obj.x}, {obj.greet()}")  # OUTPUT: dynamic class: 10, hi
print()


# --- 12.2 object (Base class for everything) ---
print("--- object ---")
o = object()
print(f"type: {type(o)}")                  # OUTPUT: type: <class 'object'>
print(f"isinstance(42, object) = {isinstance(42, object)}")    # OUTPUT: ... = True
print(f"isinstance('hi', object) = {isinstance('hi', object)}")  # OUTPUT: ... = True
print(f"isinstance(None, object) = {isinstance(None, object)}")  # OUTPUT: ... = True
# Everything in Python is an object!
print()


# --- 12.3 Ellipsis ---
print("--- Ellipsis ---")
print(f"type: {type(...)}")                # OUTPUT: type: <class 'ellipsis'>
print(f"... is Ellipsis: {... is Ellipsis}")  # OUTPUT: ... is Ellipsis: True
# Used as placeholder in type hints, slicing (NumPy), and stubs:
# def todo(): ...


# --- 12.4 NotImplemented ---
print("--- NotImplemented ---")
print(f"type: {type(NotImplemented)}")     # OUTPUT: type: <class 'NotImplementedType'>
# Returned by special methods (__eq__, __add__, etc.) to signal
# that the operation is not supported for the given types.
print()


# =============================================================================
# 13. COLLECTIONS MODULE (Specialized container datatypes)
# =============================================================================

from collections import (
    OrderedDict, defaultdict, Counter, deque, ChainMap
)

# --- 13.1 defaultdict ---
dd = defaultdict(int)            # missing keys default to 0
dd["a"] += 1
dd["b"] += 5
print("--- defaultdict ---")
print(f"dd = {dict(dd)}")                  # OUTPUT: dd = {'a': 1, 'b': 5}
print(f"dd['missing'] = {dd['missing']}")  # OUTPUT: dd['missing'] = 0

dd_list = defaultdict(list)
dd_list["fruits"].append("apple")
dd_list["fruits"].append("banana")
print(f"dd_list = {dict(dd_list)}")        # OUTPUT: dd_list = {'fruits': ['apple', 'banana']}

# --- 13.2 Counter ---
print("\n--- Counter ---")
cnt = Counter("abracadabra")
print(f"Counter: {cnt}")                   # OUTPUT: Counter: Counter({'a': 5, 'b': 2, 'r': 2, 'c': 1, 'd': 1})
print(f"most_common(2): {cnt.most_common(2)}")  # OUTPUT: most_common(2): [('a', 5), ('b', 2)]
cnt2 = Counter(["red", "blue", "red", "green", "blue", "red"])
print(f"Counter from list: {cnt2}")        # OUTPUT: Counter from list: Counter({'red': 3, 'blue': 2, 'green': 1})
print(f"total: {cnt2.total()}")            # OUTPUT: total: 6

# --- 13.3 deque (Double-ended queue) ---
print("\n--- deque ---")
dq = deque([1, 2, 3])
dq.appendleft(0)
dq.append(4)
print(f"deque: {dq}")                      # OUTPUT: deque: deque([0, 1, 2, 3, 4])
dq.popleft()
print(f"after popleft: {dq}")              # OUTPUT: after popleft: deque([1, 2, 3, 4])
dq.rotate(1)                    # rotate right
print(f"rotate(1): {dq}")                  # OUTPUT: rotate(1): deque([4, 1, 2, 3])
dq.rotate(-1)                   # rotate left
print(f"rotate(-1): {dq}")                 # OUTPUT: rotate(-1): deque([1, 2, 3, 4])
# deque with maxlen => auto-discards oldest when full
bounded = deque(maxlen=3)
for i in range(5):
    bounded.append(i)
print(f"bounded deque: {bounded}")         # OUTPUT: bounded deque: deque([2, 3, 4], maxlen=3)

# --- 13.4 OrderedDict ---
print("\n--- OrderedDict ---")
od = OrderedDict([("b", 2), ("a", 1), ("c", 3)])
print(f"OrderedDict: {od}")                # OUTPUT: OrderedDict: OrderedDict([('b', 2), ('a', 1), ('c', 3)])
od.move_to_end("a")
print(f"move_to_end: {od}")                # OUTPUT: ... [('b', 2), ('c', 3), ('a', 1)]
od.move_to_end("c", last=False)  # move to beginning
print(f"move_to_front: {od}")              # OUTPUT: ... [('c', 3), ('b', 2), ('a', 1)]

# --- 13.5 ChainMap ---
print("\n--- ChainMap ---")
defaults = {"color": "blue", "size": "medium"}
user_prefs = {"color": "red"}
combined_cm = ChainMap(user_prefs, defaults)
print(f"ChainMap: {combined_cm['color']}")  # OUTPUT: ChainMap: red
print(f"ChainMap: {combined_cm['size']}")   # OUTPUT: ChainMap: medium
print()


# =============================================================================
# 14. DATACLASSES & TYPED STRUCTURES
# =============================================================================

from dataclasses import dataclass, field

@dataclass
class Person:
    name: str
    age: int
    hobbies: list = field(default_factory=list)

    def greet(self):
        return f"Hi, I'm {self.name}!"

@dataclass(frozen=True)  # immutable dataclass
class Coordinate:
    x: float
    y: float

print("--- dataclass ---")
p1 = Person("Alice", 30, ["reading"])
p2 = Person("Alice", 30, ["reading"])
print(f"Person: {p1}")                     # OUTPUT: Person: Person(name='Alice', age=30, hobbies=['reading'])
print(f"equality: {p1 == p2}")             # OUTPUT: equality: True
print(f"greet: {p1.greet()}")              # OUTPUT: greet: Hi, I'm Alice!

coord = Coordinate(1.0, 2.0)
print(f"frozen: {coord}")                  # OUTPUT: frozen: Coordinate(x=1.0, y=2.0)
# coord.x = 3.0  # FrozenInstanceError!

# --- input() for dataclass ---
# name = input("Name: ")                    # INPUT: Bob
# age = int(input("Age: "))                 # INPUT: 25
# person = Person(name, age)                # => Person(name='Bob', age=25, hobbies=[])
print()

# --- typing.NamedTuple ---
from typing import NamedTuple

class Employee(NamedTuple):
    name: str
    department: str
    salary: float = 50000.0

emp = Employee("Bob", "Engineering", 75000.0)
print("--- NamedTuple ---")
print(f"Employee: {emp}")                  # OUTPUT: Employee: Employee(name='Bob', department='Engineering', salary=75000.0)
print(f"name: {emp.name}, dept: {emp[1]}") # OUTPUT: name: Bob, dept: Engineering
print()

# --- TypedDict ---
from typing import TypedDict

class Movie(TypedDict):
    title: str
    year: int
    rating: float

movie: Movie = {"title": "Inception", "year": 2010, "rating": 8.8}
print("--- TypedDict ---")
print(f"Movie: {movie}")                  # OUTPUT: Movie: {'title': 'Inception', 'year': 2010, 'rating': 8.8}
print(f"type: {type(movie)}")             # OUTPUT: type: <class 'dict'>
print()


# =============================================================================
# 15. ITERATOR & GENERATOR TYPES
# =============================================================================

# --- 15.1 Iterator ---
print("--- iterator ---")
my_list = [10, 20, 30]
it = iter(my_list)
print(f"type: {type(it)}")                # OUTPUT: type: <class 'list_iterator'>
print(f"next: {next(it)}")                # OUTPUT: next: 10
print(f"next: {next(it)}")                # OUTPUT: next: 20
print(f"next: {next(it)}")                # OUTPUT: next: 30
# next(it)  # raises StopIteration

# Custom iterator
class Countdown:
    def __init__(self, start):
        self.start = start

    def __iter__(self):
        return self

    def __next__(self):
        if self.start <= 0:
            raise StopIteration
        self.start -= 1
        return self.start + 1

print(f"custom iterator: {list(Countdown(3))}")  # OUTPUT: custom iterator: [3, 2, 1]

# --- 15.2 Generator ---
print("\n--- generator ---")

def fibonacci(n):
    a, b = 0, 1
    for _ in range(n):
        yield a
        a, b = b, a + b

gen = fibonacci(8)
print(f"type: {type(gen)}")               # OUTPUT: type: <class 'generator'>
print(f"fibonacci: {list(fibonacci(8))}")  # OUTPUT: fibonacci: [0, 1, 1, 2, 3, 5, 8, 13]

# Generator expression (like list comprehension but lazy)
gen_expr = (x**2 for x in range(5))
print(f"gen expression type: {type(gen_expr)}")  # OUTPUT: gen expression type: <class 'generator'>
print(f"gen expression: {list(gen_expr)}")  # OUTPUT: gen expression: [0, 1, 4, 9, 16]

# Generator with send()
def accumulator():
    total = 0
    while True:
        value = yield total
        if value is None:
            break
        total += value

acc = accumulator()
next(acc)         # prime the generator
print(f"send(10): {acc.send(10)}")         # OUTPUT: send(10): 10
print(f"send(20): {acc.send(20)}")         # OUTPUT: send(20): 30
print(f"send(5): {acc.send(5)}")           # OUTPUT: send(5): 35
print()


# =============================================================================
# 16. CALLABLE TYPES
# =============================================================================

print("--- Callable types ---")

# Regular function
def add(a, b):
    return a + b
print(f"function: {type(add)}, {add(2, 3)}")  # OUTPUT: function: <class 'function'>, 5

# Lambda (anonymous function)
multiply = lambda a, b: a * b
print(f"lambda: {type(multiply)}, {multiply(2, 3)}")  # OUTPUT: lambda: <class 'function'>, 6

# Built-in function
print(f"built-in: {type(len)}")            # OUTPUT: built-in: <class 'builtin_function_or_method'>

# Method
class Calculator:
    def add(self, a, b):
        return a + b

    @staticmethod
    def static_add(a, b):
        return a + b

    @classmethod
    def from_string(cls, s):
        return cls()

calc = Calculator()
print(f"method: {type(calc.add)}")         # OUTPUT: method: <class 'method'>
print(f"static method: {type(Calculator.static_add)}")  # OUTPUT: static method: <class 'function'>
print(f"class method: {type(Calculator.from_string)}")  # OUTPUT: class method: <class 'method'>

# Callable object (class with __call__)
class Multiplier:
    def __init__(self, factor):
        self.factor = factor

    def __call__(self, value):
        return value * self.factor

double = Multiplier(2)
print(f"callable object: {double(5)}")     # OUTPUT: callable object: 10
print(f"is callable: {callable(double)}")  # OUTPUT: is callable: True

# Closures
def make_adder(n):
    def adder(x):
        return x + n
    return adder

add5 = make_adder(5)
print(f"closure: {add5(10)}")              # OUTPUT: closure: 15

# Partial functions
from functools import partial
add10 = partial(add, 10)
print(f"partial: {add10(5)}")              # OUTPUT: partial: 15
print()


# =============================================================================
# 17. CONTEXT MANAGER TYPE
# =============================================================================

from contextlib import contextmanager

class ManagedResource:
    def __enter__(self):
        print("  Resource acquired")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print("  Resource released")
        return False  # don't suppress exceptions

@contextmanager
def managed_resource():
    print("  Setup")
    yield "resource_value"
    print("  Teardown")

print("--- Context Manager ---")
with ManagedResource() as r:
    print(f"  Using: {type(r)}")
# OUTPUT:
#   Resource acquired
#   Using: <class '__main__.ManagedResource'>
#   Resource released

with managed_resource() as val:
    print(f"  Value: {val}")
# OUTPUT:
#   Setup
#   Value: resource_value
#   Teardown
print()


# =============================================================================
# 18. REGEX MATCH TYPE
# =============================================================================

import re

print("--- regex Match ---")
pattern = r"(\d{4})-(\d{2})-(\d{2})"
match = re.search(pattern, "Today is 2024-01-15, enjoy!")
if match:
    print(f"type: {type(match)}")          # OUTPUT: type: <class 're.Match'>
    print(f"full match: {match.group()}")  # OUTPUT: full match: 2024-01-15
    print(f"group(1): {match.group(1)}")   # OUTPUT: group(1): 2024
    print(f"groups: {match.groups()}")     # OUTPUT: groups: ('2024', '01', '15')
    print(f"span: {match.span()}")         # OUTPUT: span: (9, 19)
    print(f"start: {match.start()}, end: {match.end()}")  # OUTPUT: start: 9, end: 19

# --- input() for regex ---
# import re
# text = input("Enter text: ")              # INPUT: Call me at 555-1234
# phones = re.findall(r'\d{3}-\d{4}', text) # => ['555-1234']
#
# email = input("Enter email: ")            # INPUT: user@example.com
# if re.match(r'^[\w.-]+@[\w.-]+\.\w+$', email):
#     print("Valid email")                   # OUTPUT: Valid email
print()


# =============================================================================
# 19. DATETIME TYPES
# =============================================================================

from datetime import date, time, datetime, timedelta, timezone

print("--- datetime types ---")

# date
d = date(2024, 1, 15)
today = date.today()
print(f"date: {d}, today: {today}")        # OUTPUT: date: 2024-01-15, today: 2026-07-02
print(f"year: {d.year}, month: {d.month}, day: {d.day}")  # OUTPUT: year: 2024, month: 1, day: 15
print(f"weekday: {d.weekday()}")           # OUTPUT: weekday: 0 (Monday)
print(f"isoformat: {d.isoformat()}")       # OUTPUT: isoformat: 2024-01-15
print(f"strftime: {d.strftime('%B %d, %Y')}")  # OUTPUT: strftime: January 15, 2024

# time
t = time(14, 30, 45)
print(f"\ntime: {t}")                      # OUTPUT: time: 14:30:45
print(f"hour: {t.hour}, minute: {t.minute}, second: {t.second}")
# OUTPUT: hour: 14, minute: 30, second: 45

# datetime
dt = datetime(2024, 1, 15, 14, 30, 45)
now = datetime.now()
utc_now = datetime.now(timezone.utc)
print(f"\ndatetime: {dt}")                 # OUTPUT: datetime: 2024-01-15 14:30:45
print(f"now: {now}")                       # OUTPUT: now: 2026-07-02 ...
print(f"utc now: {utc_now}")               # OUTPUT: utc now: 2026-07-02 ...+00:00
print(f"from string: {datetime.strptime('2024-01-15', '%Y-%m-%d')}")
# OUTPUT: from string: 2024-01-15 00:00:00
print(f"timestamp: {dt.timestamp()}")      # OUTPUT: timestamp: 1705312245.0
print(f"from timestamp: {datetime.fromtimestamp(1705312245)}")
# OUTPUT: from timestamp: 2024-01-15 14:30:45

# timedelta
delta = timedelta(days=7, hours=3, minutes=30)
print(f"\ntimedelta: {delta}")             # OUTPUT: timedelta: 7 days, 3:30:00
print(f"total seconds: {delta.total_seconds()}")  # OUTPUT: total seconds: 617400.0
print(f"date + delta: {d + delta}")        # OUTPUT: date + delta: 2024-01-22
print(f"date diff: {date(2024, 12, 31) - date(2024, 1, 1)}")  # OUTPUT: date diff: 365 days, 0:00:00

# --- input() for datetime ---
# date_str = input("Enter date (YYYY-MM-DD): ")        # INPUT: 2024-06-15
# d = datetime.strptime(date_str, "%Y-%m-%d").date()    # => datetime.date(2024, 6, 15)
#
# dt_str = input("Enter datetime (YYYY-MM-DD HH:MM): ")  # INPUT: 2024-06-15 14:30
# dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")       # => datetime(2024, 6, 15, 14, 30)
#
# year, month, day = map(int, input("Year Month Day: ").split())  # INPUT: 2024 6 15
# d = date(year, month, day)                               # => datetime.date(2024, 6, 15)
print()


# =============================================================================
# 20. DECIMAL & FRACTION (Exact arithmetic)
# =============================================================================

from decimal import Decimal, getcontext
from fractions import Fraction

print("--- Decimal ---")
d1_dec = Decimal("0.1")
d2_dec = Decimal("0.2")
print(f"Decimal: {d1_dec + d2_dec}")       # OUTPUT: Decimal: 0.3
print(f"float:   {0.1 + 0.2}")            # OUTPUT: float:   0.30000000000000004
print(f"Decimal('1') / Decimal('3') = {Decimal('1') / Decimal('3')}")
# OUTPUT: Decimal('1') / Decimal('3') = 0.3333333333333333333333333333

getcontext().prec = 50  # set precision
print(f"high precision: {Decimal(1) / Decimal(7)}")
# OUTPUT: high precision: 0.14285714285714285714285714285714285714285714285714

print("\n--- Fraction ---")
f1 = Fraction(1, 3)
f2 = Fraction(1, 6)
print(f"Fraction: {f1} + {f2} = {f1 + f2}")  # OUTPUT: Fraction: 1/3 + 1/6 = 1/2
print(f"from float: {Fraction(0.5)}")      # OUTPUT: from float: 1/2
print(f"from string: {Fraction('7/3')}")   # OUTPUT: from string: 7/3
print(f"limit_denominator: {Fraction(3.14159).limit_denominator(100)}")
# OUTPUT: limit_denominator: 311/99

# --- input() for Decimal/Fraction ---
# price = Decimal(input("Enter price: "))   # INPUT: 19.99 => Decimal('19.99')
# frac = Fraction(input("Enter fraction: "))  # INPUT: 3/4 => Fraction(3, 4)
print()


# =============================================================================
# 21. PATH TYPE
# =============================================================================

from pathlib import Path

print("--- Path ---")
p = Path(".")
print(f"type: {type(p)}")                  # OUTPUT: type: <class 'pathlib.WindowsPath'> (or PosixPath)
print(f"cwd: {Path.cwd()}")               # OUTPUT: cwd: /current/working/directory
print(f"home: {Path.home()}")             # OUTPUT: home: /home/username (or C:\Users\...)
print(f"resolve: {p.resolve()}")           # OUTPUT: resolve: /full/absolute/path
print(f"exists: {p.exists()}")             # OUTPUT: exists: True
print(f"is_dir: {p.is_dir()}")             # OUTPUT: is_dir: True

# Path construction
p2 = Path("folder") / "subfolder" / "file.txt"
print(f"joined: {p2}")                     # OUTPUT: joined: folder/subfolder/file.txt
print(f"parent: {p2.parent}")              # OUTPUT: parent: folder/subfolder
print(f"name: {p2.name}")                  # OUTPUT: name: file.txt
print(f"stem: {p2.stem}")                  # OUTPUT: stem: file
print(f"suffix: {p2.suffix}")              # OUTPUT: suffix: .txt
print(f"parts: {p2.parts}")               # OUTPUT: parts: ('folder', 'subfolder', 'file.txt')

# --- input() for Path ---
# filepath = Path(input("Enter file path: "))  # INPUT: /home/user/doc.txt
# print(f"exists: {filepath.exists()}")         # OUTPUT: exists: True/False
# print(f"name: {filepath.name}")               # OUTPUT: name: doc.txt
print()


# =============================================================================
# 22. QUEUE TYPES (Thread-safe)
# =============================================================================

from queue import Queue, LifoQueue, PriorityQueue

print("--- Queue types ---")
# FIFO Queue
q = Queue(maxsize=3)
q.put("first")
q.put("second")
print(f"FIFO get: {q.get()}")             # OUTPUT: FIFO get: first

# LIFO Queue (Stack)
lq = LifoQueue()
lq.put("first")
lq.put("second")
print(f"LIFO get: {lq.get()}")            # OUTPUT: LIFO get: second

# Priority Queue
pq = PriorityQueue()
pq.put((2, "medium"))
pq.put((1, "high"))
pq.put((3, "low"))
print(f"Priority get: {pq.get()}")        # OUTPUT: Priority get: (1, 'high')
print()


# =============================================================================
# 23. WEAKREF TYPE
# =============================================================================

import weakref

class MyObject:
    def __init__(self, name):
        self.name = name

print("--- weakref ---")
obj_wr = MyObject("test")
weak = weakref.ref(obj_wr)
print(f"type: {type(weak)}")              # OUTPUT: type: <class 'weakref'>
print(f"alive: {weak()}")                 # OUTPUT: alive: <__main__.MyObject object at 0x...>
print(f"name: {weak().name}")             # OUTPUT: name: test
del obj_wr
print(f"after del: {weak()}")             # OUTPUT: after del: None
print()


# =============================================================================
# 24. TYPE CHECKING UTILITIES
# =============================================================================

print("--- Type checking ---")

# type() — returns exact type
print(f"type(42): {type(42)}")             # OUTPUT: type(42): <class 'int'>
print(f"type(42) == int: {type(42) == int}")  # OUTPUT: type(42) == int: True

# isinstance() — checks type hierarchy (preferred)
print(f"isinstance(42, int): {isinstance(42, int)}")  # OUTPUT: ... True
print(f"isinstance(True, int): {isinstance(True, int)}")  # OUTPUT: ... True (bool IS int!)
print(f"isinstance(42, (int, float)): {isinstance(42, (int, float))}")  # OUTPUT: ... True

# issubclass() — checks class hierarchy
print(f"issubclass(bool, int): {issubclass(bool, int)}")  # OUTPUT: ... True
print(f"issubclass(int, object): {issubclass(int, object)}")  # OUTPUT: ... True

# id() — unique identity of object
a_id = [1, 2, 3]
b_id = a_id
c_id = [1, 2, 3]
print(f"\nid(a) == id(b): {id(a_id) == id(b_id)}")  # OUTPUT: id(a) == id(b): True
print(f"id(a) == id(c): {id(a_id) == id(c_id)}")    # OUTPUT: id(a) == id(c): False
print(f"a is b: {a_id is b_id}")           # OUTPUT: a is b: True
print(f"a is c: {a_id is c_id}")           # OUTPUT: a is c: False
print(f"a == c: {a_id == c_id}")           # OUTPUT: a == c: True


# =============================================================================
# 25. input() FUNCTION — COMPLETE REFERENCE
# =============================================================================

print()
print("=" * 70)
print("input() FUNCTION — ALL CASES")
print("=" * 70)

# input() always returns a STRING. You must convert manually.
# Syntax: variable = input("prompt message")

# All input() examples below are commented out so the script runs without blocking.
# Uncomment any section to test interactively.

# --- Basic string input ---
# name = input("Enter name: ")
#   USER TYPES: Alice
#   RESULT: name = "Alice" (type: str)

# --- Integer input ---
# age = int(input("Enter age: "))
#   USER TYPES: 25
#   RESULT: age = 25 (type: int)
#   ERROR IF: user types "abc" => ValueError: invalid literal for int()

# --- Float input ---
# price = float(input("Enter price: "))
#   USER TYPES: 19.99
#   RESULT: price = 19.99 (type: float)

# --- Boolean input (manual conversion) ---
# answer = input("Yes or No? ").strip().lower()
#   USER TYPES: Yes
#   RESULT: answer = "yes" (type: str)
# is_yes = answer in ("yes", "y", "true", "1")
#   RESULT: is_yes = True

# --- Multiple values on one line ---
# a, b, c = input("Enter 3 numbers: ").split()
#   USER TYPES: 10 20 30
#   RESULT: a="10", b="20", c="30" (all strings!)
#
# a, b, c = map(int, input("Enter 3 ints: ").split())
#   USER TYPES: 10 20 30
#   RESULT: a=10, b=20, c=30 (all ints)

# --- List from input ---
# nums = list(map(int, input("Enter numbers: ").split()))
#   USER TYPES: 1 2 3 4 5
#   RESULT: nums = [1, 2, 3, 4, 5]

# --- CSV input ---
# items = input("Enter CSV: ").split(",")
#   USER TYPES: apple,banana,cherry
#   RESULT: items = ['apple', 'banana', 'cherry']

# --- Multi-line input (read until empty line) ---
# lines = []
# while True:
#     line = input()
#     if line == "":
#         break
#     lines.append(line)
#   USER TYPES: hello
#   USER TYPES: world
#   USER TYPES: (empty enter)
#   RESULT: lines = ["hello", "world"]

# --- Input with default value ---
# name = input("Name [Anonymous]: ").strip() or "Anonymous"
#   USER TYPES: (empty enter)  => name = "Anonymous"
#   USER TYPES: Alice          => name = "Alice"

# --- Safe input with error handling ---
# while True:
#     try:
#         age = int(input("Enter age: "))
#         break
#     except ValueError:
#         print("Invalid! Enter a number.")
#   USER TYPES: abc            => "Invalid! Enter a number."
#   USER TYPES: 25             => age = 25 (breaks loop)

# --- Input with validation ---
# while True:
#     choice = input("Pick (a/b/c): ").lower()
#     if choice in ("a", "b", "c"):
#         break
#     print("Invalid choice!")
#   USER TYPES: x              => "Invalid choice!"
#   USER TYPES: a              => choice = "a" (breaks loop)

# --- Password-style input (hidden) ---
# import getpass
# password = getpass.getpass("Password: ")
#   USER TYPES: secret123      => password = "secret123" (not shown on screen)

# --- Tuple from input ---
# coords = tuple(map(float, input("x y: ").split()))
#   USER TYPES: 3.5 4.2        => coords = (3.5, 4.2)

# --- Dict from input ---
# pairs = input("key=val pairs: ").split()
#   USER TYPES: name=Alice age=30
# d = dict(p.split("=") for p in pairs)
#   RESULT: d = {'name': 'Alice', 'age': '30'}

# --- Set from input ---
# s = set(input("Enter words: ").split())
#   USER TYPES: hello world hello
#   RESULT: s = {'hello', 'world'}

# --- Complex number from input ---
# z = complex(input("Complex (e.g. 3+4j): "))
#   USER TYPES: 3+4j           => z = (3+4j)

# --- eval() — DANGEROUS, do not use with untrusted input ---
# result = eval(input("Expression: "))
#   USER TYPES: 2 + 3 * 4      => result = 14
#   USER TYPES: [1,2,3]        => result = [1, 2, 3]
#   WARNING: user could type __import__('os').system('rm -rf /') !!

# --- ast.literal_eval() — SAFE alternative to eval for literals ---
# import ast
# result = ast.literal_eval(input("Enter a Python literal: "))
#   USER TYPES: [1, 2, 3]      => result = [1, 2, 3] (type: list)
#   USER TYPES: {"a": 1}       => result = {'a': 1} (type: dict)
#   USER TYPES: (1, 2)         => result = (1, 2) (type: tuple)
#   USER TYPES: 42             => result = 42 (type: int)
#   USER TYPES: 3.14           => result = 3.14 (type: float)
#   USER TYPES: True           => result = True (type: bool)
#   USER TYPES: os.system("x") => ValueError (SAFE — rejects non-literals)


# =============================================================================
# SUMMARY TABLE
# =============================================================================
print()
print("=" * 70)
print("PYTHON DATA TYPES SUMMARY")
print("=" * 70)
print(f"""
{'Category':<20} {'Type':<15} {'Mutable':<10} {'Ordered':<10} {'input() conversion'}
{'-'*20} {'-'*15} {'-'*10} {'-'*10} {'-'*25}
{'Numeric':<20} {'int':<15} {'No':<10} {'N/A':<10} int(input())
{'Numeric':<20} {'float':<15} {'No':<10} {'N/A':<10} float(input())
{'Numeric':<20} {'complex':<15} {'No':<10} {'N/A':<10} complex(input())
{'Boolean':<20} {'bool':<15} {'No':<10} {'N/A':<10} input().lower()=="yes"
{'Text':<20} {'str':<15} {'No':<10} {'Yes':<10} input() (default!)
{'Binary':<20} {'bytes':<15} {'No':<10} {'Yes':<10} input().encode()
{'Binary':<20} {'bytearray':<15} {'Yes':<10} {'Yes':<10} bytearray(input(),"utf8")
{'Sequence':<20} {'list':<15} {'Yes':<10} {'Yes':<10} input().split()
{'Sequence':<20} {'tuple':<15} {'No':<10} {'Yes':<10} tuple(input().split())
{'Sequence':<20} {'range':<15} {'No':<10} {'Yes':<10} range(int(input()))
{'Set':<20} {'set':<15} {'Yes':<10} {'No':<10} set(input().split())
{'Set':<20} {'frozenset':<15} {'No':<10} {'No':<10} frozenset(input().split())
{'Mapping':<20} {'dict':<15} {'Yes':<10} {'Yes*':<10} json.loads(input())
{'None':<20} {'NoneType':<15} {'N/A':<10} {'N/A':<10} input() or None
{'DateTime':<20} {'datetime':<15} {'No':<10} {'N/A':<10} strptime(input(),fmt)
{'Exact Math':<20} {'Decimal':<15} {'No':<10} {'N/A':<10} Decimal(input())
{'Exact Math':<20} {'Fraction':<15} {'No':<10} {'N/A':<10} Fraction(input())

* dict is insertion-ordered since Python 3.7
""")
