// ============================================================
// JAVASCRIPT RECURSION -- COMPLETE REFERENCE
// ============================================================
//
// This file covers:
//   BASIC:        What is recursion, base case, sum, countdown, factorial
//   INTERMEDIATE: Fibonacci (naive + memoized), flatten, deep clone,
//                 binary search, power, palindrome, string reversal
//   ADVANCED:     Call stack visualization, tail recursion & TCO,
//                 trampolining, Tower of Hanoi, tree traversal,
//                 permutations, mutual recursion, iterative comparison
//
// Related files:
//   functionsinfo.js  --> pass-by-value, call/apply/bind
//   dmitripavl.js      --> closures, composition, higher-order functions


// ============================================================
// CALL STACK VISUALIZATION                           [BASIC]
// ============================================================
//
// INTERVIEW: "Explain how the call stack works with recursion."
//
// Every function call pushes a frame onto the call stack.
// Recursive calls keep pushing until the base case is reached,
// then frames pop and return values propagate back up.
//
//  add(3) call stack progression:
//
//  PUSH phase (winding):            POP phase (unwinding):
//
//  +------------+                   +------------+
//  | add(0)     | <- base case      | add(0) = 0 | -> return 0
//  +------------+                   +------------+
//  | add(1)     |                   | add(1) = 1 + 0 = 1 | -> return 1
//  +------------+                   +--------------------+
//  | add(2)     |                   | add(2) = 2 + 1 = 3 | -> return 3
//  +------------+                   +--------------------+
//  | add(3)     |                   | add(3) = 3 + 3 = 6 | -> return 6
//  +------------+                   +--------------------+
//
//  Stack depth = N + 1 frames for add(N)
//
//  WARNING: V8 default stack size ~ 10,000-15,000 frames.
//  Exceeding it throws: "RangeError: Maximum call stack size exceeded"


// ============================================================
// 1. RECURSION BASICS                                [BASIC]
// ============================================================
// Every recursive function needs:
//   1. BASE CASE -- condition to stop (prevents infinite recursion)
//   2. RECURSIVE CASE -- function calls itself with a smaller problem
//
// Template:
//   function recurse(input) {
//     if (baseCondition) return baseValue;  // stop
//     return combine( recurse(smallerInput) );  // shrink + recurse
//   }

// --- 1a. Sum of 1..N ---
function sumTo(n) {
  if (n <= 0) return 0;       // base case
  return n + sumTo(n - 1);    // recursive case
}
console.log(sumTo(5)); // 15

//  Trace:
//  sumTo(5) = 5 + sumTo(4)
//           = 5 + 4 + sumTo(3)
//           = 5 + 4 + 3 + sumTo(2)
//           = 5 + 4 + 3 + 2 + sumTo(1)
//           = 5 + 4 + 3 + 2 + 1 + sumTo(0)
//           = 5 + 4 + 3 + 2 + 1 + 0
//           = 15

// --- 1b. Countdown ---
function countDown(n) {
  console.log(n);
  if (n > 1) countDown(n - 1);
}
countDown(3); // 3, 2, 1

// --- 1c. Factorial ---
// INTERVIEW: classic recursion question
function factorial(n) {
  if (n <= 1) return 1;
  return n * factorial(n - 1);
}
console.log(factorial(5));  // 120
console.log(factorial(0));  // 1
console.log(factorial(10)); // 3628800


// ============================================================
// 2. FIBONACCI                                  [INTERMEDIATE]
// ============================================================
// INTERVIEW: "Write fibonacci recursively. What's the time complexity?
//  How would you optimize it?"
//
//  Fibonacci: 0, 1, 1, 2, 3, 5, 8, 13, 21, 34, ...
//  fib(n) = fib(n-1) + fib(n-2),  fib(0)=0, fib(1)=1
//
//  Naive recursive call tree for fib(5):
//
//                    fib(5)
//                   /      \
//              fib(4)      fib(3)
//             /    \       /    \
//         fib(3)  fib(2) fib(2) fib(1)
//         /   \   /  \   /  \
//     fib(2) fib(1) ...  ...
//     /   \
//  fib(1) fib(0)
//
//  Time: O(2^n) -- exponential!
//  Space: O(n) -- max stack depth

