from qiskit_optimization import QuadraticProgram
from qiskit_optimization.algorithms import MinimumEigenOptimizer
from qiskit_algorithms import QAOA
from qiskit_algorithms.optimizers import COBYLA
from qiskit.primitives import StatevectorSampler


def qaoa_route_optimizer(routes):

    qp = QuadraticProgram()

    # ============================================
    # CREATE BINARY VARIABLE FOR EACH ROUTE
    # ============================================

    for i in range(len(routes)):
        qp.binary_var(f"x{i}")


    # ============================================
    # QAOA OBJECTIVE
    #
    # Combined:
    # Distance + Risk + Congestion
    # ============================================

    penalty = 100


    linear = {}

    for i, route in enumerate(routes):

        combined_cost = (
            route["distance"]
            + route["risk_penalty"]
            + route["congestion_penalty"]
        )

        # One-hot selection penalty
        linear[f"x{i}"] = (
            combined_cost
            - (2 * penalty)
        )


    # ============================================
    # PENALTY FOR SELECTING MULTIPLE ROUTES
    # ============================================

    quadratic = {}

    for i in range(len(routes)):

        for j in range(i + 1, len(routes)):

            quadratic[
                (f"x{i}", f"x{j}")
            ] = 2 * penalty


    # ============================================
    # MINIMIZE TOTAL COST
    # ============================================

    qp.minimize(
        linear=linear,
        quadratic=quadratic
    )


    # ============================================
    # QAOA QUANTUM SIMULATION
    # ============================================

    sampler = StatevectorSampler(
        seed=42
    )

    qaoa = QAOA(
        sampler=sampler,
        optimizer=COBYLA(
            maxiter=5
        ),
        reps=1
    )

    optimizer = MinimumEigenOptimizer(
        qaoa
    )


    # Solve
    result = optimizer.solve(qp)


    # ============================================
    # FIND SELECTED ROUTE
    # ============================================

    selected_route = None

    for i, route in enumerate(routes):

        if result.x[i] > 0.5:

            selected_route = route
            break


    if selected_route is None:

        return {
            "status": "FAILED",
            "algorithm": "QAOA",
            "method":
                "QAOA-based Multi-Objective Route Optimization",
            "quantum_simulation": True
        }


    # Calculate combined cost
    total_cost = (
        selected_route["distance"]
        + selected_route["risk_penalty"]
        + selected_route["congestion_penalty"]
    )


    return {

        "status": "SUCCESS",

        "algorithm": "QAOA",

        "method":
            "QAOA-based Multi-Objective Route Optimization",

        "quantum_simulation": True,

        "selected_route":
            selected_route,

        "distance":
            selected_route["distance"],

        "risk_penalty":
            selected_route["risk_penalty"],

        "congestion_penalty":
            selected_route["congestion_penalty"],

        "total_cost":
            total_cost

    }