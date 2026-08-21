// ============================================================
// JAVASCRIPT FUNCTIONS -- COMPREHENSIVE REFERENCE
// ============================================================
//
// Merged from:
//   - functionsinfo.js  (javascripttutorial.net)
//   - dmitripavl.js     (dmitripavlutin.com)
//
// For recursion, memoization, trampolining, call-stack diagrams
// see --> RecusrionExample.js
//
//
// ============================================================
// TABLE OF CONTENTS
// ============================================================
//
//  BASICS
//   1.  First-Class Citizens ........................ [BASIC]
//   2.  Declaration vs Expression vs Arrow (table) .. [BASIC]
//   3.  Function Declaration ........................ [BASIC]
//   4.  Function Expression ......................... [BASIC]
//   5.  Shorthand Method Definition ................. [BASIC]
//   6.  Anonymous Functions & IIFE .................. [BASIC]
//
//  PARAMETERS & ARGUMENTS
//   7.  Function Parameters ......................... [INTERMEDIATE]
//   8.  Pass-by-Value Semantics ..................... [INTERMEDIATE]
//
//  CALLBACKS & HIGHER-ORDER FUNCTIONS
//   9.  Callbacks (Sync & Async) .................... [INTERMEDIATE]
//  10.  Higher-Order Functions ...................... [INTERMEDIATE]
//
//  ARROW FUNCTIONS
//  11.  Arrow Functions ............................. [INTERMEDIATE]
//  12.  When NOT to Use Arrow Functions ............. [INTERMEDIATE]
//
//  METHODS, `this`, & INVOCATION
//  13.  Methods in JavaScript ....................... [INTERMEDIATE]
//  14.  Function Object: length, prototype, new.target [INTERMEDIATE]
//  15.  call() / apply() / bind() .................. [INTERMEDIATE]
//  16.  Function Invocation Patterns & `this` ....... [ADVANCED]
//
//  GENERATORS
//  17.  Generator Functions ......................... [INTERMEDIATE]
//
//  ADVANCED PATTERNS
//  18.  Closures in Callbacks ....................... [ADVANCED]
//  19.  Currying .................................... [ADVANCED]
//  20.  Partial Application ......................... [ADVANCED]
//  21.  Function Composition (pipe / compose) ....... [ADVANCED]
//  22.  Thunks ...................................... [ADVANCED]
//  23.  Pure vs Impure Functions .................... [ADVANCED]
//  24.  Function Overloading Patterns ............... [ADVANCED]
//  25.  new Function Constructor .................... [ADVANCED]
//  26.  General Function Gotchas .................... [ADVANCED]
//


// ============================================================
// 1. FIRST-CLASS CITIZENS                            [BASIC]
// ============================================================
// INTERVIEW: "What does it mean that functions are first-class?"
// Answer: Functions can be assigned to variables, passed as
// arguments, and returned from other functions -- just like
// any other value (number, string, object).
//
//  +--------------------------------------------------+
//  |           First-Class Function Capabilities       |
//  +--------------------------------------------------+
//  | Capability          | Example                    |
//  |---------------------+----------------------------|
//  | Assign to variable  | let fn = add;              |
//  | Pass as argument    | higher(fn);                |
//  | Return from fn      | return function() {...};   |
//  | Store in structure   | [fn1, fn2] or { op: fn }  |
//  +--------------------------------------------------+

// --- 1a. Storing a function in a variable ---
function add(a, b) {
  return a + b;
}
let sum = add;
console.log(add(1, 2)); // 3
console.log(sum(2, 3)); // 5

// --- 1b. Passing a function as an argument ---
function average(a, b, func) {
  return func(a, b) / 2;
}
let result = average(10, 10, sum);
console.log(result); // 10

// --- 1c. Returning a function from a function ---
function compareBy(propertyName) {
  return function (a, b) {
    let x = a[propertyName], y = b[propertyName];
    if (x > y) return 1;
    if (x < y) return -1;
    return 0;
  };
}

let products = [
  { name: 'iPhone', price: 900 },
  { name: 'Samsung Galaxy', price: 850 },
  { name: 'Sony Xperia', price: 700 },
];
products.sort(compareBy('price'));
console.log(products);
// Sorted ascending by price: Sony(700), Samsung(850), iPhone(900)

// GOTCHAS -- First-Class Citizens
// - Assigning a method to a variable loses `this` context
//     const fn = obj.method; fn(); // `this` is undefined/global
// - Functions are objects, so they are compared by reference
//     (function(){}) === (function(){})  // false


// ============================================================
// 2. COMPARISON TABLE: DECLARATION vs EXPRESSION vs ARROW [BASIC]
// ============================================================
//
//  +--------------------------------------------------------------------+
//  | Feature              | Declaration     | Expression      | Arrow   |
//  |----------------------+-----------------+-----------------+---------|
//  | Hoisted?             | YES (fully)     | NO              | NO      |
//  | Has `this`?          | own (dynamic)   | own (dynamic)   | lexical |
//  | Has `arguments`?     | YES             | YES             | NO      |
//  | Can be constructor?  | YES (new Fn)    | YES (new Fn)    | NO      |
//  | Can be generator?    | YES (function*) | YES (function*) | NO      |
//  | Has .prototype?      | YES             | YES             | NO      |
//  | Named?               | always          | optional        | inferred|
//  +--------------------------------------------------------------------+
//
// INTERVIEW: "When should you use an arrow function vs a regular function?"
//   Use arrow:  callbacks, array methods, preserving outer `this`
//   Use regular: object methods, constructors, when you need `arguments`