// --- 2a. Naive (exponential) ---
function fibNaive(n) {
  if (n <= 0) return 0;
  if (n === 1) return 1;
  return fibNaive(n - 1) + fibNaive(n - 2);
}
console.log(fibNaive(10)); // 55

// --- 2b. Memoized (linear) ---  [ADVANCED]
// INTERVIEW: "What is memoization?"
// Caching previously computed results to avoid redundant work.
// Reduces fibonacci from O(2^n) to O(n).
//
//  With memoization, fib(5) call tree:
//
//                fib(5)
//               /      \
//          fib(4)     fib(3) <-- cache hit!
//         /    \
//     fib(3)  fib(2) <-- cache hit!
//     /    \
//  fib(2)  fib(1) <-- cache hit!
//  /    \
// fib(1) fib(0)
//
//  Only N unique calls instead of 2^N

function fibMemo(n, memo = {}) {
  if (n in memo) return memo[n];
  if (n <= 0) return 0;
  if (n === 1) return 1;
  memo[n] = fibMemo(n - 1, memo) + fibMemo(n - 2, memo);
  return memo[n];
}
console.log(fibMemo(10));  // 55
console.log(fibMemo(50));  // 12586269025 (instant, not heat-death-of-universe)

// --- 2c. Generic memoize wrapper ---  [ADVANCED]
function memoize(fn) {
  const cache = new Map();
  return function (...args) {
    const key = JSON.stringify(args);
    if (cache.has(key)) return cache.get(key);
    const result = fn.apply(this, args);
    cache.set(key, result);
    return result;
  };
}

const fastFib = memoize(function fib(n) {
  if (n <= 0) return 0;
  if (n === 1) return 1;
  return fastFib(n - 1) + fastFib(n - 2);
});
console.log(fastFib(40)); // 102334155

// --- 2d. Iterative fibonacci (comparison) ---
function fibIterative(n) {
  if (n <= 0) return 0;
  let a = 0, b = 1;
  for (let i = 2; i <= n; i++) {
    [a, b] = [b, a + b];
  }
  return b;
}
console.log(fibIterative(10)); // 55
console.log(fibIterative(50)); // 12586269025


// ============================================================
// 3. CLASSIC RECURSION PROBLEMS                 [INTERMEDIATE]
// ============================================================

// --- 3a. String Reversal ---
function reverseStr(str) {
  if (str.length <= 1) return str;
  return reverseStr(str.slice(1)) + str[0];
}
console.log(reverseStr("hello")); // "olleh"

// --- 3b. Palindrome Check ---
function isPalindrome(str) {
  str = str.toLowerCase().replace(/[^a-z0-9]/g, '');
  if (str.length <= 1) return true;
  if (str[0] !== str[str.length - 1]) return false;
  return isPalindrome(str.slice(1, -1));
}
console.log(isPalindrome("racecar"));    // true
console.log(isPalindrome("A man a plan a canal Panama")); // true
console.log(isPalindrome("hello"));      // false

// --- 3c. Flatten Nested Array ---
// INTERVIEW: commonly asked
function flatten(arr) {
  let result = [];
  for (const item of arr) {
    if (Array.isArray(item)) {
      result = result.concat(flatten(item));
    } else {
      result.push(item);
    }
  }
  return result;
}
console.log(flatten([1, [2, [3, [4]], 5]])); // [1, 2, 3, 4, 5]
// Note: modern JS has Array.prototype.flat(Infinity)

// --- 3d. Deep Clone ---
function deepClone(obj) {
  if (obj === null || typeof obj !== 'object') return obj;
  if (Array.isArray(obj)) return obj.map(deepClone);
  const clone = {};
  for (const key in obj) {
    if (obj.hasOwnProperty(key)) {
      clone[key] = deepClone(obj[key]);
    }
  }
  return clone;
}
const original = { a: 1, b: { c: [2, 3] } };
const cloned = deepClone(original);
cloned.b.c.push(4);
console.log(original.b.c); // [2, 3] -- original unchanged
console.log(cloned.b.c);   // [2, 3, 4]

// --- 3e. Power (exponentiation) ---
function power(base, exp) {
  if (exp === 0) return 1;
  if (exp < 0) return 1 / power(base, -exp);
  return base * power(base, exp - 1);
}
console.log(power(2, 10)); // 1024
console.log(power(2, -2)); // 0.25

