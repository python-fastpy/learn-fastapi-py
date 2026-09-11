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
//
// ------------------------------------------------------------------
// ONE EXAMPLE THAT HITS EVERY CASE ABOVE
// ------------------------------------------------------------------
// Every bullet point in both boxes is a distinct rule. Rather than
// isolate them, this single function is deliberately built to trigger
// ALL of them at once, so you can see how they interact in one place.
// Each deep-dive section is cited so you can jump to the full treatment.

function demo(x, y = 10) {                 // case 1: function arguments
  console.log(add(2, 3));                  // case 2: fully-hoisted function decl -> callable NOW
  console.log(counted);                    // case 3: var hoisted -> undefined (not yet a ReferenceError)
  // console.log(label);                   // case 4: let hoisted but TDZ -> ReferenceError if uncommented
  // console.log(Thing);                   // case 5: class hoisted but TDZ -> ReferenceError if uncommented
  // console.log(makeThing());             // case 6: function EXPRESSION treated as var -> undefined -> TypeError

  var counted = x + y;                     // "variables are assigned their values" (execution phase)
  let label = "result";                    // "let/const exit TDZ at their declaration line"
  class Thing {}                           // class also exits TDZ here
  var makeThing = function () {            // function expression: the ASSIGNMENT happens here, not hoisting
    return new Thing();
  };

  function add(a, b) { return a + b; }     // function declaration (the whole body was hoisted already)

  return counted;                          // "expressions are evaluated"
}

console.log(demo(5));                      // "functions are called (creating new ECs)"

// CREATION PHASE of demo(5) -- every row maps to a case above:
// +--------------------------------------------------------------------+
// | FEC for demo                                                        |
// | Variable Object (var-like bindings):                                |
// |   arguments: { 0: 5, length: 1 }   <- case 1: function arguments    |
// |   x: 5                             <- case 1: function arguments    |
// |   y: 10 (default applied during    <- case 1: function arguments    |
// |        parameter binding)                                          |
// |   add: function add(a,b){...}      <- case 2: function decl,        |
// |                                        HOISTED FULLY (body + all)   |
// |   counted: undefined               <- case 3: var hoisted,          |
// |                                        initialized to undefined     |
// |   makeThing: undefined             <- case 6: function EXPRESSION   |
// |                                        treated exactly like var     |
// | Lexical Environment (block-scoped bindings):                        |
// |   label: <uninitialized>           <- case 4: let hoisted, TDZ      |
// |   Thing: <uninitialized>           <- case 5: class hoisted, TDZ    |
// | Scope Chain: [demoVO, globalVO]    <- "create the scope chain"      |
// |                                        (see Section 7 for nesting)  |
// | this: undefined (strict) /         <- "determine this binding"     |
// |       window (sloppy)                 (see Section 9 for all forms)|
// +--------------------------------------------------------------------+
//
// EXECUTION PHASE of demo(5) -- line by line:
// +--------------------------------------------------------------------+
// | line                          | what happens                       |
// |-------------------------------|-------------------------------------|
// | console.log(add(2,3))         | add() CALLED -> new FEC pushed and  |
// |                                | popped -> logs 5                    |
// | console.log(counted)          | logs undefined (assignment below    |
// |                                | hasn't run yet)                     |
// | counted = x + y               | 5 + 10 = 15 (var assigned its value)|
// | let label = "result"          | label EXITS TDZ, then assigned      |
// | class Thing {}                | Thing EXITS TDZ                     |
// | var makeThing = function(){}  | makeThing reassigned from undefined |
// |                                | to the function (still just an     |
// |                                | assignment -- var itself already   |
// |                                | existed since creation phase)       |
// | return counted                | expression evaluated -> 15          |
// +--------------------------------------------------------------------+
// OUTPUT: 5, undefined, 15 (the returned value)
//
// See Sections 17-22 for var/function/let/const/class hoisting in full
// depth, and Part III (Sections 23-33) for everything about the TDZ.


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

// When the script first loads, the Global EC is created:
//
// CREATION PHASE:
// +------------------------------------------+
// | Global EC                                |
// | Variable Object:                         |
// |   globalVar: undefined                   |
// | Scope Chain: [globalVO]                  |
// | this: window (or globalThis)             |
// +------------------------------------------+
//
// EXECUTION PHASE:
// +------------------------------------------+
// | globalVar = "I'm global"                 |
// +------------------------------------------+


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