// ============================================================
// 3. FUNCTION DECLARATION                            [BASIC]
// ============================================================

function isEven(num) {
  return num % 2 === 0;
}
console.log(isEven(24)); // true
console.log(isEven(11)); // false

// Hoisting -- declaration is available BEFORE its position in code
console.log(hello('Shubham')); // "Hello Shubham"
console.log(hello.name);      // "hello"
console.log(typeof hello);    // "function"

function hello(name) {
  return `Hello ${name}`;
}

// INTERVIEW: "What is hoisting?"
// The engine moves function declarations to the top of their scope
// during the compile phase, so they can be called before their
// textual position. Only declarations are hoisted, NOT expressions.


// ============================================================
// 4. FUNCTION EXPRESSION                             [BASIC]
// ============================================================
// Starts with const/let/var, NOT with the keyword `function`.

// -- anonymous expression
const count = function (array) {
  return array.length;
};
console.log(count([5, 6, 7])); // 3

// -- named expression (useful for recursion & stack traces)
const myFunctionVar1 = function getNumber() {
  console.log(typeof getNumber === 'function'); // true (accessible inside)
  return 42;
};
console.log(myFunctionVar1());    // 42
console.log(myFunctionVar1.name); // "getNumber"
console.log(typeof getNumber);    // "undefined" (NOT accessible outside)

// -- expression as object method & callback
const methods = {
  numbers: [1, 5, 8],
  sum: function () {
    return this.numbers.reduce(function (acc, num) {
      return acc + num;
    });
  }
};
console.log(methods.sum()); // 14

// -- name inference: anonymous fn assigned to variable gets the variable name
const myFunc = function (x) { return typeof x; };
console.log(myFunc.name); // "myFunc"

// GOTCHAS -- Function Expression
// - Not hoisted: calling before definition throws ReferenceError
// - Named expressions: the name is only available INSIDE the body
// - In `const fn = function named() {}`, fn.name is "named" not "fn"

// INTERVIEW: "Declaration vs Expression -- when to use which?"
//   Declaration: top-level utility functions, hoisting needed
//   Expression: callbacks, conditional definitions, module exports


// ============================================================
// 5. SHORTHAND METHOD DEFINITION                     [BASIC]
// ============================================================

const collection = {
  items: [],
  add(...items) {
    this.items.push(...items);
  },
  get(index) {
    return this.items[index];
  }
};
collection.add('C', 'Java', 'JS');
console.log(collection.get(2)); // "JS"

// -- computed property names as methods
const addKey = 'add';
const getKey = 'get';
const collection1 = {
  items: [],
  [addKey](...items) { this.items.push(...items); },
  [getKey](index)    { return this.items[index]; }
};
collection1[addKey]('C', 'Java', 'PHP');
console.log(collection1[getKey](1)); // "Java"


// ============================================================
// 6. ANONYMOUS FUNCTIONS & IIFE                      [BASIC]
// ============================================================
// INTERVIEW: "What is an IIFE and why would you use one?"

// --- 6a. Anonymous function assigned to variable ---
let show = function () {
  console.log("hello anonymous");
};
show();

// --- 6b. Anonymous function as callback ---
setTimeout(function () {
  console.log("setTimeout callback");
}, 1000);

// --- 6c. IIFE -- Immediately Invoked Function Expression ---
// Creates a private scope; avoids polluting global namespace.
//
//  Anatomy of an IIFE:
//  ( function(params) { body } )(args)
//  ^                           ^
//  wrapping parens make it      invocation parens
//  an *expression* not a
//  declaration

(function (p1, p2) {
  console.log("IIFE", p1, p2);
})("abc", "bcd");

// Arrow-function IIFE (modern style)
((msg) => console.log("Arrow IIFE:", msg))("works!");

// IIFE with return value
const CONFIG = (() => {
  const env = "production";
  return { env, debug: env !== "production" };
})();
console.log(CONFIG); // { env: 'production', debug: false }

// GOTCHAS -- IIFE
// - Forgetting the wrapping parens causes a SyntaxError
// - IIFEs were the pre-ES6 module pattern; today `import/export`
//   or block-scoped `let`/`const` are preferred for isolation


// ============================================================
// 7. FUNCTION PARAMETERS                        [INTERMEDIATE]
// ============================================================
// INTERVIEW: "What happens when you pass fewer/more args than params?"
//   Fewer: missing params are `undefined`
//   More:  extra args ignored (but available in `arguments`)

function sumParams(a, b) {
  console.log(a); // 1
  console.log(b); // undefined
  return a + b;
}
console.log(sumParams(1)); // NaN (1 + undefined)

// --- Default parameters ---
function sumDefault(a, b = 0) {
  return a + b;
}
console.log(sumDefault(1));            // 1
console.log(sumDefault(1, undefined)); // 1 (undefined triggers default)
console.log(sumDefault(1, null));      // 1 (null does NOT trigger default)

// --- Destructured parameters ---
function greetObj({ name }) {
  return `Hello, ${name}!`;
}
console.log(greetObj({ name: 'John' })); // "Hello, John!"

// With default for the whole parameter (prevents TypeError on missing arg)
function greetSafe({ name = 'Unknown' } = {}) {
  return `Hello, ${name}!`;
}
console.log(greetSafe()); // "Hello, Unknown!"

// Array destructuring in params
function greetFirst([{ name }]) {
  return `Hello, ${name}!`;
}
console.log(greetFirst([{ name: 'John' }, { name: 'Jane' }])); // "Hello, John!"

