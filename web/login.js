/* ==========================================================================
   CA Case Scenario Solver - Login Page Logic
   ========================================================================== */

function init() {
    console.log("[+] Initializing Login Page...");
    
    // Check if user is already logged in
    try {
        const storedProfile = localStorage.getItem("ca_user_profile");
        if (storedProfile) {
            const userProfile = JSON.parse(storedProfile);
            if (userProfile && userProfile.name && userProfile.regNo) {
                console.log("[+] Already logged in as:", userProfile.name);
                window.location.href = "dashboard.html";
                return;
            }
        }
    } catch (e) {
        console.error("[-] Error reading profile from localStorage:", e);
    }

    // Set up form submission handler
    const loginForm = document.getElementById("login-form");
    loginForm.addEventListener("submit", (e) => {
        e.preventDefault();
        handleLogin();
    });
}

function handleLogin() {
    const nameInput = document.getElementById("login-name").value.trim();
    const regInput = document.getElementById("login-reg").value.trim().toUpperCase();
    
    if (!nameInput || !regInput) return;
    
    const userProfile = {
        name: nameInput,
        regNo: regInput
    };
    
    try {
        localStorage.setItem("ca_user_profile", JSON.stringify(userProfile));
        console.log("[+] User profile saved:", userProfile);
        window.location.href = "dashboard.html";
    } catch (e) {
        console.warn("[-] Failed to save user profile to localStorage:", e);
        alert("Failed to save credentials in localStorage. Please ensure cookies/local storage are enabled.");
    }
}

// Initialize on DOM ready
document.addEventListener("DOMContentLoaded", init);
