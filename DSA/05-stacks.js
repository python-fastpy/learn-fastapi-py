/* ============================================================================
 * STACKS — LIFO DATA STRUCTURE  [BASIC / INTERMEDIATE / ADVANCED]
 * ============================================================================
 * TABLE OF CONTENTS
 * --------------------------------------------------------------------------
 *  --- Stack Implementations ---
 *  2.1  Stack (ES6 class, array-backed)                 [BASIC]
 *  2.2  StackObj (object-backed, head pointer)          [BASIC]
 *  2.3  StackIndex (function-based, manual index)       [BASIC]
 *  2.4  StackIIFE (closure-based privacy)               [BASIC]
 *  2.5  StackWeakMap (WeakMap true privacy)             [BASIC]
 *  2.6  StackLinkedList (singly linked list)            [INTERMEDIATE]
 *  2.7  MinStack (O(1) getMin)                          [INTERMEDIATE]
 *  --- Classic Stack Problems ---
 *  2.8  Balanced Parentheses (isBalanced)               [INTERMEDIATE]
 *  2.9  Infix to Postfix                                [ADVANCED]
 *  2.10 Evaluate Postfix                                [INTERMEDIATE]
 *  2.11 Next Greater Element (monotonic stack)          [ADVANCED]
 *  --- Stack Applications ---
 *  2.12 Undo/Redo Manager                               [INTERMEDIATE]
 *  2.13 Browser History                                 [INTERMEDIATE]
 *  2.14 Call Stack Visualization                        [INTERMEDIATE]
 *  --- Stack Gotchas & Interview Tips ---
 * ==========================================================================*/
//
// STACK FUNDAMENTALS
// ------------------
// A Stack is a linear data structure that follows LIFO:
// Last In, First Out. Think of a stack of plates — you add
// (push) to the top and remove (pop) from the top only.
//
// ASCII DIAGRAM — LIFO behavior
//
//   push(1)      push(2)      push(3)       pop() -> 3
//   ---------    ---------    ---------     ---------
//   |       |    |       |    |   3   | <-- top |       |
//   ---------    |   2   | <- |   2   |    |   2   | <-- top
//   |   1   | <- |   1   |    |   1   |    |   1   |
//   ---------    ---------    ---------     ---------
//
//   Only the TOP element is ever accessible directly.
//
// CORE OPERATIONS & BIG-O (array-backed stack)
//   push(item)   -> add to top                 O(1)
//   pop()        -> remove & return top         O(1)
//   peek()/top() -> read top without removing   O(1)
//   isEmpty()    -> check if stack has 0 items  O(1)
//   size()       -> number of items             O(1)
//   clear()      -> remove all items            O(1) or O(n) (GC)
//   search(item) -> find item                   O(n)
//
// INTERVIEW: "Why is array push/pop O(1) but shift/unshift O(n)?"
//   push/pop operate at the END of the array (no re-indexing).
//   shift/unshift operate at the START (every element must be
//   re-indexed) — so ALWAYS use push/pop for stack behavior.
//
// REAL-WORLD APPLICATIONS
//   - Undo/Redo in editors (each action pushed; undo = pop)
//   - Browser back/forward history
//   - Function call stack (recursion, stack overflow errors)
//   - Expression evaluation / parsing (compilers, calculators)
//   - Balanced bracket / syntax checking
//   - Backtracking algorithms (maze solving, DFS)
//
// A NOTE ON ++ / -- (PRE vs POST INCREMENT)
//   let n = 0;
//   console.log(n++);   // 0  -> logs OLD value, THEN increments
//   console.log(n);     // 1
//   console.log(++n);   // 2  -> increments FIRST, THEN logs
//   In array-based stacks, `this.items[this.top++] = value` is a
//   classic combo: assign at current top, THEN bump top by 1.

// ------------------------------ 2.1 Stack (array-backed) ------------------------------
// [BASIC] LIFO — Last In First Out.
//
// ASCII diagram (push 1,20,30 — top is rightmost/topmost):
//        ┌────┐  <- top (pop/peek here)
//        │ 30 │
//        ├────┤
//        │ 20 │
//        ├────┤
//        │ 1  │
//        └────┘
// Usage: browser history, undo, expression parsing, JS call stack.
// Ops: push, pop, peek, isEmpty, size, print

