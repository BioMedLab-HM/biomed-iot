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

document.addEventListener("DOMContentLoaded", function () {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.forEach(function (tooltipTriggerEl) {
      new bootstrap.Tooltip(tooltipTriggerEl);
    });
  });

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('device-form');
  form.addEventListener('submit', e => {
    const checkbox = document.getElementById('id_same_topic');
    if (checkbox && checkbox.checked) {
      const ok = window.confirm(
        "Are you sure you want to use 'inout/' topic for this device?"
      );
      if (!ok) {
        e.preventDefault();
      }
    }
  });
});
