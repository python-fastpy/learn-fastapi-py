/* ============================================================================
 * LINKED LISTS  [INTERMEDIATE]
 * ============================================================================
 * Singly Linked List, SLL+Tail pointer, Stack/Queue via LL, Doubly Linked List.
 * ==========================================================================*/

// ------------------------------ Singly Linked List ------------------------------
// [INTERMEDIATE]
// - Linear chain of nodes; each node holds a value + pointer to the next node.
// - No random access (must walk from head); insert/delete at head is O(1).
//
// ASCII diagram:
//   head ──▶ [10|next] ──▶ [20|next] ──▶ [30|next] ──▶ null
//
// Usage: underlies stacks/queues, image viewer "next" links.
// Ops: prepend, append, insert, removeFrom, removeValue, search, reverse, print

class SLNode {
    constructor(value) {
        this.value = value;
        this.next = null;
    }
}

class LinkedList {
    constructor() {
        this.head = null;
        this.size = 0;
    }
    isEmpty() { return this.size === 0; }
    getSize() { return this.size; }
    // TRACE isEmpty() / getSize()   new list: head = null, size = 0
    //   isEmpty() -> 0 === 0 -> true      getSize() -> 0

    prepend(value) { // O(1)
        const node = new SLNode(value);
        if (this.isEmpty()) this.head = node;
        else { node.next = this.head; this.head = node; }
        this.size++;
    }
    // TRACE prepend(20)   (via insert(20, 0))   list: 10 -> null
    //   step 1  node = [20]                not empty -> else branch
    //   step 2  node.next = head           [20] -> [10] -> null
    //   step 3  head = node                head -> [20] -> [10] -> null
    //   step 4  size++                     size = 2

    append(value) { // O(n) — must walk to the tail
        const node = new SLNode(value);
        if (this.isEmpty()) { this.head = node; }
        else {
            let prev = this.head;
            while (prev.next) prev = prev.next;
            prev.next = node;
        }
        this.size++;
    }
    // TRACE append(30)   list: 20 -> 10 -> null
    //   step 1  node = [30], prev = node(20)
    //   step 2  prev.next = [10] -> prev = node(10)
    //   step 3  prev.next = null -> stop walking (prev is the tail)
    //   step 4  prev.next = node           [20] -> [10] -> [30] -> null
    //   step 5  size++                     size = 3

    insert(value, index) {
        if (index < 0 || index > this.size) return;
        if (index === 0) { this.prepend(value); return; }
        const node = new SLNode(value);
        let prev = this.head;
        for (let i = 0; i < index - 1; i++) prev = prev.next;
        node.next = prev.next;
        prev.next = node;
        this.size++;
    }
    // TRACE insert(40, 2)   list: 20 -> 30 -> 10   size = 3
    //   step 1  index 2 is in range, not 0 -> node = [40], prev = node(20)
    //   step 2  i=0 (< 1)  prev = prev.next = node(30)      loop ends
    //   step 3  node.next = prev.next      [40] -> [10]
    //   step 4  prev.next = node           [20] -> [30] -> [40] -> [10] -> null
    //   step 5  size++                     size = 4
    //   (insert(10, 0) / insert(20, 0) just call prepend)

    removeFrom(index) {
        if (index < 0 || index >= this.size) return null;
        let removeNode;
        if (index === 0) {
            removeNode = this.head;
            this.head = this.head.next;
        } else {
            let prev = this.head;
            for (let i = 0; i < index - 1; i++) prev = prev.next;
            removeNode = prev.next;
            prev.next = removeNode.next;
        }
        this.size--;
        return removeNode.value;
    }
    // TRACE removeFrom(1)   list: 20 -> 30 -> 40 -> 10   size = 4
    //   step 1  prev = node(20)            loop runs 0 times (index-1 = 0)
    //   step 2  removeNode = prev.next = node(30)
    //   step 3  prev.next = removeNode.next   [20] -> [40] -> [10] -> null
    //   step 4  size--  size = 3           return 30
    //   removeFrom(10): 10 >= size 3 -> return null

