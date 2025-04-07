// Copy code script
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.copy-text').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault(); // Prevent the default link behavior
            const text = this.getAttribute('data-clipboard-text');
            const textarea = document.createElement('textarea');
            textarea.value = text;
            document.body.appendChild(textarea);
            textarea.select();
            try {
                const successful = document.execCommand('copy');
                const msg = successful ? 'successful' : 'unsuccessful';
                console.log('Copying text command was ' + msg);
            } catch (err) {
                console.error('Oops, unable to copy', err);
            }
            document.body.removeChild(textarea);
        });
    });
});