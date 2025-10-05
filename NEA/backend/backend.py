
from flask import Flask, jsonify  # Flask web framework for building APIs, jsonify for converting python data to JSON
from flask_caching import Cache  # flask caching for caching responses to improve performance, pip install -U flask-caching
import random
import requests # used to make HTTP requests, pip install requests
from threading import Lock # used to handle multiple requests simultaneously without conflicts, so that a request has to finish before another is made
import traceback # used for more detailed debugging
from flask_cors import CORS # used to allow cross-origin requests, so that the frontend can access the backend API from a different domain or port, pip install flask-cors
import math 
from math import exp # exp used for exponential calculations
import time
import heapq # used for priority queue implementation
import logging
from typing import Tuple, Optional, Set, List # used for type hinting
from dataclasses import dataclass, field
from enum import Enum # for named values
import os

# using git bash for terminal 
# cd 'C:\Users\ethan\OneDrive\Desktop\NEA\NEA\backend' ignore this its just for me to cd into the file easier

application = Flask(__name__)  # creates flask webserver

CORS(application)  # enables CORS for the application, allowing cross-origin requests from the frontend
cache = Cache(application, config = { # refers to the https://flask-caching.readthedocs.io/en/latest/ documentation
    "CACHE_TYPE": "SimpleCache",  # using simple cache for caching responses
    "CACHE_DEFAULT_TIMEOUT": 0.5 # 0.5 for smoother updates 
})  # initialises cache 

port = int(os.getenv("PORT", 5000))  # gets port from environment variable or defaults to 5000 (i used this because render wont detect an open port otherwise) 
airportCache = {}; # this stores the airports in the cache as fetching everytime from the api is not optimal, also airport data rarely changes 
earthRadiusKM = 6378.0 
degreeToRadians = math.pi / 180.0
radianToDegree = 180.0 / math.pi
nmToKM = 1.852 
msToK = 1.94384 
kToKMH = 1.852 
degreesToMeters = 111320 
feetToMeters = 0.3048 
knotsToMs = 0.514444 
feetPerMinToMS = 0.00508 
feetToKM = 0.0003048





        
def overpassAirportAPI(icao): # https://wiki.openstreetmap.org/wiki/Overpass_API#Quick_Start_(60_seconds):_for_Developers/Programmers
    cacheKey = f"{icao} airport" # creates key based upon icao code
    if cacheKey in airportCache:
        cacheData, timestamp = airportCache[cacheKey] # timestamp is the time the data was saved
        if time.time() - timestamp < 3600: # 1 hour cache timeout
            return cacheData # returns airport data such as lat lon
    overpassURL = 'https://overpass-api.de/api/interpreter'
    overpassQuery = f'[out:json];(nwr[aeroway~"aerodrome|airport"][icao="{icao.upper()}"];);out center;'
    try:
        response = requests.get(overpassURL, params={'data': overpassQuery}, timeout=15) # make GET request to overpass
        if response.status_code == 200: # checks if the request was successful
            data = response.json() # converts to json
            for element in data.get('elements', []): # iterate through elements in the response
                if 'tags' in element: # only process elements with tags (overpass data is stored in tags)
                    AirportData = {
                        'icao': icao.upper(), # converts ICAO code to uppercase
                        'name': element['tags'].get('name', 'Unknown Airport'),
                        'lat': element.get('lat') or element.get('center', {}).get('lat'), # get lat and lon from either node or center
                        'lon': element.get('lon') or element.get('center', {}).get('lon'),
                    }
                    if AirportData['lat'] is not None and AirportData['lon'] is not None:
                        airportCache[cacheKey] = (AirportData, time.time())
                        return AirportData
        print(f"No valid data for {icao}")
        return None
    except Exception as e:
        logging.warning(f"Error fetching airport data for {icao}: {str(e)}")
        return None  # returns None if no data is found or an error occurs

@application.route('/airport/<icao>')  # defines route to retrieve airport data at localhost/airport/ICAO
def fetchAirport(icao):
    with Lock():
        cacheKey = f"{icao} airport" # same thing as above happens here
        if cacheKey in airportCache:
            cacheData, timestamp = airportCache[cacheKey]
            if time.time() - timestamp < 3600:
                return jsonify(cacheData)
        airportData = overpassAirportAPI(icao)
        if airportData:
            airportCache[cacheKey] = (airportData, time.time())
            return jsonify(airportData)
    
    return jsonify({"error": "Airport not found"}), 404  # returns 404 if airport not found or an error occurs



        
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
        return (radianToDegree * bearing + 360) % 360  # converts bearing to degrees 
    
class Waypoint:
    def __init__(self, position: Position, name: str = ""):
        self.position = position
        self.name = name

class flightPath:
    def __init__(self, departureAirport: Position, arrivalAirport: Position):
        self.waypoints = []  # list to store waypoints in the flight path
        self.currentWaypointIndex = 0 # index of the current waypoint in the flight path
        self.departureAirport = departureAirport  
        self.arrivalAirport = arrivalAirport
        self.generateRoute()

    def generateRoute(self):
        self.waypoints = [Waypoint(self.departureAirport, "Departure"), Waypoint(self.arrivalAirport, "Arrival")]  # adds departure airport as the first waypoint and arrival airport as the last waypoint in the flight path
    
    def getCurWaypoint(self):
        if self.currentWaypointIndex < len(self.waypoints): # checks if the current waypoint index is within the bounds of the waypoints list
            return self.waypoints[self.currentWaypointIndex]
        return None # returns None if the current waypoint index is out of bounds

    def advWaypoint(self):
        self.currentWaypointIndex += 1 # advances to the next waypoint in the flight path

    def pathIsComplete(self):
        return self.currentWaypointIndex >= len(self.waypoints)  # checks if the flight path is complete by comparing the current waypoint index with the length of the waypoints list, returns a bool
