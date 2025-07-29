
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
function updateAircraftMarkers(aircraftData){
    aircraftData.forEach(aircraft => {
        const{id, lat,lon,heading} = aircraft;
        if(aircraftMarkers[id]){ // checks for existing aircrafts
            aircraftMarkers[id].setLatLng([lat, lon]); // updates the marker to its new position
            aircraftMarkers[id].setRotationAngle(heading); // updates the marker angle to its new heading using leaflet marker rotation
        } else {
            // Create new marker
            aircraftMarkers[id] = L.marker([lat, lon], {
                icon: ScaleIcon(currentZoom), // sets the icon size based on the zoom level
                rotationAngle: heading,
                rotationOrigin: 'center'
            }).addTo(map);
        }
    })
    
    
        
}



let angle = 0;
const TestMarker = {id: "test", lat: 51.505, lon: -0.09, heading: 0}; // test marker to test the updateAircraftMarkers function
updateAircraftMarkers([TestMarker]); 

setInterval(() => {
    angle = (angle + 5) % 360; // add 5 degrees until 360 degrees is reached
    TestMarker.heading = angle; // set angle to the aircraft heading
    updateAircraftMarkers([TestMarker]); // update the marker with the new heading
}, 100) // updates the marker every 100ms

const flaskURL = "http:localhost:5000"

// async means the function will return a promise
// fetchAircraftData fetches the aircraft data from the flask server
async function fetchAircraftData(){ 
    try{
        const response = await fetch(flaskURL + "/aircraft"); // fetches the aircraft data from the flask server
        if(!response.ok) throw new Error(`HTTP error! status: ${response.status}`); // throws an error if the response is not ok
        return await response.json(); // returns the response as json

        
    } catch(error){
        console.error("Error fetching aircraft data:", error); // logs the error to the console
        return {error:"failed to fetch aircraft data"};// returns an error message
    }
}

async function updateAircraftData(){
    const data = await fetchAircraftData(); // waits to fetch the aircraft data from the flask server
    if(data.error){
        console.error(data.error); // logs the error to the console
        return; // exits the function if there is an error
    }

    // clears the existing aircraft markers before updating
    Object.values(aircraftMarkers).forEach(marker => map.removeLayer(marker));
    aircraftMarkers = {}; // clears the aircraft markers dictionary
    
    data.forEach(aircraft => {
        aircraftMarkers[id] = L.marker([aircraft.lat, aircraft.lon], {
            icon: ScaleIcon(currentZoom), // sets the icon size based on the zoom level
            rotationAngle: aircraft.heading,
        }).addTo(map);
    })
    .bindPopup("id: " + aircraft.id + "<br>altitude: " + aircraft.altitude).addTo(map); // binds a popup to every aeroplane with their id and altitude

    setInterval(() => { 
        updateAircraftData(); // repeats the function and updates the aircraft data every 5 seconds
    }, 2000); // updates the aircraft data every 2 seconds and matches cache timeout
}
