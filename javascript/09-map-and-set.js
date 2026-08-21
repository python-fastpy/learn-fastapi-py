// ============================================================
// JAVASCRIPT MAP & SET — ULTIMATE QUICK-REFERENCE
// ============================================================
//
// TABLE OF CONTENTS
// -----------------
// PART 1: MAP
//   1.  Why Map? (Problems with Object-as-map)       [BASIC]
//   2.  Creating & Using Map                         [BASIC]
//   3.  Map Methods                                  [BASIC]
//   4.  Map Iteration                                [BASIC]
//   5.  Map vs Object Performance                    [INTERMEDIATE]
//   6.  JSON Serialization                           [INTERMEDIATE]
//   7.  Converting Between Map and Object            [INTERMEDIATE]
//   8.  Map Gotchas                                  [ALL LEVELS]
//
// PART 2: SET
//   9.  Creating Sets                                [BASIC]
//   10. Set Methods                                  [BASIC]
//   11. Set Iteration                                [BASIC]
//   12. Set Operations (ES2025)                      [ADVANCED]
//   13. Common Set Patterns                          [INTERMEDIATE]
//   14. Set vs Array Dedup Performance               [INTERMEDIATE]
//   15. Set Gotchas                                  [ALL LEVELS]
//
// PART 3: WEAKMAP & WEAKSET
//   16. WeakMap                                      [INTERMEDIATE]
//   17. WeakSet                                      [INTERMEDIATE]
//   18. Weak Collection Gotchas                      [ALL LEVELS]
//
// PART 4: COMPARISON
//   19. Map vs Set vs WeakMap vs WeakSet             [REFERENCE]


// ************************************************************
//                      PART 1: MAP
// ************************************************************
//
// ┌──────────────────────────────────────────────────────────┐
// │  Map vs Object                                          │
// │  ─────────────────────────────────────────────────────── │
// │                 │ Object       │ Map                     │
// │  ───────────── │ ──────────── │ ──────────────────────── │
// │  Key types     │ String/Symbol│ ANY type                 │
// │  Key order     │ Complex*     │ Insertion order          │
// │  Size          │ Manual       │ .size                    │
// │  Iterable      │ No (keys())  │ Yes                      │
// │  Performance   │ Slower adds  │ Faster adds              │
// │  Serialization │ JSON native  │ Manual                   │
// │  Prototype     │ Has default  │ No prototype keys        │
// │                                                         │
// │  * Object key order: integer keys first (sorted),       │
// │    then strings (insertion order), then symbols          │
// └──────────────────────────────────────────────────────────┘
//
// INTERNAL STRUCTURE (conceptual):
//
//   Map: Hash table with linked list for insertion order
//
//   map.set('a', 1)  -->  bucket[hash('a')] --> {key:'a', val:1, next:->}
//   map.set('b', 2)  -->  bucket[hash('b')] --> {key:'b', val:2, next:->}
//   map.set('c', 3)  -->  bucket[hash('c')] --> {key:'c', val:3, next:null}
//
//   Iteration follows the insertion-order linked list,
//   NOT the hash bucket order.


// ============================================================
// 1. WHY MAP? (Problems with Object-as-map)        [BASIC]
// ============================================================

// Problem 1: Object coerces all keys to strings
var obj1 = {};
obj1[5] = "bar";
console.log(obj1["5"]); // "bar" — numeric 5 became string "5"

// Problem 2: Object keys lose identity
var obj2 = {};
var keyA = {}, keyB = {};
obj2[keyA] = "alpha";
console.log(obj2[keyB]); // "alpha" — both become "[object Object]"

// Problem 3: Falsy values are ambiguous
var obj3 = {};
obj3.foo = false;
if (obj3.foo) { /* never runs — is it missing or false? */ }
// With Map: map.has('foo') => true, map.get('foo') => false


// ============================================================
// 2. CREATING & USING MAP                          [BASIC]
// ============================================================

// Syntax: new Map([iterable])
let map4 = new Map();
map4.set(5, "shubham");
map4.set("5", "vinayak"); // different key from numeric 5!
console.log(map4.size);    // 2
console.log(map4.get(5));  // "shubham"
console.log(map4.get("5")); // "vinayak"

