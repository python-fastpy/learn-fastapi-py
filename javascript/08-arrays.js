// ============================================================
// JAVASCRIPT ARRAYS — ULTIMATE QUICK-REFERENCE
// ============================================================
//
// ┌──────────────────────────────────────────────────────────┐
// │  ARRAY METHOD CHEAT SHEET                               │
// │                                                         │
// │  MUTATING (modify original)  │ NON-MUTATING (new copy)  │
// │  ─────────────────────────── │ ──────────────────────── │
// │  push / pop                  │ concat                   │
// │  shift / unshift             │ slice                    │
// │  splice                     │ toSpliced  (ES2023)      │
// │  sort                       │ toSorted   (ES2023)      │
// │  reverse                    │ toReversed (ES2023)      │
// │  fill                       │ with       (ES2023)      │
// │  copyWithin                 │ map / filter / reduce    │
// │                             │ flat / flatMap            │
// │                             │ Array.from / Array.of    │
// ├──────────────────────────────┴──────────────────────────┤
// │  SEARCH            │ ITERATE          │ TRANSFORM       │
// │  ────────────────  │ ───────────────  │ ──────────────  │
// │  indexOf           │ for...of         │ map             │
// │  lastIndexOf       │ forEach          │ flatMap         │
// │  find              │ for (classic)    │ reduce          │
// │  findIndex         │ entries/keys/    │ reduceRight     │
// │  findLast (ES2023) │   values         │ join            │
// │  findLastIndex     │                  │ toString        │
// │  includes          │                  │                 │
// │  some / every      │                  │                 │
// ├────────────────────┴──────────────────┴─────────────────┤
// │  STATIC METHODS                                         │
// │  Array.isArray()   Array.from()   Array.of()            │
// │  Array.fromAsync() (ES2024)                             │
// │  Object.groupBy()  Map.groupBy()  (ES2024)              │
// └────────────────────────────────────────────────────────-─┘
//
// MEMORY LAYOUT (conceptual):
//
//   const arr = ['a','b','c'];
//
//   arr ──► ┌───────────┬───────────┬───────────┐
//           │ index 0   │ index 1   │ index 2   │
//           │   'a'     │   'b'     │   'c'     │
//           └───────────┴───────────┴───────────┘
//           length = 3
//
//   Sparse:  [,'a',,'c']
//   arr ──► ┌───────────┬───────────┬───────────┬───────────┐
//           │ <empty>   │   'a'     │ <empty>   │   'c'     │
//           └───────────┴───────────┴───────────┴───────────┘
//           length = 4   (holes have no value, not even undefined)


// ============================================================
// 1. CREATION — BASIC                              [BASIC]
// ============================================================

// --- Array literal (dense) ---
let items1 = ['first', 'second', 'third']; // dense, contiguous indices

// --- Sparse array (holes) ---
let items = [, 'first', 'second', 'third'];
items;        // => [<1 empty slot>, 'first', 'second', 'third']
items[0];     // => undefined  (but slot is EMPTY, not actually undefined)
items[1];     // => 'first'
items.length; // => 4

// INTERVIEW: "What's the difference between a hole and `undefined`?"
// Empty slot: `0 in items` => false   (no element at index 0)
// Explicit:   items[0] = undefined; `0 in items` => true

// --- Trailing comma ---
// ['a', 'b', 'c',] => length 3 (trailing comma is ignored)

// --- Spread operator ---
let source = ['second', 'third'];
let merged = ['first', ...source]; // => ['first', 'second', 'third']

let odds = [1, 3, 5], evens = [4, 6];
let combined = [...odds, 0, ...evens, -1]; // => [1, 3, 5, 0, 4, 6, -1]

// Spread works on any iterable, including generators:
function* elements(element, length) {
  let index = 0;
  while (length > index++) yield element;
}
[...elements(0, 5)];    // => [0, 0, 0, 0, 0]
[...elements('hi', 2)]; // => ['hi', 'hi']


// ============================================================
// 2. ARRAY CONSTRUCTOR & STATIC METHODS            [BASIC]
// ============================================================

// --- new Array() ---
let arrayConstr = new Array(1, 5);  // => [1, 5]  (multiple args = elements)
typeof arrayConstr;                 // => 'object'
arrayConstr.constructor === Array;  // => true

