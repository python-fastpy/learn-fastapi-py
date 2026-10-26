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
    // TRACE push(1) -> push(20) -> push(30) -> size() -> pop() -> print() -> peek()
    //   isEmpty()  items = []            returns true
    //   push(1)    items = [1]           top -> 1   (returns undefined)
    //   push(20)   items = [1, 20]       top -> 20
    //   push(30)   items = [1, 20, 30]   top -> 30
    //   size()     length 3              returns 3
    //   pop()      items = [1, 20]       returns 30
    //   print()    logs "1,20"
    //   peek()     items[2 - 1]          returns 20
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
    // TRACE push(1) -> push(2)
    //   start     items = {}                 head = 0
    //   push(1)   items[0] = 1  -> { 0: 1 }        head = 1
    //   push(2)   items[1] = 2  -> { 0: 1, 1: 2 }  head = 2
    pop() {
        if (this.head === 0) return undefined;
        const item = this.items[this.head - 1];
        delete this.items[this.head - 1];
        this.head--;
        return item;
    }
    // TRACE pop() x3   start items = { 0: 1, 1: 2 }  head = 2
    //   pop()  item = items[1] = 2, delete key 1  -> { 0: 1 }  head = 1  returns 2
    //   pop()  item = items[0] = 1, delete key 0  -> {}        head = 0  returns 1
    //   pop()  head === 0                                                returns undefined
    peek() { return this.items[this.head - 1]; }
    size() { return this.head; }
    isEmpty() { return this.head === 0; }
    print() { console.log(this.items); }
    // TRACE (demo) after push(1), push(2): items = { 0: 1, 1: 2 }  head = 2
    //   print()    logs { '0': 1, '1': 2 }
    //   pop()      returns 2       items = { 0: 1 }  head = 1
    //   peek()     items[1 - 1]    returns 1
    //   size()     returns head    1
    //   isEmpty()  head === 0      false
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
  // TRACE push(100) -> push(200) -> push(300)
  //   push(100)  items[0] = 100, top 0 -> 1   items = [100]
  //   push(200)  items[1] = 200, top 1 -> 2   items = [100, 200]
  //   push(300)  items[2] = 300, top 2 -> 3   items = [100, 200, 300]

  this.pop = function () {
    return items[--top]; // decrement FIRST, then read that slot
  };
  // TRACE pop()   start items = [100, 200, 300]  top = 3
  //   --top      top 3 -> 2
  //   items[2]   returns 300
  //   items is STILL [100, 200, 300] — slot 2 is just "free" now (top = 2)

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
  // TRACE (demo) after pop():  items = [100, 200, 300]  top = 2
  //   peek()     items[2 - 1]   returns 200
  //   isEmpty()  2 === 0        false
  //   size()     returns top    2
  //   clear()    top = 0        items still [100, 200, 300] (old slots ignored)
  //   isEmpty()  0 === 0        true
  //   push(999)  items[0] = 999 -> [999, 200, 300]  top = 1  (overwrites old slot)
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
    // TRACE push(100) -> push(200) -> push(300) -> pop() -> ... -> clear()
    //   (items lives in the closure — the instance only holds the methods)
    //   push x3    items = [100, 200, 300]
    //   pop()      items = [100, 200]   returns 300
    //   peek()     returns 200    isEmpty() false    size() 2
    //   clear()    items.length = 0 -> items = []    isEmpty() true
    //   stackIIFE.items -> undefined (no such property on the instance)
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
  // TRACE push(100) -> push(200) -> push(300) -> pop() -> ... -> clear()
  //   new        WeakMap: { stackWeakMap => [] }
  //   push x3    WeakMap: { stackWeakMap => [100, 200, 300] }
  //   pop()      WeakMap: { stackWeakMap => [100, 200] }   returns 300
  //   peek()     returns 200    isEmpty() false    size() 2
  //   clear()    WeakMap.set(this, [])  -> { stackWeakMap => [] }  (NEW array)
  //   isEmpty()  true
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
  // TRACE push(10) -> push(20) -> push(30)
  //   start     top -> null                              length 0
  //   push(10)  top -> [10] -> null                      length 1
  //   push(20)  top -> [20] -> [10] -> null              length 2
  //   push(30)  top -> [30] -> [20] -> [10] -> null      length 3

  pop() {
    if (this.isEmpty()) return undefined;
    const { value } = this.top;
    this.top = this.top.next; // unlink head
    this.length--;
    return value;
  }
  // TRACE pop()   start top -> [30] -> [20] -> [10] -> null  length 3
  //   value = top.value = 30
  //   top = top.next     top -> [20] -> [10] -> null  length 2
  //   returns 30         ([30] is now unreferenced -> garbage collected)

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
  // TRACE after pop():  top -> [20] -> [10] -> null  length 2
  //   peek()     top.value      returns 20
  //   isEmpty()  top === null   false
  //   size()     returns 2
  //   clear()    top -> null    length 0
  //   peek() -> undefined   isEmpty() -> true   pop() -> undefined

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
  // TRACE toArray()   top -> [30] -> [20] -> [10] -> null
  //   node=[30]  out = [30]
  //   node=[20]  out = [30, 20]
  //   node=[10]  out = [30, 20, 10]
  //   node=null  loop ends  -> returns [30, 20, 10]
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
  // TRACE push(5) -> push(3) -> push(7) -> push(2)
  //   value | currentMin        | main          | minTrack
  //   5     | (empty) -> 5      | [5]           | [5]
  //   3     | min(3, 5) = 3     | [5, 3]        | [5, 3]
  //   7     | min(7, 3) = 3     | [5, 3, 7]     | [5, 3, 3]
  //   2     | min(2, 3) = 2     | [5, 3, 7, 2]  | [5, 3, 3, 2]

  pop() {
    this.minTrack.pop(); // keep both stacks in lockstep
    return this.main.pop();
  }
  // TRACE pop() -> pop()   start main = [5, 3, 7, 2]  minTrack = [5, 3, 3, 2]
  //   pop()  main = [5, 3, 7]  minTrack = [5, 3, 3]  returns 2  (min now 3)
  //   pop()  main = [5, 3]     minTrack = [5, 3]     returns 7  (min still 3)

  top() {
    return this.main[this.main.length - 1];
  }

  getMin() {
    return this.minTrack[this.minTrack.length - 1];
  }

  isEmpty() {
    return this.main.length === 0;
  }
  // TRACE (demo)  main = [5, 3, 7, 2]  minTrack = [5, 3, 3, 2]
  //   getMin()  minTrack top   returns 2
  //   pop()     main = [5, 3, 7]  minTrack = [5, 3, 3]
  //   getMin()  minTrack top   returns 3
  //   top()     main top       returns 7
  //   isEmpty() length 3       false
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
// TRACE isBalanced("{[(])}")
//   char | action                     | stack
//   {    | opener -> push             | {
//   [    | opener -> push             | { [
//   (    | opener -> push             | { [ (
//   ]    | pop '(' !== '[' -> mismatch | { [
//   -> returns false (stops early)
// TRACE isBalanced("(()")
//   (    | push                       | (
//   (    | push                       | ( (
//   )    | pop '(' === '(' ok         | (
//   end  | stack.length 1 !== 0  -> returns false

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
// TRACE infixToPostfix("(3+4)*2")   tokens: ( 3 + 4 ) * 2
//   token | action                          | opStack | output
//   (     | push                            | (       |
//   3     | operand -> output               | (       | 3
//   +     | top is '(' -> no pop; push      | ( +     | 3
//   4     | operand -> output               | ( +     | 3 4
//   )     | pop until '(' ; discard '('     |         | 3 4 +
//   *     | stack empty -> push             | *       | 3 4 +
//   2     | operand -> output               | *       | 3 4 + 2
//   end   | pop all                         |         | 3 4 + 2 *
//   -> returns "3 4 + 2 *"

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
// TRACE evaluatePostfix("5 1 2 + 4 * + 3 -")
//   token | action                   | stack
//   5     | push                     | [5]
//   1     | push                     | [5, 1]
//   2     | push                     | [5, 1, 2]
//   +     | b=2, a=1 -> 1 + 2 = 3    | [5, 3]
//   4     | push                     | [5, 3, 4]
//   *     | b=4, a=3 -> 3 * 4 = 12   | [5, 12]
//   +     | b=12, a=5 -> 5 + 12 = 17 | [17]
//   3     | push                     | [17, 3]
//   -     | b=3, a=17 -> 17 - 3 = 14 | [14]
//   -> returns 14

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
// TRACE nextGreaterElement([4, 5, 2, 10, 8])   (stack holds INDICES)
//   i | nums[i] | popped idx | stack (idx) | result
//   4 | 8       | -          | [4]         | [-1, -1, -1, -1, -1]
//   3 | 10      | 4 (8<=10)  | [3]         | [-1, -1, -1, -1, -1]
//   2 | 2       | -          | [3, 2]      | [-1, -1, 10, -1, -1]
//   1 | 5       | 2 (2<=5)   | [3, 1]      | [-1, 10, 10, -1, -1]
//   0 | 4       | -          | [3, 1, 0]   | [5, 10, 10, -1, -1]
//   -> returns [5, 10, 10, -1, -1]

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
  // TRACE new UndoRedoManager('') -> do('Hello') -> do('Hello World') -> do('Hello World!')
  //   call                | undoStack                         | state          | redo
  //   do('Hello')         | ['']                              | 'Hello'        | []
  //   do('Hello World')   | ['', 'Hello']                     | 'Hello World'  | []
  //   do('Hello World!')  | ['', 'Hello', 'Hello World']      | 'Hello World!' | []

  undo() {
    if (this.undoStack.length === 0) return this.state;
    this.redoStack.push(this.state);
    this.state = this.undoStack.pop();
    return this.state;
  }
  // TRACE undo() -> undo()   start undo = ['', 'Hello', 'Hello World']  state = 'Hello World!'
  //   undo()  redo = ['Hello World!']                 undo = ['', 'Hello']  returns 'Hello World'
  //   undo()  redo = ['Hello World!', 'Hello World']  undo = ['']           returns 'Hello'

  redo() {
    if (this.redoStack.length === 0) return this.state;
    this.undoStack.push(this.state);
    this.state = this.redoStack.pop();
    return this.state;
  }
  // TRACE redo()   start undo = ['']  state = 'Hello'  redo = ['Hello World!', 'Hello World']
  //   push 'Hello' onto undo     undo = ['', 'Hello']
  //   pop redo -> state          redo = ['Hello World!']  returns 'Hello World'
  //   (a do('Hi') now would push 'Hello World' to undo and empty redo -> [])

  current() {
    return this.state;
  }
  // TRACE current()  after the 3 do() calls  -> returns 'Hello World!' (no stack change)
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
  // TRACE new BrowserHistory('home.com') -> visit('news.com') -> visit('sports.com')
  //   visit('news.com')    back = ['home.com']               current = 'news.com'    fwd = []
  //   visit('sports.com')  back = ['home.com', 'news.com']   current = 'sports.com'  fwd = []

  back() {
    if (this.backStack.length === 0) return this.currentUrl;
    this.forwardStack.push(this.currentUrl);
    this.currentUrl = this.backStack.pop();
    return this.currentUrl;
  }
  // TRACE back() x3   start back = ['home.com', 'news.com']  current = 'sports.com'
  //   back()  back = ['home.com']  fwd = ['sports.com']              returns 'news.com'
  //   back()  back = []            fwd = ['sports.com', 'news.com']  returns 'home.com'
  //   back()  back is empty -> nothing changes                       returns 'home.com'

  forward() {
    if (this.forwardStack.length === 0) return this.currentUrl;
    this.backStack.push(this.currentUrl);
    this.currentUrl = this.forwardStack.pop();
    return this.currentUrl;
  }
  // TRACE forward()   start back = []  current = 'home.com'  fwd = ['sports.com', 'news.com']
  //   push 'home.com' onto back   back = ['home.com']
  //   pop fwd -> current          fwd = ['sports.com']   returns 'news.com'
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
//   return 3*2=6                stack: []                 (f(3) popped)
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
// TRACE factorialWithTrace(4)
//   push f(4)   callStack = [f(4)]
//   push f(3)   callStack = [f(4), f(3)]
//   push f(2)   callStack = [f(4), f(3), f(2)]
//   push f(1)   callStack = [f(4), f(3), f(2), f(1)]   n <= 1 -> pop, return 1
//   f(2): 2 * 1 = 2    pop  callStack = [f(4), f(3)]
//   f(3): 3 * 2 = 6    pop  callStack = [f(4)]
//   f(4): 4 * 6 = 24   pop  callStack = []          -> returns 24

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
