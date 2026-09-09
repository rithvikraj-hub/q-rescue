import sqlite3
import os

from qiskit.primitives import StatevectorSampler
from qiskit_optimization import QuadraticProgram
from qiskit_optimization.algorithms import MinimumEigenOptimizer
from qiskit_optimization.minimum_eigensolvers import QAOA
from qiskit_optimization.optimizers import COBYLA


# ==============================
# DATABASE PATH
# ==============================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE = os.path.join(BASE_DIR, "backend", "qrescue.db")


# ==============================
# GET LATEST DISASTER
# ==============================

def get_latest_disaster():

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            disaster_type,
            risk_level,
            location,
            population,
            food,
            water,
            medical_kits,
            rescue_boats
        FROM disasters
        ORDER BY id DESC
        LIMIT 1
    """)

    row = cursor.fetchone()

    conn.close()

    if row is None:
        return None

    return dict(row)


# ==============================
# CREATE QUBO
# ==============================

def create_qubo(disaster):

    problem = QuadraticProgram()

    # Binary decision variables
    # 1 = select resource
    # 0 = do not select resource

    problem.binary_var("food")
    problem.binary_var("water")
    problem.binary_var("medical")
    problem.binary_var("boats")

    population = disaster["population"]
    risk = disaster["risk_level"].upper()

    # ==============================
    # REQUIRED RESOURCES
    # ==============================

    required_food = population
    required_water = population * 3
    required_medical = max(1, population // 20)
    required_boats = max(1, population // 5000)

    # ==============================
    # SHORTAGE CALCULATION
    # ==============================

    food_shortage = max(
        0,
        required_food - disaster["food"]
    )

    water_shortage = max(
        0,
        required_water - disaster["water"]
    )

    medical_shortage = max(
        0,
        required_medical - disaster["medical_kits"]
    )

    boats_shortage = max(
        0,
        required_boats - disaster["rescue_boats"]
    )

    # ==============================
    # PRIORITY SCORES
    # ==============================

    food_score = food_shortage
    water_score = water_shortage
    medical_score = medical_shortage
    boats_score = boats_shortage

    # Higher priority for dangerous disasters

    if risk == "HIGH":

        food_score += population * 0.5
        water_score += population * 0.5
        medical_score += population * 0.3
        boats_score += population * 0.2

    elif risk == "MEDIUM":

        food_score += population * 0.25
        water_score += population * 0.25
        medical_score += population * 0.15
        boats_score += population * 0.10

    # ==============================
    # RESOURCE SELECTION CONSTRAINT
    # ==============================

    # At least ONE resource must be selected
    problem.linear_constraint(
        linear={
            "food": 1,
            "water": 1,
            "medical": 1,
            "boats": 1
        },
        sense=">=",
        rhs=1,
        name="minimum_resource_selection"
    )

    # Maximum TWO resources can be selected
    # This forces the optimizer to prioritize
    # the most important resources.

    problem.linear_constraint(
        linear={
            "food": 1,
            "water": 1,
            "medical": 1,
            "boats": 1
        },
        sense="<=",
        rhs=2,
        name="maximum_resource_selection"
    )

    # ==============================
    # OBJECTIVE FUNCTION
    # ==============================

    # QAOA minimizes the objective.
    # Negative priority means:
    # higher priority → better selection.

    problem.minimize(
        linear={
            "food": -food_score,
            "water": -water_score,
            "medical": -medical_score,
            "boats": -boats_score
        }
    )

    return problem


# ==============================
# RUN QAOA
# ==============================

def run_qaoa(disaster):

    problem = create_qubo(disaster)

    sampler = StatevectorSampler()

    qaoa = QAOA(
        sampler=sampler,
        optimizer=COBYLA(),
        reps=1
    )

    optimizer = MinimumEigenOptimizer(qaoa)

    result = optimizer.solve(problem)

    selected_resources = []

    if result.x[0] > 0.5:
        selected_resources.append("Food")

    if result.x[1] > 0.5:
        selected_resources.append("Water")

    if result.x[2] > 0.5:
        selected_resources.append("Medical Kits")

    if result.x[3] > 0.5:
        selected_resources.append("Rescue Boats")

    return {
        "algorithm": "QAOA",
        "method": "Quantum Simulation",
        "selected_resources": selected_resources,
        "objective_value": float(result.fval),
        "status": "SUCCESS"
    }


# ==============================
# MAIN
# ==============================

if __name__ == "__main__":

    print("\n===== Q-RESCUE QUANTUM OPTIMIZER =====")

    disaster = get_latest_disaster()

    if disaster is None:

        print("No disaster data found.")

    else:

        print("\nDisaster Data:")

        print("Disaster:", disaster["disaster_type"])
        print("Risk:", disaster["risk_level"])
        print("Location:", disaster["location"])
        print("Population:", disaster["population"])

        result = run_qaoa(disaster)

        print("\n===== QAOA RESULT =====")

        print("Algorithm:", result["algorithm"])
        print("Method:", result["method"])

        print(
            "Selected Resources:",
            result["selected_resources"]
        )

        print(
            "Objective Value:",
            result["objective_value"]
        )

        print("Status:", result["status"])