// --- arguments object ---
// INTERVIEW: "Why is `arguments` not a real array?"
function sumArgs() {
  console.log(arguments); // { 0: 5, 1: 6, length: 2 }
  let total = 0;
  for (let i = 0; i < arguments.length; i++) total += arguments[i];
  return total;
}
console.log(sumArgs(5, 6)); // 11
// Convert to real array: [...arguments] or Array.from(arguments)

// GOTCHAS -- Parameters
// - `null` does NOT trigger default params (only `undefined` does)
// - arguments is NOT available in arrow functions
// - arguments reflects the actual passed args, not the param defaults
// - Rest params (...args) are preferred over arguments in modern JS


// ============================================================
// 8. PASS-BY-VALUE SEMANTICS                    [INTERMEDIATE]
// ============================================================
// INTERVIEW: "Is JS pass-by-value or pass-by-reference?"
// Answer: ALWAYS pass-by-value. For objects the *value* is a
// reference (pointer), so mutations inside the function are
// visible outside, but reassigning the parameter does NOT
// change the original binding.
//
//  +------------------------------------------------------+
//  |  Primitive (pass copy)     |  Object (pass ref copy) |
//  |----------------------------+-------------------------|
//  |  let y = 10;               |  let obj = {a:1};       |
//  |  fn(y);                    |  fn(obj);               |
//  |  // y is still 10          |  // obj.a may change    |
//  |  // fn cannot change y     |  // fn cannot replace   |
//  |                            |  //   obj itself        |
//  +------------------------------------------------------+

// --- 8a. Primitives: a COPY is passed ---
function squarePrim(x) {
  x = x * x;
  return x;
}
let y = 10;
let result1 = squarePrim(y);
console.log(y);       // 10 -- unchanged
console.log(result1); // 100

// --- 8b. Objects: a copy of the REFERENCE is passed ---
let person = { name: "john", age: 25 };

function increaseAge(obj) {
  obj.age += 1;          // mutates the original object
  // obj = { name: "jane", age: 22 };  // would NOT replace `person`
}
increaseAge(person);
console.log(person); // { name: "john", age: 26 }

// GOTCHAS -- Pass-by-Value
// - Array.push/splice inside a function mutates the original array
// - Spread/Object.assign create SHALLOW copies only
// - structuredClone() creates deep copies (ES2022+)


// ============================================================
// 9. CALLBACKS (Sync & Async)                   [INTERMEDIATE]
// ============================================================
// INTERVIEW: "Explain synchronous vs asynchronous callbacks."
//
//  +-------------------------------------------------------------+
//  | Sync callback                | Async callback               |
//  |------------------------------+-------------------------------|
//  | Blocks higher-order fn       | Does NOT block               |
//  | Runs within the call         | Runs later (event loop)      |
//  | array.map, .filter, .reduce  | setTimeout, addEventListener |
//  | Returns immediately          | Returns via callback/promise  |
//  +-------------------------------------------------------------+

// --- Sync callback ---
function mapImpl(arr, callback) {
  const result = [];
  for (const item of arr) {
    result.push(callback(item));
  }
  return result;
}

function greetPerson(name) {
  return `Hello ${name}`;
}

const persons = ['Ana', 'Elena'];
console.log(mapImpl(persons, greetPerson));
// ["Hello Ana", "Hello Elena"]

// Sync callbacks on arrays
const nameStartingA = persons.find((name) => name[0].toLowerCase() === 'a');
console.log(nameStartingA); // "Ana"

const countStartingA = persons.reduce(
  (count, name) => (name[0].toLowerCase() === 'a' ? count + 1 : count), 0
);
console.log(countStartingA); // 1

// String callback
const replaced = 'Cristina'.replace(/./g, (ch) =>
  ch.toLowerCase() === 'i' ? '1' : ch
);
console.log(replaced); // "Cr1st1na"

// --- Async callback ---
// setTimeout(function later() { console.log('2 sec passed'); }, 2000);
// setInterval(function repeat() { console.log('every 2 sec'); }, 2000);

// --- Async function as callback ---
async function fetchUserNames() {
  const resp = await fetch('https://api.github.com/users?per_page=5');
  const users = await resp.json();
  return users.map(({ login }) => login);
}
// button.addEventListener('click', fetchUserNames);


// ============================================================
// 10. HIGHER-ORDER FUNCTIONS                    [INTERMEDIATE]
// ============================================================
// INTERVIEW: "What is a higher-order function?"
// A function that takes a function as argument OR returns a function.
//
//  First-order:  operates on data (numbers, strings, objects)
//  Higher-order: operates on functions

function calculate(operation, initialValue, nums) {
  let total = initialValue;
  for (const n of nums) total = operation(total, n);
  return total;
}

function sumHOF(a, b)      { return a + b; }
function multiplyHOF(a, b) { return a * b; }

console.log(calculate(sumHOF, 0, [1, 2, 4]));      // 7
console.log(calculate(multiplyHOF, 1, [1, 2, 4])); // 8

// Built-in higher-order: Array.prototype.map, filter, reduce, sort,
// forEach, find, some, every, flatMap


// ============================================================
// 11. ARROW FUNCTIONS                           [INTERMEDIATE]
// ============================================================
// INTERVIEW: "List the differences between arrow and regular functions."
//
//  Arrow functions:
//  - NO own `this` (lexical, from enclosing scope)
//  - NO `arguments` object (use rest params ...args)
//  - CANNOT be used as constructors (no `new`)
//  - CANNOT be generators (no function*)
//  - Implicit return for single-expression body
//
//  ASCII diagram -- `this` in arrow vs regular:
//
//  const obj = {
//    method() {           <-- `this` = obj
//      [1].forEach(() => {
//        this             <-- `this` = obj (lexical, arrow inherits)
//      });
//      [1].forEach(function() {
//        this             <-- `this` = global/undefined (own `this`)
//      });
//    }
//  };

