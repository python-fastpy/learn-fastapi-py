// ============================================================
// JAVASCRIPT CLASSES -- ULTIMATE QUICK-REFERENCE
// ============================================================
//
//  +-----------------------------------------------------------+
//  |  DIFFICULTY MAP                                           |
//  |  [BASIC]        -- Syntax, constructors, fields           |
//  |  [INTERMEDIATE] -- Inheritance, static, accessors         |
//  |  [ADVANCED]     -- Private, mixins, symbols, patterns     |
//  +-----------------------------------------------------------+
//
//  4 Pillars of OOP
//  1. Encapsulation   -- bundle data + methods, hide internals
//  2. Abstraction     -- expose only what's necessary
//  3. Inheritance     -- derive new classes from existing ones
//  4. Polymorphism    -- same interface, different behavior
//
// ============================================================
// TABLE: class vs function constructor
// ============================================================
//
//  | Feature               | ES6 class         | function Ctor      |
//  |-----------------------|--------------------|--------------------|
//  | Hoisted?              | No (TDZ)          | Yes (declarations) |
//  | Strict mode?          | Always             | Only if opted-in   |
//  | [[Construct]] check?  | Must use `new`     | Can call without   |
//  | Methods enumerable?   | No                 | Yes (on prototype) |
//  | `super` keyword?      | Yes                | No (use .call())   |
//  | Private fields?       | #field             | Closure / WeakMap  |
//  | Static init blocks?   | Yes (ES2022)       | IIFE pattern       |
//  | Prototype under hood? | Yes                | Yes                |
//


// ============================================================
// 1. CLASS DEFINITION FORMS                          [BASIC]
// ============================================================

// 1a. Class declaration
class User {
  constructor(name) {
    this.name = name;
  }
}

// 1b. Unnamed class expression
const UserExpr = class {
  constructor(name) { this.name = name; }
};

// 1c. Named class expression (name scoped inside body only)
const UserNamed = class UserInternal {
  constructor(name) { this.name = name; }
  whoAmI() { return UserInternal.name; } // "UserInternal"
};
// UserInternal; // ReferenceError -- not visible outside

// 1d. Default export   --  export default class User { ... }
// 1e. Named export      --  export class User { ... }

const u = new User('Shubham');
console.log(u); // User { name: 'Shubham' }

// INTERVIEW: "Are classes hoisted?"
// No. Class declarations sit in the Temporal Dead Zone until
// the engine reaches the declaration -- just like `let`/`const`.


// ============================================================
// 2. CONSTRUCTOR                                     [BASIC]
// ============================================================
// - Special method called once per `new` invocation.
// - Omit it and JS creates an implicit empty constructor.
// - A class can have AT MOST one constructor (SyntaxError otherwise).

class Animal {
  constructor(species) {
    this.species = species;
  }
}
// INTERVIEW: What happens if you call a class without `new`?
// TypeError: Class constructor Animal cannot be invoked without 'new'


// ============================================================
// 3. FIELDS (PUBLIC & PRIVATE, INSTANCE & STATIC)    [BASIC]
// ============================================================

// ---- 3a. Public instance fields with initializers ----
class Config {
  retries = 3;               // field initializer -- runs per instance
  timeout = 5000;
  constructor(overrides = {}) {
    Object.assign(this, overrides);
  }
}
console.log(new Config({ retries: 5 })); // Config { retries: 5, timeout: 5000 }

