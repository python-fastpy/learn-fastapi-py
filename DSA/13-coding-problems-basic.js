/* ============================================================================
 * CODING PROBLEMS — BASIC  [BASIC]
 * ============================================================================
 * Every solution includes Time/Space complexity.
 * Multiple approaches shown where applicable.
 * ==========================================================================*/

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
