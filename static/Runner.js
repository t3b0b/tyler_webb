let watchId = null;
let positions = JSON.parse(localStorage.getItem("run_positions")) || [];
let totalDistance = parseFloat(localStorage.getItem("run_distance")) || 0;

function toRadians(degrees) {
    return degrees * (Math.PI / 180);
}

function calculateDistance(lat1, lon1, lat2, lon2) {
    const R = 6371000;
    const dLat = toRadians(lat2 - lat1);
    const dLon = toRadians(lon2 - lon1);
    const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
              Math.cos(toRadians(lat1)) * Math.cos(toRadians(lat2)) *
              Math.sin(dLon / 2) * Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
}

function updateDisplay() {
    document.getElementById("distance").textContent = `Distans: ${Math.round(totalDistance)} meter`;
}

function success(pos) {
    const { latitude, longitude } = pos.coords;
    const newPos = { latitude, longitude };

    if (positions.length > 0) {
        const prev = positions[positions.length - 1];
        const dist = calculateDistance(prev.latitude, prev.longitude, latitude, longitude);
        totalDistance += dist;
    }

    positions.push(newPos);
    localStorage.setItem("run_positions", JSON.stringify(positions));
    localStorage.setItem("run_distance", totalDistance);
    localStorage.setItem("run_active", "true");

    updateDisplay();
}

function error(err) {
    console.warn(`ERROR(${err.code}): ${err.message}`);
}

function startTracking() {
    if (localStorage.getItem("run_active") === "true") return;

    document.getElementById("status").textContent = "Spårning pågår...";
    watchId = navigator.geolocation.watchPosition(success, error, {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0
    });

    localStorage.setItem("run_active", "true");
}

function stopTracking() {
    if (watchId !== null) {
        navigator.geolocation.clearWatch(watchId);
    }

    document.getElementById("status").textContent = "Spårning stoppad";

    // Skicka till server
    fetch('/cal/save_run_data', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ positions, totalDistance })
    });

    // Rensa localStorage
    localStorage.removeItem("run_positions");
    localStorage.removeItem("run_distance");
    localStorage.removeItem("run_active");

    positions = [];
    totalDistance = 0;
    updateDisplay();
}

// ✅ Återställ distans vid sidladdning
window.addEventListener("load", () => {
    if (localStorage.getItem("run_active") === "true") {
        updateDisplay();
        startTracking();  // Fortsätt spårning om aktiv
    }
});