    removeValue(value) {
        if (this.isEmpty()) return null;
        if (this.head.value === value) {
            this.head = this.head.next;
            this.size--;
            return value;
        }
        let prev = this.head;
        while (prev.next && prev.next.value !== value) prev = prev.next;
        if (prev.next) {
            prev.next = prev.next.next;
            this.size--;
            return value;
        }
        return null;
    }
    // TRACE removeValue(10)   list: 20 -> 40 -> 10
    //   step 1  head.value 20 !== 10 -> prev = node(20)
    //   step 2  prev.next.value 40 !== 10 -> prev = node(40)
    //   step 3  prev.next.value 10 === 10 -> stop
    //   step 4  prev.next = prev.next.next (null)   [20] -> [40] -> null
    //   step 5  size = 2                   return 10

    search(value) {
        if (this.isEmpty()) return -1;
        let i = 0, curr = this.head;
        while (curr) {
            if (curr.value === value) return i;
            curr = curr.next;
            i++;
        }
        return -1;
    }
    // TRACE search(1000)   list: 20 -> 40
    //   i=0  curr=[20]  20 !== 1000 -> next
    //   i=1  curr=[40]  40 !== 1000 -> next
    //   i=2  curr=null  loop ends     -> return -1
    // TRACE search(20)  i=0 curr=[20] match -> return 0

    reverse() {
        let prev = null, curr = this.head;
        while (curr) {
            const next = curr.next;
            curr.next = prev;
            prev = curr;
            curr = next;
        }
        this.head = prev;
    }
    // TRACE reverse()   list: 1000 -> 20 -> 40 -> null
    //   start  prev=null    curr=[1000]
    //   iter1  next=[20]    [1000].next=null    prev=[1000]  curr=[20]
    //          null <- [1000]      [20] -> [40] -> null
    //   iter2  next=[40]    [20].next=[1000]    prev=[20]    curr=[40]
    //          null <- [1000] <- [20]      [40] -> null
    //   iter3  next=null    [40].next=[20]      prev=[40]    curr=null
    //   head = prev         head -> [40] -> [20] -> [1000] -> null

    print() {
        if (this.isEmpty()) { console.log("List is Empty"); return; }
        let curr = this.head, listValue = "";
        while (curr) { listValue += `${curr.value} `; curr = curr.next; }
        console.log(listValue);
    }
    // TRACE print()   list: 40 -> 20 -> 1000
    //   curr=[40]   listValue = "40 "
    //   curr=[20]   listValue = "40 20 "
    //   curr=[1000] listValue = "40 20 1000 "
    //   curr=null   -> logs "40 20 1000 "   (empty list logs "List is Empty")
}

const list = new LinkedList();
console.log(list.isEmpty(), list.getSize());
list.print();
list.insert(10, 0);
list.print();
list.insert(20, 0);
list.print();
list.insert(30, 1);
list.print();
list.insert(40, 2);
list.print();
console.log(list.getSize());
console.log(list.removeFrom(1));
console.log(list.removeFrom(10));
list.print();
list.removeValue(10);
list.print();
console.log(list.search(1000));
console.log(list.search(20));
list.insert(1000, 0);
list.print();
list.reverse();
list.print();
// Big-O: prepend O(1) | append O(n) | insert/removeFrom(index) O(n) | search O(n)
// removing the HEAD is O(1); removing anywhere else requires a traversal.
//
// GOTCHAS:
// - append() without a tail pointer is O(n) because you must walk the whole list.
// - reverse() flips `next` pointers in place — head becomes tail, no new nodes.
// INTERVIEW: "reverse a linked list" is asked in almost every interview loop;
// know the 3-pointer (prev/curr/next) technique above cold.

// -------------------- Singly Linked List with Tail pointer --------------------
// [INTERMEDIATE] Adding a tail pointer makes append() O(1) instead of O(n).
//
// ASCII diagram:
//   head ──▶ [1] ──▶ [2] ──▶ [3] ◀── tail