// Fast power O(log n) using repeated squaring
function fastPower(base, exp) {
  if (exp === 0) return 1;
  if (exp < 0) return 1 / fastPower(base, -exp);
  if (exp % 2 === 0) {
    const half = fastPower(base, exp / 2);
    return half * half;
  }
  return base * fastPower(base, exp - 1);
}
console.log(fastPower(2, 10)); // 1024

// --- 3f. Binary Search (recursive) ---
function binarySearch(arr, target, low = 0, high = arr.length - 1) {
  if (low > high) return -1;
  const mid = Math.floor((low + high) / 2);
  if (arr[mid] === target) return mid;
  if (arr[mid] < target) return binarySearch(arr, target, mid + 1, high);
  return binarySearch(arr, target, low, mid - 1);
}
console.log(binarySearch([1, 3, 5, 7, 9, 11], 7));  // 3
console.log(binarySearch([1, 3, 5, 7, 9, 11], 4));  // -1


// ============================================================
// 4. TOWER OF HANOI                                 [ADVANCED]
// ============================================================
// INTERVIEW: classic CS recursion problem
//
//  Move N disks from source to target using an auxiliary peg.
//  Rules: 1) Move one disk at a time
//         2) Never place a larger disk on a smaller one
//
//  For N=3:
//    Peg A (source)    Peg B (aux)     Peg C (target)
//      |                 |                |
//     [1]                |                |
//    [  2]               |                |
//   [   3]               |                |
//
//  Steps: 2^N - 1 = 7 moves

function hanoi(n, source = 'A', target = 'C', auxiliary = 'B') {
  if (n === 1) {
    console.log(`Move disk 1 from ${source} to ${target}`);
    return;
  }
  hanoi(n - 1, source, auxiliary, target);   // move n-1 disks to aux
  console.log(`Move disk ${n} from ${source} to ${target}`);
  hanoi(n - 1, auxiliary, target, source);   // move n-1 disks from aux to target
}
console.log('--- Tower of Hanoi (3 disks) ---');
hanoi(3);
// Move disk 1 from A to C
// Move disk 2 from A to B
// Move disk 1 from C to B
// Move disk 3 from A to C
// Move disk 1 from B to A
// Move disk 2 from B to C
// Move disk 1 from A to C


// ============================================================
// 5. TREE TRAVERSAL                                 [ADVANCED]
// ============================================================
// INTERVIEW: "Traverse a tree recursively."
//
//  Binary tree structure:
//           1
//          / \
//         2   3
//        / \   \
//       4   5   6
//
//  Traversal orders:
//    Pre-order  (Root, Left, Right): 1, 2, 4, 5, 3, 6
//    In-order   (Left, Root, Right): 4, 2, 5, 1, 3, 6
//    Post-order (Left, Right, Root): 4, 5, 2, 6, 3, 1

class TreeNode {
  constructor(val, left = null, right = null) {
    this.val = val;
    this.left = left;
    this.right = right;
  }
}

// Build the sample tree
const tree = new TreeNode(1,
  new TreeNode(2, new TreeNode(4), new TreeNode(5)),
  new TreeNode(3, null, new TreeNode(6))
);

function preOrder(node, result = []) {
  if (!node) return result;
  result.push(node.val);       // Root
  preOrder(node.left, result); // Left
  preOrder(node.right, result);// Right
  return result;
}

function inOrder(node, result = []) {
  if (!node) return result;
  inOrder(node.left, result);  // Left
  result.push(node.val);       // Root
  inOrder(node.right, result); // Right
  return result;
}

function postOrder(node, result = []) {
  if (!node) return result;
  postOrder(node.left, result);  // Left
  postOrder(node.right, result); // Right
  result.push(node.val);         // Root
  return result;
}

console.log('Pre-order: ', preOrder(tree));  // [1, 2, 4, 5, 3, 6]
console.log('In-order:  ', inOrder(tree));   // [4, 2, 5, 1, 3, 6]
console.log('Post-order:', postOrder(tree)); // [4, 5, 2, 6, 3, 1]

// General tree / nested object traversal (e.g., DOM, file system)
function walkTree(node, visit) {
  visit(node);
  if (node.children) {
    for (const child of node.children) {
      walkTree(child, visit);
    }
  }
}

