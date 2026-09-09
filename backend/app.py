from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

import sqlite3
import sys
import os


# ============================================================
# PROJECT PATH
# ============================================================

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)


# ============================================================
# QUANTUM IMPORT
# ============================================================

from quantum.quantum_optimizer import (
    run_qaoa,
    get_latest_disaster
)


# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__)
CORS(app)


# ============================================================
# DATABASE PATH
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DATABASE = os.path.join(
    BASE_DIR,
    "backend",
    "qrescue.db"
)


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def init_db():

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # --------------------------------------------------------
    # DISASTERS TABLE
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS disasters (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            disaster_type TEXT NOT NULL,

            risk_level TEXT NOT NULL,

            location TEXT NOT NULL,

            latitude REAL,

            longitude REAL,

            population INTEGER NOT NULL,

            food INTEGER NOT NULL,

            water INTEGER NOT NULL,

            medical_kits INTEGER NOT NULL,

            rescue_boats INTEGER NOT NULL

        )
    """)

    # --------------------------------------------------------
    # USERS TABLE
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            full_name TEXT NOT NULL,

            email TEXT NOT NULL UNIQUE,

            password TEXT NOT NULL,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )
    """)

    conn.commit()
    conn.close()


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    return "Q-RESCUE Backend is Running"


# ============================================================
# AUTHENTICATION - SIGNUP
# ============================================================

@app.route("/api/signup", methods=["POST"])
def signup():

    data = request.get_json()

    if not data:

        return jsonify({
            "success": False,
            "message": "JSON data is required"
        }), 400


    full_name = data.get(
        "full_name",
        ""
    ).strip()


    email = data.get(
        "email",
        ""
    ).strip().lower()


    password = data.get(
        "password",
        ""
    )


    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    if not full_name:

        return jsonify({
            "success": False,
            "message": "Full name is required"
        }), 400


    if not email:

        return jsonify({
            "success": False,
            "message": "Email is required"
        }), 400


    if not password:

        return jsonify({
            "success": False,
            "message": "Password is required"
        }), 400


    if len(password) < 6:

        return jsonify({
            "success": False,
            "message": "Password must contain at least 6 characters"
        }), 400


    # --------------------------------------------------------
    # HASH PASSWORD
    # --------------------------------------------------------

    hashed_password = generate_password_hash(
        password
    )


    # --------------------------------------------------------
    # SAVE USER
    # --------------------------------------------------------

    try:

        conn = sqlite3.connect(DATABASE)

        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO users
            (
                full_name,
                email,
                password
            )

            VALUES (?, ?, ?)
        """, (
            full_name,
            email,
            hashed_password
        ))

        conn.commit()

        conn.close()


        return jsonify({

            "success": True,

            "message":
                "Account created successfully"

        }), 201


    except sqlite3.IntegrityError:

        return jsonify({

            "success": False,

            "message":
                "Email already registered"

        }), 409


    except Exception as error:

        return jsonify({

            "success": False,

            "message":
                str(error)

        }), 500


# ============================================================
# AUTHENTICATION - LOGIN
# ============================================================

@app.route("/api/login", methods=["POST"])
def login():

    data = request.get_json()

    if not data:

        return jsonify({

            "success": False,

            "message":
                "JSON data is required"

        }), 400


    email = data.get(
        "email",
        ""
    ).strip().lower()


    password = data.get(
        "password",
        ""
    )


    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    if not email or not password:

        return jsonify({

            "success": False,

            "message":
                "Email and password are required"

        }), 400


    # --------------------------------------------------------
    # FIND USER
    # --------------------------------------------------------

    conn = sqlite3.connect(DATABASE)

    cursor = conn.cursor()


    cursor.execute("""
        SELECT
            id,
            full_name,
            email,
            password

        FROM users

        WHERE email = ?
    """, (
        email,
    ))


    user = cursor.fetchone()

    conn.close()


    # --------------------------------------------------------
    # CHECK PASSWORD
    # --------------------------------------------------------

    if user:

        stored_password = user[3]

        if check_password_hash(
            stored_password,
            password
        ):

            return jsonify({

                "success": True,

                "message":
                    "Login successful",

                "user": {

                    "id": user[0],

                    "full_name":
                        user[1],

                    "email":
                        user[2]

                }

            })


    # --------------------------------------------------------
    # INVALID LOGIN
    # --------------------------------------------------------

    return jsonify({

        "success": False,

        "message":
            "Invalid email or password"

    }), 401


# ============================================================
# DASHBOARD API
# ============================================================

@app.route("/api/dashboard")
def dashboard():

    conn = sqlite3.connect(
        DATABASE
    )

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()


    cursor.execute("""
        SELECT *

        FROM disasters

        ORDER BY id DESC

        LIMIT 1
    """)


    row = cursor.fetchone()

    conn.close()


    if row is None:

        return jsonify({

            "message":
                "No disaster data available"

        })


    return jsonify({

        "id":
            row["id"],

        "disaster":
            row["disaster_type"],

        "risk_level":
            row["risk_level"],

        "location":
            row["location"],

        "population":
            row["population"],

        "food":
            row["food"],

        "water":
            row["water"],

        "medical_kits":
            row["medical_kits"],

        "rescue_boats":
            row["rescue_boats"]

    })


# ============================================================
# ADD DISASTER
# ============================================================

@app.route(
    "/api/disasters",
    methods=["POST"]
)
def add_disaster():

    data = request.get_json()


    if not data:

        return jsonify({

            "error":
                "JSON data is required"

        }), 400


    required_fields = [

        "disaster_type",

        "risk_level",

        "location",

        "population",

        "food",

        "water",

        "medical_kits",

        "rescue_boats"

    ]


    # --------------------------------------------------------
    # VALIDATE FIELDS
    # --------------------------------------------------------

    for field in required_fields:

        if field not in data:

            return jsonify({

                "error":
                    f"Missing field: {field}"

            }), 400


    # --------------------------------------------------------
    # INSERT DISASTER
    # --------------------------------------------------------

    conn = sqlite3.connect(
        DATABASE
    )

    cursor = conn.cursor()


    cursor.execute("""
        INSERT INTO disasters
        (
            disaster_type,
            risk_level,
            location,
            latitude,
            longitude,
            population,
            food,
            water,
            medical_kits,
            rescue_boats
        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (

        data["disaster_type"],

        data["risk_level"],

        data["location"],

        data.get("latitude"),

        data.get("longitude"),

        data["population"],

        data["food"],

        data["water"],

        data["medical_kits"],

        data["rescue_boats"]

    ))


    disaster_id = cursor.lastrowid


    conn.commit()

    conn.close()


    return jsonify({

        "message":
            "Disaster data saved successfully",

        "id":
            disaster_id,

        "location":
            data["location"],

        "risk_level":
            data["risk_level"]

    }), 201


