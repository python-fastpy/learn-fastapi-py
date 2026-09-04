/* ============================================================================
 * CODING PROBLEMS — INTERMEDIATE  [INTERMEDIATE]
 * ============================================================================
 * Every solution includes Time/Space complexity.
 * Multiple approaches shown where applicable.
 * ==========================================================================*/

// ============================================================
// 19. TWO SUM                                [INTERMEDIATE]
// ============================================================
// INTERVIEW: LeetCode #1 -- the most-asked interview question.
//
// Approach 1: Brute force  -- Time: O(n^2)  |  Space: O(1)
function twoSumBrute(arr, target) {
    for (let i = 0; i < arr.length; i++) {
        for (let j = i + 1; j < arr.length; j++) {
            if (arr[i] + arr[j] === target) return [i, j];
        }
    }
    return null;
}

// Approach 2: Hash map (optimal)  -- Time: O(n)  |  Space: O(n)
function twoSum(arr, target) {
    const map = new Map();
    for (let i = 0; i < arr.length; i++) {
        const complement = target - arr[i];
        if (map.has(complement)) return [map.get(complement), i];
        map.set(arr[i], i);
    }
    return null;
}

console.log(twoSum([2, 7, 11, 15], 9)); // [0, 1]

// ============================================================
// 20. THREE SUM                              [INTERMEDIATE]
// ============================================================
// Find all unique triplets that sum to 0.
// INTERVIEW: Follow-up to Two Sum. Tests sorting + two-pointer.
//
// Approach 1: Brute force  -- Time: O(n^3)  |  Space: O(1)
// Approach 2: Sort + two-pointer  -- Time: O(n^2)  |  Space: O(1)

function threeSum(nums) {
    nums.sort((a, b) => a - b);
    const result = [];

    for (let i = 0; i < nums.length - 2; i++) {
        if (i > 0 && nums[i] === nums[i - 1]) continue; // skip duplicates

        let left = i + 1, right = nums.length - 1;
        while (left < right) {
            const sum = nums[i] + nums[left] + nums[right];
            if (sum === 0) {
                result.push([nums[i], nums[left], nums[right]]);
                while (left < right && nums[left] === nums[left + 1]) left++;
                while (left < right && nums[right] === nums[right - 1]) right--;
                left++; right--;
            } else if (sum < 0) left++;
            else right--;
        }
    }
    return result;
}

console.log(threeSum([-1, 0, 1, 2, -1, -4])); // [[-1,-1,2],[-1,0,1]]

// ============================================================
// 21. VALID PARENTHESES (Stack)              [INTERMEDIATE]
// ============================================================
// INTERVIEW: Top 10 most-asked. Tests stack data structure.
//
//  Input: "({[]})"  =>  true
//  Input: "({[}])"  =>  false
//
//  Stack trace for "({[]})":
//  char (  => push  stack: [(]
//  char {  => push  stack: [(, {]
//  char [  => push  stack: [(, {, []
//  char ]  => pop [ matches  stack: [(, {]
//  char }  => pop { matches  stack: [(]
//  char )  => pop ( matches  stack: []   <-- empty => VALID
//
// Time: O(n)  |  Space: O(n)

function isValidParens(s) {
    const stack = [];
    const pairs = { ')': '(', '}': '{', ']': '[' };

    for (const c of s) {
        if ('({['.includes(c)) {
            stack.push(c);
        } else {
            if (stack.pop() !== pairs[c]) return false;
        }
    }
    return stack.length === 0;
}

console.log(isValidParens("({[]})")); // true
console.log(isValidParens("({[}])")); // false
console.log(isValidParens("("));      // false

// GOTCHAS:
// - Don't forget to check stack.length === 0 at the end.
//   "((" would otherwise pass.
// - Only push opening brackets. Pop on closing brackets.

// ============================================================
// 22. KADANE'S ALGORITHM (Maximum Subarray)  [INTERMEDIATE]
// ============================================================
// INTERVIEW: LeetCode #53 -- classic DP / greedy problem.
//
// Find contiguous subarray with the largest sum.
//
//  arr: [-2, 1, -3, 4, -1, 2, 1, -5, 4]
//
//  Walk through:
//  idx  val  currentMax  globalMax
//   0   -2      -2          -2
//   1    1       1           1    (restart from 1, better than -2+1)
//   2   -3      -2           1
//   3    4       4           4    (restart from 4)
//   4   -1       3           4
//   5    2       5           5
//   6    1       6           6    <-- answer! subarray [4,-1,2,1]
//   7   -5       1           6
//   8    4       5           6
//
// Time: O(n)  |  Space: O(1)

function maxSubArray(arr) {
    let currentMax = arr[0];
    let globalMax = arr[0];

    for (let i = 1; i < arr.length; i++) {
        currentMax = Math.max(arr[i], currentMax + arr[i]);
        globalMax = Math.max(globalMax, currentMax);
    }
    return globalMax;
}

console.log(maxSubArray([-2, 1, -3, 4, -1, 2, 1, -5, 4])); // 6

// GOTCHAS:
// - Handles all-negative arrays correctly (returns least negative).
// - The key insight: at each step, either extend the current
//   subarray or start fresh from current element.

// ============================================================
// 23. SLIDING WINDOW PROBLEMS                [INTERMEDIATE]
// ============================================================

// --- Max sum of k consecutive elements ---
// Time: O(n)  |  Space: O(1)
function maxSumK(arr, k) {
    let windowSum = 0;
    for (let i = 0; i < k; i++) windowSum += arr[i];
    let maxSum = windowSum;
    for (let i = k; i < arr.length; i++) {
        windowSum += arr[i] - arr[i - k];
        maxSum = Math.max(maxSum, windowSum);
    }
    return maxSum;
}

