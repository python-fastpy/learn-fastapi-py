/* ============================================================================
 * DATA STRUCTURES — THE ULTIMATE JAVASCRIPT QUICK REFERENCE
 * ============================================================================
 * Refs:
 *  https://dev.to/prnvbirajdar/list-of-visual-tools-to-help-with-data-structures-and-algorithms-4nb2
 *  https://github.com/gopinav/JavaScript-Data-Structures-Tutorial
 *
 * TABLE OF CONTENTS
 * --------------------------------------------------------------------------
 *  MASTER BIG-O COMPARISON TABLE
 *  WHEN-TO-USE DECISION TREE
 *
 *  PART 1  BUILT-IN DS              [BASIC]         Array, Object, Set, Map
 *
 *  PART 2  STACKS & QUEUES          [BASIC/INTERM/ADV]
 *          --- Stack Implementations ---
 *          2.1  Stack (ES6 class, array-backed)                 [BASIC]
 *          2.2  StackObj (object-backed, head pointer)          [BASIC]
 *          2.3  StackIndex (function-based, manual index)       [BASIC]
 *          2.4  StackIIFE (closure-based privacy)               [BASIC]
 *          2.5  StackWeakMap (WeakMap true privacy)             [BASIC]
 *          2.6  StackLinkedList (singly linked list)            [INTERMEDIATE]
 *          2.7  MinStack (O(1) getMin)                          [INTERMEDIATE]
 *          --- Classic Stack Problems ---
 *          2.8  Balanced Parentheses (isBalanced)               [INTERMEDIATE]
 *          2.9  Infix to Postfix                                [ADVANCED]
 *          2.10 Evaluate Postfix                                [INTERMEDIATE]
 *          2.11 Next Greater Element (monotonic stack)          [ADVANCED]
 *          --- Stack Applications ---
 *          2.12 Undo/Redo Manager                               [INTERMEDIATE]
 *          2.13 Browser History                                 [INTERMEDIATE]
 *          2.14 Call Stack Visualization                        [INTERMEDIATE]
 *          --- Stack Gotchas & Interview Tips ---
 *          --- Queues ---
 *          Queue, QueueObj, CircularQueue
 *          --- Heaps ---
 *          MinHeap, PriorityQueue
 *          Stack vs Queue Comparison Table
 *
 *  PART 3  LINKED LISTS             [INTERMEDIATE]  SLL, SLL+Tail, Stack/Queue via LL, DLL
 *  PART 4  HASH TABLES              [INTERMEDIATE]  HashTable (chaining)
 *  PART 5  TREES                    [INTERM/ADV]    BinarySearchTree, Trie
 *  PART 6  GRAPHS                   [ADVANCED]      Graph (adjacency list), BFS, DFS
 *  PART 7  ADVANCED                 [ADVANCED]      LRUCache
 * ==========================================================================*/

// ============================================================
// MASTER BIG-O COMPARISON TABLE
// ============================================================
/*
 ┌───────────────────────┬───────────┬───────────┬───────────┬───────────┐
 │ Data Structure         │ Access    │ Search    │ Insert    │ Delete    │
 ├───────────────────────┼───────────┼───────────┼───────────┼───────────┤
 │ Array                  │ O(1)      │ O(n)      │ O(n)*     │ O(n)*     │
 │ Object                 │ O(1)      │ O(n)      │ O(1)      │ O(1)      │
 │ Set / Map              │ O(1)      │ O(1)      │ O(1)      │ O(1)      │
 │ Stack (array/LL)       │ O(n)      │ O(n)      │ O(1)      │ O(1)      │
 │ Queue (obj/LL)         │ O(n)      │ O(n)      │ O(1)      │ O(1)      │
 │ Circular Queue         │ O(n)      │ O(n)      │ O(1)      │ O(1)      │
 │ Singly Linked List     │ O(n)      │ O(n)      │ O(1)**    │ O(1)**    │
 │ Doubly Linked List     │ O(n)      │ O(n)      │ O(1)**    │ O(1)**    │
 │ Hash Table             │ -         │ O(1) avg  │ O(1) avg  │ O(1) avg  │
 │ Binary Search Tree     │ O(log n)† │ O(log n)† │ O(log n)† │ O(log n)† │
 │ Trie (per word len k)  │ O(k)      │ O(k)      │ O(k)      │ O(k)      │
 │ Binary Min-Heap        │ O(1) min  │ O(n)      │ O(log n)  │ O(log n)  │
 │ Graph (adj. list) BFS  │ -         │ O(V+E)    │ O(1)      │ O(V+E)    │
 └───────────────────────┴───────────┴───────────┴───────────┴───────────┘
  *  end of array O(1) (push/pop); front/middle O(n) (shift/unshift/splice)
  ** only true at head/tail with a pointer; middle insert/delete is O(n) (traversal)
  †  average case; worst case O(n) for an unbalanced/skewed BST
*/

// ============================================================
// WHEN-TO-USE DECISION TREE
// ============================================================
/*
 Need to store data...
 │
 ├─ ...as key/value pairs?
 │    ├─ Keys are always strings & need object literal features → Object
 │    ├─ Keys can be any type, need guaranteed insertion order/size → Map
 │    └─ Need O(1) avg lookup for a custom key → HashTable
 │
 ├─ ...as a unique collection (no duplicates)? → Set
 │
 ├─ ...as an ordered, index-accessed collection?
 │    ├─ Mostly read/access by index, occasional end push/pop → Array
 │    └─ Frequent insert/delete at head or middle → LinkedList / DoublyLinkedList
 │
 ├─ ...with LIFO access (undo, call stack, backtracking)? → Stack
 ├─ ...with FIFO access (task scheduling, BFS)? → Queue / CircularQueue (fixed size)
 ├─ ...and always need the min/max quickly (scheduling, Dijkstra)? → MinHeap / PriorityQueue
 │
 ├─ ...hierarchically with fast range/ordered search? → BinarySearchTree
 ├─ ...as strings needing prefix search (autocomplete)? → Trie
 ├─ ...as entities + relationships (social graph, routes)? → Graph (BFS/DFS)
 └─ ...with a fixed capacity + evict-oldest-unused policy? → LRUCache (Map + doubly-linked-list semantics)
*/


// ============================================================
// PART 1: BUILT-IN DATA STRUCTURES [BASIC]
// ============================================================

