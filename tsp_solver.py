"""
TSP Solver using Google OR-Tools

This module provides TSP solving functionality using OR-Tools routing optimization,
which is specifically designed for vehicle routing and TSP problems.
"""

from typing import List, Optional, Tuple

from tsp_utils import haversine_distance

try:
    from ortools.constraint_solver import pywrapcp, routing_enums_pb2
except ImportError:
    print("ERROR: OR-Tools not installed. Install with: pip install ortools")
    raise


def create_distance_matrix(points: List[Tuple[float, float]]) -> List[List[int]]:
    """
    Create distance matrix for OR-Tools (using integer distances in meters).

    Args:
        points: List of (longitude, latitude) coordinate tuples

    Returns:
        Square distance matrix as list of lists (distances in meters as integers)
    """
    n = len(points)
    distance_matrix = []

    for i in range(n):
        row = []
        for j in range(n):
            if i == j:
                distance_m = 0
            else:
                # Convert km to meters and round to integer for OR-Tools
                distance_km = haversine_distance(points[i], points[j])
                distance_m = int(round(distance_km * 1000))
            row.append(distance_m)
        distance_matrix.append(row)

    return distance_matrix


def solve_tsp_ortools(
    points: List[Tuple[float, float]], time_limit: Optional[float] = None
) -> Tuple[List[int], float]:
    """
    Solve the Traveling Salesman Problem using OR-Tools.

    Args:
        points: List of (longitude, latitude) coordinate tuples representing cities
        time_limit: Optional time limit in seconds for the solver (default: 30 seconds)

    Returns:
        Tuple of (optimal_tour, optimal_cost) where:
        - optimal_tour: List of city indices in visiting order
        - optimal_cost: Total distance of the optimal tour in kilometers

    Raises:
        ValueError: If fewer than 2 points are provided
        Exception: If OR-Tools fails to solve the problem
    """
    if len(points) < 2:
        raise ValueError("TSP requires at least 2 points")

    if len(points) == 2:
        # Special case: only 2 points
        distance = haversine_distance(points[0], points[1])
        return [0, 1], distance * 2  # Go to other city and return

    n = len(points)
    print(f"Solving TSP for {n} cities using OR-Tools...")

    # Create distance matrix
    distance_matrix = create_distance_matrix(points)

    # Create the routing index manager
    manager = pywrapcp.RoutingIndexManager(
        n, 1, 0
    )  # n locations, 1 vehicle, depot at index 0

    # Create routing model
    routing = pywrapcp.RoutingModel(manager)

    # Create distance callback
    def distance_callback(from_index, to_index):
        """Returns the distance between the two nodes."""
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return distance_matrix[from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)

    # Define cost of each arc
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Set search parameters
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )

    # Set time limit
    if time_limit:
        search_parameters.time_limit.FromSeconds(int(time_limit))
    else:
        search_parameters.time_limit.FromSeconds(30)  # Default 30 seconds

    print("Starting OR-Tools optimization...")

    # Solve the problem
    solution = routing.SolveWithParameters(search_parameters)

    if not solution:
        raise Exception("OR-Tools could not find a solution")

    # Extract solution
    print(f"OR-Tools found solution with objective value: {solution.ObjectiveValue()}")

    # Get the route
    index = routing.Start(0)
    route = []
    route_distance = 0

    while not routing.IsEnd(index):
        node = manager.IndexToNode(index)
        route.append(node)
        previous_index = index
        index = solution.Value(routing.NextVar(index))
        route_distance += routing.GetArcCostForVehicle(previous_index, index, 0)

    # Don't include the return to depot in the route list
    # route already contains the complete tour without the return to start

    # Convert distance from meters to kilometers
    total_distance_km = route_distance / 1000.0

    print(f"Optimal tour found with cost: {total_distance_km:.1f} km")
    print(f"Tour: {route}")

    return route, total_distance_km


def solve_tsp(
    points: List[Tuple[float, float]], time_limit: Optional[float] = None
) -> Tuple[List[int], float]:
    """
    Main function to solve TSP given a list of points using OR-Tools.

    Args:
        points: List of (longitude, latitude) coordinate tuples
        time_limit: Optional time limit in seconds (default: 30)

    Returns:
        Tuple of (tour, cost) where tour is list of point indices and cost is total distance in km
    """
    return solve_tsp_ortools(points, time_limit)
