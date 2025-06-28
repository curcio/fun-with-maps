"""
TSP Solver using Google OR-Tools

This module provides TSP solving functionality using OR-Tools routing optimization,
which is specifically designed for vehicle routing and TSP problems.
"""

from typing import List, Optional, Tuple

from .tsp_utils import haversine_distance

try:
    from ortools.constraint_solver import pywrapcp, routing_enums_pb2
except ImportError:
    print("ERROR: OR-Tools not installed. Install with: pip install ortools")
    raise


class TSPSolver:
    """
    A class for solving Traveling Salesman Problems using OR-Tools.
    """

    def __init__(self, time_limit: float = 30.0, strategy: str = "guided_local_search"):
        """
        Initialize the TSP solver.

        Args:
            time_limit: Maximum time limit in seconds for solving
            strategy: Search strategy ('guided_local_search', 'simulated_annealing', 'tabu_search')
        """
        self.time_limit = time_limit
        self.strategy = strategy
        self.distance_matrix = None

    def create_distance_matrix(
        self, points: List[Tuple[float, float]]
    ) -> List[List[int]]:
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

        self.distance_matrix = distance_matrix
        return distance_matrix

    def _get_search_strategy(self):
        """Get the appropriate search strategy based on configuration."""
        strategy_map = {
            "guided_local_search": routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH,
            "simulated_annealing": routing_enums_pb2.LocalSearchMetaheuristic.SIMULATED_ANNEALING,
            "tabu_search": routing_enums_pb2.LocalSearchMetaheuristic.TABU_SEARCH,
            "generic_tabu_search": routing_enums_pb2.LocalSearchMetaheuristic.GENERIC_TABU_SEARCH,
        }
        return strategy_map.get(
            self.strategy,
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH,
        )

    def solve_tsp_ortools(
        self, points: List[Tuple[float, float]]
    ) -> Tuple[List[int], float]:
        """
        Solve the Traveling Salesman Problem using OR-Tools.

        Args:
            points: List of (longitude, latitude) coordinate tuples representing cities

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
        print(
            f"Solving TSP for {n} cities using OR-Tools with {self.strategy} strategy..."
        )

        # Create distance matrix
        distance_matrix = self.create_distance_matrix(points)

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
        search_parameters.local_search_metaheuristic = self._get_search_strategy()

        # Set time limit
        search_parameters.time_limit.FromSeconds(int(self.time_limit))

        print(f"Starting OR-Tools optimization with {self.time_limit}s time limit...")

        # Solve the problem
        solution = routing.SolveWithParameters(search_parameters)

        if not solution:
            raise Exception("OR-Tools could not find a solution")

        # Extract solution
        print(
            f"OR-Tools found solution with objective value: {solution.ObjectiveValue()}"
        )

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

    def solve_multiple_strategies(
        self, points: List[Tuple[float, float]]
    ) -> Tuple[List[int], float, str]:
        """
        Try multiple solving strategies and return the best result.

        Args:
            points: List of (longitude, latitude) coordinate tuples

        Returns:
            Tuple of (best_tour, best_cost, best_strategy)
        """
        strategies = ["guided_local_search", "simulated_annealing", "tabu_search"]
        best_cost = float("inf")
        best_tour = []
        best_strategy = ""

        original_strategy = self.strategy
        original_time_limit = self.time_limit

        # Use shorter time limit for multiple strategies
        self.time_limit = max(10.0, self.time_limit / len(strategies))

        for strategy in strategies:
            try:
                print(f"\n--- Trying strategy: {strategy} ---")
                self.strategy = strategy
                tour, cost = self.solve_tsp_ortools(points)

                if cost < best_cost:
                    best_cost = cost
                    best_tour = tour
                    best_strategy = strategy
                    print(f"New best solution: {cost:.1f} km with {strategy}")

            except Exception as e:
                print(f"Strategy {strategy} failed: {e}")
                continue

        # Restore original settings
        self.strategy = original_strategy
        self.time_limit = original_time_limit

        if best_tour:
            print(f"\n=== Best solution: {best_cost:.1f} km using {best_strategy} ===")
            return best_tour, best_cost, best_strategy
        else:
            raise Exception("All solving strategies failed")

    def solve(
        self, points: List[Tuple[float, float]], try_multiple_strategies: bool = False
    ) -> Tuple[List[int], float]:
        """
        Main solving method with option to try multiple strategies.

        Args:
            points: List of (longitude, latitude) coordinate tuples
            try_multiple_strategies: Whether to try multiple solving strategies

        Returns:
            Tuple of (tour, cost) where tour is list of point indices and cost is total distance in km
        """
        if try_multiple_strategies and len(points) > 10:
            tour, cost, _ = self.solve_multiple_strategies(points)
            return tour, cost
        else:
            return self.solve_tsp_ortools(points)


# Backward compatibility functions
def create_distance_matrix(points: List[Tuple[float, float]]) -> List[List[int]]:
    """Backward compatibility wrapper."""
    solver = TSPSolver()
    return solver.create_distance_matrix(points)


def solve_tsp_ortools(
    points: List[Tuple[float, float]], time_limit: Optional[float] = None
) -> Tuple[List[int], float]:
    """Backward compatibility wrapper."""
    solver = TSPSolver(time_limit=time_limit or 30.0)
    return solver.solve_tsp_ortools(points)


def solve_tsp(
    points: List[Tuple[float, float]], time_limit: Optional[float] = None
) -> Tuple[List[int], float]:
    """Backward compatibility wrapper."""
    solver = TSPSolver(time_limit=time_limit or 30.0)
    return solver.solve(points)