// ------------------------------ Array ------------------------------
// [BASIC]
// - Holds a collection of mixed-type values, resizable, zero-indexed,
//   insertion order preserved, iterable (for..of).
//
// ASCII diagram:
//   index:  0    1    2    3
//         ┌────┬────┬────┬────┐
//   arr = │ 1  │ 2  │ 3  │"sh"│
//         └────┴────┴────┴────┘
//   push/pop -> right end (O(1)) | unshift/shift -> left end (O(n), re-index all)

const arr = [1, 2, 3, "shubam"];
arr.push(4);      // add at end        O(1)
arr.unshift(0);    // add at front      O(n)
arr.pop();         // remove from end   O(1)
arr.shift();       // remove from front O(n)
console.log(arr[0]);
for (const item of arr) console.log(item);
// map, filter, reduce, concat, slice, splice — all O(n)

// Array Big-O
// access O(1) | search O(n) | push/pop O(1) | shift/unshift/concat/slice/splice O(n)
// forEach/map/filter/reduce O(n)
//
// GOTCHAS:
// - splice() mutates the array in place; slice() does not.
// - Sparse arrays (delete arr[i]) leave holes — length doesn't shrink.
// - typeof [] === 'object'; use Array.isArray() to test for arrays.
// INTERVIEW: know push/pop vs shift/unshift complexity cold — it's asked constantly.

// ------------------------------ Object ------------------------------
// [BASIC]
// - Unordered key/value store; keys are string|symbol, values any type.
// - Not iterable directly (no for..of); use Object.keys/values/entries.
//
// ASCII diagram:
//   obj ──▶ { name: "shubham", age: 25, "key-three": true, sayMyName: fn }
//            (hash map under the hood — key hashed to an internal slot)

const obj = {
    name: "shubham",
    age: 25,
    "key-three": true,
    sayMyName: function () {
        console.log(this.name);
    },
};
obj.hobby = "footbal";
delete obj.hobby;
console.log(obj.name, obj.age, obj["age"], obj["key-three"], obj);
obj.sayMyName();
// Object.keys(), Object.values(), Object.entries()

// Object Big-O
// insert O(1) | remove O(1) | access O(1) | search O(n)
// Object.keys/values/entries O(n)
//
// GOTCHAS:
// - Object has a prototype chain; unguarded keys (e.g. "constructor") can collide.
// - Use Object.create(null) or a Map to avoid prototype pollution.
// INTERVIEW: "Object vs Map" is a classic — see comparison table below.

// ------------------------------ Set ------------------------------
// [BASIC]
// - Collection of UNIQUE values, mixed types, no guaranteed insertion order
//   contract (though V8 preserves it), iterable.
//
// ASCII diagram:
//   Set → ( 1 )  ( 2 )  ( 3 )  ( 4 )     duplicates are silently ignored

const set = new Set([1, 2, 3]);
set.add(4);
set.add(4); // ignored, already present
console.log(set.has(4));
set.delete(3);
console.log(set.size);
set.clear();
for (const item of set) console.log(item);
console.log(set);

// Set vs Array: Set forbids duplicates; search/delete faster (O(1) avg) than Array O(n).
// GOTCHAS: Set.has() uses SameValueZero equality (NaN === NaN is true here, unlike ===).
// INTERVIEW: "dedupe an array" -> [...new Set(arr)]

// ------------------------------ Map ------------------------------
// [BASIC]
// - Ordered key/value store, ANY type as key, iterable, has a .size property.
//
// ASCII diagram:
//   Map → ['a' -> 1] -> ['b' -> 2] -> ['c' -> 3]   (insertion order preserved)

const map = new Map([["a", 1], ["b", 2]]);
map.set("c", 3);
console.log(map.has("a"));
map.delete("c");
console.log(map.size);
for (const [key, value] of map) console.log(key, value);

// COMPARISON TABLE — Object vs Map
// ┌───────────────────────┬────────────────────────┬───────────────────────┐
// │ Feature                │ Object                 │ Map                   │
// ├───────────────────────┼────────────────────────┼───────────────────────┤
// │ Key types              │ string | symbol        │ any value             │
// │ Order guarantee        │ mostly, w/ int-key quirk│ insertion order       │
// │ Size                    │ manual (Object.keys)   │ .size property        │
// │ Iterable                │ no (need Object.entries)│ yes (for..of)        │
// │ Prototype collisions    │ possible                │ none                  │
// │ Perf for freq add/remove│ optimized less          │ better                │
// │ JSON.stringify support  │ yes                     │ no (needs conversion) │
// └───────────────────────┴────────────────────────┴───────────────────────┘
// INTERVIEW: mention Map avoids prototype pollution and is faster for
// frequent additions/removals of keys.


// ============================================================
// PART 2: STACKS & QUEUES [BASIC / INTERMEDIATE / ADVANCED]
// ============================================================
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


// ------------------------------ Queue ------------------------------
// [BASIC] FIFO — First In First Out.
//
// ASCII diagram (enqueue 10,20,30 — dequeue removes from front):
//   front                          rear
//    ┌────┐   ┌────┐   ┌────┐
//    │ 10 │ ─ │ 20 │ ─ │ 30 │   <- enqueue adds here
//    └────┘   └────┘   └────┘
//   dequeue removes here ^
// Usage: printers, CPU task scheduling, JS callback queue.
// Ops: enqueue, dequeue, peek, isEmpty, size, print

class Queue {
    constructor() {
        this.items = [];
    }
    enqueue(element) { this.items.push(element); }
    dequeue() { return this.items.shift(); }
    isEmpty() { return this.items.length === 0; }
    peek() { return this.isEmpty() ? null : this.items[0]; }
    size() { return this.items.length; }
    print() { console.log(this.items.toString()); }
}
let queue = new Queue();
console.log(queue.isEmpty());
queue.enqueue(10);
queue.enqueue(20);
queue.enqueue(30);
console.log(queue.size());
queue.print();
console.log(queue.dequeue());
console.log(queue.peek());
// GOTCHAS: dequeue() uses Array.shift() which is O(n) (re-indexes every element).
// For high-throughput queues prefer QueueObj or a linked-list queue below.