console.log(maxSumK([2, 1, 5, 1, 3, 2], 3)); // 9

// --- Longest substring without repeating chars (LeetCode #3) ---
// Time: O(n)  |  Space: O(min(n, alphabet))
function lengthOfLongestSubstring(s) {
    const seen = new Map();
    let maxLen = 0, start = 0;
    for (let end = 0; end < s.length; end++) {
        if (seen.has(s[end]) && seen.get(s[end]) >= start) {
            start = seen.get(s[end]) + 1;
        }
        seen.set(s[end], end);
        maxLen = Math.max(maxLen, end - start + 1);
    }
    return maxLen;
}

console.log(lengthOfLongestSubstring("abcabcbb")); // 3

// ============================================================
// 24. TWO-POINTER PROBLEMS                   [INTERMEDIATE]
// ============================================================

// --- Container With Most Water (LeetCode #11) ---
// INTERVIEW: Tests greedy + two-pointer.
//
//  height: [1, 8, 6, 2, 5, 4, 8, 3, 7]
//
//  |        |              |
//  |        |  |           |
//  |        |  |     |  |  |
//  |        |  |     |  |  |  |
//  |        |  |  |  |  |  |  |
//  |        |  |  |  |  |  |  |
//  |  |     |  |  |  |  |  |  |
//  |  |  |  |  |  |  |  |  |  |
//  1  8  6  2  5  4  8  3  7
//  L                       R  => area = min(1,7)*8 = 8
//     L                    R  => area = min(8,7)*7 = 49 <-- answer
//
// Time: O(n)  |  Space: O(1)

function maxArea(height) {
    let left = 0, right = height.length - 1, max = 0;
    while (left < right) {
        const area = Math.min(height[left], height[right]) * (right - left);
        max = Math.max(max, area);
        if (height[left] < height[right]) left++;
        else right--;
    }
    return max;
}

console.log(maxArea([1, 8, 6, 2, 5, 4, 8, 3, 7])); // 49

// --- Move Zeroes (LeetCode #283) ---
// Move all 0s to end, keep relative order of non-zero elements.
// Time: O(n)  |  Space: O(1)

function moveZeroes(arr) {
    let insertPos = 0;
    for (let i = 0; i < arr.length; i++) {
        if (arr[i] !== 0) {
            [arr[insertPos], arr[i]] = [arr[i], arr[insertPos]];
            insertPos++;
        }
    }
    return arr;
}

console.log(moveZeroes([0, 1, 0, 3, 12])); // [1, 3, 12, 0, 0]

// ============================================================
// 25. STACK-BASED PROBLEMS                   [INTERMEDIATE]
// ============================================================

// --- Min Stack (LeetCode #155) ---
// Stack that supports push, pop, top, and getMin in O(1).
// INTERVIEW: Tests auxiliary data structure design.
// Time: O(1) all operations  |  Space: O(n)

class MinStack {
    constructor() {
        this.stack = [];
        this.minStack = []; // tracks minimum at each level
    }
    push(val) {
        this.stack.push(val);
        const min = this.minStack.length === 0
            ? val
            : Math.min(val, this.minStack[this.minStack.length - 1]);
        this.minStack.push(min);
    }
    pop() {
        this.stack.pop();
        this.minStack.pop();
    }
    top() { return this.stack[this.stack.length - 1]; }
    getMin() { return this.minStack[this.minStack.length - 1]; }
}

const ms = new MinStack();
ms.push(3); ms.push(5); ms.push(2); ms.push(1);
console.log(ms.getMin()); // 1
ms.pop();
console.log(ms.getMin()); // 2

// --- Daily Temperatures (LeetCode #739) ---
// Given temperatures, find how many days until a warmer day.
// Uses a monotonic decreasing stack.
// Time: O(n)  |  Space: O(n)

function dailyTemperatures(temps) {
    const result = new Array(temps.length).fill(0);
    const stack = []; // stores indices

    for (let i = 0; i < temps.length; i++) {
        while (stack.length && temps[i] > temps[stack[stack.length - 1]]) {
            const idx = stack.pop();
            result[idx] = i - idx;
        }
        stack.push(i);
    }
    return result;
}

console.log(dailyTemperatures([73, 74, 75, 71, 69, 72, 76, 73]));
// [1, 1, 4, 2, 1, 1, 0, 0]

// ============================================================
// 26. STRING PATTERN MATCHING                [INTERMEDIATE]
// ============================================================

// --- Is Subsequence (LeetCode #392) ---
// Is "ace" a subsequence of "abcde"?   Yes (a_c_e)
// Time: O(n)  |  Space: O(1)

function isSubsequence(s, t) {
    let si = 0;
    for (let ti = 0; ti < t.length && si < s.length; ti++) {
        if (s[si] === t[ti]) si++;
    }
    return si === s.length;
}

console.log(isSubsequence("ace", "abcde")); // true
console.log(isSubsequence("aec", "abcde")); // false

// --- Count Substrings Containing a Character ---
// Time: O(n^2)  |  Space: O(1)

function countSubStringsWithChar(str, char) {
    let count = 0;
    for (let i = 0; i < str.length; i++) {
        for (let j = i + 1; j <= str.length; j++) {
            if (str.slice(i, j).includes(char)) count++;
        }
    }
    return count;
}

console.log(countSubStringsWithChar('abb', 'b')); // 5
