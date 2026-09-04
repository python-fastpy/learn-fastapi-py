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

    prepend(value) { // O(1)
        const node = new SLNode(value);
        if (this.isEmpty()) this.head = node;
        else { node.next = this.head; this.head = node; }
        this.size++;
    }

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

    print() {
        if (this.isEmpty()) { console.log("List is Empty"); return; }
        let curr = this.head, listValue = "";
        while (curr) { listValue += `${curr.value} `; curr = curr.next; }
        console.log(listValue);
    }
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

    print() {
        if (this.isEmpty()) { console.log("List is Empty"); return; }
        let curr = this.head, listValues = "";
        while (curr) { listValues += `${curr.value} `; curr = curr.next; }
        console.log(listValues);
    }

    prepend(value) {
        const node = new SLNode(value);
        if (this.isEmpty()) { this.head = node; this.tail = node; }
        else { node.next = this.head; this.head = node; }
        this.size++;
    }

    append(value) { // O(1) thanks to tail pointer
        const node = new SLNode(value);
        if (this.isEmpty()) { this.head = node; this.tail = node; }
        else { this.tail.next = node; this.tail = node; }
        this.size++;
    }

    removeFromFront() { // O(1)
        if (this.isEmpty()) return null;
        const value = this.head.value;
        this.head = this.head.next;
        if (!this.head) this.tail = null;
        this.size--;
        return value;
    }

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

    prepend(value) {
        const node = new DLNode(value);
        if (this.isEmpty()) { this.head = node; this.tail = node; }
        else { node.next = this.head; this.head.prev = node; this.head = node; }
        this.size++;
    }

    append(value) {
        const node = new DLNode(value);
        if (this.isEmpty()) { this.head = node; this.tail = node; }
        else { this.tail.next = node; node.prev = this.tail; this.tail = node; }
        this.size++;
    }

    removeFromFront() {
        if (this.isEmpty()) return null;
        const value = this.head.value;
        this.head = this.head.next;
        if (this.head) this.head.prev = null;
        else this.tail = null;
        this.size--;
        return value;
    }

    removeFromEnd() { // O(1) — the whole benefit of the `prev` pointer
        if (this.isEmpty()) return null;
        const value = this.tail.value;
        if (this.size === 1) { this.head = null; this.tail = null; }
        else { this.tail = this.tail.prev; this.tail.next = null; }
        this.size--;
        return value;
    }

    print() {
        if (this.isEmpty()) { console.log("List is empty"); return; }
        let curr = this.head, out = "";
        while (curr) { out += `${curr.value}<->`; curr = curr.next; }
        console.log(out);
    }

    printReverse() {
        if (this.isEmpty()) { console.log("List is empty"); return; }
        let curr = this.tail, out = "";
        while (curr) { out += `${curr.value}<->`; curr = curr.prev; }
        console.log(out);
    }
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