// -------------------- Queue via Object (QueueObj) -------------------
// [INTERMEDIATE] optimized: avoids shift()'s O(n) cost using front/rear pointers.
class QueueObj {
    constructor() {
        this.items = {};
        this.rear = 0;
        this.front = 0;
    }
    enqueue(element) {
        this.items[this.rear] = element;
        this.rear++;
    }
    dequeue() {
        const item = this.items[this.front];
        delete this.items[this.front];
        this.front++;
        return item;
    }
    isEmpty() { return this.rear - this.front === 0; }
    peek() { return this.items[this.front]; }
    size() { return this.rear - this.front; }
    print() { console.log(this.items); }
}
let queueobj = new QueueObj();
console.log(queueobj.isEmpty());
queueobj.enqueue(10);
queueobj.enqueue(20);
queueobj.enqueue(30);
console.log(queueobj.size());
queueobj.print();
console.log(queueobj.dequeue());
console.log(queueobj.peek());
// Big-O: enqueue/dequeue/peek O(1) — the whole point of this version.
// INTERVIEW: "why is array.shift() bad for a queue?" -> O(n) re-index; fix with
// object+pointers (above) or a linked list (Part 3).

// ------------------------------ Circular Queue ------------------------------
// [INTERMEDIATE] Fixed-size ring buffer; wraps around instead of growing.
//
// ASCII diagram (capacity 5, front/rear wrap using modulo):
//        ┌────┬────┬────┬────┬────┐
//        │ 10 │ 20 │ 30 │ 40 │ 50 │   indices 0..4
//        └────┴────┴────┴────┴────┘
//          ▲front                ▲rear
//   after dequeue(): front moves right; after wrap: rear = (rear+1) % capacity
// Usage: clocks, streaming buffers, traffic lights.
// Ops: enqueue, dequeue, isFull, isEmpty, peek, size, print

class CircularQueue {
    constructor(capacity) {
        this.items = new Array(capacity);
        this.capacity = capacity;
        this.currentLength = 0;
        this.rear = -1;
        this.front = -1;
    }
    isFull() { return this.currentLength === this.capacity; }
    isEmpty() { return this.currentLength === 0; }
    enqueue(element) {
        if (this.isFull()) return;
        this.rear = (this.rear + 1) % this.capacity;
        this.items[this.rear] = element;
        this.currentLength += 1;
        if (this.front === -1) this.front = this.rear;
    }
    dequeue() {
        if (this.isEmpty()) return null;
        const item = this.items[this.front];
        this.items[this.front] = null;
        this.front = (this.front + 1) % this.capacity;
        this.currentLength -= 1;
        if (this.isEmpty()) { this.front = -1; this.rear = -1; }
        return item;
    }
    peek() { return this.isEmpty() ? null : this.items[this.front]; }
    print() {
        if (this.isEmpty()) { console.log("queue is empty"); return; }
        let i, str = "";
        for (i = this.front; i !== this.rear; i = (i + 1) % this.capacity) {
            str += this.items[i] + " ";
        }
        str += this.items[i];
        console.log(str);
    }
}
const circularQueue = new CircularQueue(5);
console.log(circularQueue.isEmpty());
circularQueue.enqueue(10);
circularQueue.enqueue(20);
circularQueue.enqueue(30);
circularQueue.enqueue(40);
circularQueue.enqueue(50);
console.log(circularQueue.isFull());
circularQueue.print();
console.log(circularQueue.dequeue());
console.log(circularQueue.peek());
circularQueue.print();
circularQueue.enqueue(100);
circularQueue.print();
// GOTCHAS: distinguishing "full" vs "empty" both look like front===rear —
// that's why we track currentLength explicitly instead of comparing pointers only.

// ------------------------------ MinHeap ------------------------------
// [ADVANCED] Binary heap stored as an array; parent <= both children (min-heap).
// A Priority Queue is typically implemented on top of a heap.
//
// ASCII diagram (array indices as a binary tree):
//                idx0 (root/min)
//               /              \
//            idx1               idx2
//           /    \             /    \
//        idx3    idx4       idx5    idx6
//   parent(i) = (i-1)>>1 | left(i) = 2i+1 | right(i) = 2i+2

class MinHeapDS {
    constructor() { this.heap = []; }
    size() { return this.heap.length; }
    isEmpty() { return this.heap.length === 0; }
    peek() { return this.isEmpty() ? null : this.heap[0]; }

    #parent(i) { return Math.floor((i - 1) / 2); }
    #left(i) { return 2 * i + 1; }
    #right(i) { return 2 * i + 2; }
    #swap(i, j) { [this.heap[i], this.heap[j]] = [this.heap[j], this.heap[i]]; }

    insert(value) {
        this.heap.push(value);
        let i = this.heap.length - 1;
        while (i > 0 && this.heap[i] < this.heap[this.#parent(i)]) {
            this.#swap(i, this.#parent(i));
            i = this.#parent(i);
        }
    }

    extractMin() {
        if (this.isEmpty()) return null;
        const min = this.heap[0];
        const last = this.heap.pop();
        if (this.heap.length > 0) {
            this.heap[0] = last;
            this.#bubbleDown(0);
        }
        return min;
    }

    #bubbleDown(i) {
        const n = this.heap.length;
        while (true) {
            const l = this.#left(i), r = this.#right(i);
            let smallest = i;
            if (l < n && this.heap[l] < this.heap[smallest]) smallest = l;
            if (r < n && this.heap[r] < this.heap[smallest]) smallest = r;
            if (smallest === i) break;
            this.#swap(i, smallest);
            i = smallest;
        }
    }
}
const minHeap = new MinHeapDS();
[5, 3, 8, 1, 9, 2].forEach((n) => minHeap.insert(n));
console.log(minHeap.peek());       // 1
console.log(minHeap.extractMin()); // 1
console.log(minHeap.extractMin()); // 2
// Big-O: insert O(log n) | extractMin O(log n) | peek O(1)
// GOTCHAS: heap is NOT fully sorted — only the root is guaranteed min.
// INTERVIEW: heaps back "Kth largest element", Dijkstra, heap-sort, median-finder.

