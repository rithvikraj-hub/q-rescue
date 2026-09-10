from qaoa_route_optimizer import qaoa_route_optimizer


# ==================================================
# CANDIDATE EVACUATION ROUTES
# ==================================================

candidate_routes = [

    {
        "name": "Route 1",

        "path": [
            "Machilipatnam",
            "Node_A",
            "Node_C",
            "Shelter_S1"
        ],

        "distance": 37,

        "risk": "HIGH",

        "risk_penalty": 40,

        "congestion": "HIGH",

        "congestion_penalty": 8
    },


    {
        "name": "Route 2",

        "path": [
            "Machilipatnam",
            "Node_B",
            "Node_C",
            "Shelter_S1"
        ],

        "distance": 40,

        "risk": "MEDIUM",

        "risk_penalty": 20,

        "congestion": "MEDIUM",

        "congestion_penalty": 5
    },


    {
        "name": "Route 3",

        "path": [
            "Machilipatnam",
            "Node_B",
            "Node_D",
            "Shelter_S1"
        ],

        "distance": 38,

        "risk": "LOW",

        "risk_penalty": 5,

        "congestion": "LOW",

        "congestion_penalty": 2
    }

]


print("\nRunning QAOA route optimization...")


result = qaoa_route_optimizer(
    candidate_routes
)


print("\n==============================================")
print(" Q-RESCUE QAOA ROUTE OPTIMIZER")
print("==============================================")


print(
    "Algorithm:",
    result["algorithm"]
)

print(
    "Method:",
    result["method"]
)


print("\nCandidate Routes:")


for route in candidate_routes:

    print("\n", route["name"])

    print(
        "Route:",
        " → ".join(route["path"])
    )

    print(
        "Distance:",
        route["distance"],
        "km"
    )

    print(
        "Risk:",
        route["risk"]
    )

    print(
        "Congestion:",
        route["congestion"]
    )

    print(
        "QAOA Cost:",
        route["distance"]
        + route["risk_penalty"]
        + route["congestion_penalty"]
    )


if result["status"] == "SUCCESS":

    selected =result["selected_route"]


    print("\n----------------------------------------------")

    print("QAOA SELECTED ROUTE:")

    print(
        " → ".join(
            selected["path"]
        )
    )


    print(
        "Distance:",
        selected["distance"],
        "km"
    )


    print(
        "Risk:",
        selected["risk"]
    )


    print(
        "Congestion:",
        selected["congestion"]
    )


    print(
        "Total QAOA Cost:",
        result["total_cost"]
    )


print(
    "\nQuantum Simulation:",
    result["quantum_simulation"]
)


print(
    "Status:",
    result["status"]
)


print("==============================================")