// Objects as keys — each reference is unique
let map5 = new Map();
let key2 = {}, key3 = {};
map5.set(key2, "shubham");
map5.set(key3, "vinayak");
console.log(map5.size); // 2 (two distinct object keys)

// Initialize from entries (array of [key, value] pairs)
const fromEntries = new Map([
  ['name', 'Alice'],
  ['age', 30],
  [42, 'the answer']
]);


// ============================================================
// 3. MAP METHODS                                   [BASIC]
// ============================================================

let map6 = new Map();

// --- set(key, value) — returns the Map (chainable) ---
map6.set(1, "one")
    .set(2, "two")
    .set(3, "three");

// Any type as key:
map6.set('4', "string four");
map6.set(4, "number four");     // different from '4'
map6.set(undefined, 20);
let objKey = { a: 0, b: 10 };
map6.set(objKey, 25);
let fnKey = function() {};
map6.set(fnKey, 26);
map6.set(null, 27);

// Duplicate key overwrites:
map6.set(1, "ONE"); // updates value for key 1

// --- has(key) ---
console.log(map6.has(null));  // true
console.log(map6.has(fnKey)); // true
console.log(map6.has('4'));   // true
console.log(map6.has(123));   // false

// --- get(key) ---
console.log(map6.get(fnKey));  // 26
console.log(map6.get(null));   // 27
console.log(map6.get(objKey)); // 25

// --- delete(key) — returns boolean ---
map6.delete(objKey); // true
map6.delete(null);   // true
console.log(map6.has(objKey)); // false
console.log(map6.has(null));   // false

// --- clear() — removes all entries ---
// map6.clear(); map6.size; // 0


// ============================================================
// 4. MAP ITERATION                                 [BASIC]
// ============================================================

// INTERVIEW: "Does Map guarantee insertion order?"
// YES. Map iterates in insertion order. This is spec-guaranteed.

// forEach(callback(value, key, map))
map6.forEach((value, key) => {
  console.log("forEach:", key, value);
});

// for...of (default iterator = entries)
for (let [key, value] of map6) {
  console.log("for-of:", key, value);
}

// .keys() / .values() / .entries()
for (let key of map6.keys()) {
  console.log("key:", key);
}
for (let value of map6.values()) {
  console.log("value:", value);
}
for (let [k, v] of map6.entries()) {
  console.log("entry:", k, v);
}

// Spread into array of entries
const entriesArr = [...map6]; // [[key1, val1], [key2, val2], ...]


// ============================================================
// 5. MAP vs OBJECT PERFORMANCE                     [INTERMEDIATE]
// ============================================================
//
// ┌────────────────────────────────────────────────────────────┐
// │  Operation        │ Object          │ Map                  │
// │  ──────────────── │ ─────────────── │ ──────────────────── │
// │  Insert           │ O(1) amortized  │ O(1) amortized       │
// │  Lookup           │ O(1)            │ O(1)                 │
// │  Delete           │ O(1) (but slow) │ O(1) (optimized)     │
// │  Frequent add/del │ Slower (deopt)  │ Designed for this    │
// │  Iteration        │ Slower          │ Faster               │
// │  Memory (many)    │ Higher overhead │ Lower overhead       │
// └────────────────────────────────────────────────────────────┘
//
// RULE OF THUMB:
//   - Fixed-shape data with string keys? Use Object.
//   - Dynamic key/value store, frequent adds/deletes? Use Map.
//   - Need non-string keys (DOM nodes, objects)? Use Map.


// ============================================================
// 6. JSON SERIALIZATION                            [INTERMEDIATE]
// ============================================================

// INTERVIEW: "How do you serialize/deserialize a Map to JSON?"

// Map is NOT directly JSON-serializable:
// JSON.stringify(new Map([['a', 1]])); // => '{}'  (empty!)

// Serialize: Map -> Array of entries -> JSON
const myMap = new Map([['a', 1], ['b', 2], [3, 'three']]);
const json = JSON.stringify([...myMap]);
// => '[["a",1],["b",2],[3,"three"]]'

// Deserialize: JSON -> Array of entries -> Map
const restored = new Map(JSON.parse(json));
console.log(restored.get('a')); // 1

// Alternative: Map -> Object (only works for string keys)
const objFromMap = Object.fromEntries(myMap); // { a: 1, b: 2, '3': 'three' }
const mapFromObj = new Map(Object.entries(objFromMap));


