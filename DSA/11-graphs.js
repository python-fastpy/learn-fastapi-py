/* ============================================================================
 * GRAPHS  [ADVANCED]
 * ============================================================================
 * - A graph is a set of vertices (nodes) connected by edges; can be directed
 *   or undirected, weighted or unweighted. Trees are a special case of graphs
 *   (no cycles, one path between any two nodes).
 *
 * ASCII diagram (undirected graph):
 *    A ─── B
 *    │     │
 *    C ─── D ─── E
 *
 *   adjacency list: A:[B,C]  B:[A,D]  C:[A,D]  D:[B,C,E]  E:[D]
 *
 * Usage: social networks, maps/routing, dependency graphs, recommendation engines.
 * Representations: adjacency list (space-efficient, used below) vs adjacency matrix.
 * ==========================================================================*/

class Graph {
    constructor() {
        this.adjacencyList = new Map(); // vertex -> Set of neighbor vertices
    }

    addVertex(vertex) {
        if (!this.adjacencyList.has(vertex)) this.adjacencyList.set(vertex, new Set());
    }

    addEdge(v1, v2) { // undirected: add both directions
        this.addVertex(v1);
        this.addVertex(v2);
        this.adjacencyList.get(v1).add(v2);
        this.adjacencyList.get(v2).add(v1);
    }
    // TRACE addEdge("A","B") then addEdge("A","C")   (addVertex called inside)
    //   addVertex A -> A:{}        addVertex B -> B:{}
    //   A.add(B), B.add(A)         -> A:{B}  B:{A}
    //   addVertex A (exists, skip) addVertex C -> C:{}
    //   A.add(C), C.add(A)         -> A:{B,C}  B:{A}  C:{A}

    removeEdge(v1, v2) {
        this.adjacencyList.get(v1)?.delete(v2);
        this.adjacencyList.get(v2)?.delete(v1);
    }
    // TRACE removeEdge("D","B")   before: B:{A,D}  D:{B,C,E}
    //   D.delete(B) -> D:{C,E}
    //   B.delete(D) -> B:{A}

    removeVertex(vertex) {
        for (const neighbor of this.adjacencyList.get(vertex) || []) {
            this.removeEdge(vertex, neighbor);
        }
        this.adjacencyList.delete(vertex);
    }
    // TRACE removeVertex("D")   graph from demo: A:{B,C} B:{A,D} C:{A,D} D:{B,C,E} E:{D}
    //   neighbor B: removeEdge(D,B) -> B:{A}    D:{C,E}
    //   neighbor C: removeEdge(D,C) -> C:{A}    D:{E}
    //   neighbor E: removeEdge(D,E) -> E:{}     D:{}
    //   delete D    -> A:{B,C}  B:{A}  C:{A}  E:{}

    bfs(start) {
        // level-by-level traversal using a plain array as a queue.
        // See 06-queues.js for an O(1)-dequeue QueueObj if this were hot-path code.
        const visited = new Set([start]);
        const queue = [start];
        const order = [];
        while (queue.length) {
            const vertex = queue.shift();
            order.push(vertex);
            for (const neighbor of this.adjacencyList.get(vertex) || []) {
                if (!visited.has(neighbor)) {
                    visited.add(neighbor);
                    queue.push(neighbor);
                }
            }
        }
        return order;
    }
    // TRACE bfs("A")   graph:  A ─── B
    //                          │     │
    //                          C ─── D ─── E
    //   step | shift | neighbors | enqueue | queue after | visited
    //   0    |       |           |         | [A]         | {A}
    //   1    | A     | B,C       | B,C     | [B,C]       | {A,B,C}
    //   2    | B     | A,D       | D       | [C,D]       | {A,B,C,D}
    //   3    | C     | A,D       | -       | [D]         | {A,B,C,D}
    //   4    | D     | B,C,E     | E       | [E]         | {A,B,C,D,E}
    //   5    | E     | D         | -       | []          | {A,B,C,D,E}
    //   result: [A, B, C, D, E]

