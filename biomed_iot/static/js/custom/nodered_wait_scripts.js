// Call the function to check container status after the page loads
document.addEventListener('DOMContentLoaded', checkNoderedStatus);

function checkNoderedStatus() {
  const el       = document.getElementById('nodered-wait');
  const statusURL = el.dataset.statusUrl;
  const mgrURL    = el.dataset.managerUrl;

  fetch(statusURL)
    .then(r => r.json())
    .then(data => {
      if (data.status === 'running') {
        window.location.href = mgrURL;
      } else {
        setTimeout(checkNoderedStatus, 2000);
      }
    })
    .catch(e => console.error('Error checking container status:', e));
}
