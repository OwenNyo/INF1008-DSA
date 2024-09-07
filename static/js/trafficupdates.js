// Call initMap when the window has finished loading
window.onload = function() {
    initMap();
};

// Function to initialize the map and display traffic layer
function initMap() {
    const map = new google.maps.Map(document.getElementById('map'), {
        zoom: 12,
        center: { lat: 1.290270, lng: 103.851959 } // Centered at Changi Airport T3
    });

    // Display traffic layer
    const trafficLayer = new google.maps.TrafficLayer();
    trafficLayer.setMap(map);

    // Display traffic incidents
    displayTrafficMarkers(map);

    // Example usage: display traffic incidents in the North region
    displayTrafficReport('North');
}

// Function to display traffic incidents markers on the map
function displayTrafficMarkers(map) {
    const incidents = trafficData.incidents;

    incidents.forEach(incident => {
        const coordinates = {
            lat: incident.geometry.coordinates[0][1],
            lng: incident.geometry.coordinates[0][0]
        };

        let icon;
        switch (incident.properties.iconCategory) {
            case 1:
                icon = 'https://maps.google.com/mapfiles/ms/icons/red-dot.png';
                break;
            case 7:
                icon = 'https://maps.google.com/mapfiles/ms/icons/yellow-dot.png';
                break;
            case 8:
                icon = 'https://maps.google.com/mapfiles/ms/icons/orange-dot.png';
                break;
            case 9:
                icon = 'https://maps.google.com/mapfiles/ms/icons/blue-dot.png';
                break;
            case 14:
                icon = 'https://maps.google.com/mapfiles/ms/icons/green-dot.png';
                break;
            default:
                icon = 'https://maps.google.com/mapfiles/ms/icons/purple-dot.png';
        }

        const marker = new google.maps.Marker({
            position: coordinates,
            map: map,
            icon: icon
        });

        marker.addListener('click', function() {
            console.log('Marker clicked:', incident);
        });
    });
}

// Function to display traffic incident data filtered by region
function displayTrafficReport(region) {
    const incidents = trafficData.incidents;
    const trafficTableBody = document.getElementById('trafficTable').getElementsByTagName('tbody')[0];

    // Clear existing table rows
    trafficTableBody.innerHTML = '';

    // Filter incidents based on region
    const filteredIncidents = incidents.filter(incident => {
        const lat = incident.geometry.coordinates[0][1];
        const lng = incident.geometry.coordinates[0][0];

        // Determine the region based on latitude and longitude
        if (
            (region === 'North' && lat >= 1.410195 && lat <= 1.472660 && lng >= 103.695585 && lng <= 103.864240) ||
            (region === 'East' && lat >= 1.276679 && lat <= 1.410195 && lng >= 103.902273 && lng <= 104.033679) ||
            (region === 'West' && lat >= 1.276679 && lat <= 1.410195 && lng >= 103.613826 && lng <= 103.766361) ||
            (region === 'Central' && lat >= 1.233774 && lat <= 1.336059 && lng >= 103.766400 && lng <= 103.901000) ||
            (region === 'NorthEast' && lat >= 1.347385 && lat <= 1.397496 && lng >= 103.828483 && lng <= 103.903376)
        ) {
            return true;
        } else {
            return false;
        }
    });

    filteredIncidents.forEach(incident => {
        let incidentType;
        switch (incident.properties.iconCategory) {
            case 1:
                incidentType = 'Accident';
                break;
            case 7:
                incidentType = 'Lane Closed';
                break;
            case 8:
                incidentType = 'Road Closed';
                break;
            case 9:
                incidentType = 'Road Works';
                break;
            case 14:
                incidentType = 'Broken Down Vehicle';
                break;
            default:
                incidentType = 'Other';
        }

        try {
            const row = trafficTableBody.insertRow();
            const typeCell = row.insertCell(0);
            const categoryCell = row.insertCell(1);
            const locationCell = row.insertCell(2);

            typeCell.textContent = incidentType;
            categoryCell.textContent = incident.properties.iconCategory;

            reverseGeocode(incident.geometry.coordinates[0][1], incident.geometry.coordinates[0][0], function(address) {
                locationCell.textContent = address;
            });
        } catch (error) {
            console.error('Error adding row to table:', error);
        }
    });
}

// Function to update traffic report based on selected region
function updateTrafficReport() {
    const regionSelect = document.getElementById('regionSelect');
    const selectedRegion = regionSelect.value;

    // Clear search bar contents
    const searchBar = document.getElementById('searchBar');
    searchBar.value = '';

    // Display traffic incidents based on selected region
    displayTrafficReport(selectedRegion);
}

// Function to convert latitude and longitude to address using reverse geocoding
function reverseGeocode(lat, lng, callback) {
    const geocoder = new google.maps.Geocoder();
    const latlng = { lat: parseFloat(lat), lng: parseFloat(lng) };

    geocoder.geocode({ 'location': latlng }, function(results, status) {
        if (status === 'OK') {
            if (results[0]) {
                callback(results[0].formatted_address);
            } else {
                callback('Address not found');
            }
        } else {
            callback('Geocoder failed due to: ' + status);
        }
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const searchBar = document.getElementById('searchBar');

    searchBar.addEventListener('input', () => {
        const query = searchBar.value.toLowerCase();
        const tableRows = document.querySelectorAll('#trafficTable tbody tr');

        tableRows.forEach(row => {
            const cells = row.querySelectorAll('td');
            let rowText = '';
            cells.forEach(cell => {
                rowText += cell.textContent.toLowerCase() + ' ';
            });

            if (substringSearch(rowText, query)) {
                highlightMatch(row, query); // Highlight matching words
                row.style.display = '';
            } else {
                removeHighlight(row); // Remove highlight if not matching
                row.style.display = 'none';
            }
        });
    });
});

function highlightMatch(row, query) {
    const cells = row.querySelectorAll('td');
    cells.forEach(cell => {
        const text = cell.textContent.toLowerCase();
        const index = text.indexOf(query);
        if (index !== -1) {
            const matchedText = cell.textContent.substring(index, index + query.length);
            const newText = cell.textContent.replace(matchedText, `<span class="highlight">${matchedText}</span>`);
            cell.innerHTML = newText;
        }
    });
}

function removeHighlight(row) {
    const cells = row.querySelectorAll('td');
    cells.forEach(cell => {
        cell.innerHTML = cell.textContent;
    });
}

function substringSearch(text, query) {
    const n = text.length;
    const m = query.length;

    // Empty query matches everything
    if (m === 0) return true;

    for (let i = 0; i <= n - m; i++) {
        let j;
        for (j = 0; j < m; j++) {
            if (text[i + j] !== query[j]) {
                break;
            }
        }
        // Found a match
        if (j === m) return true;
    }

    return false;
}