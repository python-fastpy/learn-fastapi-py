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
// TRACE reverseNumber(-123)   n = Math.abs(-123) = 123
//   n=123  digit 3   result = 0*10 + 3  = 3     n = 12
//   n=12   digit 2   result = 3*10 + 2  = 32    n = 1
//   n=1    digit 1   result = 32*10 + 1 = 321   n = 0  (stop)
//   num < 0  -> return -321

console.log(reverseNumber(123456789)); // 987654321
console.log(reverseNumber(-123));       // -321

// ============================================================
// 2. REVERSE A STRING                                [BASIC]
// ============================================================
// Three approaches: built-in, loop, reduce.

// Approach 1: Built-in  -- Time: O(n)  |  Space: O(n)
const reverseStr1 = (s) => s.split("").reverse().join("");
// TRACE reverseStr1("hello")
//   split   -> ['h','e','l','l','o']
//   reverse -> ['o','l','l','e','h']
//   join    -> "olleh"

// Approach 2: For loop  -- Time: O(n)  |  Space: O(n)
function reverseStr2(s) {
    let rev = '';
    for (let i = s.length - 1; i >= 0; i--) rev += s[i];
    return rev;
}
// TRACE reverseStr2("hello")
//   i=4  'o'  rev = "o"
//   i=3  'l'  rev = "ol"
//   i=2  'l'  rev = "oll"
//   i=1  'e'  rev = "olle"
//   i=0  'h'  rev = "olleh"  -> return "olleh"

// Approach 3: Reduce  -- Time: O(n)  |  Space: O(n)
const reverseStr3 = (s) => s.split("").reduce((acc, c) => c + acc, "");
// TRACE reverseStr3("hello")   acc = ""
//   c='h'  acc = "h"
//   c='e'  acc = "eh"
//   c='l'  acc = "leh"
//   c='l'  acc = "lleh"
//   c='o'  acc = "olleh"  -> return "olleh"

console.log(reverseStr1("hello")); // "olleh"

// ============================================================
// 3. REVERSE WORDS IN A STRING                       [BASIC]
// ============================================================
// "the sky is blue" => "blue is sky the"
// Time: O(n)  |  Space: O(n)

function reverseWords(str) {
    return str.split(' ').reverse().join(' ');
}
// TRACE reverseWords("the sky is blue")
//   split(' ') -> ['the','sky','is','blue']
//   reverse    -> ['blue','is','sky','the']
//   join(' ')  -> "blue is sky the"

console.log(reverseWords("the sky is blue")); // "blue is sky the"

// ============================================================
// 4. PALINDROME CHECK                                [BASIC]
// ============================================================
// INTERVIEW: Very common warm-up question.

// Approach 1: Built-in  -- Time: O(n)  |  Space: O(n)
const isPalindrome1 = (s) => s === s.split("").reverse().join("");
// TRACE isPalindrome1("racecar")
//   reversed = "racecar"   "racecar" === "racecar"  -> true
// TRACE isPalindrome1("hello")
//   reversed = "olleh"     "hello" === "olleh"      -> false

// Approach 2: Two-pointer (optimal)  -- Time: O(n)  |  Space: O(1)
function isPalindrome2(s) {
    for (let i = 0; i < Math.floor(s.length / 2); i++) {
        if (s[i] !== s[s.length - 1 - i]) return false;
    }
    return true;
}
// TRACE isPalindrome2("racecar")   loop i < floor(7/2) = 3
//   r a c e c a r
//   L ^         ^ R   i=0  s[0]='r' vs s[6]='r'  equal
//     L ^     ^ R     i=1  s[1]='a' vs s[5]='a'  equal
//       L ^ ^ R       i=2  s[2]='c' vs s[4]='c'  equal
//   loop done -> true
// TRACE isPalindrome2("hello")
//   i=0  s[0]='h' vs s[4]='o'  differ -> false

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
// TRACE fibonacci(7)   fib = [0, 1]
//   i=2  1 + 0 = 1   fib = [0,1,1]
//   i=3  1 + 1 = 2   fib = [0,1,1,2]
//   i=4  2 + 1 = 3   fib = [0,1,1,2,3]
//   i=5  3 + 2 = 5   fib = [0,1,1,2,3,5]
//   i=6  5 + 3 = 8   fib = [0,1,1,2,3,5,8]
//   i=7  stop -> return [0,1,1,2,3,5,8]

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
// TRACE factorial(5)   result = 1
//   i=2  result = 1*2  = 2
//   i=3  result = 2*3  = 6
//   i=4  result = 6*4  = 24
//   i=5  result = 24*5 = 120  -> return 120
// TRACE factorial(0)   loop never runs (2 <= 0 false) -> return 1

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
// TRACE isPrime(11)
//   11 > 3;  11 % 2 = 1, 11 % 3 = 2  -> not ruled out
//   i=5  5*5 = 25 <= 11 ? no -> loop skipped
//   return true
// TRACE isPrime(15)
//   15 % 2 = 1, 15 % 3 = 0  -> return false
// TRACE isPrime(49)   (shows the loop)
//   49 % 2 = 1, 49 % 3 = 1
//   i=5  25 <= 49   49 % 5 = 4,  49 % 7 = 0  -> return false

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
// TRACE getMaxChar('aaabbc')
//   build freq:
//     'a' {a:1}   'a' {a:2}   'a' {a:3}
//     'b' {a:3,b:1}   'b' {a:3,b:2}   'c' {a:3,b:2,c:1}
//   scan freq:
//     c='a'  3 > 0 -> maxChar='a' maxCount=3
//     c='b'  2 > 3 ? no
//     c='c'  1 > 3 ? no
//   return 'a'

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
// TRACE hasDuplicatesBrute("abca")
//   i=0 'a'  j=1 'b' no   j=2 'c' no   j=3 'a' MATCH -> return true
// TRACE hasDuplicatesBrute("abc")
//   i=0 'a'  j=1 'b' no   j=2 'c' no
//   i=1 'b'  j=2 'c' no
//   i=2 'c'  (no j)       -> return false

