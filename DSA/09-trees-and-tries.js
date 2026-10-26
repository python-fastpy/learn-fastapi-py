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
    // TRACE isEmpty() on new tree: root = null -> true

    insert(value) {
        const node = new BSTNode(value);
        if (this.isEmpty()) this.root = node;
        else this.insertNode(this.root, node);
    }
    // TRACE insert(10), insert(5)
    //   insert(10): tree empty -> root = 10
    //   insert(5):  tree not empty -> insertNode(root=10, node 5)
    //                10
    //               /
    //              5

    insertNode(root, newNode) {
        if (newNode.value < root.value) {
            if (root.left === null) root.left = newNode;
            else this.insertNode(root.left, newNode);
        } else {
            if (root.right === null) root.right = newNode;
            else this.insertNode(root.right, newNode);
        }
    }
    // TRACE insert(7)   tree:     10
    //                            /  \
    //                           5    15
    //                          /
    //                         3
    //   step 1  at 10: 7 < 10 -> left is 5 -> recurse
    //   step 2  at 5:  7 > 5  -> right is null -> place 7
    //                             10
    //                            /  \
    //                           5    15
    //                          / \
    //                         3   7

    search(root, value) {
        if (!root) return false;
        if (root.value === value) return true;
        return value < root.value
            ? this.search(root.left, value)
            : this.search(root.right, value);
    }
    // TRACE search(root, 20)   tree: 10 / (5: 3, 7) / 15
    //   step 1  at 10: 20 > 10 -> go right
    //   step 2  at 15: 20 > 15 -> go right
    //   step 3  root = null    -> return false
    // (search 5: at 10, 5 < 10 -> left; at 5: match -> true)

    preorder(root) {
        if (!root) return;
        console.log(root.value);
        this.preorder(root.left);
        this.preorder(root.right);
    }
    // TRACE preorder(root)   tree:   10
    //                              /    \
    //                             5      15
    //                           /   \
    //                          3     7
    //   pre(10) print 10 -> pre(5) print 5 -> pre(3) print 3 -> (null, null)
    //   back to 5  -> pre(7) print 7 -> (null, null)
    //   back to 10 -> pre(15) print 15 -> (null, null)
    //   output: 10 5 3 7 15   (node, left, right)

    inOrder(root) {
        if (!root) return;
        this.inOrder(root.left);
        console.log(root.value);
        this.inOrder(root.right);
    }
    // TRACE inOrder(root)   same tree (10 / 5,15 / 3,7)
    //   in(10) -> in(5) -> in(3) -> left null, print 3, right null
    //   back to 5  -> print 5  -> in(7) -> print 7
    //   back to 10 -> print 10 -> in(15) -> print 15
    //   output: 3 5 7 10 15   (left, node, right = sorted)

    postOrder(root) {
        if (!root) return;
        this.postOrder(root.left);
        this.postOrder(root.right);
        console.log(root.value);
    }
    // TRACE postOrder(root)   same tree (10 / 5,15 / 3,7)
    //   post(10) -> post(5) -> post(3) -> print 3
    //   back to 5  -> post(7) -> print 7 -> then print 5
    //   back to 10 -> post(15) -> print 15 -> then print 10
    //   output: 3 7 5 15 10   (left, right, node)

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
    // TRACE levelOrder()   same tree (10 / 5,15 / 3,7)
    //   step | shift -> print | push children | queue after
    //   0    |                |               | [10]
    //   1    | 10             | 5, 15         | [5, 15]
    //   2    | 5              | 3, 7          | [15, 3, 7]
    //   3    | 15             | -             | [3, 7]
    //   4    | 3              | -             | [7]
    //   5    | 7              | -             | []  -> done
    //   output: 10 5 15 3 7

    min(root) { return root.left ? this.min(root.left) : root.value; }
    max(root) { return root.right ? this.max(root.right) : root.value; }
    // TRACE min(root) / max(root)   same tree (10 / 5,15 / 3,7)
    //   min: at 10 left=5 -> at 5 left=3 -> at 3 left=null -> 3
    //   max: at 10 right=15 -> at 15 right=null -> 15

    delete(value) { this.root = this.deleteNode(this.root, value); }
    // TRACE delete(5): root = deleteNode(10, 5) -> returns 10 (see below)

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
    // TRACE deleteNode(root, 5)   tree:     10
    //                                      /  \
    //                                     5    15
    //                                    / \
    //                                   3   7
    //   step 1  at 10: 5 < 10 -> root.left = deleteNode(5, 5)
    //   step 2  at 5:  match, two children -> min(right=7) = 7 -> value = 7
    //   step 3  root.right = deleteNode(7, 7): leaf -> returns null
    //   step 4  node(7) returned to 10.left; 10 returned as new root
    //                             10
    //                            /  \
    //                           7    15
    //                          /
    //                         3
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
    // TRACE insert("car")   trie already has "cat":  root ─ c ─ a ─ t*
    //   'c'  root has c -> reuse     curr = c
    //   'a'  c has a    -> reuse     curr = a
    //   'r'  a has no r -> create r  curr = r
    //   end: r.isEndOfWord = true
    //   root ─ c ─ a ─ t*
    //               └─ r*

    search(word) { // O(k) — exact word match
        const node = this.#traverse(word);
        return node !== null && node.isEndOfWord;
    }
    // TRACE search("cat") / search("ca")   trie: cat, car, dog
    //   "cat": traverse -> node t, t.isEndOfWord = true  -> true
    //   "ca":  traverse -> node a, a.isEndOfWord = false -> false

    startsWith(prefix) { // O(k) — used for autocomplete
        return this.#traverse(prefix) !== null;
    }
    // TRACE startsWith("ca")   traverse -> node a (not null) -> true

    #traverse(str) {
        let curr = this.root;
        for (const ch of str) {
            if (!curr.children.has(ch)) return null;
            curr = curr.children.get(ch);
        }
        return curr;
    }
    // TRACE #traverse("dogs")   trie: cat, car, dog
    //   'd'  root has d -> curr = d
    //   'o'  d has o    -> curr = o
    //   'g'  o has g    -> curr = g
    //   's'  g has no s -> return null   (so search("dogs") = false)
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