// outer() is called -> new EC pushed:
//
// CREATION PHASE:
// +------------------------------------------+
// | FEC for outer                            |
// | Variable Object:                         |
// |   outerCount: undefined                  |
// |   inner: function                        |
// | Scope Chain: [outerVO, globalVO]         |
// | this: window (or undefined in strict)    |
// +------------------------------------------+
//
// EXECUTION PHASE:
// +------------------------------------------+
// | outerCount = 1                           |
// | inner() called -> new EC pushed          |
// +------------------------------------------+
//
// inner() is called -> new EC pushed:
//
// CREATION PHASE:
// +------------------------------------------+
// | FEC for inner                            |
// | Variable Object:                         |
// |   innerCount: undefined                  |
// | Scope Chain: [innerVO, outerVO, globalVO]|
// | this: window (or undefined in strict)    |
// +------------------------------------------+
//
// EXECUTION PHASE:
// +------------------------------------------+
// | innerCount = 2                           |
// | console.log(0, 1, 2)                     |
// +------------------------------------------+

// SCOPE CHAIN VISUALIZATION:
// inner() looks up variables:
//   innerCount -> found in innerVO
//   outerCount -> not in innerVO -> found in outerVO
//   globalCount -> not in innerVO -> not in outerVO -> found in globalVO


// ============================================================
// 8. LEXICAL ENVIRONMENT vs VARIABLE ENVIRONMENT  [ADVANCED]
// ============================================================
// INTERVIEW: "What's the difference between Variable Object and
//             Variable Environment?" / "What's LE vs VE?"
//
// -----------------------------------------------------------------
// 8A. VARIABLE OBJECT (ES3) vs VARIABLE ENVIRONMENT (ES5+)
// -----------------------------------------------------------------
//
//  "Variable Object" (VO) is the OLD ES3 spec term.
//  "Variable Environment" (VE) is the MODERN ES5+ replacement.
//
//  They serve the SAME purpose -- storing declarations for an
//  execution context -- but the underlying model changed:
//
//  +---------------------+---------------------------------------------+
//  | ES3: Variable       | ES5+: Variable Environment                  |
//  | Object (VO)         | (a Lexical Environment record)              |
//  +---------------------+---------------------------------------------+
//  | A plain spec object | An Environment Record (abstract, not a real |
//  | that stores:        | JS object you can inspect) that stores:     |
//  |  - var declarations |  - var declarations                         |
//  |  - function decls   |  - function declarations                    |
//  |  - arguments        |  - arguments                                |
//  +---------------------+---------------------------------------------+
//  | In global EC, the   | In global EC, the Environment Record's      |
//  | VO IS the global    | "object record" binds to the global object, |
//  | object (window)     | so var/function still appear on window      |
//  +---------------------+---------------------------------------------+
//  | In function EC, the | In function EC, the VE is a new             |
//  | VO is called the    | declarative Environment Record (no backing  |
//  | "Activation Object" | object -- purely internal)                  |
//  | and also holds      |                                             |
//  | `arguments`         |                                             |
//  +---------------------+---------------------------------------------+
//  | Only ONE storage    | TWO environments per EC (VE + LE), which    |
//  | per EC              | is how let/const get block scoping          |
//  +---------------------+---------------------------------------------+
//
//  WHY THE CHANGE: ES3's single VO couldn't model block scoping.
//  ES5+ split it into VE (for var/function, stays fixed) and LE
//  (for let/const, swaps on every new block).
//
//  BOTTOM LINE: when you see "Variable Object" in older material,
//  read it as "Variable Environment" -- same role, newer model.
//  This file uses both terms: "VO" in ASCII diagrams for brevity,
//  and "Variable Environment" / "Lexical Environment" where the
//  ES5+ distinction matters.
//
// -----------------------------------------------------------------
// 8A-EXAMPLE: VO (ES3) vs VE+LE (ES5+) — SAME CODE, TWO MODELS
// -----------------------------------------------------------------
//  Run the code below and study how each spec models it.