class LinkedListTail {
    constructor() {
        this.head = null;
        this.tail = null;
        this.size = 0;
    }
    isEmpty() { return this.size === 0; }
    getSize() { return this.size; }
    // TRACE isEmpty() / getSize()   new listTail -> true, 0

    print() {
        if (this.isEmpty()) { console.log("List is Empty"); return; }
        let curr = this.head, listValues = "";
        while (curr) { listValues += `${curr.value} `; curr = curr.next; }
        console.log(listValues);
    }
    // TRACE print()   list: 0 -> 1 -> 2 -> 3
    //   "0 " -> "0 1 " -> "0 1 2 " -> "0 1 2 3 "   logs "0 1 2 3 "

    prepend(value) {
        const node = new SLNode(value);
        if (this.isEmpty()) { this.head = node; this.tail = node; }
        else { node.next = this.head; this.head = node; }
        this.size++;
    }
    // TRACE prepend(0)   head -> [1] -> [2] -> [3] <- tail
    //   step 1  node = [0]; node.next = head    [0] -> [1]
    //   step 2  head = node     head -> [0] -> [1] -> [2] -> [3] <- tail
    //   step 3  size = 4        (tail untouched)

    append(value) { // O(1) thanks to tail pointer
        const node = new SLNode(value);
        if (this.isEmpty()) { this.head = node; this.tail = node; }
        else { this.tail.next = node; this.tail = node; }
        this.size++;
    }
    // TRACE append(1), append(2), append(3)   empty list
    //   append(1)  empty -> head = tail = [1]          size 1
    //   append(2)  tail.next = [2]; tail = [2]
    //              head -> [1] -> [2] <- tail          size 2
    //   append(3)  tail.next = [3]; tail = [3]
    //              head -> [1] -> [2] -> [3] <- tail   size 3   (no walking)

    removeFromFront() { // O(1)
        if (this.isEmpty()) return null;
        const value = this.head.value;
        this.head = this.head.next;
        if (!this.head) this.tail = null;
        this.size--;
        return value;
    }
    // TRACE removeFromFront()   head -> [0] -> [1] -> [2] -> [3] <- tail
    //   step 1  value = 0
    //   step 2  head = head.next     head -> [1] -> [2] -> [3] <- tail
    //   step 3  head not null -> tail stays [3];  size = 3   return 0

    removeFormEnd() { // O(n) — no back-pointer, must walk to find the second-to-last node
        if (this.isEmpty()) return null;
        const value = this.tail.value;
        if (this.size === 1) { this.head = null; this.tail = null; }
        else {
            let prev = this.head;
            while (prev.next !== this.tail) prev = prev.next;
            prev.next = null;
            this.tail = prev;
        }
        this.size--;
        return value;
    }
    // TRACE removeFormEnd()   head -> [1] -> [2] -> [3] <- tail   size 3
    //   step 1  value = 3, size 3 !== 1 -> prev = [1]
    //   step 2  [1].next = [2] !== tail -> prev = [2]
    //   step 3  [2].next = [3] === tail -> stop
    //   step 4  prev.next = null; tail = prev   head -> [1] -> [2] <- tail
    //   step 5  size = 2                 return 3
}
console.log("~~~~~~~~~~~~~~~~~~~~~ linked list tail");
const listTail = new LinkedListTail();
console.log(listTail.isEmpty(), listTail.getSize());
listTail.print();
listTail.append(1);
listTail.append(2);
listTail.append(3);
listTail.prepend(0);
listTail.print();
listTail.removeFromFront();
listTail.removeFormEnd();
listTail.print();
// GOTCHAS: removeFormEnd() is still O(n) with only a forward `next` pointer —
// only a DOUBLY linked list makes tail removal O(1) (see below).
// Because prepend/append/removeFromFront are all O(1) here, Stack and Queue
// can both be implemented cleanly on top of this structure:

