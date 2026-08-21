// ============================================================
// ALGORITHM PROBLEMS -- ULTIMATE QUICK-REFERENCE
// ============================================================
// Organised by difficulty: Basic -> Intermediate -> Advanced
// Every solution includes Time/Space complexity.
// Multiple approaches shown where applicable.
// ============================================================

// ============================================================
//                    B A S I C   P R O B L E M S
// ============================================================

// ============================================================
// 1. REVERSE A NUMBER                                [BASIC]
// ============================================================
// INTERVIEW: Commonly paired with "reverse an integer" on LeetCode.
// Time: O(d) where d = number of digits  |  Space: O(1)

function reverseNumber(num) {
    let result = 0;
    let n = Math.abs(num);
    while (n > 0) {
        result = result * 10 + (n % 10);
        n = Math.floor(n / 10);
    }
    return num < 0 ? -result : result;
}

console.log(reverseNumber(123456789)); // 987654321
console.log(reverseNumber(-123));       // -321

// ============================================================
// 2. REVERSE A STRING                                [BASIC]
// ============================================================
// Three approaches: built-in, loop, reduce.

// Approach 1: Built-in  -- Time: O(n)  |  Space: O(n)
const reverseStr1 = (s) => s.split("").reverse().join("");

// Approach 2: For loop  -- Time: O(n)  |  Space: O(n)
function reverseStr2(s) {
    let rev = '';
    for (let i = s.length - 1; i >= 0; i--) rev += s[i];
    return rev;
}

// Approach 3: Reduce  -- Time: O(n)  |  Space: O(n)
const reverseStr3 = (s) => s.split("").reduce((acc, c) => c + acc, "");

console.log(reverseStr1("hello")); // "olleh"

// ============================================================
// 3. REVERSE WORDS IN A STRING                       [BASIC]
// ============================================================
// "the sky is blue" => "blue is sky the"
// Time: O(n)  |  Space: O(n)

function reverseWords(str) {
    return str.split(' ').reverse().join(' ');
}

console.log(reverseWords("the sky is blue")); // "blue is sky the"

// ============================================================
// 4. PALINDROME CHECK                                [BASIC]
// ============================================================
// INTERVIEW: Very common warm-up question.

// Approach 1: Built-in  -- Time: O(n)  |  Space: O(n)
const isPalindrome1 = (s) => s === s.split("").reverse().join("");

// Approach 2: Two-pointer (optimal)  -- Time: O(n)  |  Space: O(1)
function isPalindrome2(s) {
    for (let i = 0; i < Math.floor(s.length / 2); i++) {
        if (s[i] !== s[s.length - 1 - i]) return false;
    }
    return true;
}

console.log(isPalindrome2("racecar")); // true
console.log(isPalindrome2("hello"));   // false

// ============================================================
// 5. FIBONACCI SEQUENCE                              [BASIC]
// ============================================================
// Time: O(n)  |  Space: O(n)

function fibonacci(n) {
    const fib = [0, 1];
    for (let i = 2; i < n; i++) fib[i] = fib[i - 1] + fib[i - 2];
    return fib;
}

console.log(fibonacci(7)); // [0, 1, 1, 2, 3, 5, 8]

// ============================================================
// 6. FACTORIAL                                       [BASIC]
// ============================================================
// Time: O(n)  |  Space: O(1) iterative / O(n) recursive

function factorial(n) {
    let result = 1;
    for (let i = 2; i <= n; i++) result *= i;
    return result;
}

console.log(factorial(5)); // 120
console.log(factorial(0)); // 1

// ============================================================
// 7. PRIME NUMBER CHECK                              [BASIC]
// ============================================================
// Optimization: only check up to sqrt(n).
// Time: O(sqrt(n))  |  Space: O(1)

function isPrime(num) {
    if (num <= 1) return false;
    if (num <= 3) return true;
    if (num % 2 === 0 || num % 3 === 0) return false;
    for (let i = 5; i * i <= num; i += 6) {
        if (num % i === 0 || num % (i + 2) === 0) return false;
    }
    return true;
}

console.log(isPrime(11)); // true
console.log(isPrime(15)); // false

// ============================================================
// 8. MAX CHARACTER IN STRING                         [BASIC]
// ============================================================
// INTERVIEW: Frequency map pattern -- reused in many problems.
// Time: O(n)  |  Space: O(k) where k = unique characters

function getMaxChar(str) {
    const freq = {};
    for (const c of str) freq[c] = (freq[c] || 0) + 1;

    let maxChar = '', maxCount = 0;
    for (const c in freq) {
        if (freq[c] > maxCount) { maxCount = freq[c]; maxChar = c; }
    }
    return maxChar;
}

console.log(getMaxChar('aaabbc')); // 'a'

// ============================================================
// 9. CHECK DUPLICATE CHARACTERS                      [BASIC]
// ============================================================
// Approach 1: Brute force -- Time: O(n^2)  |  Space: O(1)
function hasDuplicatesBrute(str) {
    for (let i = 0; i < str.length; i++) {
        for (let j = i + 1; j < str.length; j++) {
            if (str[i] === str[j]) return true;
        }
    }
    return false;
}

// Approach 2: Set (optimal) -- Time: O(n)  |  Space: O(n)
const hasDuplicates = (str) => new Set(str).size !== str.length;

console.log(hasDuplicates("abcdef")); // false
console.log(hasDuplicates("aabcde")); // true