class Aircraft:
    def __init__(self, callsign: str, actype: str, alt: float, hdg: float, position: Position, speed: float, verticalspeed: float, departureICAO: str, arrivalICAO: str): # init is a constructor of the aircraft class, icao is a 4 letter code for recognising an airport
        self.callsign = callsign
        self.actype = actype
        self.alt = alt
        self.hdg = hdg
        self.position = position
        self.tas = speed
        self.verticalspeed = verticalspeed
        self.updateLOCK = Lock()  # lock to ensure thread safety when updating aircraft data
        self.departureICAO = departureICAO  # ICAO code of the departure airport
        self.arrivalICAO = arrivalICAO  # ICAO code of the arrival airport
        self.flightPath = None # flight path set to none until it is assigned
        self.targetHeading = hdg  # target heading for the aircraft, used for autopilot and navigation purposes
        self.waypointTolerance = 5.0 # tolerance in kilometres 
        self.headingChangeRate = 2.0 # rate of change in heading in degrees, used for smooth changes
        self.flightStatus = "Departure"  # flight status, can be "Departure", "Enroute","Arriving", "Arrived", etc. used to determine the current phase of flight
        self.hasArrived = False  # flag to indicate if the aircraft has arrived at its destination

    def setFlightPath(self, departurePosition: Position, arrivalPosition: Position):
        self.flightPath = flightPath(departurePosition, arrivalPosition)

    def navigateWaypoint(self):
        if not self.flightPath or self.flightPath.pathIsComplete():
            return
        curWaypoint = self.flightPath.getCurWaypoint()  # gets the current waypoint in the flight path
        if not curWaypoint:
            return
        
        self.targetHeading = self.position.bearingTo(curWaypoint.position)  # sets the target heading to the bearing to the current waypoint
        distanceFromWaypoint = self.position.distancefrom(curWaypoint.position)  # calculates the distance from the current waypoint

        if distanceFromWaypoint < self.waypointTolerance:  # checks if the aircrft is within waypoint tolerance
            print(f"Aircraft {self.callsign} reached waypoint {curWaypoint.name}")
            self.flightPath.advWaypoint()  # advances to the next waypoint in the flight path

            if self.flightPath.pathIsComplete():  # checks if the flight path is complete
                self.flightStatus = "Arrived"  # sets the flight status to "Arrival" if the flight path is complete
                self.tas = 0 # sets the speed of the plane to 0
                self.hasArrived = True
                print(f"{self.callsign} has arrived at {self.arrivalICAO} from {self.departureICAO}.")  # prints a message to the console when the aircraft arrives at its destination
            elif self.flightPath.currentWaypointIndex == len(self.flightPath.waypoints) - 1: # checks if the current waypoint is the last waypoint in the flight path
                self.flightStatus = "Arriving"
            else:
                self.flightStatus = "Enroute"
    def updateHeading(self, time: float):
        headingDifference = (self.targetHeading - self.hdg + 360) % 360 # calculates the difference between the target heading and the current heading, ensures it is positive by adding 360 and taking modulo 360
        if headingDifference > 180:  # checks if greater than 180 degrees
            headingDifference -= 360  # subtracts 360 to get the shortest path to the target heading
        maxHeadingChangeRate = self.headingChangeRate * time  # calculates the maximum heading change rate based on the time step
        if abs(headingDifference) > maxHeadingChangeRate: 
            if headingDifference > 0:
                self.hdg = (self.hdg + maxHeadingChangeRate) % 360  # updates the heading by adding the maximum heading change rate, ensures it is within 0-360 degrees
            else:
                self.hdg = (self.hdg - maxHeadingChangeRate + 360) % 360 # subtracts instead of adding to ensure it is within 0-360 degrees
        else:
            self.hdg = self.targetHeading # set the heading to the target heading if the difference is less than the maximum heading change rate

    def updateAircraftPosition(self, time: float = 1.0): 
        with self.updateLOCK:
            
            if(self.hasArrived):
                return
            
            self.navigateWaypoint()  # navigates to the next waypoint in the flight path
            self.updateHeading(time)
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
        waypoints = []
        if self.flightPath and self.flightPath.waypoints:
            waypoints = [
                {
                    "lat": waypoint.position.lat,
                    "lon": waypoint.position.lon,
                    "name": waypoint.name
                }
                for waypoint in self.flightPath.waypoints
            ]
        
        return {
            "callsign": self.callsign,
            "actype": self.actype,
            "altitude": self.alt,
            "heading": self.hdg,
            "lat": self.position.lat,
            "lon": self.position.lon,
            "speed": self.tas,
            "verticalspeed": self.verticalspeed,
            "departureICAO": self.departureICAO,
            "arrivalICAO": self.arrivalICAO,
            "flightStatus": self.flightStatus,
            "targetHeading": self.targetHeading,
            "waypoints": waypoints,
            "currentWaypointIndex": self.flightPath.currentWaypointIndex if self.flightPath else 0
        }
    
class CPA(): # store result of cpa
    def __init__(self, timeToCollision: float, distanceAtCPA: float, cpaPosition1: Tuple[float,float], cpaPosition2: Tuple[float,float]):
        self.timeToCollision = timeToCollision
        self.distanceAtCPA = distanceAtCPA
        self.cpaPosition1 = cpaPosition1
        self.cpaPosition2 = cpaPosition2

