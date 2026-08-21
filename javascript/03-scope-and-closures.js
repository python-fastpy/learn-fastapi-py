// ============================================================
//  SCOPE & CLOSURES - ULTIMATE QUICK REFERENCE
// ============================================================
//  Scope  = the accessibility/visibility of variables.
//  Closure = a function that remembers variables from its
//            outer (lexical) scope, even after the outer
//            function has returned.
//
//  Closures are built ON TOP of scope rules, so we cover
//  scope first, then closures.
//
//  Ref: https://dmitripavlutin.com/javascript-scope-gotchas/
//       https://dmitripavlutin.com/javascript-closure/
//       https://dmitripavlutin.com/javascript-closures-interview-questions/
// ============================================================


// ============================================================
//  TABLE OF CONTENTS
// ============================================================
//
//  PART 1 - SCOPE
//  ---------------------------------------------------------------
//   1.  Block Scope                                       [BASIC]
//   2.  Function Scope                                    [BASIC]
//   3.  Global Scope                                      [BASIC]
//   4.  Nested Scopes                                     [BASIC]
//   5.  Module Scope                                [INTERMEDIATE]
//   6.  Lexical (Static) Scope                      [INTERMEDIATE]
//   7.  Implicit Globals (var Gotcha)               [INTERMEDIATE]
//   8.  Variable Isolation                          [INTERMEDIATE]
//   9.  Scope Chain Lookup                          [INTERMEDIATE]
//  10.  Shadowing                                   [INTERMEDIATE]
//  11.  Scope Gotchas & Interview Traps
//
//  PART 2 - CLOSURES
//  ---------------------------------------------------------------
//  12.  Basic Closure                                     [BASIC]
//  13.  Closure After Return                              [BASIC]
//  14.  Closures in Event Handlers                  [INTERMEDIATE]
//  15.  Closures in Callbacks                       [INTERMEDIATE]
//  16.  Closure with Function Parameters            [INTERMEDIATE]
//  17.  Currying / Functional Programming           [INTERMEDIATE]
//  18.  Data Privacy / Encapsulation                [INTERMEDIATE]
//  19.  Factory Functions with Closures             [INTERMEDIATE]
//  20.  IIFE (Immediately Invoked Function Expr.)   [INTERMEDIATE]
//  21.  The Classic for-Loop Trap                   [INTERMEDIATE]
//  22.  Module Pattern                                [ADVANCED]
//  23.  Memoization with Closures                     [ADVANCED]
//  24.  Partial Application                           [ADVANCED]
//  25.  Memory / Garbage Collection Implications      [ADVANCED]
//  26.  Closure Gotchas & Interview Traps


// ############################################################
//                     PART 1 - SCOPE
// ############################################################


// ============================================================
//  SCOPE CHAIN DIAGRAM
// ============================================================
//
//  When a variable is accessed, the engine walks UP the scope chain:
//
//  +----------------------------------------------------+
//  |  GLOBAL SCOPE                                      |
//  |    var c = 1000;   (also on `window` object)       |
//  |  +----------------------------------------------+  |
//  |  |  FUNCTION SCOPE (run4)                       |  |
//  |  |    const message = "run in forest";          |  |
//  |  |  +----------------------------------------+  |  |
//  |  |  |  BLOCK SCOPE (if)                      |  |  |
//  |  |  |    const friend = "Bubba";             |  |  |
//  |  |  |    console.log(message); // found in   |  |  |
//  |  |  |    // parent function scope            |  |  |
//  |  |  +----------------------------------------+  |  |
//  |  |  // console.log(friend); // ReferenceError|  |  |
//  |  +----------------------------------------------+  |
//  +----------------------------------------------------+
//
//  Resolution: inner block -> function -> ... -> global
//  If not found in any scope -> ReferenceError


// ============================================================
//  VARIABLE LIFECYCLE DIAGRAM
// ============================================================
//
//  var:
//  +-------------+   +-----------------+   +------------+
//  | Declaration |-->| Initialization  |-->| Assignment |
//  | (hoisted)   |   | (= undefined)   |   | (= value)  |
//  +-------------+   +-----------------+   +------------+
//        ^ happens at creation phase          ^ at = line
//
//  let / const:
//  +-------------+   +-----------------+   +------------+
//  | Declaration |   | Initialization  |-->| Assignment |
//  | (hoisted)   |   | (exit TDZ)      |   | (= value)  |
//  +-------------+   +-----------------+   +------------+
//        ^                  ^
//  creation phase      at source line (TDZ between these)
//
//  function declaration:
//  +-------------+   +-----------------+   +------------+
//  | Declaration |-->| Initialization  |-->| Assignment |
//  | (hoisted)   |   | (= function)    |   | (complete) |
//  +-------------+   +-----------------+   +------------+
//        ^ ALL happen at creation phase (fully hoisted)


