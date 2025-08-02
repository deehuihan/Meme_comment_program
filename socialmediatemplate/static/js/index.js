// Firebase configuration
const firebaseConfig = {
    apiKey: "AIzaSyCMsa0rv-EJnMnFNwQ5X3F7hbjdGvwJ00E",
    authDomain: "socialmedia-7c038.firebaseapp.com",
    databaseURL: "https://socialmedia-7c038-default-rtdb.asia-southeast1.firebasedatabase.app",
    projectId: "socialmedia-7c038",
    storageBucket: "socialmedia-7c038.appspot.com",
    messagingSenderId: "851731795907",
    appId: "1:851731795907:web:c1db66a2f12857b8e2ba64"
};

// We will use the Firebase initialization from the inline script in index.html

document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM Content Loaded for index.js");
    
    // Check if the user is already logged in
    const storedUserId = localStorage.getItem('socialUserId');
    console.log("Current stored user ID:", storedUserId);
    
    // If no username is stored, redirect to input page
    if (!storedUserId) {
        console.log("No user ID found, redirecting to login page");
        window.location.href = '/';
        return;
    }
    
    // Make sure the page selection is visible
    const pageSelection = document.getElementById('pageSelection');
    console.log("pageSelection element:", pageSelection);
    
    if (pageSelection) {
        console.log("Setting pageSelection display to block");
        pageSelection.style.display = 'block';
    }
    
    // Display username
    const usernameDisplay = document.getElementById('usernameDisplay');
    console.log("usernameDisplay element:", usernameDisplay);
    
    if (usernameDisplay) {
        usernameDisplay.textContent = storedUserId;
    }
    
    // Note: startExperiment button handler is now in index.html inline script
    // to avoid conflicts with Excel logging functionality
    
    // Handle logout functionality
    const logoutButton = document.getElementById('logoutButton');
    if (logoutButton) {
        logoutButton.addEventListener('click', function() {
            // Show logout confirmation
            document.getElementById('logoutDialogContainer').style.display = 'flex';
        });
    }
    
    const cancelLogout = document.getElementById('cancelLogout');
    if (cancelLogout) {
        cancelLogout.addEventListener('click', function() {
            document.getElementById('logoutDialogContainer').style.display = 'none';
        });
    }
    
    const confirmLogout = document.getElementById('confirmLogout');
    if (confirmLogout) {
        confirmLogout.addEventListener('click', function() {
            // Clear all user data
            localStorage.clear();
            // Redirect to input page
            window.location.href = '/';
        });
    }
});