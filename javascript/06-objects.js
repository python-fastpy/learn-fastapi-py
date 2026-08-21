// ============================================================
// JAVASCRIPT OBJECTS -- ULTIMATE QUICK-REFERENCE
// ============================================================
// Covers: primitive vs structural types, creation, property
// descriptors, static methods, freeze/seal/preventExtensions,
// shallow & deep copy, equality, cloning, mutability, optional
// chaining, Proxy/Reflect, WeakRef, Object.groupBy, and more.
// ============================================================
// Merged from ObjectExample.js + objectinfo.js

// ============================================================
// TABLE OF CONTENTS
// ============================================================
//  1. Primitive vs Structural Types                    [BASIC]
//  2. Object Creation (literal, Object.create, new)    [BASIC]
//  3. Property Shorthand & Computed Properties          [BASIC]
//  4. Property Descriptors & defineProperty             [INTERMEDIATE]
//  5. Object.keys / values / entries / fromEntries      [BASIC]
//  6. Property Enumeration Order Rules                  [INTERMEDIATE]
//  7. Object.assign                                     [BASIC]
//  8. hasOwn / hasOwnProperty                           [BASIC]
//  9. Object.groupBy (ES2024)                           [INTERMEDIATE]
// 10. Object.is & Equality Comparisons                  [BASIC]
// 11. Shallow vs Deep Equality                          [INTERMEDIATE]
// 12. freeze / seal / preventExtensions                 [INTERMEDIATE]
// 13. Reference Sharing & Shallow Copy                  [BASIC]
// 14. Deep Copy Methods                                 [INTERMEDIATE]
// 15. Manual Deep Clone                                 [INTERMEDIATE]
// 16. Mutability & Immutability                         [BASIC]
// 17. Immutable Update Patterns                         [INTERMEDIATE]
// 18. Optional Chaining with Objects                    [BASIC]
// 19. Getters & Setters                                 [INTERMEDIATE]
// 20. Prototype & Iteration                             [INTERMEDIATE]
// 21. null & typeof null                                [BASIC]
// 22. Removing Properties                               [BASIC]
// 23. Proxy & Reflect                                   [ADVANCED]
// 24. WeakRef & FinalizationRegistry                    [ADVANCED]
// 25. Record & Tuple Proposal                           [ADVANCED]
// 26. Performance Comparison of Copy Methods            [ADVANCED]
// 27. Gotchas                                           [ALL]
// 28. Comparison Tables                                 [REFERENCE]


// ============================================================
// 1. PRIMITIVE vs STRUCTURAL TYPES                   [BASIC]
// ============================================================
//
// ASCII DIAGRAM -- Memory model
// -----------------------------------------------
//  Primitive (pass by value):
//    let x = 2        Stack: [ x: 2 ]
//    let y = x        Stack: [ x: 2, y: 2 ]   (independent copy)
//    y += 1            Stack: [ x: 2, y: 3 ]   (x unchanged)
//
//  Structural (pass by reference):
//    let a = [1,2]    Stack: [ a: ---> ] Heap: [ [1,2] ]
//    let b = a        Stack: [ a: ---> ] Heap: [ [1,2] ]
//                            [ b: ---> ]           ^
//                     Both point to SAME heap object
// -----------------------------------------------
//
//  Primitives: undefined, boolean, number, string, bigint, symbol
//  Structural: Object, Array, Map, Set, Date, RegExp, Function, etc.

// Primitive -- value is copied
let x = 2;
let y = x;
y += 1;
console.log(x); // 2 (unchanged)
console.log(y); // 3

// Structural -- reference is copied
let xArray = [1, 2, 3];
let yArray = xArray;
yArray.push(4);
console.log(xArray); // [1, 2, 3, 4] -- BOTH affected!
console.log(yArray); // [1, 2, 3, 4]


// ============================================================
// 2. OBJECT CREATION                                 [BASIC]
// ============================================================

// --- 2a. Object literal ---
const myObj = { name: "shubham" };
console.log(myObj); // { name: "shubham" }

const anotherObj = {
    alive: true,
    answer: 42,
    hobbies: ["Eat", "Sleep", "Code"],
    beverage: { morning: "Coffee", afternoon: "Iced Tea" },
    action() { return "Hello World"; } // shorthand method
};
console.log(anotherObj.beverage);       // dot notation
console.log(anotherObj['beverage']);     // bracket notation
console.log(anotherObj['action']());    // calling method via bracket

// INTERVIEW: How are non-string keys stored?
// All keys are coerced to strings (except Symbols).
let obj1 = {};
let obj2 = { name: "shubham" };
let obj3 = {};
obj1[obj2] = "vinayak";    // key becomes "[object Object]"
obj1.obj2 = "vpn";         // key is literally "obj2"
console.log(obj1[obj2]);   // "vinayak"
console.log(obj1);         // { '[object Object]': 'vinayak', obj2: 'vpn' }
console.log(obj1[obj3]);   // "vinayak" -- same "[object Object]" key!

// --- 2b. Object.create(proto [, propertiesObject]) ---
// Creates a new object with the given prototype.
const vehicle = {
    wheels: 4,
    engine() { return "vroom...!!!"; }
};
const truck = Object.create(vehicle);
truck.doors = 2;
console.log(truck.wheels);   // 4 -- inherited from prototype
console.log(truck.engine()); // "vroom...!!!"

