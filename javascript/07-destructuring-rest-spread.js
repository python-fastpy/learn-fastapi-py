// ============================================================
// REST & SPREAD OPERATORS -- ULTIMATE QUICK-REFERENCE
// ============================================================
// Covers: destructuring, rest in arrays/objects/params, spread
// for arrays/objects/function-calls, iteration protocols,
// Object.assign vs spread, and performance considerations.
// ============================================================

// ============================================================
// TABLE OF CONTENTS
// ============================================================
// 1. The Three Dots Rule                              [BASIC]
// 2. Array Destructuring + Rest                       [BASIC]
// 3. Object Destructuring + Rest                      [BASIC]
// 4. Rest in Function Parameters                      [BASIC]
// 5. Spread in Arrays                                 [BASIC]
// 6. Spread in Objects                                [INTERMEDIATE]
// 7. Object Spread vs Object.assign Differences       [INTERMEDIATE]
// 8. Spread in Function Calls                         [BASIC]
// 9. Immutable Object Updates with Spread             [INTERMEDIATE]
// 10. Deep Nested Updates                             [INTERMEDIATE]
// 11. Spread with Iterables vs Non-Iterables          [INTERMEDIATE]
// 12. Iteration Protocols & Custom Iterables          [ADVANCED]
// 13. Prototype Preservation Pitfall                  [ADVANCED]
// 14. Performance Considerations                      [ADVANCED]
// 15. Gotchas                                         [ALL]
// 16. Comparison Tables                               [REFERENCE]


// ============================================================
// 1. THE THREE DOTS RULE                             [BASIC]
// ============================================================
// INTERVIEW: "..." means REST or SPREAD depending on context.
//
// ASCII DIAGRAM -- When is it REST vs SPREAD?
// -------------------------------------------
//  REST (collects):
//    - In function params:   function f(...args) {}
//    - In destructuring:     const [a, ...rest] = arr
//                            const { x, ...rest } = obj
//    Mnemonic: "gathering the REST of the items"
//
//  SPREAD (expands):
//    - In array literals:    [...arr1, ...arr2]
//    - In object literals:   { ...obj1, ...obj2 }
//    - In function calls:    fn(...args)
//    Mnemonic: "SPREADing items out"
// -------------------------------------------


// ============================================================
// 2. ARRAY DESTRUCTURING + REST                      [BASIC]
// ============================================================

// --- Swap two variables (no temp needed) ---
let a = 1, b = 2;
[a, b] = [b, a];
console.log(a, b); // 2 1

// --- Default values ---
const colors = [];
const [firstColor = "white"] = colors;
console.log(firstColor); // "white" (default applied)

// --- Skip elements ---
const rgb = [255, 128, 0];
const [red, , blue] = rgb;
console.log(red, blue); // 255 0

// --- Rest collects remaining elements ---
const numbers = [1, 2, 3, 4, 5];
const [first, second, ...remaining] = numbers;
console.log(first);     // 1
console.log(remaining); // [3, 4, 5]

// INTERVIEW: Rest must be the LAST element in destructuring.
// const [a, ...mid, b] = [1,2,3,4]; // SyntaxError!

// --- Immutable head/tail split ---
const nums = [1, 2, 3];
const [, ...tail] = nums;
console.log(tail); // [2, 3]
console.log(nums); // [1, 2, 3] -- original unchanged

// --- Destructure strings (they're iterable) ---
const str = "cheese";
const [firstChar = ''] = str;
console.log(firstChar); // "c"

// --- Nested destructuring ---
const matrix = [[1, 2], [3, 4]];
const [[a1, a2], [b1, b2]] = matrix;
console.log(a1, a2, b1, b2); // 1 2 3 4


// ============================================================
// 3. OBJECT DESTRUCTURING + REST                     [BASIC]
// ============================================================

const big = { foo: 'value for foo', bar: 'value for bar', baz: 42 };

// --- Basic destructuring ---
const { foo } = big;
console.log(foo); // "value for foo"

// --- Rename (alias) ---
const { foo: myFoo } = big;
console.log(myFoo); // "value for foo"

// --- Default values ---
const { missing = "default" } = big;
console.log(missing); // "default"

// --- Rest collects remaining properties ---
const { foo: removed, ...small } = big;
console.log(small); // { bar: 'value for bar', baz: 42 }
console.log(big);   // original unchanged

// --- Dynamic (computed) property name ---
const movie = { title: 'Heat', year: 1995 };
const propKey = 'title';
const { [propKey]: movieTitle } = movie;
console.log(movieTitle); // "Heat"

