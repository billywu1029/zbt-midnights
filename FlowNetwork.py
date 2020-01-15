from Graph import Graph, Vertex
import json

class NegativeCapacityException(Exception):
    pass

class FlowNetwork:
    """
    A Flow Network. Consists of a source and sink node: S and T; and 4 auxiliary graphs that aid in calculating
    max flow or min cost max flow. These graphs include a capacity graph to store edge capacities, a flow graph to
    store any flow pushed through the network, a residual graph storing the augmenting flow through each edge, and
    a cost graph that stores the cost function applied to each edge.

    Any "flow" pushed through ah edge cannot exceed the capacity specified in the capacity graph,
    and the maximum possible amount of flow that can exist at any point in the graph is:
    min(sum(all capacities leaving S), sum(all capacities entering T))
    """
    def __init__(self, source, sink, vertices=None, capacities=None, cost=None):
        self.source = source  # Source node S
        self.sink = sink  # Sink node T
        # Maps u -> {v1: c1, v2: c2, ... }, ...; must be a mapping w "weighted" edges
        self.capacityGraph = Graph(vertices, {} if capacities is None else capacities)
        # Flow graph, keeps track of flow pushed through Network
        self.flowGraph = Graph(vertices)
        # Residual graph, keeps track of extra flow that can be pushed through
        self.residualGraph = Graph(vertices)
        self.resetFlowAndResidualGraph()

        # No methods other than this constructor and addEdge should mutate this cost function mapping
        self.cost = {} if cost is None else cost
        # Mutable, represents the residual graph's edge costs (ie cost func mappings * 1( (u,v) exists in res G ))
        self.costGraph = Graph(vertices, {k: self.cost[k] for k in self.cost})

    @staticmethod
    def createFlowNetwork(source, sink, vertices=None, capacities=None, cost=None, flowGraph=None, residualGraph=None, costGraph=None):
        # Constructor only initializes flow/residual/cost graphs, but they could be different, so update them below
        G = FlowNetwork(source, sink, vertices, capacities, cost)
        G.flowGraph = Graph.deserialize(flowGraph)
        G.residualGraph = Graph.deserialize(residualGraph)
        G.costGraph = Graph.deserialize(costGraph)
        return G

    def resetFlowAndResidualGraph(self):
        """For each edge present, reset flow to 0 and the residual to the capacity"""
        # TODO: Reset costGraph as well if we really want this reset feature to be reused outside of constructor
        for u in self.capacityGraph.edges:
            for v in self.capacityGraph.edges[u]:
                self.residualGraph.addEdge(u, v, self.getCapacity(u, v))
                self.flowGraph.addEdge(u, v, 0)

    def checkRep(self):
        """
        [DEBUG] Checks that every mapping/part of the Network rep is maintained.
        Should be called before/after methods that mutate the Network's internals.
        """
        flowMappings = self.flowGraph.getEdges()  # TODO: should I create an iterator through Graph edges?
        for u in flowMappings:
            for v in flowMappings[u]:
                # If there is flow through an edge, then the flow must be <= the capacity
                assert u in self.capacityGraph
                assert v in self.capacityGraph[u]
                f = self.flowGraph[u][v]
                cp = self.getCapacity(u, v)
                assert 0 <= f <= cp

                # No edge in residual network if flow == capacity
                if f == cp:
                    if u in self.residualGraph:
                        assert v not in self.residualGraph[u]
                    assert v in self.residualGraph and u in self.residualGraph[v]
                    assert f == self.residualGraph[v][u]
                else:  # Otherwise, residual flow must be <= capacity-flow, and must have a reverse edge w >= f(u,v)
                    assert u in self.residualGraph and v in self.residualGraph[u]
                    assert self.residualGraph[u][v] <= self.getCapacity(u, v) - self.flowGraph[u][v]
                    if f == 0:  # If 0 flow, then reverse edge shouldn't be in the residual network
                        if v in self.residualGraph:
                            assert u not in self.residualGraph[v]
                    else:  # Reverse edge >= f(u,v) since there could be other contributing flows through edge (u,v)
                        assert v in self.residualGraph and u in self.residualGraph[v]
                        assert self.residualGraph[v][u] >= self.flowGraph[u][v]

        for u in self.capacityGraph.edges:
            for v in self.capacityGraph.edges[u]:
                # Capacities must be non-negative, and also integral (o/w Ford Fulkerson might not converge properly)
                cp = self.getCapacity(u, v)
                assert cp >= 0
                assert isinstance(cp, int)

        # Source and sink nodes must be present
        # Total flow out of source must be equal to total flow into sink
        sourceSum, sinkSum = 0, 0
        assert self.source in self.flowGraph
        sinkPresent = False
        for u in flowMappings:
            if self.sink in flowMappings[u]:
                sinkPresent = True
                sinkSum += flowMappings[u][self.sink]
        assert sinkPresent
        for f in flowMappings[self.source].values():
            sourceSum += f
        assert sourceSum == sinkSum

        # Cost Graph checks: all edge weights w(u,v) must be <= cost[u][v]
        for u in self.costGraph.edges:
            for v in self.costGraph.edges[u]:
                assert u in self.cost and v in self.cost[u]
                assert self.costGraph.getWeight(u, v) <= self.cost[u][v]
                # All cost graph edges must also belong to the residual network (costGraph == costs of residual edges)
                assert u in self.residualGraph and v in self.residualGraph[u]

    def getCapacity(self, u: Vertex, v: Vertex) -> int:
        return self.capacityGraph.getWeight(u, v)

    def addEdge(self, u: Vertex, v: Vertex, capacity: int = 0, cost=None):
        """
        Given two vertices, a capacity, and a cost, adds the edge to the corresponding graphs in the Flow Network.
        Throws an exception if the capacity specified is negative.
        Behavior unspecified if there exists an edge back to the source S,
        or if there is already flow present in the flow/residual graph.
        """
        if capacity < 0:
            raise NegativeCapacityException
        # Uncomment if desired behavior becomes st if flow preexisting, then reset everything
        # if any(self.flowGraph[u][v] != 0 for u in self.flowGraph for v in self.flowGraph[u]):
        #     self.resetFlowAndResidualGraph()

        self.capacityGraph.addEdge(u, v, capacity)
        self.flowGraph.addEdge(u, v, 0)
        self.residualGraph.addEdge(u, v, capacity)
        if cost is not None:
            self.costGraph.addEdge(u, v, cost)
            if u not in self.cost:
                self.cost[u] = {v: cost}
            else:
                self.cost[u][v] = cost

    def getAugmentingPath(self) -> list:
        """
        Gets the shortest-length augmenting path via BFS on the residual network. Uses Edmonds-Karp as the spec
        since it bounds the number of augmentations to O(VE^2) rather than O(E * |f|) where f is the max flow
        @return: list of vertices in the shortest-length augmenting path
        """
        return self.residualGraph.bfs(self.source, self.sink)

    def getMinCapAlongResCycle(self, negCycle: list) -> int:
        """Gets the minimum capacity among all residual graph edges using vertices from a given negative cost cycle."""
        assert negCycle is not None
        amountRedirectedFlow = float('inf')
        for i in range(len(negCycle) - 1):
            u, v = negCycle[i], negCycle[i + 1]
            assert u in self.residualGraph and v in self.residualGraph[u]  # cycle generated from res G, should be true
            amountRedirectedFlow = min(amountRedirectedFlow, self.residualGraph[u][v])
        return amountRedirectedFlow

    def getMinCapAlongAugPath(self, augPath: list) -> int:
        """Gets the minimum capacity among all edges on a valid (non-null) augmenting path, augPath."""
        assert augPath is not None
        # Need to identify largest difference between any capacity and flow already being pushed through
        additionalFlow = float('inf')
        for i in range(len(augPath) - 1):
            u, v = augPath[i], augPath[i + 1]
            # Need this check if sending flow to "counter" existing flow
            if u not in self.capacityGraph or (u in self.capacityGraph and v not in self.capacityGraph[u]):
                assert v in self.flowGraph and u in self.flowGraph[v]  # Must be flow in opposite direction
                additionalFlow = min(additionalFlow, self.flowGraph[v][u])  # min cap is sending this flow backwards
            else:
                additionalFlow = min(additionalFlow, self.getCapacity(u, v) - self.flowGraph[u].get(v, 0))
        return additionalFlow

    def pushAugmentingFlow(self, augPath: list, costsPresent: bool):
        """
        Pushes augmenting flow along the specified path, and updates the residuals in the residual graph
            Note: also updates the cost graph's costs (which correspond to residual costs)
        @param augPath: input path from source to sink node of possible nonzero additional flow, must not be None
            Note: can also be a cycle reachable from the sink node if using cycle cancelling.
        @param costsPresent: True if cost graph represents the costs of edges in residual graph,
            o/w False if Flow Network not initialized with costs in mind.
        @return: null
        """
        if costsPresent:
            assert self.costGraph.edges  # Must have a valid cost graph for costsPresent to be flipped to True
            # The augmenting path here is assumed to be a cycle that is passed in
            assert augPath[-1] == augPath[0]
            additionalFlow = self.getMinCapAlongResCycle(augPath)
        else:
            additionalFlow = self.getMinCapAlongAugPath(augPath)
        # If an augmenting path is specified, then just need to make the necessary changes along the augmenting path
        for i in range(len(augPath) - 1):
            u, v = augPath[i], augPath[i+1]

            # In the case of cycles, we want to redirect the flow for cycle cancelling, which could mean subtracting
            # Note: ok if a flow value is 0 rather than deleted from mappings - no bfs or bellman ford on flow edges
            if v in self.flowGraph and u in self.flowGraph[v]:
                self.flowGraph[v][u] -= additionalFlow
            else:
                # Augment flow graph for f(u,v) normally: add additional flow, or add edge to mapping if needed
                if u in self.flowGraph:
                    self.flowGraph[u][v] = self.flowGraph[u].get(v, 0) + additionalFlow

            # Augment residual graph, potentially edit edges (u,v) and (v,u) if already flow going through
            assert additionalFlow <= self.residualGraph[u][v]
            # Subtract off flow pushed through, ie delta f(u,v)
            if v in self.residualGraph[u] and self.residualGraph[u][v] == additionalFlow:
                del self.residualGraph[u][v]
                # Augment cost graph, should emulate residual graph's edges but instead of capacities, have costs
                if self.costGraph.edges:
                    assert v in self.costGraph[u]
                    # Only want to delete cost graph edge if flow reaches capacity and res G also no longer has the edge
                    del self.costGraph[u][v]
            else:
                self.residualGraph[u][v] -= additionalFlow

            # Residual flow, from v->u
            if v not in self.residualGraph:
                self.residualGraph[v] = {u: additionalFlow}
                # Augment cost graph to reflect addition of new edge in residual graph
                if self.costGraph.edges:
                    assert v not in self.costGraph
                    assert u in self.costGraph
                    # pulling from the original costs mapping since that is immutable, as opposed to the mutable cost G
                    self.costGraph[v] = {u: -self.cost[u][v]}
            else:
                self.residualGraph[v][u] = self.residualGraph[v].get(u, 0) + additionalFlow
                if self.costGraph.edges:
                    assert v in self.costGraph
                    # If cycle edge part of original cost func mapping, then G_c[v][u] <- -cost(v,u)
                    # O/w edge is not on a cycle and needs the -cost(u, v)
                    if v in self.cost and u in self.cost[v]:
                        self.costGraph[v][u] = self.cost[v][u]
                    else:
                        self.costGraph[v][u] = -self.cost[u][v]

    def getMaxFlow(self) -> int:
        """
        Finds the max flow (as an integer), given the current flow network. Uses the Ford Fulkerson algorithm.
        Note: Pushes flow through the network (mutates the network's flow)
        If no augmenting path exists at all, then the max flow is just 0.
        @return: any feasible max flow as an integer

        Pseudocode (from https://www.hackerearth.com/practice/algorithms/graphs/maximum-flow/tutorial/):
        function: FordFulkerson(Graph G,Node S,Node T):
            Initialise flow in all edges to 0
            while (there exists an augmenting path(P) between S and T in residual network graph):
                Augment flow between S to T along the path P
                Update residual network graph
            return
        """
        augmentingPath = self.getAugmentingPath()
        while augmentingPath is not None:
            self.pushAugmentingFlow(augmentingPath, costsPresent=False)
            augmentingPath = self.getAugmentingPath()

        maxFlow = 0
        if self.source in self.flowGraph:
            for v in self.flowGraph[self.source]:
                maxFlow += self.flowGraph[self.source][v]
        return maxFlow

    def getNegCostResidualCycle(self) -> list:
        """
        Detects if there exists a negative cost cycle in the Residual Graph, and if so, returns the cycle, o/w None.
        Uses Bellman-Ford, since Dijkstra etc. cannot handle negative cost cycles.
        @return: list of vertices in negative cost cycle from residual graph, or null if no cycle exists
        """
        cycle, d, p = self.costGraph.bellmanFord_SSSP(self.sink)
        return cycle

    def getMinCostMaxFlow(self) -> tuple:
        """
        Finds the min cost max flow (assumed to be integral). Uses the cycle cancelling algorithm.
        Note: mutates the current Flow Network state by redirecting flow after a feasible max flow is found (minimize c)
        Note: Assumes that the cost function is defined for edges (u,v) that appear in capacities
        @return: tuple( minimum cost from an optimal max flow as an integer, max flow as an integer )

        Pseudocode (from https://www.hackerearth.com/practice/algorithms/graphs/minimum-cost-maximum-flow/tutorial/)
        function: MinCost(Graph G):
            Find a feasible maximum flow of G using Ford Fulkerson and construct residual graph(Gf)
            Gc = CostNetwork(G, Gf)
            while(negativeCycle(Gc)):
                Increase the flow along each edge in cycle C by minimum capacity in the cycle C
                Update residual graph(Gf)
                Gc = CostNetwork(G,Gf)
            mincost = sum of Cij*Fij for each of the flow in residual graph
            return mincost
        """
        self.getMaxFlow()  # Obtains a feasible max flow and updates the Flow and Residual graphs
        negCostCycle = self.getNegCostResidualCycle()
        while negCostCycle is not None:
            self.pushAugmentingFlow(negCostCycle, costsPresent=True)
            negCostCycle = self.getNegCostResidualCycle()

        # By now, there are no more negative cost cycles in the residual graph, and so our flow cost must be optimal
        minCost, maxFlow = 0, 0
        for u in self.flowGraph.edges:
            for v in self.flowGraph.edges[u]:
                if self.flowGraph.getWeight(u, v) == 0:
                    continue
                assert u in self.cost and v in self.cost[u]
                minCost += self.flowGraph.getWeight(u, v) * self.cost[u][v]
                if u == self.source:
                    maxFlow += self.flowGraph.getWeight(u, v)

        return minCost, maxFlow

    def serializeToJSON(self, outPath: str):
        """Serializes the Flow Network into a JSON object, and writes it to the file specified (overwrites contents).
        If no file exists, then it creates the file and writes to it.
        Format:
            "source": str
            "sink": str
            "vertices": list(str)
            "capacities": {str: {str: int, ...}, ...}
            "flow": {str: {str: int, ...}, ...}
            "residual": {str: {str: int, ...}, ...}
            "cost": {str: {str: int, ...}, ...}
            "residualCost": {str: {str: int, ...}, ...}
        """
        with open(outPath, "w") as out:
            result = {}
            result["source"] = self.source.val
            result["sink"] = self.sink.val
            result["vertices"] = [v.val for v in self.capacityGraph.vertices]
            result["capacities"] = self.capacityGraph.serialize()
            result["cost"] = {k.val: {v.val: self.cost[k][v] for v in self.cost[k]} for k in self.cost}
            result["flow"] = self.flowGraph.serialize()
            result["residual"] = self.residualGraph.serialize()
            result["residualCost"] = self.costGraph.serialize()
            json.dump(result, out)

    @staticmethod
    def deserialize(inPath: str):
        with open(inPath, "r") as inp:
            data = json.load(inp)
            return FlowNetwork.createFlowNetwork(data["source"],
                                                 data["sink"],
                                                 data["vertices"],
                                                 data["capacities"],
                                                 data["cost"],
                                                 data["flow"],
                                                 data["residual"],
                                                 data["residualCost"])


