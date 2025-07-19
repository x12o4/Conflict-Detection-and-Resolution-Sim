
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

const aircraftMarkers = {}; // used to store active aircraft markers

// updates the aircraft positions
function updateAircraftMarkers(aircraftData){
    aircraftData.forEach(aircraft => {
        const{id, lat,lon,heading} = aircraft;
    })
}

const iconHeading = L.icon({
    icon: 'ICONS/airplane.png', // refresh icon on map
    iconSize: [30, 30], 
    iconAnchor: [15, 15], 
    
})
var marker = L.marker([51.5, -0.09], { icon: AeroplaneIcon }).addTo(map);

