document.addEventListener("DOMContentLoaded", function() {
            var table = document.getElementById("hotelsTable").getElementsByTagName('tbody')[0];
            var rows = table.getElementsByTagName('tr').length;
            var viewMapButton = document.getElementById("viewMapButton");
            var petrolLowCheckbox = document.getElementById("petrolLowCheckbox");
            var petrolLowLabel = document.querySelector('label[for="petrolLowCheckbox"]');

            console.log('Number of rows:', rows);  // Debugging line

            if (rows === 0) {
                viewMapButton.style.display = 'none';
                petrolLowCheckbox.style.display = 'none';
                petrolLowLabel.style.display = 'none';
                console.log('View Map button hidden');  // Debugging line
            } else {
                console.log('View Map button shown');  // Debugging line
            }
});

window.onload = function() {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('success')) {
        if (urlParams.get('success') === 'True') {
            alert("Sorting was successful! Please click assign to get your job listing!");
        } else if (urlParams.get('success') === 'False') {
            alert("Sorting was unsuccessful! There are existing trips for today!");
        }
    }
};


