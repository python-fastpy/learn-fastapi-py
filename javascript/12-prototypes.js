// ============================================================
// JAVASCRIPT PROTOTYPES -- ULTIMATE QUICK-REFERENCE
// ============================================================
//
//  +-----------------------------------------------------------+
//  |  DIFFICULTY MAP                                           |
//  |  [BASIC]        -- Prototype basics, own vs inherited     |
//  |  [INTERMEDIATE] -- Chains, constructors, Object.create    |
//  |  [ADVANCED]     -- Pollution, perf, proto-less objects    |
//  +-----------------------------------------------------------+
//
// ============================================================
// THE PROTOTYPE CHAIN -- ASCII DIAGRAM
// ============================================================
//
//   const dog = new Animal("Dog");
//
//   dog                          (instance)
//    |
//    |  [[Prototype]]  (__proto__)
//    v
//   Animal.prototype             { walks(), constructor: Animal }
//    |
//    |  [[Prototype]]
//    v
//   Object.prototype             { toString(), hasOwnProperty(), ... }
//    |
//    |  [[Prototype]]
//    v
//   null                         (end of chain)
//
// Property lookup walks UP this chain until found or null.
//
//
// ============================================================
// TABLE: __proto__ vs .prototype vs Object.getPrototypeOf()
// ============================================================
//
//  | Term                       | What it is                               | On what?          |
//  |----------------------------|------------------------------------------|-------------------|
//  | obj.__proto__              | Accessor to [[Prototype]] (deprecated)   | Any object        |
//  | Constructor.prototype      | Object assigned as [[Prototype]] of      | Functions only    |
//  |                            | instances created with `new Constructor`  |                   |
//  | Object.getPrototypeOf(obj) | Standard way to READ [[Prototype]]       | Any object        |
//  | Object.setPrototypeOf(o,p) | Standard way to WRITE [[Prototype]]      | Any object        |
//  | Object.create(proto)       | Create new object with proto as          | Factory call      |
//  |                            | its [[Prototype]]                        |                   |
//
//  INTERVIEW: "What is the difference between __proto__ and prototype?"
//  __proto__ is the actual link every object has to its prototype.
//  .prototype is a property on FUNCTIONS that becomes the __proto__
//  of objects created via `new`.
//


// ============================================================
// 1. PROTOTYPE OBJECT                                [BASIC]
// ============================================================
// Every object can have a prototype -- another object it inherits from.

const pet = { legs: 4 };
const cat = { sound: 'meow', __proto__: pet };
// __proto__ is deprecated; shown for clarity. Use Object.create() in real code.

console.log(cat.legs);  // 4  (inherited from pet)
console.log(cat.sound); // "meow" (own property)


// ============================================================
// 2. OWN vs INHERITED PROPERTIES                     [BASIC]
// ============================================================

// INTERVIEW: "How do you tell own from inherited properties?"
// - obj.hasOwnProperty('key')          (classic)
// - Object.hasOwn(obj, 'key')          (ES2022, preferred)
// - Object.getOwnPropertyNames(obj)    (list own props)
// - 'key' in obj                       (includes inherited -- dangerous)

const petA = { legs: 4 };
const chicken = { sound: 'Cluck!', legs: 2, __proto__: petA };
console.log(chicken.legs); // 2  (own property wins)

delete chicken.legs;
console.log(chicken.legs); // 4  (falls through to prototype)

const myObj = { myProp: 'Value' };
console.log(Object.getOwnPropertyNames(myObj)); // ['myProp']
console.log(Object.hasOwn(myObj, 'toString'));   // false (inherited)


// ============================================================
// 3. THE IMPLICIT PROTOTYPE                          [BASIC]
// ============================================================
// Every object literal gets Object.prototype as its [[Prototype]].

const plain = { x: 1 };
console.log(plain.toString()); // "[object Object]" -- from Object.prototype

const proto = Object.getPrototypeOf(plain);
console.log(plain.toString === proto.toString); // true


// ============================================================
// 4. PROTOTYPE CHAIN                            [INTERMEDIATE]
// ============================================================
//
//  ASCII:
//    cat --> pet --> tail --> Object.prototype --> null
//

const tail = { hasTail: true };
const petB = { legs: 4, __proto__: tail };
const catB = { sound: 'meow', __proto__: petB };

console.log(catB.hasTail); // true  (3 levels up)
console.log(catB.legs);    // 4     (2 levels up)
console.log(catB.sound);   // "meow" (own)

// INTERVIEW: "What happens at the end of the chain?"
// Object.getPrototypeOf(Object.prototype) === null
// If a property isn't found by then, the result is undefined.


// ============================================================
// 5. PROPERTY SHADOWING                         [INTERMEDIATE]
// ============================================================
// When you SET a property, it always creates/updates an OWN property.
// It does NOT modify the prototype, even if the same name exists there.

