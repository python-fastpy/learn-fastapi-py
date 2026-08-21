// ============================================================
// JAVASCRIPT SYMBOLS — ULTIMATE QUICK-REFERENCE
// ============================================================
//
// ┌──────────────────────────────────────────────────────────┐
// │  Symbol is the 7th primitive type in JavaScript          │
// │  (string, number, boolean, null, undefined, bigint,     │
// │   symbol)                                                │
// │                                                         │
// │  Key properties:                                        │
// │  - Every Symbol() is UNIQUE (even with same description)│
// │  - Cannot use `new Symbol()` — it's not a constructor   │
// │  - Used for unique property keys that won't collide     │
// │  - Hidden from for...in, Object.keys, JSON.stringify    │
// │  - Visible via Object.getOwnPropertySymbols()           │
// └──────────────────────────────────────────────────────────┘


// ============================================================
// 1. CREATING SYMBOLS                              [BASIC]
// ============================================================

let name = Symbol();
let details = {};
details[name] = "shubham";
console.log(name);          // Symbol()
console.log(details[name]); // "shubham"

// GOTCHA: Cannot use `new Symbol()` — throws TypeError
// Symbols are primitives, not objects.

// Description (for debugging only — does not affect uniqueness)
let name1 = Symbol('Full Name');
let details1 = {};
details1[name1] = "shubham v";
console.log(details1[name1]); // "shubham v"
console.log(name1);           // Symbol(Full Name)


// ============================================================
// 2. SYMBOLS ARE ALWAYS UNIQUE                     [BASIC]
// ============================================================

// INTERVIEW: "Are two symbols with the same description equal?"
// NO — every Symbol() call creates a unique value.

let details2 = {};
let firstname = Symbol('Full Name');
details2[firstname] = "shubham";

let lastName = Symbol('Full Name');
details2[lastName] = "vinayak";

console.log(firstname === lastName); // false — different symbols!
console.log(details2[firstname]);    // "shubham"
console.log(details2[lastName]);     // "vinayak"


// ============================================================
// 3. SYMBOLS AS OBJECT PROPERTIES                  [BASIC]
// ============================================================

// --- Computed property names ---
let firstName1 = Symbol('First Name');
let lastName1 = Symbol('Last Name');

let details3 = {
  [firstName1]: "shubham",
  [lastName1]: "vinayak"
};
console.log(details3[firstName1]); // "shubham"
console.log(details3[lastName1]);  // "vinayak"

// --- Object.defineProperty ---
let firstname2 = Symbol("First Name");
let lastName2 = Symbol("Last Name");
let details4 = {};

Object.defineProperty(details4, firstname2, { value: "Shubham", writable: false });
Object.defineProperty(details4, lastName2, { value: "Vinayak", writable: false });
console.log(details4[firstname2]); // "Shubham"
console.log(details4[lastName2]);  // "Vinayak"

// --- Object.defineProperties ---
let firstname3 = Symbol('First Name');
let lastName3 = Symbol('Last Name');
let details5 = {};

Object.defineProperties(details5, {
  [firstname3]: { value: "shubham", writable: false },
  [lastName3]:  { value: "vinayak", writable: false }
});
console.log(details5[firstname3]); // "shubham"
console.log(details5[lastName3]);  // "vinayak"


// ============================================================
// 4. GLOBAL SYMBOL REGISTRY                        [INTERMEDIATE]
// ============================================================

// Symbol.for(key) — creates OR retrieves a symbol from global registry
// Symbols with the same key are the SAME symbol (shared across realms)

let details6 = {};

let firstname4 = Symbol.for('name');
details6[firstname4] = "shubham for";

let lastname4 = Symbol.for('name');
details6[lastname4] = "overwritten!"; // same symbol — overwrites!

console.log(firstname4 === lastname4); // true — same symbol!
console.log(details6[firstname4]);     // "overwritten!"

// Symbol.keyFor(sym) — returns the key for a global symbol
let firstname5 = Symbol.for("name");
let lastname5 = Symbol.for("name");
let middlename = Symbol('abc'); // NOT in global registry

console.log(Symbol.keyFor(firstname5)); // "name"
console.log(Symbol.keyFor(lastname5));  // "name"
console.log(Symbol.keyFor(middlename)); // undefined — not global

