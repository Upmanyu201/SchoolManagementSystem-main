// In main.js, replace the entire file with this corrected version:
// D:\School-Management-System\School-Management-System-main\static\js\main.js
document.addEventListener("DOMContentLoaded", function () {
    console.log("✅ D:\\School-Management-System\\School-Management-System-main\\static\\js\\main.js loaded");

    function getCSRFToken() {
        const csrfTokenElement = document.querySelector('[name=csrfmiddlewaretoken]');
        return csrfTokenElement ? csrfTokenElement.value : null;
    }
});