// ------------------------------ PriorityQueue ------------------------------
// [ADVANCED] Queue where each element has a priority; lowest priority number
// dequeues first. Built on top of MinHeap by comparing {priority, value}.
class PriorityQueue {
    constructor() { this.heap = new MinHeapDS(); this.#wrapComparisons(); }
    #wrapComparisons() {
        this.heap.insert = (entry) => {
            this.heap.heap.push(entry);
            let i = this.heap.heap.length - 1;
            const parent = (idx) => Math.floor((idx - 1) / 2);
            while (i > 0 && this.heap.heap[i].priority < this.heap.heap[parent(i)].priority) {
                [this.heap.heap[i], this.heap.heap[parent(i)]] = [this.heap.heap[parent(i)], this.heap.heap[i]];
                i = parent(i);
            }
        };
    }
    enqueue(value, priority) { this.heap.insert({ value, priority }); }
    dequeue() {
        const min = this.heap.extractMin();
        return min ? min.value : null;
    }
    isEmpty() { return this.heap.isEmpty(); }
}
const pq = new PriorityQueue();
pq.enqueue("low prio task", 5);
pq.enqueue("urgent task", 1);
pq.enqueue("medium task", 3);
console.log(pq.dequeue()); // "urgent task" (priority 1)
console.log(pq.dequeue()); // "medium task"
// Big-O: enqueue O(log n) | dequeue O(log n)
// GOTCHAS: "priority" convention varies — some libs treat HIGHER number as
// higher priority; always confirm the convention (here: lower number = more urgent).
// INTERVIEW: PriorityQueue = classic building block for Dijkstra's / A* / task schedulers.

// COMPARISON TABLE — Stack vs Queue
// ┌───────────────┬───────────────────────┬───────────────────────┐
// │                │ Stack (LIFO)           │ Queue (FIFO)           │
// ├───────────────┼───────────────────────┼───────────────────────┤
// │ Add            │ push (top)             │ enqueue (rear)         │
// │ Remove         │ pop (top)              │ dequeue (front)        │
// │ Use cases       │ undo, call stack, DFS  │ scheduling, BFS, print │
// │ Array pitfall   │ none (push/pop O(1))   │ shift() is O(n)        │
// └───────────────┴───────────────────────┴───────────────────────┘


// ============================================================
// PART 3: LINKED LISTS [INTERMEDIATE]
// ============================================================

// ------------------------------ Singly Linked List ------------------------------
// [INTERMEDIATE]
// - Linear chain of nodes; each node holds a value + pointer to the next node.
// - No random access (must walk from head); insert/delete at head is O(1).
//
// ASCII diagram:
//   head ──▶ [10|next] ──▶ [20|next] ──▶ [30|next] ──▶ null
//
// Usage: underlies stacks/queues, image viewer "next" links.
// Ops: prepend, append, insert, removeFrom, removeValue, search, reverse, print

class SLNode {
    constructor(value) {
        this.value = value;
        this.next = null;
    }
}

class LinkedList {
    constructor() {
        this.head = null;
        this.size = 0;
    }
    isEmpty() { return this.size === 0; }
    getSize() { return this.size; }

    prepend(value) { // O(1)
        const node = new SLNode(value);
        if (this.isEmpty()) this.head = node;
        else { node.next = this.head; this.head = node; }
        this.size++;
    }

    append(value) { // O(n) — must walk to the tail
        const node = new SLNode(value);
        if (this.isEmpty()) { this.head = node; }
        else {
            let prev = this.head;
            while (prev.next) prev = prev.next;
            prev.next = node;
        }
        this.size++;
    }

    insert(value, index) {
        if (index < 0 || index > this.size) return;
        if (index === 0) { this.prepend(value); return; }
        const node = new SLNode(value);
        let prev = this.head;
        for (let i = 0; i < index - 1; i++) prev = prev.next;
        node.next = prev.next;
        prev.next = node;
        this.size++;
    }

    removeFrom(index) {
        if (index < 0 || index >= this.size) return null;
        let removeNode;
        if (index === 0) {
            removeNode = this.head;
            this.head = this.head.next;
        } else {
            let prev = this.head;
            for (let i = 0; i < index - 1; i++) prev = prev.next;
            removeNode = prev.next;
            prev.next = removeNode.next;
        }
        this.size--;
        return removeNode.value;
    }

    removeValue(value) {
        if (this.isEmpty()) return null;
        if (this.head.value === value) {
            this.head = this.head.next;
            this.size--;
            return value;
        }
        let prev = this.head;
        while (prev.next && prev.next.value !== value) prev = prev.next;
        if (prev.next) {
            prev.next = prev.next.next;
            this.size--;
            return value;
        }
        return null;
    }

    search(value) {
        if (this.isEmpty()) return -1;
        let i = 0, curr = this.head;
        while (curr) {
            if (curr.value === value) return i;
            curr = curr.next;
            i++;
        }
        return -1;
    }

    reverse() {
        let prev = null, curr = this.head;
        while (curr) {
            const next = curr.next;
            curr.next = prev;
            prev = curr;
            curr = next;
        }
        this.head = prev;
    }

    print() {
        if (this.isEmpty()) { console.log("List is Empty"); return; }
        let curr = this.head, listValue = "";
        while (curr) { listValue += `${curr.value} `; curr = curr.next; }
        console.log(listValue);
    }
}

const list = new LinkedList();
console.log(list.isEmpty(), list.getSize());
list.print();
list.insert(10, 0);
list.print();
list.insert(20, 0);
list.print();
list.insert(30, 1);
list.print();
list.insert(40, 2);
list.print();
console.log(list.getSize());
console.log(list.removeFrom(1));
console.log(list.removeFrom(10));
list.print();
list.removeValue(10);
list.print();
console.log(list.search(1000));
console.log(list.search(20));
list.insert(1000, 0);
list.print();
list.reverse();
list.print();
// Big-O: prepend O(1) | append O(n) | insert/removeFrom(index) O(n) | search O(n)
// removing the HEAD is O(1); removing anywhere else requires a traversal.
//
// GOTCHAS:
// - append() without a tail pointer is O(n) because you must walk the whole list.
// - reverse() flips `next` pointers in place — head becomes tail, no new nodes.
// INTERVIEW: "reverse a linked list" is asked in almost every interview loop;
// know the 3-pointer (prev/curr/next) technique above cold.

// -------------------- Singly Linked List with Tail pointer --------------------
// [INTERMEDIATE] Adding a tail pointer makes append() O(1) instead of O(n).
//
// ASCII diagram:
//   head ──▶ [1] ──▶ [2] ──▶ [3] ◀── tail