const numbers = [4, 5, 2, 6];
const doubled = numbers.map((n) => n * 2);
console.log(doubled); // [8, 10, 4, 12]

// --- Lexical `this` (arrow) ---
const objectArrow = {
  items: [1, 2],
  method() {
    this.items.forEach(() => {
      console.log("arrow this === object:", this === objectArrow); // true
    });
  }
};
objectArrow.method();

// --- Dynamic `this` (regular) ---
const objectRegular = {
  items: [1, 2],
  method() {
    this.items.forEach(function () {
      console.log("regular this:", this); // global or undefined (strict)
    });
  }
};
objectRegular.method();

// --- `arguments` not available in arrow ---
function regular() {
  const arrow = () => { console.log(arguments); }; // outer arguments
  arrow('C');
}
regular('A', 'B'); // logs ['A', 'B'] -- the OUTER arguments

// Fix: use rest params
function regular1() {
  const arrow = (...args) => { console.log(args); };
  arrow('C');
}
regular1('A', 'B'); // logs ['C'] -- the arrow's OWN args

// --- Arrow class pattern for lexical `this` ---
class Numbers {
  constructor(array) {
    this.array = array;
  }
  addNumber(number) {
    if (number !== undefined) this.array.push(number);
    return (n) => { this.array.push(n); }; // arrow captures `this`
  }
}
let numObj = new Numbers([]);
const addMethod1 = numObj.addNumber();
addMethod1(1);
addMethod1(5);
console.log(numObj.array); // [1, 5]

// --- Async arrow function ---
const fetchMovies = async () => {
  const response = await fetch('/api/movies');
  const movies = await response.json();
  return movies;
};


// ============================================================
// 12. WHEN NOT TO USE ARROW FUNCTIONS           [INTERMEDIATE]
// ============================================================
// INTERVIEW: "Give examples where arrow functions cause bugs."

// 12a. Object literal methods -- `this` is global/undefined
const calcBroken = {
  array: [1, 2, 3],
  sum: () => {
    // `this` is NOT calcBroken -- it's the enclosing scope
    // return this.array.reduce(...)  // TypeError!
  }
};
// Fix: use shorthand method
const calcFixed = {
  array: [1, 2, 3],
  sum() {
    return this.array.reduce((a, b) => a + b);
  }
};
console.log(calcFixed.sum()); // 6

// 12b. Prototype methods
function MyCat(name) { this.catName = name; }
// BAD:  MyCat.prototype.say = () => { return this.catName; };
// GOOD:
MyCat.prototype.say = function () { return this.catName; };
const cat = new MyCat('Mew');
console.log(cat.say()); // "Mew"

// 12c. Event handlers needing `this` as the element
// BAD:  button.addEventListener('click', () => { this.innerHTML = '...' });
// GOOD: button.addEventListener('click', function() { this.innerHTML = '...' });

// 12d. Constructors
// const User = (name) => { this.name = name; };
// new User('x')  // TypeError: User is not a constructor
function User(name) { this.name = name; }
const user = new User('Eric');
console.log(user instanceof User); // true


// ============================================================
// 13. METHODS IN JAVASCRIPT                     [INTERMEDIATE]
// ============================================================
// A method is a function stored as an object property.
//
//  INTERVIEW: "What happens to `this` when you extract a method?"
//
//  ASCII diagram -- method extraction loses `this`:
//
//  const obj = { name: 'A', greet() { return this.name; } };
//
//  obj.greet()         --> this = obj           --> "A"
//  const fn = obj.greet;
//  fn()                --> this = global/undef  --> undefined
//  fn.call(obj)        --> this = obj           --> "A"
//  fn.bind(obj)()      --> this = obj           --> "A"
//
//  Common traps where `this` is lost:
//    setTimeout(obj.method, 1000)
//    button.addEventListener('click', obj.method)
//    <button onClick={obj.method}>  (React)
//    const fn = obj.method;  fn();

// Object literal methods
const world = {
  who: 'World',
  greet() { return `Hello, ${this.who}!`; }
};
console.log(world.greet()); // "Hello, World!"

// Adding methods dynamically
world.farewell = function () {
  return `Good bye, ${this.who}!`;
};
console.log(world.farewell()); // "Good bye, World!"

// Class methods
class Greeter {
  constructor(who) { this.who = who; }
  greet() { return `Hello, ${this.who}!`; }
}
const myGreeter = new Greeter('World');
console.log(myGreeter.greet()); // "Hello, World!"

// Arrow function as method -- BAD (lexical `this` = enclosing, not object)
const world4 = {
  who: 'World',
  greet: () => `Hello, ${this.who}!` // `this` is NOT world4
};
console.log(world4.greet()); // "Hello, undefined!"


// ============================================================
// 14. FUNCTION OBJECT: length, prototype, new.target [INTERMEDIATE]
// ============================================================
// INTERVIEW: "What is new.target?"
//
// Every function is an instance of Function. Key properties:
//  .length     -- number of declared parameters (before defaults/rest)
//  .prototype  -- object used when function is called with `new`
//  .name       -- the function's name (inferred or explicit)
//
// new.target -- meta-property available inside a function:
//   - undefined when called normally:  fn()
//   - references the constructor when called with new: new fn()

function addNums(a, b) {
  console.log("new.target:", new.target);
  return a + b;
}