def calculateCPA(aircraft1: Aircraft, aircraft2: Aircraft):
    avgLAT = math.radians((aircraft1.position.lat + aircraft2.position.lat) / 2)  # calculates average latitude in radians

    # https://stackoverflow.com/questions/7477003/calculating-new-longitude-latitude-from-old-n-meters
    x1 = aircraft1.position.lon * math.cos(avgLAT) * degreesToMeters
    y1 = aircraft1.position.lat * degreesToMeters
    z1 = aircraft1.alt * feetToMeters

    x2 = aircraft2.position.lon * math.cos(avgLAT) * degreesToMeters
    y2 = aircraft2.position.lat * degreesToMeters
    z2 = aircraft2.alt * feetToMeters

    # converts speed from knots to meters per second
    velocity1toMS = aircraft1.tas * knotsToMs
    velocity2toMS = aircraft2.tas * knotsToMs

    # formula is v = speed * sin(heading) for eastward velocity and v = speed * cos(heading) for northward velocity and z component is vertical speed in feet per minute converted to meters per second
    velocity1X = velocity1toMS * math.sin(math.radians(aircraft1.hdg))  # eastward velocity component 
    velocity1Y = velocity1toMS * math.cos(math.radians(aircraft1.hdg))  # northward velocity component
    velocity1Z = aircraft1.verticalspeed * feetPerMinToMS

    velocity2X = velocity2toMS * math.sin(math.radians(aircraft2.hdg))  # eastward velocity component
    velocity2Y = velocity2toMS * math.cos(math.radians(aircraft2.hdg))  # northward velocity component
    velocity2Z = aircraft2.verticalspeed * feetPerMinToMS

    # calculate relative position and velocity vectors, Vab = Va - Vb

    dx = x1 - x2  # difference in x coordinates
    dy = y1 - y2  # difference in y coordinates
    dz = z1 - z2  # difference in z coordinates

    dvx = velocity1X - velocity2X  # difference in eastward velocity components
    dvy = velocity1Y - velocity2Y  # difference in northward velocity components
    dvz = velocity1Z - velocity2Z  # difference in vertical velocity components

    altitudeDifference = abs(aircraft1.alt - aircraft2.alt)  
    currDistance = math.sqrt(dx * dx + dy * dy + dz * dz)  # calculates current distance between aircraft using Euclidean distance formula

    # check for conflict immediately
    if currDistance < 5000 and altitudeDifference < 1000:
        return CPA(timeToCollision=0,distanceAtCPA=currDistance/1000, cpaPosition1=(aircraft1.position.lat, aircraft1.position.lon, aircraft1.alt), cpaPosition2=(aircraft2.position.lat, aircraft2.position.lon, aircraft2.alt))  
        
    # t_cpa = -(dr · dv) / |dv|²
    drDotDv = dx * dvx + dy * dvy + dz * dvz  # dot product of position and velocity vectors
    dvSquared = dvx * dvx + dvy * dvy + dvz * dvz  # squared magnitude of the velocity vector


    if(abs(dvSquared) < 1e-6): #i used 1e-6 as a threshold to avoid division by zero
        return None # if squared magnitude of the velocity vector is small

    timeToCPA = -(drDotDv) / dvSquared  

    if timeToCPA < 0:  # if time to CPA is negative, the aircraft are moving away from each other
        return None

    x1atCPA = x1 + velocity1X * timeToCPA  # calculates x coordinate of aircraft 1 at CPA
    y1atCPA = y1 + velocity1Y * timeToCPA  # calculates y coordinate of aircraft 1 at CPA
    z1atCPA = z1 + velocity1Z * timeToCPA  # calculates z coordinate of aircraft 1 at CPA

    x2atCPA = x2 + velocity2X * timeToCPA  # calculates x coordinate of aircraft 2 at CPA
    y2atCPA = y2 + velocity2Y * timeToCPA  # calculates y coordinate of aircraft 2 at CPA
    z2atCPA = z2 + velocity2Z * timeToCPA  # calculates z coordinate of aircraft 2 at CPA

   #https://en.wikipedia.org/wiki/Euclidean_distance
   # d(p,q) = sqrt((x2 - x1)² + (y2 - y1)² + (z2 - z1)²)
    distanceAtCPA = math.sqrt((x1atCPA - x2atCPA) ** 2 + (y1atCPA - y2atCPA) ** 2 + (z1atCPA - z2atCPA) ** 2)  # calculates distance between aircraft at CPA 
    
    lat1atCPA = y1atCPA / degreesToMeters  # converts y coordinate back to latitude
    lon1atCPA = x1atCPA / (degreesToMeters * math.cos(avgLAT)) # converts x coordinate back to longitude
    alt1atCPA = z1atCPA / feetToMeters  # converts z coordinate back to altitude in feet
    lat2atCPA = y2atCPA / degreesToMeters  # converts y coordinate back to latitude
    lon2atCPA = x2atCPA / (degreesToMeters * math.cos(avgLAT))  # converts x coordinate back to longitude
    alt2atCPA = z2atCPA / feetToMeters  # converts z coordinate back to altitude in feet

    
    
    return CPA(timeToCollision=timeToCPA, distanceAtCPA=distanceAtCPA / 1000,cpaPosition1=(lat1atCPA, lon1atCPA, alt1atCPA), cpaPosition2=(lat2atCPA, lon2atCPA, alt2atCPA))  # returns a CPA object with time to collision, distance to collision and positions of aircraft at CPA

    




        

