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
    // `less(a, b)` decides "a goes above b". Default compares plain values;
    // PriorityQueue passes one that compares .priority instead.
    constructor(less = (a, b) => a < b) { this.heap = []; this.less = less; }
    size() { return this.heap.length; }
    isEmpty() { return this.heap.length === 0; }
    peek() { return this.isEmpty() ? null : this.heap[0]; }
    // TRACE size() / isEmpty() / peek()   heap = [1,3,2,5,9,8]
    //   size() -> 6    isEmpty() -> false    peek() -> heap[0] = 1
    //   on []: size() 0, isEmpty() true, peek() null

    #parent(i) { return Math.floor((i - 1) / 2); }
    #left(i) { return 2 * i + 1; }
    #right(i) { return 2 * i + 2; }
    #swap(i, j) { [this.heap[i], this.heap[j]] = [this.heap[j], this.heap[i]]; }
    // TRACE helpers   i = 1
    //   #parent(1) = floor(0/2) = 0    #parent(3) = floor(2/2) = 1
    //   #left(1)   = 2*1+1 = 3         #right(1)  = 2*1+2 = 4
    //   #swap(3,1) on [3,5,8,1] -> [3,1,8,5]

    insert(value) {
        this.heap.push(value);
        let i = this.heap.length - 1;
        while (i > 0 && this.less(this.heap[i], this.heap[this.#parent(i)])) {
            this.#swap(i, this.#parent(i));
            i = this.#parent(i);
        }
    }
    // TRACE [5, 3, 8, 1, 9, 2].forEach(insert)   (push, then sift-up)
    //   insert 5  [5]
    //   insert 3  [5,3]        swap 3<->5 -> [3,5]
    //   insert 8  [3,5,8]      8 > parent 3, stays
    //   insert 1  [3,5,8,1]    swap 1<->5 -> [3,1,8,5]  swap 1<->3 -> [1,3,8,5]
    //   insert 9  [1,3,8,5,9]  9 > parent 3, stays
    //   insert 2  [1,3,8,5,9,2] swap 2<->8 -> [1,3,2,5,9,8]  2 > parent 1, stop
    //   tree:        1
    //              /   \
    //             3     2
    //            / \   /
    //           5   9 8

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
    // TRACE extractMin()   heap = [1,3,2,5,9,8]
    //   step 1  min = 1;  last = pop() = 8      [1,3,2,5,9]
    //   step 2  heap[0] = last                  [8,3,2,5,9]
    //   step 3  #bubbleDown(0): children 3,2 -> smallest 2, swap 8<->2 -> [2,3,8,5,9]
    //           i=2 has no children -> stop
    //   tree:      2          return 1
    //            /   \
    //           3     8
    //          / \
    //         5   9
    //   2nd extractMin() -> return 2, heap [3,5,8,9]  (see #bubbleDown trace)

    #bubbleDown(i) {
        const n = this.heap.length;
        while (true) {
            const l = this.#left(i), r = this.#right(i);
            let smallest = i;
            if (l < n && this.less(this.heap[l], this.heap[smallest])) smallest = l;
            if (r < n && this.less(this.heap[r], this.heap[smallest])) smallest = r;
            if (smallest === i) break;
            this.#swap(i, smallest);
            i = smallest;
        }
    }
    // TRACE #bubbleDown(0)   heap = [9,3,8,5]   n = 4  (2nd extractMin, last=9 moved to root)
    //   i=0  l=1 (3)  r=2 (8)    smallest=1  swap 9<->3 -> [3,9,8,5]
    //   i=1  l=3 (5)  r=4 (out)  smallest=3  swap 9<->5 -> [3,5,8,9]
    //   i=3  l=7, r=8 out of range -> smallest === i -> break
    //   tree:      3
    //            /   \
    //           5     8
    //          /
    //         9
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
    // The heap compares .priority, so BOTH sift-up (insert) and sift-down
    // (extractMin) order entries correctly. Comparing the {value, priority}
    // objects themselves with `<` is always false and would silently break it.
    constructor() { this.heap = new MinHeapDS((a, b) => a.priority < b.priority); }
    enqueue(value, priority) { this.heap.insert({ value, priority }); }
    // TRACE enqueue x3   entries shown as priority:value
    //   ("low prio task", 5)  [5:low]                       i=0, nothing to compare
    //   ("urgent task", 1)    [5:low, 1:urgent]             1 < parent 5 -> swap
    //                         [1:urgent, 5:low]
    //   ("medium task", 3)    [1:urgent, 5:low, 3:medium]   3 > parent 1, stays
    dequeue() {
        const min = this.heap.extractMin();
        return min ? min.value : null;
    }
    // TRACE dequeue() x2   heap = [1:urgent, 5:low, 3:medium]
    //   1st  min = 1:urgent; pop last 3:medium -> root    [3:medium, 5:low]
    //        sift-down: child 5 > 3 -> no swap
    //        return "urgent task"
    //   2nd  min = 3:medium; pop last 5:low -> root       [5:low]
    //        return "medium task"
    //   order is now guaranteed for ANY insertion order, e.g. priorities
    //   5,1,4,2,3 dequeue as 1,2,3,4,5
    isEmpty() { return this.heap.isEmpty(); }
    // TRACE isEmpty()   after 2 dequeues heap = [5:low] -> false
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
