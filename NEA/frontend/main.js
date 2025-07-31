
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
    });
});

// updates the aircraft positions
function updateAircraftMarkers(aircraftData) {
    // Track which aircraft we've processed
    const processIDs = new Set();
    
    aircraftData.forEach(aircraft => {
        processIDs.add(aircraft.id);
        
        if(aircraftMarkers[aircraft.id]) {
            // Update every existing marker
            aircraftMarkers[aircraft.id]
                .setLatLng([aircraft.lat, aircraft.lon])
                .setRotationAngle(aircraft.heading)
                .getPopup()
                .setContent(`ID: ${aircraft.id}<br>Alt: ${aircraft.altitude}ft<br>Speed: ${aircraft.speed}kt`); // binds a popup to the marker with the aircraft information
        } else {
            // Create a new aircraft marker
            aircraftMarkers[aircraft.id] = L.marker([aircraft.lat, aircraft.lon], {
                icon: ScaleIcon(currentZoom),
                rotationAngle: aircraft.heading,
                rotationOrigin: 'center'
            }).bindPopup(`ID: ${aircraft.id}<br>Alt: ${aircraft.altitude}ft<br>Speed: ${aircraft.speed}kt`)
              .addTo(map);
        }
    });
    
    // Remove old markers
    Object.keys(aircraftMarkers).forEach(id => {
        if(!processIDs.has(id)) {
            map.removeLayer(aircraftMarkers[id]);
            delete aircraftMarkers[id];
        }
    });
}







const flaskURL = "http://localhost:5000"

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
            delete aircraftMarkers[id];}});
    
    // updates/adds markers for the aircraft/aircrafts
    data.forEach(aircraft => {
        if (!aircraftMarkers[aircraft.id]) {
            aircraftMarkers[aircraft.id] = L.marker([aircraft.lat, aircraft.lon], {
                icon: ScaleIcon(currentZoom),
                rotationAngle: aircraft.heading,
                rotationOrigin: 'center'
            }).bindPopup(`ID: ${aircraft.id}<br>Alt: ${aircraft.altitude}ft`).addTo(map);
        } else {
            aircraftMarkers[aircraft.id]
                .setLatLng([aircraft.lat, aircraft.lon])
                .setRotationAngle(aircraft.heading);
        }
    });
    
}


function startUpdate(){
    updateAircraftData(); // calls the updateAircraftData function to fetch and update the aircraft data
    setInterval(updateAircraftData, 2000); // updates the aircraft data every 2 seconds
}

map.whenReady(startUpdate); // when the map is ready, start updating the aircraft data
// ensures that the map is fully loaded before starting the update process
