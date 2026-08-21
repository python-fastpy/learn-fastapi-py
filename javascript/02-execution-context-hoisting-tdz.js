// ============================================================
//  EXECUTION CONTEXT, HOISTING & TEMPORAL DEAD ZONE
//  ULTIMATE QUICK REFERENCE
// ============================================================
//  Ref: https://www.borderlessengineer.com/post/understanding-the-execution-context-in-javascript
//       https://www.borderlessengineer.com/post/how-js-works-lexical-environment
//       https://dmitripavlutin.com/javascript-variables-and-temporal-dead-zone/
// ============================================================
//
//  TABLE OF CONTENTS
//
//  PART I: EXECUTION CONTEXT (The Big Picture)
//   1.  Three Types of Execution Context ................. [BASIC]
//   2.  Execution Context Lifecycle (Two Phases) ......... [BASIC]
//   3.  Execution Context Components ..................... [BASIC]
//   4.  The Call Stack (EC Stack) ........................ [BASIC]
//   5.  Global Execution Context ........................ [BASIC]
//   6.  Function Execution Context ...................... [BASIC]
//   7.  Nested Function ECs & Scope Chain ........... [INTERMEDIATE]
//   8.  Lexical Environment vs Variable Environment ... [ADVANCED]
//   9.  this Binding in Execution Context ........... [INTERMEDIATE]
//  10.  Closures and Execution Context .............. [INTERMEDIATE]
//  11.  Stack Overflow (Recursion Limit) ............... [ADVANCED]
//  12.  Event Loop and the Call Stack .................. [ADVANCED]
//  13.  Complete EC Walkthrough ........................ [ADVANCED]
//
//  PART II: HOISTING (What Happens During the Creation Phase)
//  14.  How Hoisting Works (+ Behavior Table) ........... [BASIC]
//  15.  Hoisting Visualized (ASCII) ..................... [BASIC]
//  16.  Hoisting in the Execution Context ........... [INTERMEDIATE]
//  17.  var Hoisting .................................... [BASIC]
//  18.  Function Declaration Hoisting ................... [BASIC]
//  19.  Function Expression vs Declaration .......... [INTERMEDIATE]
//  20.  let and const Hoisting ...................... [INTERMEDIATE]
//  21.  class Hoisting .............................. [INTERMEDIATE]
//  22.  Hoisting Edge Cases ........................... [ADVANCED]
//
//  PART III: TEMPORAL DEAD ZONE (The let/const Specific Behavior)
//  23.  What is TDZ (+ Visualization) ................... [BASIC]
//  24.  Why TDZ Exists .................................. [BASIC]
//  25.  Variable Lifecycle: var vs let vs const ...... [INTERMEDIATE]
//  26.  Basic TDZ Examples .............................. [BASIC]
//  27.  typeof in the TDZ ........................... [INTERMEDIATE]
//  28.  TDZ in Function Scope ....................... [INTERMEDIATE]
//  29.  TDZ in Blocks (if / for) .................... [INTERMEDIATE]
//  30.  TDZ with class .............................. [INTERMEDIATE]
//  31.  TDZ in Default Parameters ..................... [ADVANCED]
//  32.  TDZ in Switch Statements ...................... [ADVANCED]
//  33.  TDZ with Closures ............................. [ADVANCED]
//
//  GOTCHAS & INTERVIEW TRAPS (Combined) ............... [ALL]
// ============================================================


// ************************************************************
//  PART I: EXECUTION CONTEXT (The Big Picture)
// ************************************************************
//
//  An Execution Context (EC) is the environment in which
//  JavaScript code is evaluated and executed. Every time code
//  runs, it runs inside an execution context.
// ************************************************************


// ============================================================
// 1. THREE TYPES OF EXECUTION CONTEXT                   [BASIC]
// ============================================================
//
//  1. GLOBAL EXECUTION CONTEXT (GEC)
//     - Created when the script first loads
//     - Only ONE per program
//     - Creates the global object (window in browser, global in Node)
//     - Sets `this` to the global object
//
//  2. FUNCTION EXECUTION CONTEXT (FEC)
//     - Created each time a function is INVOKED
//     - Each function gets its own EC
//     - Has access to all variables in outer scopes (scope chain)
//
//  3. EVAL EXECUTION CONTEXT
//     - Created inside eval() calls (avoid using eval!)


