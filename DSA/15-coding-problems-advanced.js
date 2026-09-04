/* ============================================================================
 * CODING PROBLEMS — ADVANCED  [ADVANCED]
 * ============================================================================
 * Every solution includes Time/Space complexity.
 * Multiple approaches shown where applicable.
 * ==========================================================================*/

// ============================================================
// 27. DYNAMIC PROGRAMMING: CLIMBING STAIRS   [ADVANCED]
// ============================================================
// INTERVIEW: Classic DP intro problem (LeetCode #70).
// You can climb 1 or 2 steps. How many ways to reach step n?
//
//  n=1: 1 way   (1)
//  n=2: 2 ways  (1+1, 2)
//  n=3: 3 ways  (1+1+1, 1+2, 2+1)
//  n=4: 5 ways  (1+1+1+1, 1+1+2, 1+2+1, 2+1+1, 2+2)
//
// Pattern: dp[i] = dp[i-1] + dp[i-2]  (Fibonacci!)
//
//  Recursion tree (without memo) for n=5:
//                  f(5)
//                /      \
//            f(4)        f(3)
//           /    \      /    \
//        f(3)   f(2)  f(2)  f(1)    <-- overlapping subproblems!
//       / \
//    f(2) f(1)
//
// Approach 1: Recursive (slow) -- Time: O(2^n) | Space: O(n) stack
// Approach 2: DP with memo     -- Time: O(n)   | Space: O(n)
// Approach 3: Bottom-up (best) -- Time: O(n)   | Space: O(1)

function climbStairs(n) {
    if (n <= 2) return n;
    let prev2 = 1, prev1 = 2;
    for (let i = 3; i <= n; i++) {
        const curr = prev1 + prev2;
        prev2 = prev1;
        prev1 = curr;
    }
    return prev1;
}

console.log(climbStairs(4)); // 5
console.log(climbStairs(5)); // 8

// ============================================================
// 28. DYNAMIC PROGRAMMING: COIN CHANGE      [ADVANCED]
// ============================================================
// INTERVIEW: LeetCode #322. Classic DP problem.
// Given coins and an amount, find the fewest coins needed.
//
//  coins = [1, 5, 11]   amount = 15
//
//  dp table (min coins for each amount):
//  amt:  0  1  2  3  4  5  6  7  8  9  10  11  12  13  14  15
//  dp:   0  1  2  3  4  1  2  3  4  5   2   1   2   3   4   3
//                        ^               ^   ^               ^
//                       5c             5+5  11c            answer=3 (5+5+5)
//
// Time: O(amount * coins.length)  |  Space: O(amount)

function coinChange(coins, amount) {
    const dp = new Array(amount + 1).fill(Infinity);
    dp[0] = 0;

    for (let i = 1; i <= amount; i++) {
        for (const coin of coins) {
            if (coin <= i && dp[i - coin] + 1 < dp[i]) {
                dp[i] = dp[i - coin] + 1;
            }
        }
    }
    return dp[amount] === Infinity ? -1 : dp[amount];
}

console.log(coinChange([1, 5, 11], 15)); // 3  (5+5+5)
console.log(coinChange([2], 3));          // -1

// GOTCHAS:
// - Greedy (always pick largest coin) does NOT work here.
//   coins=[1,5,11] amount=15: greedy picks 11+1+1+1+1=5 coins,
//   but optimal is 5+5+5=3 coins.

// ============================================================
// 29. DYNAMIC PROGRAMMING: HOUSE ROBBER     [ADVANCED]
// ============================================================
// INTERVIEW: LeetCode #198. Can't rob adjacent houses.
//
//  houses: [2, 7, 9, 3, 1]
//           ^     ^        = 2+9+1 = 12? No...
//              ^     ^     = 7+3 = 10
//           ^     ^     ^  = 2+9+1 = 12  <-- answer
//
// dp[i] = max(dp[i-1], dp[i-2] + nums[i])
//
// Time: O(n)  |  Space: O(1)

function rob(nums) {
    let prev2 = 0, prev1 = 0;
    for (const num of nums) {
        const curr = Math.max(prev1, prev2 + num);
        prev2 = prev1;
        prev1 = curr;
    }
    return prev1;
}

console.log(rob([2, 7, 9, 3, 1])); // 12
console.log(rob([1, 2, 3, 1]));     // 4

// ============================================================
// 30. SORT STRING WITHOUT BUILT-IN                   [BASIC]
// ============================================================
// Uses bubble sort on characters.
// Time: O(n^2)  |  Space: O(n)

function sortString(value) {
    const chars = value.split("");
    let swapped;
    do {
        swapped = false;
        for (let i = 0; i < chars.length - 1; i++) {
            if (chars[i] > chars[i + 1]) {
                [chars[i], chars[i + 1]] = [chars[i + 1], chars[i]];
                swapped = true;
            }
        }
    } while (swapped);
    return chars.join("");
}

console.log(sortString("dcba")); // "abcd"

// ============================================================
// 31. ROTATE / REVERSE ARRAY                         [BASIC]
// ============================================================
// Reverse in-place with two pointers.
// Time: O(n)  |  Space: O(1)