console.log(addNums instanceof Function); // true
console.log(addNums.length);              // 2
console.log(addNums.prototype);           // {}

let result2 = addNums(10, 20);  // new.target: undefined
console.log(result2);           // 30

let result3 = new addNums(10, 30); // new.target: [Function: addNums]
console.log(result3);              // addNums {} (an object)

// Guard: prevent function from being used as constructor
function safeAdd(a, b) {
  if (new.target) {
    throw new TypeError('safeAdd cannot be invoked with new');
  }
  return a + b;
}

// GOTCHAS -- Function Object
// - Rest params and default params do NOT count toward .length
//     (function(a, b = 1, ...c) {}).length  // 1
// - Arrow functions have .length but no .prototype


// ============================================================
// 15. call() / apply() / bind()                 [INTERMEDIATE]
// ============================================================
// INTERVIEW: "Explain the difference between call, apply, and bind."
//
//  +-------------------------------------------------------------+
//  |  Method  | Invokes? | Args format     | Returns             |
//  |----------+----------+-----------------+---------------------|
//  |  call()  |  YES     | comma-separated | function result     |
//  |  apply() |  YES     | array / iterable| function result     |
//  |  bind()  |  NO      | comma-separated | NEW bound function  |
//  +-------------------------------------------------------------+
//
//  Mnemonic:
//    Call  = Commas       (individual args)
//    Apply = Array        (args as array)
//    Bind  = Binds & waits (returns new fn)

// --- 15a. call() --------------------------------------------------
// fn.call(thisArg, arg1, arg2, ...)

let result4 = addNums.call(null, 10, 50);
console.log(result4); // 60

var greeting = "hi";
var messageObj = { greeting: "hello" };

function say(name) {
  console.log(this.greeting + ' ' + name);
}

say.call(this, "shubham");       // "hi shubham" (global this)
say.call(messageObj, "shubham"); // "hello shubham"

// Using call() to chain constructors (classical inheritance)
function Box(height, width) {
  this.height = height;
  this.width = width;
}

function Widget(height, width, color) {
  Box.call(this, height, width); // borrow Box's initialization
  this.color = color;
}

let widget = new Widget(10, 20, 'red');
console.log(widget); // Widget { height: 10, width: 20, color: 'red' }

// --- 15b. apply() -------------------------------------------------
// fn.apply(thisArg, [arg1, arg2, ...])

const person1 = { firstName: 'John', lastName: 'Wick' };

function greet(greeting, message) {
  return `${greeting} ${this.firstName}. ${message}`;
}

console.log(greet.apply(person1, ["Welcome", "Home"]));
// "Welcome John. Home"

// Classic trick: push elements from one array to another
let arr = [1, 2, 3];
let moreNums = [4, 5, 6];
arr.push.apply(arr, moreNums);
console.log(arr); // [1, 2, 3, 4, 5, 6]
// Modern alternative: arr.push(...moreNums)

// Math.max with apply
console.log(Math.max.apply(null, [5, 2, 9, 1])); // 9
// Modern alternative: Math.max(...[5, 2, 9, 1])

// --- 15c. bind() --------------------------------------------------
// fn.bind(thisArg, ...partialArgs) --> returns new function
//
// INTERVIEW: "How does bind() solve the lost `this` problem?"
//
//  Without bind:
//  +-----------+     setTimeout     +-----------+
//  |  obj      |  -- passes fn --> |  global    |
//  |  .method  |     (detached)    |  context!  |
//  +-----------+                   +-----------+
//
//  With bind:
//  +-----------+     setTimeout     +-----------+
//  |  obj      |  -- bound fn -->  |  obj       |
//  |  .method  |     (locked)      |  context   |
//  +-----------+                   +-----------+

let person3 = {
  name: "John Doe",
  getName: function () {
    console.log(this.name);
  }
};

// Problem: `this` is lost when method is passed as callback
setTimeout(person3.getName, 100); // undefined (lost this)

// Fix 1: wrap in arrow function (captures `this` lexically)
setTimeout(() => { person3.getName(); }, 200);

// Fix 2: bind
let boundGetName = person3.getName.bind(person3);
setTimeout(boundGetName, 300); // "John Doe"

// Using bind() to borrow methods
let runner = {
  name: "Runner",
  run: function (speed) {
    console.log(this.name + ' runs at ' + speed + 'mph');
  }
};

let flyer = { name: "Flyer" };

let run = runner.run.bind(flyer, 20); // partial application with bind
run(); // "Flyer runs at 20mph"

// --- 15d. Partial application with bind ---
function multiply(a, b) {
  return a * b;
}
const double = multiply.bind(null, 2);
const triple = multiply.bind(null, 3);
console.log(double(5));  // 10
console.log(triple(5));  // 15

// Indirect invocation: call / apply on standalone function
function greetFn() { return `Hello, ${this.who}!`; }
const aliens = { who: 'Aliens' };
console.log(greetFn.call(aliens));  // "Hello, Aliens!"
console.log(greetFn.apply(aliens)); // "Hello, Aliens!"

// Bound function
const greetAliens = greetFn.bind(aliens);
console.log(greetAliens()); // "Hello, Aliens!"

// GOTCHAS -- call / apply / bind
// - bind() returns a NEW function; it does not modify the original
// - A bound function cannot be re-bound to a different `this`
//     const f = fn.bind(obj1); f.bind(obj2)  // still uses obj1
// - In strict mode, `this` in call/apply is exactly what you pass
//   (null stays null); in sloppy mode, null/undefined becomes global
// - Arrow functions ignore call/apply/bind for `this` (lexical)