// ============================================================
// 2. EXECUTION CONTEXT LIFECYCLE (Two Phases)           [BASIC]
// ============================================================
//
//  PHASE 1: CREATION PHASE
//  +-----------------------------------------------------+
//  | 1. Create the Variable Object (VO) / Environment    |
//  |    - Function arguments -> added to VO              |
//  |    - Function declarations -> hoisted fully          |
//  |    - var declarations -> hoisted, init to undefined  |
//  |    - let/const declarations -> hoisted, but NOT      |
//  |      initialized (enter Temporal Dead Zone)          |
//  |    - class declarations -> hoisted, NOT initialized  |
//  |    - Function expressions -> treated as var          |
//  |                                                     |
//  | 2. Create the Scope Chain                           |
//  |    - Current VO + all parent VOs                    |
//  |                                                     |
//  | 3. Determine `this` binding                         |
//  |    - Based on how the function is called            |
//  +-----------------------------------------------------+
//
//  PHASE 2: EXECUTION PHASE
//  +-----------------------------------------------------+
//  | - Code is executed line by line                     |
//  | - Variables are assigned their values               |
//  | - Functions are called (creating new ECs)           |
//  | - Expressions are evaluated                        |
//  | - let/const exit TDZ at their declaration line      |
//  +-----------------------------------------------------+


// ============================================================
// 3. EXECUTION CONTEXT COMPONENTS                       [BASIC]
// ============================================================
//
//  Each Execution Context contains:
//
//  +----------------------------------------------------------+
//  | EXECUTION CONTEXT                                        |
//  |                                                          |
//  | +------------------------+                               |
//  | | Variable Environment   |  var declarations, function   |
//  | | (VE)                   |  declarations, arguments      |
//  | +------------------------+                               |
//  |                                                          |
//  | +------------------------+                               |
//  | | Lexical Environment    |  let/const declarations,      |
//  | | (LE)                   |  block scoping, closures      |
//  | +------------------------+                               |
//  |                                                          |
//  | +------------------------+                               |
//  | | This Binding           |  `this` value, determined     |
//  | |                        |  by how function is called    |
//  | +------------------------+                               |
//  |                                                          |
//  | +------------------------+                               |
//  | | Outer Environment Ref  |  link to parent scope         |
//  | | (Scope Chain)          |  for variable lookup          |
//  | +------------------------+                               |
//  +----------------------------------------------------------+


// ============================================================
// 4. THE CALL STACK (EC Stack)                          [BASIC]
// ============================================================
// INTERVIEW: "Explain the call stack."
//
//  The engine uses a LIFO stack to manage execution contexts.
//
//  function first() {
//    second();
//  }
//  function second() {
//    third();
//  }
//  function third() {
//    console.log("hello");
//  }
//  first();
//
//  CALL STACK EVOLUTION:
//
//  Step 1        Step 2        Step 3        Step 4
//  +--------+    +--------+    +--------+    +--------+
//  |        |    |        |    | third  |    |        |
//  |        |    | second |    | second |    | second |
//  | first  |    | first  |    | first  |    | first  |
//  | Global |    | Global |    | Global |    | Global |
//  +--------+    +--------+    +--------+    +--------+
//   first()      second()      third()       third returns
//   called       called        called        popped
//
//  Step 5        Step 6        Step 7
//  +--------+    +--------+    +--------+
//  |        |    |        |    |        |
//  |        |    |        |    |        |
//  | first  |    |        |    |        |
//  | Global |    | Global |    | (empty)|
//  +--------+    +--------+    +--------+
//   second       first         Global EC
//   returns      returns       remains

function first() {
  console.log("first start");
  second();
  console.log("first end");
}
function second() {
  console.log("second start");
  third();
  console.log("second end");
}
function third() {
  console.log("third");
}
first();
// Output: first start -> second start -> third -> second end -> first end


// ============================================================
// 5. GLOBAL EXECUTION CONTEXT                          [BASIC]
// ============================================================
// Created automatically. Sets up the global object and `this`.

var globalVar = "I'm global";
// In the Global EC:
// - Variable Environment: { globalVar: undefined } (creation phase)
// - Then: { globalVar: "I'm global" } (execution phase)
// - this = window (browser) or globalThis


// ============================================================
// 6. FUNCTION EXECUTION CONTEXT                        [BASIC]
// ============================================================
// A new EC is created every time a function is called.

function greet(name) {
  var greeting = "Hello";
  return greeting + " " + name;
}

greet("Alice");