// ============================================================
// 7. CONVERTING BETWEEN MAP AND OBJECT             [INTERMEDIATE]
// ============================================================

// Object -> Map
const person = { name: 'Alice', age: 30 };
const personMap = new Map(Object.entries(person));

// Map -> Object (string keys only)
const backToObj = Object.fromEntries(personMap);

// GOTCHA: Object.fromEntries loses non-string keys
const mixed = new Map([[1, 'one'], ['two', 2]]);
const asObj = Object.fromEntries(mixed);
// asObj => { '1': 'one', 'two': 2 }  — numeric 1 became string '1'


// ============================================================
// 8. MAP GOTCHAS                                   [ALL LEVELS]
// ============================================================
//
// 1. Map uses SameValueZero for key comparison:
//      NaN === NaN is true inside Map (unlike ===)
//      const m = new Map(); m.set(NaN, 'x'); m.get(NaN); // 'x'
//
// 2. Object references as keys — identity matters:
//      map.set({}, 1); map.get({}); // undefined! (different object)
//      Store the reference: const k = {}; map.set(k, 1); map.get(k); // 1
//
// 3. Map.size is a property, not a method:
//      map.size   (correct)
//      map.size() (TypeError)
//
// 4. Don't use [] with Map:
//      map['key'] = 'val'  — sets a property on the Map object, NOT an entry
//      map.set('key', 'val') — correct
//
// 5. forEach callback order is (value, key) — opposite of set(key, value)
//
// 6. JSON.stringify on a Map returns '{}' — use [...map] first.


// ************************************************************
//                      PART 2: SET
// ************************************************************
//
// ┌──────────────────────────────────────────────────────────┐
// │  Set vs Array — WHEN TO USE WHICH                       │
// │  ─────────────────────────────────────────────────────── │
// │                 │ Array          │ Set                   │
// │  ───────────── │ ────────────── │ ───────────────────── │
// │  Duplicates    │ Allowed        │ Automatically removed │
// │  Order         │ Index-based    │ Insertion order       │
// │  Access by     │ Index O(1)     │ No index access       │
// │  has/includes  │ O(n) linear    │ O(1) hash lookup      │
// │  Add element   │ O(1) push      │ O(1) add              │
// │  Delete by val │ O(n) find+splc │ O(1) delete           │
// │  Iterate       │ for/forEach/of │ forEach/for...of      │
// │  Use case      │ Ordered list   │ Unique collection     │
// └──────────────────────────────────────────────────────────┘
//
// DEDUP PERFORMANCE COMPARISON:
//
//   Array filter:  O(n^2)  arr.filter((v,i,a) => a.indexOf(v) === i)
//   Set dedup:     O(n)    [...new Set(arr)]
//
//   For 100k items, Set is ~100x faster for dedup.


// ============================================================
// 9. CREATING SETS                                 [BASIC]
// ============================================================

// Syntax: new Set([iterable])
let set1 = new Set();
set1.add(25);
set1.add(50);
console.log(set1); // Set(2) { 25, 50 }

// From an array
let set2 = new Set([3, 4, 5, 6, 7, 8, 9]);
console.log(set2); // Set(7) { 3, 4, 5, 6, 7, 8, 9 }

// From a string (each character becomes an element)
let set3 = new Set("shubham");
console.log(set3); // Set(6) { 's', 'h', 'u', 'b', 'a', 'm' } — duplicates removed

// INTERVIEW: "Fastest way to deduplicate an array?"
const arr = [1, 2, 2, 3, 3, 3];
const unique = [...new Set(arr)]; // => [1, 2, 3]


// ============================================================
// 10. SET METHODS                                  [BASIC]
// ============================================================

let set = new Set();

// --- add(value) — returns the Set (chainable) ---
set.add(1).add(2).add(3).add(4);
set.add(4);   // ignored — duplicate
set.add('4'); // different from number 4
set.add('My name is Prashant Yadav');
set.add(undefined);
set.add({ a: 0, b: 1 });
set.add(null);
console.log(set.size); // 8

// --- has(value) — O(1) lookup ---
console.log(set.has(4));   // true
console.log(set.has(5));   // false