// ============================================================
//  SCOPE TYPE COMPARISON TABLE
// ============================================================
//
//  JavaScript has 4 scope types: Global, Function, Block, Module.
//
//  +---------------+----------+-----+-------+----------+
//  | SCOPE TYPE    | var      | let | const | function |
//  +---------------+----------+-----+-------+----------+
//  | Global        | window   | no  | no    | window*  |
//  | Function      | scoped   |scoped|scoped| scoped   |
//  | Block (if/for)| leaks!   |scoped|scoped| varies** |
//  | Module        | scoped   |scoped|scoped| scoped   |
//  +---------------+----------+-----+-------+----------+
//  *  function declarations become window properties in global scope
//  ** block-scoped in strict mode, function-scoped in sloppy mode


// ============================================================
// 1. BLOCK SCOPE                                      [BASIC]
// ============================================================
// let and const are block-scoped. var is NOT.

let a = 10;      // script scope (similar to global for let/const)
const b = 100;   // script scope
var c = 1000;    // global scope (goes on window)
console.log(a);

if (true) {
  const message = "hello"; // block-scoped, only accessible inside this if
  console.log(message, b); // "hello", 100
}
// console.log(message); // ReferenceError

// Each block creates its own scope:
for (const color of ['green', 'red', 'blue']) {
  const message = "hi"; // separate block from the `if` above
}

// Nested blocks:
{
  {
    let message = "hello first block";
    console.log(message); // "hello first block"
  }
  let message = "hello block"; // different block, no conflict
  console.log(message);        // "hello block"
}

// var LEAKS out of blocks:
if (true) {
  var count = 0;
  console.log(count); // 0
}
console.log(count);    // 0 -- var ignores block scope!


// ============================================================
// 2. FUNCTION SCOPE                                   [BASIC]
// ============================================================
// All declarations (var, let, const) are scoped to the function.
// var is ONLY scoped to functions (not blocks).

function run() {
  var message = "Run in Forest"; // function-scoped
  console.log(message);
}
run();
// console.log(message); // ReferenceError

// Nested function scopes:
function run2() {
  const two = 2;
  let one = 1;
  function run3() {
    var messagerun3 = "123"; // scoped to run3
    let messagelet = "let";  // scoped to run3
  }
  run3();
  console.log(two);  // 2
  console.log(one);  // 1
  console.log(run3); // [Function: run3]
  // console.log(messagerun3); // ReferenceError
}
run2();

// Function parameters are scoped to the function:
// function a(name) {
//   // `name` behaves like: let name = <passed value>;
//   // scoped to this function
// }


// ============================================================
// 3. GLOBAL SCOPE                                     [BASIC]
// ============================================================
// The outermost scope. Accessible from any inner scope.
// var and function declarations in global scope become window properties.
// let, const, and class do NOT become window properties.

var globalVar = "I'm on window";
let globalLet = "I'm NOT on window";
// console.log(window.globalVar);  // "I'm on window"
// console.log(window.globalLet);  // undefined


// ============================================================
// 4. NESTED SCOPES                                    [BASIC]
// ============================================================
// Inner scopes can access outer scope variables, not vice versa.

function run4() {
  const message = "run in forest";

  if (true) {
    const friend = 'Bubba';
    console.log(message); // "run in forest" (from outer scope)
  }
  // console.log(friend); // ReferenceError (block-scoped)
}
run4();


// ============================================================
// 5. MODULE SCOPE                               [INTERMEDIATE]
// ============================================================
// ES modules create their own scope. Nothing leaks by default.

// circle.js
const pi = 3.14159;
console.log(pi); // 3.14159 (accessible within module)

// main.js
// import './circle';
// console.log(pi); // ReferenceError (pi is private to circle.js)

// Only `export`ed bindings are accessible to importers.
// Module scope protects internal details.


// ============================================================
// 6. LEXICAL (STATIC) SCOPE                     [INTERMEDIATE]
// ============================================================
// INTERVIEW: "What is lexical scope?"
// Scope is determined by WHERE functions are WRITTEN, not where they are called.
// This is the foundation that makes closures possible.