class Stack {
    constructor() {
        this.items = [];
    }
    push(element) { this.items.push(element); }
    pop() { return this.items.pop(); }
    peek() { return this.items[this.items.length - 1]; }
    isEmpty() { return this.items.length === 0; }
    size() { return this.items.length; }
    print() { console.log(this.items.toString()); }
}
let stack = new Stack();
console.log(stack.isEmpty());
console.log(stack.push(1));
console.log(stack.push(20));
console.log(stack.push(30));
console.log(stack.size());
stack.pop();
console.log(stack.print());
console.log(stack.peek());
// Big-O: push/pop/peek O(1) | search O(n)
// GOTCHAS: Array-based push/pop are O(1) amortized; using shift/unshift instead
// would make it O(n) — always add/remove at the END for a stack.

// ------------------------------ 2.2 StackObj (object-backed) ------------------------------
// [BASIC] Same LIFO semantics, using a plain object + head pointer instead
// of relying on array internals (useful to show hashmap-style storage).
class StackObj {
    constructor() {
        this.items = {};
        this.head = 0;
    }
    push(element) {
        this.items[this.head] = element;
        this.head++;
    }
    pop() {
        if (this.head === 0) return undefined;
        const item = this.items[this.head - 1];
        delete this.items[this.head - 1];
        this.head--;
        return item;
    }
    peek() { return this.items[this.head - 1]; }
    size() { return this.head; }
    isEmpty() { return this.head === 0; }
    print() { console.log(this.items); }
}
const stackObj = new StackObj();
stackObj.push(1);
stackObj.push(2);
stackObj.print();
console.log(stackObj.pop(), stackObj.peek(), stackObj.size());
// GOTCHAS: object keys are stringified integers — fine for a stack because
// access is always by `head`, never by iteration order.

// ------------------------------ 2.3 StackIndex (function-based, manual index) ------------------------------
// [BASIC] Manually tracks a `top` pointer instead of relying on
// array.length. Mirrors how a stack is built in C/Java with a
// fixed-size array. Good for explaining index math in interviews.
//
// INTERVIEW: commonly asked to implement a stack "from scratch"
// without using push()/pop(), to prove you understand the mechanics.
function StackIndex() {
  let items = [];
  let top = 0; // number of elements currently stored (next free slot)

  this.push = function (element) {
    items[top++] = element; // assign at current top, THEN increment
  };

  this.pop = function () {
    return items[--top]; // decrement FIRST, then read that slot
  };

  this.peek = function () {
    return items[top - 1];
  };

  this.isEmpty = function () {
    return top === 0;
  };

  this.clear = function () {
    top = 0;
  };

  this.size = function () {
    return top;
  };
}

const stackIndex = new StackIndex();
stackIndex.push(100);
stackIndex.push(200);
stackIndex.push(300);
console.log('StackIndex pop:', stackIndex.pop());       // 300
console.log('StackIndex peek:', stackIndex.peek());     // 200
console.log('StackIndex isEmpty:', stackIndex.isEmpty()); // false
console.log('StackIndex size:', stackIndex.size());      // 2
stackIndex.clear();
console.log('StackIndex isEmpty after clear:', stackIndex.isEmpty()); // true

// ------------------------------ 2.4 StackIIFE (closure-based privacy) ------------------------------
// [BASIC] Pre-#field pattern: an Immediately Invoked Function Expression
// returns a constructor whose methods close over a private
// `items` array declared with `let` inside the IIFE. Nobody
// outside can reach `items` directly — there is no `.items`
// property on the instance at all.
//
// INTERVIEW: explain how closures create "privacy" in JS before
// class fields existed — this is exactly that mechanism.
const StackIIFE = (function () {
  return function Stack() {
    let items = []; // private via closure, not an instance property

    this.push = function (element) {
      items.push(element);
    };

    this.pop = function () {
      return items.pop();
    };

    this.peek = function () {
      return items[items.length - 1];
    };

    this.isEmpty = function () {
      return items.length === 0;
    };

    this.size = function () {
      return items.length;
    };

    this.clear = function () {
      items.length = 0;
    };
  };
})();