// GOTCHA: single numeric arg creates sparse array
// new Array(3) => [<3 empty slots>], length 3, no elements!
// new Array('3') => ['3']  (string arg = element)

// --- Array.from() --- // [BASIC]
// Array.from(arrayLike)
// Array.from(arrayLike, mapFn)
// Array.from(arrayLike, mapFn, thisArg)
let zeros = new Array(5).fill(0);                        // => [0, 0, 0, 0, 0]
let zeros1 = Array.from(new Array(5), () => 0);          // => [0, 0, 0, 0, 0]
let items2 = Array.from(new Array(5), (_, i) => i + 1);  // => [1, 2, 3, 4, 5]

// Array.from accepts any iterable:
function* generate(max) {
  let count = 0;
  while (max > count++) yield count;
}
let items3 = Array.from(generate(5)); // => [1, 2, 3, 4, 5]
let itemsSpread = [...generate(5)];   // => [1, 2, 3, 4, 5]

// --- Array.of() ---  avoids the single-number trap of new Array()
Array.of(3);       // => [3]        (one element)
Array.of(1, 2, 3); // => [1, 2, 3]

// --- Array.fromAsync() (ES2024) --- // [ADVANCED]
// Builds an array from an async iterable or iterable of promises
// const arr = await Array.fromAsync(asyncIterable);
// const arr = await Array.fromAsync([fetch(url1), fetch(url2)]);


// ============================================================
// 3. SPARSE vs DENSE ARRAYS                        [INTERMEDIATE]
// ============================================================

// Dense: every index from 0..length-1 has a value
const names = ['Batman', 'Joker', 'Bane'];
console.log(names[0]); // 'Batman'
console.log(names.length); // 3

// Sparse: has "holes" — indices with no value
// Ways to create sparse arrays:
//   1. Array literal:   ['Batman', , 'Bane']
//   2. Constructor:     new Array(5)
//   3. delete operator: delete names[1]
//   4. Increase length: names.length = 5

const sparse = ['Batman', , 'Bane'];
console.log(0 in sparse); // true  (has element)
console.log(1 in sparse); // false (hole!)

// GOTCHA: forEach, map, filter SKIP holes in sparse arrays
const names3 = ['Batman', , 'Bane'];
names3.forEach(name => console.log(name));
// logs 'Batman', 'Bane' — skips the hole entirely


// ============================================================
// 4. ARRAY-LIKE OBJECTS & CONVERSION               [INTERMEDIATE]
// ============================================================
//
// ┌─────────────────────────────────────────────────────────┐
// │  Array-like: has .length + numeric indices, but NOT     │
// │  an Array (no push/map/filter/etc.)                     │
// │                                                         │
// │  Examples: arguments, NodeList, HTMLCollection, strings  │
// │                                                         │
// │  Convert to real array:                                 │
// │    Array.from(nodeList)                                 │
// │    [...nodeList]          (if iterable)                  │
// │    Array.prototype.slice.call(arguments)  (legacy)      │
// └─────────────────────────────────────────────────────────┘

// function example() {
//   const args = Array.from(arguments); // convert arguments to real array
//   return args.map(x => x * 2);
// }
// example(1, 2, 3); // => [2, 4, 6]

// NodeList (DOM):
// const divs = document.querySelectorAll('div');  // NodeList, not Array
// const divArr = [...divs];                       // now a real Array


// ============================================================
// 5. MERGING ARRAYS                                [BASIC]
// ============================================================

const heroes = ['Batman', 'Superman'];
const villains = ['Joker', 'Bane'];

// Spread (non-mutating)
const all = [...heroes, ...villains]; // => ['Batman', 'Superman', 'Joker', 'Bane']

// concat (non-mutating)
const all2 = heroes.concat(villains); // => ['Batman', 'Superman', 'Joker', 'Bane']

// push (mutating — modifies heroes in place)
// heroes.push('Wonder Woman');
// heroes.push(...villains);  // push multiple


// ============================================================
// 6. DETECTING ARRAYS                              [BASIC]
// ============================================================

// INTERVIEW: "How do you check if something is an array?"
const array = [1, 2, 3];
const object = { message: 'Hello!' };

