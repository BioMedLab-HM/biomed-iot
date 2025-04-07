function copyValue(fieldId) {
    var inputField = document.getElementById(fieldId);
    // Temporarily change type to text to enable selection
    inputField.type = 'text';
    inputField.select();
    document.execCommand('copy');
    // Revert back to password type
    inputField.type = 'password';
    alert('Copied to clipboard!');
}

document.getElementById('openDashboard').addEventListener('click', function() {
    var url = this.getAttribute('data-url');
    window.open(url, '_blank');
});

//Alternative Button control to open Node-RED Flows in new tab --> needs adjustments in views.py
document.getElementById('openFlows').addEventListener('click', function() {
    var url = this.getAttribute('data-url');
    window.open(url, '_blank');
});

// Toggle Credential Visibility with Timer
function toggleVisibilityWithTimer() {
    var usernameField = document.getElementById("usernameField");
    var passwordField = document.getElementById("passwordField");
    var tokenField = document.getElementById("tokenField");
    // var noderedUsername = document.getElementById("noderedUsernameField");
    // var noderedPassword = document.getElementById("noderedPasswordField");
    var link = event.target; // Get the clicked link

    // Function to hide credentials
    function hideCredentials() {
        usernameField.type = "password";
        passwordField.type = "password";
        tokenField.type = "password";
        // noderedUsername.type = "password";
        // noderedPassword.type = "password";
        link.textContent = "Show Credentials";
    }

    // Only show if currently hidden
    if (usernameField.type === "password") {
        usernameField.type = "text";
        passwordField.type = "text";
        tokenField.type = "text";
        // noderedUsername.type = "text";
        // noderedPassword.type = "text";
        //link.textContent = "Hide Credentials";

        // Set a timeout to revert back to password type after 10 seconds
        setTimeout(hideCredentials, 10000); // 10000 milliseconds = 10 seconds
    }
}