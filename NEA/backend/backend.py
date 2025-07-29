from flask import Flask, jsonify  # Flask web framework for building APIs, jsonify for converting python data to JSON
from bluesky import settings, traffic, navdb  # bluesky flight simulation model used to mimic flight, pip install "bluesky-simulator[full]", docs = 'https://github.com/TUDelft-CNS-ATM/bluesky/wiki/' 'https://github.com/TUDelft-CNS-ATM/bluesky/wiki/API-Reference', 'https://github.com/TUDelft-CNS-ATM/bluesky/blob/master/docs/python_demo.ipynb'
  # NavDatabase for managing navigation data like airports, runways, etc.
from flask_caching import Cache  # flask caching for caching responses to improve performance, pip install -U flask-caching
import random as random # used to generate random numbers
import requests # used to make HTTP requests, pip install requests
from threading import Lock # used to handle multiple requests simultaneously without conflicts, so that a request has to finish before another is made
import traceback # used for more detailed debugging
from flask_cors import CORS # used to allow cross-origin requests, so that the frontend can access the backend API from a different domain or port, pip install flask-cors


application = Flask(__name__)  # creates flask webserver

CORS(application)  # enables CORS for the application, allowing cross-origin requests from the frontend
cache = Cache(application, config = { # refers to the https://flask-caching.readthedocs.io/en/latest/ documentation
    "CACHE_TYPE": "SimpleCache",  # using simple cache for caching responses
    "CACHE_DEFAULT_TIMEOUT": 0.5 # 0.5 for smoother updates 
})  # initializes cache 

simulationTraffic = None  # global variable to hold the traffic object, initially set to None
def initBluesky():
    global simulationTraffic
    try:
        
         
        settings.set_variable_defaults(performance_model ='openap',  wind_model = 'zeros', dt = 1.0)
        simulationTraffic = traffic.Traffic()  # create a Traffic instance for managing aircraft in the simulation
        
        if not hasattr(simulationTraffic, 'ntraf'): # catches ntraf (ntraf is number of aricraft) error
           raise RuntimeError("Traffic object missing ntraf")
        
        # Create test aircraft with error checking
        # aircraft ID, aircraft type, latitude, longitude, heading, altitude, speed
        # stack method not data structure
        simulationTraffic.stack("CRE BAW1 B744 51.4775 -0.4614 0 20000 450")
        simulationTraffic.stack("CRE UAL2 C172 51.50 -0.50 90 18000 400") 
        simulationTraffic.process()  # process the stack commands to create aircraft
        
        if simulationTraffic.ntraf < 2:  # check if at least 2 aircraft were created
            raise RuntimeError("created {simulationTraffic.ntraf} aircraft, expected at least 2")
        
        # Perform an update to populate aircraft data
        simulationTraffic.simdt = 1.0
        simulationTraffic.update()
        
        print("BlueSky initialized successfully with 2 aircraft")
        return True
        
    except Exception as e:
        traceback.print_exc() # prints the stack trace for debugging
        print(f"BlueSky initialization failed: {str(e)}")
        simulationTraffic = None
        return False
 
class ourAirportsAPI:
  URL = "https://www.ourairports.com/data"
  LOCK = Lock()

  @cache.memoize(timeout=3600)  # caches the response for 1 hour to reduce server load, memoize is used to cache result, timeout is an hour because airport data rarely changes

  def get_airport(self, icao): 
        try:
            with self.LOCK: # makes sure only one thread can access at a time, used for multiple users requesting the airport data simultaneously
                url = f"{self.URL}/airports/{icao}/airport.json" # retrieves airport data from ourairports.com API using the ICAO code
                response = requests.get(url, timeout=3) # makes a GET request to the API with a timeout of 3 seconds
                return response.json() if response.status_code == 200 else None # returns 200 if successful, otherwise return None
        except:
            print(f"Airport API error")
            return None # if anything goes wrong, dont crash instead return None
          
airportAPI = ourAirportsAPI()  # creates an instance of the ourAirportsAPI class to access airport data

print("Initializing Bluesky Simulation")
if initBluesky():
    print("Bluesky Simulation initialized successfully")
else:
    print("Bluesky Simulation initialization failed")

@application.route('/aircraft') # defines route for bluesky api to retrieve live aircraft data at localhost/aircraft
@cache.cached(timeout=0.5)  # caches the response for 2 seconds to reduce server load

def get_aircraft(): # executes when /aircraft is accessed
    global simulationTraffic
    if simulationTraffic is None:  # checks if the simulationTraffic object is initialized
        print("Simulation traffic not initialized, initializing now...")
        if not initBluesky():
         return jsonify({"error": "Simulation initialization failed"}), 503  # returns error if simulationTraffic is not initialized
    
    try:
        simulationTraffic.simdt = 1  # sets simulation time step to 1 second
        simulationTraffic.update()  # updates the simulation traffic to different positions
 
        aircraftdata = []
        for i in range(simulationTraffic.ntraf):
            ac = simulationTraffic.aircraft[i]
            aircraftdata.append({ # retrieves all active aircraft and extracts their id, latitude, longitude, and heading
                "id": ac.id,
                "lat": ac.lat,
                "lon": ac.lon,
                "heading": ac.hdg, # heading in degrees
                "altitude": ac.alt, # altitude in feet
                "speed": getattr(ac, 'tas', 0) # Using getattr as safety
            })
 

        return jsonify(aircraftdata)  # returns the aircraft data as JSON 
    except Exception as e:
        traceback.print_exc()  # prints the stack trace for debugging
        return jsonify({"error": str(e)}), 500  # returns error if anything goes wrong

if __name__ == '__main__':
  application.run(debug= True, port=5000, use_reloader=False) # runs the flask application


