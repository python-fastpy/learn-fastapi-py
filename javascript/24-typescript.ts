// ============================================================
// TYPESCRIPT ULTIMATE QUICK-REFERENCE
// Merged: main.ts + app.ts -- deduplicated, organized
// tsc 24-typescript --watch
// npm i -D typescript  |  npx tsc  |  npx tsc --init
// ============================================================

export {};

// ============================================================
// TABLE OF CONTENTS
// ============================================================
//
//  BASIC
//  -----
//   1.  Why TypeScript ................................ [BASIC]
//   2.  Primitive Types ............................... [BASIC]
//   3.  Type Annotations & Inference .................. [BASIC]
//   4.  Any vs Unknown vs Never (& Void) ............. [BASIC]
//   5.  Object Type vs object vs {} ................... [BASIC]
//   6.  Union & Intersection Types .................... [BASIC]
//   7.  Type Aliases & Literal Types .................. [BASIC]
//
//  ARRAYS / TUPLES / ENUMS
//  -----------------------
//   8.  Arrays & Tuples ............................... [BASIC]
//   9.  Enums ......................................... [BASIC]
//
//  FUNCTIONS
//  ---------
//  10.  Functions ..................................... [BASIC]
//  11.  Function Overloads ............................ [INTERMEDIATE]
//
//  INTERFACES
//  ----------
//  12.  Interfaces .................................... [BASIC]
//  13.  Interface vs Type Alias ....................... [INTERMEDIATE]
//  14.  Index Signatures .............................. [INTERMEDIATE]
//
//  CLASSES
//  -------
//  15.  Classes & Access Modifiers .................... [BASIC]
//  16.  Getters & Setters ............................. [INTERMEDIATE]
//  17.  Static Members ................................ [INTERMEDIATE]
//  18.  Inheritance & Abstract Classes ................ [INTERMEDIATE]
//
//  GENERICS
//  --------
//  19.  Generics ...................................... [INTERMEDIATE]
//  20.  Generics with Classes & Interfaces ............ [INTERMEDIATE]
//  21.  Advanced Generics ............................. [ADVANCED]
//
//  UTILITY TYPES
//  -------------
//  22.  Utility Types ................................. [INTERMEDIATE]
//
//  INTERMEDIATE TYPE FEATURES
//  --------------------------
//  23.  Type Guards ................................... [INTERMEDIATE]
//  24.  Discriminated Unions .......................... [INTERMEDIATE]
//  25.  Type Assertions vs Type Casting ............... [INTERMEDIATE]
//  26.  Keyof & Typeof Operators ...................... [INTERMEDIATE]
//  27.  Indexed Access Types .......................... [INTERMEDIATE]
//  28.  Const Assertions (as const) ................... [INTERMEDIATE]
//  29.  Satisfies Operator (TS 4.9+) .................. [INTERMEDIATE]
//
//  ADVANCED TYPES
//  --------------
//  30.  Conditional Types ............................. [ADVANCED]
//  31.  Mapped Types .................................. [ADVANCED]
//  32.  Template Literal Types ........................ [ADVANCED]
//  33.  Declaration Merging ........................... [ADVANCED]
//  34.  Module Augmentation ........................... [ADVANCED]
//  35.  Namespace vs Module ........................... [ADVANCED]
//
//  DECORATORS
//  ----------
//  36.  Decorators (Stage 3 / TS 5.0+) ............... [ADVANCED]
//
//  REFERENCE
//  ---------
//  37.  Quick Interview Reference
//
// ============================================================


// ============================================================
// 1. WHY TYPESCRIPT                                   [BASIC]
// ============================================================
// JS is dynamically typed -- flexible but error-prone.
// TS adds optional static types that catch bugs at compile time.

// Problem: JS lets this compile with no warning
function getProduct(id: number): { id: number; name: string; price: number } {
  return { id, name: `Awesome Gadget ${id}`, price: 99.5 };
}
const product = getProduct(1);

// TS catches: wrong property name, swapped args, missing fields
const showProduct = (name: string, price: number): void => {
  console.log(`The product ${name} costs ${price}`);
};
showProduct(product.name, product.price); // TS enforces order


// ============================================================
// 2. PRIMITIVE TYPES                                  [BASIC]
// ============================================================
// INTERVIEW: "Name all primitive types in TypeScript."

// +------------+----------------------------+-------------------+
// | Type       | Description                | Example           |
// +------------+----------------------------+-------------------+
// | string     | Text data                  | "hello"           |
// | number     | All numeric values         | 42, 3.14, 0xFF    |
// | boolean    | true / false               | true              |
// | null       | Intentional absence        | null              |
// | undefined  | Uninitialized value        | undefined         |
// | symbol     | Unique constant            | Symbol("id")      |
// | bigint     | Arbitrary precision int    | 9007199254740991n  |
// +------------+----------------------------+-------------------+

let isBeginner: boolean = true;
let total: number = 0;
let myName: string = "hello";

let sentence: string = `multiline
template literal`;

// null & undefined -- subtypes of all types (unless --strictNullChecks)
let n: null = null;
let u: undefined = undefined;

// typeof exploration
let box: unknown;
console.log(typeof box); // "undefined"
box = "Hello";
console.log(typeof box); // "string"
box = 100;
console.log(typeof box); // "number"

// GOTCHAS:
// - With strictNullChecks OFF, `let x: string = null` compiles.
//   With it ON (recommended), it errors.
// - `typeof null === "object"` is a JS legacy bug, not a TS one.
// - number is 64-bit float; for large ints use bigint.
// - symbol values are unique: Symbol("a") !== Symbol("a").


// ============================================================
// 3. TYPE ANNOTATIONS & INFERENCE                     [BASIC]
// ============================================================
// INTERVIEW: "When to annotate vs. let TS infer?"

// Annotation syntax: let varName: type = value;
let counter: number = 0;
let names: string[] = ["shubham", "vinayak"];

// Object annotation
let person: { name: string; age: number } = { name: "shubham", age: 25 };

// Function annotation
let greeting: (name: string) => string = (name) => `Hi ${name}`;
console.log(greeting("shubham"));

// +-----------------------+--------------------------------------+
// | Type Inference         | Type Annotation                     |
// +-----------------------+--------------------------------------+
// | TS guesses the type    | You explicitly tell TS the type     |
// | let x = 10 -> number  | let x: number = 10                  |
// +-----------------------+--------------------------------------+

