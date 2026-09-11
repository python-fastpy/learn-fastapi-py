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

// TRACE: linearSearch([-5, 2, 10, 4, 6], 10) -- input arr[i] checked one by one
// | step | i | arr[i] | arr[i] === target? | action        |
// |------|---|--------|---------------------|---------------|
// |  1   | 0 |   -5   | -5 === 10? no       | i++           |
// |  2   | 1 |    2   |  2 === 10? no       | i++           |
// |  3   | 2 |   10   | 10 === 10? YES      | return i (=2) |
// OUTPUT: 2

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

// TRACE: binarySearch([-5, 2, 4, 6, 10], 6) -- input passed in, halved each step
// | step | left | right | mid | arr[mid] | comparison         | action        |
// |------|------|-------|-----|----------|--------------------|---------------|
// |  1   |  0   |   4   |  2  |    4     | 4 < 6              | left = mid+1=3|
// |  2   |  3   |   4   |  3  |    6     | 6 === 6, FOUND     | return mid(=3)|
// OUTPUT: 3
// Notice: only 2 steps for 5 elements -- that's the O(log n) halving in action.

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

// TRACE: recursiveBinarySearch([-5, 2, 4, 6, 10], 6) -- each call is a stack frame
// | call depth | left | right | mid | arr[mid] | action                        |
// |------------|------|-------|-----|----------|-------------------------------|
// | bsHelper #1|  0   |   4   |  2  |    4     | 4 < 6 -> call bsHelper(3, 4)  |
// |   bsHelper #2|  3   |   4   |  3  |    6     | 6===6 -> return 3 (base case)|
// call #1 receives 3 from call #2 and returns 3 up the chain.
// OUTPUT: 3
// Compare to the ITERATIVE trace above -- same left/mid/right values, but here
// each row is a NEW function call sitting on the call stack (see DSA/05-stacks.js
// "Call Stack Visualization"), instead of one loop reusing the same variables.

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

// TRACE: jumpSearch([0..9], 7) -- step = floor(sqrt(10)) = 3
// PHASE 1 -- jump in blocks of 3, looking for the first block that overshoots:
// | prev | curr | arr[curr] | arr[curr] < 7? | action          |
// |------|------|-----------|-----------------|-----------------|
// |  0   |  3   |     3     | yes             | prev=3, curr=6  |
// |  3   |  6   |     6     | yes             | prev=6, curr=9  |
// |  6   |  9   |     9     | no (9 >= 7)     | STOP jumping    |
// PHASE 2 -- linear search inside the block [prev=6, min(curr,n-1)=9]:
// | i | arr[i] | arr[i] === 7? | action        |
// |---|--------|----------------|---------------|
// | 6 |   6    | no             | i++           |
// | 7 |   7    | YES            | return i (=7) |
// OUTPUT: 7

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

// TRACE: interpolationSearch([10,20,30,40,50,60,70], 40) -- estimates position
// instead of blindly halving:
// | step | lo | hi | pos formula                                      | pos | arr[pos] |
// |------|----|----|---------------------------------------------------|-----|----------|
// |  1   | 0  | 6  | 0 + floor((40-10)*(6-0)/(70-10)) = floor(180/60)=3 |  3  |    40    |
// arr[3] === 40 -> FOUND immediately, in exactly 1 step (vs binary search's 2-3
// steps) because the data is uniformly spaced and the formula "guesses" the
// exact slot instead of always guessing the middle.
// OUTPUT: 3

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

// TRACE: twoSumSorted([1,2,3,4,6], 6) -- pointers close in from both ends
// | step | left | right | arr[left] | arr[right] | sum | vs target | action     |
// |------|------|-------|-----------|------------|-----|-----------|------------|
// |  1   |  0   |   4   |     1     |     6      |  7  | 7 > 6     | right--    |
// |  2   |  0   |   3   |     1     |     4      |  5  | 5 < 6     | left++     |
// |  3   |  1   |   3   |     2     |     4      |  6  | 6 === 6   | return [1,3]|
// OUTPUT: [1, 3]

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

// TRACE: removeDuplicatesSorted([1,1,2,2,3,4,4,5]) -- slow marks the last unique
// slot written so far; fast scans ahead looking for the next NEW value.
// | fast | arr[fast] | arr[slow] | different? | action                | array after step        |
// |------|-----------|-----------|------------|-----------------------|--------------------------|
// |  1   |     1     |  1 (idx0) | no         | skip                  | [1,1,2,2,3,4,4,5]        |
// |  2   |     2     |  1 (idx0) | YES        | slow=1; arr[1]=2      | [1,2,2,2,3,4,4,5]        |
// |  3   |     2     |  2 (idx1) | no         | skip                  | [1,2,2,2,3,4,4,5]        |
// |  4   |     3     |  2 (idx1) | YES        | slow=2; arr[2]=3      | [1,2,3,2,3,4,4,5]        |
// |  5   |     4     |  3 (idx2) | YES        | slow=3; arr[3]=4      | [1,2,3,4,3,4,4,5]        |
// |  6   |     4     |  4 (idx3) | no         | skip                  | [1,2,3,4,3,4,4,5]        |
// |  7   |     5     |  4 (idx3) | YES        | slow=4; arr[4]=5      | [1,2,3,4,5,4,4,5]        |
// return slow+1 = 5 -- the first 5 slots [1,2,3,4,5] are now the unique values;
// anything past index 4 is leftover junk the caller should ignore.
// OUTPUT: 5

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