// GOTCHA: objects are compared by reference
set.has({ a: 0, b: 1 }); // false! (different reference)

// --- delete(value) — returns boolean ---
set.delete(null); // true
console.log(set.size); // 7

// --- clear() — removes all elements ---
// set.clear();
// console.log(set.size); // 0


// ============================================================
// 11. SET ITERATION                                [BASIC]
// ============================================================

let set4 = new Set([1, 2, 3, 4, 5]);

// forEach
set4.forEach(e => console.log(e));

// for...of
for (let item of set4) {
  console.log(item);
}

// keys() / values() / entries()
// INTERVIEW: "Why does Set have both keys() and values()?"
// They return the SAME iterator (for compatibility with Map interface).
// entries() returns [value, value] pairs.

for (let item of set4.keys()) console.log("key:", item);
for (let item of set4.values()) console.log("val:", item);
for (let [k, v] of set4.entries()) console.log("entry:", k, v);
// entry: 1 1
// entry: 2 2  (key and value are the same)

// Using the iterator protocol directly:
const iter = set4.values();
console.log(iter.next().value); // 1
console.log(iter.next().value); // 2

// Spread into array
const asArray = [...set4]; // [1, 2, 3, 4, 5]


// ============================================================
// 12. SET OPERATIONS (ES2025)                      [ADVANCED]
// ============================================================
//
// INTERVIEW: "What new Set methods were added in ES2025?"
//
// These methods return NEW Sets and do NOT mutate the originals.
//
// ┌─────────────────────┬────────────────────────────────────────┐
// │ Method              │ Description                            │
// ├─────────────────────┼────────────────────────────────────────┤
// │ union(other)        │ All elements from both sets            │
// │ intersection(other) │ Elements in BOTH sets                  │
// │ difference(other)   │ Elements in this but NOT in other      │
// │ symmetricDifference │ Elements in either but NOT both        │
// │ isSubsetOf(other)   │ true if all elements are in other      │
// │ isSupersetOf(other) │ true if other is a subset of this      │
// │ isDisjointFrom(otr) │ true if no elements in common          │
// └─────────────────────┴────────────────────────────────────────┘
//
//   Venn diagram for A = {1,2,3}, B = {2,3,4}:
//
//        A              B
//    ┌───────┐     ┌───────┐
//    │  {1}  │     │  {4}  │
//    │    ┌──┴─────┴──┐    │
//    │    │  {2, 3}   │    │
//    └────┴───────────┴────┘
//
//   A.union(B)               => {1, 2, 3, 4}
//   A.intersection(B)        => {2, 3}
//   A.difference(B)          => {1}
//   A.symmetricDifference(B) => {1, 4}

const setA = new Set([1, 2, 3]);
const setB = new Set([2, 3, 4]);

// These require ES2025+ runtime support:
// setA.union(setB);               // Set {1, 2, 3, 4}
// setA.intersection(setB);        // Set {2, 3}
// setA.difference(setB);          // Set {1}
// setA.symmetricDifference(setB); // Set {1, 4}
// setA.isSubsetOf(setB);          // false
// setA.isSupersetOf(setB);        // false
// setA.isDisjointFrom(setB);      // false

// Polyfill / legacy approach:
function union(a, b) { return new Set([...a, ...b]); }
function intersection(a, b) { return new Set([...a].filter(x => b.has(x))); }
function difference(a, b) { return new Set([...a].filter(x => !b.has(x))); }
function symmetricDiff(a, b) {
  return new Set([...[...a].filter(x => !b.has(x)), ...[...b].filter(x => !a.has(x))]);
}


// ============================================================
// 13. COMMON SET PATTERNS                          [INTERMEDIATE]
// ============================================================

// --- Remove duplicates from array ---
const duped = [1, 'a', 1, 'b', 'a', 3];
const deduped = [...new Set(duped)]; // [1, 'a', 'b', 3]

// --- Count unique values ---
const data = [1, 2, 2, 3, 3, 3];
new Set(data).size; // 3

// --- Check if two arrays have same elements ---
function sameElements(arr1, arr2) {
  const s1 = new Set(arr1), s2 = new Set(arr2);
  if (s1.size !== s2.size) return false;
  for (const v of s1) if (!s2.has(v)) return false;
  return true;
}

