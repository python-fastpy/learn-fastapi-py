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
    // TRACE new Queue() -> isEmpty() -> enqueue(10,20,30) -> size() -> print() -> dequeue() -> peek()
    //   step 1  constructor     items = [ ]            isEmpty() -> true
    //   step 2  enqueue(10)     items = [ 10 ]          (push at rear)
    //   step 3  enqueue(20)     items = [ 10, 20 ]
    //   step 4  enqueue(30)     items = [ 10, 20, 30 ]
    //   step 5  size()  -> 3    print() -> "10,20,30"
    //   step 6  dequeue()       shift() removes front -> returns 10
    //           items = [ 20, 30 ]   (20 re-indexed 1->0, 30 2->1: O(n))
    //   step 7  peek()  -> items[0] = 20   (empty queue -> null)
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
    // TRACE new QueueObj()
    //   items = { }   front = 0   rear = 0
    enqueue(element) {
        this.items[this.rear] = element;
        this.rear++;
    }
    // TRACE enqueue(10) -> enqueue(20) -> enqueue(30)
    //   step 1  items[0] = 10   rear 0->1   items = { 0:10 }
    //   step 2  items[1] = 20   rear 1->2   items = { 0:10, 1:20 }
    //   step 3  items[2] = 30   rear 2->3   items = { 0:10, 1:20, 2:30 }
    //   front = 0 (unchanged)
    dequeue() {
        const item = this.items[this.front];
        delete this.items[this.front];
        this.front++;
        return item;
    }
    // TRACE dequeue()   items = { 0:10, 1:20, 2:30 }  front=0  rear=3
    //   step 1  item = items[0] = 10
    //   step 2  delete items[0]   items = { 1:20, 2:30 }
    //   step 3  front 0->1        (nothing re-indexed -> O(1))
    //   returns 10
    isEmpty() { return this.rear - this.front === 0; }
    peek() { return this.items[this.front]; }
    size() { return this.rear - this.front; }
    print() { console.log(this.items); }
    // TRACE after enqueue(10,20,30)   front=0 rear=3
    //   isEmpty() -> 3 - 0 === 0 -> false   (new queue: 0 - 0 -> true)
    //   size()    -> 3 - 0 = 3
    //   print()   -> { '0': 10, '1': 20, '2': 30 }
    //   after dequeue(): front=1 -> peek() = items[1] = 20, size() = 3 - 1 = 2
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
    // TRACE new CircularQueue(5)
    //   items = [ _, _, _, _, _ ]   capacity=5  currentLength=0  front=-1  rear=-1
    isFull() { return this.currentLength === this.capacity; }
    isEmpty() { return this.currentLength === 0; }
    // TRACE isFull() / isEmpty()   capacity = 5
    //   currentLength=0 -> isEmpty() true,  isFull() false
    //   currentLength=5 -> isEmpty() false, isFull() true
    enqueue(element) {
        if (this.isFull()) return;
        this.rear = (this.rear + 1) % this.capacity;
        this.items[this.rear] = element;
        this.currentLength += 1;
        if (this.front === -1) this.front = this.rear;
    }
    // TRACE enqueue(10) -> enqueue(20) -> ... -> enqueue(50) -> enqueue(60)
    //   step 1  rear=(-1+1)%5=0  items=[10,_,_,_,_]  len=1  front -1->0
    //   step 2  rear=(0+1)%5=1   items=[10,20,_,_,_] len=2  front=0
    //   ...
    //   step 5  rear=(3+1)%5=4   items=[10,20,30,40,50] len=5
    //   step 6  enqueue(60): isFull() -> true -> return (ignored)
    //   wrap: after dequeue() front=1, enqueue(100): rear=(4+1)%5=0
    //         items=[100,20,30,40,50]  front=1 rear=0 len=5
    dequeue() {
        if (this.isEmpty()) return null;
        const item = this.items[this.front];
        this.items[this.front] = null;
        this.front = (this.front + 1) % this.capacity;
        this.currentLength -= 1;
        if (this.isEmpty()) { this.front = -1; this.rear = -1; }
        return item;
    }
    // TRACE dequeue()   items=[10,20,30,40,50]  front=0 rear=4 len=5
    //   step 1  item = items[0] = 10
    //   step 2  items[0] = null   items=[null,20,30,40,50]
    //   step 3  front=(0+1)%5=1   len 5->4   not empty -> no reset
    //   returns 10
    //   edge: last item removed -> len=0 -> front=-1, rear=-1 (reset)
    peek() { return this.isEmpty() ? null : this.items[this.front]; }
    // TRACE peek()   after dequeue(): front=1  items=[null,20,30,40,50]
    //   not empty -> items[1] = 20   (empty queue -> null)
    print() {
        if (this.isEmpty()) { console.log("queue is empty"); return; }
        let i, str = "";
        for (i = this.front; i !== this.rear; i = (i + 1) % this.capacity) {
            str += this.items[i] + " ";
        }
        str += this.items[i];
        console.log(str);
    }
    // TRACE print()   items=[100,20,30,40,50]  front=1  rear=0  (wrapped)
    //   i=1  i!==0  str = "20 "
    //   i=2  i!==0  str = "20 30 "
    //   i=3  i!==0  str = "20 30 40 "
    //   i=4  i!==0  str = "20 30 40 50 "
    //   i=(4+1)%5=0 === rear -> loop stops; str += items[0]
    //   prints "20 30 40 50 100"
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
