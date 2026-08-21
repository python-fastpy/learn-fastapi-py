// ============================================================
// JAVASCRIPT ITERABLES, ITERATORS & GENERATORS
// ULTIMATE QUICK-REFERENCE
// ============================================================
//
// PROTOCOL FLOW:
//
//   ┌─────────────┐       [Symbol.iterator]()     ┌──────────┐
//   │  Iterable    │ ─────────────────────────────► │ Iterator │
//   │  (object)    │                                │ (object) │
//   └─────────────┘                                └────┬─────┘
//                                                       │
//                                        .next()        │
//                                  ┌────────────────────┘
//                                  ▼
//                           ┌────────────┐
//                           │ IterResult  │
//                           │ { value,    │
//                           │   done }    │
//                           └────────────┘
//                      done:false → keep calling .next()
//                      done:true  → iteration complete
//
// ASYNC PROTOCOL (same shape, but with Promises):
//
//   ┌──────────────┐    [Symbol.asyncIterator]()   ┌──────────────┐
//   │ Async         │ ────────────────────────────► │ Async         │
//   │ Iterable      │                               │ Iterator      │
//   └──────────────┘                               └──────┬───────┘
//                                                         │
//                                         .next()         │
//                                  ┌──────────────────────┘
//                                  ▼
//                          Promise<{ value, done }>
//
//   Consumed with:  for await (const x of asyncIterable) { ... }
//
//
// BUILT-IN ITERABLES:
//   Array, String, Map, Set, TypedArray, arguments, NodeList,
//   Generator objects


// ============================================================
// 1. ITERATOR PROTOCOL                             [BASIC]
// ============================================================

// An iterator is any object with a next() method that returns
// { value: any, done: boolean }

let counter = 0;
let limit = 3;

const iteratorObjectProtocol = {
  next: function() {
    counter++;
    if (counter >= limit) return { value: undefined, done: true };
    return { value: counter, done: false };
  }
};

// Manual iteration:
// iteratorObjectProtocol.next(); // { value: 1, done: false }
// iteratorObjectProtocol.next(); // { value: 2, done: false }
// iteratorObjectProtocol.next(); // { value: undefined, done: true }


// ============================================================
// 2. ITERABLE PROTOCOL                             [BASIC]
// ============================================================

// An iterable implements [Symbol.iterator]() which returns an iterator.
// This lets it work with for...of, spread, destructuring, etc.

const myCustomObject = {
  [Symbol.iterator]: function() {
    return iteratorObjectProtocol;
  }
};
console.log(...myCustomObject);


// ============================================================
// 3. GENERATORS                                    [INTERMEDIATE]
// ============================================================

// A generator function (function*) returns a Generator object,
// which is both an iterator AND an iterable.

// --- Basic generator ---
const myCustomObject1 = {
  [Symbol.iterator]: function* () {
    yield 1;
    yield 2;
  }
};
console.log([...myCustomObject1]); // [1, 2]

// --- Generator function ---
function* GeneratorFun() {
  yield 1;
  yield 2;
}
const myFunc = GeneratorFun();
console.log(myFunc.next()); // { value: 1, done: false }
console.log(myFunc.next()); // { value: 2, done: false }
console.log(myFunc.next()); // { value: undefined, done: true }

// INTERVIEW: ".next() advances; yield pauses; return stops"
function* logGenerator() {
  console.log('running....');
  yield 'paused';
  console.log('running again....');
  return 'stopped';
}
let logger = logGenerator();
logger.next(); // logs "running...." => { value: 'paused', done: false }
logger.next(); // logs "running again...." => { value: 'stopped', done: true }


// ============================================================
// 4. GENERATORS ARE ITERABLE                       [INTERMEDIATE]
// ============================================================

function* abcs() {
  yield 'a';
  yield 'b';
  yield 'c';
}

for (let letter of abcs()) {
  console.log(letter.toUpperCase()); // A B C
}

[...abcs()]; // ["a", "b", "c"]

// Works with destructuring:
const [first, second] = abcs();
// first => 'a', second => 'b'


// ============================================================
// 5. PASSING VALUES INTO GENERATORS                [INTERMEDIATE]
// ============================================================
//
// ┌─────────────────────────────────────────────────────────┐
// │  gen.next(value) sends `value` INTO the generator.      │
// │  The value becomes the result of the `yield` expression │
// │  that the generator is currently paused at.             │
// │                                                         │
// │  FIRST .next() call starts the generator — any arg      │
// │  passed to it is IGNORED (nowhere to receive it).       │
// └─────────────────────────────────────────────────────────┘

