// ============================================================
//  JAVASCRIPT FUNDAMENTALS - ULTIMATE QUICK REFERENCE
// ============================================================
//  Visualizer: http://latentflip.com/loupe/
//  Tutorial:   https://www.javascripttutorial.net/
// ============================================================


// ============================================================
// 1. DATA TYPES                                       [BASIC]
// ============================================================
// INTERVIEW: "Name all JS data types" is a top-5 question.
//
//  +------------------+----------------------------+
//  |    PRIMITIVES    |        DESCRIPTION         |
//  +------------------+----------------------------+
//  | string           | text data                  |
//  | number           | 64-bit IEEE 754 float      |
//  | bigint (ES2020)  | arbitrary-precision int    |
//  | boolean          | true / false               |
//  | undefined        | declared but unassigned    |
//  | null             | intentional "no value"     |
//  | symbol (ES2015)  | unique identifier          |
//  +------------------+----------------------------+
//  | COMPLEX          |                            |
//  +------------------+----------------------------+
//  | object           | collections / functions    |
//  +------------------+----------------------------+
//
// All primitives are immutable (value cannot be changed in place).
// Objects (including arrays, functions, dates) are mutable and passed by reference.


// ============================================================
// 2. typeof QUIRKS                                    [BASIC]
// ============================================================
// INTERVIEW: "What does typeof null return?" - extremely common trap.
//
//  +----------------------------+----------------+----------------------------+
//  |        EXPRESSION          |    RESULT      |          NOTE              |
//  +----------------------------+----------------+----------------------------+
//  | typeof undefined           | "undefined"    |                            |
//  | typeof true                | "boolean"      |                            |
//  | typeof 42                  | "number"       |                            |
//  | typeof 9007199254740991n   | "bigint"       |                            |
//  | typeof "hello"             | "string"       |                            |
//  | typeof Symbol()            | "symbol"       |                            |
//  | typeof null                | "object"       | BUG since ES1, kept forever|
//  | typeof {}                  | "object"       |                            |
//  | typeof []                  | "object"       | Use Array.isArray()        |
//  | typeof function(){}        | "function"     | Special subtype of object  |
//  | typeof undeclaredVar       | "undefined"    | Does NOT throw!            |
//  | typeof NaN                 | "number"       | NaN is a number type       |
//  +----------------------------+----------------+----------------------------+

console.log(typeof null);             // "object"  -- historical bug
console.log(typeof NaN);             // "number"
console.log(typeof function(){});    // "function"
console.log(typeof []);              // "object"   -- use Array.isArray([]) => true
console.log(typeof undeclaredVar);   // "undefined" -- safe check, no ReferenceError


// ============================================================
// 3. UNDEFINED vs UNDECLARED vs UNINITIALIZED         [BASIC]
// ============================================================

// Undefined: declared but no value assigned
let message;
console.log(message);        // undefined
console.log(typeof message); // "undefined"

// Undeclared: never declared at all
// console.log(counter);     // ReferenceError: counter is not defined

// Uninitialized: let/const in the Temporal Dead Zone (see TDZ.js)
// {
//   console.log(x);         // ReferenceError (TDZ)
//   let x = 5;
// }


// ============================================================
// 4. null vs undefined COMPARISON TABLE               [BASIC]
// ============================================================
//  +------------------------------+------+------+
//  |          CHECK               | null | undef|
//  +------------------------------+------+------+
//  | typeof                       |"object"|"undefined"|
//  | Boolean()                    | false| false|
//  | null == undefined            | true |      |
//  | null === undefined           | false|      |
//  | null == 0                    | false|      |
//  | undefined == 0              | false|      |
//  | null == false                | false|      |
//  | null + 1                     |  1   |      |
//  | undefined + 1                | NaN  |      |
//  +------------------------------+------+------+

console.log(null == undefined);  // true  (abstract equality)
console.log(null === undefined); // false (strict equality)
console.log(null + 1);          // 1     (null coerces to 0)
console.log(undefined + 1);     // NaN   (undefined coerces to NaN)


