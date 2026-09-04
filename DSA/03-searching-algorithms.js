// ============================================================
// SEARCH ALGORITHMS -- ULTIMATE QUICK-REFERENCE
// ============================================================
// Covers: Linear, Binary (iterative + recursive), Jump,
// Interpolation, Two-Pointer, Sliding Window.
//
// INTERVIEW: Search is foundational. Binary search alone
// appears in ~30% of coding interviews.
// ============================================================

// ============================================================
// COMPARISON TABLE
// ============================================================
//
// +------------------+----------+-----------+-------+-----------+
// | Algorithm        | Best     | Worst     | Space | Requires  |
// +------------------+----------+-----------+-------+-----------+
// | Linear search    | O(1)     | O(n)      | O(1)  | Nothing   |
// | Binary search    | O(1)     | O(log n)  | O(1)  | Sorted    |
// | Jump search      | O(1)     | O(sqrt n) | O(1)  | Sorted    |
// | Interpolation    | O(1)     | O(n)      | O(1)  | Sorted+   |
// |                  |          |           |       | uniform   |
// | Two-pointer      | O(n)     | O(n)      | O(1)  | Sorted*   |
// | Sliding window   | O(n)     | O(n)      | O(1)  | Contiguous|
// +------------------+----------+-----------+-------+-----------+
// * Two-pointer often needs sorted input, but not always.

// ============================================================
// 1. LINEAR SEARCH                                   [BASIC]
// ============================================================
// Walk through every element. Works on any array (sorted or not).
//
//  arr: [-5, 2, 10, 4, 6]   target: 10
//        ^  ^   ^
//  idx:  0  1   2  <-- found! return 2
//
// Time: O(n)  |  Space: O(1)

function linearSearch(arr, target) {
    for (let i = 0; i < arr.length; i++) {
        if (arr[i] === target) return i;
    }
    return -1;
}

console.log(linearSearch([-5, 2, 10, 4, 6], 10));  // 2
console.log(linearSearch([-5, 2, 10, 4, 6], 6));   // 4
console.log(linearSearch([-5, 2, 10, 4, 6], 20));  // -1

// GOTCHAS:
// - Use for small or unsorted arrays; never for sorted data.
// - Array.indexOf() and Array.includes() are linear searches.

// ============================================================
// 2. BINARY SEARCH (ITERATIVE)                       [BASIC]
// ============================================================
// PREREQUISITE: Array MUST be sorted.
// Halve the search space each step.
//
//  arr: [-5, 2, 4, 6, 10]   target: 6
//        L        M      R      M=arr[2]=4, 4<6 => L=M+1
//                    L  M  R    M=arr[3]=6 => found! return 3
//
//  Step-by-step diagram:
//  +----+---+---+---+----+
//  | -5 | 2 | 4 | 6 | 10 |
//  +----+---+---+---+----+
//    L         M        R     arr[2]=4 < 6 => move L right
//  +----+---+---+---+----+
//  | -5 | 2 | 4 | 6 | 10 |
//  +----+---+---+---+----+
//                L  M    R    arr[3]=6 === 6 => FOUND at index 3
//
// Time: O(log n)  |  Space: O(1)
// INTERVIEW: Classic. Know this cold.

function binarySearch(arr, target) {
    let left = 0;
    let right = arr.length - 1;

    while (left <= right) {
        let mid = Math.floor((left + right) / 2);
        if (target === arr[mid]) return mid;
        if (target < arr[mid]) right = mid - 1;
        else left = mid + 1;
    }
    return -1;
}

console.log(binarySearch([-5, 2, 4, 6, 10], 10)); // 4
console.log(binarySearch([-5, 2, 4, 6, 10], 6));  // 3
console.log(binarySearch([-5, 2, 4, 6, 10], 20)); // -1

// ============================================================
// 3. BINARY SEARCH (RECURSIVE)               [INTERMEDIATE]
// ============================================================
// Same logic, expressed recursively. Base case: left > right.
//
// Time: O(log n)  |  Space: O(log n) -- call stack

function recursiveBinarySearch(arr, target) {
    return bsHelper(arr, target, 0, arr.length - 1);
}

function bsHelper(arr, target, left, right) {
    if (left > right) return -1;
    let mid = Math.floor((left + right) / 2);
    if (target === arr[mid]) return mid;
    if (target < arr[mid]) return bsHelper(arr, target, left, mid - 1);
    return bsHelper(arr, target, mid + 1, right);
}

console.log(recursiveBinarySearch([-5, 2, 4, 6, 10], 10)); // 4
console.log(recursiveBinarySearch([-5, 2, 4, 6, 10], 6));  // 3
console.log(recursiveBinarySearch([-5, 2, 4, 6, 10], 20)); // -1