function outerFun() {
  let outerValue = 'I am outside value';

  function innerFunc() {
    console.log(outerValue); // accesses outer via lexical scope
  }
  return innerFunc;
}

const inner = outerFun();
inner(); // "I am outside value" (lexical scope preserved -- this IS a closure)


// ============================================================
// 7. IMPLICIT GLOBALS (var GOTCHA)              [INTERMEDIATE]
// ============================================================
// INTERVIEW: "What happens with `let b = c = d = 100` inside a function?"

// function a() {
//   var e = 300;           // local to a()
//   let b = c = d = 100;  // b is local, BUT c and d are GLOBAL!
//   // Because c = d = 100 is assignment without declaration.
//   // Only `b` has the `let` keyword.
// }
// a();
// console.log(c); // 100 (leaked to global!)
// console.log(d); // 100 (leaked to global!)
// console.log(b); // ReferenceError (properly scoped)


// ============================================================
// 8. VARIABLE ISOLATION                         [INTERMEDIATE]
// ============================================================
// Different scopes can have variables with the same name without collision.

function foo() {
  let count = 0;
  console.log(count); // 0
}
function bar() {
  let count = 1;
  console.log(count); // 1
}
foo();
bar();
// Each function has its own `count`. No conflict.


// ============================================================
// 9. SCOPE CHAIN LOOKUP                         [INTERMEDIATE]
// ============================================================
// INTERVIEW: "How does JavaScript resolve variables?"
//
//  SCOPE CHAIN LOOKUP:
//  +---------------------+
//  | 1. Current scope    | <-- check here first
//  +---------------------+
//           |
//  +---------------------+
//  | 2. Parent scope     | <-- if not found, go up
//  +---------------------+
//           |
//  +---------------------+
//  | 3. Grandparent...   |
//  +---------------------+
//           |
//  +---------------------+
//  | N. Global scope     | <-- last resort
//  +---------------------+
//           |
//     ReferenceError!       <-- if not found anywhere

let globalX = "global";
function outer() {
  let outerX = "outer";
  function middle() {
    let middleX = "middle";
    function inner() {
      // Looks up: inner scope -> middle -> outer -> global
      console.log(middleX, outerX, globalX); // "middle", "outer", "global"
    }
    inner();
  }
  middle();
}
outer();


// ============================================================
// 10. SHADOWING                                 [INTERMEDIATE]
// ============================================================
// INTERVIEW: "What is variable shadowing?"

let shadow = "outer";
function shadowDemo() {
  let shadow = "inner";       // shadows the outer `shadow`
  console.log(shadow);        // "inner"

  if (true) {
    let shadow = "block";    // shadows the function `shadow`
    console.log(shadow);      // "block"
  }
  console.log(shadow);        // "inner" (block shadow is gone)
}
shadowDemo();
console.log(shadow);          // "outer" (untouched)


// ============================================================
// 11. SCOPE GOTCHAS & INTERVIEW TRAPS
// ============================================================

// GOTCHA: Function declarations in blocks (sloppy mode)
{
  function hello() {
    let message = "hello";
    console.log(message);
  }
}
hello(); // Works in sloppy mode! (function declarations leak from blocks)
// In strict mode, this would throw ReferenceError.

// GOTCHA: Parameter default values have their own scope
let p = 1;
// function myFunc(p = p + 1) { return p; }
// myFunc(); // ReferenceError!
// The parameter `p` shadows the outer `p`, but `p + 1` tries to use
// the parameter `p` before it's initialized -> TDZ!

// FIX: Use a different name
function myFunc(q = p + 1) { return q; }
myFunc(); // 2  (uses outer `p` since `q` doesn't shadow it)

// GOTCHA: var does not respect block scope
for (var i = 0; i < 5; i++) { /* ... */ }
console.log(i); // 5 -- leaked!

// GOTCHA: Undeclared assignments create globals (sloppy mode)
function leaky() {
  oops = "I'm global now!"; // no var/let/const -> implicit global
}
leaky();
// console.log(window.oops); // "I'm global now!" -- accidental global!

// GOTCHA: let/const in for loops create new bindings per iteration
// (see Section 21 for the full for-loop closure trap and fixes)
for (let i = 0; i < 3; i++) {
  setTimeout(() => console.log(i), 0); // 0, 1, 2 (each iteration has its own i)
}
for (var i = 0; i < 3; i++) {
  setTimeout(() => console.log(i), 0); // 3, 3, 3 (shared i)
}


