// init map
console.log("main.js loaded");

const checkEnv = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'; // checks if we are in development or prod
const apiBaseURL = checkEnv ? 'http://localhost:5000' : ''; // sets the api url based on the environment

function validateInput(){
    const input = document.getElementById('aircraftCount')
    const error = document.getElementById('error');
    const value = parseInt(input.value);

    if(isNaN(value) || value < 1 || value > 200){
        error.style.display = 'block';
        return false;
    }
    error.style.display = 'none';
    return true;
}
async function initialiseAirspace(){
    if(!validateInput()) return;

    const input = document.getElementById('aircraftCount')
    const aircraftCount = parseInt(input.value);
    const button = document.querySelector('.init-button')
    const container = document.getElementById('init-airspace-container')
    const infoMessage = document.getElementById('infoMessage');

    button.disabled = true; // disables the button to prevent multiple clicks
    button.textContent="Loading...."
    infoMessage.style.display = 'block';
    try{
        const response = await fetch(`${apiBaseURL}/initAirspace/${aircraftCount}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        });

        if(!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

        const res = await response.json();

        if(res.success){
            console.log(`Fully initialised airspace with ${aircraftCount} aircraft.`);
            container.style.display = 'none'; // hides the initialisation container
            infoMessage.style.display = 'none'; // hides the info message
            startUpdate(); // starts updating the aircraft data after initialising the airspace
        } else {
            console.error("Failed to initialise airspace:", result.error);
        }
    } catch(error){
        console.error("Error initialising airspace:", error);
        button.disabled = false;
        button.textContent = "Start Simulation"
        loadingMessage.style.display = 'none';
    }
}
var map = L.map('map', {
    minZoom: 2,
    worldCopyJump: true, // allows markers to stay on a single map (e.g if a marker flies to the west of america it will show near the west of the earth instead of moving to another map)
    maxBounds: [ // defines the rectangle that you cant scroll out of
        [-90, -Infinity], // north corner
        [90, Infinity]    // south corner
    ],
    maxBoundsViscosity: 1.0 // makes the map not bounce back when scrolling out of view
}).setView([20, 0], 2);

// Create tile layer with openstreetmap 
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    minZoom: 2, 
    continuousWorld: true,
    attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
}).addTo(map);

var AeroplaneIcon = L.icon({
    iconUrl: '/static/ICONS/airplane.svg', // sets image for the aeroplane
    iconSize: [30, 30], // size of the icon
    iconAnchor: [15, 15] // centers the icon on long, lat coordinates.
})

let conflictMarkers = {}; // dictionary used to store active conflict markers
const aircraftMarkers = {}; // dictionary used to store active aircraft markers
const defaultIconSize = [12,12]; // default icon size for the aircraft markers, used to scale the icon size based on the zoom level
const DefaultZoom = 7;
const minimumScale = 1.3; // minimum scale factor for the icon size
const maximumScale = 1.6; // maximum scale factor for the icon size
let currentZoom = map.getZoom(); // get the current zoom level
const airportMarkers = {};
const flightPathLines = {}; // dictionary used to store flight path markers
const waypointMarkers   = {}; // dictionary used to store waypoint markers
let showFlightPath = true; // boolean to toggle flight path visibility

function createFlightLines(aircraft){
    const aircraftID = aircraft.id; // gets the aircraft id
    if (flightPathLines[aircraftID]) { // checks if the flight path line already exists
        map.removeLayer(flightPathLines[aircraftID]); // removes the existing flight path line from the map
    }

    if (waypointMarkers[aircraftID]){ // checks if the waypoint markers exist for the aircraft
        waypointMarkers[aircraftID].forEach(marker => map.removeLayer(marker)); // removes any existing waypoint markers from the map
        }

    if (!showFlightPath || !aircraft.waypoints || aircraft.waypoints.length < 2) { // only create flight lines if showFlightPath is true and there are at least 2 waypoints
        return; // exits the function if flight path is not shown or there are not enough waypoints
    }
    
    const pathPoints = []; // array to store the path points for the flight path line

    pathPoints.push([aircraft.lat, aircraft.lon]); // adds the current position of the aircraft to the path points

    for(let i = aircraft.currentWaypointIndex || 0; i < aircraft.waypoints.length; i++)
        {
            const waypoint = aircraft.waypoints[i]; // gets the waypoint
            pathPoints.push([waypoint.lat, waypoint.lon]) ; // adds the waypoint coordinates to the path points
        }

    if(pathPoints.length > 1)
    {
        const pathLine = L.polyline(pathPoints, {
            color: getFlightColourPath(aircraft),
            weight: 2, 
            opacity: 0.6,
            dashArray: '5, 5' // makes the line dashed
        }).addTo(map); 
    
        pathLine.bindPopup(`Flight Path for ${aircraft.id}<br>From: ${aircraft.departureICAO}<br>To: ${aircraft.arrivalICAO}`); // binds a popup to the flight path line with the aircraft id
        flightPathLines[aircraftID] = pathLine; // adds the flight path line to the flight path lines dictionary
    }

    /*const waypointMarkerArray = []; // to create waypoint markers 
    for(let i = aircraft.currentWaypointIndex || 0; i < aircraft.waypoints.length; i++){
        const waypoint = aircraft.waypoints[i]; // gets the waypoint
        const currentTarget = i === (aircraft.currentWaypointIndex || 0)
        const waypointMarker = L.circleMarker([waypoint.lat, waypoint.lon], {
            radius: currentTarget ? 2 : 3, // makes the current target waypoint larger, ? used as a boolean
            fillColor: currentTarget ? '' : 'blue', 
            color: currentTarget? 'red' : 'blue', 
            weight: 1,
            opacity: 0.5,
            fillOpacity: 0.5
        }).addTo(map);

        waypointMarker.bindPopup(`Waypoint: ${waypoint.name}<br>Aircraft: ${aircraft.id}`) 
    }

    waypointMarkers[aircraftID] = waypointMarkerArray; // adds the waypoint markers to the waypoint markers dictionary */
}
function getFlightColourPath(aircraft){ // changes colour depending on altitude https://support.fr24.com/support/solutions/articles/3000115027-why-does-the-aircraft-s-trail-change-colour- for reference
    if(aircraft.altitude < 100){
        return 'white'
    }
    else if(aircraft.altitude >= 100 && aircraft.altitude < 400)
    {
        return 'yellow'
    }
    else if(aircraft.altitude >= 400 && aircraft.altitude < 2000){
        return 'green'
    }
    else if(aircraft.altitude >= 2000 && aircraft.altitude < 4000){
        return 'cyan'
    }
    else if(aircraft.altitude >= 4000 && aircraft.altitude < 6000){
        return 'blue'
    }
    else if(aircraft.altitude >= 6000 && aircraft.altitude < 8000){
        return 'darkblue'
    }
    else if(aircraft.altitude >= 8000 && aircraft.altitude < 10500){
        return 'purple'
    }
    else if(aircraft.altitude >= 10500 && aircraft.altitude < 12500){
        return '#FF69B4' // used hotpink as pink is too hard to see
    }
    else if(aircraft.altitude >= 12500){
        return 'green'
    }
}

function clearFlightLines(aircraftID){
    if(flightPathLines[aircraftID]){
        map.removeLayer(flightPathLines[aircraftID]); // removes the flight path line from the map
        delete flightPathLines[aircraftID]; // deletes the flight path line from the flight path lines dictionary
    }

    if(waypointMarkers[aircraftID]){
        waypointMarkers[aircraftID].forEach(marker => map.removeLayer(marker)); // removes the waypoint markers from the map
        delete waypointMarkers[aircraftID]; // deletes the waypoint markers from the waypoint markers dictionary
    }
}

function toggleFlightPath(){
    showFlightPath = !showFlightPath; // toggles the flight path visibility

    if(!showFlightPath){ // if flight path is not shown, clear the flight path lines and waypoint markers
        Object.keys(flightPathLines).forEach(aircraftID => clearFlightLines(aircraftID)); // clears all flight path lines
    }
    else{

    }
}
    
    



async function fetchAirport(icao){
    try{
        const response = await fetch(`${apiBaseURL}/airport/${icao}`); // fetches the airport data from the flask server
        if(!response.ok) throw new Error(`HTTP error! status: ${response.status}`); // throws an error if the response is not ok
        const data = await response.json(); // returns the response as json
        return data;
    } catch(error)
    {
        console.error("Error occured fetching airport", error); // logs the error to the console
        return null; // returns null if there is an error
    }
        
}

async function createAirportMarker(icao){
    if(airportMarkers[icao])
    {
        return airportMarkers[icao];
    }
    const airport = await fetchAirport(icao); // fetches the airport data from the flask server
    if(airport && airport.lat && airport.lon){ // checks if the airport data is valid
        const marker = L.marker([airport.lat, airport.lon], {
            icon: L.divIcon({
                className: 'airport',
                html: `${airport.icao}`,
                iconSize: [60, 20]
            })
        });
        marker.bindPopup(`ICAO: ${airport.icao}<br>Name: ${airport.name}`); // binds a popup to the marker with the airport information<br>Altitude:
        marker.addTo(map);
        airportMarkers[icao] = marker;  
        return marker; 
    }
    return null; // Return null if airport data is invalid
}

    

function calculateRotation(heading){
    return heading;// converts the heading to a true heading, as Leaflet uses clockwise rotation
}

function ScaleIcon(zoom){
    const scaleFactor = Math.min(maximumScale, Math.max(minimumScale, Math.pow(1.2,DefaultZoom - zoom))); // calculates the scale factor based on the zoom level, ensuring it stays within the minimum and maximum scale limits
    // scale factor is calculated by taking the difference between the default zoom level and the current zoom level, and raising 1.2 to that power, then clamping it between the minimum and maximum scale limits
    return L.icon({        
        iconUrl: '/static/ICONS/airplane.svg',
        iconSize: defaultIconSize.map(size => size * scaleFactor), // scales the icon size based on the zoom level
        iconAnchor: [defaultIconSize[0]/2 * scaleFactor, defaultIconSize[1]/2 * scaleFactor] // centers the icon on long, lat coordinates based on the scaled size
    })
}

map.on('zoomend', () => { // zoomend event is triggered when the zoom level animation is finished 
    currentZoom = map.getZoom(); // get the current zoom level
    Object.values(aircraftMarkers).forEach(marker => { // object.values converts our aircraftMarkers dictionary into an array of markers
        marker.setIcon(ScaleIcon(currentZoom)); // update the icon size based on the zoom level and refreshes the icon of the marker
        const rotation = marker.options.rotationAngle || 0;
        marker.setRotationAngle(rotation); // ensures the rotation angle is preserved when the icon size is updated
    });
});

// async means the function will return a promise
// fetchAircraftData fetches the aircraft data from the flask server
async function fetchAircraftData(){
    try{
        
        const response = await fetch(`${apiBaseURL}/aircraft`); // fetches the aircraft data from the flask server
        if(!response.ok) throw new Error(`HTTP error! status: ${response.status}`); // throws an error if the response is not ok
        const data = await response.json(); // returns the response as json
        console.log("aircraft data from server:", data);
        if(!Array.isArray(data)) throw new Error("Expected array but got " + JSON.stringify(data))
                    
        return data.map(aircraft => ({ // maps the data to the required format
            id: aircraft.callsign,
            lat: aircraft.lat,
            lon: aircraft.lon,
            heading: aircraft.heading,
            altitude: aircraft.altitude,
            speed: aircraft.speed,
            departureICAO: aircraft.departureICAO,
            arrivalICAO: aircraft.arrivalICAO,
            flightStatus: aircraft.flightStatus,
            waypoints: aircraft.waypoints || [], // ensures waypoints is an array, defaulting to empty if not present
            currentWaypointIndex: aircraft.currentWaypointIndex || 0 // ensures currentWaypointIndex is defined, defaulting to 0 if not present
        }));         
    } catch(error){
        console.error("Error fetching aircraft data:", error); // logs the error to the console
        return [];
    }
}

function calculateMidpoint(latlng1, latlng2) {
    return L.latLng(
        // x2 + x1 / 2, y2 + y1 / 2
        (latlng1.lat + latlng2.lat) / 2,
        (latlng1.lng + latlng2.lng) / 2
    )
}

async function displayConflicts(){
    try{
        const response = await fetch(`${apiBaseURL}/conflicts`); // fetches the conflicts data from the flask server
        if(!response.ok) throw new Error(`HTTP error! status: ${response.status}`); 
        const conflicts = await response.json(); 
        console.log("conflicts data from flask:", conflicts); 


        Object.values(conflictMarkers).forEach(marker => map.removeLayer(marker)); // clear previous conflict markers
        conflictMarkers = {}; // clears the conflict markers dictionary

        conflicts.forEach(conflict => {
            const aircraft1 = aircraftMarkers[conflict.aircraft1];
            const aircraft2 = aircraftMarkers[conflict.aircraft2];
            if(aircraft1 && aircraft2){
                const midpoint = calculateMidpoint(aircraft1.getLatLng(),  aircraft2.getLatLng());
                
                // ? is used like a boolean but its just shorter for me to use than if !distance etc
                const distance = conflict.distanceKM != undefined ? conflict.distanceKM.toFixed(2) : 'n/a'
                const altDiff = conflict.altitudeDifferenceFT != undefined ? conflict.altitudeDifferenceFT.toFixed(0) : 'n/a'
                const riskScore = conflict.riskScore != undefined ? (conflict.riskScore * 100).toFixed(0) : 'n/a'
                const timeToCollision = conflict.timeToCollision != undefined ? conflict.timeToCollision.toFixed(2) : 'n/a';
                const status = conflict.status || 'unknown' 
            
                let conflictMarker = L.marker(midpoint, {
                    icon: L.divIcon({
                        className: 'conflict',
                        html: `&#9888;`,
                        iconSize: [100, 100] 
                    })
                 }).bindPopup(`Conflict between ${conflict.aircraft1} and ${conflict.aircraft2}<br>Distance: ${distance}km<br>Altitude difference: ${altDiff}ft<br>Risk Score: ${riskScore}<br>Time till collision: ${timeToCollision} mins <br> Status: ${status}`).addTo(map); // binds a popup to the marker with the conflict information
                conflictMarkers[`${conflict.aircraft1}-${conflict.aircraft2}`] = conflictMarker; // adds the conflict marker to the conflict markers dictionary
        }
    });
}   catch (error) {
        console.error("Error fetching conflicts data:", error); // logs the error to the console
        return; // exits the function if there is an error
}

    
}
function addAircraftButton(){
    const button = document.getElementById('addAircraftButton');

    if(!button) return;

    button.replaceWith(button.cloneNode(true)); // remove existing event listeners on the button
    const newButton = document.getElementById('addAircraftButton');

    newButton.style.display = 'flex';
    newButton.style.alignItems = 'center';
    newButton.style.justifyContent = 'center';
    newButton.style.zIndex = 100000; // makes sure the button is above the map
    newButton.style.visibility = 'visible'; 
    newButton.style.opacity= 1;

    button.addEventListener('click', () => {
        generateRandomAircraft();
    }, { once: false }); // ensures the event listener is only added once
}
async function generateRandomAircraft(){
    try{
        const res = await fetch(`${apiBaseURL}/addAircraft`,{
            method: 'POST', // this will send the request to the flask server
            headers: {
                'Content-Type': 'application/json', // tells the server that the request body is in json format
            },
        });
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);

        const result = await res.json();

        if (result.success){
            console.log(`randomly generated ${result.aircraft.callsign}`)
            updateAircraftData();
            alert(`Successfully generated aircraft ${result.aircraft.callsign}`);
        }
        else{
            console.log("generation failed:", result.error)
        }
    } catch(error){
        console.error("Error generating random aircraft:", error);
    }
}

