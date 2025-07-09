
// init map
var map = L.map('map').setView([51.505, -0.09], 13);

// Create tile layer with openstreetmap 

L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
}).addTo(map);

var AeroplaneIcon = L.icon({
    iconUrl: 'ICONS/airplane.png', // sets image for the aeroplane
    iconSize: [38, 38], // size of the icon

})

var marker = L.marker([51.5, -0.09], { icon: AeroplaneIcon }).addTo(map);