const stackIIFE = new StackIIFE();
stackIIFE.push(100);
stackIIFE.push(200);
stackIIFE.push(300);
console.log('StackIIFE pop:', stackIIFE.pop());       // 300
console.log('StackIIFE peek:', stackIIFE.peek());     // 200
console.log('StackIIFE isEmpty:', stackIIFE.isEmpty()); // false
console.log('StackIIFE size:', stackIIFE.size());      // 2
stackIIFE.clear();
console.log('StackIIFE isEmpty after clear:', stackIIFE.isEmpty()); // true
// stackIIFE.items is undefined -- there IS no `items` property on
// the instance; it only exists inside the closure.
console.log('StackIIFE.items (should be undefined):', stackIIFE.items);

// ------------------------------ 2.5 StackWeakMap (WeakMap true privacy) ------------------------------
// [BASIC] Uses a module-level WeakMap keyed by `this` to store each
// instance's private array. Unlike a plain closure variable, this
// scales cleanly to MANY instances without redefining methods per
// instance (methods live on the prototype, shared across all
// instances). It also garbage-collects automatically once the
// instance itself is no longer referenced.
//
// INTERVIEW: contrast this with #private class fields — WeakMap privacy
// can still be bypassed by code that holds a reference to the WeakMap
// itself; #fields cannot be bypassed at all, even with such a reference.
const stackPrivateData = new WeakMap();

class StackWeakMap {
  constructor() {
    stackPrivateData.set(this, []); // private storage, keyed by instance
  }

  push(element) {
    stackPrivateData.get(this).push(element);
  }

  pop() {
    return stackPrivateData.get(this).pop();
  }

  peek() {
    const items = stackPrivateData.get(this);
    return items[items.length - 1];
  }

  isEmpty() {
    return stackPrivateData.get(this).length === 0;
  }

  clear() {
    stackPrivateData.set(this, []);
  }

  size() {
    return stackPrivateData.get(this).length;
  }
}

const stackWeakMap = new StackWeakMap();
stackWeakMap.push(100);
stackWeakMap.push(200);
stackWeakMap.push(300);
console.log('StackWeakMap pop:', stackWeakMap.pop());       // 300
console.log('StackWeakMap peek:', stackWeakMap.peek());     // 200
console.log('StackWeakMap isEmpty:', stackWeakMap.isEmpty()); // false
console.log('StackWeakMap size:', stackWeakMap.size());      // 2
stackWeakMap.clear();
console.log('StackWeakMap isEmpty after clear:', stackWeakMap.isEmpty()); // true

// ------------------------------ 2.6 StackLinkedList ------------------------------
// [INTERMEDIATE] Stack backed by a singly linked list.
// Instead of an array, each element is a Node pointing to the
// element below it. `top` always points to the head node.
// push/pop only ever touch the head -> both O(1), and no array
// resizing / index shifting is ever needed.
//
// ASCII DIAGRAM
//   top -> [30] -> [20] -> [10] -> null
//           ^head            ^bottom
//
// INTERVIEW: "Why use a linked list instead of an array for a
// stack?" -> No pre-allocation/resizing cost, O(1) push/pop with
// no amortization concerns, memory used only as needed. Trade-off:
// extra memory per node (pointer overhead) and no O(1) random
// access (but stacks never need random access anyway).
class StackNode {
  constructor(value, next = null) {
    this.value = value;
    this.next = next;
  }
}

class StackLinkedList {
  constructor() {
    this.top = null;
    this.length = 0;
  }

  push(value) {
    this.top = new StackNode(value, this.top); // new node becomes head
    this.length++;
  }

  pop() {
    if (this.isEmpty()) return undefined;
    const { value } = this.top;
    this.top = this.top.next; // unlink head
    this.length--;
    return value;
  }

  peek() {
    return this.top ? this.top.value : undefined;
  }

  isEmpty() {
    return this.top === null;
  }

  size() {
    return this.length;
  }

  clear() {
    this.top = null;
    this.length = 0;
  }

  toArray() {
    // returns top -> bottom order
    const out = [];
    let node = this.top;
    while (node) {
      out.push(node.value);
      node = node.next;
    }
    return out;
  }
}

const stackLinkedList = new StackLinkedList();
stackLinkedList.push(10);
stackLinkedList.push(20);
stackLinkedList.push(30);
console.log('StackLinkedList (top->bottom):', stackLinkedList.toArray()); // [30, 20, 10]
console.log('StackLinkedList pop:', stackLinkedList.pop());               // 30
console.log('StackLinkedList size:', stackLinkedList.size());             // 2