// When greet("Alice") is called, a new FEC is created:
//
// CREATION PHASE:
// +------------------------------------------+
// | FEC for greet                            |
// | Variable Object:                         |
// |   arguments: { 0: "Alice", length: 1 }  |
// |   name: "Alice"                          |
// |   greeting: undefined                    |
// | Scope Chain: [greetVO, globalVO]         |
// | this: window (or undefined in strict)    |
// +------------------------------------------+
//
// EXECUTION PHASE:
// +------------------------------------------+
// | greeting = "Hello"                       |
// | return "Hello Alice"                     |
// +------------------------------------------+


// ============================================================
// 7. NESTED FUNCTION ECs & SCOPE CHAIN          [INTERMEDIATE]
// ============================================================

var globalCount = 0;

function outer() {
  var outerCount = 1;

  function inner() {
    var innerCount = 2;
    console.log(globalCount, outerCount, innerCount); // 0, 1, 2
    // inner's scope chain: [innerVO, outerVO, globalVO]
  }

  inner();
}
outer();

// SCOPE CHAIN VISUALIZATION:
// inner() looks up variables:
//   innerCount -> found in innerVO
//   outerCount -> not in innerVO -> found in outerVO
//   globalCount -> not in innerVO -> not in outerVO -> found in globalVO


// ============================================================
// 8. LEXICAL ENVIRONMENT vs VARIABLE ENVIRONMENT  [ADVANCED]
// ============================================================
// INTERVIEW: "What's the difference between LE and VE?"
//
//  VARIABLE ENVIRONMENT:
//  - Stores var declarations and function declarations
//  - Created once per function/global EC
//  - Doesn't change structurally during execution
//
//  LEXICAL ENVIRONMENT:
//  - Stores let and const declarations
//  - Initially same as VE
//  - Changes when entering new blocks (if, for, {})
//  - Each block creates a new LE that chains to the outer one
//
//  EXAMPLE:
//  function foo() {
//    var a = 1;         // in VE
//    let b = 2;         // in LE
//    if (true) {
//      var c = 3;       // in VE (var ignores block)
//      let d = 4;       // in NEW LE (block-scoped)
//    }
//    // d is gone (LE for the block is discarded)
//    // c is still here (in VE)
//  }


// ============================================================
// 9. this BINDING IN EXECUTION CONTEXT          [INTERMEDIATE]
// ============================================================
// `this` is determined during the CREATION phase of the EC.
// See thisInfo.js for full `this` binding rules.

// Global EC: this = window (browser) / globalThis
console.log(this); // window or {}

// Function EC: depends on how called
function showThis() {
  console.log(this);
}
showThis();              // window (sloppy) or undefined (strict)

const obj = { showThis };
obj.showThis();          // obj (method invocation)

showThis.call({ x: 1 });// { x: 1 } (explicit binding)


// ============================================================
// 10. CLOSURES AND EXECUTION CONTEXT            [INTERMEDIATE]
// ============================================================

function makeCounter() {
  let count = 0;
  return function() {
    count++;
    return count;
  };
}

const counter = makeCounter();
counter(); // 1
counter(); // 2

// After makeCounter() returns:
// - Its EC is popped from the call stack
// - BUT the inner function's [[Scope]] still references
//   makeCounter's Variable Environment (where count lives)
// - This is WHY closures work: the LE is not garbage collected
//   as long as something references it

// EC STACK + CLOSURE DIAGRAM:
//
// makeCounter() called:
// +-------------------+
// | makeCounter EC    |
// |  count: 0         |---+
// | Global EC         |   |
// +-------------------+   |
//                         |
// makeCounter() returns:  |
// +-------------------+   |
// | Global EC         |   |
// |  counter: fn -------->+ (closure reference to count)
// +-------------------+
//
// counter() called:
// +-------------------+
// | anonymous fn EC   |
// |  [[Scope]] --------> count: 0 -> 1
// | Global EC         |
// +-------------------+


// ============================================================
// 11. STACK OVERFLOW (Recursion Limit)             [ADVANCED]
// ============================================================
// INTERVIEW: "What causes stack overflow?"
// Each function call creates a new EC on the stack.
// Too many nested calls -> stack overflow.

// function infinite() {
//   infinite(); // RangeError: Maximum call stack size exceeded
// }
// infinite();

// Typical limit: ~10,000-25,000 frames (engine-dependent).

// FIX: Use tail call optimization (strict mode, Safari only) or iteration.
function factorial(n, acc = 1) {
  if (n <= 1) return acc;
  return factorial(n - 1, n * acc); // tail call (last operation is the call)
}
// Or convert to iterative:
function factorialIter(n) {
  let result = 1;
  for (let i = 2; i <= n; i++) result *= i;
  return result;
}