// With property descriptors as second argument:
const base = { greet: "hi" };
const derived = Object.create(base, {
    foo: { writable: true, configurable: true, enumerable: false, value: "hello" }
});
console.log(derived.foo);           // "hello"
console.log(Object.keys(derived));  // [] -- foo is non-enumerable


// ============================================================
// 3. PROPERTY SHORTHAND & COMPUTED PROPERTIES        [BASIC]
// ============================================================

// --- Shorthand ---
const px = 10, py = 20;
const point = { x: px, y: py }; // shorthand: { px, py } if names match
console.log(point);              // { x: 10, y: 20 }

// --- Computed property names ---
const propName = "score";
const player = {
    name: "Alice",
    [propName]: 100,               // key is "score"
    [`${propName}Doubled`]: 200    // key is "scoreDoubled"
};
console.log(player.score);         // 100
console.log(player.scoreDoubled);  // 200

// INTERVIEW: Computed keys are evaluated at object-creation time.
// Any expression is valid inside [ ].
const i = 0;
const dynamic = { [`key_${i}`]: "first", [`key_${i + 1}`]: "second" };
console.log(dynamic); // { key_0: 'first', key_1: 'second' }


// ============================================================
// 4. PROPERTY DESCRIPTORS & defineProperty      [INTERMEDIATE]
// ============================================================
//
// ASCII DIAGRAM -- Property Descriptor Flags
// -------------------------------------------
//  +------------------+------------------------------------------+
//  | Flag             | What it controls                         |
//  +------------------+------------------------------------------+
//  | value            | The property's value                     |
//  | writable         | Can value be changed with = ?            |
//  | enumerable       | Shows up in for...in / Object.keys?      |
//  | configurable     | Can descriptor be changed / prop deleted?|
//  | get              | Getter function (accessor descriptor)    |
//  | set              | Setter function (accessor descriptor)    |
//  +------------------+------------------------------------------+
//  NOTE: A descriptor is EITHER data (value+writable) OR
//        accessor (get+set). Mixing them throws TypeError.

// --- defineProperty ---
const obj5 = {};
Object.defineProperty(obj5, 'readOnly', {
    value: 42,
    writable: false,
    enumerable: true,
    configurable: false
});
obj5.readOnly = 77;          // silently fails (throws in strict mode)
console.log(obj5.readOnly);  // 42

// --- defineProperties (batch) ---
const obj4 = {};
Object.defineProperties(obj4, {
    propA: { value: 1, writable: true, enumerable: true, configurable: true },
    propB: { value: 2, enumerable: false }
});
console.log(obj4.propA);           // 1
console.log(Object.keys(obj4));    // ['propA'] -- propB is non-enumerable

// --- Accessor descriptor (getter/setter) ---
const obj6 = {};
let _secret = 38;
Object.defineProperty(obj6, "secret", {
    get() { return _secret; },
    set(val) { _secret = Number(val); },
    enumerable: true,
    configurable: true
});
obj6.secret = "99";
console.log(obj6.secret); // 99 (number)

// INTERVIEW: You cannot combine value/writable with get/set.
// Object.defineProperty(obj6, "bad", { value: 1, get() {} }); // TypeError!

// --- getOwnPropertyDescriptor / getOwnPropertyDescriptors ---
console.log(Object.getOwnPropertyDescriptor(obj5, 'readOnly'));
// { value: 42, writable: false, enumerable: true, configurable: false }


// ============================================================
// 5. Object.keys / values / entries / fromEntries    [BASIC]
// ============================================================

const sample = { a: 'str', b: 42, c: false };

console.log(Object.keys(sample));    // ['a', 'b', 'c']
console.log(Object.values(sample));  // ['str', 42, false]
console.log(Object.entries(sample)); // [['a','str'], ['b',42], ['c',false]]

// Iterate with entries
for (const [key, value] of Object.entries(sample)) {
    console.log(`${key}: ${value}`);
}

// String edge case
console.log(Object.keys("foo"));    // ['0', '1', '2']
console.log(Object.values("foo"));  // ['f', 'o', 'o']

// Convert Object -> Map
const map = new Map(Object.entries(sample));
console.log(map); // Map(3) { 'a' => 'str', 'b' => 42, 'c' => false }

// --- Object.fromEntries ---
// Inverse of Object.entries(). Converts [key, value] pairs -> object.

// From Map
const myMap = new Map([['a', 1], ['b', 2]]);
console.log(Object.fromEntries(myMap)); // { a: 1, b: 2 }

// From entries array
const entries = [['name', 'Alice'], ['age', 30]];
console.log(Object.fromEntries(entries)); // { name: 'Alice', age: 30 }

// INTERVIEW: Transform object values with entries + fromEntries
const prices = { apple: 1.5, banana: 0.75, cherry: 2.0 };
const doubledPrices = Object.fromEntries(
    Object.entries(prices).map(([k, v]) => [k, v * 2])
);
console.log(doubledPrices); // { apple: 3, banana: 1.5, cherry: 4 }

// Convert URLSearchParams -> object
// const params = new URLSearchParams("foo=1&bar=2");
// console.log(Object.fromEntries(params)); // { foo: '1', bar: '2' }