function scopeDemo() {
  var x = 1;
  let y = 2;

  if (true) {
    var x2 = 10;      // var -> function-scoped
    let y2 = 20;      // let -> block-scoped
    console.log(x, y, x2, y2); // 1, 2, 10, 20
  }

  console.log(x);     // 1
  console.log(x2);    // 10  (var escapes the block)
  // console.log(y2); // ReferenceError (let is block-scoped, gone)
}
scopeDemo();

//  HOW ES3 (Variable Object) WOULD MODEL scopeDemo():
//  ---------------------------------------------------
//  ES3 has ONE Variable Object per function — no block awareness.
//
//  CREATION PHASE:
//  +------------------------------------------+
//  | VO for scopeDemo (the only storage)      |
//  |   x:  undefined                          |
//  |   x2: undefined                          |
//  |   y:  ??? (let didn't exist in ES3)      |
//  |   y2: ??? (let didn't exist in ES3)      |
//  +------------------------------------------+
//
//  PROBLEM: ES3's single VO has no way to:
//    - block-scope y2 inside the if-block
//    - enforce TDZ for y and y2
//    - discard y2 when the if-block ends
//  This is exactly why ES5+ replaced the VO model.
//
//
//  HOW ES5+ (VE + LE) MODELS scopeDemo():
//  ---------------------------------------------------
//  ES5+ gives EACH execution context a VE and an LE,
//  and creates a NEW LE when entering a block.
//
//  CREATION PHASE:
//  +------------------------------------------+
//  | FEC for scopeDemo                        |
//  | Variable Environment (VE):               |
//  |   x:  undefined          (var)           |
//  |   x2: undefined          (var)           |
//  | Lexical Environment (LE):                |
//  |   y:  <uninitialized>    (let, TDZ)      |
//  +------------------------------------------+
//
//  EXECUTION — entering the if-block:
//  Engine creates a NEW block LE and pushes it:
//
//  +------------------+     +--------------------+
//  | Block LE (new)   |     | Function LE / VE   |
//  |   y2: <uninit>   |---->|   x: 1     (var)   |
//  +------------------+     |   x2: undef (var)   |
//     (TDZ for y2)          |   y: 2     (let)    |
//                           +--------------------+
//
//  Inside the if-block:
//    x2 = 10  -> found in VE (var ignores block)
//    y2 = 20  -> found in block LE (let is block-scoped)
//
//  EXECUTION — leaving the if-block:
//  Block LE is DISCARDED. y2 is gone. x2 survives in VE.
//
//  +--------------------+
//  | Function LE / VE   |
//  |   x: 1     (var)   |
//  |   x2: 10   (var)   |  <- still accessible
//  |   y: 2     (let)   |
//  +--------------------+
//  |   y2: GONE         |  <- block LE discarded
//  +--------------------+
//
//  SIDE-BY-SIDE SUMMARY:
//  +----------------------------+------------------------------------+
//  |  ES3 (VO)                  |  ES5+ (VE + LE)                   |
//  +----------------------------+------------------------------------+
//  | One flat VO per function   | VE (var/func) + LE (let/const)    |
//  | No block awareness         | New LE per block { }              |
//  | Can't model let/const TDZ  | TDZ = <uninitialized> in LE      |
//  | Can't discard block vars   | Block LE discarded on }           |
//  | x2 leaks — by design      | x2 leaks — var goes to VE        |
//  | y2 would also leak         | y2 gone — block LE discarded     |
//  +----------------------------+------------------------------------+
//
// -----------------------------------------------------------------
// 8B. VARIABLE ENVIRONMENT (VE) vs LEXICAL ENVIRONMENT (LE)
// -----------------------------------------------------------------
//  Both are Lexical Environments, but they play different roles
//  inside the SAME execution context:
//
//  VARIABLE ENVIRONMENT (VE):
//  - Stores var declarations and function declarations
//  - Created once per function/global EC
//  - Doesn't change structurally during execution
//
//  LEXICAL ENVIRONMENT (LE):
//  - Stores let and const declarations
//  - Initially points to the SAME record as VE
//  - Changes when entering new blocks (if, for, {})
//  - Each block creates a new LE that chains to the outer one