// ---------------------- Stack via Linked List ----------------------
// [INTERMEDIATE] push/pop at head = O(1), avoids array-resizing overhead entirely.
class LinkedListStack {
    constructor() { this.list = new LinkedListTail(); }
    push(value) { this.list.prepend(value); }
    pop() { return this.list.removeFromFront(); }
    peek() { return this.list.head.value; }
    isEmpty() { return this.list.isEmpty(); }
    getSize() { return this.list.getSize(); }
    print() { return this.list.print(); }
}
// TRACE push(20), push(10), push(30), pop(), peek()   (all at the head)
//   start      isEmpty() -> true
//   push(20)   prepend -> head -> [20]
//   push(10)   prepend -> head -> [10] -> [20]
//   push(30)   prepend -> head -> [30] -> [10] -> [20]   getSize() 3
//   pop()      removeFromFront -> returns 30   head -> [10] -> [20]
//   peek()     head.value -> 10
const linkedlistStack = new LinkedListStack();
console.log(linkedlistStack.isEmpty());
linkedlistStack.push(20);
linkedlistStack.push(10);
linkedlistStack.push(30);
console.log(linkedlistStack.getSize());
linkedlistStack.print();
console.log(linkedlistStack.pop());
console.log(linkedlistStack.peek());

// ---------------------- Queue via Linked List ----------------------
// [INTERMEDIATE] enqueue at tail, dequeue at head = O(1) both ends.
class LinkedListqueue {
    constructor() { this.list = new LinkedListTail(); }
    enqueue(value) { this.list.append(value); }
    dequeue() { return this.list.removeFromFront(); }
    peek() { return this.list.head.value; }
    isEmpty() { return this.list.isEmpty(); }
    getSize() { return this.list.getSize(); }
    print() { return this.list.print(); }
}
// TRACE enqueue(10), enqueue(30), enqueue(20), dequeue(), peek()
//   start        isEmpty() -> true
//   enqueue(10)  append -> head -> [10] <- tail
//   enqueue(30)  append -> head -> [10] -> [30] <- tail
//   enqueue(20)  append -> head -> [10] -> [30] -> [20] <- tail   getSize() 3
//   dequeue()    removeFromFront -> returns 10   head -> [30] -> [20] <- tail
//   peek()       head.value -> 30
const linkedlistqueue = new LinkedListqueue();
console.log(linkedlistqueue.isEmpty());
linkedlistqueue.enqueue(10);
linkedlistqueue.enqueue(30);
linkedlistqueue.enqueue(20);
console.log(linkedlistqueue.getSize());
linkedlistqueue.print();
console.log(linkedlistqueue.dequeue());
linkedlistqueue.print();
console.log(linkedlistqueue.peek());

// ------------------------------ Doubly Linked List ------------------------------
// [INTERMEDIATE] Each node also has a `prev` pointer, enabling O(1) removal
// from BOTH ends and backward traversal.
//
// ASCII diagram:
//   null ◀── [0] ⇄ [1] ⇄ [2] ⇄ [3] ──▶ null
//   head ─────────────────────────▶ tail

class DLNode {
    constructor(value) {
        this.value = value;
        this.prev = null;
        this.next = null;
    }
}

class DoublyLinkedList {
    constructor() {
        this.head = null;
        this.tail = null;
        this.size = 0;
    }
    isEmpty() { return this.size === 0; }
    getSize() { return this.size; }
    // TRACE isEmpty() / getSize()   new list -> true, 0;  after demo appends/prepend -> false, 4

    prepend(value) {
        const node = new DLNode(value);
        if (this.isEmpty()) { this.head = node; this.tail = node; }
        else { node.next = this.head; this.head.prev = node; this.head = node; }
        this.size++;
    }
    // TRACE prepend(0)   head -> [1] ⇄ [2] ⇄ [3] <- tail
    //   step 1  node = [0]; node.next = head        [0] -> [1]
    //   step 2  head.prev = node                    [0] ⇄ [1]
    //   step 3  head = node    head -> [0] ⇄ [1] ⇄ [2] ⇄ [3] <- tail   size 4