class LinkedListTail {
    constructor() {
        this.head = null;
        this.tail = null;
        this.size = 0;
    }
    isEmpty() { return this.size === 0; }
    getSize() { return this.size; }

    print() {
        if (this.isEmpty()) { console.log("List is Empty"); return; }
        let curr = this.head, listValues = "";
        while (curr) { listValues += `${curr.value} `; curr = curr.next; }
        console.log(listValues);
    }

    prepend(value) {
        const node = new SLNode(value);
        if (this.isEmpty()) { this.head = node; this.tail = node; }
        else { node.next = this.head; this.head = node; }
        this.size++;
    }

    append(value) { // O(1) thanks to tail pointer
        const node = new SLNode(value);
        if (this.isEmpty()) { this.head = node; this.tail = node; }
        else { this.tail.next = node; this.tail = node; }
        this.size++;
    }

    removeFromFront() { // O(1)
        if (this.isEmpty()) return null;
        const value = this.head.value;
        this.head = this.head.next;
        if (!this.head) this.tail = null;
        this.size--;
        return value;
    }

    removeFormEnd() { // O(n) — no back-pointer, must walk to find the second-to-last node
        if (this.isEmpty()) return null;
        const value = this.tail.value;
        if (this.size === 1) { this.head = null; this.tail = null; }
        else {
            let prev = this.head;
            while (prev.next !== this.tail) prev = prev.next;
            prev.next = null;
            this.tail = prev;
        }
        this.size--;
        return value;
    }
}
console.log("~~~~~~~~~~~~~~~~~~~~~ linked list tail");
const listTail = new LinkedListTail();
console.log(listTail.isEmpty(), listTail.getSize());
listTail.print();
listTail.append(1);
listTail.append(2);
listTail.append(3);
listTail.prepend(0);
listTail.print();
listTail.removeFromFront();
listTail.removeFormEnd();
listTail.print();
// GOTCHAS: removeFormEnd() is still O(n) with only a forward `next` pointer —
// only a DOUBLY linked list makes tail removal O(1) (see below).
// Because prepend/append/removeFromFront are all O(1) here, Stack and Queue
// can both be implemented cleanly on top of this structure:

// ---------------------- Stack via Linked List ----------------------
// [INTERMEDIATE] push/pop at head = O(1), avoids array-resizing overhead entirely.
class LinkedListStack {
    constructor() { this.list = new LinkedListTail(); }
    push(value) { this.list.prepend(value); }
    pop() { return this.list.removeFromFront(); }
    peek() { return this.list.head.value; }
    isEmpty() { return this.list.isEmpty(); }
    getSize() { return this.list.getSize(); }
    print() { return this.list.print(); }
}
const linkedlistStack = new LinkedListStack();
console.log(linkedlistStack.isEmpty());
linkedlistStack.push(20);
linkedlistStack.push(10);
linkedlistStack.push(30);
console.log(linkedlistStack.getSize());
linkedlistStack.print();
console.log(linkedlistStack.pop());
console.log(linkedlistStack.peek());

// ---------------------- Queue via Linked List ----------------------
// [INTERMEDIATE] enqueue at tail, dequeue at head = O(1) both ends.
class LinkedListqueue {
    constructor() { this.list = new LinkedListTail(); }
    enqueue(value) { this.list.append(value); }
    dequeue() { return this.list.removeFromFront(); }
    peek() { return this.list.head.value; }
    isEmpty() { return this.list.isEmpty(); }
    getSize() { return this.list.getSize(); }
    print() { return this.list.print(); }
}
const linkedlistqueue = new LinkedListqueue();
console.log(linkedlistqueue.isEmpty());
linkedlistqueue.enqueue(10);
linkedlistqueue.enqueue(30);
linkedlistqueue.enqueue(20);
console.log(linkedlistqueue.getSize());
linkedlistqueue.print();
console.log(linkedlistqueue.dequeue());
linkedlistqueue.print();
console.log(linkedlistqueue.peek());

// ------------------------------ Doubly Linked List ------------------------------
// [INTERMEDIATE] Each node also has a `prev` pointer, enabling O(1) removal
// from BOTH ends and backward traversal.
//
// ASCII diagram:
//   null ◀── [0] ⇄ [1] ⇄ [2] ⇄ [3] ──▶ null
//   head ─────────────────────────▶ tail

class DLNode {
    constructor(value) {
        this.value = value;
        this.prev = null;
        this.next = null;
    }
}

class DoublyLinkedList {
    constructor() {
        this.head = null;
        this.tail = null;
        this.size = 0;
    }
    isEmpty() { return this.size === 0; }
    getSize() { return this.size; }

    prepend(value) {
        const node = new DLNode(value);
        if (this.isEmpty()) { this.head = node; this.tail = node; }
        else { node.next = this.head; this.head.prev = node; this.head = node; }
        this.size++;
    }

    append(value) {
        const node = new DLNode(value);
        if (this.isEmpty()) { this.head = node; this.tail = node; }
        else { this.tail.next = node; node.prev = this.tail; this.tail = node; }
        this.size++;
    }

    removeFromFront() {
        if (this.isEmpty()) return null;
        const value = this.head.value;
        this.head = this.head.next;
        if (this.head) this.head.prev = null;
        else this.tail = null;
        this.size--;
        return value;
    }

    removeFromEnd() { // O(1) — the whole benefit of the `prev` pointer
        if (this.isEmpty()) return null;
        const value = this.tail.value;
        if (this.size === 1) { this.head = null; this.tail = null; }
        else { this.tail = this.tail.prev; this.tail.next = null; }
        this.size--;
        return value;
    }

    print() {
        if (this.isEmpty()) { console.log("List is empty"); return; }
        let curr = this.head, out = "";
        while (curr) { out += `${curr.value}<->`; curr = curr.next; }
        console.log(out);
    }

    printReverse() {
        if (this.isEmpty()) { console.log("List is empty"); return; }
        let curr = this.tail, out = "";
        while (curr) { out += `${curr.value}<->`; curr = curr.prev; }
        console.log(out);
    }
}