function veLEDemo() {
  var a = 1;
  let b = 2;

  if (true) {
    var c = 3;
    let d = 4;
    console.log(a, b, c, d); // 1, 2, 3, 4
  }

  console.log(a, b, c);    // 1, 2, 3 (c survived — it's in VE)
  // console.log(d);        // ReferenceError (d was in block LE, now gone)
}
veLEDemo();

//  STEP-BY-STEP EC DIAGRAM FOR veLEDemo():
//
//  STEP 1 — CREATION PHASE (function entry):
//  VE and LE start pointing to the SAME environment record.
//
//  +----------------------------------------------+
//  | FEC for veLEDemo                             |
//  |                                              |
//  | VE ──┐                                       |
//  |      ├──> Environment Record {               |
//  | LE ──┘     a: undefined    (var)             |
//  |            c: undefined    (var)             |
//  |            b: <uninit>     (let, TDZ)        |
//  |          }                                   |
//  | outer ref -> Global Environment              |
//  +----------------------------------------------+
//  Note: VE and LE are the same pointer right now.
//
//
//  STEP 2 — EXECUTION (before if-block):
//  a = 1, b exits TDZ and gets 2.
//
//  VE ──┐
//       ├──> { a: 1, c: undefined, b: 2 }
//  LE ──┘
//
//
//  STEP 3 — ENTERING the if-block:
//  Engine creates a NEW LE for the block. VE does NOT change.
//  LE pointer swaps to the new block environment.
//
//  VE ──────> { a: 1, c: undefined, b: 2 }   (UNCHANGED)
//                        ^
//  LE ──> Block Env {    |
//           d: <uninit>  |  (let, TDZ)
//           outer ───────┘  (chains back to function env)
//         }
//
//
//  STEP 4 — INSIDE the if-block:
//  c = 3  -> engine walks from block LE -> finds c in VE -> assigns 3
//  d = 4  -> found directly in block LE -> exits TDZ, assigned 4
//
//  VE ──────> { a: 1, c: 3, b: 2 }    (c updated HERE)
//                      ^
//  LE ──> Block Env {  |
//           d: 4       |
//           outer ─────┘
//         }
//
//
//  STEP 5 — LEAVING the if-block:
//  Block LE is discarded. LE pointer reverts to function env.
//  d is GONE. c survives in VE.
//
//  VE ──┐
//       ├──> { a: 1, c: 3, b: 2 }
//  LE ──┘
//
//       Block Env { d: 4 }  <- garbage collected (no references)
//
//
//  WHY THIS MATTERS FOR INTERVIEWS:
//  "var c = 3 inside the if-block ends up in VE because var
//   ignores blocks. let d = 4 goes into the block LE and dies
//   when the block ends. That's the whole mechanism behind
//   block scoping — VE is stable, LE swaps per block."


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

// Same function, three calls -> three different `this` bindings.
// `this` is decided fresh in EACH call's CREATION PHASE, based on
// HOW the function was invoked (not where it was defined):
//
// showThis() -- plain call:
// CREATION PHASE:
// +------------------------------------------+
// | FEC for showThis                         |
// | Variable Object: (none)                  |
// | Scope Chain: [showThisVO, globalVO]      |
// | this: window (sloppy) / undefined (strict)|
// +------------------------------------------+
//
// obj.showThis() -- method call:
// CREATION PHASE:
// +------------------------------------------+
// | FEC for showThis                         |
// | Variable Object: (none)                  |
// | Scope Chain: [showThisVO, globalVO]      |
// | this: obj (the object before the dot)    |
// +------------------------------------------+
//
// showThis.call({ x: 1 }) -- explicit binding:
// CREATION PHASE:
// +------------------------------------------+
// | FEC for showThis                         |
// | Variable Object: (none)                  |
// | Scope Chain: [showThisVO, globalVO]      |
// | this: { x: 1 } (forced via .call())      |
// +------------------------------------------+


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