function reverseArray(arr) {
    let l = 0, r = arr.length - 1;
    while (l < r) {
        [arr[l], arr[r]] = [arr[r], arr[l]];
        l++; r--;
    }
    return arr;
}

console.log(reverseArray([1, 3, 6, 5, 4])); // [4, 5, 6, 3, 1]

// ============================================================
// 32. COMPARE TWO OBJECTS (CONTAINS CHECK)   [INTERMEDIATE]
// ============================================================
// Check if obj1 contains all key-value pairs from obj2.
// Time: O(k) where k = keys in obj2  |  Space: O(k)

function objectContains(obj1, obj2) {
    return Object.keys(obj2).every(
        key => obj1.hasOwnProperty(key) && obj1[key] === obj2[key]
    );
}

console.log(objectContains({ name: "John", age: 23 }, { age: 23 })); // true

// ============================================================
// 33. PRODUCT OF ARRAY EXCEPT SELF           [INTERMEDIATE]
// ============================================================
// INTERVIEW: LeetCode #238. No division allowed.
//
//  arr:     [1, 2, 3, 4]
//  prefix:  [1, 1, 2, 6]   (running product from left)
//  suffix:  [24,12,4, 1]   (running product from right)
//  result:  [24,12,8, 6]   prefix[i] * suffix[i]
//
// Time: O(n)  |  Space: O(n) for output (O(1) extra if output not counted)

function productExceptSelf(nums) {
    const n = nums.length;
    const result = new Array(n).fill(1);

    let prefix = 1;
    for (let i = 0; i < n; i++) {
        result[i] = prefix;
        prefix *= nums[i];
    }

    let suffix = 1;
    for (let i = n - 1; i >= 0; i--) {
        result[i] *= suffix;
        suffix *= nums[i];
    }
    return result;
}

console.log(productExceptSelf([1, 2, 3, 4])); // [24, 12, 8, 6]

// ============================================================
// 34. MERGE INTERVALS                        [INTERMEDIATE]
// ============================================================
// INTERVIEW: LeetCode #56. Very common.
// Time: O(n log n)  |  Space: O(n)

function mergeIntervals(intervals) {
    intervals.sort((a, b) => a[0] - b[0]);
    const merged = [intervals[0]];

    for (let i = 1; i < intervals.length; i++) {
        const last = merged[merged.length - 1];
        if (intervals[i][0] <= last[1]) {
            last[1] = Math.max(last[1], intervals[i][1]);
        } else {
            merged.push(intervals[i]);
        }
    }
    return merged;
}

console.log(mergeIntervals([[1,3],[2,6],[8,10],[15,18]]));
// [[1,6],[8,10],[15,18]]

// ============================================================
// PROBLEM PATTERN CHEAT SHEET               [INTERVIEW TIP]
// ============================================================
//
// +-------------------------------+-----------------------------+
// | Pattern                       | Problems                    |
// +-------------------------------+-----------------------------+
// | Frequency map / hash map      | Two Sum, Anagram, Max Char, |
// |                                | Group Anagrams, Top K       |
// +-------------------------------+-----------------------------+
// | Two pointers                  | Two Sum (sorted), 3Sum,     |
// |                                | Container With Most Water,  |
// |                                | Remove Duplicates, Palindrome|
// +-------------------------------+-----------------------------+
// | Sliding window                | Max Sum Subarray, Longest   |
// |                                | Substring, Min Window Sub   |
// +-------------------------------+-----------------------------+
// | Stack                         | Valid Parentheses, Min Stack,|
// |                                | Daily Temperatures, Eval RPN|
// +-------------------------------+-----------------------------+
// | DP (bottom-up or memo)        | Climbing Stairs, Coin Change|
// |                                | House Robber, Longest Common|
// |                                | Subsequence, 0/1 Knapsack   |
// +-------------------------------+-----------------------------+
// | Greedy / Kadane               | Max Subarray, Jump Game,    |
// |                                | Best Time to Buy Stock      |
// +-------------------------------+-----------------------------+
// | Binary search                 | Search Rotated Array, Find  |
// |                                | Peak, Koko Eating Bananas   |
// +-------------------------------+-----------------------------+
// | BFS / DFS                     | Tree traversal, Graph paths,|
// |                                | Number of Islands           |
// +-------------------------------+-----------------------------+
//
// INTERVIEW TIP: Before coding, identify which pattern applies.
// State: "This is a sliding window problem because we need the
// maximum of a contiguous subarray."

// ============================================================
// GOTCHAS SUMMARY
// ============================================================
// 1. Two Sum: use Map not object {} for numeric keys.
// 2. Kadane's: initialise both currentMax and globalMax to arr[0],
//    not 0 (handles all-negative arrays).
// 3. Valid Parentheses: check stack.length === 0 at the end.
// 4. Coin Change: greedy fails. Must use DP.
// 5. Fisher-Yates: loop from END to START. Math.random() * (i+1).
// 6. Flatten: arr.flat(Infinity) is the one-liner, but know the
//    recursive implementation for interviews.
// 7. isPrime: check up to sqrt(n), not n. Skip even numbers
//    after checking 2.
// 8. Array.sort() comparator must return a NUMBER, not boolean.