// Approach 2: Set (optimal) -- Time: O(n)  |  Space: O(n)
const hasDuplicates = (str) => new Set(str).size !== str.length;
// TRACE hasDuplicates("abcdef")   Set{a,b,c,d,e,f} size 6 vs length 6  -> false
// TRACE hasDuplicates("aabcde")   Set{a,b,c,d,e}   size 5 vs length 6  -> true

console.log(hasDuplicates("abcdef")); // false
console.log(hasDuplicates("aabcde")); // true

// ============================================================
// 10. COUNT SUBSTRING OCCURRENCES                    [BASIC]
// ============================================================
// Time: O(n)  |  Space: O(n)

function countOccurrences(str, sub) {
    return str.split(sub).length - 1;
}
// TRACE countOccurrences('Geeks for Geeks shubham Geeks', "Geeks")
//   split("Geeks") -> ['', ' for ', ' shubham ', '']   (3 cuts -> 4 pieces)
//   4 - 1 = 3  -> return 3

console.log(countOccurrences('Geeks for Geeks shubham Geeks', "Geeks")); // 3

// ============================================================
// 11. CAPITALIZE FIRST LETTER OF EACH WORD           [BASIC]
// ============================================================
// Time: O(n)  |  Space: O(n)

const capitalize = (s) =>
    s.split(" ").map(w => w[0].toUpperCase() + w.slice(1)).join(" ");
// TRACE capitalize("hello world")
//   split  -> ['hello','world']
//   map    'hello' -> 'H' + 'ello' = 'Hello'
//          'world' -> 'W' + 'orld' = 'World'
//   join   -> "Hello World"

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
// TRACE isAnagram1("listen", "silent")
//   "listen" sorted -> "eilnst"
//   "silent" sorted -> "eilnst"
//   "eilnst" === "eilnst"  -> true

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
// TRACE isAnagram2("listen", "silent")
//   lengths 6 = 6
//   freq from a: {l:1,i:1,s:1,t:1,e:1,n:1}
//   c='s'  s:1 -> 0
//   c='i'  i:1 -> 0
//   c='l'  l:1 -> 0
//   ...    (e, n the same)
//   c='t'  t:1 -> 0   all zero -> return true
// TRACE isAnagram2("hello", "world")
//   freq from a: {h:1,e:1,l:2,o:1}
//   c='w'  freq['w'] undefined -> return false

console.log(isAnagram2("listen", "silent")); // true
console.log(isAnagram2("hello", "world"));   // false

// ============================================================
// 13. REMOVE DUPLICATES FROM ARRAY                   [BASIC]
// ============================================================
// Approach 1: Set  -- Time: O(n)  |  Space: O(n)
const unique1 = (arr) => [...new Set(arr)];
// TRACE unique1(["apple", "mango", "apple", "mango"])
//   add "apple" {apple}   add "mango" {apple,mango}
//   add "apple" (exists)  add "mango" (exists)
//   spread -> ["apple","mango"]