// ============================================================
// 5. NaN (Not a Number)                               [BASIC]
// ============================================================
// INTERVIEW: "How do you check for NaN?"

console.log('a' / 2);       // NaN
console.log(NaN === NaN);   // false  -- NaN is NOT equal to itself!
console.log(NaN + 5);       // NaN    -- any op with NaN => NaN

// Checking for NaN:
console.log(Number.isNaN(NaN));       // true  (preferred - no coercion)
console.log(Number.isNaN("hello"));   // false (no coercion)
console.log(isNaN("hello"));         // true  (coerces string first - legacy)


// ============================================================
// 6. EQUALITY COMPARISON TABLE                  [INTERMEDIATE]
// ============================================================
// INTERVIEW: "Difference between ==, ===, and Object.is()"
//
//  +--------------------+---+----+----------+---------------------------+
//  |    COMPARISON      |== | ===| Object.is|       NOTES               |
//  +--------------------+---+----+----------+---------------------------+
//  | 1 == "1"           | T |  F |    F     | == coerces string->number |
//  | 1 == true          | T |  F |    F     | == coerces bool->number   |
//  | 0 == false         | T |  F |    F     |                           |
//  | 0 == ""            | T |  F |    F     | "" -> 0                   |
//  | 0 == "0"           | T |  F |    F     |                           |
//  | "" == "0"          | F |  F |    F     | both strings, no coercion |
//  | null == undefined  | T |  F |    F     | special == rule           |
//  | null == 0          | F |  F |    F     | null only == undefined    |
//  | NaN == NaN         | F |  F |    F     |                           |
//  | NaN === NaN        | F |  F |    F     |                           |
//  | Object.is(NaN,NaN) | - |  - |    T     | Object.is handles NaN    |
//  | +0 === -0          | T |  T |    F     | Object.is distinguishes  |
//  | Object.is(+0, -0)  | - |  - |    F     | +0 and -0                |
//  +--------------------+---+----+----------+---------------------------+
//
// Rule of thumb: always use === unless you specifically want coercion.
// Use Object.is() when you need to distinguish NaN/NaN or +0/-0.

console.log(Object.is(NaN, NaN));   // true
console.log(Object.is(+0, -0));     // false
console.log(+0 === -0);            // true


// ============================================================
// 7. TYPE COERCION RULES                        [INTERMEDIATE]
// ============================================================
// INTERVIEW: "Explain implicit type coercion in JS."
//
// To Number:
//   +------------------+----------+
//   | Value            | Number   |
//   +------------------+----------+
//   | true             | 1        |
//   | false            | 0        |
//   | null             | 0        |
//   | undefined        | NaN      |
//   | ""               | 0        |
//   | "123"            | 123      |
//   | "abc"            | NaN      |
//   | []               | 0        |  ([] -> "" -> 0)
//   | [5]              | 5        |  ([5] -> "5" -> 5)
//   | {}               | NaN      |
//   +------------------+----------+
//
// To String:
//   +------------------+------------------+
//   | Value            | String           |
//   +------------------+------------------+
//   | true             | "true"           |
//   | false            | "false"          |
//   | null             | "null"           |
//   | undefined        | "undefined"      |
//   | 123              | "123"            |
//   | NaN              | "NaN"            |
//   | []               | ""               |
//   | [1,2]            | "1,2"            |
//   | {}               | "[object Object]"|
//   +------------------+------------------+
//
// To Boolean (falsy values - everything else is truthy):
//   false, 0, -0, 0n, "", null, undefined, NaN

// GOTCHA examples:
console.log([] + []);      // ""       (both toString -> "" + "")
console.log([] + {});      // "[object Object]"
console.log({} + []);      // "[object Object]" (or 0 in some consoles)
console.log(true + true);  // 2
console.log("5" - 3);      // 2  (string->number for -)
console.log("5" + 3);      // "53" (number->string for +)
console.log("5" * "2");    // 10 (both->number for *)