// --- Filter unique objects by property ---
const people = [
  { id: 1, name: 'Alice' },
  { id: 2, name: 'Bob' },
  { id: 1, name: 'Alice duplicate' },
];
const seen = new Set();
const uniquePeople = people.filter(p => {
  if (seen.has(p.id)) return false;
  seen.add(p.id);
  return true;
});


// ============================================================
// 14. SET vs ARRAY DEDUP PERFORMANCE               [INTERMEDIATE]
// ============================================================
//
// ┌───────────────┬──────────────┬───────────────────────────────┐
// │ Approach      │ Time         │ Code                          │
// ├───────────────┼──────────────┼───────────────────────────────┤
// │ Set (best)    │ O(n)         │ [...new Set(arr)]             │
// │ filter+indexOf│ O(n^2)       │ arr.filter((v,i)=>            │
// │               │              │   arr.indexOf(v)===i)         │
// │ reduce+incl   │ O(n^2)       │ arr.reduce((a,v)=>           │
// │               │              │   a.includes(v)?a:[...a,v],[])│
// │ Object keys   │ O(n)         │ Object.keys(arr.reduce(...))  │
// │               │              │   (only works for primitives) │
// └───────────────┴──────────────┴───────────────────────────────┘


// ============================================================
// 15. SET GOTCHAS                                  [ALL LEVELS]
// ============================================================
//
// 1. Set uses SameValueZero for equality:
//      NaN is equal to NaN inside a Set (unlike ===)
//      new Set([NaN, NaN]).size; // 1
//
// 2. Objects are compared by REFERENCE, not value:
//      new Set([{a:1}, {a:1}]).size; // 2 (different references!)
//
// 3. Set has no index access:
//      set[0]       // undefined (sets property, not element)
//      [...set][0]  // works, but defeats the purpose
//
// 4. .add() is NOT .push():
//      set.push(1)  // TypeError
//      set.add(1)   // correct
//
// 5. Set preserves insertion order, but has no indexOf/findIndex.
//    If you need positional access, convert to array first.
//
// 6. Set.entries() returns [value, value] pairs (not [index, value]).
//    This is for API consistency with Map.
//
// 7. JSON.stringify(new Set([1,2,3])) => '{}'
//    Serialize via: JSON.stringify([...set])


// ************************************************************
//              PART 3: WEAKMAP & WEAKSET
// ************************************************************
//
// Both WeakMap and WeakSet hold "weak" references to their
// keys/values, allowing garbage collection when no other
// references to the object exist. This makes them ideal for
// metadata, caching, and tracking without memory leaks.


// ============================================================
// 16. WEAKMAP                                      [INTERMEDIATE]
// ============================================================
//
// ┌────────────────────────────────────────────────────────┐
// │  WeakMap keys MUST be objects (or non-registered       │
// │  symbols). Values are garbage collected when the key   │
// │  object has no other references.                       │
// │                                                       │
// │  Methods: get, set, has, delete (only 4!)              │
// │  NOT iterable. No .size. No .clear(). No .keys().     │
// └────────────────────────────────────────────────────────┘

// Use case: associate private data with DOM elements or objects
// without preventing garbage collection.

let wk1 = {}, wk2 = {};
let weakMap = new WeakMap([[wk1, "prashant"], [wk2, 23]]);
console.log(weakMap.has(wk1)); // true
console.log(weakMap.get(wk1)); // "prashant"

// GC demo:
let dad = { name: "Daddy" };
let mom = { name: "Mommy" };
const regularMap = new Map();
const wm = new WeakMap();
regularMap.set(dad, 1);
wm.set(mom, 2);

dad = null; // regularMap still holds reference => NOT garbage collected
mom = null; // weakMap allows GC => entry eventually removed

// INTERVIEW: "When would you use WeakMap over Map?"
// - Caching computed results for objects (cache is auto-cleaned)
// - Storing private data for class instances
// - Tracking DOM elements without causing memory leaks


// ============================================================
// 17. WEAKSET                                      [INTERMEDIATE]
// ============================================================
//
// ┌────────────────────────────────────────────────────────┐
// │  WeakSet values MUST be objects (or non-registered     │
// │  symbols). Values are garbage collected when no other  │
// │  references exist.                                     │
// │                                                       │
// │  Methods: add, has, delete (only 3!)                   │
// │  NOT iterable. No .size. No .clear(). No forEach.     │
// └────────────────────────────────────────────────────────┘

