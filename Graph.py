import heapq

class Vertex:
    # Assume that a Vertex is immutable
    def __init__(self, x):
        # Must have immutable value x
        self.val = x

    def copy(self):
        return Vertex(self.val)

    def serialize(self):
        return str(self.val)

    @staticmethod
    def deserialize(val):
        return Vertex(val)

    def __str__(self):
        return "vertex %r" % self.val

    def __repr__(self):
        return "Vertex(%r)" % self.val

    def __hash__(self):
        return hash(self.val)

    def __eq__(self, other):
        return isinstance(other, Vertex) and other.val == self.val

    def __lt__(self, other):
        return self if self.val < other.val else other

    def __le__(self, other):
        return self if self.val <= other.val else other

    def __gt__(self, other):
        return self if self.val > other.val else other

    def __ge__(self, other):
        return self if self.val >= other.val else other

class Graph:
    def __init__(self, vertices=None, edges=None):
        # Can construct a graph via edges adjacency set (u -> {v1: w1, v2: w2}, ...})
        # For ease of use, the vertices are assumed to not be be of type Graph.Vertex(x)
        self.vertices = set() if vertices is None else vertices
        # Adjacency set for all the edges - {u: {v1: w1, v2: w2, ...}, ...}
        self.edges = {} if edges is None else edges

    def getVertices(self):
        return self.vertices  # Consider making deep copies to prevent aliasing/rep exposure issues

    def getEdges(self):
        return self.edges

    def getChildren(self, u):
        assert isinstance(u, Vertex) and u in self.vertices
        # Can instead yield from a generator for better performance, since there could be a lot of children
        if u in self.edges:
            return (v for v in self.edges[u].keys())
        else:
            return ()

    def __getitem__(self, item):
        return self.edges.get(item, {})

    def __setitem__(self, key, value):
        assert isinstance(key, Vertex)
        assert isinstance(value, dict) and all(isinstance(v, Vertex) for v in value)
        self.edges[key] = value

    def getWeight(self, u, v):
        # Given vertices u and v, get the weight of the edge (u, v)
        # Returns 0 if (u, v) not in the graph
        if u not in self.edges or v not in self.edges[u]:
            raise ValueError("Edge not present in graph: %r, %r" % (u, v))
        return self.edges[u][v]

    def __contains__(self, item):
        return item in self.vertices and item in self.edges

    def addEdge(self, u, v, w=0):  # Unweighted edges by default
        # TODO: clean this up
        # Lazy way of making graph creation easier by specifying numbers in addEdge()
        # (instead of wrapping every number x with Vertex(x))
        if not isinstance(u, Vertex):
            u = Vertex(u)
        if not isinstance(v, Vertex):
            v = Vertex(v)
        # Adds edge (u, v) with weight w to the Graph
        # Undefined behavior if we call addEdge(u, v, w) if there is already edge (u,v)
        if u in self.edges.keys():
            self.edges[u][v] = w
        else:
            self.edges[u] = {v: w}

        # Add new vertices if an edge connects ones not already in the graph
        self.vertices = self.vertices.union({u, v})

    def addVertex(self, x):
        self.vertices.add(Vertex(x))

    def serialize(self) -> dict:
        """Serializes the graph into a Python dictionary, with each vertex also serialized.
        Format: {str: {str: int, ...}, ...}
        """
        result = {}
        for u in self.edges:
            uStr = u.serialize()
            for v in self.edges[u]:
                vStr = v.serialize()
                if uStr not in result:
                    result[uStr] = {vStr: self.edges[u][v]}
                else:
                    result[uStr][vStr] = self.edges[u][v]
        return result

    @staticmethod
    def deserialize(data):
        G = Graph()
        for ustr in data:
            u = Vertex.deserialize(ustr)
            for vstr in data[u]:
                v = Vertex.deserialize(vstr)
                G.addEdge(u, v)
        return G

    def bfs(self, start, target):
        # Given a graph/adjacency matrix/adjacency set, (in 6.006 ex create dict of paths to all V) find SP to target
        queue, visited, parents = [start], {start}, {start: start}
        while queue:  # While there are still items in the queue (FIFO)
            # Pop off first node in the current queue; once nodes in curr lvl set popped, next lvl set will be formed
            node = queue.pop(0)
            if node == target:  # Short circuit if found the target node
                break

            # Push all neighbors for the next level set onto queue, add to seen, add parent pointers etc
            for neighbor in self.getChildren(node):
                if neighbor not in visited:  # Make sure to not visit any already visited nodes
                    parents[neighbor] = node
                    queue.append(neighbor)
                    visited.add(neighbor)

        if target not in parents:  # No path exists/target doesn't have a parent node
            return None
        # Invariant at this point is that start, target \in parents set, and so \exists a path from start~~>target
        # Now, construct path from start to target
        i, path = target, [target]
        while i != start:  # Potentially O(V) loop here
            i = parents[i]
            path.append(i)

        return path[::-1]  # Reverse path so that it is from start to target

    def dfs(self, start, target):
        # Given graph/adjacency matrix/adjacency set, return *a* path from start to target, using depth-first search
        stack, visited, parents = [start], {start}, {start: start}

        # Difference between BFS and DFS is queue vs stack -> popping off from front vs back for next node to be processed
        while stack:  # While items still on stack
            curr_node = stack.pop()  # Use last element of stack as current (ie LIFO policy)
            visited.add(curr_node)
            if curr_node == target: break  # If found the target node, short circuit
            # Loop through all neighbors of current node, add them to stack if not visit
            for next_node in self.getChildren(curr_node):
                if next_node not in visited:
                    parents[next_node] = curr_node
                    stack.append(next_node)

        if target not in parents:
            return None
        # Now found the target node, want to construct path from start to target
        i, path = target, [target]
        while i != start:  # Potentially O(V) loop here
            i = parents[i]
            path.append(i)

        return path[::-1]  # Reverse path so that it is from start to target

    def relax(self, u, v, d, p=None, pq=None, curr_d=None):
        """
        If current "shortest" distance from s to v is greater than shortest distance from s to u + w(u,v), then set
        the new shortest distance from s to v to be = newly found shortest distance d(s,u) + w(u,v).
        Return the boolean result from the triangle inequality condition mentioned above as well.
        Better explained by illustration: d(s,v) <- d(s,u) + w(u,v) if d(s,v) > d(s,u) + w(u,v)
                   d(s,v)
                s ~~~~~~> v
                |      /
                |     /
         d(s,u) |    /
                |   /  w(u,v)
                |  /
                | /
                u
        Additional params pq and curr_d used by Dijkstra's to update the vertex heap
        p used by both Dijkstra's and Bellman Ford, etc to find shortest path by following predecessors to source
        @param u first input vertex
        @param v second input vertex
        @param d current shortest path distances mapping
        @param p predecessor mapping, default to None
        @param pq priority queue of vertices ordered by key=distance
        @param curr_d current distance away from source
        """
        assert u in d and v in d and u in self.edges and v in self.edges[u]
        if d[v] > d[u] + self.edges[u][v]:
            d[v] = d[u] + self.edges[u][v]
            if p is not None:
                p[v] = u
            if pq is not None:
                assert curr_d is not None
                heapq.heappush(pq, (curr_d + self.edges[u][v], v))

    def verifyDAG(self, s):
        """
        In order for the SSSP by topological sort to work, ensure that this graph is a directed acyclic graph (DAG),
        for the nodes reachable by s
        @param s specifying source node s to make traversal start easier
        """
        # Find presence of a back edge, if none, then the nodes reachable from s + edges traversed form a DAG
        curr_nodes = set()

        def traverse(root):
            curr_nodes.add(root)
            for child in self.getChildren(root):
                if child in curr_nodes:
                    assert False
                traverse(child)
            curr_nodes.remove(root)  # Important, to keep nodes in the stack updated

        return traverse(s)

    def dijkstra_SSSP(self, source):
        """
        Dijkstra's algorithm for single-source shortest paths, given a start and target Vertex.
        Note: graph must not contain any cycles with negative weights (for now, just restrict the graph to be a DAG)
        Since this implementation uses heaps, our runtime complexity of Dijkstra's Algorithm is:
        O(|E| * T(decrease_key()) + |V| * T(extract_min()))
        -> O((|E| + |V|) log |V|)
            since the heappush for decrease key and heappop's readjusting after extracting min are both O(log |V|). 
        @param source: source node
        @return: 1. mapping of the shortest distances between source and every vertex (default d(s, s) <- 0)
                 2. mapping of every node to its parent in its corresponding shortest path (see: subpaths of SP's
                 are themselves SPs, and triangle inequality for why this works)
        """
        self.verifyDAG(source)
        d = {}
        for v in self.vertices:
            d[v] = float('inf')
        d[source] = 0
        visited = set()
        priority_queue = [(0, source)]
        parentMap = {source: source}

        while priority_queue:
            curr_d, u = heapq.heappop(priority_queue)
            if curr_d > d[u]:
                continue
            visited.add(u)
            for v in self.getChildren(u):
                self.relax(u, v, d, parentMap, priority_queue, curr_d)

        return d, parentMap

    def bellmanFord_SSSP(self, source):
        """
        Bellman-Ford algorithm for single source shortest paths. Detects negative cycles in addition to providing
        the cycle itself if applicable, o/w returns the mapping of the sp distance from source to each vertex,
        and the predecessor mapping to help construct shortest paths.
        Runtime complexity: O(|V||E|) since we need to iterate over every vertex and for each, relax each edge.
        Correctness: We need this VE loop to guarantee that every edge is optimally relaxed. Each outer iteration
            only reduces the shortest path distance from source to each vertex. At iteration i of this loop, we know
            that d[v] is at most the weight of any path from source to v using at most i edges:
                d[v] <= minWeight(p) : len(p) <= i-1
            where p is a given path. We also know that if there is no negative cycle, then the shortest path will have
            at most |V| vertices, ie |V*| <= |V|.
            A negative cycle must also be found (and no false positives either) since it only identifies the cycle if
            for some vertex u,
        @param source: input source node
        @return: 1. A negative cycle if it exists, as a list of vertices. None o/w
                 2. Mapping of the shortest distances between source and every vertex. None if negative cycle exists.
                 3. Mapping of predecessors, None if negative cycle exists
        """
        d, p = {}, {}  # Initialize sp distances mapping and predecessor mapping
        for v in self.vertices:
            d[v] = float('inf')
        d[source] = 0

        for _ in self.vertices:
            for u in self.edges:
                for v in self.edges[u]:
                    self.relax(u, v, d, p)

        for u in self.edges:
            for v in self.edges[u]:
                if d[v] > d[u] + self.getWeight(u, v):
                    return self.getCycle(v, p), None, None

        return None, d, p

    def getCycle(self, v, p):
        """
        Assuming that a negative weight cycle exists in the graph, return it by following the predecessors until
        a seen vertex along the predecessor path is seen again. Output vertices only on the cycle itself (without any
        of the vertices used to reach the cycle).
        @param v: Input vertex where cycle was detected via Bellman Ford, not necessarily already on the cycle path
        @param p: predecessor mapping
        @return: list of vertices in the cycle
        """
        seen, cycle = set(), []
        nextNode = v
        # No infinite loop if there isn't a cycle, since p[source] = source, just garbage return value
        while nextNode not in seen:
            seen.add(nextNode)
            cycle.append(nextNode)
            nextNode = p[nextNode]
        lastNode = nextNode
        cycle.append(lastNode)  # Have the repeat just to emphasize that it is a cycle

        # If reached the original v, then the following does nothing. o/w we delete all vertices needed to reach a
        # vertex in the cycle by identifying the index where the first cycle vertex occurred in our predecessor walk
        firstOccurIdx = cycle.index(lastNode)  # Gets the index of the first occurrence of the lastNode Vertex
        del cycle[:firstOccurIdx]  # Removes all vertices used to reach cycle, ie up to but not including firstOccurIdx

        return list(reversed(cycle))  # Reversed since we followed predecessors backwards to identify cycle

    def printSSSPs(self, source, desiredVertices=None):
        """
        Prints the SSSP from source to each vertex in desiredVertices. Uses Dijkstra's Algorithm for SSSP.
        @param source input source node
        @param desiredVertices: if None, then assume all vertices are desired
        """
        if desiredVertices is None:
            desiredVertices = self.getVertices()
        assert all(isinstance(v, Vertex) for v in desiredVertices)
        d, p = self.dijkstra_SSSP(source)
        # _, d, p = self.bellmanFord_SSSP(source)
        for v in desiredVertices:
            if v not in p or v not in desiredVertices:
                continue
            i, path = v, [v]
            while i != source:  # Potentially O(V) loop here
                i = p[i]
                path.append(i)

            print("SSSP from source %r to node %r has distance %r and path %r" % (source, v, d[v], path[::-1]))


if __name__ == "__main__":
    a, b, c, d, e = Vertex("a"), Vertex("b"), Vertex("c"), Vertex("d"), Vertex("e")
    G = Graph()
    G.addEdge(a, b, 3)
    G.addEdge(a, c, 1)
    G.addEdge(c, b, 1)
    G.addEdge(b, d, 4)
    G.addEdge(c, e, 5)
    G.addEdge(d, e, 4)

    G.printSSSPs(a)

    cycleG = Graph()
    cycleG.addEdge(a, b, 2)
    cycleG.addEdge(d, a, 2)
    cycleG.addEdge(a, c, -1)
    cycleG.addEdge(c, e, -2)
    cycleG.addEdge(e, a, 1)

    result = cycleG.bellmanFord_SSSP(d)
    print(result)