// ============================================================
// 10. COUNT SUBSTRING OCCURRENCES                    [BASIC]
// ============================================================
// Time: O(n)  |  Space: O(n)

function countOccurrences(str, sub) {
    return str.split(sub).length - 1;
}

console.log(countOccurrences('Geeks for Geeks shubham Geeks', "Geeks")); // 3

// ============================================================
// 11. CAPITALIZE FIRST LETTER OF EACH WORD           [BASIC]
// ============================================================
// Time: O(n)  |  Space: O(n)

const capitalize = (s) =>
    s.split(" ").map(w => w[0].toUpperCase() + w.slice(1)).join(" ");

console.log(capitalize("hello world")); // "Hello World"

// ============================================================
// 12. ANAGRAM CHECK                                  [BASIC]
// ============================================================
// Two strings are anagrams if they contain the same characters
// in the same frequency.

// Approach 1: Sort  -- Time: O(n log n)  |  Space: O(n)
const isAnagram1 = (a, b) =>
    a.toLowerCase().split('').sort().join('') ===
    b.toLowerCase().split('').sort().join('');

// Approach 2: Frequency map (optimal)  -- Time: O(n)  |  Space: O(n)
function isAnagram2(a, b) {
    if (a.length !== b.length) return false;
    const freq = {};
    for (const c of a.toLowerCase()) freq[c] = (freq[c] || 0) + 1;
    for (const c of b.toLowerCase()) {
        if (!freq[c]) return false;
        freq[c]--;
    }
    return true;
}

console.log(isAnagram2("listen", "silent")); // true
console.log(isAnagram2("hello", "world"));   // false

// ============================================================
// 13. REMOVE DUPLICATES FROM ARRAY                   [BASIC]
// ============================================================
// Approach 1: Set  -- Time: O(n)  |  Space: O(n)
const unique1 = (arr) => [...new Set(arr)];

// Approach 2: Filter  -- Time: O(n^2)  |  Space: O(n)
const unique2 = (arr) => arr.filter((item, i) => arr.indexOf(item) === i);

// Approach 3: Objects (deduplicate by key)
function uniqueByKey(arr, key) {
    return arr.filter((item, i) =>
        i === arr.findIndex(el => el[key] === item[key])
    );
}

console.log(unique1(["apple", "mango", "apple", "mango"])); // ["apple", "mango"]

// ============================================================
// 14. MIN AND MAX OF ARRAY                           [BASIC]
// ============================================================
// Approach 1: Built-in  -- Time: O(n)  |  Space: O(n) spread
const minMax1 = (arr) => ({ min: Math.min(...arr), max: Math.max(...arr) });

// Approach 2: Single pass (optimal)  -- Time: O(n)  |  Space: O(1)
function minMax2(arr) {
    let min = arr[0], max = arr[0];
    for (const val of arr) {
        if (val > max) max = val;
        if (val < min) min = val;
    }
    return { min, max };
}

console.log(minMax2([3, 1, 4, 1, 5, 9, 2, 6])); // {min:1, max:9}

// ============================================================
// 15. FLATTEN ARRAY (DEEP)                           [BASIC]
// ============================================================
// Approach 1: Recursive reduce  -- Time: O(n)  |  Space: O(d) call stack

function flattenDeep(arr) {
    return arr.reduce((acc, val) =>
        acc.concat(Array.isArray(val) ? flattenDeep(val) : val), []);
}

console.log(flattenDeep([1, [2, [3, [4, 5]]]])); // [1, 2, 3, 4, 5]
// Or use: arr.flat(Infinity)

// ============================================================
// 16. FLATTEN OBJECT                                 [BASIC]
// ============================================================
// { a: { b: 1 } } => { "a.b": 1 }
// Time: O(n) where n = total keys  |  Space: O(n)

function flattenObj(obj, prefix = '', result = {}) {
    for (const key in obj) {
        const path = prefix ? `${prefix}.${key}` : key;
        if (typeof obj[key] === 'object' && !Array.isArray(obj[key]) && obj[key] !== null) {
            flattenObj(obj[key], path, result);
        } else {
            result[path] = obj[key];
        }
    }
    return result;
}

console.log(flattenObj({ a: { b: 1, c: { d: 2 } }, e: 3 }));
// { "a.b": 1, "a.c.d": 2, e: 3 }

// ============================================================
// 17. SHUFFLE ARRAY (Fisher-Yates)                   [BASIC]
// ============================================================
// INTERVIEW: The ONLY correct way to shuffle uniformly.
// Time: O(n)  |  Space: O(1)

function shuffleArray(arr) {
    for (let i = arr.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [arr[i], arr[j]] = [arr[j], arr[i]];
    }
    return arr;
}

console.log(shuffleArray([1, 2, 3, 4, 5]));
// GOTCHA: arr.sort(() => Math.random() - 0.5) is NOT uniform!

// ============================================================
// 18. INFINITE CURRYING                              [BASIC]
// ============================================================
// add(1)(2)(3)() => 6
// Time: O(n) calls  |  Space: O(n) call stack

function add(a) {
    return function (b) {
        if (b !== undefined) return add(a + b);
        return a;
    };
}

console.log(add(4)(5)(7)()); // 16

// ============================================================
//            I N T E R M E D I A T E   P R O B L E M S
// ============================================================

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

// ============================================================
//             A D V A N C E D   P R O B L E M S
// ============================================================

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
