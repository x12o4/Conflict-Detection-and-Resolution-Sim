
from flask import Flask, jsonify  # Flask web framework for building APIs, jsonify for converting python data to JSON
from flask_caching import Cache  # flask caching for caching responses to improve performance, pip install -U flask-caching
import random as random # used to generate random numbers
import requests # used to make HTTP requests, pip install requests
from threading import Lock # used to handle multiple requests simultaneously without conflicts, so that a request has to finish before another is made
import traceback # used for more detailed debugging
from flask_cors import CORS # used to allow cross-origin requests, so that the frontend can access the backend API from a different domain or port, pip install flask-cors
import math 
from math import exp # exp used for exponential calculations
import time
import heapq # used for priority queue implementation
import logging

# cd 'C:\Users\ethan\OneDrive\Desktop\NEA\NEA\backend' ignore this its just for me to cd into the file easier
logging.basicConfig(filename="collision.log", level=logging.WARNING) # sets up logging to a file, logs warnings and above (error, critical) to the file

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
kToKMH = 1.852 # conversion factor from knots to kilometers per hour


class ourAirportsAPI:
  URL = "https://www.ourairports.com/data"
  LOCK = Lock()

  @cache.memoize(timeout=3600)  # caches the response for 1 hour to reduce server load, memoize is used to cache result, timeout is an hour because airport data rarely changes

  def getAirport(self, icao): 
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

    def __init__(self, lat: float, lon: float):
        self.lat = lat
        self.lon = lon
        
    

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
    
    def bearingTo(self, other: 'Position'):
        lat1 = degreeToRadians * self.lat  # converts latitude from degrees to radians
        lon1 = degreeToRadians * self.lon  # converts longitude from degrees to radians
        lat2 = degreeToRadians * other.lat  # converts latitude from degrees to radians
        lon2 = degreeToRadians * other.lon  # converts longitude from degrees to radians
        # θ = atan2( sin Δλ ⋅ cos φ2 , cos φ1 ⋅ sin φ2 − sin φ1 ⋅ cos φ2 ⋅ cos Δλ )
        dlon = lon2 - lon1  # calculates the difference in longitude
        x = math.sin(dlon) * math.cos(lat2)  # calculates the x component of the bearing
        y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)  # calculates the y component of the bearing

        bearing = math.atan2(x, y)  # calculates the bearing in radians
        return (radianToDegree(bearing) + 360) % 360  # converts bearing to degrees 

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
            speedKMs = (self.tas * nmToKM) / 3600 # converts speed from knots to kilometers per second
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