// ============================================================
// 6. PROPERTY ENUMERATION ORDER RULES           [INTERMEDIATE]
// ============================================================
// INTERVIEW: Since ES2015, own properties follow this order:
//
//  1. Integer indices (0, 1, 2...) in ascending numeric order
//  2. String keys in insertion order
//  3. Symbol keys in insertion order
//
// This applies to: Object.keys, Object.getOwnPropertyNames,
// Reflect.ownKeys, JSON.stringify, Object.assign, spread.

const ordered = { 10: "ten", 1: "one", b: "bravo", a: "alpha", 2: "two" };
console.log(Object.keys(ordered));
// ['1', '2', '10', 'b', 'a']  -- integers first (sorted), then strings (insertion)

// for...in additionally walks the prototype chain (still follows same order per level).
// GOTCHA: for...in order is only guaranteed for own properties since ES2020.


// ============================================================
// 7. Object.assign(target, ...sources)               [BASIC]
// ============================================================
// Copies enumerable own properties from sources to target.
// MUTATES target. Returns target.

const target = { a: 1, b: 2 };
const source = { b: 4, c: 5 };
const returned = Object.assign(target, source);
console.log(target);             // { a: 1, b: 4, c: 5 }
console.log(returned === target); // true

// Non-enumerable & inherited properties are NOT copied
// Primitives as source: only strings produce enumerable own props
const wrapped = Object.assign({}, "abc", true, 10, null, undefined);
console.log(wrapped); // { '0': 'a', '1': 'b', '2': 'c' }


// ============================================================
// 8. hasOwn / hasOwnProperty                         [BASIC]
// ============================================================

// INTERVIEW: Prefer Object.hasOwn() (ES2022) over .hasOwnProperty()
// because it works on objects created with Object.create(null).

const proto = { inherited: true };
const child = Object.create(proto);
child.own = 42;

console.log(Object.hasOwn(child, 'own'));       // true
console.log(Object.hasOwn(child, 'inherited')); // false
console.log(Object.hasOwn(child, 'toString'));  // false

// Legacy: child.hasOwnProperty('own') -- same result but fails
// if child was created with Object.create(null).


// ============================================================
// 9. Object.groupBy (ES2024)                    [INTERMEDIATE]
// ============================================================
// INTERVIEW: New in ES2024. Groups array items into an object
// whose keys come from a callback. Returns a null-prototype object.

const inventory = [
    { name: "asparagus", type: "vegetables", qty: 5 },
    { name: "bananas",   type: "fruit",      qty: 0 },
    { name: "goat",      type: "meat",       qty: 23 },
    { name: "cherries",  type: "fruit",      qty: 5 },
    { name: "fish",      type: "meat",       qty: 22 }
];

const grouped = Object.groupBy(inventory, item => item.type);
console.log(grouped);
// {
//   vegetables: [ { name: 'asparagus', ... } ],
//   fruit:      [ { name: 'bananas', ... }, { name: 'cherries', ... } ],
//   meat:       [ { name: 'goat', ... }, { name: 'fish', ... } ]
// }

// Group by custom logic
const byStock = Object.groupBy(inventory, ({ qty }) =>
    qty > 0 ? "inStock" : "outOfStock"
);
console.log(Object.keys(byStock)); // ['inStock', 'outOfStock']

// NOTE: For Map keys (non-string), use Map.groupBy() instead.


// ============================================================
// 10. Object.is & EQUALITY COMPARISONS               [BASIC]
// ============================================================
//
// +--------------------+----------+----------+-----------+
// | Comparison         |  ==      |  ===     | Object.is |
// +--------------------+----------+----------+-----------+
// | NaN vs NaN         | false    | false    | true      |
// | +0 vs -0           | true     | true     | false     |
// | null vs undefined  | true     | false    | false     |
// | '1' vs 1           | true     | false    | false     |
// +--------------------+----------+----------+-----------+

console.log(Object.is(NaN, NaN));  // true  (unlike ===)
console.log(Object.is(-0, 0));     // false (unlike ===)
console.log(Object.is('1', 1));    // false


// ============================================================
// 11. SHALLOW vs DEEP EQUALITY                  [INTERMEDIATE]
// ============================================================

// --- Referential equality ---
const hero1 = { name: 'Batman' };
const hero2 = { name: 'Batman' };
console.log(hero1 === hero1);           // true  (same reference)
console.log(hero1 === hero2);           // false (different objects)
console.log(Object.is(hero1, hero2));   // false

// --- Shallow equality ---
function shallowEqual(a, b) {
    const keysA = Object.keys(a), keysB = Object.keys(b);
    if (keysA.length !== keysB.length) return false;
    return keysA.every(key => a[key] === b[key]);
}
console.log(shallowEqual({ x: 1 }, { x: 1 }));                         // true
console.log(shallowEqual({ x: { n: 1 } }, { x: { n: 1 } }));           // false (nested)

// --- Deep equality ---
function deepEqual(a, b) {
    if (a === b) return true;
    if (typeof a !== 'object' || typeof b !== 'object' || a == null || b == null) return false;
    const keysA = Object.keys(a), keysB = Object.keys(b);
    if (keysA.length !== keysB.length) return false;
    return keysA.every(key => deepEqual(a[key], b[key]));
}
console.log(deepEqual({ x: { n: 1 } }, { x: { n: 1 } })); // true