// --- Nested destructuring ---
const response = {
    data: { users: [{ name: "Alice" }] },
    status: 200
};
const { data: { users: [{ name: userName }] } } = response;
console.log(userName); // "Alice"

// INTERVIEW: Rest in destructuring creates a SHALLOW copy
// of the remaining properties. Nested objects still share refs.


// ============================================================
// 4. REST IN FUNCTION PARAMETERS                     [BASIC]
// ============================================================
// INTERVIEW: Rest params vs arguments object
//
// +---------------------------+------------------+------------------+
// | Feature                   | ...rest          | arguments        |
// +---------------------------+------------------+------------------+
// | Type                      | Real Array       | Array-like       |
// | Has .map/.filter/.reduce  | yes              | no               |
// | Works in arrow functions  | yes              | no (inherits)    |
// | Can name subset           | yes              | no               |
// | ES version                | ES6+             | ES1              |
// +---------------------------+------------------+------------------+

// --- Selective rest (named params + rest) ---
function filter(type, ...items) {
    return items.filter(item => typeof item === type);
}
console.log(filter('boolean', true, 0, false));        // [true, false]
console.log(filter('number', false, 4, 'Welcome', 7)); // [4, 7]

// --- Old way: using `arguments` (avoid this) ---
function sumOnlyNumbers_old() {
    return Array.prototype.filter
        .call(arguments, el => typeof el === 'number')
        .reduce((sum, el) => sum + el, 0);
}
console.log(sumOnlyNumbers_old(1, 'Hello', 5, false)); // 6

// --- Modern way: rest params ---
function sumOnlyNumbers(...args) {
    return args
        .filter(el => typeof el === 'number')
        .reduce((sum, el) => sum + el, 0);
}
console.log(sumOnlyNumbers(1, 'Hello', 5, false)); // 6

// Arrow functions have no `arguments` -- rest is the only option
const concat = (...items) => items.join('');
console.log(concat('a', 'b', 'c')); // "abc"

// Prove arrow functions inherit outer `arguments`:
(function() {
    const outerArgs = arguments;
    const inner = (...items) => {
        console.log(arguments === outerArgs); // true -- inherited
        return items.reduce((r, i) => r + i, '');
    };
    inner(1, 5, 'nine'); // "15nine"
})(42);


// ============================================================
// 5. SPREAD IN ARRAYS                                [BASIC]
// ============================================================

// --- Create with initial elements ---
const initial = [0, 1];
const nums1 = [...initial, 5, 7];    // [0, 1, 5, 7]
const nums2 = [4, 8, ...initial];    // [4, 8, 0, 1]

// --- Concatenate arrays ---
const odds = [1, 5, 7];
const evens = [4, 6, 8];
const all = [...odds, ...evens];     // [1, 5, 7, 4, 6, 8]

// --- Clone array (shallow) ---
const words = ['Hi', 'Hello', 'Good day'];
const clonedWords = [...words];
console.log(clonedWords === words);  // false

// --- Convert string to char array ---
console.log([...'hello']); // ['h', 'e', 'l', 'l', 'o']

// --- Convert Set to array ---
const unique = [...new Set([1, 2, 2, 3])]; // [1, 2, 3]

// --- Array destructure with rest ---
const seasons = ['winter', 'spring', 'summer', 'autumn'];
const [head, ...restSeasons] = seasons;
console.log(head);        // 'winter'
console.log(restSeasons); // ['spring', 'summer', 'autumn']


// ============================================================
// 6. SPREAD IN OBJECTS                          [INTERMEDIATE]
// ============================================================

// INTERVIEW: Object spread copies only OWN ENUMERABLE properties.
// Non-enumerable properties and prototype are NOT copied.

// --- Clone ---
const bird = { type: 'pigeon', color: 'white' };
const birdClone = { ...bird };
console.log(birdClone);            // { type: 'pigeon', color: 'white' }
console.log(bird === birdClone);   // false

// --- Merge multiple objects ---
const part1 = { color: 'white' };
const part2 = { model: 'Honda' };
const part3 = { year: 2005 };
const car = { ...part1, ...part2, ...part3 };
console.log(car); // { color: 'white', model: 'Honda', year: 2005 }

// Later sources override earlier ones:
const merged = { a: 1, b: 2, ...{ b: 3, c: 4 } };
console.log(merged); // { a: 1, b: 3, c: 4 }