if __name__ == "__main__":
    a, b, c, d, e, t = Vertex("a"), Vertex("b"), Vertex("c"), Vertex("d"), Vertex("e"), Vertex("t")
    g = Graph()
    g.addEdge(a, b, 2)
    g.addEdge(a, c, 3)
    g.addEdge(c, b, 5)
    g.addEdge(b, d, 4)
    g.addEdge(c, e, 5)
    g.addEdge(d, e, 4)
    vertices = g.getVertices()
    edges = g.getEdges()
    N = FlowNetwork(a, e, vertices, edges)

    G = FlowNetwork(a, e)
    G.addEdge(a, b, 2)
    G.addEdge(a, c, 3)
    G.addEdge(c, b, 5)
    G.addEdge(b, d, 4)
    G.addEdge(c, e, 5)
    G.addEdge(d, e, 4)
    # Can implement a __eq__ to see if these really match programmatically if there's more time

    N.checkRep()
    G.checkRep()
    print(N.getMaxFlow())
    print(G.getMaxFlow())
    N.checkRep()
    G.checkRep()

    # Testing the min cost max flow
    g = FlowNetwork(a, t)
    g.addEdge(a, b, 10, 5)
    g.addEdge(a, c, 15, 2)
    g.addEdge(b, c, 5, 2)
    g.addEdge(b, d, 5, 5)
    g.addEdge(c, d, 3, 1)
    g.addEdge(c, e, 15, 7)
    g.addEdge(d, t, 2, 2)
    g.addEdge(e, t, 20, 1)

    print(g.getMinCostMaxFlow())
    a = 1