const fileSystem = {
  name: 'root', children: [
    { name: 'src', children: [
      { name: 'index.js', children: [] },
      { name: 'utils.js', children: [] },
    ]},
    { name: 'README.md', children: [] },
  ]
};
const names = [];
walkTree(fileSystem, (node) => names.push(node.name));
console.log(names); // ["root", "src", "index.js", "utils.js", "README.md"]


// ============================================================
// 6. PERMUTATIONS                                   [ADVANCED]
// ============================================================
// INTERVIEW: "Generate all permutations of an array."
//
//  For [1, 2, 3]:
//  [1,2,3], [1,3,2], [2,1,3], [2,3,1], [3,1,2], [3,2,1]
//  Total = n! = 6

function permutations(arr) {
  if (arr.length <= 1) return [arr];
  const result = [];
  for (let i = 0; i < arr.length; i++) {
    const current = arr[i];
    const remaining = [...arr.slice(0, i), ...arr.slice(i + 1)];
    const perms = permutations(remaining);
    for (const perm of perms) {
      result.push([current, ...perm]);
    }
  }
  return result;
}
console.log(permutations([1, 2, 3]));
// [[1,2,3],[1,3,2],[2,1,3],[2,3,1],[3,1,2],[3,2,1]]

// String permutations
function stringPermutations(str) {
  return permutations([...str]).map(chars => chars.join(''));
}
console.log(stringPermutations('abc'));
// ["abc","acb","bac","bca","cab","cba"]


// ============================================================
// 7. MUTUAL RECURSION                               [ADVANCED]
// ============================================================
// INTERVIEW: "What is mutual recursion?"
// Two or more functions that call each other.
//
//  isEven(4) -> isOdd(3) -> isEven(2) -> isOdd(1) -> isEven(0) -> true
//
//  ASCII diagram:
//  isEven(4) --calls--> isOdd(3) --calls--> isEven(2) --calls--> isOdd(1) --calls--> isEven(0)
//      ^                                                                                  |
//      |                              returns true <--------------------------------------+

function isEvenMutual(n) {
  if (n === 0) return true;
  return isOddMutual(Math.abs(n) - 1);
}

function isOddMutual(n) {
  if (n === 0) return false;
  return isEvenMutual(Math.abs(n) - 1);
}

console.log(isEvenMutual(4));  // true
console.log(isEvenMutual(3));  // false
console.log(isOddMutual(5));   // true

// Practical mutual recursion: parsing nested structures
// e.g., JSON parser where parseValue calls parseArray which calls parseValue


// ============================================================
// 8. TAIL RECURSION & TCO                           [ADVANCED]
// ============================================================
// INTERVIEW: "What is tail call optimization?"
//
//  A tail call is when the recursive call is the LAST operation
//  in the function (nothing happens after it returns).
//
//  Non-tail:   return n * factorial(n-1)     <-- multiply AFTER call
//  Tail:       return factTail(n-1, n*acc)   <-- call IS the last thing
//
//  With TCO, the engine reuses the current stack frame instead
//  of pushing a new one. This makes recursion O(1) space.
//
//  +----------------------------------------------+
//  | Non-tail (grows stack)  | Tail (constant)    |
//  |-------------------------+--------------------|
//  | factorial(5)            | factTail(5, 1)     |
//  |   5 * factorial(4)      |   factTail(4, 5)   |
//  |     4 * factorial(3)    |     factTail(3, 20) |
//  |       3 * factorial(2)  |       factTail(2,60)|
//  |         2 * factorial(1)|         factTail(1, |
//  |           1             |           120)      |
//  |         = 2             |         = 120       |
//  |       = 6               |                     |
//  |     = 24                | Stack depth: 1      |
//  |   = 120                 | (with TCO enabled)  |
//  | Stack depth: 5          |                     |
//  +----------------------------------------------+
//
//  IMPORTANT: As of 2026, only Safari (JavaScriptCore) implements
//  TCO. V8 (Chrome/Node) does NOT. So tail recursion in JS is a
//  correctness pattern but not a performance guarantee in most engines.

// Non-tail recursive factorial (grows stack)
function factorialNonTail(n) {
  if (n <= 1) return 1;
  return n * factorialNonTail(n - 1); // multiplication after call
}

