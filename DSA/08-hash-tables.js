/* ============================================================================
 * HASH TABLES  [INTERMEDIATE]
 * ============================================================================
 * - A hash table (hash map) stores key/value pairs. A hash FUNCTION converts
 *   a string key into a numeric index into a fixed-size backing array.
 * - JS Object and Map are both hash-table-backed under the hood.
 * - Writing your own is a very common interview exercise.
 *
 * ASCII diagram (size 50, chaining on collision):
 *   hash("name") -> 12    table[12] -> [["name","shubham"]]
 *   hash("mane") -> 12    table[12] -> [["name","shubham"], ["mane","vinayak"]]
 *                                        (collision resolved via chaining/bucket array)
 *
 * Usage: DB indexing, caches, dedup, O(1)-avg lookups.
 * Ops: hash, set, get, remove, display
 * ==========================================================================*/

class HashTable {
    constructor(size) {
        this.table = new Array(size);
        this.size = size;
    }

    hash(key) {
        let total = 0;
        for (let i = 0; i < key.length; i++) total += key.charCodeAt(i);
        return total % this.size;
    }
    // TRACE hash("name")   size = 50
    //   i=0  'n' 110   total = 110
    //   i=1  'a'  97   total = 207
    //   i=2  'm' 109   total = 316
    //   i=3  'e' 101   total = 417
    //   417 % 50 = 17  -> index 17
    //   hash("mane") -> same letters, same total 417 -> ALSO 17 (collision!)

    set(key, value) { // chaining handles collisions (e.g. "name" & "mane" -> same index)
        const index = this.hash(key);
        const bucket = this.table[index];
        if (!bucket) {
            this.table[index] = [[key, value]];
        } else {
            const sameKeyItem = bucket.find((item) => item[0] === key);
            if (sameKeyItem) sameKeyItem[1] = value;
            else bucket.push([key, value]);
        }
    }
    // TRACE set("name","shubham") -> set("age",25) -> set("mane","vinayak")
    //   step 1  hash("name") = 17   table[17] empty -> create bucket
    //           table[17] = [ ["name","shubham"] ]
    //   step 2  hash("age")  = 1    table[1] empty  -> create bucket
    //           table[1]  = [ ["age",25] ]
    //   step 3  hash("mane") = 17   table[17] exists, no "mane" inside -> push
    //           table[17] = [ ["name","shubham"], ["mane","vinayak"] ]   <- chaining
    //   (same key again, e.g. set("name","x") -> found -> value overwritten in place)

    get(key) {
        const index = this.hash(key);
        const bucket = this.table[index];
        if (bucket) {
            const sameKeyItem = bucket.find((item) => item[0] === key);
            if (sameKeyItem) return sameKeyItem[1];
        }
        return undefined;
    }
    // TRACE get("mane")
    //   step 1  hash("mane") = 17
    //   step 2  bucket = [ ["name","shubham"], ["mane","vinayak"] ]
    //   step 3  scan: "name" != "mane" -> next; "mane" == "mane" -> found
    //   return "vinayak"
    //   get("zzz") -> its bucket is empty -> return undefined

    remove(key) {
        const index = this.hash(key);
        const bucket = this.table[index];
        if (bucket) {
            const sameKeyItem = bucket.find((item) => item[0] === key);
            if (sameKeyItem) bucket.splice(bucket.indexOf(sameKeyItem), 1);
        }
    }
    // TRACE remove("name")
    //   step 1  hash("name") = 17
    //   step 2  bucket = [ ["name","shubham"], ["mane","vinayak"] ]
    //   step 3  found ["name","shubham"] at position 0 -> splice(0, 1)
    //           table[17] = [ ["mane","vinayak"] ]   <- "mane" survives

    display() {
        for (let i = 0; i < this.table.length; i++) {
            if (this.table[i]) console.log(i, this.table[i]);
        }
    }
    // TRACE display()   (after the sets above)
    //   i=0  empty -> skip
    //   i=1  prints: 1 [ [ 'age', 25 ] ]
    //   i=2..16  empty -> skip
    //   i=17 prints: 17 [ [ 'name', 'shubham' ], [ 'mane', 'vinayak' ] ]
}

const table = new HashTable(50);
console.log("Hash table ------", table.hash("shubham"));
table.set("name", "shubham");
table.set("age", 25);
table.display();
console.log(table.get("name"));
table.set("mane", "vinayak"); // "mane" is an anagram of "name" -> SAME hash index
table.display();              // both entries live in the same bucket (chaining)
table.remove("name");
table.display();

// Big-O: set/get/remove are O(1) average, O(n) worst case (all keys collide
// into one bucket) — that's why chaining (bucket = array of [k,v] pairs) matters.
//
// GOTCHAS:
// - A naive hash (sum of char codes) means anagrams collide ("name" vs "mane")
//   — always resolve collisions via chaining or open addressing, never overwrite blindly.
// - Table size should ideally be prime to reduce clustering.
// INTERVIEW: implement a hash table from scratch AND explain collision handling
// (chaining vs open addressing/linear probing) — asked very often.

// COMPARISON TABLE — BST vs Hash Table
// ┌───────────────────────┬───────────────────────┬───────────────────────┐
// │                        │ Binary Search Tree     │ Hash Table             │
// ├───────────────────────┼───────────────────────┼───────────────────────┤
// │ Avg lookup              │ O(log n)               │ O(1)                   │
// │ Worst-case lookup       │ O(n) (unbalanced)      │ O(n) (bad hash/collide)│
// │ Maintains sorted order  │ yes                    │ no                     │
// │ Range queries           │ efficient (in-order)   │ inefficient            │
// │ Memory overhead          │ 2 pointers/node        │ bucket arrays          │
// │ Use when                │ need ordered data       │ need fastest lookup    │
// └───────────────────────┴───────────────────────┴───────────────────────┘