    dfs(start) { // depth-first traversal using recursion (a call stack)
        const visited = new Set();
        const order = [];
        const traverse = (vertex) => {
            if (!vertex || visited.has(vertex)) return;
            visited.add(vertex);
            order.push(vertex);
            for (const neighbor of this.adjacencyList.get(vertex) || []) {
                traverse(neighbor);
            }
        };
        traverse(start);
        return order;
    }
    // TRACE dfs("A")   same graph (A:[B,C] B:[A,D] C:[A,D] D:[B,C,E] E:[D])
    //   step | visiting | call stack     | visited
    //   1    | A        | A              | {A}
    //   2    | B        | A > B          | {A,B}        (B's A already visited)
    //   3    | D        | A > B > D      | {A,B,D}      (D's B already visited)
    //   4    | C        | A > B > D > C  | {A,B,D,C}    (C's A, D visited -> return)
    //   5    | E        | A > B > D > E  | {A,B,D,C,E}  (E's D visited -> return)
    //   unwind D, B; back at A: C already visited -> done
    //   result: [A, B, D, C, E]

    dfsIterative(start) {
        // same result as dfs(), but with an explicit array-as-stack (no recursion).
        // See 05-stacks.js for a dedicated Stack class if you want named push/pop/isEmpty.
        const visited = new Set();
        const order = [];
        const stack = [start];
        while (stack.length) {
            const vertex = stack.pop();
            if (visited.has(vertex)) continue;
            visited.add(vertex);
            order.push(vertex);
            for (const neighbor of this.adjacencyList.get(vertex) || []) {
                stack.push(neighbor);
            }
        }
        return order;
    }
    // TRACE dfsIterative("A")   same graph (A:[B,C] B:[A,D] C:[A,D] D:[B,C,E] E:[D])
    //   step | pop | action | stack after     | visited
    //   0    |     |        | [A]             | {}
    //   1    | A   | visit  | [B,C]           | {A}
    //   2    | C   | visit  | [B,A,D]         | {A,C}
    //   3    | D   | visit  | [B,A,B,C,E]     | {A,C,D}
    //   4    | E   | visit  | [B,A,B,C,D]     | {A,C,D,E}
    //   5    | D   | skip   | [B,A,B,C]       |
    //   6    | C   | skip   | [B,A,B]         |
    //   7    | B   | visit  | [B,A,A,D]       | {A,C,D,E,B}
    //   8-11 | D,A,A,B all skip -> []
    //   result: [A, C, D, E, B]  (last-pushed neighbor goes first, so differs from dfs())

    print() {
        for (const [vertex, neighbors] of this.adjacencyList) {
            console.log(vertex, "->", [...neighbors].join(", "));
        }
    }
    // TRACE print()   demo graph, Map keeps insertion order A,B,C,D,E
    //   A -> B, C
    //   B -> A, D
    //   C -> A, D
    //   D -> B, C, E
    //   E -> D
}

const graph = new Graph();
graph.addEdge("A", "B");
graph.addEdge("A", "C");
graph.addEdge("B", "D");
graph.addEdge("C", "D");
graph.addEdge("D", "E");
graph.print();
console.log("BFS from A:", graph.bfs("A")); // A B C D E
console.log("DFS from A:", graph.dfs("A")); // A B D C E
console.log("DFS (iterative) from A:", graph.dfsIterative("A"));

// Big-O: addVertex O(1) | addEdge O(1) | BFS/DFS O(V + E) (V=vertices, E=edges)
//
// GOTCHAS:
// - BFS finds the SHORTEST PATH in an unweighted graph; DFS does not.
// - Recursive DFS can blow the call stack on very deep/large graphs — use the
//   iterative version (explicit stack) for huge graphs.
// - Must track `visited` or you'll infinite-loop on any cycle.
// - Adjacency list is O(V+E) space and fast for sparse graphs; adjacency
//   matrix is O(V^2) space but O(1) edge lookup — better for dense graphs.
// INTERVIEW: BFS = shortest path/levels ("number of islands", "rotting oranges");
// DFS = connectivity/backtracking ("clone graph", "course schedule" cycle detection).
