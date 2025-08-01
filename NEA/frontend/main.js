// init map
var map = L.map('map').setView([51.505, -0.09], 3);

// Create tile layer with openstreetmap 
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
}).addTo(map);

var AeroplaneIcon = L.icon({
    iconUrl: 'ICONS/airplane.svg', // sets image for the aeroplane
    iconSize: [30, 30], // size of the icon
    iconAnchor: [15, 15] // centers the icon on long, lat coordinates.
})

const aircraftMarkers = {}; // dictionary used to store active aircraft markers
const defaultIconSize = [12,12]; // default icon size for the aircraft markers, used to scale the icon size based on the zoom level
const DefaultZoom = 7;
const minimumScale = 1; // minimum scale factor for the icon size
const maximumScale = 1.6; // maximum scale factor for the icon size
let currentZoom = map.getZoom(); // get the current zoom level

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
            heading: aircraft.hdg,
            altitude: aircraft.alt,
            speed: aircraft.tas
        }));         
    } catch(error){
        console.error("Error fetching aircraft data:", error); // logs the error to the console
        return [];
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
    data.forEach(aircraft => {
        const Rotation = calculateRotation(aircraft.heading);
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
    });
}

function startUpdate(){
    updateAircraftData(); // calls the updateAircraftData function to fetch and update the aircraft data
    setInterval(updateAircraftData, 2000); // updates the aircraft data every 2 seconds
}

map.whenReady(startUpdate); // when the map is ready, start updating the aircraft data
// ensures that the map is fully loaded before starting the update process