// INTERVIEW: "Symbol() vs Symbol.for()"
// Symbol()      — always unique, local scope
// Symbol.for()  — shared globally, same key = same symbol


// ============================================================
// 5. RETRIEVING SYMBOL PROPERTIES                  [INTERMEDIATE]
// ============================================================

// Symbols are HIDDEN from:
//   Object.keys()              — returns only string keys
//   Object.getOwnPropertyNames() — returns only string keys
//   for...in                   — iterates only string keys
//   JSON.stringify()           — ignores symbol properties

// To find symbol properties:
//   Object.getOwnPropertySymbols(obj) — returns array of symbol keys

let office = {
  [Symbol("tom")]: "CEO",
  [Symbol("mark")]: "CTO",
  [Symbol("henry")]: "HR"
};

let symbols1 = Object.getOwnPropertySymbols(office);
console.log(symbols1); // [Symbol(tom), Symbol(mark), Symbol(henry)]

let values = symbols1.map(sym => office[sym]);
console.log(values); // ["CEO", "CTO", "HR"]

// Reflect.ownKeys() returns ALL keys (strings + symbols)
// Reflect.ownKeys(office); // [Symbol(tom), Symbol(mark), Symbol(henry)]


// ============================================================
// 6. WELL-KNOWN SYMBOLS                            [ADVANCED]
// ============================================================
//
// INTERVIEW: "What are well-known symbols and why do they matter?"
//
// Well-known symbols are built-in Symbol values that customize
// language-level behavior. They let you hook into JS internals.
//
// ┌────────────────────────┬────────────────────────────────────────┐
// │ Symbol                 │ Purpose                                │
// ├────────────────────────┼────────────────────────────────────────┤
// │ Symbol.iterator        │ Makes object iterable (for...of)       │
// │ Symbol.asyncIterator   │ Makes object async iterable            │
// │ Symbol.toPrimitive     │ Custom type conversion                 │
// │ Symbol.hasInstance      │ Custom instanceof behavior             │
// │ Symbol.toStringTag     │ Custom Object.prototype.toString       │
// │ Symbol.species         │ Constructor for derived objects         │
// │ Symbol.isConcatSpreadable │ Controls Array.concat behavior      │
// │ Symbol.match/replace/  │ Custom string method behavior          │
// │   search/split         │                                        │
// │ Symbol.unscopables     │ Exclude props from `with` statement    │
// └────────────────────────┴────────────────────────────────────────┘


// --- Symbol.iterator --- // [INTERMEDIATE]
// Makes an object work with for...of, spread, destructuring

const range = {
  from: 1,
  to: 5,
  [Symbol.iterator]() {
    let current = this.from;
    const last = this.to;
    return {
      next() {
        return current <= last
          ? { value: current++, done: false }
          : { value: undefined, done: true };
      }
    };
  }
};
console.log([...range]); // [1, 2, 3, 4, 5]
for (const n of range) console.log(n); // 1, 2, 3, 4, 5


// --- Symbol.toPrimitive --- // [ADVANCED]
// Controls what happens when object is coerced to a primitive

class Money {
  constructor(amount, currency) {
    this.amount = amount;
    this.currency = currency;
  }
  [Symbol.toPrimitive](hint) {
    if (hint === 'number') return this.amount;
    if (hint === 'string') return `${this.amount} ${this.currency}`;
    return this.amount; // default
  }
}

const price = new Money(42, 'USD');
console.log(+price);       // 42          (hint: 'number')
console.log(`${price}`);   // "42 USD"    (hint: 'string')
console.log(price + 0);    // 42          (hint: 'default')

// hint values:
//   'number'  — unary +, comparison, Math functions
//   'string'  — template literal, String()
//   'default' — binary +, == comparison


// --- Symbol.hasInstance --- // [ADVANCED]
// Custom behavior for `instanceof`

class EvenNumber {
  static [Symbol.hasInstance](num) {
    return typeof num === 'number' && num % 2 === 0;
  }
}
console.log(4 instanceof EvenNumber);  // true
console.log(3 instanceof EvenNumber);  // false


// --- Symbol.toStringTag --- // [ADVANCED]
// Controls Object.prototype.toString() output

class MyCollection {
  get [Symbol.toStringTag]() {
    return 'MyCollection';
  }
}
const col = new MyCollection();
console.log(Object.prototype.toString.call(col)); // "[object MyCollection]"

