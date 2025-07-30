
from flask import Flask, jsonify  # Flask web framework for building APIs, jsonify for converting python data to JSON
from flask_caching import Cache  # flask caching for caching responses to improve performance, pip install -U flask-caching
import random as random # used to generate random numbers
import requests # used to make HTTP requests, pip install requests
from threading import Lock # used to handle multiple requests simultaneously without conflicts, so that a request has to finish before another is made
import traceback # used for more detailed debugging
from flask_cors import CORS # used to allow cross-origin requests, so that the frontend can access the backend API from a different domain or port, pip install flask-cors
import math

application = Flask(__name__)  # creates flask webserver

CORS(application)  # enables CORS for the application, allowing cross-origin requests from the frontend
cache = Cache(application, config = { # refers to the https://flask-caching.readthedocs.io/en/latest/ documentation
    "CACHE_TYPE": "SimpleCache",  # using simple cache for caching responses
    "CACHE_DEFAULT_TIMEOUT": 0.5 # 0.5 for smoother updates 
})  # initializes cache 

earthRadiusKM = 6378.0 # radius of the Earth in kilometers
degreeToRadians = math.pi / 180.0
radianToDegree = 180.0 / math.pi
nmToKM = 1.852 # conversion factor from nautical miles to kilometers
msToK = 1.94384 # conversion factor from meters per second to knots

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
class Position:
    lat: float # latitude in degrees
    lon: float # longitude in degrees

    def distancefrom(self, other: 'Position'):  
        # calculate distance between two aircraft using the haversine formula
        #a = sin²(Δφ/2) + cos φ1 ⋅ cos φ2 ⋅ sin²(Δλ/2)
        #c = 2 ⋅ atan2( √a, √(1−a) )
        #d = R ⋅ c

        lat1 = self.lat * degreeToRadians
        lon1 = self.lon * degreeToRadians
        lat2 = other.lat * degreeToRadians
        lon2 = other.lon * degreeToRadians 

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2 
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return earthRadiusKM * c  # returns distance in kilometers

class Aircraft:
    def __init__(self, callsign: str, actype: str, alt: float, hdg: float, position: Position, speed: float, verticalspeed: float): # init is a constructor of the aircraft class
        self.callsign = callsign
        self.actype = actype
        self.alt = alt
        self.hdg = hdg
        self.position = position
        self.tas = speed
        self.verticalspeed = verticalspeed
        self.updateLOCK = Lock()  # lock to ensure thread safety when updating aircraft data
        
    def updateAircraftPosition(self, time: float = 1.0): 
        with self.updateLOCK:
            speedKMs = (self.speed * nmToKM) / 3600 # converts speed from knots to kilometers per second
            headingRadians = self.hdg * degreeToRadians  # converts heading from degrees to radians
            distance = speedKMs * time  # distance = speed x time
            angularDistance = distance / earthRadiusKM  # angular distance in radians used for calculating new position

            lat1 = self.position.lat * degreeToRadians  # converts latitude from degrees to radians
            lon1 = self.position.lon * degreeToRadians  # converts longitude from degrees to radians
            # φ₂ (newlat) = asin(sin(φ₁) * cos(d/R) + cos(φ₁) * sin(d/R) * cos(θ))
            # λ₂ (newlon) = λ₁ + atan2(sin(θ) * sin(d/R) * cos(φ₁), cos(d/R) − sin(φ₁) * sin(φ₂))
            newLat = math.asin(math.sin(lat1) * math.cos(angularDistance) + math.cos(lat1) * math.sin(angularDistance) * math.cos(headingRadians))  
            newLon = lon1 + math.atan2(math.sin(headingRadians) * math.sin(angularDistance) * math.cos(lat1),math.cos(angularDistance) - math.sin(lat1) * math.sin(newLat)) 

            self.position.lat = newLat * radianToDegree  # converts latitude back to degrees
            self.position.lon = newLon * radianToDegree  # converts longitude back to degrees
            self.alt += self.verticalspeed * (time/60)  # updates altitude based on vertical speed and time


    def dataToJsonDictionary(self): # use of abstract data type Dictionary to convert aircraft data to JSON to send to the frontend
        return {
            "callsign": self.callsign,
            "actype": self.actype,
            "altitude": self.alt,
            "heading": self.hdg,
            "lat": self.position.lat,
            "lon": self.position.lon,
            "speed": self.tas,
            "verticalspeed": self.verticalspeed
        }



@application.route('/aircraft') # defines route for bluesky api to retrieve live aircraft data at localhost/aircraft
@cache.cached(timeout=0.5)  # caches the response for 2 seconds to reduce server load

def get_aircraft(): # executes when /aircraft is accessed
    global traffic
    if traffic is None:  # checks if the traffic object is initialized
        return jsonify({"error": "Simulation initialization failed"}), 503  # returns error if traffic is not initialized
    
    
    try:
        
        traffic.update()  # updates the simulation traffic to different positions
 
        aircraftdata = []
        for i in range(traffic.ntraf):
            ac = traffic.aircraft[i]
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