// ============================================================
// 12. freeze / seal / preventExtensions         [INTERMEDIATE]
// ============================================================
//
// COMPARISON TABLE
// +---------------------+------------------+-------------+--------------------+
// |                     | preventExtensions| seal        | freeze             |
// +---------------------+------------------+-------------+--------------------+
// | Add new properties  | NO               | NO          | NO                 |
// | Delete properties   | yes              | NO          | NO                 |
// | Change values       | yes              | yes         | NO                 |
// | Reconfigure props   | yes              | NO          | NO                 |
// | Change prototype    | NO               | NO          | NO                 |
// | Checker method      | isExtensible()   | isSealed()  | isFrozen()         |
// +---------------------+------------------+-------------+--------------------+
// ALL THREE ARE SHALLOW -- nested objects are NOT affected.

// --- freeze ---
const employee = {
    name: "Mayank",
    designation: "Developer",
    address: { street: "Rohini", city: "Delhi" }
};
Object.freeze(employee);
employee.name = "Dummy";           // silently fails
employee.address.city = "Noida";   // SUCCEEDS -- shallow freeze!
console.log(employee.address.city); // "Noida"

// Deep freeze helper:
function deepFreeze(obj) {
    Object.freeze(obj);
    Object.keys(obj).forEach(key => {
        if (typeof obj[key] === 'object' && obj[key] !== null && !Object.isFrozen(obj[key])) {
            deepFreeze(obj[key]);
        }
    });
    return obj;
}

// --- seal ---
const sealed = { prop: 42 };
Object.seal(sealed);
sealed.prop = 33;       // allowed -- value change OK
delete sealed.prop;     // fails -- cannot delete
sealed.newProp = "hi";  // fails -- cannot add
console.log(sealed);    // { prop: 33 }

// --- preventExtensions ---
const ext = { a: 1 };
Object.preventExtensions(ext);
ext.a = 2;       // allowed
delete ext.a;    // allowed
ext.b = 3;       // fails -- cannot add


// ============================================================
// 13. REFERENCE SHARING & SHALLOW COPY               [BASIC]
// ============================================================
//
// ASCII DIAGRAM -- Shallow vs Deep Copy Memory
// -----------------------------------------------
//  Original:
//    obj ──> { name: "A", address: ──> { city: "Delhi" } }
//
//  Shallow Copy:
//    copy ─> { name: "A", address: ──> { city: "Delhi" } }
//                                  ^--- SAME reference!
//    Changing copy.name = "B"       -> only copy changes
//    Changing copy.address.city = X -> BOTH change!
//
//  Deep Copy:
//    copy ─> { name: "A", address: ──> { city: "Delhi" } }
//                                       (NEW object)
//    Changing anything on copy -> original untouched
// -----------------------------------------------

const parentObject = {
    name: 'Lazy Panda',
    profile: 'Developer',
    address: { country: 'IN', state: 'WB' }
};

// --- 3 shallow copy methods ---

// Method 1: Spread
const shallow1 = { ...parentObject };

// Method 2: Object.assign
const shallow2 = Object.assign({}, parentObject);

// Method 3: Destructuring rest
const { ...shallow3 } = parentObject;

// Primitive fields are independent
shallow1.name = "Lazy Panda Tech";
console.log(parentObject.name); // "Lazy Panda" (unaffected)

// Nested objects still share references!
shallow1.address.country = 'India';
console.log(parentObject.address.country); // "India" -- AFFECTED!

// INTERVIEW: Shallow copy is sufficient when the object has only
// primitive values. For nested objects, you need deep copy.

// --- Clone + override ---
const hero = { name: 'Batman', city: 'Gotham' };
const enhanced = Object.assign({}, hero, { name: 'Batman Clone' });
console.log(enhanced); // { name: 'Batman Clone', city: 'Gotham' }

// --- Clone + omit (destructure away unwanted key) ---
const { city: _discard, ...withoutCity } = { ...hero, realName: 'Bruce Wayne' };
console.log(withoutCity); // { name: 'Batman', realName: 'Bruce Wayne' }


// ============================================================
// 14. DEEP COPY METHODS                         [INTERMEDIATE]
// ============================================================

// --- Method 1: structuredClone (recommended, ES2022+) ---
const deep1 = structuredClone(parentObject);
deep1.address.country = 'US';
console.log(parentObject.address.country); // "India" (unaffected by deep1)

// --- Method 2: JSON round-trip (lossy) ---
const developer = {
    name: "shubham",
    code: "javascript",
    getAge: function() { return 30; },
    createdAt: new Date()
};

const jsonClone = JSON.parse(JSON.stringify(developer));
console.log(jsonClone);
// INTERVIEW: What's lost?
//   - getAge is GONE (functions are stripped)
//   - createdAt is a STRING, not a Date object
//   - undefined values are stripped
//   - NaN/Infinity become null
//   - Symbol keys/values are stripped
//   - Circular references throw TypeError

// --- structuredClone limitations ---
// Functions are still NOT cloneable -- throws DataCloneError
// Must remove functions first or use manual clone