// ============================================================
// 16. FUNCTION INVOCATION PATTERNS & `this`         [ADVANCED]
// ============================================================
//
//  +------------------------------------------------------------+
//  | Pattern              | `this` value                        |
//  |----------------------+-------------------------------------|
//  | fn()                 | global (sloppy) / undefined (strict)|
//  | obj.fn()             | obj                                 |
//  | fn.call(ctx, ...)    | ctx                                 |
//  | fn.apply(ctx, [...]) | ctx                                 |
//  | fn.bind(ctx)(...)    | ctx                                 |
//  | new Fn()             | new instance                        |
//  | () => {}             | enclosing lexical `this`            |
//  +------------------------------------------------------------+
//
// INTERVIEW: "List the ways `this` can be determined in JS."
// Priority (highest first):
//   1. new binding        -> new instance
//   2. explicit binding   -> call/apply/bind
//   3. implicit binding   -> obj.method()
//   4. default binding    -> global / undefined
//   * arrow functions     -> lexical (ignores all above)


// ============================================================
// 17. GENERATOR FUNCTIONS                       [INTERMEDIATE]
// ============================================================
// INTERVIEW: "What is a generator and how does yield work?"
//
// A generator returns an iterator. Each yield pauses execution
// and returns { value, done }. Calling .next() resumes.
//
//  Execution flow:
//  gen.next() --> runs until yield --> { value: X, done: false }
//  gen.next() --> runs until yield --> { value: Y, done: false }
//  gen.next() --> runs until end   --> { value: undefined, done: true }

// Declaration form
function* indexGenerator() {
  let index = 0;
  while (true) yield index++;
}
const g = indexGenerator();
console.log(g.next().value); // 0
console.log(g.next().value); // 1

// Expression form
const indexGen2 = function* () {
  let i = 0;
  while (true) yield i++;
};
const g1 = indexGen2();
console.log(g1.next().value); // 0

// Shorthand method form
const genObj = {
  *indexGenerator() {
    let i = 0;
    while (true) yield i++;
  }
};
const g2 = genObj.indexGenerator();
console.log(g2.next().value); // 0

// Finite generator
function* range(start, end) {
  for (let i = start; i <= end; i++) yield i;
}
console.log([...range(1, 5)]); // [1, 2, 3, 4, 5]


// ============================================================
// 18. CLOSURES IN CALLBACKS                         [ADVANCED]
// ============================================================
// INTERVIEW: "Explain closures with a practical example."
//
//  ASCII diagram -- closure captures outer scope:
//
//  function outer(x) {
//    return function inner(y) {   <-- inner "closes over" x
//      return x + y;              <-- x is still accessible
//    };                               even after outer returns
//  }
//
//  Call stack + closure:
//  +------------------+
//  | outer(10)        |  x = 10
//  |  returns inner   |
//  +------------------+  <-- outer pops off stack
//  | inner(5)         |  y = 5, x = 10 (from closure)
//  |  returns 15      |
//  +------------------+

function createCounter(initial = 0) {
  let count = initial; // closed over by increment/decrement/getCount
  return {
    increment: () => ++count,
    decrement: () => --count,
    getCount:  () => count,
  };
}
const ctr = createCounter(10);
console.log(ctr.increment()); // 11
console.log(ctr.increment()); // 12
console.log(ctr.decrement()); // 11
console.log(ctr.getCount());  // 11

// Classic closure gotcha: loop variable
// BAD: all callbacks log 3
for (var i = 0; i < 3; i++) {
  setTimeout(function () { console.log('var loop:', i); }, 0);
}
// logs: 3, 3, 3  (var is function-scoped, shared)

// FIX 1: use let (block-scoped)
for (let j = 0; j < 3; j++) {
  setTimeout(function () { console.log('let loop:', j); }, 0);
}
// logs: 0, 1, 2

// FIX 2: IIFE closure
for (var k = 0; k < 3; k++) {
  (function (captured) {
    setTimeout(function () { console.log('IIFE loop:', captured); }, 0);
  })(k);
}
// logs: 0, 1, 2


// ============================================================
// 19. CURRYING                                      [ADVANCED]
// ============================================================
// INTERVIEW: "What is currying?"
// Transforming f(a, b, c) into f(a)(b)(c).
// Each call returns a new function that takes the next argument.
//
//  Normal:  add(2, 3, 4)  --> 9
//  Curried: add(2)(3)(4)  --> 9
//
//  ASCII diagram -- currying pipeline:
//
//  add(2)      --> returns fn(b)
//  add(2)(3)   --> returns fn(c)
//  add(2)(3)(4)--> returns 9

// Manual currying
function addCurried(a) {
  return function (b) {
    return function (c) {
      return a + b + c;
    };
  };
}
console.log(addCurried(2)(3)(4)); // 9

// Arrow syntax (concise)
const addCurriedArrow = (a) => (b) => (c) => a + b + c;
console.log(addCurriedArrow(2)(3)(4)); // 9

// Practical use: property accessor
let userObj = { name: "shubham", age: 30 };
function getUserInfo(obj) {
  return function (key) {
    return obj[key];
  };
}
console.log(getUserInfo(userObj)("name")); // "shubham"

// Generic curry utility
function curry(fn) {
  return function curried(...args) {
    if (args.length >= fn.length) {
      return fn.apply(this, args);
    }
    return function (...args2) {
      return curried.apply(this, args.concat(args2));
    };
  };
}

function addThree(a, b, c) { return a + b + c; }
const curriedAdd = curry(addThree);
console.log(curriedAdd(1)(2)(3));   // 6
console.log(curriedAdd(1, 2)(3));   // 6
console.log(curriedAdd(1)(2, 3));   // 6
console.log(curriedAdd(1, 2, 3));   // 6