# ============================================================
# GET ALL DISASTERS
# ============================================================

@app.route(
    "/api/disasters",
    methods=["GET"]
)
def get_disasters():

    conn = sqlite3.connect(
        DATABASE
    )

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()


    cursor.execute("""
        SELECT *

        FROM disasters

        ORDER BY id DESC
    """)


    rows = cursor.fetchall()

    conn.close()


    disasters = [

        dict(row)

        for row in rows

    ]


    return jsonify(
        disasters
    )


# ============================================================
# RESOURCE PLANNING API
# ============================================================

@app.route(
    "/api/resources",
    methods=["GET"]
)
def calculate_resources():

    conn = sqlite3.connect(
        DATABASE
    )

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()


    cursor.execute("""
        SELECT *

        FROM disasters

        ORDER BY id DESC

        LIMIT 1
    """)


    row = cursor.fetchone()

    conn.close()


    if row is None:

        return jsonify({

            "message":
                "No disaster data available"

        })


    population = row["population"]


    # ========================================================
    # PROTOTYPE RESOURCE ASSUMPTIONS
    # ========================================================

    # 1 food packet per person

    required_food = population


    # 3 water units per person

    required_water = population * 3


    # 1 medical kit for every 20 people

    required_medical = max(

        1,

        population // 20

    )


    # 1 rescue boat for every 5000 people

    required_boats = max(

        1,

        population // 5000

    )


    # ========================================================
    # AVAILABLE RESOURCES
    # ========================================================

    available_food = row["food"]

    available_water = row["water"]

    available_medical = row["medical_kits"]

    available_boats = row["rescue_boats"]


    # ========================================================
    # READINESS CALCULATION
    # ========================================================

    food_readiness = min(

        100,

        round(
            (
                available_food
                /
                required_food
            ) * 100
        )

    )


    water_readiness = min(

        100,

        round(
            (
                available_water
                /
                required_water
            ) * 100
        )

    )


    medical_readiness = min(

        100,

        round(
            (
                available_medical
                /
                required_medical
            ) * 100
        )

    )


    boat_readiness = min(

        100,

        round(
            (
                available_boats
                /
                required_boats
            ) * 100
        )

    )


    # ========================================================
    # OVERALL READINESS
    # ========================================================

    overall_readiness = round(

        (
            food_readiness
            +
            water_readiness
            +
            medical_readiness
            +
            boat_readiness
        )
        /
        4

    )


    # ========================================================
    # RESPONSE
    # ========================================================

    return jsonify({

        "population":
            population,


        "food": {

            "required":
                required_food,

            "available":
                available_food,

            "readiness":
                food_readiness

        },


        "water": {

            "required":
                required_water,

            "available":
                available_water,

            "readiness":
                water_readiness

        },


        "medical_kits": {

            "required":
                required_medical,

            "available":
                available_medical,

            "readiness":
                medical_readiness

        },


        "rescue_boats": {

            "required":
                required_boats,

            "available":
                available_boats,

            "readiness":
                boat_readiness

        },


        "overall_readiness":
            overall_readiness

    })