// --- Non-enumerable properties are skipped ---
const person = { name: 'Dave', surname: 'Bowman' };
Object.defineProperty(person, 'age', { enumerable: false, value: 25 });
console.log(person.age);      // 25
console.log({ ...person });   // { name: 'Dave', surname: 'Bowman' } -- no age!

// --- Spreading primitives in object context ---
console.log({ ...undefined }); // {}
console.log({ ...null });      // {}
console.log({ ...42 });        // {}
console.log({ ...'hi' });      // { '0': 'h', '1': 'i' }  -- string is iterable

// --- Shallow copy warning ---
const laptop = {
    name: 'MacBook Pro',
    screen: { size: 17, isRetina: true }
};
const laptopClone = { ...laptop };
console.log(laptop.screen === laptopClone.screen); // true -- SAME ref!

// Manual deep-spread for one level:
const laptopDeepClone = {
    ...laptop,
    screen: { ...laptop.screen }
};
console.log(laptop.screen === laptopDeepClone.screen); // false


// ============================================================
// 7. OBJECT SPREAD vs OBJECT.ASSIGN DIFFERENCES [INTERMEDIATE]
// ============================================================
//
// INTERVIEW: Both copy own enumerable properties, but differ in edge cases.
//
// +-----------------------------------+------------------+------------------+
// | Feature                           | { ...src }       | Object.assign    |
// +-----------------------------------+------------------+------------------+
// | Mutates target                    | No (new object)  | YES (1st arg)    |
// | Triggers setters on target        | No               | YES              |
// | Can set prototype                 | No               | No               |
// | Copies property descriptors       | No (values only) | No (values only) |
// | Works with non-objects as source  | Wraps/ignores    | Wraps/ignores    |
// | Can be used in expressions        | Yes              | Yes (returns)    |
// | Syntax                            | Declarative      | Imperative       |
// +-----------------------------------+------------------+------------------+

// Key difference -- setters:
const target1 = {
    set name(val) { console.log('setter called:', val); }
};

Object.assign(target1, { name: 'Alice' });
// Logs: "setter called: Alice" -- setter IS triggered

const target2 = { ...target1, name: 'Bob' };
// Does NOT trigger setter -- spread creates a data property

// Key difference -- mutation:
const orig = { a: 1 };
const spreaded = { ...orig, b: 2 }; // orig unchanged
Object.assign(orig, { b: 2 });       // orig IS mutated
console.log(orig); // { a: 1, b: 2 }


// ============================================================
// 8. SPREAD IN FUNCTION CALLS                        [BASIC]
// ============================================================

// Spread replaces .apply() for passing arrays as arguments
const values = [3, 1, 4, 1, 5, 9];
console.log(Math.max(...values)); // 9

// Old way with .apply():
console.log(Math.max.apply(null, values)); // 9

// Push multiple items
const countries = ['Moldova', 'Ukraine'];
const others = ['USA', 'Japan'];
countries.push(...others);
console.log(countries); // ['Moldova', 'Ukraine', 'USA', 'Japan']

// Spread in constructor calls (impossible with .apply):
class King {
    constructor(name, country) {
        this.name = name;
        this.country = country;
    }
    getDescription() { return `${this.name} leads ${this.country}`; }
}
const details = ['Alexander the Great', 'Greece'];
const king = new King(...details);
console.log(king.getDescription()); // "Alexander the Great leads Greece"

// Combine spread with other args:
const nums3 = [1, 2];
const evens2 = [4, 8];
nums3.splice(0, 2, ...evens2, 0);
console.log(nums3); // [4, 8, 0]


// ============================================================
// 9. IMMUTABLE OBJECT UPDATES WITH SPREAD       [INTERMEDIATE]
// ============================================================

const book = {
    name: 'JavaScript: The Definitive Guide',
    author: 'David Flanagan',
    edition: 5,
    year: 2008
};

// Override specific fields (immutable update)
const newerBook = { ...book, edition: 6, year: 2011 };
console.log(newerBook.edition); // 6
console.log(book.edition);      // 5 (unchanged)

// Add a field
const withIsbn = { ...book, isbn: '978-1491952023' };

// Remove a field (destructure away + spread rest)
const { author, ...bookWithoutAuthor } = book;
console.log(bookWithoutAuthor);
// { name: 'JavaScript: The Definitive Guide', edition: 5, year: 2008 }


// ============================================================
// 10. DEEP NESTED UPDATES                       [INTERMEDIATE]
// ============================================================

const box = {
    color: 'red',
    size: { width: 200, height: 100 },
    items: ['pencil', 'notebook']
};