// ============================================================
// 20. PARTIAL APPLICATION                           [ADVANCED]
// ============================================================
// INTERVIEW: "What is the difference between currying and partial application?"
//
//  +-------------------------------------------------------------+
//  | Concept             | Description                           |
//  |---------------------+---------------------------------------|
//  | Currying            | Always unary: f(a)(b)(c)              |
//  |                     | Transforms to chain of single-arg fns |
//  | Partial Application | Fix SOME args, return fn for the rest |
//  |                     | Can fix 1, 2, or N args at once       |
//  +-------------------------------------------------------------+
//
//  Example contrast:
//    curry(f)(1)(2)(3)         -- one arg at a time
//    partial(f, 1, 2)(3)      -- two args fixed, one left

// Generic partial utility
function partial(fn, ...presetArgs) {
  return function (...laterArgs) {
    return fn(...presetArgs, ...laterArgs);
  };
}

function volume(l, w, h) { return l * w * h; }
const area2D = partial(volume, 1);     // fix height = 1
console.log(area2D(3, 4));             // 12

const fixedBox = partial(volume, 2, 3); // fix l=2, w=3
console.log(fixedBox(4));               // 24

// bind() is also partial application (see section 15d above)
// const double = multiply.bind(null, 2);


// ============================================================
// 21. FUNCTION COMPOSITION (pipe / compose)         [ADVANCED]
// ============================================================
// INTERVIEW: "What is function composition?"
// Combining simple functions to build complex operations.
// compose: right-to-left     compose(f, g)(x) = f(g(x))
// pipe:    left-to-right     pipe(f, g)(x) = g(f(x))
//
//  ASCII diagram -- data flow:
//
//  compose(toUpper, trim, greet)("  world  ")
//       greet  --->  trim  --->  toUpper
//    "hi   world  " -> "hi world" -> "HI WORLD"
//
//  pipe(greet, trim, toUpper)("  world  ")
//       greet  --->  trim  --->  toUpper    (same order as reading)

// compose: right-to-left
const compose = (...fns) => (x) =>
  fns.reduceRight((acc, fn) => fn(acc), x);

// pipe: left-to-right (more readable)
const pipe = (...fns) => (x) =>
  fns.reduce((acc, fn) => fn(acc), x);

const trim = (s) => s.trim();
const toLowerCase = (s) => s.toLowerCase();
const split = (sep) => (s) => s.split(sep);

const processInput = pipe(trim, toLowerCase, split(' '));
console.log(processInput('  Hello World  ')); // ["hello", "world"]

// compose equivalent (reverse order)
const processInput2 = compose(split(' '), toLowerCase, trim);
console.log(processInput2('  Hello World  ')); // ["hello", "world"]

// Real-world: data transformation pipeline
const doubleNum = (x) => x * 2;
const increment = (x) => x + 1;
const squareNum = (x) => x * x;

const transform = pipe(doubleNum, increment, squareNum);
console.log(transform(3)); // square(increment(double(3))) = square(7) = 49

// GOTCHAS -- Composition
// - Functions must be unary (single arg) for simple compose/pipe
// - For multi-arg, combine with currying or partial application
// - Error handling: wrap in try/catch or use Result/Either monads


// ============================================================
// 22. THUNKS                                        [ADVANCED]
// ============================================================
// INTERVIEW: "What is a thunk?"
// A thunk is a function that wraps a computation to delay its
// execution. It takes no arguments and returns a value.
//
//  Eager:   const val = expensiveCalc();       // runs NOW
//  Lazy:    const thunk = () => expensiveCalc(); // runs LATER
//           const val = thunk();               // runs when needed
//
// Used in: Redux-Thunk, lazy evaluation, trampolining

// Simple thunk: deferred computation
const apiThunk = () => fetch('/api/data').then(r => r.json());
// apiThunk();  // only fetches when called

// Redux-style thunk (action creator returns a function)
function fetchUser(userId) {
  // Returns a thunk (function) instead of an action (object)
  return function thunk(dispatch) {
    dispatch({ type: 'FETCH_USER_START' });
    return fetch(`/api/users/${userId}`)
      .then(r => r.json())
      .then(user => dispatch({ type: 'FETCH_USER_SUCCESS', payload: user }))
      .catch(err => dispatch({ type: 'FETCH_USER_ERROR', payload: err }));
  };
}

// Thunk for lazy initialization
function lazyInit(factory) {
  let value;
  let initialized = false;
  return () => {
    if (!initialized) {
      value = factory();
      initialized = true;
    }
    return value;
  };
}
const getConfig = lazyInit(() => {
  console.log('Computing config...');
  return { debug: true, version: '1.0' };
});
// getConfig();  // logs "Computing config..." (first call only)
// getConfig();  // returns cached value, no log


// ============================================================
// 23. PURE vs IMPURE FUNCTIONS                      [ADVANCED]
// ============================================================
// INTERVIEW: "What is a pure function?"
// 1. Same input always produces same output (deterministic)
// 2. No side effects (no mutation, no I/O, no external state)
//
//  +-------------------------------------------------------------+
//  | Pure                          | Impure                      |
//  |-------------------------------+-----------------------------|
//  | function add(a, b) {          | let total = 0;              |
//  |   return a + b;               | function add(x) {           |
//  | }                             |   total += x; // side effect|
//  |                               |   return total;             |
//  |                               | }                           |
//  |-------------------------------+-----------------------------|
//  | Math.max(1, 2)                | Math.random()               |
//  | [1,2,3].map(x => x*2)        | console.log('hi')           |
//  | str.toUpperCase()             | Date.now()                  |
//  | Object.freeze({a:1})          | arr.push(4)                 |
//  +-------------------------------------------------------------+

