// toggle_mqtt_credentials_visibility.js
function toggleVisibility() {
    var usernameFields = document.querySelectorAll(".usernameField");
    var passwordFields = document.querySelectorAll(".passwordField");

    usernameFields.forEach(function (field) {
        field.type = field.type === "password" ? "text" : "password";
    });

    passwordFields.forEach(function (field) {
        field.type = field.type === "password" ? "text" : "password";
    });
}

// copy_input_field_text_btn.js
function copyValue(btn) {
    var inputField = btn.parentElement.querySelector('input');
    var originalType = inputField.type;
    inputField.type = 'text';
    inputField.select();
    document.execCommand('copy');
    inputField.type = originalType;
    alert('Copied to clipboard!');
}