class simAirspace:

    def __init__(self):
        self.aircraft: dict[str, Aircraft] = {}  # dictionary to store aircraft objects with callsign as key
        self.LOCK = Lock()  # lock to ensure thread safety when updating aircraft data
        self.startTime = time.time()  # records the start time of the simulation
        self.conflictCounter = 0

    def addAircraft(self, aircraft: Aircraft):
        with self.LOCK:
            self.aircraft[aircraft.callsign] = aircraft # adds aircraft to the dictionary
    
    def removeAircraft(self, aircraft: Aircraft):
        with self.LOCK:
            if aircraft.callsign in self.aircraft:
                del self.aircraft[aircraft.callsign]

    def updateAirspace(self, time):
        with self.LOCK:
            for aircraft in self.aircraft.values():
                aircraft.updateAircraftPosition(time)  # updates the position of each aircraft in the airspace
    def getAircraftData(self):
        with self.LOCK:
            return [aircraft.dataToJsonDictionary() for aircraft in self.aircraft.values()] # returns a list of aircraft data in JSON format
    
      # minimum separation distance in kilometers, set to 5 nautical miles
     # minimum altitude difference in feet, set to 1000 feet

    # priority queue implementation
    def DetectConflicts(self, minimumSeperationDistanceKM: float = nmToKM * 1,
                    minimumAltitudeDifferenceFT: float = 500, lookaheadTime: float = 5):  # looks 5 mins ahead for conflicts 

        conflictHeap = []  # list to store current conflicts
        aircraftList = list(self.aircraft.values())  # converts the dictionary of aircraft to a list 
        resolvedConflicts = []
    
    # use of 2 for loops means the function becomes O(N^2) in time complexity, n being the number of aircraft in the airspace
    # might need to be optimised if the number of aircraft increases 
        for i in range(len(aircraftList)): 
            for j in range(i + 1, len(aircraftList)):  # iterate through the aircraft list
                # compares each aircraft with every other aircraft to find conflicts
                aircraft1 = aircraftList[i] 
                aircraft2 = aircraftList[j]

                if aircraft1.flightStatus == "Arrived" or aircraft2.flightStatus == "Arrived":  # checks if either aircraft has arrived at its destination
                    continue  

                cpa = calculateCPA(aircraft1, aircraft2)  # calculates the closest point of approach (CPA) between the two aircraft

                if cpa is None:  # if CPA is None, the aircraft are not on a collision course
                    continue  # skip to the next pair of aircraft

                if cpa.timeToCollision <= 60 or cpa.distanceAtCPA < 1.0:  # 1 minute or 1km
                    print(f"conflict detected: {aircraft1.callsign} : {aircraft2.callsign}")
                    if self.resolveConflicts(aircraft1, aircraft2):
                        resolvedConflicts.append(f"{aircraft1.callsign} : {aircraft2.callsign}")
                        print(f"Rerouted {aircraft1.callsign}")
                        # for immediate conflicts add to a seperate list
                        self.conflictCounter += 1  
                        heapq.heappush(conflictHeap,(-1.0, self.conflictCounter, {  # -1.0 highest priority
                            "aircraft1": aircraft1.callsign,
                            "aircraft2": aircraft2.callsign,
                            "timeToCPA": cpa.timeToCollision,
                            "distanceAtCPA": cpa.distanceAtCPA,
                            "altitudeDifference": abs(cpa.cpaPosition1[2] - cpa.cpaPosition2[2]),
                            "riskScore": 1.0,  #  max risk
                            "status": "Resolved"
                        }
                    ))
                    else:
                        print(f"Failed to resolve: {aircraft1.callsign} : {aircraft2.callsign}")
                        self.conflictCounter += 1  
                        heapq.heappush(conflictHeap,(-1.0, self.conflictCounter, {
                            "aircraft1": aircraft1.callsign,
                            "aircraft2": aircraft2.callsign,
                            "timeToCPA": cpa.timeToCollision,
                            "distanceAtCPA": cpa.distanceAtCPA,
                            "altitudeDifference": abs(cpa.cpaPosition1[2] - cpa.cpaPosition2[2]),
                            "riskScore": 1.0,
                            "status": "Unresolved"
                        }))
                    continue  # skip to the next pair of aircraft

                if cpa.timeToCollision > lookaheadTime * 60:  # check if the time to collision is greater than the lookahead time in seconds
                    continue  
            
                horizontalViolation = cpa.distanceAtCPA < minimumSeperationDistanceKM  # checks if the distance at CPA is less than the minimum separation distance
                altitudeDifferenceAtCPA = abs(cpa.cpaPosition1[2] - cpa.cpaPosition2[2])  # calculates the altitude difference at CPA
                verticalViolation = altitudeDifferenceAtCPA < minimumAltitudeDifferenceFT  # checks if the altitude difference at CPA is less than the minimum altitude difference
            
            # checks if the distance and altitude difference are below the minimum standard for aeroplanes by ICAO standards
                if horizontalViolation and verticalViolation:
                # used to determine the place in the priority queue, the closer to 1 means the higher the risk of colliding
                    currDistance = aircraft1.position.distancefrom(aircraft2.position)
                    currAltitudeDifference = abs(aircraft1.alt - aircraft2.alt)  

                # # normalises the risk to a value between 0 and 1, 1 being the highest risk
                    # ill use exponential decay functions to normalise as my weighted formula just made everything 1.0 risk score
                    horizontalRisk = math.exp(-cpa.distanceAtCPA / minimumSeperationDistanceKM) 
                    verticalRisk = math.exp(-altitudeDifferenceAtCPA / minimumAltitudeDifferenceFT)
                    timeRisk = math.exp(-cpa.timeToCollision / (lookaheadTime * 60))

                # placeholders until the actual function is implemented
                    speedRisk = self.calculateSpeedRisk(aircraft1, aircraft2)

                # risk score ranging from 0 to 1, used to determine the place in the priority queue
                    riskScore = (0.4 * horizontalRisk + 0.4 * verticalRisk + 0.1 * timeRisk + 0.1 * speedRisk) 
                    self.conflictCounter += 1  
                #  -riskScore is used to implement a maxheap (finding the highest priority first) as python's heapq  is a minheap (finds the lowest priority) by default
                    if riskScore > 0.8: # high risk
                        print(f"High risk conflict detected: {aircraft1.callsign} : {aircraft2.callsign}")
                        if self.resolveConflicts(aircraft1, aircraft2):
                            resolvedConflicts.append(f"{aircraft1.callsign} : {aircraft2.callsign}")
                            print(f"rerouted {aircraft1.callsign}")
                            conflictStatus = "Resolved"
                        else:
                            print(f"reroute failed: {aircraft1.callsign} : {aircraft2.callsign}")
                            conflictStatus = "Unresolved"
                    else:
                        conflictStatus = "Monitoring"
                    
                    heapq.heappush(conflictHeap, (-riskScore, self.conflictCounter,   {
                        "aircraft1": aircraft1.callsign,  # callsign of aircraft 1
                        "aircraft2": aircraft2.callsign,  # callsign of aircraft 2
                        "distanceKM": round(currDistance, 2),
                        "altitudeDifferenceFT": round(currAltitudeDifference, 0),  # current altitude difference in feet
                        "timeToCollision": round(cpa.timeToCollision / 60, 2),  # time to collision in minutes
                        "distanceAtCPAKM": round(cpa.distanceAtCPA, 2),  # distance at CPA in kilometers
                        "altitudeDiffCpaFT": round(altitudeDifferenceAtCPA, 0),  # altitude difference at CPA in feet   
                        "riskScore": round(riskScore, 3),  # risk score ranging from 0 to 1
                        "status": conflictStatus,
                        "cpaPosition1": {
                            "lat": round(cpa.cpaPosition1[0], 6),
                            "lon": round(cpa.cpaPosition1[1], 6),
                            "alt": round(cpa.cpaPosition1[2], 0)
                        },
                        "cpaPosition2": {
                            "lat": round(cpa.cpaPosition2[0], 6),
                            "lon": round(cpa.cpaPosition2[1], 6),
                            "alt": round(cpa.cpaPosition2[2], 0)
                        }


                    }))
                
        conflict = []
        while conflictHeap:  # ensures the conflicts are returned in descending order of risk
            conflict.append(heapq.heappop(conflictHeap)[2])  # adds all current conflicts to the conflict list, [2] extracts the third element (conflict dictionary)
        if resolvedConflicts:
            print(f"{len(resolvedConflicts)} resolved")
            for conflicts in resolvedConflicts:
                print(conflicts)
        return conflict
                
                
    
    def resolveConflicts(self, aircraft1: Aircraft, aircraft2: Aircraft):
        resolver = conflictResolver(self)
        return resolver.resolveConflict(aircraft1, aircraft2)

     
                
    
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
    
    def removeArrivedAircraft(self): # use when aircraft reaches their destiantion
        with self.LOCK:
            removeList = [callsign for callsign, aircraft in self.aircraft.items() if aircraft.hasArrived]
            for callsign in removeList:
                print(f"Removing {callsign} from airspace") # for test/debug can remove this later
                del self.aircraft[callsign]
            
            if removeList:
                print(f"Removed {len(removeList)} aircraft from airspace, {len(self.aircraft)} remaining aircraft on the map")