# ============================================================
# SHELTER SOURCE DATA
# ============================================================

SHELTER_SOURCES = {

    "Machilipatnam": {

        "risk":
            "HIGH",

        "population":
            24500,

        "latitude":
            16.18,

        "longitude":
            81.13

    },


    "Narsapur": {

        "risk":
            "HIGH",

        "population":
            15700,

        "latitude":
            16.43,

        "longitude":
            81.70

    },


    "Kakinada": {

        "risk":
            "MEDIUM",

        "population":
            18200,

        "latitude":
            16.99,

        "longitude":
            82.24

    },


    "Vijayawada": {

        "risk":
            "LOW",

        "population":
            8400,

        "latitude":
            16.51,

        "longitude":
            80.64

    }

}


# ============================================================
# SHELTER DATA
# ============================================================

SHELTERS = [

    {

        "name":
            "Shelter S1",

        "capacity":
            5000,

        "occupied":
            3200,

        "latitude":
            16.30,

        "longitude":
            81.10

    },


    {

        "name":
            "Shelter S2",

        "capacity":
            3500,

        "occupied":
            2100,

        "latitude":
            16.70,

        "longitude":
            81.25

    },


    {

        "name":
            "Shelter S3",

        "capacity":
            4200,

        "occupied":
            2500,

        "latitude":
            17.00,

        "longitude":
            82.20

    }

]


# ============================================================
# DISTANCE CALCULATION
# ============================================================

def calculate_distance(
    lat1,
    lon1,
    lat2,
    lon2
):

    # Prototype distance approximation

    lat_distance = (
        lat2 - lat1
    ) * 111


    lon_distance = (

        lon2 - lon1

    ) * 111 * 0.96


    distance = (

        lat_distance ** 2

        +

        lon_distance ** 2

    ) ** 0.5


    return round(
        distance,
        2
    )


# ============================================================
# QAOA SHELTER PRIORITY OPTIMIZATION
# ============================================================