// ############################################################
//                    PART 2 - CLOSURES
// ############################################################


// ============================================================
//  HOW CLOSURES WORK (Memory Diagram)
// ============================================================
//
//  function outer() {
//    let count = 0;                // lives in outer's scope
//    return function inner() {     // inner "closes over" count
//      return ++count;
//    };
//  }
//  const fn = outer();
//  fn(); // 1
//  fn(); // 2
//
//  MEMORY:
//  +---------------------+
//  | Global Scope        |
//  |  fn ──────────────────────> [Function: inner]
//  +---------------------+              |
//                                       | [[Scope]] (closure)
//                                       v
//                              +------------------+
//                              | Closure Scope    |
//                              |  count: 0 -> 1   |
//                              |  -> 2 -> 3 ...   |
//                              +------------------+
//
//  Even though outer() has returned, `count` is NOT garbage
//  collected because `inner` still holds a reference to it
//  via the closure.
//
//  GARBAGE COLLECTION:
//  When `fn` is set to null or goes out of scope, the closure
//  scope (including `count`) becomes eligible for GC.
//  fn = null; // now the closure and `count` can be freed


// ============================================================
// 12. BASIC CLOSURE - Nested Scope Access               [BASIC]
// ============================================================
// INTERVIEW: "What is a closure?"
// A closure is a function bundled with its lexical environment.
// Every function that accesses a variable from an outer scope
// is technically a closure.

const myGlobal = 0;

function myFunction() {
  const myVar = 1;
  console.log(myGlobal); // 0 (accesses outer scope)

  function innerOfFunction() {
    const myInnerVar = 2;
    console.log(myVar, myInnerVar); // 1, 2

    function innerOfInnerFunction() {
      console.log(myInnerVar, myVar, myGlobal); // 2, 1, 0
    }
    innerOfInnerFunction();
  }
  innerOfFunction();
}
myFunction();

//  SCOPE CHAIN:
//  innerOfInnerFunction
//    --> innerOfFunction (myInnerVar)
//      --> myFunction (myVar)
//        --> Global (myGlobal)


// ============================================================
// 13. CLOSURE AFTER RETURN                              [BASIC]
// ============================================================
// The defining characteristic: accessing outer vars after outer returns.

function outerFunction() {
  let outerVar = "outer var";

  function innerFunction() {
    console.log(outerVar); // still accessible!
  }
  return innerFunction;
}

let outerRef = outerFunction();  // outerFunction returns, stack frame gone
outerRef();                      // "outer var" -- closure keeps outerVar alive


// ============================================================
// 14. CLOSURES IN EVENT HANDLERS                [INTERMEDIATE]
// ============================================================

// let countClicked = 0;
// myButton.addEventListener('click', function handleClick() {
//   countClicked++;
//   myText.innerText = `You clicked ${countClicked} times`;
// });
// handleClick closes over countClicked and myText.


// ============================================================
// 15. CLOSURES IN CALLBACKS                     [INTERMEDIATE]
// ============================================================

let message4 = "hello world123";
setTimeout(function callback() {
  console.log(message4); // closure captures message4
}, 1000);

let countEven = 0;
const items = [1, 5, 100, 10];
items.forEach(function iterator(number) {
  if (number % 2 === 0) countEven++; // closure captures countEven
});
console.log(countEven); // 2


// ============================================================
// 16. CLOSURE WITH FUNCTION PARAMETERS          [INTERMEDIATE]
// ============================================================
// Parameters live in the closure scope, just like local variables.

function counter(c = 100) {
  let count = 0;
  count++;
  c++;
  console.log("~~~~~~", count); // 1

  function innerFunction() {
    console.log("~", c, count); // 101, 1
  }
  innerFunction();
}
counter();


// ============================================================
// 17. CURRYING / FUNCTIONAL PROGRAMMING         [INTERMEDIATE]
// ============================================================
// INTERVIEW: "Explain currying with closures."

function multiply(a) {
  return function executeMultiply(b) {
    return a * b;  // `a` is captured in the closure
  };
}

const double = multiply(2);
double(3); // 6
double(5); // 10