@dataclass
class aStarNode: # node for a star
    position: Position
    altitude: float
    gCost: float = float('inf') # cost from start to current node
    hCost: float = float('inf') # heuristic cost from current node to goal
    fCost: float = field(init=False) # total cost, f(n) = g(n) + h(n), field(init=False), field(init=False) means fCost is not included in the constructor and is calculated automatically
    parent: Optional['aStarNode'] = None  # parent node in the path, used to reconstruct the path after the search is complete, previous node in the path

    def __post_init__(self):
        self.fCost = self.gCost + self.hCost
    # runs after the constructor is finished, we cant calculate the fCost during init 
    def __lt__(self, other: 'aStarNode'): # defines what < (less than) means for Nodes
        if self.fCost == other.fCost:
            return self.hCost < other.hCost
        return self.fCost < other.fCost
        
    def __eq__(self, other):  # defines what == (equal to) means for Nodes
        if not isinstance(other, aStarNode):
            return False
        return (abs(self.position.lat - other.position.lat) < 1e-6 and
        abs(self.position.lon - other.position.lon) < 1e-6 and
        abs(self.altitude - other.altitude) < 500) 

    def __hash__(self): # to avoid unhashable type errors
        return hash((round(self.position.lat, 4),
        round(self.position.lon, 4), 
        round(self.altitude, -2)))

class conflictResolutionStrategy(Enum): # used for different strategies when rerouting 
    altitudeChange = "altitudeChange"
    horizontalReroute = "horizontalReroute"
    speedAdjustment = "speedAdjustment"
    combined = "combined"

@dataclass
class conflictResolution: # container for resolution info
    aircraftID = str
    strategy: conflictResolutionStrategy
    newAltitude: float
    newWaypoints: Optional[List['Position']] = None # can either be a list of positions or none
    speedFactor: float = 1.0
    estimatedDelay: float = 0.0
    fuelCost: float = 0.0
    
