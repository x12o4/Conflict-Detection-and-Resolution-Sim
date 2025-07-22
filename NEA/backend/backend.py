from flask import Flask, jsonify  # Flask web framework for building APIs, jsonify for converting python data to JSON
from bluesky import settings, navdb, traffic  # bluesky flight simulation model used to mimic flight, pip install "bluesky-simulator[full]", docs = 'https://github.com/TUDelft-CNS-ATM/bluesky/wiki/' 'https://github.com/TUDelft-CNS-ATM/bluesky/wiki/API-Reference'
from flask_caching import Cache  # flask caching for caching responses to improve performance, pip install -U flask-caching
import random as random # used to generate random numbers

application = Flask(__name__)  # creates flask webserver

cache = Cache(application, config = { # refers to the https://flask-caching.readthedocs.io/en/latest/ documentation
    "CACHE_TYPE": "SimpleCache",  # using simple cache for caching responses
    "CACHE_DEFAULT_TIMEOUT": 0.5 # 0.5 for smoother updates 
})  # initializes cache 

try:
    # try-catch block to handle potential errors during simulation initialization
    settings.init_mode('sim')  # initializes settings for the simulation
    navdb.init()  # initialize navigation database which contains airports, etc.
    simulationTraffic = traffic.Traffic()  # creates traffic object to manage aircraft in the simulation

    if simulationTraffic is not None:
        # Two test aircraft, contain callsign, aircraft type, latitude, longitude, heading, altitude (ft), and speed (knots)
        aircraft1 = simulationTraffic.cre('BAW123', 'A320', lat=51.4775, lon=-0.4614, hdg=0, alt=20000, spd=450)
        aircraft2 = simulationTraffic.cre('UAL456', 'B737', lat=51.50, lon=-0.50, hdg=90, alt=18000, spd=400)
        print("BlueSky is initialised successfully with 2 aircraft.")
    else:
        raise RuntimeError("Traffic creation failed.")  # raise error if simulationTraffic is None

except Exception as e:
    print(f"An error occurred during simulation initialization: {e}")
   
except Exception as e:
  print(f"Error initializing BlueSky: {e}")
  simulationTraffic = None # fallback if simulation fails to initialize


@application.route('/aircraft') # defines route for bluesky api to retrieve live aircraft data at localhost/aircraft
@cache.cached()  # caches the response for 2 seconds to reduce server load

def get_aircraft(): # executes when /aircraft is accessed
  if not simulationTraffic: # check if simulation is initialized
    return jsonify({"error": "Simulation is not initialized!"}), 500  # return error if simulation is not initialized
    
  simulationTraffic.simdt = 1  # sets simulation time step to 1 second
  simulationTraffic.update()  # updates the simulation traffic to different positions
 
  return jsonify([{  # converts to JSON to send to the frontend
        "id": aircraft.id,
        "lat": aircraft.lat,
        "lon": aircraft.lon,
        "heading": aircraft.hdg,  # heading in degrees
        "altitude": aircraft.alt,  # altitude in feet
    } for aircraft in simulationTraffic]) # retrieves all active aircraft and extracts their id, latitude, longitude, and heading

if __name__ == '__main__':
  application.run(debug= True) # runs the flask application