// ============================================================
// 8. BOOLEAN TRUTHINESS TABLE                         [BASIC]
// ============================================================
//  +-------------------+-------+--------+
//  |       Type        | true  | false  |
//  +-------------------+-------+--------+
//  | string            | "abc" |  ""    |
//  | number            | 1, -1,|  0, NaN|
//  |                   |Infinity|       |
//  | object            | {}, []| (n/a)  |
//  | null              |       | null   |
//  | undefined         |       | undef  |
//  +-------------------+-------+--------+
//
// GOTCHA: These are truthy!
console.log(Boolean("0"));       // true  (non-empty string)
console.log(Boolean("false"));   // true  (non-empty string)
console.log(Boolean([]));        // true  (empty array IS truthy)
console.log(Boolean({}));        // true  (empty object IS truthy)
console.log(Boolean(new Boolean(false))); // true (object wrapper)


// ============================================================
// 9. STRINGS                                          [BASIC]
// ============================================================
// Strings are immutable. Operations create NEW strings.

let str = 'JavaScript';
str = str + ' String';   // new string created, old one garbage-collected

// Template literals (ES6)
const name = "World";
console.log(`Hello, ${name}!`);   // "Hello, World!"

// Tagged template literals [ADVANCED]
function highlight(strings, ...values) {
  return strings.reduce((result, str, i) =>
    `${result}${str}${values[i] ? `**${values[i]}**` : ''}`, '');
}
const x = 42;
console.log(highlight`The answer is ${x}`); // "The answer is **42**"


// ============================================================
// 10. SYMBOL                                    [INTERMEDIATE]
// ============================================================
// INTERVIEW: "What are Symbols used for?"

let s1 = Symbol();
let s2 = Symbol('description');
console.log(Symbol() == Symbol());  // false -- every symbol is unique

// Use case: private-ish object keys
const SECRET = Symbol('secret');
const myObj = { [SECRET]: 42, public: 'visible' };
console.log(Object.keys(myObj));          // ["public"] -- symbol keys hidden
console.log(myObj[SECRET]);               // 42

// Well-known symbols: Symbol.iterator, Symbol.toPrimitive, Symbol.hasInstance


// ============================================================
// 11. ++ PREFIX vs POSTFIX                            [BASIC]
// ============================================================
// https://stackoverflow.com/questions/3469885/somevariable-vs-somevariable-in-javascript

let a1 = 5;
console.log(a1++); // 5  (returns THEN increments)
console.log(a1);   // 6
console.log(++a1); // 7  (increments THEN returns)

// INTERVIEW GOTCHA:
let v = 1;
console.log(v++ + ++v); // 1 + 3 = 4  (v++ returns 1, v becomes 2, ++v makes 3)


// ============================================================
// 12. OPTIONAL CHAINING (?.)                    [INTERMEDIATE]
// ============================================================
// Safely access deeply nested properties without null checks.

let person = {
  name: "shubham",
  address: { state: "karnataka" }
};

console.log(person.name);           // "shubham"
console.log(person.address.country);// undefined (property missing, no error)
// console.log(person.state.street); // TypeError: Cannot read property 'street' of undefined
console.log(person.state?.street);  // undefined (safe)
console.log(undefined?.address);    // undefined (safe)
console.log(null?.address);         // undefined (safe)

// Also works with methods and bracket notation:
const arr = null;
console.log(arr?.[0]);              // undefined
console.log(arr?.length);           // undefined

const obj1 = { greet: null };
console.log(obj1.greet?.());        // undefined (greet is not a function, no error)


// ============================================================
// 13. NULLISH COALESCING (??)                   [INTERMEDIATE]
// ============================================================
// Returns right side ONLY when left is null or undefined (not 0 or "").

console.log("shubham" ?? "shubham123"); // "shubham"
console.log(undefined ?? "shubham");    // "shubham"
console.log(null ?? "vinayak");         // "vinayak"
console.log("" ?? "emptystring");       // ""    (empty string is NOT nullish)
console.log(0 ?? 42);                   // 0     (0 is NOT nullish)
console.log(false ?? true);            // false  (false is NOT nullish)

