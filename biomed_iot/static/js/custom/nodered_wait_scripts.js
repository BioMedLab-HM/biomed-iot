// Call the function to check container status after the page loads
document.addEventListener('DOMContentLoaded', function() {checkNoderedStatus();});

function checkNoderedStatus() {
    fetch('{% url "nodered-status-check" %}')  //  path to the status checking endpoint
        .then(response => response.json())
        .then(data => {
            if(data.status == "running") {
                window.location.href = "{% url 'nodered-manager' %}";  // Redirect when running
            } else {
                setTimeout(checkNoderedStatus, 2000);  // Recheck after 2 seconds
            }
        })
        .catch(error => console.error('Error checking container status:', error));
}