class aStarPathfinding: # nodes - 3D pos (lat,lon,alt)  edges - possible movements  goal - destination airport
    # class to reroute the aircraft once a collision is detected, formula is f(n) = g(n) + h(n), g(n) = kilometers travelled + fuel for altitude change, h(n) = straight line distance + altitude change, f(n) being total cost
    # 1. generate neighbours around aircraft 1 2. for each neighbour, predict where aircraft 2 will be in 60 seconds 3. only store safe neighbours 4.continue search from safe positions
    def __init__(self, airspace: 'simAirspace'):
        self.airspace = airspace
        self.gridResDegrees = 0.05  # resolution of the grid, controls search space, good for a world map
        self.altitudeLevel = [30000, 32000, 34000, 36000, 38000, 40000, 42000, 44000] # avg flight levels
        self.safetyBufferKM = 6.0 # safety buffer for other aircraft
        self.cache = {}
        self.maxNumberOfIterations = 2000

    def Heuristic(self, node: aStarNode, goal: aStarNode): # calculates h(n)
        horDistance = node.position.distancefrom(goal.position)  # calculates horizontal distance between current node and goal node
        altDifference = abs(node.altitude - goal.altitude) * feetToMeters / 1000 # calculates altitude difference between current node and goal node, in KM

        # penalty for straying away from route
        directBearing = node.position.bearingTo(goal.position)
        return horDistance + altDifference * 1.5 # returns the heuristic cost, h(n) = straight line distance + altitude change, in KM
    
    def findClosestAltitudeIndex(self, altitude: float):
        return min(range(len(self.altitudeLevel)), key=lambda i: abs(self.altitudeLevel[i] - altitude))  # finds the index of the closest altitude level to the current node's altitude

    def getNeighbours(self, node: aStarNode, goalPosition: Position): # generate neighbour nodes for a current node
        neighbours = []
        distanceToGoal = node.position.distancefrom(goalPosition)

        if distanceToGoal > 500: # far from goal
            stepMultiplier = 2
        elif distanceToGoal > 100: # medium distance
            stepMultiplier = 1
        else:
            stepMultiplier = 0.5 # closer to goal
        directions = [ # possible horizontal movement (8 directions)
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1),           (0, 1),
            (1, -1),  (1, 0),  (1, 1)
        ]

        bearingToGoal = node.position.bearingTo(goalPosition)
        goalDirection = (math.sin(math.radians(bearingToGoal)), math.cos(math.radians(bearingToGoal))) # becomes a vector
        directions.append(goalDirection)
        for dx, dy in directions: # dx = sin(x), dy = cos(x)
            stepSize = self.gridResDegrees * stepMultiplier
            newLat = node.position.lat + (dx * stepSize)
            newLon = node.position.lon + (dy * stepSize)
            newPos = Position(newLat, newLon)  
            neighbour = aStarNode(newPos, node.altitude)  # creates a new neighbour node with the new position and same altitude as the current node
            if self.isSafePosition(neighbour, goalPosition):
                neighbours.append(neighbour)  # adds the neighbour node to the list if it is a safe position

        currentAltitudeIndex = self.findClosestAltitudeIndex(node.altitude)  # finds the index of the closest altitude level to the current node's altitude

        for altitudeChange in [-1,1,-2,2]: # climbing or descending 
            newAltitudeIndex = currentAltitudeIndex + altitudeChange  # calculates the new altitude index by adding or subtracting 1 from the current altitude index
            if 0 <= newAltitudeIndex < len(self.altitudeLevel):
                newAlt = self.altitudeLevel[newAltitudeIndex]  # gets the new altitude from the altitude level list
                neighbour = aStarNode(node.position, newAlt)  # creates a new neighbour node with the node position and new altitude
                if self.isSafePosition(neighbour, goalPosition):  # checks if the new neighbour node is a safe position
                        neighbours.append(neighbour)  

        return neighbours  # returns the list of neighbour nodes
        
    def isSafePosition(self, node: aStarNode, goalPosition: Position): # checks if a node is a safe position
        cacheKey = (round(node.position.lat, 3),round(node.position.lon, 3), round(node.altitude, -2)) # check for frequently checked pos
        if cacheKey in self.cache:
            return self.cache[cacheKey]
        
        isSafe = True
        predictedTime = 90 # 90 seconds lookahead
 
        for aircraft in self.airspace.aircraft.values():
            if aircraft.flightStatus == "Arrived":
                continue # skip if aircraft has arrived at its destination

            predictedPosition = self.predictAircraftPosition(aircraft, predictedTime)
            predictedAltitude = aircraft.alt + (aircraft.verticalspeed * (predictedTime / 60))

            horDistance = node.position.distancefrom(predictedPosition)  
            altDifference = abs(node.altitude - predictedAltitude) 

            if(horDistance < self.safetyBufferKM and altDifference < 2000): # if the horizontal distance is less than the safety buffer and altitude difference is less than 2000 feet, the position is not safe
                isSafe = False
                break
        self.cache[cacheKey] = isSafe
        return isSafe

    def predictAircraftPosition(self, aircraft: Aircraft, predictedTime: float):
        speedKMs = (aircraft.tas * nmToKM) / 3600  # converts speed from knots to kilometers per second
        headingRadians = aircraft.hdg * degreeToRadians 

        distance = speedKMs * predictedTime  # distance = speed x time
        angularDistance = distance / earthRadiusKM 

        lat1 = aircraft.position.lat * degreeToRadians  
        lon1 = aircraft.position.lon * degreeToRadians  

        # haversine formula
        predictedLat = math.asin(math.sin(lat1) * math.cos(angularDistance) + math.cos(lat1) * math.sin(angularDistance) * math.cos(headingRadians))
        predictedLon = lon1 + math.atan2(math.sin(headingRadians) * math.sin(angularDistance) * math.cos(lat1), math.cos(angularDistance) - math.sin(lat1) * math.sin(predictedLat))
        
        return Position(predictedLon * radianToDegree, predictedLon * radianToDegree)

    def getMovementCost(self, fNode: aStarNode, tNode: aStarNode): # calculates cost of moving from one node to another
        horDistance = fNode.position.distancefrom(tNode.position)
        altDifference = abs(tNode.altitude - fNode.altitude) * feetToMeters / 1000

        cost = horDistance # base cost = horizontal distance 
        cost += altDifference * 3.0 # added penalty for altitude change and fuel consumption 
        
        # penalty for direction change
        if fNode.parent:
            previousBearing = fNode.parent.position.bearingTo(fNode.position)
            currentBearing = fNode.position.bearingTo(tNode.position)
            bearingDifference = abs(previousBearing - currentBearing)
            if bearingDifference > 180:
                bearingDifference = 360 - bearingDifference
            cost += bearingDifference / 180 # between 0-1


        return cost

    def findOptimalPath(self, startingAircraft: Aircraft, goalPosition: Position, maxNumberOfIterations: int = 1000): 
        if maxNumberOfIterations is None:
            maxNumberOfIterations = self.maxNumberOfIterations

        strategies = [ # cycle through looser constraints
            {'gridResolution': 0.05, 'safetyBuffer': 6.0},
            {'gridResolution': 0.08, 'safetyBuffer': 4.0}, 
            {'gridResolution': 0.1, 'safetyBuffer': 3.0}
        ]

        for strategy in strategies:
            self.gridResDegrees = strategy['gridResolution']
            self.safetyBufferKM = strategy['safetyBuffer']

            path = self.aStarSearch(startingAircraft, goalPosition, maxNumberOfIterations)
            if path: 
                return path
        return None
        
    
    def aStarSearch(self, aircraft: Aircraft, goalPosition: Position, maxNumberOfIterations: int):
        sNode = aStarNode(aircraft.position, aircraft.alt)
        sNode.gCost = 0 # g(n)
        goalAltitude = self.findSafeAltitudeNearGoal(goalPosition, aircraft.alt)
        goalNode = aStarNode(goalPosition, goalAltitude) # assuming the same altitude
        sNode.hCost = self.Heuristic(sNode, goalNode) # h(n)

        openSet = [sNode] # nodes the program has found but not processed yet
        heapq.heapify(openSet)
        closedSet = set(); # nodes that are already processed, not revisited

        bestNode = sNode
        bestDistance = sNode.hCost
        iterationCounter = 0

        while openSet and iterationCounter < maxNumberOfIterations: # while there still is nodes is to be processed and not more than the failsafe max iteration count
            iterationCounter += 1
            currNode = heapq.heappop(openSet) # get the node with the lowest f(n) cost, which is the shortest and fastest path
            distanceToGoal = currNode.position.distancefrom(goalPosition)
            if distanceToGoal < 5.0: # within 5km
                print(f"Path found in {iterationCounter} iterations")
                return self.reconstructPath(currNode)

            if distanceToGoal < bestDistance:
                bestNode = currNode
                bestDistance = distanceToGoal
            
            nodeTuple = self.nodeToTuple(currNode)
            if nodeTuple in closedSet:
                continue

            closedSet.add(nodeTuple)

            neighbours = self.getNeighbours(currNode, goalPosition)
            for neighbour in neighbours: # gets all neighbour positions 
                neighbourTuple = self.nodeToTuple(neighbour)
                if neighbourTuple in closedSet:
                    continue # avoids already visited nodes

                predictedGCost = currNode.gCost + self.getMovementCost(currNode, neighbour)
                if predictedGCost < neighbour.gCost: # if there is a cheaper route
                    neighbour.parent = currNode
                    neighbour.gCost = predictedGCost
                    neighbour.hCost = self.Heuristic(neighbour, goalNode)
                    neighbour.fCost = neighbour.gCost + neighbour.hCost

                    if neighbour not in openSet:
                        heapq.heappush(openSet, neighbour) # if neighbour isnt to be discovered yet push it into the heapq
        if bestNode != sNode and bestDistance < sNode.hCost * 0.7:
            return self.reconstructPath(bestNode) 
        print(f"A* pathfinding failed at {iterationCounter} iterations") # this will occur if either the max number of iterations is reached or no path exists
        return None
    
    def nodeToTuple(self, node: aStarNode):
        return (
            round(node.position.lat, 4),
            round(node.position.lon, 4),
            round(node.altitude, -2)
        )
    def reconstructPath(self, goalNode: aStarNode):
        path = []
        curr = goalNode

        while curr is not None:
            path.append(curr.position)
            curr = curr.parent
        path.reverse()
        return path

    def findSafeAltitudeNearGoal(self, goalPosition: Position, currentAltitude: float):
        tNode = aStarNode(goalPosition, currentAltitude) # temp node to test current altitude
        if self.isSafePosition(tNode, goalPosition):
            return currentAltitude

        currIndex = self.findClosestAltitudeIndex(currentAltitude)
        for offset in [0, 1, -1, 2, -2, 3, -3]: # checks altitudes near the current one
            newIndex = currIndex + offset
            if 0 <= newIndex < len(self.altitudeLevel):
                tAltitude = self.altitudeLevel[newIndex]
                tNode = aStarNode(goalPosition, tAltitude)
                if self.isSafePosition(tNode, goalPosition):
                    return tAltitude

        return currentAltitude # if no other altitude is safe