// ============================================================
// 12. EVENT LOOP AND THE CALL STACK               [ADVANCED]
// ============================================================
// INTERVIEW: "How does the event loop relate to the call stack?"
//
//  +-------------------+     +------------------+
//  |   CALL STACK      |     |  CALLBACK QUEUE  |
//  |   (EC Stack)      |     | (Task Queue)     |
//  | +--------------+  |     | +-------------+  |
//  | | current EC   |  |     | | setTimeout  |  |
//  | +--------------+  |     | | callback    |  |
//  | | ...          |  |     | +-------------+  |
//  | +--------------+  |     | | click       |  |
//  | | Global EC    |  |     | | handler     |  |
//  | +--------------+  |     | +-------------+  |
//  +-------------------+     +------------------+
//           ^                         |
//           |    +------------------+ |
//           +----| EVENT LOOP       |<+
//                | (checks if stack |
//                |  is empty, then  |
//                |  dequeues next)  |
//                +------------------+
//
//  The event loop ONLY moves callbacks to the stack when
//  the call stack is EMPTY.

console.log("1");
setTimeout(() => console.log("2"), 0);
Promise.resolve().then(() => console.log("3"));
console.log("4");
// Output: 1, 4, 3, 2
// Microtasks (Promise) run before macrotasks (setTimeout)


// ============================================================
// 13. COMPLETE EC WALKTHROUGH                     [ADVANCED]
// ============================================================
// INTERVIEW: "Walk me through the execution of this code step by step."

var x = 10;
function foo(a) {
  var b = 20;
  function bar(c) {
    var d = 30;
    return a + b + c + d + x;
  }
  return bar(40);
}
var result = foo(50);
console.log(result); // 150

// STEP-BY-STEP:
//
// 1. Global EC created:
//    VE: { x: undefined, foo: function, result: undefined }
//    this: window
//
// 2. x = 10
//
// 3. foo(50) called -> new EC pushed:
//    FEC(foo):
//      VE: { a: 50, b: undefined, bar: function }
//      Scope Chain: [fooVE, globalVE]
//      this: window
//    b = 20
//
// 4. bar(40) called -> new EC pushed:
//    FEC(bar):
//      VE: { c: 40, d: undefined }
//      Scope Chain: [barVE, fooVE, globalVE]
//      this: window
//    d = 30
//    return 50 + 20 + 40 + 30 + 10 = 150
//
// 5. bar EC popped, foo returns 150
// 6. foo EC popped, result = 150
// 7. console.log(150)


// ************************************************************
//  PART II: HOISTING (What Happens During the Creation Phase)
// ************************************************************
//
//  Hoisting = the engine moves declarations to the top of their
//  scope during the CREATION phase of the execution context.
//  Only declarations are hoisted, NOT initializations.
// ************************************************************


// ============================================================
// 14. HOW HOISTING WORKS (+ Behavior Table)             [BASIC]
// ============================================================
// INTERVIEW: "Explain the hoisting behavior of each declaration type."
//
//  +---------------------+----------+-------------+--------+--------+-------------+
//  | Declaration         | Hoisted? | Initialized | Scope  | TDZ?   | Before decl.|
//  +---------------------+----------+-------------+--------+--------+-------------+
//  | var x = 5           | Yes      | undefined   | Func   | No     | undefined   |
//  | let x = 5           | Yes*     | NO (TDZ)    | Block  | Yes    | RefError    |
//  | const x = 5         | Yes*     | NO (TDZ)    | Block  | Yes    | RefError    |
//  | function foo() {}   | Yes      | Full body   | Func** | No     | works!      |
//  | var foo = function()| Yes      | undefined   | Func   | No     | undefined   |
//  | var foo = () => {}  | Yes      | undefined   | Func   | No     | undefined   |
//  | class Foo {}        | Yes*     | NO (TDZ)    | Block  | Yes    | RefError    |
//  | import x from 'm'  | Yes      | Full binding | Module | No***  | works       |
//  +---------------------+----------+-------------+--------+--------+-------------+
//  *  Hoisted to top of scope but NOT accessible until declaration
//     (Temporal Dead Zone). Accessing throws ReferenceError.
//  ** In strict mode / modules, function declarations are block-scoped.
//  *** Imports are live bindings, fully initialized before module body runs.