// --- structuredClone LIMITATIONS TABLE ---
//
// +----------------------------+-------------------+----------------------------+
// | Type                       | Can Clone?        | Notes                      |
// +----------------------------+-------------------+----------------------------+
// | Plain objects / arrays     | YES               |                            |
// | Date                       | YES               | Preserves type             |
// | RegExp                     | YES               | Preserves flags            |
// | Map / Set                  | YES               | Deep clones contents       |
// | ArrayBuffer / TypedArray   | YES               | Can transfer ownership     |
// | Blob / File / FileList     | YES               |                            |
// | ImageData                  | YES               |                            |
// | Error (basic types)        | YES (most)        | Message + name preserved   |
// | Circular references        | YES               | Handles correctly          |
// +----------------------------+-------------------+----------------------------+
// | Functions                  | NO -- throws      | DataCloneError             |
// | DOM Nodes                  | NO -- throws      | DataCloneError             |
// | Proxy                      | NO -- throws      | DataCloneError             |
// | Symbols (as values)        | NO -- throws      | DataCloneError             |
// | Property descriptors       | NO -- lost        | All become writable/enum   |
// | Prototype chain            | NO -- lost        | Result is plain object     |
// | Getters / Setters          | NO -- lost        | Value is read and copied   |
// | WeakMap / WeakRef          | NO -- throws      | DataCloneError             |
// +----------------------------+-------------------+----------------------------+
//
// INTERVIEW: structuredClone is the best built-in option for deep copy.
// Use lodash.cloneDeep or manual recursion only when you need to handle
// functions or preserve prototypes.

// --- JSON.parse(JSON.stringify) LIMITATIONS TABLE ---
//
// +----------------------------+-------------------+----------------------------+
// | Type                       | Survives?         | What happens               |
// +----------------------------+-------------------+----------------------------+
// | Plain objects / arrays     | YES               |                            |
// | Strings / Numbers / Bool   | YES               |                            |
// | null                       | YES               |                            |
// | Date                       | Partially         | Becomes ISO string         |
// | RegExp                     | NO                | Becomes {}                 |
// | Map / Set                  | NO                | Becomes {}                 |
// | undefined                  | NO                | Stripped from objects       |
// | NaN / Infinity             | NO                | Becomes null               |
// | Functions                  | NO                | Stripped                   |
// | Symbol keys/values         | NO                | Stripped                   |
// | BigInt                     | NO                | Throws TypeError           |
// | Circular references        | NO                | Throws TypeError           |
// +----------------------------+-------------------+----------------------------+


// ============================================================
// 15. MANUAL DEEP CLONE                         [INTERMEDIATE]
// ============================================================

const deepClone = (obj) => {
    if (typeof obj !== "object" || obj === null) return obj;
    const clone = Array.isArray(obj) ? [] : {};
    for (let key in obj) {
        if (Object.hasOwn(obj, key)) {
            clone[key] = deepClone(obj[key]);
        }
    }
    return clone;
};

const scoreArray = [44, 23, 12];
const clonedArr = deepClone(scoreArray);
console.log(clonedArr);                 // [44, 23, 12]
console.log(clonedArr === scoreArray);  // false

const scoreObj = { first: 44, second: 12, third: { a: 1, b: 2 } };
const clonedObj = deepClone(scoreObj);
clonedObj.third.a = 99;
console.log(scoreObj.third.a);  // 1 (unaffected)
console.log(clonedObj.third.a); // 99

// GOTCHA: This simple deepClone does NOT handle:
// - Date, RegExp, Map, Set (they need special constructors)
// - Circular references (infinite recursion)
// - Symbols, non-enumerable properties
// For production, use structuredClone or lodash.cloneDeep.


// ============================================================
// 16. MUTABILITY & IMMUTABILITY                      [BASIC]
// ============================================================

// Primitives are immutable
let myName = "Dave";
myName[0] = "W";        // silently fails
console.log(myName);     // "Dave" (unchanged)

// Reassignment is NOT mutation -- it points to a new value
myName = "David";
console.log(myName);     // "David"

// Structural types contain mutable data
yArray[0] = 9;
console.log(yArray);    // [9, 2, 3, 4]
console.log(xArray);    // [9, 2, 3, 4] -- same reference!

// INTERVIEW: const prevents reassignment, NOT mutation
const arr = [1, 2, 3];
arr.push(4);            // allowed!
// arr = [5];            // TypeError: Assignment to constant variable

// --- Pure functions avoid mutating input data ---
// Impure (mutates input):
const addToHistory_impure = (array, score) => {
    array.push(score);   // side effect!
    return array;
};

// Pure (returns new array):
const addToHistory_pure = (array, score) => {
    return [...array, score]; // no mutation
};

const scores = [44, 23, 12];
const newScores = addToHistory_pure(scores, 14);
console.log(scores);    // [44, 23, 12] (unchanged)
console.log(newScores); // [44, 23, 12, 14]


// ============================================================
// 17. IMMUTABLE UPDATE PATTERNS                 [INTERMEDIATE]
// ============================================================
// INTERVIEW: Common in React, Redux, and functional programming.

// --- Spread-based updates (native JS) ---
const state = {
    user: { name: "Alice", address: { city: "NYC", zip: "10001" } },
    items: [1, 2, 3]
};

// Update nested field immutably
const newState = {
    ...state,
    user: {
        ...state.user,
        address: {
            ...state.user.address,
            city: "LA"           // only this changes
        }
    }
};
console.log(state.user.address.city);    // "NYC" (unchanged)
console.log(newState.user.address.city); // "LA"

// Add to array immutably
const withItem = { ...state, items: [...state.items, 4] };

// Remove from array immutably
const without2 = { ...state, items: state.items.filter(i => i !== 2) };

// Update item in array immutably
const doubled = {
    ...state,
    items: state.items.map(i => i === 2 ? i * 10 : i) // [1, 20, 3]
};

