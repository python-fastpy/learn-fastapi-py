// ============================================================
//  `this` KEYWORD - ULTIMATE QUICK REFERENCE
// ============================================================
//  `this` is determined by HOW a function is CALLED, not where
//  it is defined (except arrow functions).
// ============================================================


// ============================================================
//  DECISION TREE: "What is `this`?"
// ============================================================
//
//  Is it an arrow function?
//  |-- YES --> `this` = enclosing lexical scope's `this` (FIXED, cannot change)
//  |-- NO  --> How is the function called?
//      |
//      |-- new Foo()          --> `this` = newly created object
//      |-- foo.call(obj) /    --> `this` = obj (first argument)
//      |   foo.apply(obj) /
//      |   foo.bind(obj)()
//      |-- obj.foo()          --> `this` = obj (object before the dot)
//      |-- foo()              --> `this` = window (sloppy) / undefined (strict)
//
//  Priority (highest wins):
//  1. new binding          (new Foo())
//  2. explicit binding     (call/apply/bind)
//  3. implicit binding     (obj.foo())
//  4. default binding      (plain foo())
//
// ============================================================


// ============================================================
//  ALL 5 BINDING RULES - COMPARISON TABLE
// ============================================================
//
//  +--------------------+--------------------+-------------------+------------------+
//  | RULE               | SYNTAX             | `this` VALUE      | CAN OVERRIDE?    |
//  +--------------------+--------------------+-------------------+------------------+
//  | Default            | foo()              | window / undefined| Yes (all methods)|
//  | Implicit           | obj.foo()          | obj               | Yes (all methods)|
//  | Explicit           | foo.call(obj)      | obj               | Yes (new only)   |
//  | Hard Bind          | foo.bind(obj)()    | obj               | Yes (new only)   |
//  | new Binding        | new Foo()          | new object        | N/A (highest)    |
//  | Arrow (lexical)    | () => {}           | enclosing `this`  | No (permanent)   |
//  +--------------------+--------------------+-------------------+------------------+


// ============================================================
// 1. DEFAULT BINDING - Function Invocation            [BASIC]
// ============================================================
// INTERVIEW: "What is `this` in a regular function call?"
// `this` is the global object (window) in sloppy mode, undefined in strict mode.

function hello(name) {
  return 'Hello ' + name + '!';
}
const message = hello("shubham");
console.log(message); // "Hello shubham!"

// Function invocation: no dot, no new, no call/apply
function sum(a, b) {
  console.log(this === window); // true (sloppy mode)
  this.myNumber = 20;           // adds property to global object!
  return a + b;
}
sum(15, 16);
console.log(window.myNumber); // 20


// ============================================================
// 2. DEFAULT BINDING - Strict Mode                    [BASIC]
// ============================================================
// `this` is undefined in strict mode function invocation.

function multiply(a, b) {
  'use strict';
  console.log(this === undefined); // true
  return a * b;
}
multiply(2, 5); // 10

// Strict mode propagates to inner functions:
function execute() {
  'use strict';
  function concat(str1, str2) {
    console.log(this === undefined); // true
    return str1 + str2;
  }
  concat('Hello', ' World!');
}
execute();


// ============================================================
// 3. IMPLICIT BINDING - Method Invocation             [BASIC]
// ============================================================
// INTERVIEW: "What is `this` in a method call?"
// `this` = the object BEFORE the dot.

const calc = {
  num: 0,
  increment() {
    console.log(this === calc); // true
    this.num += 1;
    return this.num;
  }
};
calc.increment(); // 1
calc.increment(); // 2

// Method invocation vs function invocation:
const myObject = {
  helloMethod: function() { return 'Hello World!'; }
};
const message1 = myObject.helloMethod(); // method invocation

const words = ['Hello', 'World'];
words.join(', ');        // method invocation

const obj = {
  myMethod() { return new Date().toString(); }
};
obj.myMethod();          // method invocation
const func = obj.myMethod;
func();                  // FUNCTION invocation (this = window/undefined)
parseFloat('16.6');      // function invocation
isNaN(0);                // function invocation