// makeCounter() is called -> new EC pushed:
//
// CREATION PHASE:
// +------------------------------------------+
// | FEC for makeCounter                      |
// | Variable Object:                         |
// |   count: undefined (var-like, via let)   |
// | Scope Chain: [makeCounterVO, globalVO]   |
// | this: window (or undefined in strict)    |
// +------------------------------------------+
//
// EXECUTION PHASE:
// +------------------------------------------+
// | count = 0                                |
// | return anonymous function                |
// | (EC popped, but its LE survives --       |
// |  see closure diagram below)              |
// +------------------------------------------+
//
// counter() is called -> new EC pushed:
//
// CREATION PHASE:
// +------------------------------------------+
// | FEC for (anonymous)                      |
// | Variable Object: (none of its own)       |
// | Scope Chain: [anonVO, makeCounterLE]     |
// | this: window (or undefined in strict)    |
// +------------------------------------------+
//
// EXECUTION PHASE:
// +------------------------------------------+
// | count++  (mutates makeCounter's LE)      |
// | return count                             |
// +------------------------------------------+

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
console.log(factorial(5)); // 120 -- 5 recursive ECs pushed, then all popped

// Or convert to iterative (no extra ECs at all -- one EC, one loop):
function factorialIter(n) {
  let result = 1;
  for (let i = 2; i <= n; i++) result *= i;
  return result;
}
console.log(factorialIter(5)); // 120 -- same result, zero recursion depth


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

// STEP 1 -- Global EC created (script loads):
//
// CREATION PHASE:
// +------------------------------------------+
// | Global EC                                |
// | Variable Object:                         |
// |   x: undefined                           |
// |   foo: function                          |
// |   result: undefined                      |
// | Scope Chain: [globalVO]                  |
// | this: window                             |
// +------------------------------------------+
//
// EXECUTION PHASE:
// +------------------------------------------+
// | x = 10                                   |
// | foo(50) called -> new EC pushed          |
// +------------------------------------------+
//
// STEP 2 -- foo(50) called -> new EC pushed:
//
// CREATION PHASE:
// +------------------------------------------+
// | FEC for foo                              |
// | Variable Object:                         |
// |   a: 50 (argument)                       |
// |   b: undefined                           |
// |   bar: function                          |
// | Scope Chain: [fooVO, globalVO]           |
// | this: window                             |
// +------------------------------------------+
//
// EXECUTION PHASE:
// +------------------------------------------+
// | b = 20                                   |
// | bar(40) called -> new EC pushed          |
// +------------------------------------------+
//
// STEP 3 -- bar(40) called -> new EC pushed:
//
// CREATION PHASE:
// +------------------------------------------+
// | FEC for bar                              |
// | Variable Object:                         |
// |   c: 40 (argument)                       |
// |   d: undefined                           |
// | Scope Chain: [barVO, fooVO, globalVO]    |
// | this: window                             |
// +------------------------------------------+
//
// EXECUTION PHASE:
// +------------------------------------------+
// | d = 30                                   |
// | return a + b + c + d + x                 |
// |   = 50 + 20 + 40 + 30 + 10 = 150         |
// +------------------------------------------+
//
// STEP 4 -- unwind the call stack:
//   bar EC popped, foo's bar(40) call returns 150
//   foo EC popped, result = 150 (back in Global EC)
//   console.log(150)


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
// The name is only accessible inside the function itself.
// (Named `taggedFn`/`tagged` here -- NOT `foo`/`bar` -- so this doesn't
// collide with the unrelated `foo`/`bar` from Section 13's walkthrough.)
var taggedFn = function tagged() {
  console.log(typeof tagged); // "function" (accessible inside)
};
taggedFn();                    // actually run it so the log above fires
// console.log(typeof tagged); // "undefined" (not accessible outside)


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
function counterFn() {
  var count = 0;
  return ++count;
}
counterFn(); // 1
counterFn(); // 1 (brand new EC each time, count starts at 0)

// GOTCHA: Arrow functions do NOT create their own EC for `this`
// They inherit `this` from the enclosing EC.
const arrowObj = {
  value: 42,
  getVal: () => this.value, // `this` = enclosing EC's `this`, NOT arrowObj
  getValMethod() { return this.value; } // `this` = arrowObj (normal method call)
};
console.log(arrowObj.getVal());       // undefined -- this.value on the OUTER `this`
                                       // (browser script: window.value; here,
                                       // running via `node file.js`: module.exports.value)
console.log(arrowObj.getValMethod()); // 42 -- `this` correctly bound to arrowObj

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