def optimize_shelters_qaoa(
    shelters
):

    try:

        from qiskit_optimization import (
            QuadraticProgram
        )

        from qiskit_optimization.algorithms import (
            MinimumEigenOptimizer
        )

        from qiskit_algorithms import (
            QAOA
        )

        from qiskit_algorithms.optimizers import (
            COBYLA
        )

        from qiskit.primitives import (
            StatevectorSampler
        )


        # ----------------------------------------------------
        # NORMALIZATION
        # ----------------------------------------------------

        max_capacity = max(

            s["available"]

            for s in shelters

        )


        max_distance = max(

            s["distance_km"]

            for s in shelters

        )


        # ----------------------------------------------------
        # QUANTUM SCORES
        # ----------------------------------------------------

        for shelter in shelters:

            capacity_score = (

                shelter["available"]
                /
                max_capacity

                if max_capacity > 0

                else 0

            )


            distance_score = (

                1
                -
                (
                    shelter["distance_km"]
                    /
                    max_distance
                )

                if max_distance > 0

                else 1

            )


            shelter["quantum_score"] = round(

                (
                    0.65
                    *
                    capacity_score
                )

                +

                (
                    0.35
                    *
                    distance_score
                ),

                4

            )


        # ----------------------------------------------------
        # QUADRATIC PROGRAM
        # ----------------------------------------------------

        qp = QuadraticProgram(
            "qrescue_shelter_priority"
        )


        for i in range(
            len(shelters)
        ):

            qp.binary_var(
                name=f"x_{i}"
            )


        linear = {}

        for i, shelter in enumerate(
            shelters
        ):

            linear[f"x_{i}"] = -shelter[
                "quantum_score"
            ]


        qp.minimize(
            linear=linear
        )


        # ----------------------------------------------------
        # QAOA
        # ----------------------------------------------------

        sampler = StatevectorSampler(
            seed=42
        )


        qaoa = QAOA(

            sampler=sampler,

            optimizer=COBYLA(
                maxiter=50
            ),

            reps=1

        )


        optimizer = MinimumEigenOptimizer(
            qaoa
        )


        result = optimizer.solve(
            qp
        )


        # ----------------------------------------------------
        # SELECTED SHELTERS
        # ----------------------------------------------------

        selected_indices = []


        for i, value in enumerate(
            result.x
        ):

            if value > 0.5:

                selected_indices.append(i)


        # ----------------------------------------------------
        # FALLBACK
        # ----------------------------------------------------

        if not selected_indices:

            best_index = max(

                range(len(shelters)),

                key=lambda i:
                    shelters[i]["quantum_score"]

            )

            selected_indices = [
                best_index
            ]


        # ----------------------------------------------------
        # ORDER
        # ----------------------------------------------------

        selected_set = set(
            selected_indices
        )


        selected_shelters = [

            shelters[i]

            for i in selected_indices

        ]


        remaining_shelters = [

            shelters[i]

            for i in range(
                len(shelters)
            )

            if i not in selected_set

        ]


        selected_shelters.sort(

            key=lambda x:
                x["quantum_score"],

            reverse=True

        )


        remaining_shelters.sort(

            key=lambda x:
                x["quantum_score"],

            reverse=True

        )


        ordered_shelters = (

            selected_shelters
            +
            remaining_shelters

        )


        return {

            "shelters":
                ordered_shelters,

            "objective_value":
                float(result.fval),

            "algorithm":
                "QAOA",

            "method":
                "QAOA-based Shelter Priority Optimization",

            "quantum_simulation":
                True

        }


    except Exception as error:

        # ----------------------------------------------------
        # CLASSICAL FALLBACK
        # ----------------------------------------------------

        shelters.sort(

            key=lambda x:
                x["score"],

            reverse=True

        )


        return {

            "shelters":
                shelters,

            "objective_value":
                None,

            "algorithm":
                "Classical Fallback",

            "method":
                "Capacity + Distance Heuristic",

            "quantum_simulation":
                False,

            "error":
                str(error)

        }


# ============================================================
# SMART SHELTER ALLOCATION API
# ============================================================

@app.route(
    "/api/shelter-allocation",
    methods=["GET"]
)
def shelter_allocation():

    location = request.args.get(
        "location"
    )


    if not location:

        return jsonify({

            "status":
                "ERROR",

            "message":
                "Location is required"

        }), 400


    # --------------------------------------------------------
    # CASE-INSENSITIVE LOCATION
    # --------------------------------------------------------

    matched_location = None


    for name in SHELTER_SOURCES:

        if name.lower() == location.lower():

            matched_location = name

            break


    if matched_location is None:

        return jsonify({

            "status":
                "ERROR",

            "message":
                "Invalid location"

        }), 400


    location = matched_location


    source = SHELTER_SOURCES[
        location
    ]


    population = source[
        "population"
    ]


    # ========================================================
    # PREPARE SHELTERS
    # ========================================================

    shelters = []


    for shelter in SHELTERS:

        available = (

            shelter["capacity"]

            -
            shelter["occupied"]

        )


        distance = calculate_distance(

            source["latitude"],

            source["longitude"],

            shelter["latitude"],

            shelter["longitude"]

        )


        availability_ratio = (

            available
            /
            shelter["capacity"]

        )


        # ----------------------------------------------------
        # CLASSICAL BASE SCORE
        # ----------------------------------------------------

        score = (

            availability_ratio
            *
            0.6

        ) + (

            (
                1
                /
                (
                    1
                    +
                    distance
                )
            )
            *
            0.4

        )


        shelters.append({

            "name":
                shelter["name"],

            "capacity":
                shelter["capacity"],

            "occupied":
                shelter["occupied"],

            "available":
                available,

            "distance_km":
                distance,

            "score":
                round(
                    score,
                    4
                )

        })


    # ========================================================
    # QAOA OPTIMIZATION
    # ========================================================

    quantum_result = optimize_shelters_qaoa(
        shelters
    )


    shelters = quantum_result[
        "shelters"
    ]


    # ========================================================
    # ALLOCATE POPULATION
    # ========================================================

    remaining_population = population

    total_allocated = 0


    for shelter in shelters:

        allocation = min(

            remaining_population,

            shelter["available"]

        )


        shelter["allocated"] = (
            allocation
        )


        shelter["remaining_capacity"] = (

            shelter["available"]
            -
            allocation

        )


        shelter["final_occupancy"] = (

            shelter["occupied"]
            +
            allocation

        )


        shelter["utilization"] = round(

            (

                shelter["final_occupancy"]
                /
                shelter["capacity"]

            ) * 100

        )


        total_allocated += allocation

        remaining_population -= allocation


    # ========================================================
    # FINAL RESULT
    # ========================================================

    shortage = max(

        population
        -
        total_allocated,

        0

    )


    allocation_rate = round(

        (

            total_allocated
            /
            population

        ) * 100

    )


    return jsonify({

        "status":
            "SUCCESS",

        "source":
            location,

        "risk_level":
            source["risk"],

        "population":
            population,

        "total_available_capacity":
            sum(
                s["available"]
                for s in shelters
            ),

        "total_allocated":
            total_allocated,

        "shortage":
            shortage,

        "allocation_rate":
            allocation_rate,

        "algorithm":
            quantum_result[
                "algorithm"
            ],

        "method":
            quantum_result[
                "method"
            ],

        "quantum_simulation":
            quantum_result[
                "quantum_simulation"
            ],

        "objective_value":
            quantum_result[
                "objective_value"
            ],

        "shelters":
            shelters

    })