// Inherited methods: `this` = the object the method is called ON
const myDog = Object.create({
  sayName() {
    console.log(this === myDog); // true
    return this.name;
  }
});
myDog.name = 'Milo';
myDog.sayName(); // 'Milo'

// ES2015 class methods:
class Planet {
  constructor(name) { this.name = name; }
  getName() {
    console.log(this === earth); // true
    return this.name;
  }
}
const earth = new Planet('Earth');
earth.getName(); // 'Earth'


// ============================================================
// 4. IMPLICIT BINDING LOSS (The #1 `this` Trap) [INTERMEDIATE]
// ============================================================
// INTERVIEW: "What happens when you extract a method from an object?"
//
//  When you detach a method, it becomes a plain function invocation.
//
//     obj.method() --> `this` = obj
//     const fn = obj.method; fn() --> `this` = window/undefined

function Pet(type, legs) {
  this.type = type;
  this.legs = legs;
  this.logInfo = function() {
    console.log(this === myCat); // false when detached!
    console.log(`The ${this.type} has ${this.legs} legs`);
  };
}
const myCat = new Pet('Cat', 4);
setTimeout(myCat.logInfo, 1000); // "The undefined has undefined legs"

// FIX 1: .bind()
const boundLogInfo = myCat.logInfo.bind(myCat);
setTimeout(boundLogInfo, 1000); // "The Cat has 4 legs"

// FIX 2: Arrow function in constructor
function Pet2(type, legs) {
  this.type = type;
  this.legs = legs;
  this.logInfo = () => {
    console.log(`The ${this.type} has ${this.legs} legs`);
  };
}

// FIX 3: Arrow function as class field (modern, recommended)
class Pet3 {
  constructor(type, legs) {
    this.type = type;
    this.legs = legs;
  }
  logInfo = () => {
    console.log(`The ${this.type} has ${this.legs} legs`);
  };
}


// ============================================================
// 5. INNER FUNCTION `this` TRAP                 [INTERMEDIATE]
// ============================================================
// INTERVIEW: "Why doesn't `this` work in nested functions?"

const numbers = {
  numberA: 5,
  numberB: 10,
  sum: function() {
    console.log(this === numbers); // true

    function calculate() {
      console.log(this === numbers); // FALSE! (function invocation)
      return this.numberA + this.numberB;
    }
    return calculate(); // plain function call -> `this` = window/undefined
  }
};
numbers.sum(); // NaN or TypeError in strict mode

// FIX 1: .call(this)
// return calculate.call(this);

// FIX 2: Arrow function (inherits `this` from sum)
// const calculate = () => {
//   console.log(this === numbers); // true
//   return this.numberA + this.numberB;
// };


// ============================================================
// 6. EXPLICIT BINDING - call / apply / bind     [INTERMEDIATE]
// ============================================================
// INTERVIEW: "Difference between call, apply, and bind?"
//
//  +--------+-----------------------+---------+---------------+
//  | METHOD | SYNTAX                | INVOKES | ARGS FORMAT   |
//  +--------+-----------------------+---------+---------------+
//  | call   | fn.call(ctx, a, b)    | YES     | comma-sep     |
//  | apply  | fn.apply(ctx, [a, b]) | YES     | array         |
//  | bind   | fn.bind(ctx, a)       | NO*     | comma-sep     |
//  +--------+-----------------------+---------+---------------+
//  * bind returns a NEW function with `this` permanently set.

function sumNums(number1, number2) {
  return number1 + number2;
}
sumNums.call(undefined, 10, 2);    // 12
sumNums.apply(undefined, [10, 2]); // 12

const rabbit = { name: 'White Rabbit' };
function concatName(string) {
  console.log(this === rabbit); // true
  return string + this.name;
}
concatName.call(rabbit, 'Hello ');   // 'Hello White Rabbit'
concatName.apply(rabbit, ['Bye ']);  // 'Bye White Rabbit'

// ES5 parent constructor pattern with call:
function Runner(name) {
  this.name = name;
}
function Rabbit(name, countLegs) {
  Runner.call(this, name);       // call parent constructor
  this.countLegs = countLegs;
}
const myRabbit = new Rabbit('White Rabbit', 4);
// { name: 'White Rabbit', countLegs: 4 }