// ============================================================
// 15. HOISTING VISUALIZED (ASCII)                       [BASIC]
// ============================================================
//
//  WHAT YOU WRITE:             WHAT THE ENGINE SEES:
//  +---------------------+    +---------------------+
//  | console.log(a);     |    | var a;              |  <-- declaration hoisted
//  | console.log(b);     |    | function c() {      |  <-- entire function hoisted
//  | var a = 5;          |    |   return "hello";   |
//  | let b = 10;         |    | }                   |
//  | function c() {      |    | console.log(a);     |  --> undefined
//  |   return "hello";   |    | console.log(b);     |  --> ReferenceError (TDZ!)
//  | }                   |    | a = 5;              |  <-- assignment stays
//  +---------------------+    | let b = 10;         |  <-- b exits TDZ here
//                              +---------------------+


// ============================================================
// 16. HOISTING IN THE EXECUTION CONTEXT         [INTERMEDIATE]
// ============================================================
// INTERVIEW: "Walk through what the engine does with this code."
//
// This is where EC creation phase and hoisting meet:

console.log(a);      // undefined (var hoisted, initialized to undefined)
// console.log(b);   // ReferenceError (let is in TDZ)
console.log(fn());   // "hello" (function declaration fully hoisted)
// console.log(expr()); // TypeError (var expr = undefined, undefined())

var a = 10;
let b = 20;
function fn() { return "hello"; }
var expr = function() { return "world"; };

// CREATION PHASE of Global EC:
// +---------------------------------------------+
// | Variable Environment:                       |
// |   a: undefined         (var hoisted)        |
// |   fn: function() {...} (fully hoisted)      |
// |   expr: undefined      (var hoisted)        |
// | Lexical Environment:                        |
// |   b: <uninitialized>   (TDZ)                |
// +---------------------------------------------+


// ============================================================
// 17. var HOISTING                                      [BASIC]
// ============================================================

// var declarations are hoisted and initialized to undefined.
var num;
console.log(num); // undefined

function double(num) {
  console.log(myVariable); // undefined (hoisted, not yet assigned)
  var myVariable;
  return num * 2;
}
console.log(double(3)); // 6

// Equivalent to:
function double1(num) {
  var myVariable;               // hoisted to top of function
  console.log(myVariable);      // undefined
  return num * 2;
}
console.log(double1(3)); // 6

// var hoisting with initialization:
function sum1(a, b) {
  console.log(myString); // undefined (declaration hoisted, assignment not)
  var myString = 'Hello World';
  console.log(myString); // 'Hello World'
  return a + b;
}
console.log(sum1(16, 10)); // 26

// The engine sees it as:
function sum(a, b) {
  var myString;               // declaration moved to top
  console.log(myString);      // undefined
  myString = 'Hello World';   // assignment stays in place
  console.log(myString);      // 'Hello World'
  return a + b;
}
console.log(sum(16, 10)); // 26


// ============================================================
// 18. FUNCTION DECLARATION HOISTING                     [BASIC]
// ============================================================
// INTERVIEW: "Can you call a function before it's declared?"
// YES -- function declarations are FULLY hoisted (body and all).

console.log(equal(1, '1'));  // false  (called BEFORE declaration)
function equal(value1, value2) {
  return value1 === value2;
}

console.log(addition(4, 7)); // 11   (called BEFORE declaration)
function addition(num1, num2) {
  return num1 + num2;
}


// ============================================================
// 19. FUNCTION EXPRESSION vs DECLARATION        [INTERMEDIATE]
// ============================================================
// INTERVIEW: "What's the difference between function declaration and expression?"
//
//  +------------------------+----------------------------------+
//  | DECLARATION            | EXPRESSION                       |
//  +------------------------+----------------------------------+
//  | function foo() {}      | const foo = function() {}        |
//  |                        | const foo = () => {}             |
//  +------------------------+----------------------------------+
//  | Fully hoisted          | Only var name hoisted (undefined)|
//  | Can call before decl.  | Cannot call before assignment    |
//  +------------------------+----------------------------------+

// This works:
console.log(addition(4, 7)); // 11
function addition(num1, num2) { return num1 + num2; }

// This does NOT work:
// console.log(minus(10, 7)); // TypeError: minus is not a function
var minus = function(num1, num2) { return num1 - num2; };
// `var minus` is hoisted as undefined. Calling undefined() -> TypeError.


// ============================================================
// 20. let AND const HOISTING                    [INTERMEDIATE]
// ============================================================
// let/const ARE hoisted but NOT initialized -> Temporal Dead Zone.
// (See Part III for comprehensive TDZ coverage.)

// let:
if (true) {
  let month;
  console.log(month); // undefined (declared, not assigned)
  let year = 1994;
  console.log(year);  // 1994
}
// console.log(year); // ReferenceError: year is not defined