// Use case: track whether objects have been "seen" without
// preventing garbage collection.

let user1 = { name: "Prashant Yadav", age: 23 };
let user2 = { name: "Jane Doe", age: 30 };
let user3 = { name: "John Smith", age: 25 };

const ws = new WeakSet();
ws.add(user1);
ws.add(user2);
ws.add(user3);

console.log(ws.has(user2)); // true
ws.delete(user2);
console.log(ws.has(user2)); // false

// GC behavior:
// user3 = null;
// After GC runs, user3 is automatically removed from WeakSet.

// INTERVIEW: "When would you use WeakSet?"
// - Tracking visited DOM nodes
// - Preventing circular references during serialization
// - Marking objects as "processed" without memory leaks


// ============================================================
// 18. WEAK COLLECTION GOTCHAS                      [ALL LEVELS]
// ============================================================
//
// 1. WeakMap keys must be objects. Passing a primitive throws TypeError:
//      new WeakMap([[1, 'one']]) // TypeError
//
// 2. WeakSet values must be objects. Passing a primitive throws TypeError:
//      new WeakSet([1, 2]) // TypeError
//
// 3. Neither WeakMap nor WeakSet is iterable:
//      You cannot use for...of, forEach, .keys(), .values(), or .entries().
//
// 4. Neither has a .size property:
//      You cannot know how many entries exist (by design — GC is non-deterministic).
//
// 5. Neither has .clear():
//      To "clear" a WeakMap/WeakSet, create a new one.
//
// 6. You cannot serialize them:
//      JSON.stringify(weakMap) and JSON.stringify(weakSet) both produce '{}'.
//      There is no workaround since you cannot iterate entries.


// ************************************************************
//              PART 4: COMPARISON TABLE
// ************************************************************
//
// ============================================================
// 19. MAP vs SET vs WEAKMAP vs WEAKSET             [REFERENCE]
// ============================================================
//
// ┌──────────────────┬──────────────┬──────────────┬──────────────┬──────────────┐
// │                  │ Map          │ Set          │ WeakMap      │ WeakSet      │
// ├──────────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
// │ Stores           │ key-value    │ values only  │ key-value    │ values only  │
// │                  │ pairs        │              │ pairs        │              │
// ├──────────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
// │ Key/value types  │ Any -> Any   │ Any          │ Object -> Any│ Object only  │
// ├──────────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
// │ Duplicates       │ Keys unique  │ Values unique│ Keys unique  │ Values unique│
// ├──────────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
// │ Ordered          │ Insertion    │ Insertion    │ N/A          │ N/A          │
// ├──────────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
// │ Iterable         │ Yes          │ Yes          │ No           │ No           │
// ├──────────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
// │ .size            │ Yes          │ Yes          │ No           │ No           │
// ├──────────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
// │ .clear()         │ Yes          │ Yes          │ No           │ No           │
// ├──────────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
// │ GC of keys/vals  │ No           │ No           │ Yes (keys)   │ Yes (values) │
// ├──────────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
// │ Equality check   │ SameValueZero│ SameValueZero│ Reference    │ Reference    │
// ├──────────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
// │ JSON serialize   │ [...map]     │ [...set]     │ Not possible │ Not possible │
// ├──────────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
// │ Main methods     │ set, get,    │ add, has,    │ set, get,    │ add, has,    │
// │                  │ has, delete  │ delete       │ has, delete  │ delete       │
// ├──────────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
// │ Use case         │ Key-value    │ Unique       │ Object       │ Object       │
// │                  │ store with   │ collection,  │ metadata,    │ tagging,     │
// │                  │ any key type │ dedup, fast  │ caching,     │ tracking     │
// │                  │              │ lookup       │ private data │ "seen" state │
// └──────────────────┴──────────────┴──────────────┴──────────────┴──────────────┘
//
// DECISION GUIDE:
//
//   Need key-value pairs?
//     YES -> Keys are objects you don't control + need GC? -> WeakMap
//            Otherwise                                     -> Map
//     NO  -> Need to track object identity + need GC?      -> WeakSet
//            Need unique values or fast has()?              -> Set
//            Need ordered list or index access?             -> Array