// Inference examples
let a; // any (no initializer)
a = 10;
a = true;

let b = 20; // inferred as number
// b = true; // ERROR

// Best practice: let TS infer when possible. Annotate when:
// 1. Declaring without initializing
// 2. Function parameters (always annotate)
// 3. Complex return types for public APIs
// 4. Type can't be inferred (complex expressions)
// 5. Function returns `any` and you need to clarify


// ============================================================
// 4. ANY vs UNKNOWN vs NEVER (& VOID)                 [BASIC]
// ============================================================
// INTERVIEW: "Explain any vs unknown vs never."

// +----------+------------------+-------------------+------------------+
// | Type     | Assignable FROM  | Assignable TO     | Operations       |
// +----------+------------------+-------------------+------------------+
// | any      | Everything       | Everything        | All (no checks)  |
// | unknown  | Everything       | Only after narrow  | None until narrow|
// | never    | Nothing          | Everything (vacuous)| N/A (no value)  |
// +----------+------------------+-------------------+------------------+

//                +-----------+
//                |    any    |  <-- escape hatch, disables checking
//                +-----------+
//                      |
//       accepts anything, allows anything
//
//                +-----------+
//                |  unknown  |  <-- safe "any": must narrow before use
//                +-----------+
//                      |
//       accepts anything, allows NOTHING until narrowed
//
//                +-----------+
//                |   never   |  <-- bottom type: no value inhabits it
//                +-----------+
//       used for exhaustiveness, impossible branches

// any -- opts out of type checking entirely
let random: any = 10;
random = true;
random = "shubham";
random.nonExistentMethod(); // no error at compile time!

// unknown -- type-safe counterpart of any
let myUnknown: unknown = 10;
// myUnknown.toUpperCase(); // ERROR: Object is of type 'unknown'
(myUnknown as string).toUpperCase(); // assertion narrows it

if (typeof myUnknown === "string") {
  myUnknown.toUpperCase(); // OK -- narrowed via typeof
}

// void -- absence of return value
function log(message: string): void {
  console.log(message);
}

// never -- function that never returns
function throwError(msg: string): never {
  throw new Error(msg);
}
function infiniteLoop(): never {
  while (true) {}
}

// INTERVIEW: "How does never help with exhaustiveness checking?"
type Shape = "circle" | "square";
function area(s: Shape): number {
  switch (s) {
    case "circle": return Math.PI;
    case "square": return 1;
    default:
      const _exhaustive: never = s; // ERROR if a case is missing
      return _exhaustive;
  }
}

// Another exhaustiveness pattern
function fn(a: string | number): boolean {
  if (typeof a === "string") return true;
  if (typeof a === "number") return false;
  const _never: never = a; // compile error if union is not exhausted
  return _never;
}

// GOTCHAS:
// - `any` is contagious: `let x: any = 5; let y = x;` -- y is any.
// - Prefer `unknown` over `any` when receiving external data.
// - `unknown` requires narrowing; it's always the safer choice.
// - `never` is assignable TO every type (vacuous truth), but nothing
//   is assignable TO never (except never itself).
// - void != undefined: a void-returning callback CAN return a value
//   (TS ignores it). This enables `arr.forEach(callback)` to work
//   when callback returns something.
// - void variables can only be undefined (mostly useless).


// ============================================================
// 5. OBJECT TYPE vs object vs {}                      [BASIC]
// ============================================================
// INTERVIEW: "Difference between Object, object, and {}?"

// +----------+----------------------------------------------------+
// | Type     | Accepts                                            |
// +----------+----------------------------------------------------+
// | Object   | Any value with .toString()/.valueOf() (avoid)      |
// | object   | Any non-primitive (objects, arrays, functions)      |
// | {}       | Any non-null/undefined value (almost useless)       |
// +----------+----------------------------------------------------+

let employee: object = { firstName: "shubham", age: 25 };
// employee = "string"; // ERROR: string is not object

// Prefer specific shapes over `object`:
let employee2: { firstName: string; lastName: string; age: number; job: string } = {
  firstName: "shubham", lastName: "vinayak", age: 25, job: "engineer"
};

let vacant: {} = {};
console.log(vacant.toString()); // OK -- {} has Object prototype


// ============================================================
// 6. UNION & INTERSECTION TYPES                       [BASIC]
// ============================================================

let multitype: number | boolean;
multitype = 20;
multitype = true;

// Union narrowing
//
//   number | string
//        |
//    typeof === "number"?
//      /          \
//   YES            NO
//   number        string

function format(input: number | string): string {
  if (typeof input === "number") return input.toFixed(2);
  return input.trim();
}

// INTERVIEW: "Union vs Intersection?"
// +-------------------+------------------------------------------+
// | Union (A | B)     | Value is EITHER A or B                   |
// | Intersection (A&B)| Value is BOTH A and B simultaneously     |
// +-------------------+------------------------------------------+

// Intersection: combine types
type HasName = { name: string };
type HasAge = { age: number };
type PersonInfo = HasName & HasAge; // must have BOTH
let pi: PersonInfo = { name: "A", age: 1 };

type HasEmail = { email: string };
type Contact = HasName & HasEmail;
let contact: Contact = { name: "Alice", email: "alice@example.com" };

// Intersection of primitives = never
type Impossible = string & number; // never

// Practical: mixin pattern
interface ProductBase {
  id: number;
  name: string;
  price: number;
}
type Timestamped<T> = T & { createdAt: Date; updatedAt: Date };
type TimestampedProduct = Timestamped<ProductBase>;

// GOTCHAS:
// - Intersecting incompatible types produces `never`.
// - Intersection of two object types MERGES their properties.
//   Conflicts on same property create `never` for that property.


// ============================================================
// 7. TYPE ALIASES & LITERAL TYPES                     [BASIC]
// ============================================================

type Alphanumeric = string | number;
let input: Alphanumeric = "hello";
input = 123;

// String literal types
type MouseEvent1 = "click" | "dblclick" | "mouseup" | "mousedown";
let evt: MouseEvent1 = "click";
// evt = "mouseover"; // ERROR

// Numeric & boolean literals
type DiceRoll = 1 | 2 | 3 | 4 | 5 | 6;
type Toggle = true | false; // same as boolean, but self-documenting


// ============================================================
// 8. ARRAYS & TUPLES                                  [BASIC]
// ============================================================