// TDZ example with let:
function isTruthy(value) {
  if (value) {
    // ---------- TDZ for myVariable starts here ----------
    // console.log(myVariable); // ReferenceError!
    let myVariable = 'Value 2';
    // ---------- TDZ for myVariable ends here   ----------
    console.log(myVariable); // 'Value 2'
    return true;
  }
  return false;
}
isTruthy(1);

// const -- same as let: hoisted but in TDZ.
// Must be initialized at declaration time.
function double2(number) {
  // ---------- TDZ for TWO starts here ----------
  // console.log(TWO); // ReferenceError!
  const TWO = 2;
  // ---------- TDZ for TWO ends here   ----------
  return number * TWO;
}
double2(5); // 10


// ============================================================
// 21. class HOISTING                            [INTERMEDIATE]
// ============================================================
// Classes are hoisted but remain in the TDZ. NOT accessible before declaration.

// const apple = new Company('Apple'); // ReferenceError: Company is not defined
class Company {
  constructor(name) { this.name = name; }
}
const microsoft = new Company('Microsoft'); // works (after declaration)


// ============================================================
// 22. HOISTING EDGE CASES                         [ADVANCED]
// ============================================================

// CASE 1: Function declarations in blocks (non-strict)
// Behavior is implementation-dependent! Avoid this pattern.
// In strict mode, function declarations are block-scoped.

// CASE 2: Function vs var with same name
var myFunc = "hello";
function myFunc() { return "world"; }
console.log(typeof myFunc); // "string"
// function declaration hoisted first, then var assignment overwrites

// CASE 3: Duplicate function declarations
function dup() { return 1; }
function dup() { return 2; }
console.log(dup()); // 2 (last declaration wins)

// CASE 4: let/const in for loops
// Each iteration gets its own block scope (new binding per iteration)
for (let i = 0; i < 3; i++) {
  setTimeout(() => console.log(i), 100); // 0, 1, 2  (each `i` is a new binding)
}
// Compare with var:
for (var j = 0; j < 3; j++) {
  setTimeout(() => console.log(j), 100); // 3, 3, 3  (one shared `j`)
}

// CASE 5: Named function expressions
// The name is only accessible inside the function itself
var foo = function bar() {
  console.log(typeof bar); // "function" (accessible inside)
};
// console.log(typeof bar); // "undefined" (not accessible outside)


// ************************************************************
//  PART III: TEMPORAL DEAD ZONE (The let/const Specific Behavior)
// ************************************************************
//
//  TDZ = the period between entering a scope where a variable
//  is hoisted and the line where it is actually declared.
//  Accessing a variable in its TDZ throws ReferenceError.
//
//  Applies to: let, const, class
//  Does NOT apply to: var, function declarations
// ************************************************************


// ============================================================
// 23. WHAT IS TDZ (+ Visualization)                     [BASIC]
// ============================================================
//
//  {
//    // ============ TDZ for `x` STARTS ============
//    //
//    //  `x` is hoisted (the engine KNOWS it exists)
//    //  but it is UNINITIALIZED.
//    //
//    //  ANY access here throws ReferenceError:
//    //    console.log(x);  // ReferenceError
//    //    x = 5;           // ReferenceError
//    //    typeof x;        // ReferenceError (!)
//    //    x + 1;           // ReferenceError
//    //
//    // ============ TDZ for `x` ENDS ==============
//    let x = 10;  // <-- initialization happens HERE
//    //
//    console.log(x);  // 10 (safe to use)
//  }
//
//  Timeline:
//  +---+---+---+---+---+---+---+---+---+---+
//  | { |   |   |   |   | let x=10 |   | } |
//  +---+---+---+---+---+---+---+---+---+---+
//  |<--- TDZ (ReferenceError) --->|<- OK ->|


// ============================================================
// 24. WHY TDZ EXISTS                                    [BASIC]
// ============================================================
//
//  1. CATCHES BUGS: Using a variable before declaring it is almost
//     always a mistake. TDZ makes it an explicit error.
//
//  2. CONST CORRECTNESS: const MUST have a value at declaration.
//     Without TDZ, you could observe const as undefined, then
//     as its assigned value -- violating the "constant" contract.
//
//  3. PREDICTABILITY: Code reads top-to-bottom. Variables should
//     not be usable before you define them.


