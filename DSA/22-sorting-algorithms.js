// ============================================================
// SORTING ALGORITHMS -- ULTIMATE QUICK-REFERENCE
// ============================================================
// Covers: Bubble, Selection, Insertion, Quick, Merge,
// Counting sort, JS Array.sort() internals (TimSort),
// stability, and when to use which.
// ============================================================

// ============================================================
// SORT ALGORITHM COMPARISON TABLE
// ============================================================
//
// +----------------+----------+-----------+-----------+-------+---------+----------+
// | Algorithm      | Best     | Average   | Worst     | Space | Stable? | In-place?|
// +----------------+----------+-----------+-----------+-------+---------+----------+
// | Bubble sort    | O(n)*    | O(n^2)    | O(n^2)    | O(1)  | Yes     | Yes      |
// | Selection sort | O(n^2)   | O(n^2)    | O(n^2)    | O(1)  | No      | Yes      |
// | Insertion sort | O(n)*    | O(n^2)    | O(n^2)    | O(1)  | Yes     | Yes      |
// | Quick sort     | O(n lg n)| O(n lg n) | O(n^2)    |O(lg n)| No**    | Yes      |
// | Merge sort     | O(n lg n)| O(n lg n) | O(n lg n) | O(n)  | Yes     | No       |
// | Counting sort  | O(n+k)   | O(n+k)   | O(n+k)    | O(k)  | Yes     | No       |
// | Tim sort (JS)  | O(n)*    | O(n lg n) | O(n lg n) | O(n)  | Yes     | No       |
// | Heap sort      | O(n lg n)| O(n lg n) | O(n lg n) | O(1)  | No      | Yes      |
// +----------------+----------+-----------+-----------+-------+---------+----------+
// * = when already sorted     ** = depends on implementation
// k = range of input values (for counting sort)

// ============================================================
// SORT STABILITY EXPLAINED                           [BASIC]
// ============================================================
// A STABLE sort preserves the relative order of elements with
// equal keys.
//
// Example: sort by age
//   Before: [{name:"Bob",age:25}, {name:"Alice",age:25}, {name:"Eve",age:22}]
//
//   Stable sort result (Bob stays before Alice):
//     [{name:"Eve",age:22}, {name:"Bob",age:25}, {name:"Alice",age:25}]
//
//   Unstable sort might swap Bob and Alice:
//     [{name:"Eve",age:22}, {name:"Alice",age:25}, {name:"Bob",age:25}]
//
// INTERVIEW: Stability matters when you sort by multiple keys.
//   Sort by name first, then stable-sort by age => both orderings
//   are preserved. Unstable sort would destroy the name ordering.

// ============================================================
// 1. BUBBLE SORT                                     [BASIC]
// ============================================================
// Repeatedly swap adjacent elements if out of order.
// Like bubbles rising: largest element "bubbles" to the end.
//
//  Pass 1: [8, 20, -2, 4, -6]
//          [8, 20, -2, 4, -6]  8<20 ok
//          [8, -2, 20, 4, -6]  20>-2 swap
//          [8, -2, 4, 20, -6]  20>4  swap
//          [8, -2, 4, -6, 20]  20>-6 swap   <-- 20 in final position
//  Pass 2: [8, -2, 4, -6, 20]
//          [-2, 8, 4, -6, 20]  8>-2  swap
//          [-2, 4, 8, -6, 20]  8>4   swap
//          [-2, 4, -6, 8, 20]  8>-6  swap   <-- 8 in final position
//  Pass 3: [-2, 4, -6, 8, 20]
//          [-2, 4, -6, 8, 20]  -2<4  ok
//          [-2, -6, 4, 8, 20]  4>-6  swap   <-- 4 in final position
//  Pass 4: [-6, -2, 4, 8, 20]                <-- DONE
//
// Time: O(n^2)  |  Space: O(1)  |  Stable: Yes

function bubbleSort(arr) {
    let swapped;
    do {
        swapped = false;
        for (let i = 0; i < arr.length - 1; i++) {
            if (arr[i] > arr[i + 1]) {
                [arr[i], arr[i + 1]] = [arr[i + 1], arr[i]]; // ES6 swap
                swapped = true;
            }
        }
    } while (swapped);
    return arr;
}