// TRACE: isPalindrome("A man, a plan, a canal: Panama")
// Step 0 (before the loop): clean the string first --
//   "A man, a plan, a canal: Panama" --> lowercase + strip non-alphanumeric -->
//   "amanaplanacanalpanama"  (21 characters, indices 0..20)
// | step | l | r  | clean[l] | clean[r] | equal? | action |
// |------|---|----|----------|----------|--------|--------|
// |  1   | 0 | 20 |    a     |    a     | yes    | l++ r--|
// |  2   | 1 | 19 |    m     |    m     | yes    | l++ r--|
// |  3   | 2 | 18 |    a     |    a     | yes    | l++ r--|
// | ...  |...| ...|   ...    |   ...    | ...    | (continues symmetrically) |
// |  10  | 9 | 11 |    a     |    a     | yes    | l++ r--|
// loop ends when l >= r (l=10, r=10) -- every pair matched, nothing returned false
// OUTPUT: true

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

// TRACE: maxSumSubarray([2,1,5,1,3,2], 3) -- window slides right by 1 each step,
// reusing the previous sum instead of re-adding all 3 elements from scratch.
// Setup: first window = arr[0..2] = [2,1,5] -> windowSum = 2+1+5 = 8, maxSum = 8
// | i (new right edge) | leaving (arr[i-k]) | entering (arr[i]) | windowSum = old + enter - leave | maxSum |
// |---------------------|---------------------|--------------------|-----------------------------------|--------|
// |          3          |     arr[0]=2        |      arr[3]=1      | 8 + 1 - 2 = 7                      |   8    |
// |          4          |     arr[1]=1        |      arr[4]=3      | 7 + 3 - 1 = 9                      |   9    |
// |          5          |     arr[2]=5        |      arr[5]=2      | 9 + 2 - 5 = 6                      |   9    |
// OUTPUT: 9  (best window was arr[2..4] = [5,1,3], reached when i=4 above)

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

// TRACE: longestUniqueSubstring("abcabcbb") -- this is the trickiest trace in
// this file: `start` only jumps forward when a REPEAT is seen INSIDE the
// current window (checked via `seen.get(char) >= start`, not just "seen before").
// | end | char | seen.get(char) | >= start? | start after | seen map after      | maxLen |
// |-----|------|-----------------|-----------|-------------|---------------------|--------|
// |  0  |  a   |    (none)       |    --     |     0       | {a:0}               |   1    |
// |  1  |  b   |    (none)       |    --     |     0       | {a:0,b:1}           |   2    |
// |  2  |  c   |    (none)       |    --     |     0       | {a:0,b:1,c:2}       |   3    |
// |  3  |  a   |       0         |  0>=0 yes | 1 (=0+1)    | {a:3,b:1,c:2}       |   3    |
// |  4  |  b   |       1         |  1>=1 yes | 2 (=1+1)    | {a:3,b:4,c:2}       |   3    |
// |  5  |  c   |       2         |  2>=2 yes | 3 (=2+1)    | {a:3,b:4,c:5}       |   3    |
// |  6  |  b   |       4         |  4>=3 yes | 5 (=4+1)    | {a:3,b:6,c:5}       |   3    |
// |  7  |  b   |       6         |  6>=5 yes | 7 (=6+1)    | {a:3,b:7,c:5}       |   3    |
// maxLen never beats 3 again after end=2 -- the window [a,b,c] (end=0..2) was
// the longest unique run in the whole string.
// OUTPUT: 3

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

// TRACE: minSubarrayLen(7, [2,3,1,2,4,3]) -- expand `end` one step at a time;
// whenever sum >= target, the INNER while shrinks `start` as much as possible
// before moving `end` again (that inner loop is what makes this "sliding").
// | end | sum after += arr[end] | >= 7? | inner while (start -> sum, minLen)         |
// |-----|------------------------|-------|----------------------------------------------|
// |  0  |         2              |  no   | (skipped)                                     |
// |  1  |         5              |  no   | (skipped)                                     |
// |  2  |         6              |  no   | (skipped)                                     |
// |  3  |         8              |  yes  | minLen=4; sum-=2->6,start=1; 6>=7? no, stop    |
// |  4  |        10              |  yes  | minLen=4; sum-=3->7,start=2; 7>=7? yes ->      |
// |     |                        |       |   minLen=3; sum-=1->6,start=3; 6>=7? no, stop  |
// |  5  |         9              |  yes  | minLen=3; sum-=2->7,start=4; 7>=7? yes ->      |
// |     |                        |       |   minLen=2; sum-=4->3,start=5; 3>=7? no, stop  |
// final minLen = 2 -- that's the window arr[4..5] = [4,3], which sums to 7.
// OUTPUT: 2

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