// ============================================================
// 25. VARIABLE LIFECYCLE: var vs let vs const    [INTERMEDIATE]
// ============================================================
//
//  +-------------+    +---------------+    +------------+
//  | DECLARATION |    | INITIALIZATION|    | ASSIGNMENT |
//  | (hoisting)  |--->| (exit TDZ)    |--->| (= value)  |
//  +-------------+    +---------------+    +------------+
//       var: all three happen "at top" (init = undefined)
//       let: declaration hoisted, init at source line, assignment at =
//       const: declaration hoisted, init+assignment at source line
//
//  +------------------------------------------------------------+
//  |                   var x = 5;                               |
//  +------------------------------------------------------------+
//  | Creation phase:  var x; (hoisted, x = undefined)           |
//  | Execution:       x = 5; (assignment)                       |
//  | Before decl:     console.log(x) -> undefined               |
//  +------------------------------------------------------------+
//
//  +------------------------------------------------------------+
//  |                   let x = 5;                               |
//  +------------------------------------------------------------+
//  | Creation phase:  let x; (hoisted, NOT initialized -> TDZ)  |
//  | Execution:       x = 5; (initialization + assignment)      |
//  | Before decl:     console.log(x) -> ReferenceError          |
//  +------------------------------------------------------------+
//
//  +------------------------------------------------------------+
//  |                   const x = 5;                             |
//  +------------------------------------------------------------+
//  | Creation phase:  const x; (hoisted, NOT initialized -> TDZ)|
//  | Execution:       x = 5; (initialization + assignment, once)|
//  | Before decl:     console.log(x) -> ReferenceError          |
//  +------------------------------------------------------------+


// ============================================================
// 26. BASIC TDZ EXAMPLES                                [BASIC]
// ============================================================

// let in TDZ:
{
  // console.log(myLet); // ReferenceError: Cannot access 'myLet' before initialization
  let myLet = "hello";
  console.log(myLet); // "hello" (safe)
}

// const in TDZ:
{
  // console.log(MY_CONST); // ReferenceError
  const MY_CONST = 42;
  console.log(MY_CONST); // 42 (safe)
}

// var has NO TDZ:
{
  console.log(myVar); // undefined (hoisted and initialized)
  var myVar = "hello";
  console.log(myVar); // "hello"
}


// ============================================================
// 27. typeof IN THE TDZ                         [INTERMEDIATE]
// ============================================================
// INTERVIEW: "Does typeof throw for let/const?"
// YES! This is a major difference from undeclared variables.

// typeof on UNDECLARED variable -> safe, returns "undefined"
console.log(typeof undeclaredVar); // "undefined" (no error)

// typeof on TDZ variable -> throws!
// {
//   console.log(typeof myTdzVar); // ReferenceError!
//   let myTdzVar = 5;
// }


// ============================================================
// 28. TDZ IN FUNCTION SCOPE                    [INTERMEDIATE]
// ============================================================

function example() {
  // console.log(x); // ReferenceError (TDZ)
  // console.log(y); // ReferenceError (TDZ)
  let x = 1;
  const y = 2;
  console.log(x, y); // 1, 2
}
example();


// ============================================================
// 29. TDZ IN BLOCKS (if / for)                 [INTERMEDIATE]
// ============================================================

// Each block creates its own TDZ:
if (true) {
  // TDZ for `msg` starts here
  // console.log(msg); // ReferenceError
  let msg = "hello";
  console.log(msg); // "hello"
}

// for loop with let: each iteration has its own TDZ
for (let i = 0; i < 3; i++) {
  // `i` is initialized at the start of each iteration
  console.log(i); // 0, 1, 2
}


// ============================================================
// 30. TDZ WITH class                           [INTERMEDIATE]
// ============================================================

// Classes are hoisted but in TDZ:
// const obj2 = new MyClass(); // ReferenceError: Cannot access 'MyClass' before initialization

class MyClass {
  constructor() {
    this.value = 42;
  }
}

const obj2 = new MyClass(); // works after declaration
console.log(obj2.value);    // 42


// ============================================================
// 31. TDZ IN DEFAULT PARAMETERS                  [ADVANCED]
// ============================================================
// INTERVIEW: Tricky edge case with TDZ in function parameters.

// Parameters are evaluated left-to-right.
// Later params can reference earlier params, but NOT themselves.

function valid(a, b = a) {
  console.log(a, b); // 1, 1
}
valid(1);

// function invalid(a = b, b) {
//   console.log(a, b);
// }
// invalid(undefined, 2); // ReferenceError! `b` is in TDZ when `a = b` evaluates

// Self-reference also triggers TDZ:
let p = 1;
// function selfRef(p = p + 1) { return p; }
// selfRef(); // ReferenceError! parameter `p` shadows outer `p`, references itself in TDZ

function fixed(q = p + 1) { return q; }
fixed(); // 2 (uses outer `p` since `q` is a different name)