let list1: number[] = [1, 2, 3];
let list2: Array<number> = [1, 2, 4]; // generic syntax

// Mixed-type array via union
let scores: (string | number)[] = ["shubh", 12, 23, "abc"];

// Tuples -- fixed-length, fixed-type arrays
let person1: [string, number] = ["shubham", 22];
// person1 = [22, "shubham"]; // ERROR: type mismatch

// Optional tuple element
let coords: [number, number, number?] = [1, 2];

// Labeled tuples (TS 4.0+)
type Range = [start: number, end: number];

// Readonly tuple
type Point = readonly [number, number];
// let p: Point = [1, 2]; p[0] = 3; // ERROR

// GOTCHAS:
// - Tuples allow .push() at runtime (TS won't stop you).
// - Labeled tuples improve readability: [name: string, age: number]
// - Destructuring: const [skill, level] = skills;


// ============================================================
// 9. ENUMS                                            [BASIC]
// ============================================================
// INTERVIEW: "What's the difference between enum, const enum, and union?"

enum Color { Red, Green, Blue }
let c: Color = Color.Green; // 1

enum Month {
  Jan, Feb, Mar, Apr, May, Jun,
  Jul, Aug, Sep, Oct, Nov, Dec
}
console.log(Month.Jan); // 0

// Custom starting value
enum Month1 { Jan = 1, Feb, Mar } // Feb=2, Mar=3

// String enum
enum Status { Active = "ACTIVE", Inactive = "INACTIVE" }

function isItSummer(month: Month): boolean {
  return month >= Month.Jun && month <= Month.Aug;
}

// +--------------+--------------------------------------------+
// | Kind         | JS Output      | Reverse Map | Tree-Shake |
// +--------------+----------------+-------------+------------+
// | enum         | Object + IIFE  | Yes (num)   | No         |
// | const enum   | Inlined values | No          | Yes        |
// | Union type   | None (erased)  | N/A         | Yes        |
// +--------------+----------------+-------------+------------+

const enum Direction { Up, Down, Left, Right }
let d = Direction.Up; // compiled to: let d = 0;

type DirectionUnion = "Up" | "Down" | "Left" | "Right"; // preferred

// GOTCHAS:
// - Numeric enums have reverse mapping: Color[1] === "Green"
// - String enums do NOT have reverse mapping.
// - const enum cannot be used with --isolatedModules (Babel, esbuild).
// - Prefer union types for most use cases; use enums only when
//   you need runtime object (iteration, key lookup).


// ============================================================
// 10. FUNCTIONS                                       [BASIC]
// ============================================================

// Typed parameters and return
function addType(num1: number, num2: number): number {
  return num1 + num2;
}

// Void return
function echo(message: string): void {
  console.log(message.toUpperCase());
}

// Optional parameter (must come after required)
function greet(first: string, last?: string): string {
  return last ? `${first} ${last}` : first;
}

// Default parameter
function greetDefault(name: string, greeting: string = "Hello"): string {
  return `${greeting}, ${name}`;
}

// Optional with explicit check
function multiply(a: number, b: number, c?: number): number {
  return c !== undefined ? a * b * c : a * b;
}

// Rest parameter
function getTotal(...nums: number[]): number {
  return nums.reduce((sum, n) => sum + n, 0);
}
console.log(getTotal(10, 20, 30)); // 60

// void return
function logMsg(msg: string): void {
  console.log(msg);
}

// Function type expression
let adder: (a: number, b: number) => number = (x, y) => x + y;

// GOTCHAS:
// - Optional params are `T | undefined`, not nullable.
// - Default params don't need a type annotation (inferred from default).
// - void != undefined: a void-returning callback CAN return a value
//   (TS ignores it). This enables `arr.forEach(callback)` to work
//   when callback returns something.
// - The overload implementation signature is NOT callable directly.
// - Arrow functions don't have their own `this`.


// ============================================================
// 11. FUNCTION OVERLOADS                       [INTERMEDIATE]
// ============================================================
// INTERVIEW: "Explain function overloading in TS."

function add(a: number, b: number): number;
function add(a: string, b: string): string;
function add(a: any, b: any): any {
  return a + b;
}
let numResult = add(1, 2);     // number
let strResult = add("a", "b"); // string

// Overload with optional param
function sum(a: number, b: number): number;
function sum(a: number, b: number, c: number): number;
function sum(a: number, b: number, c?: number): number {
  return c ? a + b + c : a + b;
}


// ============================================================
// 12. INTERFACES                                      [BASIC]
// ============================================================

interface Person {
  firstName: string;
  lastName: string;
  age?: number; // optional
  readonly id?: number; // readonly
}

function fullName(person: Person): string {
  return `${person.firstName} ${person.lastName}`;
}

// Richer interface example
interface Product {
  id: number;
  name: string;
  price: number;
  description?: string;       // optional
  readonly sku: string;       // immutable after creation
}

// Extending interfaces
interface DigitalProduct extends Product {
  downloadUrl: string;
  fileSize: number;
}

// Interface for functions
interface MathFunc {
  (a: number, b: number): number;
}
const subtract: MathFunc = (a, b) => a - b;

// Interface for classes
interface Printable {
  print(): void;
}
class Invoice implements Printable {
  print(): void { console.log("Printing invoice..."); }
}


// ============================================================
// 13. INTERFACE vs TYPE ALIAS                  [INTERMEDIATE]
// ============================================================
// INTERVIEW: "When to use interface vs type?"

// +-------------------------+------------------+------------------+
// | Feature                 | interface        | type             |
// +-------------------------+------------------+------------------+
// | Extend                  | extends keyword  | & intersection   |
// | Implements (class)      | Yes              | Yes              |
// | Declaration merging     | Yes              | No               |
// | Computed properties     | No               | Yes              |
// | Union / intersection    | No               | Yes              |
// | Mapped types            | No               | Yes              |
// | Primitive alias         | No               | Yes              |
// +-------------------------+------------------+------------------+

// Declaration merging (interfaces only):
interface Window {
  myCustomProp: string;
}
// Both declarations merge into one interface.

// Guideline: Use interface for object shapes (especially public APIs).
// Use type for unions, intersections, mapped types, primitives.


// ============================================================
// 14. INDEX SIGNATURES                         [INTERMEDIATE]
// ============================================================
// INTERVIEW: "What are index signatures?"

