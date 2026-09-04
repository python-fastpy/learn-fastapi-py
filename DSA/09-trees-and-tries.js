/* ============================================================================
 * TREES — BINARY SEARCH TREE & TRIE  [INTERMEDIATE / ADVANCED]
 * ============================================================================
 * - A tree is a hierarchical, non-linear DS: nodes connected by edges, no
 *   cycles. Non-linear structures allow faster search than linear ones.
 * Usage: file systems, DOM, org charts, ASTs, chat bot decision trees.
 * ==========================================================================*/

// ------------------------------ Binary Search Tree ------------------------------
// [INTERMEDIATE/ADVANCED]
// - Binary tree: each node has at most 2 children (left, right).
// - BST invariant: left subtree values < node < right subtree values.
//
// ASCII diagram (after inserting 10, 5, 15, 3, 7):
//                 10
//               /    \
//              5      15
//            /   \
//           3     7
//
// Ops: insert, search, DFS (preorder/inOrder/postOrder), BFS (levelOrder),
//      min, max, delete
// Usage: searching, sorting, lookup tables, priority queues.

class BSTNode {
    constructor(value) {
        this.value = value;
        this.left = null;
        this.right = null;
    }
}

class BinarySearchTree {
    constructor() {
        this.root = null;
    }

    isEmpty() { return this.root === null; }

    insert(value) {
        const node = new BSTNode(value);
        if (this.isEmpty()) this.root = node;
        else this.insertNode(this.root, node);
    }

    insertNode(root, newNode) {
        if (newNode.value < root.value) {
            if (root.left === null) root.left = newNode;
            else this.insertNode(root.left, newNode);
        } else {
            if (root.right === null) root.right = newNode;
            else this.insertNode(root.right, newNode);
        }
    }

    search(root, value) {
        if (!root) return false;
        if (root.value === value) return true;
        return value < root.value
            ? this.search(root.left, value)
            : this.search(root.right, value);
    }

    preorder(root) {
        if (!root) return;
        console.log(root.value);
        this.preorder(root.left);
        this.preorder(root.right);
    }

    inOrder(root) {
        if (!root) return;
        this.inOrder(root.left);
        console.log(root.value);
        this.inOrder(root.right);
    }

    postOrder(root) {
        if (!root) return;
        this.postOrder(root.left);
        this.postOrder(root.right);
        console.log(root.value);
    }

    levelOrder() {
        // BFS — plain array used as a queue (push at rear, shift from front).
        // See 06-queues.js for an O(1)-dequeue QueueObj if this were hot-path code.
        const queue = [this.root];
        while (queue.length) {
            const curr = queue.shift();
            console.log(curr.value);
            if (curr.left) queue.push(curr.left);
            if (curr.right) queue.push(curr.right);
        }
    }

    min(root) { return root.left ? this.min(root.left) : root.value; }
    max(root) { return root.right ? this.max(root.right) : root.value; }

    delete(value) { this.root = this.deleteNode(this.root, value); }

    deleteNode(root, value) {
        if (root === null) return root;
        if (value < root.value) {
            root.left = this.deleteNode(root.left, value);
        } else if (value > root.value) {
            root.right = this.deleteNode(root.right, value);
        } else {
            // found the node to delete
            if (!root.left && !root.right) return null;          // no children
            if (!root.left) return root.right;                    // one child (right)
            if (!root.right) return root.left;                    // one child (left)
            // two children: replace value with min of right subtree, then delete that min
            root.value = this.min(root.right);
            root.right = this.deleteNode(root.right, root.value);
        }
        return root;
    }
}

let bst = new BinarySearchTree();
console.log(bst.isEmpty());
bst.insert(10);
bst.insert(5);
bst.insert(15);
bst.insert(3);
bst.insert(7);

console.log(bst.search(bst.root, 10));
console.log(bst.search(bst.root, 5));
console.log(bst.search(bst.root, 15));
console.log(bst.search(bst.root, 20));

bst.preorder(bst.root);  // 10 5 3 7 15
bst.inOrder(bst.root);   // 3 5 7 10 15
bst.postOrder(bst.root); // 3 7 5 15 10
bst.levelOrder();        // 10 5 15 3 7

console.log(bst.min(bst.root));
console.log(bst.max(bst.root));
bst.delete(5);
bst.inOrder(bst.root); // 3 7 10 15

// Big-O (average, on a balanced tree): insert/search/delete O(log n)
// Worst case (degenerates into a linked list, e.g. inserting sorted data): O(n)
//
// GOTCHAS:
// - A plain BST is NOT self-balancing; inserting sorted input turns it into
//   a linked list (all O(n)). Self-balancing variants: AVL, Red-Black trees.
// - Deleting a two-children node requires the in-order successor (min of right
//   subtree) or predecessor (max of left subtree) — a very common interview trap.
// INTERVIEW: "delete a node from a BST" (3 cases: leaf / one child / two children)
// and "validate a BST" are extremely common questions.

// ------------------------------ Trie (Prefix Tree) ------------------------------
// [ADVANCED]
// - Tree where each path from root spells out a prefix; nodes are shared
//   between words with common prefixes. Great for autocomplete/spell-check.
//
// ASCII diagram (inserted "cat", "car", "dog"):
//   root
//    ├─ c ─ a ─ t*      (t marked isEndOfWord)
//    │       └─ r*
//    └─ d ─ o ─ g*
//
// Ops: insert, search (exact word), startsWith (prefix check)

class TrieNode {
    constructor() {
        this.children = new Map(); // char -> TrieNode
        this.isEndOfWord = false;
    }
}

class Trie {
    constructor() {
        this.root = new TrieNode();
    }

    insert(word) { // O(k), k = word length
        let curr = this.root;
        for (const ch of word) {
            if (!curr.children.has(ch)) curr.children.set(ch, new TrieNode());
            curr = curr.children.get(ch);
        }
        curr.isEndOfWord = true;
    }

    search(word) { // O(k) — exact word match
        const node = this.#traverse(word);
        return node !== null && node.isEndOfWord;
    }

    startsWith(prefix) { // O(k) — used for autocomplete
        return this.#traverse(prefix) !== null;
    }

    #traverse(str) {
        let curr = this.root;
        for (const ch of str) {
            if (!curr.children.has(ch)) return null;
            curr = curr.children.get(ch);
        }
        return curr;
    }
}

const trie = new Trie();
trie.insert("cat");
trie.insert("car");
trie.insert("dog");
console.log(trie.search("cat"));       // true
console.log(trie.search("ca"));        // false (not a full word)
console.log(trie.startsWith("ca"));    // true (prefix exists)
console.log(trie.startsWith("do"));    // true
console.log(trie.search("dogs"));      // false

// Big-O: insert/search/startsWith all O(k) where k = string length (NOT
// dependent on how many words are stored — huge advantage over scanning an array).
//
// GOTCHAS:
// - Memory heavy: every node can fan out to 26+ children; use a Map (not a
//   fixed array) when the alphabet is large or sparse (unicode, etc).
// - Don't forget to mark isEndOfWord — otherwise "car" being a prefix of
//   nothing else still won't register as a complete word.
// INTERVIEW: Trie == the go-to answer for "autocomplete", "spell checker",
// "longest common prefix", "word search II".