const base = { color: 'red' };
const child = Object.create(base);

console.log(child.color);                 // "red" (inherited)
child.color = 'blue';                     // creates OWN property
console.log(child.color);                 // "blue" (own, shadows)
console.log(Object.getPrototypeOf(child).color); // "red" (unchanged)

// Gotcha: setter on the prototype WILL be invoked.
// If the prototype has a setter for 'x', setting child.x calls it
// rather than creating an own property.


// ============================================================
// 6. THREE RULES OF PROTOTYPAL INHERITANCE      [INTERMEDIATE]
// ============================================================
// 1. No circular references   (a -> b -> a  throws TypeError)
// 2. __proto__ must be object or null
// 3. An object can only directly inherit from ONE prototype
//    (single inheritance; use mixins for multi-source)


// ============================================================
// 7. Object.setPrototypeOf / Object.getPrototypeOf  [INTERMEDIATE]
// ============================================================

const person = { alive: true };
const musician = { plays: true };

Object.setPrototypeOf(musician, person);

console.log(Object.getPrototypeOf(musician) === person); // true
console.log(musician.__proto__ === person);               // true (same thing)
console.log(musician.alive); // true


// ============================================================
// 8. EXTENDING THE CHAIN                        [INTERMEDIATE]
// ============================================================

const guitarist = { strings: 6, __proto__: musician };
console.log(guitarist.strings); // 6  (own)
console.log(guitarist.plays);   // true (from musician)
console.log(guitarist.alive);   // true (from person)

//  ASCII:
//    guitarist --> musician --> person --> Object.prototype --> null


// ============================================================
// 9. GETTERS / SETTERS ON PROTOTYPE             [INTERMEDIATE]
// ============================================================
// `this` in an inherited getter/setter refers to the CALLING object,
// not the prototype that defines it.

const car = {
  doors: 2,
  seats: 'vinyl',
  get seatMaterial() { return this.seats; },
  set seatMaterial(m) { this.seats = m; },
};

const luxuryCar = Object.create(car);
luxuryCar.seatMaterial = 'leather';
console.log(luxuryCar.seats);        // "leather" (own prop via setter)
console.log(luxuryCar.doors);        // 2 (inherited)
console.log(Object.keys(luxuryCar)); // ["seats"] -- only own props


// ============================================================
// 10. ENUMERATING PROPERTIES                    [INTERMEDIATE]
// ============================================================
//
//  | Method                      | Own? | Inherited? | Non-enum? |
//  |-----------------------------|------|------------|-----------|
//  | Object.keys()               | Yes  | No         | No        |
//  | Object.getOwnPropertyNames()| Yes  | No         | Yes       |
//  | for...in                    | Yes  | Yes        | No        |
//  | obj.hasOwnProperty(k)       | check| --         | --        |
//  | Object.hasOwn(obj, k)       | check| --         | --        |
//

// Object.keys -- own enumerable only
Object.keys(luxuryCar).forEach(key => console.log('own:', key));

// for..in -- includes inherited enumerable
for (let key in luxuryCar) {
  const source = Object.hasOwn(luxuryCar, key) ? 'own' : 'inherited';
  console.log(`${source}: ${key}`);
}


// ============================================================
// 11. CONSTRUCTOR FUNCTIONS                     [INTERMEDIATE]
// ============================================================
//
//  ASCII:  what `new Animal("Bear")` does
//
//    1. obj = {}                                 (create empty obj)
//    2. obj.[[Prototype]] = Animal.prototype      (link prototype)
//    3. Animal.call(obj, "Bear")                  (run constructor)
//    4. return obj  (unless ctor returns an object)
//

function AnimalCtor(species) {
  this.species = species;
  this.eats = true;
}
AnimalCtor.prototype.walks = function () {
  return `A ${this.species} is walking`;
};

const bear = new AnimalCtor('Bear');
console.log(bear.species);   // "Bear"
console.log(bear.walks());   // "A Bear is walking"

// Verifying the chain
console.log(bear.__proto__ === AnimalCtor.prototype);          // true
console.log(AnimalCtor.prototype.constructor === AnimalCtor);  // true

// INTERVIEW: bear does NOT have walks() as own property.
// It's on AnimalCtor.prototype and shared by all instances.


// ============================================================
// 12. THE `new` KEYWORD STEP-BY-STEP           [INTERMEDIATE]
// ============================================================
//
//  function Foo(x) { this.x = x; }
//  const f = new Foo(42);
//
//  Equivalent manual steps:
//
//    1. const obj = Object.create(Foo.prototype);
//    2. const result = Foo.call(obj, 42);
//    3. f = (typeof result === 'object' && result !== null) ? result : obj;
//
// INTERVIEW: If the constructor explicitly returns an object,
// that object replaces the newly created one. Returning a
// primitive is ignored.