//   Index Signature:
//   { [key: string]: ValueType }
//         |
//   Allows any string key, all values must be ValueType

interface StringMap {
  [key: string]: string;
}
let dict: StringMap = {};
dict["hello"] = "world";
// dict["hello"] = 42; // ERROR: not string

// Mixing known and index signature
interface CSSStyles {
  display: string;
  position: string;
  [prop: string]: string; // catch-all for unknown CSS props
}

// number index signature (for array-like objects)
interface StringArray {
  [index: number]: string;
}
let myArr: StringArray = ["a", "b", "c"];

// GOTCHAS:
// - If you have both string and number index signatures,
//   the number index value must be a subtype of string index value.
// - Index signatures force ALL known properties to match the index type.
// - Use `Record<string, T>` or `Map<K,V>` as alternatives.


// ============================================================
// 15. CLASSES & ACCESS MODIFIERS                      [BASIC]
// ============================================================
// INTERVIEW: "Explain public, private, protected, readonly."

// +------------+-------------------+-------------------+------------------+
// | Modifier   | Same class        | Subclass          | Outside          |
// +------------+-------------------+-------------------+------------------+
// | public     | Yes               | Yes               | Yes              |
// | protected  | Yes               | Yes               | No               |
// | private    | Yes               | No                | No               |
// | # (ES pvt) | Yes               | No                | No (truly pvt)   |
// | readonly   | Set once (constructor or declaration)                    |
// +------------+-------------------+-------------------+------------------+

// ES5 constructor function (pre-class JS)
function PersonES5(this: any, ssn: string, firstName: string, lastName: string) {
  this.ssn = ssn;
  this.firstName = firstName;
  this.lastName = lastName;
}
PersonES5.prototype.getFullName = function() {
  return `${this.firstName} ${this.lastName}`;
};

// TypeScript class with parameter properties (shorthand for declare + assign)
class Employee {
  constructor(
    public employeeName: string,
    private _salary: number = 0,
    protected department: string = "General"
  ) {}

  greet(): string {
    return `Good morning, ${this.employeeName}`;
  }
}

let e1 = new Employee("shubham", 50000);
console.log(e1.employeeName);
console.log(e1.greet());
// e1._salary; // ERROR: private

// Private class with accessor pattern
class Person4 {
  constructor(
    private ssn: string,
    private firstName: string,
    private lastName: string
  ) {}
  getFullName(): string { return `${this.firstName} ${this.lastName}`; }
}
// new Person4("1","a","b").ssn; // ERROR: private

// Protected -- accessible in subclass
class Person5 {
  constructor(protected ssn: string, private firstName: string, private lastName: string) {}
  getFullName(): string { return `${this.firstName} ${this.lastName}`; }
}

// Readonly property
class Config {
  readonly apiUrl: string;
  constructor(url: string) {
    this.apiUrl = url; // only assignable in constructor
  }
}

// Readonly shorthand in constructor param
class Person7 {
  constructor(readonly birthDate: Date) {}
}

// GOTCHAS:
// - TS `private` is compile-time only; at runtime, the property exists.
// - Use `#field` (ES private fields) for true runtime privacy.
// - `readonly` prevents reassignment, NOT mutation of objects/arrays.


// ============================================================
// 16. GETTERS & SETTERS                        [INTERMEDIATE]
// ============================================================
// INTERVIEW: "How do getters/setters work in TS?"

class Person8 {
  private _age: number = 0;
  private _firstName: string = "";
  private _lastName: string = "";

  get age(): number { return this._age; }
  set age(val: number) {
    if (val <= 0 || val >= 200) throw new Error("Invalid age");
    this._age = val;
  }

  get firstName(): string { return this._firstName; }
  set firstName(val: string) {
    if (!val) throw new Error("Invalid first name");
    this._firstName = val;
  }

  get fullName(): string { return `${this._firstName} ${this._lastName}`; }
}

let person8 = new Person8();
person8.age = 20;
person8.firstName = "shubham";
console.log(person8.age, person8.fullName);

// GOTCHAS:
// - A getter without setter is implicitly readonly.
// - Getter/setter must have same visibility modifier (TS 4.3+
//   allows different visibility for get vs set).


// ============================================================
// 17. STATIC MEMBERS                           [INTERMEDIATE]
// ============================================================

class Employee2 {
  private static headcount: number = 0;

  constructor(private firstName: string, private lastName: string, private jobTitle: string) {
    Employee2.headcount++;
  }

  static getHeadcount(): number { return Employee2.headcount; }
}
new Employee2("John", "Doe", "FE");
new Employee2("Jane", "Doe", "BE");
console.log(Employee2.getHeadcount()); // 2

// GOTCHAS:
// - Static members belong to the class, not instances.
// - `this` inside a static method refers to the class itself.


// ============================================================
// 18. INHERITANCE & ABSTRACT CLASSES           [INTERMEDIATE]
// ============================================================

// Basic inheritance
class Manager extends Employee {
  constructor(name: string) {
    super(name);
  }
  delegateWork(): void {
    console.log("Manager delegating tasks");
  }
}

let m1 = new Manager("shubham manager");
m1.greet();
m1.delegateWork();

// Inheritance with method overriding
class Person9 {
  constructor(private firstName: string, private lastName: string) {}
  getFullName(): string { return `${this.firstName} ${this.lastName}`; }
  describe(): string { return `This is ${this.firstName} ${this.lastName}`; }
}

class EmployeeExt extends Person9 {
  constructor(firstName: string, lastName: string, private jobTitle: string) {
    super(firstName, lastName);
  }
  // Method override
  describe(): string {
    return `${super.describe()}. I'm a ${this.jobTitle}.`;
  }
}
let emp3 = new EmployeeExt("John", "Doe", "Front-end Developer");
console.log(emp3.getFullName());
console.log(emp3.describe());

// INTERVIEW: "Abstract class vs interface?"
// +-----------------------+-------------------+-------------------+
// | Feature               | Abstract Class    | Interface         |
// +-----------------------+-------------------+-------------------+
// | Concrete methods      | Yes               | No (TS 5.0+: No) |
// | Constructor           | Yes               | No                |
// | Runtime existence      | Yes (JS class)    | No (erased)       |
// | Multiple inheritance  | No (single ext.)  | Yes (multi impl.) |
// | State (properties)    | Yes               | Declaration only  |
// +-----------------------+-------------------+-------------------+