const doublelist = new DoublyLinkedList();
doublelist.append(1);
doublelist.append(2);
doublelist.append(3);
doublelist.prepend(0);
doublelist.print();
doublelist.printReverse();
doublelist.removeFromEnd();
doublelist.print();
doublelist.removeFromFront();
doublelist.print();
// Big-O: prepend/append/removeFromFront/removeFromEnd all O(1) | search O(n)
// GOTCHAS: every extra `prev` pointer costs memory — DLL uses ~2x pointer
// storage vs a singly linked list. Only pay for it if you need backward
// traversal or O(1) tail removal.
// INTERVIEW: DLL underlies LRUCache (Part 7) and browser back/forward history.

// COMPARISON TABLE — Array vs Linked List
// ┌───────────────────────┬───────────────────┬───────────────────────┐
// │                        │ Array              │ Linked List            │
// ├───────────────────────┼───────────────────┼───────────────────────┤
// │ Random access           │ O(1)               │ O(n)                   │
// │ Insert/delete at start  │ O(n)               │ O(1)                   │
// │ Insert/delete at end    │ O(1) (push/pop)    │ O(1) w/ tail, else O(n)│
// │ Memory layout            │ contiguous         │ scattered (+ pointers) │
// │ Cache friendliness       │ high               │ low                    │
// │ Resize cost               │ occasional realloc │ none needed            │
// └───────────────────────┴───────────────────┴───────────────────────┘


// ============================================================
// PART 4: HASH TABLES [INTERMEDIATE]
// ============================================================
// - A hash table (hash map) stores key/value pairs. A hash FUNCTION converts
//   a string key into a numeric index into a fixed-size backing array.
// - JS Object and Map are both hash-table-backed under the hood.
// - Writing your own is a very common interview exercise.
//
// ASCII diagram (size 50, chaining on collision):
//   hash("name") -> 12    table[12] -> [["name","shubham"]]
//   hash("mane") -> 12    table[12] -> [["name","shubham"], ["mane","vinayak"]]
//                                        (collision resolved via chaining/bucket array)
//
// Usage: DB indexing, caches, dedup, O(1)-avg lookups.
// Ops: hash, set, get, remove, display

class HashTable {
    constructor(size) {
        this.table = new Array(size);
        this.size = size;
    }

    hash(key) {
        let total = 0;
        for (let i = 0; i < key.length; i++) total += key.charCodeAt(i);
        return total % this.size;
    }

    set(key, value) { // chaining handles collisions (e.g. "name" & "mane" -> same index)
        const index = this.hash(key);
        const bucket = this.table[index];
        if (!bucket) {
            this.table[index] = [[key, value]];
        } else {
            const sameKeyItem = bucket.find((item) => item[0] === key);
            if (sameKeyItem) sameKeyItem[1] = value;
            else bucket.push([key, value]);
        }
    }

    get(key) {
        const index = this.hash(key);
        const bucket = this.table[index];
        if (bucket) {
            const sameKeyItem = bucket.find((item) => item[0] === key);
            if (sameKeyItem) return sameKeyItem[1];
        }
        return undefined;
    }

    remove(key) {
        const index = this.hash(key);
        const bucket = this.table[index];
        if (bucket) {
            const sameKeyItem = bucket.find((item) => item[0] === key);
            if (sameKeyItem) bucket.splice(bucket.indexOf(sameKeyItem), 1);
        }
    }

    display() {
        for (let i = 0; i < this.table.length; i++) {
            if (this.table[i]) console.log(i, this.table[i]);
        }
    }
}

const table = new HashTable(50);
console.log("Hash table ------", table.hash("shubham"));
table.set("name", "shubham");
table.set("age", 25);
table.display();
console.log(table.get("name"));
table.set("mane", "vinayak"); // "mane" is an anagram of "name" -> SAME hash index
table.display();              // both entries live in the same bucket (chaining)
table.remove("name");
table.display();

// Big-O: set/get/remove are O(1) average, O(n) worst case (all keys collide
// into one bucket) — that's why chaining (bucket = array of [k,v] pairs) matters.
//
// GOTCHAS:
// - A naive hash (sum of char codes) means anagrams collide ("name" vs "mane")
//   — always resolve collisions via chaining or open addressing, never overwrite blindly.
// - Table size should ideally be prime to reduce clustering.
// INTERVIEW: implement a hash table from scratch AND explain collision handling
// (chaining vs open addressing/linear probing) — asked very often.

// COMPARISON TABLE — BST vs Hash Table
// ┌───────────────────────┬───────────────────────┬───────────────────────┐
// │                        │ Binary Search Tree     │ Hash Table             │
// ├───────────────────────┼───────────────────────┼───────────────────────┤
// │ Avg lookup              │ O(log n)               │ O(1)                   │
// │ Worst-case lookup       │ O(n) (unbalanced)      │ O(n) (bad hash/collide)│
// │ Maintains sorted order  │ yes                    │ no                     │
// │ Range queries           │ efficient (in-order)   │ inefficient            │
// │ Memory overhead          │ 2 pointers/node        │ bucket arrays          │
// │ Use when                │ need ordered data       │ need fastest lookup    │
// └───────────────────────┴───────────────────────┴───────────────────────┘


// ============================================================
// PART 5: TREES [INTERMEDIATE / ADVANCED]
// ============================================================
// - A tree is a hierarchical, non-linear DS: nodes connected by edges, no
//   cycles. Non-linear structures allow faster search than linear ones.
// Usage: file systems, DOM, org charts, ASTs, chat bot decision trees.

// ------------------------------ Binary Search Tree ------------------------------
// [INTERMEDIATE/ADVANCED]
// - Binary tree: each node has at most 2 children (left, right).
// - BST invariant: left subtree values < node < right subtree values.
//
// ASCII diagram (after inserting 10, 5, 15, 3, 7):
//                 10
//               /    \
//              5      15
//            /   \
//           3     7
//
// Ops: insert, search, DFS (preorder/inOrder/postOrder), BFS (levelOrder),
//      min, max, delete
// Usage: searching, sorting, lookup tables, priority queues.

class BSTNode {
    constructor(value) {
        this.value = value;
        this.left = null;
        this.right = null;
    }
}

class BinarySearchTree {
    constructor() {
        this.root = null;
    }

    isEmpty() { return this.root === null; }

    insert(value) {
        const node = new BSTNode(value);
        if (this.isEmpty()) this.root = node;
        else this.insertNode(this.root, node);
    }

