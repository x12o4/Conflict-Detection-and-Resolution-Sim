Flight Collision Avoidance System

A real-time 3D aircraft collision avoidance simulator with a 2D world map interface. The system continuously monitors airspace, predicts conflict windows using Closest Point of Approach (CPA) geometry, ranks threats by a composite risk score, and autonomously reroutes aircraft using A* pathfinding, sourcing real airport coordinates using the OpenStreetMap Overpass API.

Live demo: nea-dps5.onrender.com (server has to be turned on because very resource intensive)

How It Works

Physics Simulation

Each aircraft is modelled with real flight physics. Position is updated each tick using the spherical law of cosines (haversine), computing new latitude/longitude from heading, true airspeed (knots), and a changeable time step.

Overpass API

Real airport coordinates are fetched from the OpenStreetMap Overpass API by ICAO code and cached in-memory for one hour, avoiding redundant network calls. Thread safety is enforced with a Lock on the cache.

Conflict Detection 

All aircraft pairs are checked each cycle (O(n²)). For each pair, 3D position and velocity vectors are projected into a local Cartesian frame (metres). The Closest Point of Approach time is derived by the equation:

t_cpa = -(Δr · Δv) / |Δv|²

Separation at t_cpa is then checked against ICAO minima (default: 5 NM horizontal, 1000 ft vertical). Immediate conflicts (within 20 s or 0.8 km) are flagged for urgent resolution; predicted conflicts within a 15-minute lookahead window are queued for monitoring or rerouting.

Risk Scoring

Each conflict is assigned a composite risk score (0–1) using exponential decay functions across four dimensions.
Emergency conflicts receive a multiplier that pushes their score toward 1.0.

Priority Queue

Scored conflicts are pushed into a max-heap (with negated scores) so the most dangerous pair is always resolved first.

Conflict Resolution

The resolver cycles through four strategies in order, stopping at the first that works:

Altitude separation reassigns the aircraft to a safe flight level (1000 ft minimum vertical separation from all traffic)
Horizontal reroute runs A* to find a new path to the destination
Speed adjustment reduces speed by 10% and rechecks CPA
Combined — altitude change + 15 degrees heading offset
A 60-second cooldown per aircraft pair prevents re-resolution thrashing.

A* Pathfinding (3D)

A* searches a 3D grid of (lat, lon, altitude) nodes. The heuristic is straight-line distance + altitude difference penalty. Neighbours are generated in 8 horizontal directions plus 1/2 flight levels. Each node is checked for safety by predicting all other aircraft positions 90 seconds ahead (haversine). Movement cost penalises altitude changes (×3) and bearing deviations. Three fallback strategies with looser safety buffers (6 km - 4 km - 3 km) are tried if the initial search fails.

Tech Stack

Python,Flask,Javascript, Html,Css


API Endpoints

GET/Serves the frontend
POST/initAirspace/<n> Initialises airspace with n aircraft (1–100)
GET/aircraft Returns live aircraft state (cached 0.5s)
GET/conflicts Detects and returns current conflicts with risk scores
POST/addAircraftAdds one random aircraft to the simulation
GET/airport/<icao> Returns lat/lon for an ICAO airport code


Getting Started

Prerequisites

Flask==3.1.1
flask-caching==2.3.1
flask-cors==6.0.1
requests==2.32.4
gunicorn==21.2.0

Installation

bashgit clone https://github.com/x12o4/Conflict-Detection-and-Resolution-Sim.git
cd Conflict-Detection-and-Resolution-Sim/NEA/backend
pip install flask flask-cors flask-caching requests

Running

bashpython backend.py

Then open http://localhost:5000 in your browser.

Project Structure

NEA/
└── backend/
    ├── backend.py        # Simulation engine, Flask API, CPA, A*, risk scoring
    └── templates/
        └── index.html    # Frontend map interface
collision.log             # Runtime conflict event log