// --- Immer-style approach (conceptual) ---
// Libraries like Immer let you write "mutations" that produce immutable updates:
//
//   import produce from 'immer';
//   const next = produce(state, draft => {
//       draft.user.address.city = "LA";   // looks like mutation
//       draft.items.push(4);              // but returns new object
//   });
//
// Under the hood, Immer uses Proxy to track changes and produces
// a structurally shared immutable result.

// --- Object.assign for immutable updates ---
const updated = Object.assign({}, state, {
    user: Object.assign({}, state.user, { name: "Bob" })
});
console.log(state.user.name);   // "Alice"
console.log(updated.user.name); // "Bob"

// INTERVIEW TIP: Spread is more readable than Object.assign for
// immutable updates. Use Immer for deeply nested state.


// ============================================================
// 18. OPTIONAL CHAINING WITH OBJECTS                 [BASIC]
// ============================================================
// INTERVIEW: ?. short-circuits to undefined if left side is null/undefined

const user = {
    profile: {
        address: { city: "NYC" }
    },
    getGreeting() { return "Hello!"; }
};

console.log(user.profile?.address?.city);  // "NYC"
console.log(user.profile?.phone?.number);  // undefined (no error)
console.log(user.getGreeting?.());         // "Hello!" -- method call
console.log(user.missing?.());             // undefined -- missing method
console.log(user.profile?.['address']?.['city']); // "NYC" -- bracket

// With nullish coalescing
const userCity = user.profile?.address?.zip ?? "No ZIP";
console.log(userCity); // "No ZIP"


// ============================================================
// 19. GETTERS & SETTERS                         [INTERMEDIATE]
// ============================================================

const myObject = {
    myString: 'value 1',
    get myNumber() { return this._myNumber; },
    set myNumber(value) { this._myNumber = Number(value); }
};
myObject.myNumber = '15';
console.log(myObject.myNumber); // 15 (converted to number)

// Shorthand methods in object literals
const collection = {
    items: [],
    add(item) { this.items.push(item); },
    get(index) { return this.items[index]; }
};
collection.add(15);
collection.add(3);
console.log(collection.get(0)); // 15


// ============================================================
// 20. PROTOTYPE & ITERATION                     [INTERMEDIATE]
// ============================================================

// --- setPrototypeOf ---
const simpleColors = { colorA: 'white', colorB: 'black' };
const natureColors = { colorC: 'green', colorD: 'yellow' };
Object.setPrototypeOf(natureColors, simpleColors);

console.log(Object.keys(natureColors)); // ['colorC', 'colorD'] -- own only
console.log(natureColors.colorA);       // 'white' -- inherited access

// COMPARISON TABLE -- Iteration methods
// +---------------------------+------+----------+---------+
// | Method                    | Own? | Inherited?| Symbols?|
// +---------------------------+------+----------+---------+
// | Object.keys()             | yes  | no       | no      |
// | Object.values()           | yes  | no       | no      |
// | Object.entries()          | yes  | no       | no      |
// | for...in                  | yes  | yes      | no      |
// | Object.getOwnPropertyNames| yes | no       | no      |
// | Reflect.ownKeys()         | yes  | no       | YES     |
// +---------------------------+------+----------+---------+
// All skip non-enumerable except getOwnPropertyNames & Reflect.ownKeys.

// __proto__ in literals (for reference only -- prefer Object.create)
const myProto = {
    propertyExists(name) { return name in this; }
};
const myNumber = { __proto__: myProto, array: [1, 2, 3] };
console.log(myNumber.propertyExists('array'));    // true
console.log(myNumber.propertyExists('missing'));  // false


// ============================================================
// 21. null & typeof null                             [BASIC]
// ============================================================

// INTERVIEW: typeof null === 'object' is a historical bug in JS.
// null represents intentional absence of an object value.

const missingObject = null;
console.log(missingObject === null);  // true
console.log(Boolean(null));           // false (null is falsy)
console.log(typeof null);            // "object" -- the famous bug

// Safe type check
function isObject(value) {
    return typeof value === 'object' && value !== null;
}
console.log(isObject({}));   // true
console.log(isObject(null)); // false
console.log(isObject(42));   // false

// null vs undefined
// - null: explicit "no value" (assigned intentionally)
// - undefined: variable declared but never assigned, or missing property

// Optional chaining + nullish coalescing for safe access
const config = null;
const theme = config?.theme ?? 'default';
console.log(theme); // 'default'


// ============================================================
// 22. REMOVING PROPERTIES                            [BASIC]
// ============================================================

// Mutable: delete operator
const emp = { name: 'John Smith', position: 'Sales Manager' };
delete emp.position;
console.log(emp); // { name: 'John Smith' }

// Immutable: destructure + rest (preferred in functional style)
const emp2 = { name: 'Jane', position: 'Engineer', dept: 'IT' };
const { position, ...empWithout } = emp2;
console.log(empWithout); // { name: 'Jane', dept: 'IT' }

// Dynamic key removal
const keyToRemove = 'dept';
const { [keyToRemove]: removed, ...rest } = empWithout;
console.log(rest); // { name: 'Jane' }


