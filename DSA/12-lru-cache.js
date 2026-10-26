/* ============================================================================
 * LRU CACHE  [ADVANCED]
 * ============================================================================
 * Least Recently Used cache: fixed capacity; when full, evicts the item that
 * hasn't been used (get/set) in the longest time.
 * Built with a Map, which in JS preserves insertion order — re-inserting a
 * key on access moves it to the "most recently used" end for free.
 *
 * ASCII diagram (capacity 3, MRU on the right):
 *   [LRU] key1 <-> key2 <-> key3 [MRU]
 *   get(key1) -> moves key1 to MRU end: key2 <-> key3 <-> key1
 *   set(new key) when full -> evict key2 (current LRU / leftmost)
 * ==========================================================================*/

class LRUCache {
    constructor(capacity) {
        this.capacity = capacity;
        this.cache = new Map(); // Map preserves insertion order -> front = LRU, back = MRU
    }

    get(key) {
        if (!this.cache.has(key)) return -1;
        const value = this.cache.get(key);
        this.cache.delete(key);   // remove then re-add -> moves to MRU (end)
        this.cache.set(key, value);
        return value;
    }
    // TRACE get()   capacity = 2   cache order LRU -> MRU
    //   start           [a:1, b:2]
    //   get("a")  hit   delete a, set a   [b:2, a:1]   returns 1
    //   get("z")  miss  no change         [b:2, a:1]   returns -1

    put(key, value) {
        if (this.cache.has(key)) this.cache.delete(key); // refresh position
        else if (this.cache.size >= this.capacity) {
            const lruKey = this.cache.keys().next().value; // first key = least recently used
            this.cache.delete(lruKey);
        }
        this.cache.set(key, value);
    }
    // TRACE put()   capacity = 2   cache order LRU -> MRU
    //   put("a", 1)   new, size 0 < 2          [a:1]
    //   put("b", 2)   new, size 1 < 2          [a:1, b:2]
    //   put("b", 20)  exists -> delete, re-set [a:1, b:20]
    //   put("c", 3)   new, size 2 >= 2 -> evict lruKey "a"   [b:20, c:3]

    print() { console.log([...this.cache.entries()]); }
}

const lru = new LRUCache(3);
lru.put("a", 1);
lru.put("b", 2);
lru.put("c", 3);
lru.print();          // a,b,c  (c is MRU)
console.log(lru.get("a")); // 1 -> a becomes MRU
lru.print();          // b,c,a
lru.put("d", 4);      // capacity exceeded -> evicts "b" (current LRU)
lru.print();          // c,a,d

// Big-O: get/put O(1) average (Map lookup + delete/set are O(1))
//
// GOTCHAS:
// - A true from-scratch interview answer often expects a HashMap + Doubly
//   Linked List (see 07-linked-lists.js's DoublyLinkedList) so eviction/
//   promotion is O(1) without relying on Map's insertion-order behavior —
//   know both approaches.
// - Must handle the "key already exists" case in put() by refreshing its
//   position, not just overwriting the value.
// INTERVIEW: "Design an LRU Cache" (LeetCode 146) is one of the most-asked
// system-design-adjacent coding questions — know both the Map-only shortcut
// (above) and the HashMap+DLL from-scratch version.