// Update nested object field
const biggerBox = {
    ...box,
    size: { ...box.size, height: 200 }
};
console.log(biggerBox.size); // { width: 200, height: 200 }
console.log(box.size);       // { width: 200, height: 100 } -- unchanged

// Update multiple nested levels + array
const blackBox = {
    ...box,
    color: 'black',
    size: { ...box.size, width: 400 },
    items: [...box.items, 'ruler']
};
console.log(blackBox);
// { color: 'black', size: { width: 400, height: 100 }, items: ['pencil', 'notebook', 'ruler'] }

// INTERVIEW: This gets verbose for deeply nested state.
// Libraries like Immer solve this with a "draft" proxy pattern.


// ============================================================
// 11. SPREAD WITH ITERABLES vs NON-ITERABLES    [INTERMEDIATE]
// ============================================================
//
// INTERVIEW: In ARRAY context, spread requires an iterable
// (Symbol.iterator). In OBJECT context, it works on any object.
//
// +-------------------------------+------------------+------------------+
// | Expression                    | Works?           | Why              |
// +-------------------------------+------------------+------------------+
// | [...[1,2]]                    | yes              | Array is iterable|
// | [..."abc"]                    | yes              | String is iter.  |
// | [...new Set([1,2])]          | yes              | Set is iterable  |
// | [...new Map([['a',1]])]      | yes              | Map is iterable  |
// | [...{a:1}]                    | NO -- TypeError  | Object not iter. |
// | {...{a:1}}                    | yes              | Object spread    |
// | {...[1,2]}                    | yes              | { '0':1, '1':2 }|
// | {...42}                       | yes              | {} (no own enum) |
// | {...null}                     | yes              | {} (null ignored)|
// +-------------------------------+------------------+------------------+

// Spread a generator (iterable)
function* range(start, end) {
    for (let i = start; i < end; i++) yield i;
}
console.log([...range(1, 5)]); // [1, 2, 3, 4]

// Spread a Map
const myMap = new Map([['x', 10], ['y', 20]]);
console.log([...myMap]); // [['x', 10], ['y', 20]]

// Object spread on an array
console.log({ ...[10, 20, 30] }); // { '0': 10, '1': 20, '2': 30 }

// GOTCHA: try { [...{}] } catch (e) { console.log(e.message); }
// "object is not iterable"


// ============================================================
// 12. ITERATION PROTOCOLS & CUSTOM ITERABLES    [ADVANCED]
// ============================================================

// Any object with [Symbol.iterator] method is iterable.
// Spread calls this method to get values.

const arrayLike = {
    0: 'Cat',
    1: 'Bird',
    length: 2,
    [Symbol.iterator]() {
        let index = 0;
        return {
            next: () => ({
                done: index >= this.length,
                value: this[index++]
            })
        };
    }
};
console.log([...arrayLike]); // ['Cat', 'Bird']

// String's built-in iterator handles Unicode correctly:
console.log([...'hello']); // ['h', 'e', 'l', 'l', 'o']

// INTERVIEW: Spread uses the iterable protocol, NOT .length.
// Array.from() also accepts array-likes (objects with .length)
// even without Symbol.iterator.
console.log(Array.from({ 0: 'a', 1: 'b', length: 2 })); // ['a', 'b']
// [...{ 0: 'a', 1: 'b', length: 2 }] // TypeError -- not iterable!


// ============================================================
// 13. PROTOTYPE PRESERVATION PITFALL            [ADVANCED]
// ============================================================

class Game {
    constructor(name) { this.name = name; }
    getMessage() { return `I like ${this.name}!`; }
}

const doom = new Game('Doom');
console.log(doom instanceof Game);  // true
console.log(doom.getMessage());     // "I like Doom!"

// Spread LOSES the prototype
const doomClone = { ...doom };
console.log(doomClone instanceof Game);  // false
// doomClone.getMessage();              // TypeError: not a function

// Fix: preserve prototype with Object.assign on a proper instance
const doomFull = Object.assign(new Game(), doom);
console.log(doomFull instanceof Game);   // true
console.log(doomFull.getMessage());      // "I like Doom!"

// Or (legacy, not recommended):
// const doomFull = { ...doom, __proto__: Game.prototype };