// Abstract class -- cannot be instantiated directly
abstract class Employee9 {
  constructor(private firstName: string, private lastName: string) {}
  abstract getSalary(): number;
  get fullName(): string { return `${this.firstName} ${this.lastName}`; }
  compensationStatement(): string {
    return `${this.fullName} makes ${this.getSalary()} a month.`;
  }
}

class FullTimeEmployee extends Employee9 {
  constructor(first: string, last: string, private salary: number) { super(first, last); }
  getSalary(): number { return this.salary; }
}

class Contractor extends Employee9 {
  constructor(first: string, last: string, private rate: number, private hours: number) {
    super(first, last);
  }
  getSalary(): number { return this.rate * this.hours; }
}

console.log(new FullTimeEmployee("John", "Doe", 12000).compensationStatement());
console.log(new Contractor("Jane", "Doe", 100, 160).compensationStatement());

// GOTCHAS:
// - Abstract classes CAN have concrete methods.
// - You can't do `new Employee9()` but you CAN use it as a type.


// ============================================================
// 19. GENERICS                                 [INTERMEDIATE]
// ============================================================
// INTERVIEW: "What are generics? Why use them?"

//   Without generics:           With generics:
//   identity(x: any): any       identity<T>(x: T): T
//        |                           |
//   loses type info              preserves type info

// Basic generic function
function identity<T>(value: T): T {
  return value;
}
let str = identity("hello"); // string
let num = identity(42);       // number

// Generic with constraint
function getLength<T extends { length: number }>(item: T): number {
  return item.length;
}
getLength("abc");      // OK
getLength([1, 2, 3]);  // OK
// getLength(123);     // ERROR: number has no .length

// Default type parameter
function createPair<A, B = A>(a: A, b: B): [A, B] {
  return [a, b];
}
let pair1 = createPair<string>("a", "b");     // [string, string]
let pair2 = createPair<string, number>("a", 1); // [string, number]

// Generic interface
interface ApiResponse<T> {
  data: T;
  status: number;
  error?: string;
}
let userResp: ApiResponse<{ name: string }> = {
  data: { name: "Alice" },
  status: 200
};

// Multiple type parameters
function merge<T, U>(obj1: T, obj2: U): T & U {
  return { ...obj1, ...obj2 };
}

// Generic constraint with keyof
function pluck<T, K extends keyof T>(items: T[], key: K): T[K][] {
  return items.map(item => item[key]);
}

// GOTCHAS:
// - `<T>` in .tsx files conflicts with JSX. Use `<T,>` or `<T extends unknown>`.
// - Constraints (`extends`) limit what T can be, enabling property access.
// - Default type params must come after non-default ones.


// ============================================================
// 20. GENERICS WITH CLASSES & INTERFACES       [INTERMEDIATE]
// ============================================================
// INTERVIEW: "How do generics work with classes?"

// Generic interface
interface Repository<T> {
  getById(id: number): T;
  getAll(): T[];
  save(item: T): void;
}

// Generic class
class InMemoryRepo<T extends { id: number }> implements Repository<T> {
  private items: T[] = [];

  getById(id: number): T {
    const item = this.items.find(i => i.id === id);
    if (!item) throw new Error(`Item ${id} not found`);
    return item;
  }
  getAll(): T[] { return [...this.items]; }
  save(item: T): void { this.items.push(item); }
}

interface Todo { id: number; title: string; done: boolean }
const todoRepo = new InMemoryRepo<Todo>();
todoRepo.save({ id: 1, title: "Learn TS", done: false });

// GOTCHAS:
// - Generic constraints are checked at call site, not definition.
// - Class static members CANNOT reference class type params.


// ============================================================
// 21. ADVANCED GENERICS                         [ADVANCED]
// ============================================================

// Multiple constraints
function copyFields<T extends object, U extends object>(target: T, source: U): T & U {
  return { ...target, ...source };
}

// Generic utility: make specified keys optional
interface UserProfile {
  id: number;
  name: string;
  email: string;
}
type PartialBy<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;
type UserOptionalEmail = PartialBy<UserProfile, "email">;

// Generic conditional
type IsArray<T> = T extends any[] ? true : false;


// ============================================================
// 22. UTILITY TYPES                            [INTERMEDIATE]
// ============================================================
// INTERVIEW: "Name and explain the most common utility types."

interface User {
  id: number;
  name: string;
  email: string;
  age: number;
}

// Partial<T> -- all properties optional
type PartialUser = Partial<User>;
let patch: PartialUser = { name: "new name" };

// Required<T> -- all properties required
interface OptionalConfig { host?: string; port?: number }
type StrictConfig = Required<OptionalConfig>;

// Pick<T, K> -- select subset of properties
type UserPreview = Pick<User, "id" | "name">;

// Omit<T, K> -- exclude properties
type UserWithoutEmail = Omit<User, "email">;

// Record<K, V> -- construct object type with keys K and values V
type Roles = "admin" | "editor" | "viewer";
type RolePermissions = Record<Roles, boolean>;

// Exclude<T, U> -- remove members from union
type NumberOrString = string | number | boolean;
type NoBoolean = Exclude<NumberOrString, boolean>; // string | number

// Extract<T, U> -- keep only members assignable to U
type OnlyString = Extract<NumberOrString, string>; // string

// NonNullable<T> -- remove null and undefined
type MaybeStr = string | null | undefined;
type DefiniteStr = NonNullable<MaybeStr>; // string

// ReturnType<T> -- extract return type of function
function createUser() { return { id: 1, name: "A" }; }
type NewUser = ReturnType<typeof createUser>; // { id: number; name: string }

// Parameters<T> -- extract parameter types as tuple
type CreateUserParams = Parameters<typeof createUser>; // []

function updateUser(id: number, data: Partial<User>): void {}
type UpdateParams = Parameters<typeof updateUser>; // [number, Partial<User>]

// Readonly<T> -- all properties readonly
type FrozenUser = Readonly<User>;

//   Utility Types Cheat Sheet:
//
//   Partial<T>                All props optional (shallow)
//   Required<T>               All props required
//   Readonly<T>               All props readonly
//   Pick<T, K>                Subset of props
//   Omit<T, K>                All props except K
//   Record<K, V>              Object with keys K and values V
//   Exclude<U, E>             Remove members from union
//   Extract<U, E>             Keep members in union
//   NonNullable<T>            Remove null | undefined
//   ReturnType<F>             Return type of function
//   Parameters<F>             Param types as tuple
//   ConstructorParameters<C>  Constructor param types
//   InstanceType<C>           Instance type of class
//   Awaited<T>                Unwrap Promise<T>