function WeirdCtor() {
  this.a = 1;
  return { b: 2 }; // overrides the new object
}
const w = new WeirdCtor();
console.log(w.a); // undefined
console.log(w.b); // 2


// ============================================================
// 13. Function.prototype METHODS ON PROTOTYPE   [INTERMEDIATE]
// ============================================================
// call, apply, bind are on Function.prototype.
// All functions inherit them. Useful for borrowing methods.

const arrayLike = { 0: 'a', 1: 'b', length: 2 };
const realArray = Array.prototype.slice.call(arrayLike);
console.log(realArray); // ['a', 'b']

// Borrowing hasOwnProperty (safe from overrides)
const safe = Object.prototype.hasOwnProperty;
console.log(safe.call({ x: 1 }, 'x')); // true


// ============================================================
// 14. ES6 CLASSES (SYNTACTIC SUGAR)             [INTERMEDIATE]
// ============================================================
//
//  ASCII: class Vehicle -- what JS actually creates
//
//    Vehicle (function)
//     .prototype  --->  { ready(), constructor: Vehicle }
//                            ^
//                            | [[Prototype]]
//    Motorcycle (function)
//     .prototype  --->  { wheelie(), constructor: Motorcycle }
//
//    myBike.__proto__ --> Motorcycle.prototype
//    Motorcycle.prototype.__proto__ --> Vehicle.prototype
//    Vehicle.prototype.__proto__ --> Object.prototype
//

class Vehicle {
  constructor() {
    this.wheels = 4;
    this.motorized = true;
  }
  ready() { return 'Ready to go'; }
}

class Motorcycle extends Vehicle {
  constructor() {
    super();
    this.wheels = 2;
  }
  wheelie() { return 'On one wheel now'; }
}

const myBike = new Motorcycle();
console.log(myBike.wheels);    // 2
console.log(myBike.ready());   // "Ready to go"
console.log(myBike.wheelie()); // "On one wheel now"

// Proof it's prototypal under the hood:
console.log(myBike instanceof Motorcycle);                                // true
console.log(myBike instanceof Vehicle);                                   // true
console.log(Object.getPrototypeOf(Motorcycle.prototype) === Vehicle.prototype); // true


// ============================================================
// 15. Object.create()                               [ADVANCED]
// ============================================================
// Creates a new object with the specified prototype, without
// needing a constructor function.

const protoAnimal = {
  speak() { return `${this.name} makes a sound`; },
};
const dog = Object.create(protoAnimal);
dog.name = 'Rex';
console.log(dog.speak()); // "Rex makes a sound"
console.log(Object.getPrototypeOf(dog) === protoAnimal); // true


// ============================================================
// 16. PROTOTYPE-LESS OBJECTS: Object.create(null)   [ADVANCED]
// ============================================================
// Creates an object with NO prototype -- no toString, no hasOwnProperty,
// no inherited pollution risk. Perfect for dictionaries/maps.

const dict = Object.create(null);
dict['__proto__'] = 'safe';      // just a regular key, not a link
dict['constructor'] = 'also safe';
console.log(dict.__proto__);     // "safe" (not Object.prototype)
console.log(Object.getPrototypeOf(dict)); // null

// INTERVIEW: "Why use Object.create(null)?"
// 1. Safe dictionary -- no inherited keys to collide with
// 2. Prevents prototype pollution in user-input-driven lookups
// 3. Used internally by many frameworks (e.g., Vue's reactivity)


// ============================================================
// 17. PROTOTYPE POLLUTION & PREVENTION              [ADVANCED]
// ============================================================
// Prototype pollution: attacker modifies Object.prototype to inject
// properties into ALL objects. Common in unsafe deep-merge / JSON parse.
//
//  Example attack (DO NOT do this in production):
//    const malicious = JSON.parse('{"__proto__":{"isAdmin":true}}');
//    // naive merge copies isAdmin onto Object.prototype
//    // now ({}).isAdmin === true for EVERY object
//
//  Prevention:
//  1. Use Object.create(null) for lookup maps
//  2. Validate keys: skip "__proto__", "constructor", "prototype"
//  3. Use Map instead of plain objects for user-controlled keys
//  4. Freeze Object.prototype (extreme, may break libraries)
//  5. Use Object.hasOwn() checks before accessing properties

function safeMerge(target, source) {
  for (const key of Object.keys(source)) {
    if (key === '__proto__' || key === 'constructor' || key === 'prototype') {
      continue; // skip dangerous keys
    }
    target[key] = source[key];
  }
  return target;
}

// INTERVIEW: "What is prototype pollution?"
// It's a vulnerability where an attacker injects properties into
// Object.prototype via __proto__, affecting all objects globally.