// Best: Array.isArray()  — works across iframes/realms
Array.isArray(array);  // => true
Array.isArray(object); // => false
Array.isArray(null);   // => false

// Also works: instanceof (fails across realms)
array instanceof Array; // => true

// Legacy: Object.prototype.toString
({}).toString.call(array);  // => '[object Array]'
({}).toString.call(object); // => '[object Object]'


// ============================================================
// 7. SEARCHING & CHECKING                          [BASIC]
// ============================================================

// --- includes --- (ES2016, returns boolean)
const greetings = ['hi', 'hello'];
greetings.includes('hi');  // => true
greetings.includes('hey'); // => false

// With fromIndex:
const letters = ['a', 'b', 'c', 'd'];
letters.includes('c', 1); // => true
letters.includes('a', 1); // => false  (starts searching at index 1)

// GOTCHA: includes uses SameValueZero — finds NaN!
[NaN].includes(NaN); // => true
[NaN].indexOf(NaN);  // => -1  (indexOf uses ===, NaN !== NaN)

// --- indexOf / lastIndexOf ---
const names4 = ['Batman', 'Catwoman', 'Joker', 'Bane'];
names4.indexOf('Joker');     // => 2
names4.lastIndexOf('Joker'); // => 2

// --- find / findIndex --- (returns first match or undefined/-1)
const number3 = [1, 2, 3, 4, 5];
number3.find(v => v % 2 === 0);      // => 2
number3.findIndex(v => v % 2 === 0); // => 1

// --- findLast / findLastIndex (ES2023) --- // [INTERMEDIATE]
// Searches from the END of the array
number3.findLast(v => v % 2 === 0);      // => 4
number3.findLastIndex(v => v % 2 === 0); // => 3

// --- Searching for objects (reference vs value equality) ---
const objArr = [{ message: 'hi' }, { message: 'hello' }];
objArr.includes({ message: 'hi' }); // => false! (different reference)
objArr.includes(objArr[0]);         // => true   (same reference)

// Use find for deep matching:
objArr.find(o => o.message === 'hi'); // => { message: 'hi' }

// Shallow equality helper:
function shallowEqual(obj1, obj2) {
  const keys1 = Object.keys(obj1);
  const keys2 = Object.keys(obj2);
  if (keys1.length !== keys2.length) return false;
  return keys1.every(key => obj1[key] === obj2[key]);
}
shallowEqual({ message: 'hi' }, { message: 'hi' }); // => true

// --- some / every ---
// some: at least one passes     every: all must pass
const nums = [1, 2, 3, 4, 5];
nums.some(n => n > 4);  // => true
nums.every(n => n > 0); // => true
nums.every(n => n > 3); // => false

// --- at() (ES2022) --- // [BASIC]
// INTERVIEW: "How do you get the last element of an array?"
const colors = ['red', 'green', 'blue'];
colors.at(0);  // => 'red'
colors.at(-1); // => 'blue'   (negative index counts from end)
colors.at(-2); // => 'green'
// Before at():  colors[colors.length - 1]


// ============================================================
// 8. ITERATION                                     [BASIC]
// ============================================================
//
// ┌────────────────────────────────────────────────────────────────┐
// │  for...of  vs  for...in  vs  forEach                          │
// │  ──────────────────────────────────────────────────────────── │
// │  for...of   │ Iterates VALUES  │ Works on iterables           │
// │             │ Can break/return │ Recommended for arrays       │
// │  ──────────────────────────────────────────────────────────── │
// │  for...in   │ Iterates KEYS    │ Designed for objects          │
// │             │ Includes proto   │ AVOID on arrays              │
// │  ──────────────────────────────────────────────────────────── │
// │  forEach    │ Callback-based   │ Cannot break/return          │
// │             │ Skips holes      │ No await support             │
// └────────────────────────────────────────────────────────────────┘

const iterColors = ['blue', 'green', 'white'];

// for...of — recommended
for (const color of iterColors) {
  console.log(color); // 'blue', 'green', 'white'
}

// Classic for loop — when you need the index
for (let i = 0; i < iterColors.length; i++) {
  console.log(i, iterColors[i]);
}

