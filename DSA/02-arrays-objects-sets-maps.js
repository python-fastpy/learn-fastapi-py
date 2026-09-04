/* ============================================================================
 * BUILT-IN DATA STRUCTURES — ARRAY, OBJECT, SET, MAP  [BASIC]
 * ============================================================================
 * Refs:
 *  https://dev.to/prnvbirajdar/list-of-visual-tools-to-help-with-data-structures-and-algorithms-4nb2
 *  https://github.com/gopinav/JavaScript-Data-Structures-Tutorial
 * ==========================================================================*/

// ============================================================
// MASTER BIG-O COMPARISON TABLE (all data structures in this folder)
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