// GOTCHAS:
// - Partial makes ALL levels optional (shallow only). For deep,
//   you need a custom DeepPartial recursive type.
// - Record<string, T> allows any string key, unlike a stricter union.


// ============================================================
// 23. TYPE GUARDS                              [INTERMEDIATE]
// ============================================================
// INTERVIEW: "What are type guards and how do you create them?"

//   Type Guard Flow:
//
//   value: unknown
//       |
//       +-- typeof value === "string"  -->  string
//       +-- value instanceof Date      -->  Date
//       +-- "prop" in value            -->  { prop: ... }
//       +-- isCustomType(value)        -->  CustomType  (user-defined)
//       +-- value.kind === "circle"    -->  CircleType  (discriminated)

// typeof guard
function double(x: number | string): number | string {
  if (typeof x === "number") return x * 2;
  return x.repeat(2);
}

// instanceof guard
function formatDate(input: Date | string): string {
  if (input instanceof Date) return input.toISOString();
  return new Date(input).toISOString();
}

// in guard
interface Fish { swim(): void }
interface Bird { fly(): void }
function move(animal: Fish | Bird): void {
  if ("swim" in animal) animal.swim();
  else animal.fly();
}

// Custom type predicate (user-defined type guard)
// INTERVIEW: "What is `obj is Type` syntax?"
function hasName(obj: unknown): obj is { name: string } {
  return typeof obj === "object" && obj !== null && "name" in obj;
}

let mystery: unknown = { name: "TypeScript" };
if (hasName(mystery)) {
  console.log(mystery.name); // narrowed!
}

// Another custom predicate
interface Cat { meow(): void }
interface Dog { bark(): void }

function isCat(animal: Cat | Dog): animal is Cat {
  return "meow" in animal;
}

function makeSound(animal: Cat | Dog): void {
  if (isCat(animal)) animal.meow();
  else animal.bark();
}

// Assertion function (TS 3.7+)
function assertString(val: unknown): asserts val is string {
  if (typeof val !== "string") throw new Error("Not a string!");
}

// GOTCHAS:
// - typeof null === "object" -- always check for null first.
// - Type predicates are NOT validated by TS; if your logic is wrong,
//   the narrowing will be wrong. You're telling TS to trust you.


// ============================================================
// 24. DISCRIMINATED UNIONS                     [INTERMEDIATE]
// ============================================================
// INTERVIEW: "Explain discriminated unions and their benefits."

//   Discriminated Union Pattern:
//
//   { kind: "circle", radius }  --|
//   { kind: "square", side }    --|-->  Shape3
//   { kind: "rect", w, h }     --|
//                                     |
//                               switch(s.kind)
//                              /       |       \
//                         "circle"  "square"  "rect"
//                          radius     side      w, h

interface Circle2 { kind: "circle"; radius: number }
interface Square2 { kind: "square"; side: number }
interface Rect2   { kind: "rect"; width: number; height: number }
type Shape3 = Circle2 | Square2 | Rect2;

function getArea(s: Shape3): number {
  switch (s.kind) {
    case "circle": return Math.PI * s.radius ** 2;
    case "square": return s.side ** 2;
    case "rect":   return s.width * s.height;
  }
}

// Result type pattern (Success/Failure)
//   { type: "success", data }   --|
//   { type: "error", message }  --|-->  ResultType<T>

type Success<T> = { type: "success"; data: T };
type Failure = { type: "error"; message: string };
type ResultType<T> = Success<T> | Failure;

function handleResult(r: ResultType<string>): string {
  switch (r.type) {
    case "success": return r.data;
    case "error": return `Error: ${r.message}`;
  }
}

// GOTCHAS:
// - The discriminant must be a literal type (string, number, boolean).
// - Add `default: never` for exhaustiveness checking.


// ============================================================
// 25. TYPE ASSERTIONS vs TYPE CASTING          [INTERMEDIATE]
// ============================================================
// INTERVIEW: "Difference between type assertion and casting?"

// Type assertion -- tells TS "trust me, I know the type"
let someValue: unknown = "hello world";
let strLength1: number = (someValue as string).length;    // "as" syntax
let strLength2: number = (<string>someValue).length;       // angle bracket

// Double assertion (escape hatch -- use sparingly)
let numFromUnknown = (someValue as unknown as number);

// INTERVIEW: Key distinction:
// - Assertion: compile-time only, no runtime conversion.
// - Casting (other languages): runtime conversion.
// - TS has NO runtime casting. "as" is a compile-time hint only.

//   Type Assertion Flow:
//
//   unknown value
//       |
//       v
//   (value as string)     <-- compile-time ONLY
//       |
//       v
//   TS treats as string   <-- no runtime check!
//       |
//   If wrong type at runtime --> crash

// GOTCHAS:
// - Assertions don't change the runtime value AT ALL.
// - TS only allows assertion between overlapping types. For
//   non-overlapping: use double assertion `as unknown as T`.
// - Prefer type guards (typeof, instanceof) over assertions.


// ============================================================
// 26. KEYOF & TYPEOF OPERATORS                 [INTERMEDIATE]
// ============================================================
// INTERVIEW: "What do keyof and typeof do at the type level?"

// keyof -- union of an object type's keys
type UserKeys = keyof UserProfile; // "id" | "name" | "email"

function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key];
}

const user: UserProfile = { id: 1, name: "Alice", email: "a@b.com" };
const userName = getProperty(user, "name"); // string

// typeof -- extract type from a runtime value
const config = { host: "localhost", port: 8080 };
type ConfigType = typeof config; // { host: string; port: number }

// Combining keyof + typeof
type ConfigKeys = keyof typeof config; // "host" | "port"

// GOTCHAS:
// - `keyof` operates on TYPES, not values. Use `keyof typeof val`.
// - `typeof` in type position is different from JS runtime `typeof`.


// ============================================================
// 27. INDEXED ACCESS TYPES                     [INTERMEDIATE]
// ============================================================
// INTERVIEW: "How do you access a property's type from another type?"

//   T["key"]  -->  type of that property
//   T[K]      -->  generic indexed access