const bArr = [8, 20, -2, 4, -6];
bubbleSort(bArr);
console.log("bubble sort:", bArr); // [-6, -2, 4, 8, 20]

// GOTCHAS:
// - The `swapped` flag is the optimization. Without it, runs
//   n^2 even on a sorted array. With it, best case is O(n).
// - Never use in production. Only good for teaching.

// ============================================================
// 2. SELECTION SORT                                  [BASIC]
// ============================================================
// Find the minimum, swap it to the front. Repeat for the rest.
//
//  [8, 20, -2, 4, -6]
//   ^               min=-6 at idx 4 => swap with idx 0
//  [-6, 20, -2, 4, 8]
//       ^           min=-2 at idx 2 => swap with idx 1
//  [-6, -2, 20, 4, 8]
//            ^      min=4  at idx 3 => swap with idx 2
//  [-6, -2, 4, 20, 8]
//               ^   min=8  at idx 4 => swap with idx 3
//  [-6, -2, 4, 8, 20]  DONE
//
// Time: O(n^2) always  |  Space: O(1)  |  Stable: No

function selectionSort(arr) {
    for (let i = 0; i < arr.length - 1; i++) {
        let minIdx = i;
        for (let j = i + 1; j < arr.length; j++) {
            if (arr[j] < arr[minIdx]) minIdx = j;
        }
        if (minIdx !== i) {
            [arr[i], arr[minIdx]] = [arr[minIdx], arr[i]];
        }
    }
    return arr;
}

const sArr = [8, 20, -2, 4, -6];
selectionSort(sArr);
console.log("selection sort:", sArr); // [-6, -2, 4, 8, 20]

// GOTCHAS:
// - Always O(n^2) -- no early exit even if sorted.
// - Unstable: swapping can change relative order of equal elements.
// - Minimises number of swaps: exactly n-1 swaps. Good when
//   writes are expensive (e.g., flash memory).

// ============================================================
// 3. INSERTION SORT                                  [BASIC]
// ============================================================
// Build a sorted portion from left to right. Take the next
// unsorted element and insert it into the correct position.
//
//  [8, 20, -2, 4, -6]
//   sorted|unsorted
//  [8] | 20  insert 20 after 8
//  [8, 20] | -2  insert -2 before 8
//  [-2, 8, 20] | 4  insert 4 between 8 and 20
//  [-2, 4, 8, 20] | -6  insert -6 before -2
//  [-6, -2, 4, 8, 20]  DONE
//
// Time: O(n^2) worst  |  O(n) best (sorted)  |  Space: O(1)  |  Stable: Yes
// INTERVIEW: Best for small arrays and nearly-sorted data.
//   TimSort uses insertion sort for small sub-arrays (< 64 elements).

function insertionSort(arr) {
    for (let i = 1; i < arr.length; i++) {
        let key = arr[i];
        let j = i - 1;
        while (j >= 0 && arr[j] > key) {
            arr[j + 1] = arr[j];
            j--;
        }
        arr[j + 1] = key;
    }
    return arr;
}

const iArr = [8, 20, -2, 4, -6];
insertionSort(iArr);
console.log("insertion sort:", iArr); // [-6, -2, 4, 8, 20]

// GOTCHAS:
// - Shifts, not swaps => fewer writes than bubble sort.
// - O(n) on nearly sorted data -- very efficient as an
//   "adaptive" sort for real-world data.

// ============================================================
// 4. QUICK SORT                              [INTERMEDIATE]
// ============================================================
// Pick a pivot, partition into left (< pivot) and right (>= pivot),
// recurse on each side.
//
//  [8, 20, -2, 4, -6]   pivot=last=-6
//   left: []   right: [8, 20, -2, 4]
//   => [-6] ++ quickSort([]) ++ quickSort([8, 20, -2, 4])
//
//  Recursion tree (last-element pivot):
//                    [8,20,-2,4,-6]
//                    pivot=-6
//                   /            \
//                 []          [8,20,-2,4]
//                              pivot=4
//                            /         \
//                        [-2]        [8,20]
//                                   pivot=20
//                                  /       \
//                                [8]       []
//
//   Result: [-6, -2, 4, 8, 20]
//
// Time: O(n log n) avg  |  O(n^2) worst (sorted input + bad pivot)
// Space: O(log n) avg (call stack)  |  Stable: No