// ============================================================
// 18. PERFORMANCE OF PROTOTYPE CHAINS               [ADVANCED]
// ============================================================
//
// - Property lookup traverses the chain: O(depth).
// - Long chains (>3-4 levels) can measurably slow hot paths.
// - Engines optimize with hidden classes / inline caches,
//   but deep chains break those optimizations.
// - Object.setPrototypeOf() after creation de-optimizes the
//   object in V8 (resets hidden class). Avoid in hot code.
//
// Best practices:
// - Keep chains shallow (2-3 levels typical)
// - Prefer composition over deep inheritance
// - Avoid modifying prototypes of existing objects at runtime
// - Use Object.create() at creation time, not setPrototypeOf later


// ============================================================
// 19. USEFUL PROTOTYPE INSPECTION METHODS           [ADVANCED]
// ============================================================

function Cat(name) { this.name = name; }
Cat.prototype.purr = function () { return 'purr'; };
const myCat = new Cat('Whiskers');

// isPrototypeOf -- check if object is in another's chain
console.log(Cat.prototype.isPrototypeOf(myCat)); // true

// propertyIsEnumerable
console.log(myCat.propertyIsEnumerable('name')); // true (own)
console.log(myCat.propertyIsEnumerable('purr')); // false (on prototype)

// Object.getOwnPropertyDescriptor
console.log(Object.getOwnPropertyDescriptor(myCat, 'name'));
// { value: 'Whiskers', writable: true, enumerable: true, configurable: true }

// Walking the full chain manually
function getPrototypeChain(obj) {
  const chain = [];
  let current = obj;
  while (current !== null) {
    chain.push(current);
    current = Object.getPrototypeOf(current);
  }
  return chain;
}
console.log(getPrototypeChain(myCat).length); // 3: myCat -> Cat.prototype -> Object.prototype
// (null is the 4th stop but not pushed)


// ============================================================
// GOTCHAS
// ============================================================
//
// 1. __proto__ vs [[Prototype]]:
//    __proto__ is a getter/setter on Object.prototype.
//    [[Prototype]] is the internal slot. They point to the same thing,
//    but __proto__ is deprecated. Use Object.getPrototypeOf().
//
// 2. Modifying Constructor.prototype AFTER creating instances:
//    Existing instances still link to the OLD prototype object.
//    If you REPLACE .prototype (not mutate), old instances are orphaned.
//      function Foo() {}
//      const a = new Foo();
//      Foo.prototype = { newMethod() {} };
//      const b = new Foo();
//      a.newMethod(); // TypeError -- a still has the old prototype
//      b.newMethod(); // works
//
// 3. for...in enumerates inherited properties.
//    Always guard with Object.hasOwn(obj, key) or hasOwnProperty.
//
// 4. Array.isArray(x) is more reliable than x instanceof Array
//    across realms (iframes). instanceof checks prototype identity,
//    and each realm has its own Array.prototype.
//
// 5. Object.keys() does NOT include Symbol-keyed properties.
//    Use Object.getOwnPropertySymbols() for those.
//
// 6. Frozen prototypes: Object.freeze(Object.prototype) prevents
//    pollution but may break libraries that monkey-patch built-ins.
//
// 7. typeof null === "object" -- this is a historic JS bug, not
//    a prototype feature. null is the chain terminator, not an object.
//

// ============================================================
// INTERVIEW CHEAT SHEET
// ============================================================
//
// Q: Explain prototypal inheritance.
// A: Every JS object has an internal [[Prototype]] link. When a
//    property is accessed, JS walks the chain: own -> prototype ->
//    prototype's prototype -> ... -> null. This is delegation,
//    not copying.
//
// Q: What does `new` do?
// A: 1. Creates empty object
//    2. Sets its [[Prototype]] to Constructor.prototype
//    3. Calls the constructor with `this` = new object
//    4. Returns the object (unless ctor returns an object)
//
// Q: Difference between Object.create() and new?
// A: Object.create(proto) sets proto as [[Prototype]] without
//    calling a constructor. `new Ctor()` calls the constructor
//    and uses Ctor.prototype.
//
// Q: How do classes relate to prototypes?
// A: Classes are syntactic sugar. `class Foo extends Bar` sets up
//    Foo.prototype.__proto__ === Bar.prototype and Foo.__proto__
//    === Bar (for static inheritance).
//
// Q: What is at the top of every prototype chain?
// A: Object.prototype, whose [[Prototype]] is null.
//    Exception: Object.create(null) makes objects with no prototype.
//
// Q: How do you check if a property is own?
// A: Object.hasOwn(obj, key) (ES2022) or
//    Object.prototype.hasOwnProperty.call(obj, key) (safe classic).
//
