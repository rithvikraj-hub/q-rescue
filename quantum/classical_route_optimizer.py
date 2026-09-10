import heapq


def dijkstra(graph, start, end):
    """
    Classical shortest-path optimization using Dijkstra's algorithm.
    graph format:
    {
        "A": [("B", 5), ("C", 8)],
        ...
    }
    """

    distances = {
        node: float("inf")
        for node in graph
    }

    previous = {
        node: None
        for node in graph
    }

    distances[start] = 0

    priority_queue = [(0, start)]

    while priority_queue:

        current_distance, current_node = heapq.heappop(
            priority_queue
        )

        if current_distance > distances[current_node]:
            continue

        if current_node == end:
            break

        for neighbor, weight in graph[current_node]:

            distance = (
                current_distance + weight
            )

            if distance < distances[neighbor]:

                distances[neighbor] = distance

                previous[neighbor] = current_node

                heapq.heappush(
                    priority_queue,
                    (distance, neighbor)
                )

    if distances[end] == float("inf"):
        return {
            "status": "FAILED",
            "path": [],
            "distance": None
        }

    path = []

    current = end

    while current is not None:
        path.append(current)
        current = previous[current]

    path.reverse()

    return {
        "status": "SUCCESS",
        "algorithm": "Dijkstra",
        "path": path,
        "distance": round(
            distances[end],
            2
        )
    }