// ============================================================
// 32. TDZ IN SWITCH STATEMENTS                   [ADVANCED]
// ============================================================
// All cases share ONE block scope in switch (unless you add {}).

// switch (x) {
//   case 0:
//     let y = 1;   // declared here
//     break;
//   case 1:
//     console.log(y); // ReferenceError! (TDZ - same block, different case)
//     break;
// }

// FIX: Wrap each case in its own block
// switch (x) {
//   case 0: {
//     let y = 1;
//     break;
//   }
//   case 1: {
//     let y = 2; // separate block, no conflict
//     break;
//   }
// }


// ============================================================
// 33. TDZ WITH CLOSURES                          [ADVANCED]
// ============================================================

// A closure can reference a TDZ variable IF it's called AFTER initialization.
{
  const fn2 = () => x2; // defined before `x2` is initialized
  // fn2(); // ReferenceError if called here (x2 in TDZ)
  let x2 = 42;
  console.log(fn2()); // 42 (called after x2 is initialized -- works!)
}


// ************************************************************
//  GOTCHAS & INTERVIEW TRAPS (Combined)
// ************************************************************


// ============================================================
// EXECUTION CONTEXT GOTCHAS
// ============================================================

// GOTCHA: Each function CALL creates a NEW EC (not each definition)
function counter() {
  var count = 0;
  return ++count;
}
counter(); // 1
counter(); // 1 (brand new EC each time, count starts at 0)

// GOTCHA: Arrow functions do NOT create their own EC for `this`
// They inherit `this` from the enclosing EC.
const arrowObj = {
  value: 42,
  getVal: () => this.value, // `this` = enclosing EC's `this` (window)
  getValMethod() { return this.value; } // `this` = arrowObj
};

// GOTCHA: eval() creates its own EC (avoid eval!)

// GOTCHA: Async functions create ECs that can be suspended
// async function foo() {
//   console.log("A");
//   await somePromise;  // EC is suspended here
//   console.log("B");   // EC is resumed when promise resolves
// }

// GOTCHA: Generator functions create ECs that can be paused/resumed
// function* gen() {
//   yield 1;  // EC paused
//   yield 2;  // EC resumed, then paused again
// }

// GOTCHA: The Global EC is NEVER popped from the stack
// (until the page/process is closed)


// ============================================================
// HOISTING GOTCHAS
// ============================================================

// GOTCHA: var in if blocks is NOT block-scoped
if (false) {
  var ghostVar = "I exist!";
}
console.log(ghostVar); // undefined (hoisted, but never assigned)

// GOTCHA: Function expression with var
// console.log(foo); // undefined (not a function yet!)
// foo();            // TypeError: foo is not a function
// var foo = function() { return 42; };

// GOTCHA: Parameters are hoisted to function scope
function paramExample(a) {
  console.log(a);   // value passed in
  var a = 99;       // var a is hoisted but doesn't shadow param
  console.log(a);   // 99
}
paramExample(5); // logs 5, then 99

// GOTCHA: Hoisting does not cross script boundaries
// Each <script> tag has its own execution context
// A var in one script is available in the next (via global), but
// a function declaration might not be (depends on timing)


// ============================================================
// TDZ GOTCHAS
// ============================================================

// GOTCHA: typeof throws in TDZ (unlike undeclared variables)
// {
//   typeof x;    // ReferenceError (x is in TDZ)
//   let x;
// }
// typeof y;      // "undefined" (y is truly undeclared -- safe)

// GOTCHA: TDZ is temporal (time-based), not spatial (position-based)
{
  // This works because `fn3` is called AFTER `x3` is initialized:
  function fn3() { return x3; }
  let x3 = 10;
  console.log(fn3()); // 10
  // TDZ is about WHEN you access, not WHERE the code is written.
}

// GOTCHA: TDZ applies to the ENTIRE block from the start
{
  // Even if `let x` is at line 100, TDZ starts at the opening `{`.
  // You cannot access `x` anywhere before line 100.
}

// GOTCHA: const must be initialized at declaration
// {
//   const x; // SyntaxError: Missing initializer in const declaration
// }

// GOTCHA: let allows declaration without initialization
{
  let x;             // fine (x = undefined)
  console.log(x);    // undefined
}

// GOTCHA: for-of/for-in creates a new TDZ per iteration
for (const item of [1, 2, 3]) {
  // A new `item` binding is created each iteration.
  // const works here because each iteration is a new scope.
  console.log(item); // 1, 2, 3
}

// GOTCHA: Nested functions can "escape" TDZ by delayed execution
// (see Section 33 above)