// ------------------------------ 2.7 MinStack (O(1) getMin) ------------------------------
// [INTERMEDIATE] Classic interview problem (LeetCode 155). A plain
// stack gives O(n) min lookup (must scan everything). MinStack keeps
// a SECOND, auxiliary stack that tracks the running minimum at each
// push, so getMin() is O(1).
//
// ASCII DIAGRAM (push order: 5, 3, 7, 2)
//   main:  [5, 3, 7, 2]   (top = 2)
//   minSt: [5, 3, 3, 2]   (top = 2)  <- running min at each depth
//
// INTERVIEW: commonly asked as "design a stack that supports
// push, pop, top, and retrieving the minimum element in O(1)."
// Key insight: push the CURRENT min (not just smaller values) onto
// the aux stack every single time, so pop() stays perfectly in sync.
class MinStack {
  constructor() {
    this.main = [];
    this.minTrack = []; // parallel stack: minTrack[i] = min of main[0..i]
  }

  push(value) {
    this.main.push(value);
    const currentMin =
      this.minTrack.length === 0
        ? value
        : Math.min(value, this.minTrack[this.minTrack.length - 1]);
    this.minTrack.push(currentMin);
  }

  pop() {
    this.minTrack.pop(); // keep both stacks in lockstep
    return this.main.pop();
  }

  top() {
    return this.main[this.main.length - 1];
  }

  getMin() {
    return this.minTrack[this.minTrack.length - 1];
  }

  isEmpty() {
    return this.main.length === 0;
  }
}

const minStack = new MinStack();
minStack.push(5);
minStack.push(3);
minStack.push(7);
minStack.push(2);
console.log('MinStack getMin:', minStack.getMin());          // 2
minStack.pop(); // removes 2
console.log('MinStack getMin after pop:', minStack.getMin()); // 3
console.log('MinStack top:', minStack.top());                 // 7
// GOTCHA: a naive MinStack that only pushes to minTrack "when the
// new value is smaller" breaks on pop() — the two stacks fall out
// of sync. ALWAYS push a min value on every push, even if it's a
// duplicate of the previous min.


// ============================================================
// CLASSIC STACK PROBLEMS [INTERMEDIATE / ADVANCED]
// ============================================================

// ------------------------------ 2.8 Balanced Parentheses ------------------------------
// [INTERMEDIATE] Push opening brackets. On a closing bracket, pop
// and check it matches. Valid iff the stack is empty at the end.
//
// ASCII DIAGRAM for "{[()]}"
//   read {  -> push {         stack: {
//   read [  -> push [         stack: { [
//   read (  -> push (         stack: { [ (
//   read )  -> pop, matches ( stack: { [
//   read ]  -> pop, matches [ stack: {
//   read }  -> pop, matches { stack: (empty) -> VALID
//
// INTERVIEW: THE #1 most-asked stack question. Also appears as
// "valid HTML tags" or "matching XML tags" with the same pattern.
// Big-O: O(n) time, O(n) worst-case space (all openers).
function isBalanced(expression) {
  const pairs = { ')': '(', ']': '[', '}': '{' };
  const openers = new Set(['(', '[', '{']);
  const stack = [];

  for (const char of expression) {
    if (openers.has(char)) {
      stack.push(char);
    } else if (char in pairs) {
      if (stack.pop() !== pairs[char]) return false; // mismatch or empty
    }
    // any other character (letters, digits, spaces) is ignored
  }
  return stack.length === 0; // GOTCHA: must also check nothing is left over
}

console.log('isBalanced "{[()]}":', isBalanced('{[()]}')); // true
console.log('isBalanced "{[(])}":', isBalanced('{[(])}')); // false
console.log('isBalanced "(()":', isBalanced('(()'));        // false (unclosed)