// ============================================================
// 7. HARD BINDING with .bind()                  [INTERMEDIATE]
// ============================================================
// .bind() creates a permanent context link.

function multiplyBy(number) {
  'use strict';
  return this * number;
}
const double = multiplyBy.bind(2);
double(3);  // 6
double(10); // 20

// INTERVIEW: "Can you change a bound function's `this`?"
// NO -- except with `new`.
function getThis() {
  'use strict';
  return this;
}
const one = getThis.bind(1);
one();          // 1
one.call(2);    // 1 (ignored!)
one.apply(2);   // 1 (ignored!)
one.bind(2)();  // 1 (ignored!)
new one();      // Object {} (new wins over bind)


// ============================================================
// 8. new BINDING - Constructor Invocation       [INTERMEDIATE]
// ============================================================
// INTERVIEW: "What does `new` do?"
//
// The `new` operator:
// 1. Creates a new empty object {}
// 2. Sets __proto__ to Constructor.prototype
// 3. Binds `this` to the new object
// 4. Returns the new object (unless constructor returns an object)

function Foo() {
  this.property = 'Default Value';
}
const fooInstance = new Foo();
fooInstance.property; // 'Default Value'

// With class syntax:
class Bar {
  constructor() {
    this.property = 'Default Value';
  }
}
const barInstance = new Bar();
barInstance.property; // 'Default Value'

// Prototype methods:
function Country(name, traveled) {
  this.name = name || 'United Kingdom';
  this.traveled = Boolean(traveled);
}
Country.prototype.travel = function() {
  this.traveled = true;
};
const france = new Country('France', false);
france.travel();

// Class syntax:
class City {
  constructor(name) {
    this.name = name;
    this.traveled = false;
  }
  travel() { this.traveled = true; }
}
const paris = new City('Paris');
paris.travel();


// ============================================================
// 9. FORGETTING `new` (Constructor Safety)        [ADVANCED]
// ============================================================

function Vehicle(type, wheelsCount) {
  this.type = type;
  this.wheelsCount = wheelsCount;
  return this;
}

// Without `new` -> `this` = window -> pollutes global!
const car = Vehicle('Car', 4);
car === window; // true -- oops!

// SAFETY PATTERN: guard against missing `new`
function SafeVehicle(type, wheelsCount) {
  if (!(this instanceof SafeVehicle)) {
    throw Error('Error: Incorrect invocation');
  }
  this.type = type;
  this.wheelsCount = wheelsCount;
  return this;
}
// SafeVehicle('Car', 4); // throws Error
const safeCar = new SafeVehicle('Car', 4); // works correctly

// Modern: class syntax prevents this by default (always requires `new`)


// ============================================================
// 10. ARROW FUNCTION `this` (Lexical Binding)   [INTERMEDIATE]
// ============================================================
// INTERVIEW: "How does `this` work in arrow functions?"
//
// Arrow functions do NOT have their own `this`.
// They capture `this` from the enclosing lexical scope at DEFINITION time.
// This CANNOT be changed by call/apply/bind/new.

class Point {
  constructor(x, y) {
    this.x = x;
    this.y = y;
  }
  log() {
    console.log(this === myPoint); // true
    setTimeout(() => {
      console.log(this === myPoint);      // true (captured from log())
      console.log(this.x + ':' + this.y); // '95:165'
    }, 1000);
  }
}
const myPoint = new Point(95, 165);
myPoint.log();

// Arrow function at top level -> `this` = global/module
const getContext = () => {
  console.log(this === window); // true (in browser, top-level)
  return this;
};

// Arrow functions CANNOT be rebound:
// (function() {
//   const get = () => this;
//   get.call([0]);   // still the original `this`
//   get.apply([0]);  // still the original `this`
//   get.bind([0])(); // still the original `this`
// }).call(numbers);

// Arrow functions CANNOT be constructors:
// new getContext() // TypeError: getContext is not a constructor