// ============================================================
// 4. JUMP SEARCH                             [INTERMEDIATE]
// ============================================================
// Jump ahead by sqrt(n) blocks, then linear search within block.
// A middle ground between linear and binary search.
//
//  arr: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]   target: 7  step=3
//        ^--------^                         jump: 0->3
//                  ^--------^               jump: 3->6
//                            ^--------^     jump: 6->9, arr[9]=9>7
//                            ^  ^  ^        linear back from 6: found at 7
//
// Time: O(sqrt n)  |  Space: O(1)

function jumpSearch(arr, target) {
    const n = arr.length;
    const step = Math.floor(Math.sqrt(n));
    let prev = 0;
    let curr = step;

    // Jump ahead until we pass the target or reach the end
    while (curr < n && arr[curr] < target) {
        prev = curr;
        curr += step;
    }

    // Linear search within the block [prev, min(curr, n-1)]
    for (let i = prev; i <= Math.min(curr, n - 1); i++) {
        if (arr[i] === target) return i;
    }
    return -1;
}

console.log(jumpSearch([0, 1, 2, 3, 4, 5, 6, 7, 8, 9], 7)); // 7
console.log(jumpSearch([0, 1, 2, 3, 4, 5, 6, 7, 8, 9], 0)); // 0
console.log(jumpSearch([0, 1, 2, 3, 4, 5, 6, 7, 8, 9], 11)); // -1

// GOTCHAS:
// - Array must be sorted.
// - Optimal step size is sqrt(n).
// - Slightly worse than binary search but simpler for linked lists
//   where you can only move forward.

// ============================================================
// 5. INTERPOLATION SEARCH                    [ADVANCED]
// ============================================================
// Like binary search but estimates position using value distribution.
// Works best on UNIFORMLY distributed, sorted data.
//
// Instead of mid = (lo + hi) / 2, we compute:
//   pos = lo + ((target - arr[lo]) * (hi - lo)) / (arr[hi] - arr[lo])
//
// Time: O(log log n) avg for uniform data | O(n) worst
// Space: O(1)
// INTERVIEW: Rarely asked to code, but mention as an optimization.

function interpolationSearch(arr, target) {
    let lo = 0;
    let hi = arr.length - 1;

    while (lo <= hi && target >= arr[lo] && target <= arr[hi]) {
        if (lo === hi) {
            return arr[lo] === target ? lo : -1;
        }
        let pos = lo + Math.floor(
            ((target - arr[lo]) * (hi - lo)) / (arr[hi] - arr[lo])
        );
        if (arr[pos] === target) return pos;
        if (arr[pos] < target) lo = pos + 1;
        else hi = pos - 1;
    }
    return -1;
}

console.log(interpolationSearch([10, 20, 30, 40, 50, 60, 70], 40)); // 3
console.log(interpolationSearch([10, 20, 30, 40, 50, 60, 70], 15)); // -1

// ============================================================
// 6. TWO-POINTER TECHNIQUE                   [INTERMEDIATE]
// ============================================================
// Use two pointers (often from opposite ends) to search or
// partition in O(n) instead of O(n^2).
//
// INTERVIEW: Extremely common. Two Sum (sorted), Container
// With Most Water, Remove Duplicates, Valid Palindrome.
//
// Pattern: sorted array + pair that meets condition
//
//  arr: [1, 2, 3, 4, 6]   target: 6
//        L              R     1+6=7 > 6 => R--
//        L           R        1+4=5 < 6 => L++
//           L        R        2+4=6 => FOUND [1,3]
//
// Time: O(n)  |  Space: O(1)

// --- Two Sum (sorted) ---
function twoSumSorted(arr, target) {
    let left = 0;
    let right = arr.length - 1;

    while (left < right) {
        const sum = arr[left] + arr[right];
        if (sum === target) return [left, right];
        if (sum < target) left++;
        else right--;
    }
    return null;
}

console.log(twoSumSorted([1, 2, 3, 4, 6], 6)); // [1, 3]  (indices of 2,4)
console.log(twoSumSorted([1, 2, 3, 4, 6], 20)); // null

// --- Remove duplicates in-place (sorted) ---
// Returns new length. Modifies array in-place.
function removeDuplicatesSorted(arr) {
    if (arr.length === 0) return 0;
    let slow = 0;
    for (let fast = 1; fast < arr.length; fast++) {
        if (arr[fast] !== arr[slow]) {
            slow++;
            arr[slow] = arr[fast];
        }
    }
    return slow + 1;
}

const dupArr = [1, 1, 2, 2, 3, 4, 4, 5];
console.log(removeDuplicatesSorted(dupArr)); // 5 (unique: 1,2,3,4,5)

// --- Valid Palindrome (two-pointer) ---
function isPalindrome(s) {
    const clean = s.toLowerCase().replace(/[^a-z0-9]/g, '');
    let l = 0, r = clean.length - 1;
    while (l < r) {
        if (clean[l] !== clean[r]) return false;
        l++; r--;
    }
    return true;
}

console.log(isPalindrome("A man, a plan, a canal: Panama")); // true
console.log(isPalindrome("hello")); // false

