// ============================================================
// ALGORITHM COMPLEXITY -- ULTIMATE QUICK-REFERENCE
// ============================================================
// Covers: Big-O, Big-Omega, Big-Theta, space complexity,
// amortized analysis, how to analyze nested loops, and a
// complete cheat-sheet of common algorithm complexities.
//
// INTERVIEW: This is the #1 foundational topic. Every coding
// interview expects you to state time AND space complexity.
// ============================================================

// ============================================================
// 1. CORE DEFINITIONS                                [BASIC]
// ============================================================
// Time  complexity -- how runtime grows with input size n.
// Space complexity -- how memory usage grows with input size n.
//
// We evaluate against input size so the analysis is:
//   - Machine-independent
//   - Comparable across implementations
//
// Trade-off rule of thumb:
//   Fast + lots of memory  -->  optimise for time
//   Slow is OK + low memory -->  optimise for space

// ============================================================
// 2. ASYMPTOTIC NOTATIONS                            [BASIC]
// ============================================================
// Big-O   (O)  -- Upper bound  (worst case)   -- most common
// Omega   (Omega)  -- Lower bound  (best case)
// Theta   (Theta)  -- Tight bound  (average case)
//
// In interviews we almost always talk about Big-O (worst case).

// ============================================================
// 3. BIG-O COMPLEXITY GROWTH -- ASCII CHART          [BASIC]
// ============================================================
//
//  time
//   |
//   |                                              O(n!)
//   |                                         .
//   |                                     O(2^n)
//   |                                 .
//   |                            O(n^2)
//   |                        .
//   |                   O(n log n)
//   |               .
//   |          O(n)
//   |       .
//   |    O(log n)
//   |  .
//   | O(1)
//   +----------------------------------------------> n
//
// Rule: the flatter the curve, the better.

// ============================================================
// 4. BIG-O CHEAT SHEET TABLE                         [BASIC]
// ============================================================
//
// +--------------+----------------+--------------------------+
// | Notation     | Name           | Example                  |
// +--------------+----------------+--------------------------+
// | O(1)         | Constant       | Hash lookup, array[i]    |
// | O(log n)     | Logarithmic    | Binary search            |
// | O(n)         | Linear         | Linear search, one loop  |
// | O(n log n)   | Linearithmic   | Merge sort, Tim sort     |
// | O(n^2)       | Quadratic      | Bubble/Insertion sort    |
// | O(n^3)       | Cubic          | Naive matrix multiply    |
// | O(2^n)       | Exponential    | Recursive fib, subsets   |
// | O(n!)        | Factorial      | Permutations, TSP brute  |
// +--------------+----------------+--------------------------+
//
// INTERVIEW: "Can you do better than O(n^2)?" usually means
//            O(n log n) via sorting or O(n) via hash map.

// ============================================================
// 5. COMMON ALGORITHM COMPLEXITIES TABLE     [INTERMEDIATE]
// ============================================================
//
// +---------------------+----------+----------+----------+-------+
// | Algorithm           | Best     | Average  | Worst    | Space |
// +---------------------+----------+----------+----------+-------+
// | Linear search       | O(1)     | O(n)     | O(n)     | O(1)  |
// | Binary search       | O(1)     | O(log n) | O(log n) | O(1)  |
// | Bubble sort         | O(n)*    | O(n^2)   | O(n^2)   | O(1)  |
// | Selection sort      | O(n^2)   | O(n^2)   | O(n^2)   | O(1)  |
// | Insertion sort      | O(n)*    | O(n^2)   | O(n^2)   | O(1)  |
// | Merge sort          | O(n lg n)| O(n lg n)| O(n lg n)| O(n)  |
// | Quick sort          | O(n lg n)| O(n lg n)| O(n^2)   | O(lg n)|
// | Tim sort (JS .sort) | O(n)*    | O(n lg n)| O(n lg n)| O(n)  |
// | Counting sort       | O(n+k)   | O(n+k)   | O(n+k)   | O(k)  |
// | Heap sort           | O(n lg n)| O(n lg n)| O(n lg n)| O(1)  |
// | BFS / DFS           |  --      |  --      | O(V+E)   | O(V)  |
// | Dijkstra            |  --      |  --      |O(E lg V) | O(V)  |
// +---------------------+----------+----------+----------+-------+
// * = when already sorted
//
// +---------------------+----------+----------+----------+-------+
// | Data Structure Op   | Average  | Worst    | Space    |       |
// +---------------------+----------+----------+----------+-------+
// | Array access        | O(1)     | O(1)     | O(n)     |       |
// | Array search        | O(n)     | O(n)     |  --      |       |
// | Array insert/delete | O(n)     | O(n)     |  --      |       |
// | Hash table get/set  | O(1)     | O(n)     | O(n)     |       |
// | BST search          | O(log n) | O(n)     | O(n)     |       |
// | Stack push/pop      | O(1)     | O(1)     | O(n)     |       |
// | Queue enq/deq       | O(1)     | O(1)     | O(n)     |       |
// +---------------------+----------+----------+----------+-------+

