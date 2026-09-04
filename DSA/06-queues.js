/* ============================================================================
 * QUEUES — FIFO DATA STRUCTURE  [BASIC / INTERMEDIATE]
 * ============================================================================
 * Queue, QueueObj (optimized), CircularQueue, Stack vs Queue comparison.
 * ==========================================================================*/

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
// object+pointers (above) or a linked list (see 07-linked-lists.js).

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

// COMPARISON TABLE — Stack vs Queue
// ┌───────────────┬───────────────────────┬───────────────────────┐
// │                │ Stack (LIFO)           │ Queue (FIFO)           │
// ├───────────────┼───────────────────────┼───────────────────────┤
// │ Add            │ push (top)             │ enqueue (rear)         │
// │ Remove         │ pop (top)              │ dequeue (front)        │
// │ Use cases       │ undo, call stack, DFS  │ scheduling, BFS, print │
// │ Array pitfall   │ none (push/pop O(1))   │ shift() is O(n)        │
// └───────────────┴───────────────────────┴───────────────────────┘