// Generalized curry helper [ADVANCED]:
function curry(fn) {
  return function curried(...args) {
    if (args.length >= fn.length) return fn(...args);
    return (...moreArgs) => curried(...args, ...moreArgs);
  };
}
const add = curry((a, b, c) => a + b + c);
add(1)(2)(3);    // 6
add(1, 2)(3);    // 6
add(1)(2, 3);    // 6


// ============================================================
// 18. DATA PRIVACY / ENCAPSULATION              [INTERMEDIATE]
// ============================================================
// INTERVIEW: "How do closures enable private variables?"
// Ref: https://dmitripavlutin.com/javascript-closure/#54-encapsulation

function createCounter(initial = 0) {
  let count = initial;   // private - inaccessible from outside

  return {
    increment() { return ++count; },
    decrement() { return --count; },
    getCount()  { return count; },
    // No setCount -- truly private!
  };
}

const myCounter = createCounter(10);
myCounter.increment(); // 11
myCounter.increment(); // 12
myCounter.getCount();  // 12
// myCounter.count;    // undefined -- cannot access directly!


// ============================================================
// 19. FACTORY FUNCTIONS WITH CLOSURES           [INTERMEDIATE]
// ============================================================

function createPerson(name, age) {
  // `name` and `age` are closed over
  return {
    getName()  { return name; },
    getAge()   { return age; },
    greet()    { return `Hi, I'm ${name}, ${age} years old.`; },
    birthday() { age++; }   // mutates the closed-over variable
  };
}

const alice = createPerson("Alice", 30);
alice.greet();    // "Hi, I'm Alice, 30 years old."
alice.birthday();
alice.getAge();   // 31


// ============================================================
// 20. IIFE (Immediately Invoked Function Expr.) [INTERMEDIATE]
// ============================================================
// Classic closure pattern for creating private scope.
// Before ES6 block scoping, IIFEs were the primary way to
// avoid polluting the global namespace.

const module = (function() {
  let privateVar = 0;
  return {
    increment() { return ++privateVar; },
    getVal()    { return privateVar; }
  };
})();
module.increment(); // 1
module.increment(); // 2
// privateVar is inaccessible from outside

// IIFE also used as pre-ES6 block scope alternative:
(function() {
  var private = "can't touch this";
})();
// console.log(private); // ReferenceError


// ============================================================
// 21. THE CLASSIC for-LOOP TRAP                 [INTERMEDIATE]
// ============================================================
// INTERVIEW: "What does this code output? How do you fix it?"

for (var i = 0; i < 3; i++) {
  setTimeout(function log() {
    console.log(i); // 3, 3, 3  (all reference the SAME `i`)
  }, 1000);
}
// After the loop, i = 3. All three callbacks share the same `i`.

// FIX 1: Use `let` (creates new binding per iteration)
for (let i = 0; i < 3; i++) {
  setTimeout(() => console.log(i), 1000); // 0, 1, 2
}

// FIX 2: IIFE (creates new scope per iteration)
for (var i = 0; i < 3; i++) {
  (function(j) {
    setTimeout(() => console.log(j), 1000); // 0, 1, 2
  })(i);
}

// FIX 3: Third argument to setTimeout
for (var i = 0; i < 3; i++) {
  setTimeout((j) => console.log(j), 1000, i); // 0, 1, 2
}


// ============================================================
// 22. MODULE PATTERN                              [ADVANCED]
// ============================================================
// INTERVIEW: "Explain the module pattern."
// Before ES6 modules, closures were THE way to create private scope.

const UserModule = (function() {
  // Private variables (hidden in closure)
  let users = [];
  let nextId = 1;

  // Private function
  function validateName(name) {
    return typeof name === 'string' && name.length > 0;
  }

  // Public API (returned object)
  return {
    addUser(name) {
      if (!validateName(name)) throw new Error('Invalid name');
      const user = { id: nextId++, name };
      users.push(user);
      return user;
    },
    getUser(id) {
      return users.find(u => u.id === id);
    },
    getUserCount() {
      return users.length;
    }
  };
})();

UserModule.addUser("Alice");   // { id: 1, name: "Alice" }
UserModule.getUserCount();     // 1
// UserModule.users;           // undefined (private!)
// UserModule.validateName;    // undefined (private!)


// ============================================================
// 23. MEMOIZATION WITH CLOSURES                   [ADVANCED]
// ============================================================
// INTERVIEW: "Implement memoization using closures."