// ============================================================
// 6. HOW TO ANALYZE CODE -- RULES OF THUMB           [BASIC]
// ============================================================
// Rule 1: Drop constants        -- O(2n) => O(n)
// Rule 2: Drop lower-order terms -- O(n^2 + n) => O(n^2)
// Rule 3: Different inputs => different variables
//         -- two arrays a, b => O(a + b) not O(2n)
// Rule 4: Arithmetic/assignment/comparison = O(1)
// Rule 5: A loop of n iterations = O(n) * (body cost)

// ============================================================
// 7. ANALYZING NESTED LOOPS                  [INTERMEDIATE]
// ============================================================

// --- Example 1: Independent nested loops => O(n^2) ---
function example1(n) {
    for (let i = 0; i < n; i++) {         // n times
        for (let j = 0; j < n; j++) {     // n times each
            console.log(i, j);            // O(1) body
        }
    }
}
// Total: n * n = O(n^2)

// --- Example 2: Dependent inner loop => O(n^2) ---
function example2(n) {
    for (let i = 0; i < n; i++) {         // n times
        for (let j = 0; j < i; j++) {     // 0+1+2+...+(n-1) = n(n-1)/2
            console.log(i, j);
        }
    }
}
// Total: n(n-1)/2 => O(n^2)  (drop constant 1/2)

// --- Example 3: Inner loop halves => O(n log n) ---
function example3(n) {
    for (let i = 0; i < n; i++) {         // n times
        for (let j = n; j > 0; j = Math.floor(j / 2)) { // log(n) times
            console.log(i, j);
        }
    }
}
// Total: n * log(n) => O(n log n)

// --- Example 4: Loop that halves => O(log n) ---
function example4(n) {
    let i = n;
    while (i > 1) {
        i = Math.floor(i / 2);           // halves each time
    }
}
// Total: O(log n)   (binary search pattern)

// --- Example 5: Two sequential loops => O(n) ---
function example5(arr) {
    for (let i = 0; i < arr.length; i++) { console.log(arr[i]); } // O(n)
    for (let j = 0; j < arr.length; j++) { console.log(arr[j]); } // O(n)
}
// Total: O(n) + O(n) = O(2n) = O(n)

// --- Example 6: Two DIFFERENT inputs ---
function example6(arrA, arrB) {
    for (let i = 0; i < arrA.length; i++) { console.log(arrA[i]); }
    for (let j = 0; j < arrB.length; j++) { console.log(arrB[j]); }
}
// Total: O(a + b)  -- NOT O(n)!  Different inputs, different variables.

// ============================================================
// 8. SPACE COMPLEXITY EXAMPLES               [INTERMEDIATE]
// ============================================================

// O(1) space -- constant; uses fixed variables regardless of n
function sumArray(arr) {
    let total = 0;                     // one variable
    for (let i = 0; i < arr.length; i++) {
        total += arr[i];
    }
    return total;
}
// Time: O(n)  |  Space: O(1)