// ============================================================
// 23. PROXY & REFLECT                             [ADVANCED]
// ============================================================
// INTERVIEW: Proxy lets you intercept and customize operations
// on objects. Reflect provides the default behavior for each trap.
//
// ASCII DIAGRAM -- Proxy architecture
// ------------------------------------
//   Code ---> Proxy ---> Handler (traps)
//                |              |
//                |   get/set/has/deleteProperty/apply/construct/...
//                v              |
//             Target <----------+  (Reflect forwards to target)

// --- Basic validation proxy ---
const validator = {
    set(target, prop, value) {
        if (prop === 'age' && (typeof value !== 'number' || value < 0)) {
            throw new TypeError('Age must be a non-negative number');
        }
        return Reflect.set(target, prop, value);
    },
    get(target, prop) {
        if (prop in target) return Reflect.get(target, prop);
        return `Property "${prop}" does not exist`;
    }
};
const person = new Proxy({}, validator);
person.age = 25;
console.log(person.age);      // 25
console.log(person.missing);  // 'Property "missing" does not exist'
// person.age = -5;            // TypeError: Age must be a non-negative number

// --- Logging proxy ---
function createLoggingProxy(target) {
    return new Proxy(target, {
        get(t, prop) {
            console.log(`GET ${String(prop)}`);
            return Reflect.get(t, prop);
        },
        set(t, prop, value) {
            console.log(`SET ${String(prop)} = ${value}`);
            return Reflect.set(t, prop, value);
        }
    });
}
const logged = createLoggingProxy({ a: 1 });
logged.a;     // logs: GET a
logged.b = 2; // logs: SET b = 2

// --- Common traps ---
// has(target, prop)           -- intercepts `prop in obj`
// deleteProperty(target, prop) -- intercepts `delete obj.prop`
// ownKeys(target)             -- intercepts Object.keys, for...in, etc.
// apply(target, thisArg, args) -- intercepts function calls (target must be function)
// construct(target, args)     -- intercepts `new target()`

// INTERVIEW: Reflect methods mirror every Proxy trap 1:1.
// Always use Reflect inside traps to preserve default behavior.


// ============================================================
// 24. WeakRef & FinalizationRegistry              [ADVANCED]
// ============================================================
// INTERVIEW: Rarely asked, but impressive to know.

// WeakRef holds a weak reference to an object -- does NOT prevent
// garbage collection. Use .deref() to access (returns undefined
// if collected).

let heavyObj = { data: new Array(1000).fill("x") };
const weakRef = new WeakRef(heavyObj);

console.log(weakRef.deref()?.data?.length); // 1000

// If heavyObj is set to null and GC runs, weakRef.deref() => undefined
// heavyObj = null;
// After GC: weakRef.deref() => undefined

// FinalizationRegistry -- callback when object is garbage collected
const registry = new FinalizationRegistry((heldValue) => {
    console.log(`Object with id "${heldValue}" was garbage collected`);
});

let tempObj = { id: "abc123" };
registry.register(tempObj, "abc123"); // heldValue = "abc123"
// tempObj = null; // Eventually triggers the callback after GC

// Use cases:
//   - Cache eviction (clean up when cached object is GC'd)
//   - Resource cleanup (close file handles, network connections)
//   - Preventing memory leaks in long-running applications
//
// GOTCHA: GC timing is non-deterministic. Never rely on
// FinalizationRegistry for essential cleanup logic.


// ============================================================
// 25. RECORD & TUPLE PROPOSAL                     [ADVANCED]
// ============================================================
// Status: TC39 Stage 2 (as of 2024 -- progress stalled)
//
// Records (#{ }) and Tuples (#[ ]) are deeply immutable
// value types. They compare by value, not by reference.
//
//   const r1 = #{ x: 1, y: 2 };
//   const r2 = #{ x: 1, y: 2 };
//   r1 === r2   // true (value equality!)
//
//   const t1 = #[1, 2, 3];
//   const t2 = #[1, 2, 3];
//   t1 === t2   // true
//
//   r1.x = 5;   // TypeError -- deeply immutable
//
// Constraints:
//   - Can only contain primitives, other Records, and Tuples
//   - No objects, functions, or class instances inside
//   - Works with Map/Set as keys (value-based hashing)
//
// INTERVIEW: Record & Tuple would solve the "deep equality" and
// "accidental mutation" problems natively, but adoption timeline
// is uncertain. Use Object.freeze + spread patterns until then.


// ============================================================
// 26. PERFORMANCE COMPARISON OF COPY METHODS    [ADVANCED]
// ============================================================
//
// Rough relative performance (smaller object ~10 keys, 2 levels deep):
//
// +------------------------------+-----------+------+-------+
// | Method                       | Speed     | Deep | Safe  |
// +------------------------------+-----------+------+-------+
// | { ...obj }                   | Fastest   | No   | Yes   |
// | Object.assign({}, obj)       | Fast      | No   | Yes   |
// | JSON parse/stringify         | Slow      | Yes  | Lossy |
// | structuredClone(obj)         | Moderate  | Yes  | Yes*  |
// | Manual recursive clone       | Varies    | Yes  | Custom|
// | lodash.cloneDeep             | Moderate  | Yes  | Yes   |
// +------------------------------+-----------+------+-------+
// * Cannot clone functions, DOM nodes, etc.
//
// INTERVIEW TIP: For hot-path code with flat objects, use spread.
// For anything nested, structuredClone is the go-to since ES2022.
// JSON round-trip is a hack -- avoid in production if possible.
//
// Benchmark tip: performance.now() around 100k iterations:
//   Spread:           ~15ms
//   Object.assign:    ~18ms
//   JSON roundtrip:   ~150ms
//   structuredClone:  ~80ms
//   (Numbers are illustrative; always benchmark your own data.)