// forEach — functional style, cannot break
iterColors.forEach((value, index) => {
  console.log(value, index);
});

// entries / keys / values
const arrEntries = ['a', 'b', 'c'];
const iter = arrEntries.entries();
console.log(iter.next().value); // [0, 'a']
console.log(iter.next().value); // [1, 'b']

for (const [index, val] of arrEntries.entries()) {
  console.log(index, val);
}


// ============================================================
// 9. SORTING                                       [INTERMEDIATE]
// ============================================================

// INTERVIEW: "How does Array.sort() work? What's the default behavior?"

// Default: converts to strings, sorts alphabetically (lexicographic)
// const words = ['joker', 'batman', 'catwoman'];
// words.sort(); // => ['batman', 'catwoman', 'joker']

// GOTCHA: numeric sort is WRONG without comparator
// [10, 5, 11].sort(); // => [10, 11, 5]  (string comparison!)

// --- Comparator function ---
// If comparator(a, b) returns:
//   negative: a before b
//   positive: b before a
//   zero:     keep order

const numbers = [10, 5, 11];

// Ascending
numbers.sort((a, b) => a - b); // => [5, 10, 11]

// Descending
// numbers.sort((a, b) => b - a); // => [11, 10, 5]

// Sort objects by property:
const characters = [
  { name: 'Luke Skywalker', height: '172', mass: '77', eye_color: 'blue', gender: 'male' },
  { name: 'Darth Vader', height: '202', mass: '136', eye_color: 'yellow', gender: 'male' },
  { name: 'Leia Organa', height: '150', mass: '49', eye_color: 'brown', gender: 'female' },
  { name: 'Anakin Skywalker', height: '188', mass: '84', eye_color: 'blue', gender: 'male' },
];

// By numeric property:
// characters.sort((a, b) => parseInt(a.mass) - parseInt(b.mass));

// By string property (use localeCompare for proper Unicode sort):
// characters.sort((a, b) => a.name.localeCompare(b.name));

// String arrays:
let a = ["aab", "aac", "aad", "aaa"];
console.log(a.sort((a, b) => a < b ? 1 : -1)); // descending

let b = ["18", "20", "1", "2", "3", "4", "-1"];
console.log(b.sort((a, b) => parseInt(a) - parseInt(b))); // numeric ascending

// --- toSorted() (ES2023) — non-mutating version --- // [INTERMEDIATE]
const orig = [3, 1, 2];
const sorted = orig.toSorted((a, b) => a - b); // => [1, 2, 3]
console.log(orig); // => [3, 1, 2]  (unchanged!)


// ============================================================
// 10. IMMUTABLE METHODS (ES2023)                   [INTERMEDIATE]
// ============================================================
//
// INTERVIEW: "What are the new immutable array methods in ES2023?"
//
// ┌──────────────┬─────────────────┬──────────────────────────────┐
// │ Mutating     │ Non-mutating    │ Description                  │
// │              │ (ES2023)        │                              │
// ├──────────────┼─────────────────┼──────────────────────────────┤
// │ sort()       │ toSorted()      │ Sort without mutating        │
// │ reverse()    │ toReversed()    │ Reverse without mutating     │
// │ splice()     │ toSpliced()     │ Splice without mutating      │
// │ arr[i] = v   │ with(i, v)      │ Set element without mutating │
// └──────────────┴─────────────────┴──────────────────────────────┘

const base = [1, 2, 3, 4, 5];

// toReversed()
const rev = base.toReversed(); // => [5, 4, 3, 2, 1]
console.log(base);             // => [1, 2, 3, 4, 5] (unchanged)

// toSpliced(start, deleteCount, ...items)
const spliced = base.toSpliced(1, 2, 'a', 'b'); // => [1, 'a', 'b', 4, 5]

// with(index, value)  — returns copy with one element replaced
const replaced = base.with(2, 99); // => [1, 2, 99, 4, 5]
// Supports negative index:
const replaced2 = base.with(-1, 99); // => [1, 2, 3, 4, 99]


