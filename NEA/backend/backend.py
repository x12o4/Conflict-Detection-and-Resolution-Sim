from flask import Flask, jsonify  # Flask web framework for building APIs, jsonify for converting python data to JSON
from bluesky import simulation  # bluesky flight simulation model

application = Flask(__name__)  # creates flask webserver
simulation = simulation.Sim()  # creates a bluesky simulation  

try: # try catch block to handle potential errors during simulation initialization
  simulation = simulation.Sim() # init sim
except Exception as e:
  print(f"Error initializing simulation: {e}")
  sim = None # fallback if simulation fails to initialize

@application.route('/aircraft') # defines route for bluesky api to retrieve live aircraft data at localhost/aircraft

def GET_aircraft(): # executes when /aircraft is accessed
  if not simulation: # check if simulation is initialized
    return jsonify({"error": "Simulation is not initialized!"}), 500  # return error if simulation is not initialized
    
    simulation.step() # advances the simulation by a timestep which makes the aircraft move to the next position
    return jsonify([{ # converts to JSON to send to the frontend
        "id": aircraft.id,
        "lat": aircraft.lat,
        "lon": aircraft.lon,
        "heading": ac.heading
    } for aircraft in sim.get_aircraft()]) # retrieves all active aircraft and extracts their id, latitude, longitude, and heading