function* add() {
  const num = yield;       // pauses, waits for value
  yield 2 + num;           // resumes with value, yields result
  yield 4 + num;
}

var gen = add();
gen.next();     // { value: undefined, done: false } — starts generator
gen.next(2);    // { value: 4, done: false }  — num = 2, yields 2+2
gen.next();     // { value: 6, done: false }  — yields 4+2
gen.next();     // { value: undefined, done: true }

// --- Extended example ---
function* calculator() {
  const num = yield;           // pause 1: receive num
  yield 2 + num;               // pause 2: yield 2+num
  const num1 = yield;          // pause 3: receive num1
  yield 4 + num1 + num;        // pause 4: yield 4+num1+num
}
var calc = calculator();
console.log(calc.next());       // { value: undefined, done: false }
console.log(calc.next(10));     // { value: 12, done: false }
console.log(calc.next());       // { value: undefined, done: false }
console.log(calc.next(20));     // { value: 34, done: false }


// ============================================================
// 6. yield* DELEGATION                             [INTERMEDIATE]
// ============================================================

// yield* delegates to another generator or iterable

function* outer() {
  yield 1;
  yield* inner();
  yield 2;
}
function* inner() {
  yield "a";
  yield "b";
}

let gen3 = outer();
gen3.next(); // { value: 1, done: false }
gen3.next(); // { value: "a", done: false }
gen3.next(); // { value: "b", done: false }
gen3.next(); // { value: 2, done: false }
gen3.next(); // { value: undefined, done: true }

// yield* works on any iterable:
// function* yieldArray() { yield* [10, 20, 30]; }
// [...yieldArray()]; // [10, 20, 30]


// ============================================================
// 7. CUSTOM ITERABLE FROM SCRATCH                  [INTERMEDIATE]
// ============================================================

// Making any object iterable with Symbol.iterator
function createIterator() {
  let step = 0;
  return {
    next: () => {
      step++;
      if (step <= 3) return { value: String(step), done: false };
      return { value: undefined, done: true };
    }
  };
}

const iterable6 = {};
iterable6[Symbol.iterator] = createIterator;
console.log(...iterable6); // "1" "2" "3"

for (let x of iterable6) {
  console.log(x); // "1", "2", "3"
}

// INTERVIEW: "What consumes the iterable protocol?"
// for...of, spread [...x], destructuring [a,b]=x,
// Array.from(x), new Map(x), new Set(x), Promise.all(x),
// yield* x


// ============================================================
// 8. BUILT-IN ITERABLES                            [BASIC]
// ============================================================

// Array
const arr = [1, 2, 3];
console.log("::", ...arr);

// String
console.log(..."abc"); // "a" "b" "c"

// Rest parameters (function argument spread)
function func(...args) {
  console.log(args);
}
func(1, 2, 4); // [1, 2, 4]

// All built-in iterables:
// Array.prototype[Symbol.iterator]
// String.prototype[Symbol.iterator]
// Map.prototype[Symbol.iterator]
// Set.prototype[Symbol.iterator]
// TypedArray.prototype[Symbol.iterator]
// arguments[Symbol.iterator]
// NodeList.prototype[Symbol.iterator]


// ============================================================
// 9. ASYNC ITERATORS & for-await-of                [ADVANCED]
// ============================================================
//
// ┌─────────────────────────────────────────────────────────┐
// │  ASYNC ITERATOR PROTOCOL:                               │
// │  - Implement [Symbol.asyncIterator]()                   │
// │  - .next() returns Promise<{ value, done }>             │
// │  - Consumed with: for await (const x of asyncIterable)  │
// └─────────────────────────────────────────────────────────┘