class conflictResolver:
    def __init__(self, airspace: 'simAirspace'):
        self.airspace = airspace
        self.pathfinder = aStarPathfinding(airspace)
        self.resHistory = {}

    def resolveConflict(self, aircraft1: Aircraft, aircraft2: Aircraft):
        conflictKey = f"{aircraft1.callsign}:{aircraft2.callsign}"

        if conflictKey in self.resHistory:
            lastAttempt = self.resHistory[conflictKey]
            if time.time() - lastAttempt < 60: # wait a min before retrying
                return False
        
        self.resHistory[conflictKey] = time.time()

        strategies = [self.tryAltitudeSeperation, self.tryHorizontalReroute, self.trySpeedAdjustment, self.tryCombinedResolution]

        for strategy in strategies:
            if strategy(aircraft1, aircraft2):
                return True
        
        return False
    
    def tryAltitudeSeperation(self, aircraft1: Aircraft, aircraft2: Aircraft): # try to avoid conflicts throug hchanging the altitude of an aircraft
        altitudeLevel = [28000, 30000, 32000, 34000 ,36000, 38000, 40000, 42000 ,44000]

        for altitude in altitudeLevel:
            if abs(altitude - aircraft2.alt) >= 2000: # 2000 feet seperation
                testPosition = Position(aircraft1.position.lat, aircraft1.position.lon)
                if self.isSafeAltitude(testPosition, altitude, aircraft1):
                    aircraft1.alt = altitude
                    aircraft1.targetHeading = aircraft1.position.bearingTo(aircraft1.flightPath.getCurWaypoint().position)
                    print(f"Changed {aircraft1.callsign} altitude into {altitude}")
                    return True
                
        return False
    
    def tryHorizontalReroute(self, aircraft1: Aircraft, aircraft2: Aircraft ): # try to avoid collision through horizontalReroute
        arrivalData = self.getAirportData(aircraft1.arrivalICAO)

        if not arrivalData or 'lat' not in arrivalData or 'lon' not in arrivalData:
            return False
        goalPosition = Position(arrivalData['lat'], arrivalData['lon'])
        newPath = self.pathfinder.findOptimalPath(aircraft1, goalPosition)

        if newPath and len(newPath) > 1:
            aircraft1.flightPath.waypoints = [Waypoint(pos, f"Waypoint {i}") for i, pos in enumerate(newPath)]
            aircraft1.flightPath.currentWaypointIndex = 0
            print(f"Rerouted {aircraft1.callsign} with {len(newPath)} waypoints")
            return True
        
        return False
    
    def trySpeedAdjustment(self, aircraft1: Aircraft, aircraft2: Aircraft): # seeing if adjusting the speed of an aircraft would stop collision
        cpa = calculateCPA(aircraft1, aircraft2)
        if not cpa or cpa.timeToCollision > 300: # 300 means 5 minutes
            return False
        
        originalSpeed = aircraft1.tas
        aircraft1.tas *= 0.9 # reduce aircraft speed by ten percent

        newCPA = self.calculateCPA(aircraft1, aircraft2)
        if newCPA and newCPA.distanceAtCPA > 5.0: # at a safe distance
            print(f"Reduced {aircraft1.callsign} speed to {aircraft1.tas:.0f} knots")
            return True
        else:
            aircraft1.tas = originalSpeed
            return False
        
    def tryCombinedResolution(self, aircraft1: Aircraft, aircraft2: Aircraft): # try combined alt and route change
        if self.tryAltitudeSeperation(aircraft1, aircraft2):
            aircraft1.targetHeading = (aircraft1.targetHeading + 15) % 360
            return True
        return False
    
    def isSafeAltitude(self, position: Position, altitude: float, excludeAircraft: Aircraft): # check if the altitude is safe at a given pos
        for aircraft in self.airspace.aircraft.values():
            if aircraft == excludeAircraft or aircraft.flightStatus == 'Arrived':
                continue

            distance = position.distancefrom(aircraft.position)
            altitudeDifference = abs(altitude - aircraft.alt)
            if distance < 10 and altitudeDifference < 1500: # too close
                return False
        
        return True
    
    def getAirportData(self, icao: str): # same thing as Overpass 
        with Lock():
            cacheKey = f"{icao} airport"
            if cacheKey in airportCache:
                cacheData, timestamp = airportCache[cacheKey]
                if time.time() - timestamp < 3600:
                    return cacheData
            airportData = overpassAirportAPI(icao)
            if airportData:
                airportCache[cacheKey] = (airportData, time.time())
                return airportData
    
        return None
    
    
    def calculateCPA(aircraft1: Aircraft, aircraft2: Aircraft):
        cpa = calculateCPA(aircraft1, aircraft2)
        return cpa









        