// ------------------------------ 2.9 Infix to Postfix ------------------------------
// [ADVANCED] Shunting-yard style algorithm using an operator stack.
// Infix:   3 + 4 * 2
// Postfix: 3 4 2 * +      (operands first, operators after)
//
// ASCII DIAGRAM of the operator stack while scanning "3+4*2"
//   token 3 -> output: 3                 opStack: (empty)
//   token + -> output: 3                 opStack: +
//   token 4 -> output: 3 4               opStack: +
//   token * -> output: 3 4   (+ has lower prec, stays) opStack: + *
//   token 2 -> output: 3 4 2             opStack: + *
//   end     -> pop all: output: 3 4 2 * +
//
// INTERVIEW: shows you understand OPERATOR PRECEDENCE parsing —
// foundational to how calculators/compilers turn expressions into
// something a stack-based evaluator can run.
function infixToPostfix(expression) {
  const precedence = { '+': 1, '-': 1, '*': 2, '/': 2, '^': 3 };
  const isRightAssoc = (op) => op === '^';
  const output = [];
  const opStack = [];

  const tokens = expression.match(/\d+(\.\d+)?|[A-Za-z]+|[+\-*/^()]/g) || [];

  for (const token of tokens) {
    if (!isNaN(parseFloat(token)) || /^[A-Za-z]+$/.test(token)) {
      output.push(token); // operand (number or identifier) -> straight to output
    } else if (token === '(') {
      opStack.push(token);
    } else if (token === ')') {
      while (opStack.length && opStack[opStack.length - 1] !== '(') {
        output.push(opStack.pop());
      }
      opStack.pop(); // discard the matching '('
    } else {
      // operator: pop while stack top has >= precedence (unless right-assoc)
      while (
        opStack.length &&
        opStack[opStack.length - 1] !== '(' &&
        (precedence[opStack[opStack.length - 1]] > precedence[token] ||
          (precedence[opStack[opStack.length - 1]] === precedence[token] &&
            !isRightAssoc(token)))
      ) {
        output.push(opStack.pop());
      }
      opStack.push(token);
    }
  }
  while (opStack.length) output.push(opStack.pop());

  return output.join(' ');
}

console.log('infixToPostfix "A+B*C":', infixToPostfix('A+B*C'));       // "A B C * +"
console.log('infixToPostfix "3+4*2":', infixToPostfix('3+4*2'));       // "3 4 2 * +"
console.log('infixToPostfix "(3+4)*2":', infixToPostfix('(3+4)*2'));   // "3 4 + 2 *"
// GOTCHA: this tokenizer treats multi-letter runs ("ABC") as ONE
// identifier token, not three separate single-letter operands.

// ------------------------------ 2.10 Evaluate Postfix ------------------------------
// [INTERMEDIATE] Scan left to right: push numbers; on an operator,
// pop the top TWO operands, apply the operator, push the result back.
//
// ASCII DIAGRAM for postfix "3 4 2 * +"
//   token 3 -> push        stack: [3]
//   token 4 -> push        stack: [3, 4]
//   token 2 -> push        stack: [3, 4, 2]
//   token * -> pop 2,4 -> 4*2=8, push  stack: [3, 8]
//   token + -> pop 8,3 -> 3+8=11, push stack: [11]
//   result = 11
//
// INTERVIEW: pair this with infixToPostfix to show a full pipeline:
// human-readable infix -> postfix -> evaluated result.
function evaluatePostfix(postfix) {
  const stack = [];
  const ops = {
    '+': (a, b) => a + b,
    '-': (a, b) => a - b,
    '*': (a, b) => a * b,
    '/': (a, b) => a / b,
    '^': (a, b) => a ** b,
  };

  for (const token of postfix.split(' ')) {
    if (token in ops) {
      const b = stack.pop(); // GOTCHA: order matters! b was pushed LAST
      const a = stack.pop(); // a was pushed before b
      stack.push(ops[token](a, b)); // a OP b, not b OP a
    } else {
      stack.push(Number(token));
    }
  }
  return stack.pop();
}

console.log('evaluatePostfix "3 4 2 * +":', evaluatePostfix('3 4 2 * +'));                 // 11
console.log('evaluatePostfix "5 1 2 + 4 * + 3 -":', evaluatePostfix('5 1 2 + 4 * + 3 -'));  // 14