function quickSort(arr) {
    if (arr.length < 2) return arr;

    let pivot = arr[arr.length - 1];
    let left = [], right = [];

    for (let i = 0; i < arr.length - 1; i++) {
        if (arr[i] < pivot) left.push(arr[i]);
        else right.push(arr[i]);
    }
    return [...quickSort(left), pivot, ...quickSort(right)];
}

console.log("quick sort:", quickSort([8, 20, -2, 4, -6])); // [-6, -2, 4, 8, 20]

// GOTCHAS:
// - This version creates new arrays => O(n) space per level.
//   In-place partitioning (Lomuto/Hoare) uses O(log n) space.
// - Worst case O(n^2) when pivot is always min or max (e.g.,
//   already sorted + last-element pivot). Fix: random pivot
//   or median-of-three.
// - Despite O(n^2) worst case, quick sort is fastest in practice
//   due to cache-friendly sequential access and small constants.

// ============================================================
// 5. MERGE SORT                              [INTERMEDIATE]
// ============================================================
// Divide array in half recursively until single elements,
// then merge sorted halves back together.
//
//  Split phase:
//  [8, 20, -2, 4, -6]
//      /            \
//  [8, 20]      [-2, 4, -6]
//   /   \        /       \
//  [8] [20]   [-2]    [4, -6]
//                      /    \
//                    [4]   [-6]
//
//  Merge phase:
//  [8]+[20] => [8,20]
//  [4]+[-6] => [-6,4]
//  [-2]+[-6,4] => [-6,-2,4]
//  [8,20]+[-6,-2,4] => [-6,-2,4,8,20]
//
// Time: O(n log n) always  |  Space: O(n)  |  Stable: Yes
// INTERVIEW: The go-to when stability or guaranteed O(n log n) is needed.

function mergeSort(arr) {
    if (arr.length < 2) return arr;

    const mid = Math.floor(arr.length / 2);
    const left = mergeSort(arr.slice(0, mid));
    const right = mergeSort(arr.slice(mid));
    return merge(left, right);
}

function merge(left, right) {
    const sorted = [];
    while (left.length && right.length) {
        if (left[0] <= right[0]) sorted.push(left.shift());
        else sorted.push(right.shift());
    }
    return [...sorted, ...left, ...right];
}

console.log("merge sort:", mergeSort([8, 20, -2, 4, -6])); // [-6, -2, 4, 8, 20]

// GOTCHAS:
// - Always O(n) extra space. Cannot be done truly in-place.
// - The `<=` in merge preserves stability (equal elements keep
//   their original order).
// - shift() is O(n). For production, use index pointers instead.

// ============================================================
// 6. COUNTING SORT                           [ADVANCED]
// ============================================================
// Non-comparison sort. Count occurrences of each value, then
// reconstruct the array. Only works for non-negative integers
// within a known range.
//
//  arr: [4, 2, 2, 8, 3, 3, 1]   max=8
//
//  Count array (idx = value, val = frequency):
//  idx: 0  1  2  3  4  5  6  7  8
//       0  1  2  2  1  0  0  0  1
//
//  Reconstruct: 1, 2, 2, 3, 3, 4, 8
//
// Time: O(n + k)  |  Space: O(k)  |  k = max value
// Stable: Yes (with the cumulative count technique)
// INTERVIEW: Mention when values are in a small known range.

function countingSort(arr) {
    if (arr.length === 0) return arr;

    const max = Math.max(...arr);
    const count = new Array(max + 1).fill(0);

    for (const num of arr) count[num]++;

    const sorted = [];
    for (let i = 0; i < count.length; i++) {
        while (count[i] > 0) {
            sorted.push(i);
            count[i]--;
        }
    }
    return sorted;
}

console.log("counting sort:", countingSort([4, 2, 2, 8, 3, 3, 1])); // [1, 2, 2, 3, 3, 4, 8]