// ============================================================
// 14. PERFORMANCE CONSIDERATIONS                [ADVANCED]
// ============================================================
//
// +---------------------------------------------+----------+
// | Operation                                   | Speed    |
// +---------------------------------------------+----------+
// | { ...small }  (5 keys)                      | Fastest  |
// | Object.assign({}, small)                    | Fast     |
// | { ...large }  (1000+ keys)                  | Slower   |
// | [...smallArr] (10 items)                    | Fastest  |
// | [...largeArr] (100K items)                  | Moderate |
// | Array.from(largeArr)                        | Similar  |
// +---------------------------------------------+----------+
//
// Key performance insights:
//
// 1. AVOID spreading in hot loops:
//    BAD:  arr.reduce((acc, x) => [...acc, x], [])  // O(n^2)!
//    GOOD: arr.reduce((acc, x) => { acc.push(x); return acc; }, [])
//
// 2. For large objects, Object.assign can be slightly faster than
//    spread because spread creates an intermediate object.
//
// 3. Spread copies ALL own enumerable properties every time.
//    For partial updates on large objects, consider Immer which
//    uses structural sharing.
//
// 4. Rest parameters (...args) have negligible overhead vs arguments.
//    Prefer rest -- it's cleaner and produces a real Array.
//
// 5. Destructuring with rest ({ a, ...rest } = obj) creates a new
//    object on every call. In hot paths, manual property access
//    may be faster.

// INTERVIEW: "What's wrong with this code?"
// function flatten(arr) {
//     return arr.reduce((flat, item) =>
//         Array.isArray(item) ? [...flat, ...flatten(item)] : [...flat, item], []);
// }
// Answer: O(n^2) due to spreading into a new array each iteration.
// Fix: use flat.concat() or push into a mutable accumulator.


// ============================================================
// 15. GOTCHAS                                        [ALL]
// ============================================================

// GOTCHA 1: Rest must be LAST in destructuring.
//   const [a, ...mid, b] = [1,2,3,4]; // SyntaxError

// GOTCHA 2: Object spread is SHALLOW. Nested objects share refs.

// GOTCHA 3: Spread in object literal ignores prototype methods.
//   class Foo { bar() {} }
//   { ...new Foo() } // bar is NOT in the result

// GOTCHA 4: Spreading null/undefined in OBJECT context is OK ({}).
//   Spreading them in ARRAY context throws TypeError.
//   { ...null }  // {}
//   [...null]    // TypeError: null is not iterable

// GOTCHA 5: Property order -- later spread overwrites earlier keys.
//   { a: 1, ...{ a: 2 } }  // { a: 2 }

// GOTCHA 6: Spread does not copy non-enumerable properties.

// GOTCHA 7: Spread does not trigger setters (unlike Object.assign).

// GOTCHA 8: arguments is NOT available in arrow functions.
//   Use rest params (...args) instead.

// GOTCHA 9: Spreading a string in object context gives index keys.
//   { ..."abc" }  // { '0': 'a', '1': 'b', '2': 'c' }

// GOTCHA 10: Large spread chains (many objects) create intermediate
//   objects. For merging many sources, Object.assign(target, ...sources)
//   with a single target can be more efficient.


// ============================================================
// 16. COMPARISON TABLES                          [REFERENCE]
// ============================================================
//
// --- REST vs SPREAD at a glance ---
// +-----------------------+------------------------------+------------------------------+
// | Context               | REST (collects)              | SPREAD (expands)             |
// +-----------------------+------------------------------+------------------------------+
// | Function definition   | function f(a, ...rest) {}    | (N/A)                        |
// | Function call         | (N/A)                        | f(...args)                   |
// | Array destructuring   | const [a, ...rest] = arr     | (N/A)                        |
// | Array literal         | (N/A)                        | [...arr1, ...arr2]           |
// | Object destructuring  | const { a, ...rest } = obj   | (N/A)                        |
// | Object literal        | (N/A)                        | { ...obj1, ...obj2 }         |
// +-----------------------+------------------------------+------------------------------+
//
// --- Object Spread vs Object.assign ---
// (See detailed table in section 7 above)
//
// --- What can be spread where ---
// +------------------+--------------------+--------------------+
// | Source type       | In array [...]     | In object {...}    |
// +------------------+--------------------+--------------------+
// | Array            | yes                | yes (index keys)   |
// | String           | yes (chars)        | yes (index keys)   |
// | Set              | yes                | TypeError in {...} |
// | Map              | yes (entries)      | TypeError in {...} |
// | Generator        | yes                | TypeError in {...} |
// | Plain object     | TypeError          | yes                |
// | null/undefined   | TypeError          | {} (ignored)       |
// | Number/Boolean   | TypeError          | {} (ignored)       |
// +------------------+--------------------+--------------------+