// ------------------------------ 2.11 Next Greater Element ------------------------------
// [ADVANCED] For each element, find the first element to its right
// that is strictly greater. Naive approach is O(n^2). A "monotonic
// stack" solves it in O(n): scan right-to-left, keeping the stack
// strictly decreasing from the top down.
//
// ASCII DIAGRAM for [4, 5, 2, 10, 8]  (scanning right -> left)
//   i=8:  stack=[]        -> NGE(8)=-1   push 8   stack:[8]
//   i=10: pop 8 (<=10)    -> NGE(10)=-1  push 10  stack:[10]
//   i=2:  top=10 (>2)     -> NGE(2)=10   push 2   stack:[10,2]
//   i=5:  pop 2 (<=5)     -> top=10(>5)  -> NGE(5)=10 push5 stack:[10,5]
//   i=4:  top=5 (>4)      -> NGE(4)=5    push 4   stack:[10,5,4]
//   result (in original order): [5, 10, 10, -1, -1]
//
// INTERVIEW: the "monotonic stack" pattern also solves Largest
// Rectangle in Histogram, Daily Temperatures, and Trapping Rain
// Water variants — recognize the pattern, not just this problem.
function nextGreaterElement(nums) {
  const result = new Array(nums.length).fill(-1);
  const stack = []; // holds INDICES, kept monotonically decreasing in value

  for (let i = nums.length - 1; i >= 0; i--) {
    while (stack.length && nums[stack[stack.length - 1]] <= nums[i]) {
      stack.pop(); // discard indices that can never be an answer again
    }
    if (stack.length) result[i] = nums[stack[stack.length - 1]];
    stack.push(i);
  }
  return result;
}

console.log('nextGreaterElement [4,5,2,10,8]:', nextGreaterElement([4, 5, 2, 10, 8])); // [5,10,10,-1,-1]


// ============================================================
// STACK APPLICATIONS [INTERMEDIATE]
// ============================================================

// ------------------------------ 2.12 Undo/Redo Manager ------------------------------
// [INTERMEDIATE] Two stacks: `undoStack` holds past states,
// `redoStack` holds states you've undone (so redo can restore them).
// Every NEW action clears redoStack — you can't redo into a branch
// that no longer exists once you've done something new.
//
// ASCII DIAGRAM
//   do(A) do(B) do(C):  undo=[A,B,C]     redo=[]
//   undo():             undo=[A,B]       redo=[C]
//   undo():             undo=[A]         redo=[C,B]
//   redo():             undo=[A,B]       redo=[C]
//   do(D):               undo=[A,B,D]    redo=[]   <- cleared!
//
// INTERVIEW: "design an undo/redo feature" is a common systems /
// practical-coding question — the two-stack pattern is the answer.
class UndoRedoManager {
  constructor(initialState) {
    this.undoStack = [];
    this.redoStack = [];
    this.state = initialState;
  }

  do(newState) {
    this.undoStack.push(this.state);
    this.state = newState;
    this.redoStack.length = 0; // new action invalidates redo history
    return this.state;
  }

  undo() {
    if (this.undoStack.length === 0) return this.state;
    this.redoStack.push(this.state);
    this.state = this.undoStack.pop();
    return this.state;
  }

  redo() {
    if (this.redoStack.length === 0) return this.state;
    this.undoStack.push(this.state);
    this.state = this.redoStack.pop();
    return this.state;
  }

  current() {
    return this.state;
  }
}

const editor = new UndoRedoManager('');
editor.do('Hello');
editor.do('Hello World');
editor.do('Hello World!');
console.log('UndoRedo current:', editor.current()); // "Hello World!"
console.log('UndoRedo undo:', editor.undo());        // "Hello World"
console.log('UndoRedo undo:', editor.undo());        // "Hello"
console.log('UndoRedo redo:', editor.redo());         // "Hello World"

// ------------------------------ 2.13 Browser History ------------------------------
// [INTERMEDIATE] Same two-stack pattern as undo/redo, applied to URLs.
class BrowserHistory {
  constructor(homepage) {
    this.backStack = [];
    this.forwardStack = [];
    this.currentUrl = homepage;
  }

  visit(url) {
    this.backStack.push(this.currentUrl);
    this.currentUrl = url;
    this.forwardStack.length = 0; // visiting a new page kills "forward"
  }

  back() {
    if (this.backStack.length === 0) return this.currentUrl;
    this.forwardStack.push(this.currentUrl);
    this.currentUrl = this.backStack.pop();
    return this.currentUrl;
  }

  forward() {
    if (this.forwardStack.length === 0) return this.currentUrl;
    this.backStack.push(this.currentUrl);
    this.currentUrl = this.forwardStack.pop();
    return this.currentUrl;
  }
}

