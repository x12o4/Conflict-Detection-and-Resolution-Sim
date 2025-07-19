
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

const defaultIconSize = [12,12]; // default icon size for the aircraft markers, used to scale the icon size based on the zoom level

const DefaultZoom = 7;

const minimumScale = 0.3; // maximum scale factor for the icon size
const maximumScale = 1.3; // minimum scale factor for the icon size

let currentZoom = map.getZoom(); // get the current zoom level

function ScaleIcon(zoom){
    const scaleFactor = Math.min(maximumScale, Math.max(minimumScale, Math.pow(1.2,DefaultZoom - zoom))); // calculates the scale factor based on the zoom level, ensuring it stays within the minimum and maximum scale limits
    // scale factor is calculated by taking the difference between the default zoom level and the current zoom level, and raising 1.2 to that power, then clamping it between the minimum and maximum scale limits
    return L.icon({
        
        iconUrl: 'ICONS/airplane.png',
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