// COMPARISON: ?? vs || vs &&
//  +------------------+------+------+------+
//  |    Expression    |  ??  |  ||  |  &&  |
//  +------------------+------+------+------+
//  | null OP "b"      | "b"  | "b"  | null |
//  | undefined OP "b" | "b"  | "b"  | undef|
//  | 0 OP "b"         |  0   | "b"  |  0   |  <-- key difference
//  | "" OP "b"        |  ""  | "b"  |  ""  |  <-- key difference
//  | false OP "b"     | false| "b"  | false|  <-- key difference
//  | "a" OP "b"       | "a"  | "a"  | "b"  |
//  +------------------+------+------+------+


// ============================================================
// 14. SHORT-CIRCUIT EVALUATION                  [INTERMEDIATE]
// ============================================================
// INTERVIEW: "Explain short-circuit evaluation."
//
// || returns the first truthy value, or the last value
// && returns the first falsy value, or the last value

// Common patterns:
const port = undefined;
const defaultPort = port || 3000;           // 3000 (fallback for falsy)
const safePort = port ?? 8080;              // 8080 (fallback for nullish only)

// Guard pattern (&&):
const user = { isAdmin: true, showPanel: () => "Admin Panel" };
const panel = user.isAdmin && user.showPanel(); // "Admin Panel"

// Default assignment:
function greet(name) {
  name = name || "Guest";    // old pattern (treats "" and 0 as missing)
  // name ??= "Guest";       // modern pattern (only null/undefined)
  return `Hello, ${name}!`;
}

// Logical assignment operators (ES2021) [ADVANCED]:
let aa = null;
aa ??= 10;   // aa is now 10  (assigns only if null/undefined)
let bb = 0;
bb ||= 10;   // bb is now 10  (assigns if falsy)
bb &&= 20;   // bb is now 20  (assigns if truthy)


// ============================================================
// 15. BITWISE OPERATORS                         [INTERMEDIATE]
// ============================================================
// INTERVIEW: Rarely asked directly, but useful for flags and tricks.
//
//  +--------+-----------------------------+-----------+
//  |  OP    |        DESCRIPTION          |  EXAMPLE  |
//  +--------+-----------------------------+-----------+
//  |  &     | AND                         | 5 & 3 = 1 |
//  |  |     | OR                          | 5 | 3 = 7 |
//  |  ^     | XOR                         | 5 ^ 3 = 6 |
//  |  ~     | NOT (bitwise complement)    | ~5 = -6   |
//  |  <<    | Left shift                  | 5 << 1 =10|
//  |  >>    | Right shift (sign-preserv)  | -8 >> 2=-2|
//  |  >>>   | Right shift (zero-fill)     | -1>>>0=4294967295|
//  +--------+-----------------------------+-----------+

// Practical trick: double bitwise NOT for truncation (faster than Math.floor)
console.log(~~3.7);     // 3
console.log(~~(-3.7));  // -3 (differs from Math.floor which gives -4)

// Check if number is integer:
console.log((5.2 | 0) === 5.2);  // false (not integer)
console.log((5.0 | 0) === 5.0);  // true  (is integer)

// Swap without temp variable:
let sw1 = 10, sw2 = 20;
sw1 ^= sw2; sw2 ^= sw1; sw1 ^= sw2;
console.log(sw1, sw2); // 20, 10


// ============================================================
// 16. LABEL STATEMENTS                            [ADVANCED]
// ============================================================
// INTERVIEW: Rarely asked, but shows deep knowledge.

// Labels let you break/continue outer loops from inner loops.
outerLoop: for (let i = 0; i < 3; i++) {
  for (let j = 0; j < 3; j++) {
    if (i === 1 && j === 1) break outerLoop; // breaks BOTH loops
    console.log(`i=${i}, j=${j}`);
  }
}
// Output: i=0,j=0  i=0,j=1  i=0,j=2  i=1,j=0