// Tail recursive factorial (constant stack with TCO)
function factorialTail(n, accumulator = 1) {
  if (n <= 1) return accumulator;
  return factorialTail(n - 1, n * accumulator); // nothing after call
}
console.log(factorialTail(5));   // 120
console.log(factorialTail(20));  // 2432902008176640000

// Tail recursive sum
function sumTail(n, acc = 0) {
  if (n <= 0) return acc;
  return sumTail(n - 1, acc + n);
}
console.log(sumTail(10000)); // 50005000 (would overflow non-tail in some engines)


// ============================================================
// 9. TRAMPOLINING                                   [ADVANCED]
// ============================================================
// INTERVIEW: "How can you prevent stack overflow in recursive JS
//  when TCO is not available?"
//
//  A trampoline converts recursion into iteration by returning
//  thunks (functions) instead of making direct recursive calls.
//  The trampoline loop keeps calling the thunks until a non-function
//  value is returned.
//
//  ASCII diagram:
//
//  Normal recursion:           Trampolined:
//  f(3) calls f(2)             trampoline(f(3))
//    f(2) calls f(1)             loop: f(3) -> thunk
//      f(1) calls f(0)           loop: f(2) -> thunk
//        f(0) returns 0          loop: f(1) -> thunk
//      returns 1                 loop: f(0) -> 0 (done!)
//    returns 3
//  returns 6                   Stack depth: always 1!
//
//  The trampoline trades stack depth for a loop iteration.

function trampoline(fn) {
  return function (...args) {
    let result = fn(...args);
    while (typeof result === 'function') {
      result = result(); // "bounce" -- call the thunk
    }
    return result;
  };
}

// Trampolined factorial
function factTramp(n, acc = 1) {
  if (n <= 1) return acc;
  return () => factTramp(n - 1, n * acc); // return thunk, don't recurse
}

const safeFact = trampoline(factTramp);
console.log(safeFact(5));     // 120
console.log(safeFact(20));    // 2432902008176640000
// console.log(safeFact(100000)); // works! no stack overflow

// Trampolined sum (would overflow at ~10k without trampoline)
function sumTramp(n, acc = 0) {
  if (n <= 0) return acc;
  return () => sumTramp(n - 1, acc + n);
}

const safeSum = trampoline(sumTramp);
console.log(safeSum(10000));  // 50005000
// console.log(safeSum(1000000)); // works without stack overflow

// Trampolined mutual recursion
function isEvenTramp(n) {
  if (n === 0) return true;
  return () => isOddTramp(n - 1);
}
function isOddTramp(n) {
  if (n === 0) return false;
  return () => isEvenTramp(n - 1);
}
const safeIsEven = trampoline(isEvenTramp);
console.log(safeIsEven(100000)); // true (no stack overflow)


// ============================================================
// 10. ITERATIVE vs RECURSIVE COMPARISON             [ADVANCED]
// ============================================================
// INTERVIEW: "When should you use recursion vs iteration?"
//
//  +--------------------------------------------------------------+
//  | Aspect           | Recursive           | Iterative           |
//  |------------------+----------------------+---------------------|
//  | Readability      | Often cleaner for    | Better for simple   |
//  |                  | tree/graph problems  | linear problems     |
//  | Stack usage      | O(n) frames (risk    | O(1) (loop)         |
//  |                  | of overflow)         |                     |
//  | Performance      | Function call        | Loop overhead is    |
//  |                  | overhead per frame   | minimal             |
//  | State management | Implicit (call stack)| Explicit (variables)|
//  | Debugging        | Stack trace helps    | Step-through easier |
//  | Tail optimization| Possible (Safari)    | N/A                 |
//  | Best for         | Trees, graphs, divide| Arrays, counters,   |
//  |                  | & conquer, backtrack | simple sequences    |
//  +--------------------------------------------------------------+
//
// Rule of thumb:
//   Use recursion when the problem has a recursive STRUCTURE
//   (trees, nested data, divide & conquer).
//   Convert to iteration when stack depth is a concern.

// --- Factorial: recursive vs iterative ---
function factRec(n) {
  if (n <= 1) return 1;
  return n * factRec(n - 1);
}