// GOTCHAS:
// - Two-pointer on unsorted array? Sort first (adds O(n log n)).
// - For unsorted Two Sum, use a hash map instead: O(n) time, O(n) space.
// - Watch out for duplicates -- you may need to skip them.

// ============================================================
// 7. SLIDING WINDOW TECHNIQUE                [INTERMEDIATE]
// ============================================================
// Maintain a "window" (subarray) that slides across the array.
// Avoids recomputing the entire window from scratch each step.
//
// Pattern: contiguous subarray/substring of size k (or variable).
//
// INTERVIEW: Maximum sum subarray of size k, longest substring
// without repeating characters, minimum window substring.
//
//  arr: [2, 1, 5, 1, 3, 2]   k=3   find max sum of k elements
//
//  window -->
//  [2, 1, 5] 1  3  2     sum=8
//   2 [1, 5, 1] 3  2     sum=7   (subtract 2, add 1)
//   2  1 [5, 1, 3] 2     sum=9   (subtract 1, add 3) <-- max
//   2  1  5 [1, 3, 2]    sum=6   (subtract 5, add 2)
//                         answer: 9
//
// Time: O(n)  |  Space: O(1)

// --- Fixed-size window: max sum of k consecutive elements ---
function maxSumSubarray(arr, k) {
    if (arr.length < k) return null;

    let windowSum = 0;
    for (let i = 0; i < k; i++) windowSum += arr[i]; // first window

    let maxSum = windowSum;
    for (let i = k; i < arr.length; i++) {
        windowSum += arr[i] - arr[i - k]; // slide: add right, remove left
        maxSum = Math.max(maxSum, windowSum);
    }
    return maxSum;
}

console.log(maxSumSubarray([2, 1, 5, 1, 3, 2], 3)); // 9
console.log(maxSumSubarray([4, 2, 1, 7, 8, 1, 2, 8, 1, 0], 3)); // 16

// --- Variable-size window: longest substring without repeating chars ---
// INTERVIEW: LeetCode #3 -- top 5 most-asked string problem.
function longestUniqueSubstring(s) {
    const seen = new Map(); // char -> last index
    let maxLen = 0;
    let start = 0;

    for (let end = 0; end < s.length; end++) {
        if (seen.has(s[end]) && seen.get(s[end]) >= start) {
            start = seen.get(s[end]) + 1; // shrink window
        }
        seen.set(s[end], end);
        maxLen = Math.max(maxLen, end - start + 1);
    }
    return maxLen;
}

console.log(longestUniqueSubstring("abcabcbb")); // 3  ("abc")
console.log(longestUniqueSubstring("bbbbb"));    // 1  ("b")
console.log(longestUniqueSubstring("pwwkew"));   // 3  ("wke")

// --- Variable-size window: smallest subarray with sum >= target ---
function minSubarrayLen(target, arr) {
    let minLen = Infinity;
    let sum = 0;
    let start = 0;

    for (let end = 0; end < arr.length; end++) {
        sum += arr[end];
        while (sum >= target) {
            minLen = Math.min(minLen, end - start + 1);
            sum -= arr[start];
            start++;
        }
    }
    return minLen === Infinity ? 0 : minLen;
}

console.log(minSubarrayLen(7, [2, 3, 1, 2, 4, 3])); // 2 ([4,3])
console.log(minSubarrayLen(100, [1, 2, 3]));          // 0

// GOTCHAS:
// - Fixed window: always size k. Variable window: expand right,
//   shrink left based on condition.
// - Don't confuse with two-pointer. Sliding window is a subset
//   where both pointers move in the SAME direction.
// - Hash maps (Map/Set) are often used inside the window for
//   character frequency / uniqueness tracking.

// ============================================================
// 8. SEARCH DECISION TREE                    [INTERVIEW TIP]
// ============================================================
//
//  Is the data sorted?
//  |
//  +-- NO  --> Linear search O(n)
//  |           or use a Hash Set for O(1) lookup
//  |
//  +-- YES --> Is random access available?
//              |
//              +-- YES --> Binary search O(log n)
//              |           Data uniformly distributed?
//              |           +-- YES --> Interpolation O(log log n)
//              |
//              +-- NO  --> Jump search O(sqrt n)
//                          (e.g., linked list)
//
//  Need to find a pair / subarray?
//  +-- Pair with sum = target  --> Two-pointer (sorted) or Hash map
//  +-- Contiguous subarray     --> Sliding window

// ============================================================
// GOTCHAS SUMMARY
// ============================================================
// 1. Binary search: off-by-one errors. Use left <= right and
//    mid-1 / mid+1. Never use left < right unless you understand
//    the invariant change.
// 2. Binary search: integer overflow with (left + right) / 2 in
//    other languages. In JS, numbers are 64-bit floats so this
//    is not an issue, but left + Math.floor((right - left) / 2)
//    is still a good habit.
// 3. Sliding window: remember to shrink the window (move start)
//    when the condition is violated.
// 4. Two-pointer: only works for PAIR problems on sorted data.
//    For unsorted, sort first or use a hash map.