// ============================================================
// 11. SPLICE vs SLICE                              [BASIC]
// ============================================================
//
// INTERVIEW: "What's the difference between splice and slice?"
//
// ┌──────────────────────────────────────────────────────┐
// │  splice(start, deleteCount, ...items)  → MUTATES     │
// │  Changes contents by removing/replacing/adding       │
// │  Returns: array of REMOVED elements                  │
// │                                                      │
// │  slice(start, end)  → NON-MUTATING                   │
// │  Returns shallow copy from start to end (exclusive)  │
// │  Returns: NEW array                                  │
// └──────────────────────────────────────────────────────┘

// splice examples:
// const arr = [1, 2, 3, 4, 5];
// arr.splice(1, 2);        // removes [2, 3], arr is now [1, 4, 5]
// arr.splice(1, 0, 'a');   // inserts 'a' at index 1, arr is [1, 'a', 4, 5]

// slice examples:
// const arr = [1, 2, 3, 4, 5];
// arr.slice(1, 3);  // => [2, 3]   (arr unchanged)
// arr.slice(-2);    // => [4, 5]   (last 2 elements)


// ============================================================
// 12. MAP, FILTER, REDUCE                          [INTERMEDIATE]
// ============================================================

const arr = [5, 1, 3, 2, 6];

// --- map: transform each element ---
const double = arr.map(item => item * 2);   // => [10, 2, 6, 4, 12]
const triple = arr.map(item => item * 3);   // => [15, 3, 9, 6, 18]
const binary = arr.map(item => item.toString(2)); // => ['101','1','11','10','110']

// --- filter: keep elements that pass the test ---
const oddNums = arr.filter(item => item % 2); // => [5, 1, 3]
console.log(oddNums);

// --- reduce: accumulate into a single value ---
// reduce(callbackFn, initialValue)
//
// ┌──────────────────────────────────────────────────┐
// │  Step │ acc │ curr │ return                      │
// │  ──── │ ─── │ ──── │ ──────                      │
// │  1    │  0  │  5   │  5                          │
// │  2    │  5  │  1   │  6                          │
// │  3    │  6  │  3   │  9                          │
// │  4    │  9  │  2   │  11                         │
// │  5    │ 11  │  6   │  17                         │
// └──────────────────────────────────────────────────┘

const sum = arr.reduce((acc, curr) => acc + curr, 0);
console.log(sum); // 17

const max = arr.reduce((acc, curr) => curr > acc ? curr : acc, 0);
console.log(max); // 6

// INTERVIEW: "Use reduce to group objects by a property"
const users = [
  { firstName: "akshay", lastName: "saini", age: 26 },
  { firstName: "donald", lastName: "trump", age: 75 },
  { firstName: "elon", lastName: "musk", age: 50 },
  { firstName: "deepika", lastName: "padukone", age: 26 },
];

const fullNames = users.map(x => x.firstName + " " + x.lastName);
console.log(fullNames); // ["akshay saini", "donald trump", ...]

// Group by age:  { 26: 2, 75: 1, 50: 1 }
const ageCount = users.reduce((acc, curr) => {
  acc[curr.age] = (acc[curr.age] || 0) + 1;
  return acc;
}, {});

// Chaining: filter then map
let youngNames = users
  .filter(user => user.age < 30)
  .map(user => user.firstName);
// => ["akshay", "deepika"]


// ============================================================
// 13. flat / flatMap                               [INTERMEDIATE]
// ============================================================

const nested1 = [0, 1, 2, [3, 4]];
console.log(nested1.flat()); // => [0, 1, 2, 3, 4]

const nested2 = [0, 1, [2, [3, [4, 5]]]];
console.log(nested2.flat());         // => [0, 1, 2, [3, [4, 5]]]  depth 1
console.log(nested2.flat(2));        // => [0, 1, 2, 3, [4, 5]]    depth 2
console.log(nested2.flat(Infinity)); // => [0, 1, 2, 3, 4, 5]      fully flat

// flatMap = map + flat(1) in one pass
const sentences = ["hello world", "foo bar"];
sentences.flatMap(s => s.split(' ')); // => ['hello', 'world', 'foo', 'bar']


// ============================================================
// 14. join / reverse                               [BASIC]
// ============================================================

const elems = ['Fire', 'Air', 'Water'];
elems.join();    // => "Fire,Air,Water"
elems.join('');  // => "FireAirWater"
elems.join('-'); // => "Fire-Air-Water"