// Built-in examples:
// Object.prototype.toString.call(new Map());  // "[object Map]"
// Object.prototype.toString.call(new Set());  // "[object Set]"


// --- Symbol.species --- // [ADVANCED]
// Controls which constructor is used for derived objects

class SpecialArray extends Array {
  static get [Symbol.species]() {
    return Array; // map/filter/etc. return plain Array, not SpecialArray
  }
}
const special = new SpecialArray(1, 2, 3);
const mapped = special.map(x => x * 2);
console.log(mapped instanceof SpecialArray); // false
console.log(mapped instanceof Array);        // true


// --- Symbol.isConcatSpreadable --- // [ADVANCED]
// Controls whether Array.concat spreads an object

const nonSpreadable = [1, 2, 3];
nonSpreadable[Symbol.isConcatSpreadable] = false;
console.log([0].concat(nonSpreadable)); // [0, [1, 2, 3]] — not spread!

// Make an array-like spreadable:
const arrayLike = { 0: 'a', 1: 'b', length: 2, [Symbol.isConcatSpreadable]: true };
console.log([].concat(arrayLike)); // ['a', 'b']


// --- Symbol.asyncIterator --- // [ADVANCED]
// Makes object consumable with `for await...of`

const asyncRange = {
  from: 1,
  to: 3,
  [Symbol.asyncIterator]() {
    let current = this.from;
    const last = this.to;
    return {
      async next() {
        await new Promise(r => setTimeout(r, 100));
        return current <= last
          ? { value: current++, done: false }
          : { done: true };
      }
    };
  }
};
// (async () => { for await (const n of asyncRange) console.log(n); })();
// 1, 2, 3


// ============================================================
// 7. PRACTICAL USE CASES                           [INTERMEDIATE]
// ============================================================

// --- Private-ish properties ---
// Symbols are not truly private but are hidden from most reflection.
const _id = Symbol('id');
class User {
  constructor(name, id) {
    this.name = name;
    this[_id] = id;
  }
  getId() { return this[_id]; }
}
const u = new User('Alice', 42);
console.log(u.name);             // "Alice"
console.log(u[_id]);             // 42 (accessible if you have the symbol)
console.log(JSON.stringify(u));   // '{"name":"Alice"}' — symbol key hidden!
console.log(Object.keys(u));      // ['name'] — symbol key hidden!

// --- Enum-like constants ---
const Direction = Object.freeze({
  UP:    Symbol('UP'),
  DOWN:  Symbol('DOWN'),
  LEFT:  Symbol('LEFT'),
  RIGHT: Symbol('RIGHT'),
});
// Guaranteed unique — no accidental collision with strings

// --- Metaprogramming hooks ---
// Use well-known symbols to customize how your objects interact
// with built-in JS operations (see section 6 above).


// ============================================================
// GOTCHAS                                          [ALL LEVELS]
// ============================================================
//
// 1. `new Symbol()` throws TypeError — symbols are primitives
//
// 2. Symbol() === Symbol() is ALWAYS false
//    Symbol.for('x') === Symbol.for('x') is true (global registry)
//
// 3. Symbols are NOT auto-converted to strings:
//      const s = Symbol('hi');
//      'prefix' + s;     // TypeError!
//      `template ${s}`;  // TypeError!
//      String(s);        // "Symbol(hi)" — explicit conversion OK
//      s.toString();     // "Symbol(hi)" — explicit OK
//      s.description;    // "hi" — ES2019, no "Symbol()" wrapper
//
// 4. Symbol properties are hidden from:
//      for...in, Object.keys(), Object.getOwnPropertyNames(),
//      JSON.stringify()
//    Visible via:
//      Object.getOwnPropertySymbols(), Reflect.ownKeys()
//
// 5. typeof Symbol() === 'symbol' (lowercase)
//
// 6. Symbols survive across serialization boundaries only
//    if you use Symbol.for() (global registry).
//    Regular Symbol() values are lost in structured clone,
//    JSON, postMessage, etc.
//
// 7. WeakMap can use symbols as keys (since ES2023), but only
//    non-registered symbols (created with Symbol(), not Symbol.for()).
//
// 8. Symbol.for() is cross-realm: same key returns same symbol
//    even across iframes, workers, and service workers.
