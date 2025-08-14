// init map
console.log("main.js loaded");
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
    iconUrl: '/NEA/frontend/ICONS/airplane.svg', // sets image for the aeroplane
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


async function fetchAirport(icao){
    try{
        const response = await fetch(`http://localhost:5000/airport/${icao}`); // fetches the airport data from the flask server
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
        iconUrl: 'ICONS/airplane.svg',
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
        
        const response = await fetch("http://localhost:5000/aircraft"); // fetches the aircraft data from the flask server
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
            arrivalICAO: aircraft.arrivalICAO
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
        const response = await fetch("http://localhost:5000/conflicts"); // fetches the conflicts data from the flask server
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
                const altDiff = conflict.altitudeDifferenceFT != undefined ? conflict.distanceKM.toFixed(0) : 'n/a'
                const riskScore = conflict.riskScore != undefined ? (conflict.riskScore * 100).toFixed(0) : 'n/a'
                const timeToCollision = conflict.timeToCollision != undefined ? conflict.timeToCollision.toFixed(2) : 'n/a';
                const status = conflict.status || 'unknown' 
            
                let conflictMarker = L.marker(midpoint, {
                    icon: L.divIcon({
                        className: 'conflict',
                        html: `&#9888;`,
                        iconSize: [100, 100] 
                    })
                 }).bindPopup(`Conflict between ${conflict.aircraft1} and ${conflict.aircraft2}<br>Distance: ${distance}m<br>Altitude difference: ${altDiff}ft<br>Risk Score: ${riskScore}<br>Time till collision: ${timeToCollision} mins <br> Status: ${status}`).addTo(map); // binds a popup to the marker with the conflict information
                conflictMarkers[`${conflict.aircraft1}-${conflict.aircraft2}`] = conflictMarker; // adds the conflict marker to the conflict markers dictionary
        }
    });
}   catch (error) {
        console.error("Error fetching conflicts data:", error); // logs the error to the console
        return; // exits the function if there is an error
}

    
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
        }
    });
        
    // updates/adds markers for the aircraft/aircrafts
    for (const aircraft of data) {
        const Rotation = calculateRotation(aircraft.heading);
        if (aircraft.departureICAO){
            await createAirportMarker(aircraft.departureICAO);
        } 
        if (aircraft.arrivalICAO){
            await createAirportMarker(aircraft.arrivalICAO);
        }

        
        
        if (!aircraftMarkers[aircraft.id]) {
            // create a marker and assign it
            const newMarker = L.marker([aircraft.lat, aircraft.lon], {
                icon: ScaleIcon(currentZoom),
                rotationAngle: Rotation,
                rotationOrigin: 'center'
            }).bindPopup(`ID: ${aircraft.id}<br>Alt: ${aircraft.altitude}ft<br>Speed: ${aircraft.speed}kt`).addTo(map);
            
            aircraftMarkers[aircraft.id] = newMarker;  
        } else {
            // update existing markers
            aircraftMarkers[aircraft.id]
                .setLatLng([aircraft.lat, aircraft.lon])
                .setRotationAngle(Rotation)
                .getPopup()
                .setContent(`ID: ${aircraft.id}<br>Alt: ${aircraft.altitude}ft<br>Speed: ${aircraft.speed}kt`);
        }
    };
}

function startUpdate(){
    updateAircraftData(); // calls the updateAircraftData function to fetch and update the aircraft data
    displayConflicts(); // calls the displayConflicts function to fetch and display the conflicts data
    setInterval(updateAircraftData, 2000); // updates the aircraft data every 2 seconds
    setInterval(displayConflicts, 2000); // updates the conflicts data every 2 seconds
}

map.whenReady(startUpdate); // when the map is ready, start updating the aircraft data
// ensures that the map is fully loaded before starting the update process