function factIter(n) {
  let result = 1;
  for (let i = 2; i <= n; i++) result *= i;
  return result;
}

console.log(factRec(10));  // 3628800
console.log(factIter(10)); // 3628800

// --- Flatten: recursive vs iterative (with stack) ---
function flattenRec(arr) {
  let result = [];
  for (const item of arr) {
    if (Array.isArray(item)) result = result.concat(flattenRec(item));
    else result.push(item);
  }
  return result;
}

function flattenIter(arr) {
  const stack = [...arr];
  const result = [];
  while (stack.length) {
    const item = stack.pop();
    if (Array.isArray(item)) stack.push(...item);
    else result.push(item);
  }
  return result.reverse(); // pop reverses order
}

console.log(flattenRec([1, [2, [3, [4]]]]));  // [1, 2, 3, 4]
console.log(flattenIter([1, [2, [3, [4]]]])); // [1, 2, 3, 4]

// --- Sum: recursive vs iterative ---
function sumRec(n) {
  if (n <= 0) return 0;
  return n + sumRec(n - 1);
}

function sumIter(n) {
  // O(1) formula: Gauss's trick
  return (n * (n + 1)) / 2;
}

console.log(sumRec(100));  // 5050
console.log(sumIter(100)); // 5050


// ============================================================
// 11. BONUS: MORE RECURSION PATTERNS                [ADVANCED]
// ============================================================

// --- 11a. GCD (Euclidean algorithm) ---
function gcd(a, b) {
  if (b === 0) return a;
  return gcd(b, a % b);
}
console.log(gcd(48, 18)); // 6

// --- 11b. Count occurrences in nested structure ---
function countValue(data, target) {
  if (!Array.isArray(data)) return data === target ? 1 : 0;
  return data.reduce((sum, item) => sum + countValue(item, target), 0);
}
console.log(countValue([1, [2, 1, [1, 3]], 1], 1)); // 4

// --- 11c. Generate nested object paths ---
function getPaths(obj, prefix = '') {
  let paths = [];
  for (const key of Object.keys(obj)) {
    const fullPath = prefix ? `${prefix}.${key}` : key;
    if (typeof obj[key] === 'object' && obj[key] !== null && !Array.isArray(obj[key])) {
      paths = paths.concat(getPaths(obj[key], fullPath));
    } else {
      paths.push(fullPath);
    }
  }
  return paths;
}
console.log(getPaths({ a: 1, b: { c: 2, d: { e: 3 } } }));
// ["a", "b.c", "b.d.e"]

// --- 11d. Combinations (n choose k) ---
function combinations(arr, k) {
  if (k === 0) return [[]];
  if (arr.length === 0) return [];
  const [first, ...rest] = arr;
  // Include first element
  const withFirst = combinations(rest, k - 1).map(c => [first, ...c]);
  // Exclude first element
  const withoutFirst = combinations(rest, k);
  return [...withFirst, ...withoutFirst];
}
console.log(combinations([1, 2, 3, 4], 2));
// [[1,2],[1,3],[1,4],[2,3],[2,4],[3,4]]


// ============================================================
// GOTCHAS -- RECURSION
// ============================================================
//
// 1. Missing base case = infinite recursion = stack overflow
//    ALWAYS define the termination condition first.
//
// 2. Stack limit: ~10,000-15,000 frames in V8.
//    Use trampolining or convert to iteration for deep recursion.
//
// 3. Naive recursion can be exponential (e.g., fibonacci O(2^n)).
//    Memoization or dynamic programming brings it to O(n).
//
// 4. Mutation in recursive calls: be careful passing arrays/objects.
//    Use spread/slice to avoid accidentally sharing state between frames.
//
// 5. Tail call optimization only works in Safari.
//    Do NOT rely on it in Node.js or Chrome.
//
// 6. Recursive regex (like matching balanced parens) can also
//    overflow the internal regex engine stack. Use iterative parsing.
//
// 7. Every recursive solution has an iterative equivalent
//    (Church-Turing thesis). The iterative version uses an explicit
//    stack (array) to simulate the call stack.
//
// 8. For interview practice, always:
//    a) Identify the base case
//    b) Identify how the problem shrinks
//    c) Trust the recursion (assume the recursive call works)
//    d) Analyze time/space complexity
