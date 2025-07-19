
// init map
var map = L.map('map').setView([51.505, -0.09], 3); 

// Create tile layer with openstreetmap 

L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
}).addTo(map);

var AeroplaneIcon = L.icon({
    iconUrl: 'ICONS/airplane.png', // sets image for the aeroplane
    iconSize: [30, 30], // size of the icon
    iconAnchor: [15, 15] // centers the icon on long, lat coordinates.

})

const aircraftMarkers = {}; // dictionary used to store active aircraft markers

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
                icon: AeroplaneIcon,
                rotationAngle: heading,
                rotationStart: 'center'
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

const defaultIconSize = [30,30];

let currentZoom = map.getZoom(); // get the current zoom level

function ScaleIcon(zoom){
    const scaleFactor = Math.pow(1.3, 13 - zoom); // scale factor based on zoom level, 13 is default zoom level
    return L.icon({
        icon: 'ICONS/airplane.png',
        iconSize: defaultIconSize.map(size => size * scaleFactor), // scale the icon size based on the zoom level
        iconAnchor: [15 * scaleFactor, 15 * scaleFactor] // scale the icon anchor based on the zoom level
    })
}