    append(value) {
        const node = new DLNode(value);
        if (this.isEmpty()) { this.head = node; this.tail = node; }
        else { this.tail.next = node; node.prev = this.tail; this.tail = node; }
        this.size++;
    }
    // TRACE append(1), append(2), append(3)   empty list
    //   append(1)  empty -> head = tail = [1]
    //   append(2)  tail.next = [2]; [2].prev = [1]; tail = [2]   [1] ⇄ [2]
    //   append(3)  tail.next = [3]; [3].prev = [2]; tail = [3]   [1] ⇄ [2] ⇄ [3]   size 3

    removeFromFront() {
        if (this.isEmpty()) return null;
        const value = this.head.value;
        this.head = this.head.next;
        if (this.head) this.head.prev = null;
        else this.tail = null;
        this.size--;
        return value;
    }
    // TRACE removeFromFront()   head -> [0] ⇄ [1] ⇄ [2] <- tail
    //   step 1  value = 0; head = head.next = [1]
    //   step 2  head exists -> [1].prev = null    head -> [1] ⇄ [2] <- tail
    //   step 3  size = 2                          return 0

    removeFromEnd() { // O(1) — the whole benefit of the `prev` pointer
        if (this.isEmpty()) return null;
        const value = this.tail.value;
        if (this.size === 1) { this.head = null; this.tail = null; }
        else { this.tail = this.tail.prev; this.tail.next = null; }
        this.size--;
        return value;
    }
    // TRACE removeFromEnd()   head -> [0] ⇄ [1] ⇄ [2] ⇄ [3] <- tail   size 4
    //   step 1  value = 3; size !== 1
    //   step 2  tail = tail.prev = [2]   (no walking needed)
    //   step 3  tail.next = null         head -> [0] ⇄ [1] ⇄ [2] <- tail
    //   step 4  size = 3                 return 3

    print() {
        if (this.isEmpty()) { console.log("List is empty"); return; }
        let curr = this.head, out = "";
        while (curr) { out += `${curr.value}<->`; curr = curr.next; }
        console.log(out);
    }
    // TRACE print()   [0] ⇄ [1] ⇄ [2] ⇄ [3]   follow .next from head
    //   "0<->" -> "0<->1<->" -> "0<->1<->2<->" -> "0<->1<->2<->3<->"   logged

    printReverse() {
        if (this.isEmpty()) { console.log("List is empty"); return; }
        let curr = this.tail, out = "";
        while (curr) { out += `${curr.value}<->`; curr = curr.prev; }
        console.log(out);
    }
    // TRACE printReverse()   [0] ⇄ [1] ⇄ [2] ⇄ [3]   follow .prev from tail
    //   "3<->" -> "3<->2<->" -> "3<->2<->1<->" -> "3<->2<->1<->0<->"   logged
}

const doublelist = new DoublyLinkedList();
doublelist.append(1);
doublelist.append(2);
doublelist.append(3);
doublelist.prepend(0);
doublelist.print();
doublelist.printReverse();
doublelist.removeFromEnd();
doublelist.print();
doublelist.removeFromFront();
doublelist.print();
// Big-O: prepend/append/removeFromFront/removeFromEnd all O(1) | search O(n)
// GOTCHAS: every extra `prev` pointer costs memory — DLL uses ~2x pointer
// storage vs a singly linked list. Only pay for it if you need backward
// traversal or O(1) tail removal.
// INTERVIEW: DLL underlies LRUCache (see 12-lru-cache.js) and browser
// back/forward history.

// COMPARISON TABLE — Array vs Linked List
// ┌───────────────────────┬───────────────────┬───────────────────────┐
// │                        │ Array              │ Linked List            │
// ├───────────────────────┼───────────────────┼───────────────────────┤
// │ Random access           │ O(1)               │ O(n)                   │
// │ Insert/delete at start  │ O(n)               │ O(1)                   │
// │ Insert/delete at end    │ O(1) (push/pop)    │ O(1) w/ tail, else O(n)│
// │ Memory layout            │ contiguous         │ scattered (+ pointers) │
// │ Cache friendliness       │ high               │ low                    │
// │ Resize cost               │ occasional realloc │ none needed            │
// └───────────────────────┴───────────────────┴───────────────────────┘