class simAirspace:

    def __init__(self):
        self.aircraft: dict[str, Aircraft] = {}  # dictionary to store aircraft objects with callsign as key
        self.LOCK = Lock()  # lock to ensure thread safety when updating aircraft data
        self.startTime = time.time()  # records the start time of the simulation

    def addAircraft(self, aircraft: Aircraft):
        with self.LOCK:
            self.aircraft[aircraft.callsign] = aircraft # adds aircraft to the dictionary
    
    def removeAircraft(self, aircraft: Aircraft):
        with self.LOCK:
            if aircraft.callsign in self.aircraft:
                del self.aircraft[aircraft.callsign]

    def updateAirspace(self, time):
        print(f"\n updating airspace ")
        with self.LOCK:
            for aircraft in self.aircraft.values():
                aircraft.updateAircraftPosition(time)  # updates the position of each aircraft in the airspace
    def getAircraftData(self):
        with self.LOCK:
            return [aircraft.dataToJsonDictionary() for aircraft in self.aircraft.values()] # returns a list of aircraft data in JSON format
    
      # minimum separation distance in kilometers, set to 5 nautical miles
     # minimum altitude difference in feet, set to 1000 feet

    # priority queue implementation
    def DetectConflicts(self,  minimumSeperationDistanceKM: float = nmToKM * 5,
     minimumAltitudeDifferenceFT: float = 1000.0):

     conflict = [] # list to store conflicts
     aircraftList = list(self.aircraft.values())  # converts the dictionary of aircraft to a list 

    # use of 2 for loops means the function becomes O(N^2) in time complexity, n being the number of aircraft in the airspace
    # might need to be optimised if the number of aircraft increases 
     for i in range(len(aircraftList)): 
        for j in range(i + 1, len(aircraftList)): # iterate through the aircraft list, starting from the next aircraft to avoid comparing the same aircraft with itself
            # compares each aircraft with every other aircraft to find conflicts
            aircraft1 = aircraftList[i] #
            aircraft2 = aircraftList[j]
            distanceKM = aircraft1.position.distancefrom(aircraft2.position) # calculates distance between two aircraft using the distancefrom subroutine in Position class     
            altitudeDifferenceFT = abs(aircraft1.alt - aircraft2.alt) # calculates altitude difference between two aircraft, abs used to get the absolute value

            # checks if the distance and altitude difference are below the minimum standard for aeroplanes by ICAO standards
            if distanceKM < minimumSeperationDistanceKM and altitudeDifferenceFT < minimumAltitudeDifferenceFT:
                # used to determine the place in the priority queue, the closer to 1 means the higher the risk of colliding
                horizontalRisk = 1 - (distanceKM / minimumSeperationDistanceKM)
                verticalRisk = 1 - (altitudeDifferenceFT / minimumAltitudeDifferenceFT)

                # placeholders until the actual function is implemented
                speedRisk = self.calculateSpeedRisk(aircraft1, aircraft2)
                timeToCollision = self.calculateTimeToCollision(aircraft1, aircraft2) 

                # risk score ranging from 0 to 1, used to determine the place in the priority queue
                riskScore = 0.4 * horizontalRisk + 0.4 * verticalRisk + 0.2 * speedRisk * 0.1 * (1 / (1 + exp(timeToCollision)))
                

                heapq.heappush(conflict, ( 
                -riskScore, { # -riskScore is used to implement a maxheap (finding the highest priority first) as python's heapq  is a minheap (finds the lowest priority) by default
                "aircraft1": aircraft1.callsign,
                "aircraft2": aircraft2.callsign,
                "distanceKM": distanceKM,
                "altitudeDifferenceFT": altitudeDifferenceFT,
                "riskScore": riskScore,
                "timeToCollision": timeToCollision
                    }
                ))
                

        return [item[1] for item in heapq.nsmallest(len(conflict),conflict)] # returns conflicts sorted by risk score,  heapq.nsmallest(len(conflict),conflict)] returns items ordered asc, which because of the negative risk scores it # means the highest risk score is first, so we return the first item in the list, item[1] returns the second element in the tuple which is the dictionary 
            
    
    def velocityvector(self, aircraft: Aircraft): # calculates the velocity vector of an aircraft in km/h
        speedKMs = (aircraft.tas * kToKMH) / 3600  # converts speed from knots to kilometers per second
        headingRadians = aircraft.hdg * degreeToRadians

        vEast = speedKMs * math.sin(headingRadians)  # calculates eastward velocity component, formula is v = speed * sin(heading) for eastward velocity
        vNorth = speedKMs * math.cos(headingRadians)  # calculates northward velocity component, formula is v = speed * cos(heading) for northward velocity

        return (vEast, vNorth)  # returns the velocity vector as a tuple (eastward velocity, northward velocity) in km/h
    def calculateSpeedRisk(self, aircraft1: Aircraft, aircraft2: Aircraft): # calculates speed risk between two aircraft

        vel1 = self.velocityvector(aircraft1)
        vel2 = self.velocityvector(aircraft2)
        # euclidean distance formula 
        relativeVelocity = math.sqrt((vel1[0] - vel2[0]) ** 2 + (vel1[1] - vel2[1]) ** 2)  # calculates relative velocity between two aircraft
        normalisedSpeedRisk = relativeVelocity /500 # normalises the speed risk to a value between 0 and 1, 500 is an arbitrary value for normalisation, can be adjusted 
        return min(normalisedSpeedRisk, 1.0) # returns the minimum of the normalised speed risk and 1.0 to ensure it does not exceed 1.0
    
    

    def Converging(self, aircraft1: Aircraft, aircraft2: Aircraft):
        # checks if two aircraft are converging based on their headings
        bearing = aircraft1.position.bearingTo(aircraft2.position)  # calculates bearing from aircraft1 to aircraft2 (0-360)
        relAngle = (aircraft1.hdg - bearing + 360) % 360  # calculates relative angle between aircraft1 and aircraft2
        return abs(relAngle - 180) < 90 # checks if the relative angle is within 90 deg of convergence 
    
    


    def calculateTimeToCollision(self, aircraft1: Aircraft, aircraft2: Aircraft):
        if not self.Converging(aircraft1, aircraft2): # checks if the two aircraft are converging
            return float('inf') # if aircraft are not converging, return infinity as there is no risk of collision (mathimatically, this means they are not on a collision course)
        
        currentDistanceKM = aircraft1.position.distancefrom(aircraft2.position)  # calculates current distance between two aircraft
        closingSpeedKMH = self.getClosingSpeed(aircraft1, aircraft2)  # calculates closing speed between two aircraft in km/h

        if closingSpeedKMH < 0.1: # avoids near-zero division
            return float('inf')
        
        return (currentDistanceKM / closingSpeedKMH) * 60 # returns time to collision in mins
    
    def getClosingSpeed(self, aircraft1: Aircraft, aircraft2: Aircraft): # closing speed is the negative derivative of the distance between two aircraft
        v1East = aircraft1.tas * math.sin(degreeToRadians * aircraft1.hdg)  # formula is v = speed * sin(heading) for eastward velocity
        v1North = aircraft1.tas * math.cos(degreeToRadians * aircraft1.hdg) # formula is v = speed * cos(heading) for northward velocity

        v2East = aircraft2.tas * math.sin(degreeToRadians * aircraft2.hdg)
        v2North = aircraft2.tas * math.cos(degreeToRadians* aircraft2.hdg)

        relativeEast = v1East - v2East  # calculates relative eastward velocity
        relativeNorth = v1North - v2North # calculates relative northward velocity

        # closing speed = √[(V₁ₓ - V₂ₓ)² + (V₁ᵧ - V₂ᵧ)²]
        return math.sqrt(relativeEast ** 2 + relativeNorth ** 2) * kToKMH # returns closing speed in km/h
    

airspace = simAirspace() # creates an instance of the simAirspace class to manage aircraft data and conflicts
airspace.addAircraft(Aircraft(callsign="BAW1", actype="B744", alt=35000, hdg=45, position=Position(51.4775, -0.4614), speed=450, verticalspeed=0)) #  callsign, aircraft type, altitude in feet,  heading in degrees, latitude, longitude, speed in knots, vertical speed in feet per minute
airspace.addAircraft(Aircraft(callsign="UAL2", actype="B744", alt=36000, hdg=225, position=Position(51.50, -0.40), speed=500, verticalspeed=0))
@application.route('/aircraft') # defines route to retrieve live aircraft data at localhost/aircraft
@cache.cached(timeout=0.5)  # caches the response for 0.5 seconds to reduce server load




def getAircraft(): # executes when /aircraft is accessed
   try:
       airspace.updateAirspace(1.0) # updates the airspace with a time step of 1 second
       return jsonify(airspace.getAircraftData())  # returns the aircraft data in JSON format
   except Exception as e:
       traceback.print_exc()
       return jsonify({"error": str(e)}), 500
       
if __name__ == '__main__':
    print("Starting Simulation..")
    
    application.run(debug=True, port=5000, use_reloader=False)