// reverse() — MUTATES the original
// const rev = [1, 2, 3].reverse(); // => [3, 2, 1]
// Use toReversed() for non-mutating (see section 10)


// ============================================================
// 15. Object.groupBy / Map.groupBy (ES2024)        [ADVANCED]
// ============================================================

// INTERVIEW: "How do you group array elements by a key in modern JS?"

// Object.groupBy(iterable, callbackFn)
// Returns a null-prototype object with groups as keys

// const inventory = [
//   { name: "asparagus", type: "vegetables", qty: 5 },
//   { name: "bananas",   type: "fruit",      qty: 0 },
//   { name: "cherries",  type: "fruit",      qty: 5 },
//   { name: "goat",      type: "meat",       qty: 23 },
// ];
// const grouped = Object.groupBy(inventory, item => item.type);
// grouped.fruit      => [{name:"bananas",...}, {name:"cherries",...}]
// grouped.vegetables => [{name:"asparagus",...}]

// Map.groupBy — same but returns a Map (useful for non-string keys)
// const grouped = Map.groupBy(inventory, item => item.qty > 0 ? 'ok' : 'restock');


// ============================================================
// 16. TYPED ARRAYS                                 [ADVANCED]
// ============================================================
//
// ┌──────────────────────────────────────────────────────────┐
// │  Typed Arrays provide fixed-type, fixed-size arrays     │
// │  backed by an ArrayBuffer. Used for binary data, WebGL, │
// │  Web Audio, file I/O, etc.                              │
// │                                                         │
// │  Type            │ Bytes │ Range                        │
// │  ─────────────── │ ───── │ ──────────────────────────── │
// │  Int8Array       │   1   │ -128 to 127                  │
// │  Uint8Array      │   1   │ 0 to 255                     │
// │  Int16Array      │   2   │ -32768 to 32767              │
// │  Uint16Array     │   2   │ 0 to 65535                   │
// │  Int32Array      │   4   │ -2^31 to 2^31-1              │
// │  Float32Array    │   4   │ IEEE 754 float               │
// │  Float64Array    │   8   │ IEEE 754 double              │
// │  BigInt64Array   │   8   │ -2^63 to 2^63-1              │
// │  BigUint64Array  │   8   │ 0 to 2^64-1                  │
// └──────────────────────────────────────────────────────────┘
//
// const buf = new ArrayBuffer(16);        // 16 bytes of raw memory
// const view = new Int32Array(buf);       // 4 x 32-bit integers
// view[0] = 42;
// view.length; // => 4
//
// Typed arrays have most array methods (map, filter, slice, etc.)
// but always return the SAME typed array type.


// ============================================================
// GOTCHAS                                          [ALL LEVELS]
// ============================================================
//
// 1. typeof [] === 'object'   — use Array.isArray() instead
//
// 2. Array(5) vs Array.of(5):
//      new Array(5)  => [<5 empty>]   (sparse!)
//      Array.of(5)   => [5]           (one element)
//
// 3. sort() without comparator converts to strings:
//      [10, 9, 80].sort() => [10, 80, 9]  (string sort!)
//
// 4. forEach cannot be broken — use for...of + break instead
//
// 5. delete arr[i] creates a HOLE, doesn't shift elements:
//      const a = [1,2,3]; delete a[1]; // [1, <empty>, 3]
//      Use splice to truly remove: a.splice(1, 1)
//
// 6. arr.length is writable — setting it smaller truncates!
//      const a = [1,2,3,4,5]; a.length = 2; // [1, 2]
//
// 7. Spread vs Array.from for array-likes:
//      [...nodeList]       — only works if iterable
//      Array.from(nodeList) — works on any array-like
//
// 8. NaN searching:
//      [NaN].indexOf(NaN)  => -1     (uses ===)
//      [NaN].includes(NaN) => true   (uses SameValueZero)
//
// 9. map() preserves holes, but callback is NOT called for them:
//      [1,,3].map(x => x*2) => [2, <empty>, 6]
//
// 10. Mutation surprise — sort/reverse return the SAME array:
//       const a = [3,1,2]; const b = a.sort();
//       a === b // true! Both point to the sorted array