def generateRandomAircraft(callsign = None):
    
    airportICAOS = [ # splited into continents with OSM supported icao codes, havent fully tested them yet
        # europe
        "EGLL", "EGKK", "LFPG", "LFPO", "LIRF",
         "LTFM", "EBBR",  "ESSA", "ENGM", "EFHK", "BIKF",

        # north America
        "KJFK", "KLAX", "KORD", "KATL",  "KSEA", "CYYZ", "CYVR",
          "KPHL", "KIAD",  "KDEN", "KSLC",
        "KFLL",
    
        # south America
        "SBGR", "SAEZ", "SPJC", "SKBO", "TJSJ", "MDPC", "MKJP",
    
        # asia
        "OMDB", "RJTT",  "WSSS", "ZBAA",  "OTHH", "VABB", 
        "ZSPD",  "RPVM", "WMKK", "VOCI",  "VOBL",
    
        # oceania
        "YSSY", 
    
        # middle East
         "OERK",  "OTHH",
    
        # africa
        "FAOR", "DNMM", "GMMN"
    ]
    
    aircraftTypes = [
        "B744", "B777", "A380", "B737", "A320", "A330", "B787", "A350"
    ]
    airlinePrefixes = [ "BAW", "UAL", "AAL", "DLH", "AFR", "KLM", "EZY", "RYR", "SWA", "JBU"] 

    departureICAO = random.choice(airportICAOS)  # randomly selects a departure airport from the list
    arrivalICAO = random.choice([icao for icao in airportICAOS if icao != departureICAO ])  # randomly selects an arrival airport from the list, makes sure arrival airport cannot be the same as departure airport
    aircrafttype = random.choice(aircraftTypes)  # randomly selects an aircraft type from the list

    if callsign is None:
        airline = random.choice(airlinePrefixes)  
        number = random.randint(100,999)
        callsign = f"{airline}{number}" # assigns a random callsign

    def getAirportPos(icao):
        if icao in airportCache:
            airportData = airportCache[icao]  # retrieves airport data from the cache
            return Position(airportData['lat'], airportData['lon'])  # returns the position of the airport with lat and long
        
        cacheKey = f"{icao} airport"
        if cacheKey in airportCache:
            airportData, timestamp = airportCache[cacheKey]
            if time.time() - timestamp < 3600:
                return Position(airportData['lat'], airportData['lon'])
            
        airportData = overpassAirportAPI(icao)  # fetches airport data from the overpass API
        if airportData and airportData.get('lat') and airportData.get('lon'):  # checks if the airport data is valid
            airportCache[cacheKey] = (airportData, time.time())  # adds the airport data to the cache
            return Position(airportData['lat'], airportData['lon']) # returns the position of the airport with lat and long
        
        print(f"Error fetching data for the airport: {icao}")  # prints an error message if the airport data is not valid
        return Position(51.4775, 0.4614) # default position is set to heathrow

        
    departurePos = getAirportPos(departureICAO)  # gets the position of the departure airport
    arrivalPos = getAirportPos(arrivalICAO)  # gets the position of the arrival airport
    heading = departurePos.bearingTo(arrivalPos) # calculates the bearing from the departure airport to the arrival airport
    lat = departurePos.lat 
    lon = departurePos.lon 
    alt = random.uniform(31000, 42000)
    speed = random.uniform(450, 550)  # random speed between 450 and 550 knots
    verticalspeed = random.uniform(-200, 200)  # random vertical speed between -200 and 200 feet per minute

    aircraft = Aircraft(
        callsign=callsign,
        actype=aircrafttype,
        alt=alt,
        hdg=heading,
        position = Position(lat,lon),
        speed=speed,
        verticalspeed= verticalspeed,
        departureICAO=departureICAO,
        arrivalICAO=arrivalICAO

    )
    aircraft.setFlightPath(departurePos, arrivalPos)  
    return aircraft

def initialiseAirspace(numAircraft = 10):
    airspace = simAirspace()  # creates an instance of the simAirspace class to manage aircraft data and conflicts
    print(f"Creating {numAircraft} random aircraft for the simulation")

    for i in range(numAircraft):
        try:
            aircraft = generateRandomAircraft()
            airspace.addAircraft(aircraft)  # adds the generated aircraft to the airspace
            print(f"Aircraft {aircraft.callsign} added to the simulation")  # prints when an aircraft is added to the simulation
        except Exception as e:
            print(f"Error creating aircraft: {str(e)}") 
    return airspace


airspace = initialiseAirspace(100)  # this controls how many aircraft are created


@application.route('/aircraft') # defines route to retrieve live aircraft data at localhost/aircraft
@cache.cached(timeout=0.5)  # caches the response for 0.5 seconds to reduce server load
def getAircraft(): # executes when /aircraft is accessed
   try:
       airspace.updateAirspace(5) # updates the airspace with a time step of 5 second
       airspace.removeArrivedAircraft() # removes aircraft that have arrived at their destination
       return jsonify(airspace.getAircraftData())  # returns the aircraft data in JSON format
   except Exception as e:
       traceback.print_exc()
       return jsonify({"error": str(e)}), 500
   
@application.route('/conflicts') # defines route to retrieve live aircraft data at localhost/aircraft
def getConflicts():
    try:
        airspace.updateAirspace(1) # for faster checks
        conflicts = airspace.DetectConflicts(
                minimumSeperationDistanceKM=nmToKM * 5,  # 5 NM 
                minimumAltitudeDifferenceFT=1000,      # 1000 ft 
                lookaheadTime=15.0                # 15 minutes lookahead 
            )
        print("current conflicts: ", conflicts)  # prints the current conflicts to the console
        return jsonify(conflicts)  # returns the conflicts in JSON format
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@application.route('/addAircraft', methods=['POST']) # defines route to add an aircraft when clicking the button via a POST request
def addRandomAircraft():
    try:
        ac = generateRandomAircraft()
        airspace.addAircraft(ac)
        print(f"Added aircraft {ac.callsign}")
        
        return jsonify({
            "success": True, 
            "aircraft": {
                "callsign": ac.callsign,
                "departureICAO": ac.departureICAO,
                "arrivalICAO": ac.arrivalICAO
            }
        })
    except Exception as e:
        print(f"error occured when adding the aircraft: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
       
if __name__ == '__main__':
    print("Starting Simulation..")
    
    application.run(debug=False, host='0.0.0.0', port=port)