    insertNode(root, newNode) {
        if (newNode.value < root.value) {
            if (root.left === null) root.left = newNode;
            else this.insertNode(root.left, newNode);
        } else {
            if (root.right === null) root.right = newNode;
            else this.insertNode(root.right, newNode);
        }
    }

    search(root, value) {
        if (!root) return false;
        if (root.value === value) return true;
        return value < root.value
            ? this.search(root.left, value)
            : this.search(root.right, value);
    }

    preorder(root) {
        if (!root) return;
        console.log(root.value);
        this.preorder(root.left);
        this.preorder(root.right);
    }

    inOrder(root) {
        if (!root) return;
        this.inOrder(root.left);
        console.log(root.value);
        this.inOrder(root.right);
    }

    postOrder(root) {
        if (!root) return;
        this.postOrder(root.left);
        this.postOrder(root.right);
        console.log(root.value);
    }

    levelOrder() { // BFS — use the optimized QueueObj implementation from Part 2
        const queue = new QueueObj();
        queue.enqueue(this.root);
        while (!queue.isEmpty()) {
            const curr = queue.dequeue();
            console.log(curr.value);
            if (curr.left) queue.enqueue(curr.left);
            if (curr.right) queue.enqueue(curr.right);
        }
    }

    min(root) { return root.left ? this.min(root.left) : root.value; }
    max(root) { return root.right ? this.max(root.right) : root.value; }

    delete(value) { this.root = this.deleteNode(this.root, value); }

    deleteNode(root, value) {
        if (root === null) return root;
        if (value < root.value) {
            root.left = this.deleteNode(root.left, value);
        } else if (value > root.value) {
            root.right = this.deleteNode(root.right, value);
        } else {
            // found the node to delete
            if (!root.left && !root.right) return null;          // no children
            if (!root.left) return root.right;                    // one child (right)
            if (!root.right) return root.left;                    // one child (left)
            // two children: replace value with min of right subtree, then delete that min
            root.value = this.min(root.right);
            root.right = this.deleteNode(root.right, root.value);
        }
        return root;
    }
}

let bst = new BinarySearchTree();
console.log(bst.isEmpty());
bst.insert(10);
bst.insert(5);
bst.insert(15);
bst.insert(3);
bst.insert(7);

console.log(bst.search(bst.root, 10));
console.log(bst.search(bst.root, 5));
console.log(bst.search(bst.root, 15));
console.log(bst.search(bst.root, 20));

bst.preorder(bst.root);  // 10 5 3 7 15
bst.inOrder(bst.root);   // 3 5 7 10 15
bst.postOrder(bst.root); // 3 7 5 15 10
bst.levelOrder();        // 10 5 15 3 7

console.log(bst.min(bst.root));
console.log(bst.max(bst.root));
bst.delete(5);
bst.inOrder(bst.root); // 3 7 10 15

// Big-O (average, on a balanced tree): insert/search/delete O(log n)
// Worst case (degenerates into a linked list, e.g. inserting sorted data): O(n)
//
// GOTCHAS:
// - A plain BST is NOT self-balancing; inserting sorted input turns it into
//   a linked list (all O(n)). Self-balancing variants: AVL, Red-Black trees.
// - Deleting a two-children node requires the in-order successor (min of right
//   subtree) or predecessor (max of left subtree) — a very common interview trap.
// INTERVIEW: "delete a node from a BST" (3 cases: leaf / one child / two children)
// and "validate a BST" are extremely common questions.

// ------------------------------ Trie (Prefix Tree) ------------------------------
// [ADVANCED]
// - Tree where each path from root spells out a prefix; nodes are shared
//   between words with common prefixes. Great for autocomplete/spell-check.
//
// ASCII diagram (inserted "cat", "car", "dog"):
//   root
//    ├─ c ─ a ─ t*      (t marked isEndOfWord)
//    │       └─ r*
//    └─ d ─ o ─ g*
//
// Ops: insert, search (exact word), startsWith (prefix check)

class TrieNode {
    constructor() {
        this.children = new Map(); // char -> TrieNode
        this.isEndOfWord = false;
    }
}

class Trie {
    constructor() {
        this.root = new TrieNode();
    }

    insert(word) { // O(k), k = word length
        let curr = this.root;
        for (const ch of word) {
            if (!curr.children.has(ch)) curr.children.set(ch, new TrieNode());
            curr = curr.children.get(ch);
        }
        curr.isEndOfWord = true;
    }

    search(word) { // O(k) — exact word match
        const node = this.#traverse(word);
        return node !== null && node.isEndOfWord;
    }

    startsWith(prefix) { // O(k) — used for autocomplete
        return this.#traverse(prefix) !== null;
    }

    #traverse(str) {
        let curr = this.root;
        for (const ch of str) {
            if (!curr.children.has(ch)) return null;
            curr = curr.children.get(ch);
        }
        return curr;
    }
}

const trie = new Trie();
trie.insert("cat");
trie.insert("car");
trie.insert("dog");
console.log(trie.search("cat"));       // true
console.log(trie.search("ca"));        // false (not a full word)
console.log(trie.startsWith("ca"));    // true (prefix exists)
console.log(trie.startsWith("do"));    // true
console.log(trie.search("dogs"));      // false

// Big-O: insert/search/startsWith all O(k) where k = string length (NOT
// dependent on how many words are stored — huge advantage over scanning an array).
//
// GOTCHAS:
// - Memory heavy: every node can fan out to 26+ children; use a Map (not a
//   fixed array) when the alphabet is large or sparse (unicode, etc).
// - Don't forget to mark isEndOfWord — otherwise "car" being a prefix of
//   nothing else still won't register as a complete word.
// INTERVIEW: Trie == the go-to answer for "autocomplete", "spell checker",
// "longest common prefix", "word search II".


// ============================================================
// PART 6: GRAPHS [ADVANCED]
// ============================================================
// - A graph is a set of vertices (nodes) connected by edges; can be directed
//   or undirected, weighted or unweighted. Trees are a special case of graphs
//   (no cycles, one path between any two nodes).
//
// ASCII diagram (undirected graph):
//    A ─── B
//    │     │
//    C ─── D ─── E
//
//   adjacency list: A:[B,C]  B:[A,D]  C:[A,D]  D:[B,C,E]  E:[D]
//
// Usage: social networks, maps/routing, dependency graphs, recommendation engines.
// Representations: adjacency list (space-efficient, used below) vs adjacency matrix.