// ============================================================
// 11. ARROW FUNCTION AS METHOD (PITFALL)          [ADVANCED]
// ============================================================
// INTERVIEW: "Should you use arrow functions as object methods?"
// NO. Arrow functions capture the ENCLOSING `this`, not the object.

Period.prototype.format = () => {
  console.log(this === window); // true (defined at top level)
  return this.hours + ' hours and ' + this.minutes + ' minutes';
};
function Period(hours, minutes) {
  this.hours = hours;
  this.minutes = minutes;
}
const walkPeriod = new Period(2, 30);
walkPeriod.format(); // "undefined hours and undefined minutes"

// Object literal with arrow method:
const object = {
  who: 'World',
  greet() { return `Hello, ${this.who}!`; },        // works
  farewell: () => { return `Goodbye, ${this.who}!`; } // broken
};
console.log(object.greet());    // "Hello, World!"
console.log(object.farewell()); // "Goodbye, undefined!"


// ============================================================
// 12. CLASS FIELDS vs METHODS `this` BINDING      [ADVANCED]
// ============================================================
// INTERVIEW: "What's the difference between class methods and class fields?"
//
//  +-------------------+-------------------+-------------------+
//  |                   | METHOD            | ARROW FIELD       |
//  +-------------------+-------------------+-------------------+
//  | Syntax            | foo() {}          | foo = () => {}    |
//  | On prototype?     | Yes               | No (on instance)  |
//  | `this` binding    | Depends on call   | Always the instance|
//  | Memory            | Shared            | Per instance copy |
//  | Safe for callback?| No (may lose this)| Yes               |
//  +-------------------+-------------------+-------------------+

class Example {
  value = 42;

  // Regular method - on prototype, `this` depends on call site
  regularMethod() {
    return this.value;
  }

  // Arrow field - on each instance, `this` always = instance
  arrowField = () => {
    return this.value;
  };
}

const ex = new Example();
const reg = ex.regularMethod;
const arrow = ex.arrowField;

// reg();    // undefined or TypeError (lost `this`)
arrow();     // 42 (always works)

// Trade-off: arrow fields use more memory (one copy per instance)
// Use arrow fields when passing as callbacks; methods for everything else.


// ============================================================
// 13. `this` IN EVENT HANDLERS                  [INTERMEDIATE]
// ============================================================
// INTERVIEW: "What is `this` in a DOM event handler?"

// Regular function: `this` = the element that fired the event
// button.addEventListener('click', function() {
//   console.log(this);          // <button> element
//   console.log(this === button); // true
// });

// Arrow function: `this` = enclosing scope (usually window/module)
// button.addEventListener('click', () => {
//   console.log(this);          // window (NOT the button!)
// });


// ============================================================
// 14. `this` IN setTimeout/setInterval          [INTERMEDIATE]
// ============================================================

// let a = true;
// setTimeout(() => { a = false; }, 1000);
// while (a) {
//   console.log("hi"); // INFINITE LOOP! JS is single-threaded.
//                       // setTimeout callback never fires because
//                       // the while loop never yields to the event loop.
// }


// ============================================================
// GOTCHAS & INTERVIEW TRAPS
// ============================================================

// GOTCHA 1: Method extraction loses `this`
// const fn = obj.method; fn(); // `this` = window/undefined

// GOTCHA 2: Arrow functions in objects use enclosing `this` (usually window)
// const o = { x: 1, getX: () => this.x }; o.getX(); // undefined

// GOTCHA 3: bind is permanent
// const bound = fn.bind(a); bound.call(b); // still uses `a`

// GOTCHA 4: forEach/map/filter callbacks
// [1,2,3].forEach(function() { console.log(this); }); // window/undefined
// [1,2,3].forEach(function() { console.log(this); }, obj); // obj (2nd arg)
// [1,2,3].forEach(() => { console.log(this); }); // enclosing `this`

// GOTCHA 5: Nested function inside method
// obj.method = function() { function inner() { /* this != obj */ } }

// GOTCHA 6: new overrides bind
// const BoundFoo = Foo.bind(obj); new BoundFoo(); // `this` = new object, not obj

// GOTCHA 7: class fields are NOT on prototype
// class C { field = () => {} }
// new C().field === new C().field // false (different function instances)