function cleanUpAirportMarkers(activeAircraft){
    const currentAirportsUsed = new Set(); // tracks the current airports being used
    activeAircraft.forEach(aircraft => { // collect aall active airport
        if (aircraft.departureICAO) currentAirportsUsed.add(aircraft.departureICAO);
        if (aircraft.arrivalICAO) currentAirportsUsed.add(aircraft.arrivalICAO);
    });
    Object.keys(airportMarkers).forEach(icao => { // removes any airport markers that are no longer being used
        if(!currentAirportsUsed.has(icao)){
            if(airportMarkers[icao]){
                map.removeLayer(airportMarkers[icao]);
                delete airportMarkers[icao];
                console.log("Removed airport marker for", icao);
            }
        }
    });
        
}
async function updateAircraftData(){
    const data = await fetchAircraftData(); // waits to fetch the aircraft data from the flask server
    if(data.error){
        console.error(data.error); // logs the error to the console
        return; // exits the function if there is an error
    }
    const currentAircraftIDs = new Set(data.map(aircraft => aircraft.id)); // tracks the current aircrafts, hashset used for no duplicates and fast lookups
    
    // clears the markers that no longer exist before updating
    Object.keys(aircraftMarkers).forEach(id => {
        if (!currentAircraftIDs.has(id)) {
            map.removeLayer(aircraftMarkers[id]);
            delete aircraftMarkers[id];
            clearFlightLines(id); // clears the flight lines
        }
    });
    
    cleanUpAirportMarkers(data); // cleans up any airport markers that are no longer being used

    // updates/adds markers for the aircraft/aircrafts
    for (const aircraft of data) {
        const Rotation = calculateRotation(aircraft.heading);
        if (aircraft.departureICAO && !airportMarkers[aircraft.departureICAO]){
            await createAirportMarker(aircraft.departureICAO);
        } 
        if (aircraft.arrivalICAO && !airportMarkers[aircraft.arrivalICAO]){
            await createAirportMarker(aircraft.arrivalICAO);
        }

        
        
        if (!aircraftMarkers[aircraft.id]) {
            // create a marker and assign it
            const newMarker = L.marker([aircraft.lat, aircraft.lon], {
                icon: ScaleIcon(currentZoom),
                rotationAngle: Rotation,
                rotationOrigin: 'center'
            }).bindPopup(`ID: ${aircraft.id}<br>Alt: ${aircraft.altitude}ft<br>Speed: ${aircraft.speed}kt<br>Journey: ${aircraft.departureICAO} to ${aircraft.arrivalICAO}`).addTo(map);
            
            aircraftMarkers[aircraft.id] = newMarker;  
        } else {
            // update existing markers
            aircraftMarkers[aircraft.id]
                .setLatLng([aircraft.lat, aircraft.lon])
                .setRotationAngle(Rotation)
                .getPopup()
                .setContent(`ID: ${aircraft.id}<br>Alt: ${aircraft.altitude}ft<br>Speed: ${aircraft.speed}kt<br>Journey: ${aircraft.departureICAO} to ${aircraft.arrivalICAO} `);
        }
        createFlightLines(aircraft); // creates the flight lines for the aircraft
    }
}
document.addEventListener('DOMContentLoaded', () => {
    addAircraftButton();
    const startButton = document.getElementById('simButton');
    if (startButton) {
        startButton.addEventListener('click', initialiseAirspace);
    }
    const aircraftInput = document.getElementById('aircraftCount');
    if (aircraftInput) {
        aircraftInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                initialiseAirspace();
            }
        });
    }
});
let updateInterval = null;
let conflictInterval = null;
function startUpdate(){
    if(updateInterval) clearInterval(updateInterval); // clears the previous interval if it exists
    if(conflictInterval) clearInterval(conflictInterval); // clears the previous interval if it exists

    updateAircraftData(); // calls the updateAircraftData function to fetch and update the aircraft data
    displayConflicts(); // calls the displayConflicts function to fetch and display the conflicts data
    setInterval(updateAircraftData, 2000); // updates the aircraft data every 2 seconds
    setInterval(displayConflicts, 2000); // updates the conflicts data every 2 seconds
}

//map.whenReady(startUpdate); // when the map is ready, start updating the aircraft data
// ensures that the map is fully loaded before starting the update process