// Pure: no side effects, deterministic
function pureAdd(a, b) {
  return a + b;
}

function pureFilter(arr, predicate) {
  return arr.filter(predicate); // .filter returns NEW array
}

// Impure: mutates external state
let counter = 0;
function impureIncrement() {
  counter++; // side effect: mutates external variable
  return counter;
}

// Impure: depends on external state
function impureGreet(name) {
  const hour = new Date().getHours(); // non-deterministic
  if (hour < 12) return `Good morning, ${name}`;
  return `Good afternoon, ${name}`;
}

// Making impure functions pure: inject dependencies
function pureGreet(name, hour) {
  if (hour < 12) return `Good morning, ${name}`;
  return `Good afternoon, ${name}`;
}

// GOTCHAS -- Purity
// - Array methods that MUTATE: push, pop, shift, splice, sort, reverse
// - Array methods that are PURE: map, filter, reduce, slice, concat
// - Object.assign mutates the first arg; use spread for purity


// ============================================================
// 24. FUNCTION OVERLOADING PATTERNS IN JS           [ADVANCED]
// ============================================================
// INTERVIEW: "Does JS support function overloading?"
// No. JS does not have built-in overloading like Java/C++.
// Defining two functions with the same name: the second overwrites the first.
// But there are PATTERNS to achieve similar behavior:

// Pattern 1: Check arguments count / types
function formatDate(input) {
  if (typeof input === 'string') {
    return new Date(input).toISOString();
  }
  if (input instanceof Date) {
    return input.toISOString();
  }
  if (typeof input === 'number') {
    return new Date(input).toISOString();
  }
  throw new TypeError('Unsupported input type');
}

// Pattern 2: Options object (most common in JS)
function createElement(tag, options = {}) {
  const { className = '', id = '', text = '' } = options;
  return `<${tag} class="${className}" id="${id}">${text}</${tag}>`;
}
console.log(createElement('div', { className: 'box', text: 'Hello' }));
// <div class="box" id="">Hello</div>

// Pattern 3: Default parameters
function greetOverload(name, greeting = 'Hello') {
  return `${greeting}, ${name}!`;
}
console.log(greetOverload('Alice'));           // "Hello, Alice!"
console.log(greetOverload('Alice', 'Howdy'));  // "Howdy, Alice!"

// Pattern 4: Rest parameters + conditional logic
function sumOverloaded(...args) {
  if (args.length === 1 && Array.isArray(args[0])) {
    return args[0].reduce((a, b) => a + b, 0); // sum([1,2,3])
  }
  return args.reduce((a, b) => a + b, 0);       // sum(1,2,3)
}
console.log(sumOverloaded(1, 2, 3));    // 6
console.log(sumOverloaded([1, 2, 3]));  // 6


// ============================================================
// 25. new Function CONSTRUCTOR                      [ADVANCED]
// ============================================================
// INTERVIEW: Rarely used. Creates functions from strings at runtime.
// Useful for dynamic code, templates, or sandboxing. Security risk!

const sumFromStr = new Function('a', 'b', 'return a + b');
console.log(sumFromStr(10, 15)); // 25
console.log(typeof sumFromStr === 'function'); // true

// GOTCHAS -- new Function
// - Does NOT have access to local scope (only global)
// - Similar security risks to eval()
// - Never use with user-supplied strings


// ============================================================
// 26. GENERAL FUNCTION GOTCHAS                      [ADVANCED]
// ============================================================
//
// --- Hoisting & Declarations ---
// 1. Hoisting: function DECLARATIONS are hoisted fully;
//    function EXPRESSIONS (const fn = ...) are NOT.
//
// --- arguments Object ---
// 2. arguments object:
//    - Available in regular functions, NOT in arrow functions
//    - Is array-LIKE, not a real Array (use [...arguments] or
//      Array.from(arguments) to convert)
//
// --- Duplicate Parameters ---
// 3. Duplicate parameter names are allowed in sloppy mode
//    but throw in strict mode:
//      function f(a, a) {}     // OK in sloppy
//      'use strict';
//      function f(a, a) {}     // SyntaxError
//
// --- Default Parameters ---
// 4. Default params create their own scope:
//      let x = 1;
//      function f(a = x) { let x = 2; return a; }
//      f(); // 1, not 2
//
// 5. Default params are evaluated at CALL time, not definition time:
//      function f(arr = []) { arr.push(1); return arr; }
//      f(); // [1]   f(); // [1]  (fresh array each time -- safe!)
//
// --- typeof ---
// 6. typeof returns 'function' for functions, even though
//    they are objects (typeof null === 'object' is the
//    famous JS quirk, this is the "nice" quirk).
//
// --- Arrow Function Pitfalls ---
// 7. Implicit return in arrow functions:
//      const fn = () => ({ key: 'val' });  // wrap object in ()
//      const fn = () => { key: 'val' };    // BUG: labeled statement, returns undefined
//
// 8. Rest params must be last:
//      function f(...rest, last) {}  // SyntaxError
//
// 9. Generator arrow functions do NOT exist:
//      const gen = *() => { yield 1; };  // SyntaxError
//
// 10. Recursive arrow functions need a name binding:
//      const fib = (n) => n <= 1 ? n : fib(n-1) + fib(n-2);
//      // Works because `fib` is in scope via the const binding