function memoize(fn) {
  const cache = {};  // closed over -- persists between calls
  return function(...args) {
    const key = JSON.stringify(args);
    if (key in cache) {
      console.log('Cache hit');
      return cache[key];
    }
    console.log('Computing');
    const result = fn(...args);
    cache[key] = result;
    return result;
  };
}

const expensiveAdd = memoize((a, b) => a + b);
expensiveAdd(1, 2); // "Computing" -> 3
expensiveAdd(1, 2); // "Cache hit"  -> 3


// ============================================================
// 24. PARTIAL APPLICATION                         [ADVANCED]
// ============================================================
// INTERVIEW: "What's the difference between currying and partial application?"

function partial(fn, ...presetArgs) {
  return function(...laterArgs) {
    return fn(...presetArgs, ...laterArgs);
  };
}

function greet(greeting, name) {
  return `${greeting}, ${name}!`;
}

const sayHello = partial(greet, "Hello");
sayHello("Alice"); // "Hello, Alice!"
sayHello("Bob");   // "Hello, Bob!"

// Currying: f(a)(b)(c) -- one arg at a time
// Partial:  f(a, b) --> g(c) -- fix some args, pass rest later


// ============================================================
// 25. MEMORY / GARBAGE COLLECTION IMPLICATIONS    [ADVANCED]
// ============================================================
// INTERVIEW: "Can closures cause memory leaks?"
//
//  MEMORY DIAGRAM:
//  +--------------------------------------------------+
//  |  function createHeavy() {                        |
//  |    const bigData = new Array(1000000).fill('x');  |
//  |    return function() {                            |
//  |      return bigData.length;  // bigData held!     |
//  |    };                                             |
//  |  }                                               |
//  |  let heavy = createHeavy(); // bigData in memory  |
//  |  heavy = null;  // NOW bigData can be GC'd        |
//  +--------------------------------------------------+
//
//  KEY RULES:
//  1. A closure keeps ALL variables in its scope alive,
//     not just the ones it references (engine-dependent).
//  2. Modern engines (V8) optimize: only keep referenced vars.
//  3. Closures in long-lived objects (event handlers, timers,
//     global refs) can prevent GC of large data.
//
//  PATTERNS TO AVOID LEAKS:

// BAD: Unnecessary closure over large data
function processData() {
  const hugeArray = new Array(1000000).fill('data');
  const result = hugeArray.length;
  // Return closure that still holds hugeArray reference
  return function() { return hugeArray.length; }; // leak!
}

// GOOD: Extract what you need, let the rest be GC'd
function processDataFixed() {
  const hugeArray = new Array(1000000).fill('data');
  const length = hugeArray.length; // extract the value
  // hugeArray is no longer referenced in the closure
  return function() { return length; }; // clean
}

// CLEANUP PATTERN: Remove references when done
// const handler = () => { /* uses closedVar */ };
// element.addEventListener('click', handler);
// // Later:
// element.removeEventListener('click', handler);


// ============================================================
// 26. CLOSURE GOTCHAS & INTERVIEW TRAPS
// ============================================================

// GOTCHA: Closures capture by REFERENCE, not by VALUE
function createFunctions() {
  let val = 1;
  const fn = () => val;
  val = 2;        // mutated AFTER closure created
  return fn;
}
console.log(createFunctions()()); // 2 (not 1!)

// GOTCHA: var in for loop (see Section 21)
// All callbacks share the same `i` because var is function-scoped.

// GOTCHA: Stale closures (common in React hooks)
// function Component() {
//   const [count, setCount] = useState(0);
//   useEffect(() => {
//     setInterval(() => console.log(count), 1000); // always logs 0!
//   }, []);
//   // The interval callback closes over the initial `count`.
// }

// GOTCHA: Closures in loops with objects
const funcs = [];
for (var k = 0; k < 3; k++) {
  funcs.push({ fn: () => k });
}
console.log(funcs[0].fn()); // 3 (not 0!)
console.log(funcs[1].fn()); // 3 (not 1!)

// GOTCHA: Closures and `this`
// Closures capture variables, NOT `this`.
// `this` depends on how the function is CALLED, not where defined.
// Arrow functions are the exception -- they capture `this` lexically.

// GOTCHA: Multiple closures share the same scope
function shared() {
  let x = 0;
  return {
    inc: () => ++x,
    dec: () => --x,
    get: () => x
  };
}
const s = shared();
s.inc(); s.inc(); s.dec();
s.get(); // 1 (all three share the same `x`)
