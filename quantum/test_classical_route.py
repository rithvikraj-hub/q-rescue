from classical_route_optimizer import dijkstra


# Q-RESCUE DEMO ROAD NETWORK
# Distance values are in kilometers

road_network = {
    "Machilipatnam": [
        ("Node_A", 12),
        ("Node_B", 18)
    ],

    "Node_A": [
        ("Machilipatnam", 12),
        ("Node_C", 10),
        ("Node_D", 20)
    ],

    "Node_B": [
        ("Machilipatnam", 18),
        ("Node_C", 7),
        ("Node_D", 12)
    ],

    "Node_C": [
        ("Node_A", 10),
        ("Node_B", 7),
        ("Shelter_S1", 15)
    ],

    "Node_D": [
        ("Node_A", 20),
        ("Node_B", 12),
        ("Shelter_S1", 8)
    ],

    "Shelter_S1": [
        ("Node_C", 15),
        ("Node_D", 8)
    ]
}


# SOURCE AND DESTINATION
source = "Machilipatnam"
destination = "Shelter_S1"


# RUN CLASSICAL OPTIMIZATION
result = dijkstra(
    road_network,
    source,
    destination
)


# DISPLAY RESULT
print("\n===== Q-RESCUE CLASSICAL ROUTE OPTIMIZER =====")

print("Algorithm:", result["algorithm"])
print("Source:", source)
print("Destination:", destination)

print("Route:")

if result["status"] == "SUCCESS":

    print(" → ".join(result["path"]))

    print(
        "Distance:",
        result["distance"],
        "km"
    )

    print("Status:", result["status"])

else:

    print("No route found")

    print("Status:", result["status"])