type UserName = UserProfile["name"];      // string
type UserIdOrEmail = UserProfile["id" | "email"]; // number | string

// With arrays
const roles = ["admin", "editor", "viewer"] as const;
type Role = typeof roles[number]; // "admin" | "editor" | "viewer"

// Nested access
interface ApiResponseNested {
  data: { users: UserProfile[]; total: number };
  status: number;
}
type Users = ApiResponseNested["data"]["users"];       // UserProfile[]
type SingleUser = ApiResponseNested["data"]["users"][number]; // UserProfile

// GOTCHAS:
// - Use string literal types as keys, not values.
// - `T[number]` extracts the element type from array/tuple types.


// ============================================================
// 28. CONST ASSERTIONS (as const)              [INTERMEDIATE]
// ============================================================
// INTERVIEW: "What does `as const` do?"

//   Without as const:              With as const:
//   const x = { a: 1 }             const x = { a: 1 } as const
//   // { a: number }               // { readonly a: 1 }
//   x.a = 2; // OK                 x.a = 2; // ERROR

const directions = ["up", "down", "left", "right"] as const;
// type: readonly ["up", "down", "left", "right"]
type DirectionStr = typeof directions[number]; // "up" | "down" | "left" | "right"

const configObj = {
  endpoint: "/api",
  retries: 3,
  verbose: false
} as const;
// All properties are readonly and literal-typed

// Enum-like pattern without enums
const COLOR = {
  Red: "#FF0000",
  Green: "#00FF00",
  Blue: "#0000FF"
} as const;
type ColorValue = typeof COLOR[keyof typeof COLOR]; // "#FF0000" | "#00FF00" | "#0000FF"

// GOTCHAS:
// - `as const` makes the ENTIRE structure deeply readonly.
// - Cannot push to `as const` arrays.
// - Useful for creating narrow types from runtime values.


// ============================================================
// 29. SATISFIES OPERATOR (TS 4.9+)             [INTERMEDIATE]
// ============================================================
// INTERVIEW: "What problem does `satisfies` solve?"

//   Problem: type annotation WIDENS, losing specific info
//   Solution: `satisfies` validates WITHOUT widening

type Colors = Record<string, string | number[]>;

// With annotation -- loses specificity:
const colorsAnnotated: Colors = {
  red: "#FF0000",
  green: [0, 255, 0]
};
// colorsAnnotated.red.toUpperCase(); // ERROR: string | number[]

// With satisfies -- validates AND preserves narrowness:
const colorsSatisfied = {
  red: "#FF0000",
  green: [0, 255, 0]
} satisfies Colors;
colorsSatisfied.red.toUpperCase();   // OK: TS knows it's string
colorsSatisfied.green.map(x => x);   // OK: TS knows it's number[]

//   Annotation:     satisfies:
//   type Colors     type Colors
//       |               |
//   WIDENS to       VALIDATES against
//   Colors type     Colors type
//       |               |
//   Loses "red"     Keeps "red" = string
//   = string|num[]  and "green" = number[]

// GOTCHAS:
// - `satisfies` does NOT change the type; it only validates.
// - Combine with `as const` for maximum narrowing:
//   `{ ... } as const satisfies Schema`


// ============================================================
// 30. CONDITIONAL TYPES                         [ADVANCED]
// ============================================================
// INTERVIEW: "Explain conditional types and distributive behavior."

//   T extends U ? X : Y
//
//   Is T assignable to U?
//     /          \
//   YES          NO
//    X            Y

type IsString<T> = T extends string ? true : false;
type A1 = IsString<"hello">; // true
type A2 = IsString<42>;      // false

// Distributive conditional types (over unions)
type ToArray<T> = T extends any ? T[] : never;
type Result = ToArray<string | number>; // string[] | number[]

// infer keyword -- extract types from patterns
type ElementType<T> = T extends (infer E)[] ? E : T;
type X1 = ElementType<string[]>; // string
type X2 = ElementType<number>;   // number (fallback)

// Flatten arrays
type Flatten<T> = T extends Array<infer U> ? U : T;
type FlatStr = Flatten<string[]>;  // string
type FlatNum = Flatten<number>;    // number

// Extract return type manually (like ReturnType)
type MyReturnType<T> = T extends (...args: any[]) => infer R ? R : never;

// GOTCHAS:
// - Distributive behavior only applies when T is a naked type param.
//   Wrapping in [] disables distribution: [T] extends [U] ? X : Y
// - `infer` only works inside conditional type extends clause.


// ============================================================
// 31. MAPPED TYPES                              [ADVANCED]
// ============================================================
// INTERVIEW: "How do mapped types work?"

//   Source type:        Mapped type transformation:
//   { a: string }  --> { [K in keyof T]: newValueType }
//   { b: number }

type Optional<T> = { [K in keyof T]?: T[K] };
type ReadonlyAll<T> = { readonly [K in keyof T]: T[K] };

// Key remapping (TS 4.1+)
type Getters<T> = {
  [K in keyof T as `get${Capitalize<string & K>}`]: () => T[K]
};
type UserGetters = Getters<User>;
// { getId: () => number; getName: () => string; ... }

// Removing keys
type RemoveKind<T> = {
  [K in keyof T as Exclude<K, "kind">]: T[K]
};

// +/- modifiers
type Mutable<T> = { -readonly [K in keyof T]: T[K] };
type Concrete<T> = { [K in keyof T]-?: T[K] };

// Event handler pattern
type PropChangedHandler<T> = {
  [K in keyof T as `on${Capitalize<string & K>}Changed`]: (newVal: T[K]) => void
};

// GOTCHAS:
// - `keyof T` returns `string | number | symbol`. Use `string & K`
//   to narrow to string keys when needed.
// - Mapped types create new types; they don't modify existing ones.


// ============================================================
// 32. TEMPLATE LITERAL TYPES                    [ADVANCED]
// ============================================================
// INTERVIEW: "What are template literal types?"

type EventName = "click" | "scroll" | "mousemove";
type HandlerName = `on${Capitalize<EventName>}`;
// "onClick" | "onScroll" | "onMousemove"

type CSSUnit = "px" | "em" | "rem" | "%";
type CSSValue = `${number}${CSSUnit}`; // "16px", "1.5em", etc.

type HTTPMethod = "GET" | "POST" | "PUT" | "DELETE";
type APIRoute = `/${string}`;
type Endpoint = `${HTTPMethod} ${APIRoute}`;
// "GET /users", "POST /login", etc.