function wait(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// --- Custom async iterable ---
const asyncCountdown = {
  [Symbol.asyncIterator]() {
    let count = 3;
    return {
      async next() {
        await wait(100);
        if (count > 0) return { value: count--, done: false };
        return { value: undefined, done: true };
      }
    };
  }
};

// Usage:
// (async () => {
//   for await (const num of asyncCountdown) {
//     console.log(num); // 3, 2, 1 (with 100ms delay each)
//   }
// })();

// --- Async generator function ---
async function* asyncRange(start, end) {
  for (let i = start; i <= end; i++) {
    await wait(100);
    yield i;
  }
}

// (async () => {
//   for await (const num of asyncRange(1, 5)) {
//     console.log(num); // 1, 2, 3, 4, 5
//   }
// })();

// --- Practical example: paginated API fetch ---
// async function* fetchPages(baseUrl) {
//   let page = 1;
//   while (true) {
//     const response = await fetch(`${baseUrl}?page=${page}`);
//     const data = await response.json();
//     if (data.results.length === 0) return;
//     yield data.results;
//     page++;
//   }
// }
//
// for await (const pageResults of fetchPages('/api/items')) {
//   console.log('Got page:', pageResults);
// }


// ============================================================
// 10. ASYNC GENERATOR + yield                      [ADVANCED]
// ============================================================

const emoji = { one: '1', two: '2', three: '3' };

function random(max) {
  return Math.floor(Math.random() * Math.floor(max));
}

async function getName(request) {
  await wait(1000);
  return emoji[request];
}

async function* asyncGen() {
  yield getName(yield);
}

let gen1 = asyncGen();
gen1.next();                                           // starts generator
gen1.next('three').then(({ value }) => console.log(value)); // '3'


// ============================================================
// 11. INFINITE SEQUENCES                           [ADVANCED]
// ============================================================

// Generators enable lazy evaluation of infinite sequences
function* fibonacci() {
  let [a, b] = [0, 1];
  while (true) {
    yield a;
    [a, b] = [b, a + b];
  }
}

// Take first N values from an infinite generator
function take(n, iterable) {
  const result = [];
  for (const val of iterable) {
    result.push(val);
    if (result.length >= n) break;
  }
  return result;
}

// take(10, fibonacci()) => [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]

function* naturals() {
  let n = 1;
  while (true) yield n++;
}
// take(5, naturals()) => [1, 2, 3, 4, 5]


// ============================================================
// COMPARISON TABLE                                 [ALL LEVELS]
// ============================================================
//
// ┌─────────────────┬──────────────────────────────────────────┐
// │ Concept         │ Key Points                               │
// ├─────────────────┼──────────────────────────────────────────┤
// │ Iterable        │ Has [Symbol.iterator]() method            │
// │                 │ Can be used with for..of, spread, etc.    │
// ├─────────────────┼──────────────────────────────────────────┤
// │ Iterator        │ Has .next() returning {value, done}       │
// │                 │ Stateful — tracks current position        │
// ├─────────────────┼──────────────────────────────────────────┤
// │ Generator fn    │ function* with yield                      │
// │                 │ Returns a Generator (iterator+iterable)   │
// │                 │ Lazy evaluation, can be infinite           │
// ├─────────────────┼──────────────────────────────────────────┤
// │ Async Iterable  │ Has [Symbol.asyncIterator]() method       │
// │                 │ .next() returns Promise<{value, done}>    │
// │                 │ Consumed with for await...of              │
// ├─────────────────┼──────────────────────────────────────────┤
// │ Async Generator │ async function* with yield                │
// │                 │ Can use await inside, yields promises     │
// └─────────────────┴──────────────────────────────────────────┘


// ============================================================
// GOTCHAS                                          [ALL LEVELS]
// ============================================================
//
// 1. Generators are one-time-use:
//      const g = abcs();
//      [...g]; // ['a','b','c']
//      [...g]; // [] — exhausted! Must call abcs() again.
//
// 2. for...of ignores the last `return` value:
//      function* f() { yield 1; return 2; }
//      [...f()]; // [1] — NOT [1, 2]
//      But: f().next() after yield 1 gives {value:2, done:true}
//
// 3. Don't override Array.prototype[Symbol.iterator] in production!
//      It breaks ALL array iteration, destructuring, spread, etc.
//
// 4. First .next(value) argument is discarded:
//      function* g() { const x = yield; yield x; }
//      const it = g();
//      it.next(999); // 999 is IGNORED — no yield to receive it
//      it.next(42);  // { value: 42, done: false }
//
// 5. for await...of only works inside async functions
//
// 6. Plain objects are NOT iterable by default:
//      for (const x of {a:1}) {} // TypeError
//      Must implement [Symbol.iterator] or use Object.entries()
//
// 7. yield is not allowed in arrow functions:
//      const g = *() => { yield 1; } // SyntaxError
//      Must use: const g = function*() { yield 1; }
//
// 8. .return() and .throw() on generators:
//      gen.return(value) — forces generator to finish
//      gen.throw(error)  — throws error inside generator at yield point
