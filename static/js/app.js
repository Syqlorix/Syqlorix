// static/js/app.js
console.log("External JS loaded!");
document.addEventListener('DOMContentLoaded', () => {
    const externalBtn = document.getElementById('externalBtn');
    if (externalBtn) {
        externalBtn.onclick = function() {
            alert('This click is from an external JS file!');
        };
    }
});