# ============================================================
# QUANTUM RESOURCE OPTIMIZATION
# ============================================================

@app.route(
    "/api/quantum-optimize",
    methods=["GET"]
)
def quantum_optimize():

    try:

        disaster = get_latest_disaster()


        if disaster is None:

            return jsonify({

                "status":
                    "ERROR",

                "message":
                    "No disaster data found"

            }), 404


        result = run_qaoa(
            disaster
        )


        return jsonify({

            "status":
                "SUCCESS",

            "disaster":
                disaster.get(
                    "disaster_type"
                ),

            "risk_level":
                disaster.get(
                    "risk_level"
                ),

            "location":
                disaster.get(
                    "location"
                ),

            "population":
                disaster.get(
                    "population"
                ),

            "algorithm":
                result[
                    "algorithm"
                ],

            "method":
                result[
                    "method"
                ],

            "selected_resources":
                result[
                    "selected_resources"
                ],

            "objective_value":
                result[
                    "objective_value"
                ]

        })


    except Exception as error:

        return jsonify({

            "status":
                "ERROR",

            "message":
                str(error)

        }), 500


# ============================================================
# REPORT API
# ============================================================

@app.route(
    "/api/report",
    methods=["GET"]
)
def report():

    disaster = get_latest_disaster()


    if disaster is None:

        return jsonify({

            "status":
                "ERROR",

            "message":
                "No disaster data available"

        }), 404


    population = disaster.get(
        "population",
        0
    )


    food = disaster.get(
        "food",
        0
    )


    water = disaster.get(
        "water",
        0
    )


    medical = disaster.get(
        "medical_kits",
        0
    )


    boats = disaster.get(
        "rescue_boats",
        0
    )


    # ========================================================
    # REQUIREMENTS
    # ========================================================

    food_required = population


    water_required = (
        population * 3
    )


    medical_required = max(

        1,

        population // 20

    )


    boats_required = max(

        1,

        population // 3500

    )


    # ========================================================
    # RESPONSE
    # ========================================================

    return jsonify({

        "status":
            "SUCCESS",

        "disaster":
            disaster.get(
                "disaster_type"
            )
            or
            "Cyclone",

        "location":
            disaster.get(
                "location"
            ),

        "risk_level":
            disaster.get(
                "risk_level"
            ),

        "population":
            population,

        "resources": {

            "food":
                food,

            "food_required":
                food_required,

            "water":
                water,

            "water_required":
                water_required,

            "medical_kits":
                medical,

            "medical_required":
                medical_required,

            "rescue_boats":
                boats,

            "boats_required":
                boats_required

        }

    })


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    # Create database tables
    init_db()


    print()
    print("=" * 60)
    print("        Q-RESCUE BACKEND SERVER")
    print("=" * 60)
    print("Database:", DATABASE)
    print("Server:   http://127.0.0.1:5000")
    print()
    print("Available APIs:")
    print("  GET  /")
    print("  POST /api/signup")
    print("  POST /api/login")
    print("  GET  /api/dashboard")
    print("  POST /api/disasters")
    print("  GET  /api/disasters")
    print("  GET  /api/resources")
    print("  GET  /api/shelter-allocation")
    print("  GET  /api/quantum-optimize")
    print("  GET  /api/report")
    print("=" * 60)
    print()


    app.run(

        debug=True,

        port=5000

    )