// ============================================================
// 27. GOTCHAS                                        [ALL]
// ============================================================

// -- Object keys & types --

// GOTCHA 1: Object keys are always strings (or Symbols).
//   { 1: 'a' } -- the key is the string "1", not the number 1.

// GOTCHA 2: Using an object as a key -- toString() is called.
//   obj[{}] and obj[{a:1}] both become obj["[object Object]"].
//   Use Map if you need object keys.

// GOTCHA 3: typeof null === 'object'. Use === null to check.

// GOTCHA 4: typeof obj === "object" catches null too.
//   Always add `&& obj !== null` to your type checks.

// -- Enumeration & iteration --

// GOTCHA 5: for...in iterates inherited enumerable props.
//   Always guard with hasOwn() or prefer Object.keys().

// GOTCHA 6: Property order is deterministic but nuanced:
//   integer indices first (sorted), then strings (insertion order),
//   then Symbols (insertion order).

// GOTCHA 7: Object.keys() returns string[] even for numeric keys.

// GOTCHA 8: Object.groupBy returns a null-prototype object.
//   It has no inherited methods like .hasOwnProperty().

// -- Freeze & immutability --

// GOTCHA 9: freeze/seal are SHALLOW. Nested objects are untouched.

// GOTCHA 10: const does NOT make objects immutable.
//   It only prevents reassignment of the variable binding.

// -- Copying --

// GOTCHA 11: Spread / Object.assign are SHALLOW.
//   Nested objects still share references. Always deep-clone
//   when you need full independence.

// GOTCHA 12: Object.assign and spread do NOT copy:
//   - non-enumerable properties
//   - prototype chain
//   - property descriptors (writable, configurable flags)
//   - getters/setters (they invoke the getter and copy the value)

// GOTCHA 13: JSON.parse(JSON.stringify()) loses:
//   functions, undefined, Symbols, Dates (become strings),
//   NaN/Infinity (become null), circular refs (throws).

// GOTCHA 14: structuredClone cannot clone functions or DOM nodes.
//   It throws DataCloneError.

// GOTCHA 15: structuredClone loses the prototype chain.
//   class Foo {}; const f = new Foo(); structuredClone(f) instanceof Foo // false

// GOTCHA 16: Copying an object with a Date field via spread
//   gives you the SAME Date instance, not a copy.
//   Mutating the Date in the copy mutates the original.

// GOTCHA 17: Array spread [...arr] is shallow too.
//   Nested arrays/objects inside are still shared references.

// -- Misc --

// GOTCHA 18: delete is slow. In hot paths, set to undefined instead
//   (but the key still exists -- use hasOwn to check).

// GOTCHA 19: The simple deepClone function using typeof === "Object"
//   (capital O) is a common bug. It should be "object" (lowercase).

// GOTCHA 20: GC timing is non-deterministic. Never rely on
//   FinalizationRegistry for essential cleanup logic.


// ============================================================
// 28. COMPARISON TABLES                          [REFERENCE]
// ============================================================
//
// --- freeze vs seal vs preventExtensions ---
// (See section 12 table above)
//
// --- Object.keys vs for...in ---
// +--------------------+-------------------+--------------------+
// | Feature            | Object.keys()     | for...in           |
// +--------------------+-------------------+--------------------+
// | Own properties     | yes               | yes                |
// | Inherited props    | no                | yes                |
// | Non-enumerable     | no                | no                 |
// | Symbol keys        | no                | no                 |
// | Returns            | string[]          | iterates keys      |
// | Guaranteed order   | yes (ES2015+)     | yes (ES2020+ own)  |
// +--------------------+-------------------+--------------------+
//
// --- Copy Method Comparison ---
// +---------------------------+--------+---------+----------+--------+-----------+
// | Method                    | Shallow| Deep    | Functions| Dates  | Circular  |
// +---------------------------+--------+---------+----------+--------+-----------+
// | { ...obj }                | yes    | no      | ref copy | ref    | N/A       |
// | Object.assign({}, obj)    | yes    | no      | ref copy | ref    | N/A       |
// | JSON parse/stringify       | no    | yes     | LOST     | string | THROWS    |
// | structuredClone()         | no     | yes     | THROWS   | ok     | ok        |
// | Manual recursive          | no     | yes     | custom   | custom | custom    |
// | lodash.cloneDeep          | no     | yes     | ok       | ok     | ok        |
// +---------------------------+--------+---------+----------+--------+-----------+
//
// --- When to Use What (Copy) ---
// +-------------------------------+------------------------------------------+
// | Scenario                      | Best Method                              |
// +-------------------------------+------------------------------------------+
// | Flat object, hot path         | Spread { ...obj }                        |
// | Flat object, need assign API  | Object.assign({}, obj)                   |
// | Nested, no functions          | structuredClone(obj)                     |
// | Nested, has functions         | lodash.cloneDeep or manual               |
// | Serialization / transfer      | JSON round-trip (if types fit)           |
// | React/Redux state update      | Spread patterns or Immer                |
// +-------------------------------+------------------------------------------+
//
// --- Equality ---
// (See section 10 table above)