// Intrinsic string manipulation types:
// Uppercase<S>, Lowercase<S>, Capitalize<S>, Uncapitalize<S>
type Shouting = Uppercase<"hello">; // "HELLO"

// GOTCHAS:
// - Template literal types can create HUGE unions. Avoid cartesian
//   explosions (e.g., combining two large unions).


// ============================================================
// 33. DECLARATION MERGING                       [ADVANCED]
// ============================================================
// INTERVIEW: "What is declaration merging?"

// Interfaces merge when declared with the same name in the same scope:
interface Box {
  width: number;
}
interface Box {
  height: number;
}
// Box is now { width: number; height: number }

// Merging with namespaces (augmenting a class/function):
class Album {
  label: Album.AlbumLabel | undefined;
}
namespace Album {
  export interface AlbumLabel {
    name: string;
  }
}

// GOTCHAS:
// - Type aliases (type) do NOT merge; redeclaring is an error.
// - Later interface declarations must have compatible types for
//   any overlapping members.


// ============================================================
// 34. MODULE AUGMENTATION                       [ADVANCED]
// ============================================================
// INTERVIEW: "How do you add types to third-party modules?"

// Augmenting an existing module's types (e.g., Express):
// declare module "express" {
//   interface Request {
//     userId?: string;
//   }
// }

// Global augmentation:
// declare global {
//   interface Window {
//     analytics: { track(event: string): void };
//   }
// }

// GOTCHAS:
// - Module augmentation file must have at least one top-level
//   import/export to be treated as a module.
// - You can only augment existing declarations; you cannot add
//   entirely new top-level exports via augmentation.


// ============================================================
// 35. NAMESPACE vs MODULE                       [ADVANCED]
// ============================================================
// INTERVIEW: "When to use namespaces vs modules?"

// +-------------------+------------------------------------------+
// | Feature           | Namespace              | Module           |
// +-------------------+------------------------+------------------+
// | Scope             | Global or nested       | File-scoped      |
// | Loading           | Concatenated/<script>  | ESM, CommonJS    |
// | Tree-shaking      | No                     | Yes              |
// | Modern use        | Rarely (decl merging)  | Always (standard)|
// +-------------------+------------------------+------------------+

// Namespace (mostly legacy; avoid in new code)
namespace Validation {
  export interface StringValidator {
    isValid(s: string): boolean;
  }
  export class EmailValidator implements StringValidator {
    isValid(s: string): boolean {
      return s.includes("@");
    }
  }
}
const emailValidator = new Validation.EmailValidator();

// Module (preferred -- this file IS a module because of top-level export)
// import { something } from "./other-module";
// export class MyClass { ... }

// GOTCHAS:
// - A file with no import/export is a SCRIPT (global scope), not a module.
// - `namespace` compiles to IIFE; `module` (the keyword) is deprecated.
// - Use `namespace` only for declaration merging or ambient declarations.


// ============================================================
// 36. DECORATORS (Stage 3 / TS 5.0+)           [ADVANCED]
// ============================================================
// INTERVIEW: "What are decorators and how have they changed?"

// Enable: "experimentalDecorators": true in tsconfig (legacy)
// TS 5.0+ supports Stage 3 decorators natively (no flag needed).

//   Decorator Application Order:
//
//   @classDecorator          <-- applied LAST
//   class Foo {
//     @propertyDecorator     <-- applied 2nd
//     name: string;
//
//     @methodDecorator       <-- applied 1st
//     greet() {}
//   }
//
//   Evaluation: top-down. Application: bottom-up (inner -> outer).

// Legacy decorator example (experimentalDecorators):
// function sealed(constructor: Function) {
//   Object.seal(constructor);
//   Object.seal(constructor.prototype);
// }
// @sealed class Greeter { greeting: string = "hello"; }

// Stage 3 decorator example (TS 5.0+):
function logged<T extends new (...args: any[]) => any>(
  target: T,
  _context: ClassDecoratorContext
) {
  return class extends target {
    constructor(...args: any[]) {
      super(...args);
      console.log(`Created instance of ${target.name}`);
    }
  };
}

// Method decorator
function logMethod(
  _target: any,
  context: ClassMethodDecoratorContext
) {
  const methodName = String(context.name);
  return function (this: any, ...args: any[]) {
    console.log(`Calling ${methodName} with`, args);
    return _target.call(this, ...args);
  };
}

// GOTCHAS:
// - Legacy (experimentalDecorators) and Stage 3 decorators are INCOMPATIBLE.
// - Stage 3 decorators don't support parameter decorators (yet).
// - Decorator factories return the actual decorator: @factory()


// ============================================================
// 37. QUICK INTERVIEW REFERENCE
// ============================================================
//
// Q: "What is structural typing?"
// A: TS uses structural (duck) typing: if an object has the
//    required shape, it's compatible regardless of declaration.
//    Use branded types for nominal behavior:
//    type USD = number & { __brand: "USD" };
//    Prevents accidentally mixing USD and EUR values.
//
// Q: "What is type widening / narrowing?"
// A: Widening: TS broadens literal types (e.g., "hello" -> string)
//    when assigned to let. `const x = "hello"` -> x: "hello" (literal).
//    `as const` prevents widening for objects/arrays.
//    Narrowing: control flow reduces types
//    (typeof, instanceof, in, truthiness checks).
//
// Q: "What is the `satisfies` operator?"
// A: `expr satisfies Type` validates without widening.
//    const cfg = { port: 8080 } satisfies Config;
//    cfg.port is still 8080 (literal), not number.
//
// Q: "What is declaration merging?"
// A: Multiple interface declarations with the same name in the
//    same scope are merged into one. Types (type aliases) cannot merge.
//
// Q: "Explain the `infer` keyword."
// A: Used in conditional types to introduce a type variable:
//    T extends Promise<infer U> ? U : T  -- extracts the Promise value.
//
// Q: "What is the `override` keyword?"
// A: TS 4.3+: marks a method as intentionally overriding a parent.
//    With noImplicitOverride, forgetting it is an error.
//
// Q: "Explain covariance and contravariance."
// A: Covariant: Dog extends Animal => Array<Dog> assignable to Array<Animal>.
//    Contravariant: function params are contravariant (reversed).
//    TS is bivariant for method params by default (unless strictFunctionTypes).
