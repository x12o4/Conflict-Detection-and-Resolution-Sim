from flask import Flask, jsonify  # Flask web framework for building APIs, jsonify for converting python data to JSON
from bluesky import settings, traffic  # bluesky flight simulation model used to mimic flight, pip install "bluesky-simulator[full]", docs = 'https://github.com/TUDelft-CNS-ATM/bluesky/wiki/' 'https://github.com/TUDelft-CNS-ATM/bluesky/wiki/API-Reference', 'https://github.com/TUDelft-CNS-ATM/bluesky/blob/master/docs/python_demo.ipynb'
  # NavDatabase for managing navigation data like airports, runways, etc.
from flask_caching import Cache  # flask caching for caching responses to improve performance, pip install -U flask-caching
import random as random # used to generate random numbers
import requests # used to make HTTP requests, pip install requests
from threading import Lock # used to handle multiple requests simultaneously without conflicts, so that a request has to finish before another is made


application = Flask(__name__)  # creates flask webserver

cache = Cache(application, config = { # refers to the https://flask-caching.readthedocs.io/en/latest/ documentation
    "CACHE_TYPE": "SimpleCache",  # using simple cache for caching responses
    "CACHE_DEFAULT_TIMEOUT": 0.5 # 0.5 for smoother updates 
})  # initializes cache 

simulationTraffic = None  # global variable to hold the traffic object, initially set to None
def initBluesky():
  global simulationTraffic  # allows modification of the global variable simulationTraffic
  try:
    # try-catch block to handle potential errors during simulation initialization
      settings.set_variable_defaults(init_mode= 'sim')  # initializes settings for the simulation
      simulationTraffic = traffic.Traffic()  # creates traffic object to manage aircraft in the simulation
      
      if simulationTraffic is not None:
        # Two test aircraft, contain callsign, aircraft type, latitude, longitude, heading, altitude (ft), and speed (knots)
        aircraft1 = simulationTraffic.cre('BAW123', 'A320', 51.4775, -0.4614, 0, 20000, 450)
        aircraft2 = simulationTraffic.cre('UAL456', 'B737', 51.50, -0.50, 90, 18000, 400)
        

        if None in [aircraft1, aircraft2]:
            raise RuntimeError("Aircraft creation failed")
        
        print("BlueSky is initialised successfully with 2 aircraft.")
        return True
      else:
        raise RuntimeError("Traffic creation failed.")  # raise error if simulationTraffic is None

  except Exception as e:
    print(f"An error occurred during simulation initialization: {e}")
    simulationTraffic = None  # set simulationTraffic to None if an error occurs
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







initBluesky() # calls the function to initialize the BlueSky simulation
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