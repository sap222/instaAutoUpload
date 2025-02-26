document.addEventListener("DOMContentLoaded", () => {
    const loginForm = document.getElementById("loginForm");
    const uploadForm = document.getElementById("uploadForm");
    const loginResponse = document.getElementById("loginResponse");
    const uploadResponse = document.getElementById("uploadResponse");
    const loginSection = document.getElementById("loginSection");
    const uploadSection = document.getElementById("uploadSection");

    // Login function
    window.submitLogin = function() {
        const username = document.getElementById("username").value.trim();
        const password = document.getElementById("password").value.trim();
        const verificationCode = document.getElementById("verificationCode").value.trim() || null;

        if (!username || !password) {
            loginResponse.innerText = "❌ Please enter both username and password!";
            return;
        }

        loginResponse.innerText = "Logging in...";

        fetch("/login/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password, verification_code: verificationCode })
        })
        .then(response => {
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return response.json();
        })
        .then(data => {
            loginResponse.innerText = "✅ " + data.message;
            loginSection.style.display = "none"; // Hide login section
            uploadSection.style.display = "block"; // Show upload section
        })
        .catch(error => {
            loginResponse.innerText = "❌ Login failed: " + error.message;
        });
    };

    // Upload function
    window.submitLinks = function() {
        let links = document.getElementById("links").value.trim().split("\n").map(link => link.trim()).filter(link => link);
        if (links.length === 0) {
            uploadResponse.innerText = "❌ Please enter at least one valid link!";
            return;
        }

        uploadResponse.innerText = "Processing...";

        fetch("/process_videos/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ instagram_links: links })
        })
        .then(response => {
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return response.json();
        })
        .then(data => {
            uploadResponse.innerText = "✅ " + data.message;
        })
        .catch(error => {
            uploadResponse.innerText = "❌ Error: " + error.message;
        });
    };
});