// O(n) space -- creates an array proportional to input
function doubleArray(arr) {
    const result = [];
    for (let i = 0; i < arr.length; i++) {
        result.push(arr[i] * 2);       // result grows to n elements
    }
    return result;
}
// Time: O(n)  |  Space: O(n)

// O(n) space -- recursion call stack
function recursiveSum(n) {
    if (n <= 0) return 0;
    return n + recursiveSum(n - 1);    // n frames on the call stack
}
// Time: O(n)  |  Space: O(n)  (call stack)

// O(n^2) space -- 2D matrix
function createMatrix(n) {
    const matrix = [];
    for (let i = 0; i < n; i++) {
        matrix[i] = new Array(n).fill(0);
    }
    return matrix;
}
// Time: O(n^2)  |  Space: O(n^2)

// ============================================================
// 9. AMORTIZED COMPLEXITY                    [ADVANCED]
// ============================================================
// Amortized analysis looks at the AVERAGE cost per operation
// over a SEQUENCE of operations, even if some individual
// operations are expensive.
//
// Classic example: Dynamic array (JS Array.push)
//
//  push #1  --> capacity 1, no resize              O(1)
//  push #2  --> capacity 2, resize+copy 1 element  O(1) resize
//  push #3  --> capacity 4, resize+copy 2 elements O(2)
//  push #4  --> fits                                O(1)
//  push #5  --> capacity 8, resize+copy 4 elements O(4)
//  ...
//
//  Array capacity doubling diagram:
//  +---+
//  | 1 |  cap=1
//  +---+---+
//  | 1 | 2 |  cap=2  (copied 1)
//  +---+---+---+---+
//  | 1 | 2 | 3 |   |  cap=4  (copied 2)
//  +---+---+---+---+
//  | 1 | 2 | 3 | 4 |  cap=4  (no resize)
//  +---+---+---+---+---+---+---+---+
//  | 1 | 2 | 3 | 4 | 5 |   |   |   |  cap=8  (copied 4)
//  +---+---+---+---+---+---+---+---+
//
// Total cost for n pushes: n + (1+2+4+8+...+n) ~= 3n
// Amortized cost per push: 3n/n = O(1)
//
// INTERVIEW: "Array.push() is O(1) amortized" is a safe answer.
// But a SINGLE push CAN be O(n) when a resize triggers.

// ============================================================
// 10. GOTCHAS                                [INTERMEDIATE]
// ============================================================
// GOTCHA 1: String concatenation in a loop is O(n^2) in many
//   languages because each concat creates a new string.
//   Use Array.join() instead.

// GOTCHA 2: Array.shift() / unshift() is O(n) not O(1)!
//   Every element must be re-indexed. Use a Queue or deque.

// GOTCHA 3: Object.keys() is O(n) -- it creates a new array.

// GOTCHA 4: Recursive fib without memoization is O(2^n).
//   With memoization it becomes O(n).

// GOTCHA 5: Sorting + scanning is O(n log n), often better
//   than brute-force O(n^2) but worse than hash-map O(n).

// GOTCHA 6: Space complexity of recursion includes the call
//   stack. Depth d => O(d) space even with no extra data.

// GOTCHA 7: log base does not matter for Big-O.
//   O(log2 n) = O(log10 n) = O(ln n) because bases differ
//   by a constant factor.

// ============================================================
// 11. QUICK DECISION FRAMEWORK               [INTERVIEW TIP]
// ============================================================
// "What's the best complexity for this problem?"
//
//  Need to look at every element?       => at least O(n)
//  Need to compare all pairs?           => at least O(n^2)
//  Sorted input + search?               => O(log n) binary search
//  Need sorted output?                  => at least O(n log n)
//  Counting / frequency?                => O(n) with hash map
//  Subsequences / subsets?              => O(2^n)
//  Permutations?                        => O(n!)
//
// INTERVIEW: Always state BOTH time and space complexity.
//            "This runs in O(n) time and O(1) space."

// ============================================================
// REFERENCES
// ============================================================
// 1. https://cs.slides.com/colt_steele/big-o-notation
// 2. https://rithmschool.github.io/function-timer-demo/
// 3. https://www.bigocheatsheet.com/