// ---- 3b. Private instance fields (#) ----
class BankAccount {
  #balance = 0;                        // private field
  constructor(initial) { this.#balance = initial; }
  get balance() { return this.#balance; }
  deposit(amt) { if (amt > 0) this.#balance += amt; }
}
const acct = new BankAccount(100);
console.log(acct.balance);  // 100
// acct.#balance;            // SyntaxError -- truly private

// ---- 3c. Public static fields ----
class HttpStatus {
  static OK = 200;
  static NOT_FOUND = 404;
}
console.log(HttpStatus.OK); // 200

// ---- 3d. Private static fields (singleton pattern) ----
class Singleton {
  static #instance = null;
  constructor(data) {
    if (Singleton.#instance) return Singleton.#instance;
    this.data = data;
    Singleton.#instance = this;
  }
}
const s1 = new Singleton('first');
const s2 = new Singleton('second');
console.log(s1 === s2); // true -- same instance


// ============================================================
// 4. METHODS                                         [BASIC]
// ============================================================

// ---- 4a. Instance methods (on prototype) ----
class Person {
  constructor(name, age) {
    this.name = name;
    this.age = age;
  }
  details() { return `${this.name} is ${this.age} years old.`; }
}
console.log(new Person('Prashant', 23).details());

// ---- 4b. Static methods ----
// Callable on the class itself, NOT on instances.
class MathUtil {
  static clamp(val, min, max) { return Math.min(Math.max(val, min), max); }
}
console.log(MathUtil.clamp(15, 0, 10)); // 10
// new MathUtil().clamp(5,0,10);         // TypeError


// ============================================================
// 5. ACCESSOR PROPERTIES (get / set)                 [BASIC]
// ============================================================

class Temperature {
  #celsius;
  constructor(c) { this.#celsius = c; }
  get fahrenheit() { return this.#celsius * 9 / 5 + 32; }
  set fahrenheit(f) { this.#celsius = (f - 32) * 5 / 9; }
  get celsius() { return this.#celsius; }
}
const t = new Temperature(100);
console.log(t.fahrenheit); // 212
t.fahrenheit = 32;
console.log(t.celsius);    // 0


// ============================================================
// 6. COMPUTED METHOD NAMES                      [INTERMEDIATE]
// ============================================================

const action = 'greet';
class Greeter {
  [action]() { return 'Hello!'; }
  get [`${action}Loudly`]() { return 'HELLO!'; }
}
const g = new Greeter();
console.log(g.greet());      // "Hello!"
console.log(g.greetLoudly);  // "HELLO!"


// ============================================================
// 7. PRIVATE METHODS & ACCESSORS (#)            [INTERMEDIATE]
// ============================================================
// INTERVIEW: "How do private methods differ from private fields?"
// Both use # prefix. Private methods live on the prototype (shared),
// private fields are per-instance. Neither is accessible outside.

class Logger {
  #prefix;
  constructor(prefix) { this.#prefix = prefix; }

  // private method
  #formatMessage(msg) {
    return `[${this.#prefix}] ${new Date().toISOString()}: ${msg}`;
  }

  // private accessor
  get #tag() { return this.#prefix.toUpperCase(); }

  log(msg) {
    console.log(this.#formatMessage(msg));
  }
  getTag() { return this.#tag; }
}
const logger = new Logger('app');
logger.log('started');         // [app] 2026-...: started
// logger.#formatMessage('x'); // SyntaxError


// ============================================================
// 8. STATIC INITIALIZATION BLOCKS (ES2022)      [INTERMEDIATE]
// ============================================================
// Runs once when the class is evaluated. Useful for complex
// static setup that requires try/catch or multi-step init.

class DbConfig {
  static host;
  static port;
  static {
    try {
      // Imagine reading from env or file
      DbConfig.host = 'localhost'; // process.env.DB_HOST
      DbConfig.port = 5432;       // parseInt(process.env.DB_PORT)
    } catch {
      DbConfig.host = '127.0.0.1';
      DbConfig.port = 5432;
    }
  }
}
console.log(DbConfig.host, DbConfig.port); // localhost 5432


// ============================================================
// 9. INHERITANCE (extends / super)              [INTERMEDIATE]
// ============================================================
//
//  ASCII: Inheritance chain
//
//    Rectangle
//       ^
//       | extends
//     Square
//
//  Under the hood:
//    square --> Square.prototype --> Rectangle.prototype --> Object.prototype --> null
//

// ---- Pre-ES6 inheritance ----
function RectFn(w, h) { this.width = w; this.height = h; }
RectFn.prototype.getArea = function () { return this.width * this.height; };

function SquareFn(len) { RectFn.call(this, len, len); }
SquareFn.prototype = Object.create(RectFn.prototype);
SquareFn.prototype.constructor = SquareFn;

const sqFn = new SquareFn(3);
console.log(sqFn.getArea());              // 9
console.log(sqFn instanceof SquareFn);    // true
console.log(sqFn instanceof RectFn);      // true

// ---- ES6 class inheritance ----
class Rectangle {
  constructor(w, h) { this.width = w; this.height = h; }
  getArea() { return this.width * this.height; }
}

class Square extends Rectangle {
  constructor(len) { super(len, len); } // must call super before `this`
}
const sq = new Square(4);
console.log(sq.getArea());              // 16
console.log(sq instanceof Square);     // true
console.log(sq instanceof Rectangle);  // true

// INTERVIEW: "What does super() do?"
// Calls the parent constructor. MUST be called before accessing
// `this` in a derived constructor -- otherwise ReferenceError.


// ============================================================
// 10. EXTENDING BUILT-INS                       [INTERMEDIATE]
// ============================================================

class TypedArray extends Array {
  add(item) { this.push(item); return this; }
}
const arr = new TypedArray();
arr.add(1).add(2).add(3);
console.log(arr.length); // 3
console.log(arr instanceof Array); // true

// Extending from expression (any [[Construct]]-able)
function Base(val) { this.val = val; }
Base.prototype.show = function () { return this.val; };
class Derived extends Base {
  constructor(v) { super(v); }
}
console.log(new Derived(42).show()); // 42


// ============================================================
// 11. METHOD CHAINING PATTERN                   [INTERMEDIATE]
// ============================================================

class QueryBuilder {
  #parts = [];
  select(cols) { this.#parts.push(`SELECT ${cols}`); return this; }
  from(table) { this.#parts.push(`FROM ${table}`); return this; }
  where(cond) { this.#parts.push(`WHERE ${cond}`); return this; }
  build() { return this.#parts.join(' '); }
}
const query = new QueryBuilder()
  .select('*')
  .from('users')
  .where('active = true')
  .build();
console.log(query); // "SELECT * FROM users WHERE active = true"

// INTERVIEW: "How does method chaining work?"
// Each method returns `this`, allowing consecutive calls on the same object.


// ============================================================
// 12. instanceof AND Symbol.hasInstance            [ADVANCED]
// ============================================================
//
//  instanceof walks the prototype chain:
//    obj instanceof Ctor  ===  Ctor.prototype isPrototypeOf(obj)
//

class EvenNumber {
  static [Symbol.hasInstance](num) {
    return typeof num === 'number' && num % 2 === 0;
  }
}
console.log(4 instanceof EvenNumber);  // true
console.log(5 instanceof EvenNumber);  // false

// INTERVIEW: "Can you customize instanceof?"
// Yes -- define static [Symbol.hasInstance](instance) on the class.


// ============================================================
// 13. Symbol.species                              [ADVANCED]
// ============================================================
// Controls which constructor is used when built-in methods create
// derived instances (e.g., .map(), .filter() on subclassed Array).

class TrackedArray extends Array {
  static get [Symbol.species]() { return Array; } // map/filter return plain Array
}
const tracked = new TrackedArray(1, 2, 3);
const mapped = tracked.map(x => x * 2);
console.log(mapped instanceof TrackedArray); // false
console.log(mapped instanceof Array);       // true


// ============================================================
// 14. MIXINS PATTERN                              [ADVANCED]
// ============================================================
// JS has single inheritance. Mixins simulate multiple inheritance
// by dynamically extending a base class.
//
//  ASCII:
//    Base <-- Serializable(Base) <-- Validatable(Serializable(Base))
//

const Serializable = (Base) => class extends Base {
  serialize() { return JSON.stringify(this); }
  static deserialize(json) { return Object.assign(new this(), JSON.parse(json)); }
};

const Validatable = (Base) => class extends Base {
  validate() {
    for (const [key, val] of Object.entries(this)) {
      if (val == null) throw new Error(`${key} is required`);
    }
    return true;
  }
};

class UserModel extends Validatable(Serializable(Object)) {
  constructor(name, email) {
    super();
    this.name = name;
    this.email = email;
  }
}
const um = new UserModel('Alice', 'alice@test.com');
console.log(um.serialize());  // {"name":"Alice","email":"alice@test.com"}
console.log(um.validate());   // true

// INTERVIEW: "How do you achieve multiple inheritance in JS?"
// Use mixins -- functions that take a base class and return a
// subclass, then chain them: class X extends B(A(Object)) {}


// ============================================================
// 15. ABSTRACT CLASS PATTERN                      [ADVANCED]
// ============================================================
// JS has no native abstract classes. Simulate by throwing in
// the constructor and in methods that must be overridden.

class Shape {
  constructor() {
    if (new.target === Shape) {
      throw new Error('Shape is abstract -- cannot instantiate directly');
    }
  }
  area() { throw new Error('Subclass must implement area()'); }
  toString() { return `${this.constructor.name}: area=${this.area()}`; }
}

class Circle extends Shape {
  constructor(r) { super(); this.r = r; }
  area() { return Math.PI * this.r ** 2; }
}
console.log(new Circle(5).toString()); // "Circle: area=78.539..."
// new Shape(); // Error: Shape is abstract

// INTERVIEW: new.target is the constructor that was directly invoked
// with `new`. Inside a base constructor called via super(), new.target
// is the derived class.


// ============================================================
// 16. DECORATOR PROPOSAL (Stage 3)                [ADVANCED]
// ============================================================
// Not yet in the language spec (as of ES2024), but widely used
// via TypeScript and Babel. The TC39 proposal uses @ syntax:
//
//   @logged
//   class Api {
//     @throttle(300)
//     fetchData() { ... }
//   }
//
// Manual decorator pattern (works today):
function readonly(target, name, descriptor) {
  descriptor.writable = false;
  return descriptor;
}
// Usage with Object.defineProperty:
class Api {
  fetchData() { return 'data'; }
}
Object.defineProperty(Api.prototype, 'fetchData',
  readonly(Api.prototype, 'fetchData',
    Object.getOwnPropertyDescriptor(Api.prototype, 'fetchData')));
// Api.prototype.fetchData = () => {}; // TypeError in strict mode


// ============================================================
// GOTCHAS
// ============================================================
//
// 1. `this` in class methods is NOT auto-bound.
//      const fn = obj.method;  fn();  // `this` is undefined (strict)
//    Fix: arrow in constructor, bind in constructor, or class field arrow.
//
// 2. Class fields run BEFORE the constructor body when using
//    initializers: `x = this.compute()` works if compute() is
//    on the prototype, but `this.y` may not be set yet.
//
// 3. Private fields (#) cannot be detected with `in` on arbitrary
//    objects -- use try/catch or a branded check:
//      static hasInstance(obj) { try { obj.#field; return true; } catch { return false; } }
//    UPDATE (ES2022): `#field in obj` is valid syntax now.
//
// 4. `typeof MyClass` is "function" -- classes are functions.
//
// 5. Arrow functions in class fields create a NEW function per
//    instance (not shared via prototype). Good for callbacks,
//    bad for memory if thousands of instances.
//
// 6. `super` in static methods refers to the parent CLASS, not
//    the parent prototype.
//
// 7. You cannot use `arguments` object inside class methods
//    (strict mode); use rest params instead.
//

// ============================================================
// COMPARISON: CLASS FIELDS vs PROTOTYPE METHODS
// ============================================================
//
//  | Aspect             | Class field (arrow)     | Prototype method     |
//  |--------------------|-------------------------|----------------------|
//  | Where it lives     | Own property (instance) | Constructor.prototype|
//  | Shared?            | No (per instance copy)  | Yes (shared)         |
//  | `this` binding     | Lexical (auto-bound)    | Dynamic              |
//  | Memory             | Higher (N copies)       | Lower (1 copy)       |
//  | Overridable?       | Shadows prototype       | Yes (standard)       |
//  | Shows in for..in   | Yes (own enumerable)    | No (non-enumerable)  |
//

// ============================================================
// INTERVIEW CHEAT SHEET
// ============================================================
//
// Q: Are JS classes just syntactic sugar?
// A: Mostly yes -- they set up the same prototype chain as constructor
//    functions + .prototype. But classes add: TDZ, strict mode, non-
//    enumerable methods, [[Construct]] requirement, and private fields.
//
// Q: Can you call a class without `new`?
// A: No. TypeError. (Unlike function constructors.)
//
// Q: Difference between class fields and constructor assignments?
// A: Fields with initializers run per-instance BEFORE the constructor
//    body. They're declared explicitly, making the shape predictable.
//
// Q: How do static methods inherit?
// A: Child.__proto__ === Parent, so Child inherits static methods.
//    `static display()` on Parent is callable as Child.display().
//
// Q: Explain new.target.
// A: Inside a constructor, new.target is the constructor that `new`
//    was called on. In a base class called via super(), it's the
//    derived class. Useful for abstract class enforcement.
//