// Continue with label:
outer: for (let i = 0; i < 3; i++) {
  for (let j = 0; j < 3; j++) {
    if (j === 1) continue outer; // skips to next i
    console.log(`i=${i}, j=${j}`);
  }
}
// Output: i=0,j=0  i=1,j=0  i=2,j=0

// Label with block (for scoping):
blockLabel: {
  console.log("before break");
  break blockLabel;
  console.log("this never runs");
}


// ============================================================
// 17. COMMA OPERATOR                              [ADVANCED]
// ============================================================
// INTERVIEW: "What does the comma operator do?"
// Evaluates left-to-right, returns the LAST expression's value.

const result = (1 + 2, 3 + 4, 5 + 6);
console.log(result); // 11 (only last expression returned)

// Common use in for loops:
for (let i = 0, j = 10; i < j; i++, j--) {
  console.log(i, j); // 0,10  1,9  2,8  3,7  4,6
}

// Compact one-liners (use sparingly for readability):
const inc = (x) => (x++, x * 2);
console.log(inc(3)); // 8  (x becomes 4, then 4*2)


// ============================================================
// 18. var vs let vs const                             [BASIC]
// ============================================================
// INTERVIEW: Top-3 question. See also Hoisting.js and TDZ.js.
//
//  +-------------+--------+-----+-------+----------+---------+
//  |             |  var   | let | const | function | class   |
//  +-------------+--------+-----+-------+----------+---------+
//  | Scope       |function|block| block | function | block   |
//  | Hoisted?    |  yes   | yes*| yes*  |   yes    | yes*    |
//  | TDZ?        |  no    | yes | yes   |   no     | yes     |
//  | Redeclare?  |  yes   | no  |  no   |   yes    | no      |
//  | Reassign?   |  yes   | yes |  no   |   yes    | yes     |
//  | window prop?|  yes   | no  |  no   |   yes    | no      |
//  +-------------+--------+-----+-------+----------+---------+
//  * hoisted but NOT initialized (Temporal Dead Zone)


// ============================================================
// GOTCHAS & INTERVIEW TRAPS
// ============================================================

// GOTCHA 1: typeof null
console.log(typeof null === "object"); // true (historical bug)

// GOTCHA 2: Array check
console.log(typeof [] === "object"); // true - useless, use Array.isArray()

// GOTCHA 3: Floating point
console.log(0.1 + 0.2 === 0.3);       // false!
console.log(0.1 + 0.2);               // 0.30000000000000004
console.log(Math.abs(0.1 + 0.2 - 0.3) < Number.EPSILON); // true (proper way)

// GOTCHA 4: String comparison
console.log("10" > "9");  // false! (lexicographic: "1" < "9")
console.log(10 > 9);      // true

// GOTCHA 5: undefined arithmetic
console.log(undefined + 1);   // NaN
console.log(null + 1);        // 1
console.log("" + 1);          // "1"

// GOTCHA 6: == coercion surprises
console.log(false == "0");    // true  (both coerce to 0)
console.log(false == []);     // true  ([] -> "" -> 0, false -> 0)
console.log("" == []);        // true  ([] -> "")
console.log(0 == []);         // true  ([] -> "" -> 0)
console.log([] == ![]);       // true  (![] is false, then false==[] is true)

// GOTCHA 7: Number edge cases
console.log(Number(""));       // 0
console.log(Number(" "));      // 0
console.log(Number(null));     // 0
console.log(Number(undefined));// NaN
console.log(Number(true));     // 1
console.log(Number(false));    // 0
console.log(Number([]));       // 0
console.log(Number([1]));      // 1
console.log(Number([1,2]));    // NaN

// GOTCHA 8: parseInt quirks
console.log(parseInt("08"));     // 8
console.log(parseInt("0xF"));    // 15 (hex)
console.log(parseInt("hello"));  // NaN
console.log(parseInt("123abc")); // 123 (parses until non-digit)
console.log(parseInt(0.0000005));// 5 (converts to "5e-7", parses "5")