// Approach 2: Filter  -- Time: O(n^2)  |  Space: O(n)
const unique2 = (arr) => arr.filter((item, i) => arr.indexOf(item) === i);
// TRACE unique2(["apple", "mango", "apple", "mango"])
//   i=0 "apple"  indexOf=0  0===0 keep
//   i=1 "mango"  indexOf=1  1===1 keep
//   i=2 "apple"  indexOf=0  0!==2 drop
//   i=3 "mango"  indexOf=1  1!==3 drop
//   -> ["apple","mango"]

// Approach 3: Objects (deduplicate by key)
function uniqueByKey(arr, key) {
    return arr.filter((item, i) =>
        i === arr.findIndex(el => el[key] === item[key])
    );
}
// TRACE uniqueByKey([{id:1,n:'a'}, {id:2,n:'b'}, {id:1,n:'c'}], 'id')
//   i=0 id=1  findIndex=0  keep
//   i=1 id=2  findIndex=1  keep
//   i=2 id=1  findIndex=0  drop (first id=1 is at 0)
//   -> [{id:1,n:'a'}, {id:2,n:'b'}]

console.log(unique1(["apple", "mango", "apple", "mango"])); // ["apple", "mango"]

// ============================================================
// 14. MIN AND MAX OF ARRAY                           [BASIC]
// ============================================================
// Approach 1: Built-in  -- Time: O(n)  |  Space: O(n) spread
const minMax1 = (arr) => ({ min: Math.min(...arr), max: Math.max(...arr) });
// TRACE minMax1([3, 1, 4, 1, 5, 9, 2, 6])
//   Math.min(3,1,4,1,5,9,2,6) = 1
//   Math.max(3,1,4,1,5,9,2,6) = 9   -> {min:1, max:9}

// Approach 2: Single pass (optimal)  -- Time: O(n)  |  Space: O(1)
function minMax2(arr) {
    let min = arr[0], max = arr[0];
    for (const val of arr) {
        if (val > max) max = val;
        if (val < min) min = val;
    }
    return { min, max };
}
// TRACE minMax2([3, 1, 4, 1, 5, 9, 2, 6])   min = 3, max = 3
//   val=3  min=3 max=3
//   val=1  min=1 max=3
//   val=4  min=1 max=4
//   val=1  min=1 max=4
//   val=5  min=1 max=5
//   val=9  min=1 max=9
//   val=2  min=1 max=9
//   val=6  min=1 max=9   -> {min:1, max:9}

console.log(minMax2([3, 1, 4, 1, 5, 9, 2, 6])); // {min:1, max:9}

// ============================================================
// 15. FLATTEN ARRAY (DEEP)                           [BASIC]
// ============================================================
// Approach 1: Recursive reduce  -- Time: O(n)  |  Space: O(d) call stack

function flattenDeep(arr) {
    return arr.reduce((acc, val) =>
        acc.concat(Array.isArray(val) ? flattenDeep(val) : val), []);
}
// TRACE flattenDeep([1, [2, [3, [4, 5]]]])
//   flattenDeep([1,[2,[3,[4,5]]]])     acc=[1], then recurse on [2,...]
//     flattenDeep([2,[3,[4,5]]])       acc=[2], then recurse
//       flattenDeep([3,[4,5]])         acc=[3], then recurse
//         flattenDeep([4,5])           -> [4,5]
//       -> [3,4,5]
//     -> [2,3,4,5]
//   -> [1,2,3,4,5]

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
// TRACE flattenObj({ a: { b: 1, c: { d: 2 } }, e: 3 })
//   key 'a'  path "a"     object -> recurse(prefix "a")
//     key 'b'  path "a.b"   result = {"a.b":1}
//     key 'c'  path "a.c"   object -> recurse(prefix "a.c")
//       key 'd'  path "a.c.d" result = {"a.b":1,"a.c.d":2}
//   key 'e'  path "e"     result = {"a.b":1,"a.c.d":2,e:3}
//   -> { "a.b": 1, "a.c.d": 2, e: 3 }

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
// TRACE shuffleArray([1, 2, 3, 4, 5])   (j is random; one possible run)
//   i=4  j=1  swap arr[4],arr[1]  [1,5,3,4,2]
//   i=3  j=3  swap with itself     [1,5,3,4,2]
//   i=2  j=0  swap arr[2],arr[0]  [3,5,1,4,2]
//   i=1  j=0  swap arr[1],arr[0]  [5,3,1,4,2]
//   -> [5,3,1,4,2]

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
// TRACE add(4)(5)(7)()
//   add(4)        -> fn with a=4
//   (5)  b=5      -> add(4+5)  = fn with a=9
//   (7)  b=7      -> add(9+7)  = fn with a=16
//   ()   b=undefined -> return a = 16

console.log(add(4)(5)(7)()); // 16