// GOTCHAS:
// - Only works for non-negative integers.
// - If max value k >> n, this wastes memory. Use radix sort
//   or bucket sort instead.
// - O(n+k) can beat O(n log n) comparison sorts when k is small.

// ============================================================
// 7. JS Array.sort() INTERNALS (TIMSORT)     [INTERMEDIATE]
// ============================================================
// V8 (Chrome/Node) uses TimSort since 2019.
// TimSort = Merge Sort + Insertion Sort hybrid.
//
// How it works:
//  1. Divide array into "runs" (naturally sorted subsequences).
//  2. If a run is shorter than minrun (32-64), extend it using
//     insertion sort.
//  3. Merge runs using merge sort, maintaining a stack invariant.
//
//   Input:  [5, 3, 8, 6, 2, 7, 1, 4]
//           |run1|  |run2|  |run3|  ...
//           insertion sort each run
//           merge runs together
//
// Time: O(n) best (already sorted)  |  O(n log n) average/worst
// Space: O(n)  |  Stable: Yes
//
// INTERVIEW: "JS sort is TimSort, stable, O(n log n), but the
//   comparator function matters!"

// --- Default sort is LEXICOGRAPHIC (string comparison) ---
console.log([10, 9, 8, 1, 2].sort());          // [1, 10, 2, 8, 9]  WRONG!
console.log([10, 9, 8, 1, 2].sort((a, b) => a - b)); // [1, 2, 8, 9, 10]  correct

// --- Sort objects by property ---
const people = [
    { name: "Charlie", age: 30 },
    { name: "Alice", age: 25 },
    { name: "Bob", age: 25 },
];
people.sort((a, b) => a.age - b.age);
console.log(people);
// [ {Alice,25}, {Bob,25}, {Charlie,30} ]
// Note: Alice and Bob keep original order (stable!)

// GOTCHAS:
// - sort() WITHOUT a comparator converts to strings first!
//   [10, 2, 1].sort() => [1, 10, 2]  (string "10" < "2")
// - sort() mutates the original array. Use [...arr].sort() for
//   a non-mutating version.
// - Comparator must return negative, zero, or positive:
//     (a, b) => a - b   ascending
//     (a, b) => b - a   descending
// - Returning only true/false from the comparator is WRONG.

// ============================================================
// 8. WHEN TO USE WHICH SORT                  [INTERVIEW TIP]
// ============================================================
//
// +----------------------------+----------------------------+
// | Situation                  | Best Sort                  |
// +----------------------------+----------------------------+
// | Small array (< 50)         | Insertion sort             |
// | Nearly sorted data         | Insertion sort or TimSort  |
// | Guaranteed O(n log n)      | Merge sort                 |
// | Fastest in practice        | Quick sort (random pivot)  |
// | Stability required         | Merge sort or TimSort      |
// | Memory constrained         | Quick sort (in-place) or   |
// |                            | Heap sort                  |
// | Integers in small range    | Counting sort              |
// | Large integers/strings     | Radix sort                 |
// | JavaScript built-in        | Array.sort() (TimSort)     |
// | Linked list                | Merge sort (no random      |
// |                            | access needed)             |
// +----------------------------+----------------------------+
//
// INTERVIEW: "In practice I'd use Array.sort() with a proper
//   comparator. For interview purposes, merge sort gives
//   guaranteed O(n log n) with stability."

// ============================================================
// GOTCHAS SUMMARY
// ============================================================
// 1. Array.sort() without comparator is LEXICOGRAPHIC.
// 2. Quick sort worst case is O(n^2) on sorted input with a bad
//    pivot strategy. Use random or median-of-three pivot.
// 3. Merge sort needs O(n) extra space -- not ideal for memory-
//    constrained environments.
// 4. Insertion sort is actually FASTEST for small n. That's why
//    TimSort and IntroSort use it as a base case.
// 5. Counting sort is O(n+k), not O(n). If k is huge (e.g.,
//    sorting floats), it's impractical.
// 6. "Stable" matters when you sort objects by multiple keys.
//    Sort by secondary key first, then stable-sort by primary key.
