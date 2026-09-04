/* ============================================================================
 * HEAPS & PRIORITY QUEUE  [ADVANCED]
 * ============================================================================
 * MinHeap (binary heap array), PriorityQueue (built on top of MinHeap).
 * ==========================================================================*/

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