class Graph {
    constructor() {
        this.adjacencyList = new Map(); // vertex -> Set of neighbor vertices
    }

    addVertex(vertex) {
        if (!this.adjacencyList.has(vertex)) this.adjacencyList.set(vertex, new Set());
    }

    addEdge(v1, v2) { // undirected: add both directions
        this.addVertex(v1);
        this.addVertex(v2);
        this.adjacencyList.get(v1).add(v2);
        this.adjacencyList.get(v2).add(v1);
    }

    removeEdge(v1, v2) {
        this.adjacencyList.get(v1)?.delete(v2);
        this.adjacencyList.get(v2)?.delete(v1);
    }

    removeVertex(vertex) {
        for (const neighbor of this.adjacencyList.get(vertex) || []) {
            this.removeEdge(vertex, neighbor);
        }
        this.adjacencyList.delete(vertex);
    }

    bfs(start) { // level-by-level traversal using a queue
        const visited = new Set([start]);
        const queue = new QueueObj();
        queue.enqueue(start);
        const order = [];
        while (!queue.isEmpty()) {
            const vertex = queue.dequeue();
            order.push(vertex);
            for (const neighbor of this.adjacencyList.get(vertex) || []) {
                if (!visited.has(neighbor)) {
                    visited.add(neighbor);
                    queue.enqueue(neighbor);
                }
            }
        }
        return order;
    }

    dfs(start) { // depth-first traversal using recursion (a call stack)
        const visited = new Set();
        const order = [];
        const traverse = (vertex) => {
            if (!vertex || visited.has(vertex)) return;
            visited.add(vertex);
            order.push(vertex);
            for (const neighbor of this.adjacencyList.get(vertex) || []) {
                traverse(neighbor);
            }
        };
        traverse(start);
        return order;
    }

    dfsIterative(start) { // same result as dfs(), but with an explicit Stack (no recursion)
        const visited = new Set();
        const order = [];
        const stack = new Stack();
        stack.push(start);
        while (!stack.isEmpty()) {
            const vertex = stack.pop();
            if (visited.has(vertex)) continue;
            visited.add(vertex);
            order.push(vertex);
            for (const neighbor of this.adjacencyList.get(vertex) || []) {
                stack.push(neighbor);
            }
        }
        return order;
    }

    print() {
        for (const [vertex, neighbors] of this.adjacencyList) {
            console.log(vertex, "->", [...neighbors].join(", "));
        }
    }
}

const graph = new Graph();
graph.addEdge("A", "B");
graph.addEdge("A", "C");
graph.addEdge("B", "D");
graph.addEdge("C", "D");
graph.addEdge("D", "E");
graph.print();
console.log("BFS from A:", graph.bfs("A")); // A B C D E
console.log("DFS from A:", graph.dfs("A")); // A B D C E
console.log("DFS (iterative) from A:", graph.dfsIterative("A"));

// Big-O: addVertex O(1) | addEdge O(1) | BFS/DFS O(V + E) (V=vertices, E=edges)
//
// GOTCHAS:
// - BFS finds the SHORTEST PATH in an unweighted graph; DFS does not.
// - Recursive DFS can blow the call stack on very deep/large graphs — use the
//   iterative version (explicit Stack) for huge graphs.
// - Must track `visited` or you'll infinite-loop on any cycle.
// - Adjacency list is O(V+E) space and fast for sparse graphs; adjacency
//   matrix is O(V^2) space but O(1) edge lookup — better for dense graphs.
// INTERVIEW: BFS = shortest path/levels ("number of islands", "rotting oranges");
// DFS = connectivity/backtracking ("clone graph", "course schedule" cycle detection).


// ============================================================
// PART 7: ADVANCED [ADVANCED]
// ============================================================

// ------------------------------ LRU Cache ------------------------------
// [ADVANCED] Least Recently Used cache: fixed capacity; when full, evicts the
// item that hasn't been used (get/set) in the longest time.
// Built with a Map, which in JS preserves insertion order — re-inserting a
// key on access moves it to the "most recently used" end for free.
//
// ASCII diagram (capacity 3, MRU on the right):
//   [LRU] key1 <-> key2 <-> key3 [MRU]
//   get(key1) -> moves key1 to MRU end: key2 <-> key3 <-> key1
//   set(new key) when full -> evict key2 (current LRU / leftmost)

class LRUCache {
    constructor(capacity) {
        this.capacity = capacity;
        this.cache = new Map(); // Map preserves insertion order -> front = LRU, back = MRU
    }

    get(key) {
        if (!this.cache.has(key)) return -1;
        const value = this.cache.get(key);
        this.cache.delete(key);   // remove then re-add -> moves to MRU (end)
        this.cache.set(key, value);
        return value;
    }

    put(key, value) {
        if (this.cache.has(key)) this.cache.delete(key); // refresh position
        else if (this.cache.size >= this.capacity) {
            const lruKey = this.cache.keys().next().value; // first key = least recently used
            this.cache.delete(lruKey);
        }
        this.cache.set(key, value);
    }

    print() { console.log([...this.cache.entries()]); }
}

const lru = new LRUCache(3);
lru.put("a", 1);
lru.put("b", 2);
lru.put("c", 3);
lru.print();          // a,b,c  (c is MRU)
console.log(lru.get("a")); // 1 -> a becomes MRU
lru.print();          // b,c,a
lru.put("d", 4);      // capacity exceeded -> evicts "b" (current LRU)
lru.print();          // c,a,d

// Big-O: get/put O(1) average (Map lookup + delete/set are O(1))
//
// GOTCHAS:
// - A true from-scratch interview answer often expects a HashMap + Doubly
//   Linked List (Part 3's DoublyLinkedList) so eviction/promotion is O(1)
//   without relying on Map's insertion-order behavior — know both approaches.
// - Must handle the "key already exists" case in put() by refreshing its
//   position, not just overwriting the value.
// INTERVIEW: "Design an LRU Cache" (LeetCode 146) is one of the most-asked
// system-design-adjacent coding questions — know both the Map-only shortcut
// (above) and the HashMap+DLL from-scratch version.