const browser = new BrowserHistory('home.com');
browser.visit('news.com');
browser.visit('sports.com');
console.log('Browser back:', browser.back());       // "news.com"
console.log('Browser back:', browser.back());       // "home.com"
console.log('Browser forward:', browser.forward()); // "news.com"

// ------------------------------ 2.14 Call Stack Visualization ------------------------------
// [INTERMEDIATE] The JS engine itself uses a call stack for every
// function call. This simulates it explicitly so you can SEE what
// recursion does to the stack, and why deep recursion causes
// "Maximum call stack size exceeded" (a real stack overflow).
//
// ASCII DIAGRAM for factorial(3)
//   call factorial(3)           stack: [f(3)]
//     call factorial(2)         stack: [f(3), f(2)]
//       call factorial(1)       stack: [f(3), f(2), f(1)]
//       return 1                stack: [f(3), f(2)]      (f(1) popped)
//     return 2*1=2              stack: [f(3)]             (f(2) popped)
//   return 3*2=3                stack: []                 (f(3) popped)
//
// INTERVIEW: explain WHY recursion needs a base case — without
// one, you push forever until you exhaust the (finite!) real call
// stack and get a RangeError.
function factorialWithTrace(n, callStack = []) {
  callStack.push(`factorial(${n})`);
  console.log('CALL STACK:', callStack.join(' -> '));

  if (n <= 1) {
    callStack.pop();
    return 1;
  }
  const result = n * factorialWithTrace(n - 1, callStack);
  callStack.pop();
  return result;
}

console.log('factorialWithTrace(4):', factorialWithTrace(4)); // 24


// ============================================================
// STACK GOTCHAS & PITFALLS
// ============================================================
// 1. shift()/unshift() are NOT stack operations — they're O(n)
//    because every remaining element must be re-indexed. Always
//    use push()/pop() (the END of the array) for O(1) stack ops.
//
// 2. pop() on an empty array returns `undefined`, it does NOT
//    throw. Always check isEmpty() first if `undefined` is a
//    valid stored value and you need to distinguish "empty" from
//    "top value is undefined".
//
// 3. Popping to "peek" (i.e. pop() then push() the value back) is
//    a common beginner mistake — it's needless extra work. Always
//    implement a dedicated peek()/top() that only reads array[length - 1].
//
// 4. Object/array references pushed onto a stack are NOT cloned —
//    mutating an object after pushing it mutates the version
//    stored in the stack too. Clone (structuredClone, spread) if
//    you need independent snapshots (critical for undo/redo!).
//
// 5. MinStack / monotonic-stack bugs almost always come from
//    letting two "parallel" stacks fall out of sync — always
//    push/pop them together, in the same operation.
//
// 6. Deep recursion will overflow the REAL call stack
//    ("Maximum call stack size exceeded") long before you run out
//    of heap memory — convert to an explicit iterative stack to
//    process deep/unbounded structures.
//
// 7. WeakMap-based privacy (StackWeakMap) is NOT truly unbreakable
//    like class #fields — anyone with a reference to the WeakMap
//    itself can read/write the data.
//
// 8. `stack.length = 0` and `stack = []` are both valid "clear"
//    strategies but differ: the former clears IN PLACE (any other
//    reference to the same array sees the change too); the latter
//    only rebinds the local variable.


// ============================================================
// STACK INTERVIEW TIPS SUMMARY
// ============================================================
// - Know Big-O cold: push/pop/peek/isEmpty/size = O(1); search = O(n).
// - Recognize "monotonic stack" as the pattern behind Next Greater
//   Element, Daily Temperatures, Largest Rectangle in Histogram.
// - Balanced Parentheses is the single most common stack question —
//   be able to write isBalanced() from memory in under 2 minutes.
// - MinStack (getMin O(1)) tests whether you think of "auxiliary
//   data structures kept in lockstep" as a general technique.
// - Infix->Postfix->Evaluate is a 3-part pipeline that shows you
//   understand both parsing (operator precedence) and evaluation.
// - Be ready to implement a stack 3 ways: array-backed, linked-list
//   backed, and with genuine privacy (closures/#fields/WeakMap) —
//   and explain the tradeoffs of each.
// - Always mention the real call stack connection: recursion IS a
//   stack, and stack overflow is a literal, not just a metaphor.
