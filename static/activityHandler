function startActivity(actId, actName, goalName) {
    openTime = new Date(); // Spara starttiden
    localStorage.setItem('start', openTime.getTime());
    localStorage.setItem('active', 'true');
    localStorage.setItem('selectedActivityId', actId);
    
    if (goalName === "Skriva") {
        window.location.href = `/txt/journal?section_name=${actName}`;
    } else {
        window.location.href = `/pmg/focus_room/${actId}`;
    }
}

function stopActivity(event) {
    if (event) {
        event.preventDefault(); // Förhindra sidomladdning
    }
    const savedActive = localStorage.getItem('active');
    
    const closeTime = new Date(); // Spara stopptiden
    localStorage.setItem('active', false);
    localStorage.setItem('end', closeTime.getTime()); // Spara UNIX-tid istället för UTC

    // Hämta sparade tider från localStorage
    const startStored = localStorage.getItem('start');
    const endStored = localStorage.getItem('end');
    const activityId = localStorage.getItem('selectedActivityId');
    
    const stopBtn = document.getElementById('stopBtn');
    const end = document.getElementById('endValue');
    const start = document.getElementById('startValue');
    const score = document.getElementById('scoreValue');

    if (startStored && endStored && activityId) {
        // Omvandla UNIX-tid till lokal tid
        const startTime = new Date(Number(startStored));  // Konvertera sträng till nummer
        const endTime = new Date(Number(endStored));      // Konvertera sträng till nummer

        // Formatera till 'YYYY-MM-DD HH:MM:SS' i lokal tid
        const options = { year: 'numeric', month: '2-digit', day: '2-digit', 
                          hour: '2-digit', minute: '2-digit', second: '2-digit',
                          hour12: false };

        const locale = 'sv-SE';

        document.getElementById("startValue").value = new Intl.DateTimeFormat(locale, options)
            .format(startTime).replace(',', '');
        document.getElementById("endValue").value = new Intl.DateTimeFormat(locale, options)
            .format(endTime).replace(',', '');

        document.getElementById("aID").value = activityId;
        document.getElementById("end").classList.remove("hidden");
        document.getElementById("start").classList.remove("hidden");
        document.getElementById("time").classList.remove("hidden");
        document.getElementById("aDate").classList.remove("hidden");
        document.getElementById("complete-form").classList.remove("hidden");
        document.getElementById("continueButton").classList.remove("hidden");

    }
    
    document.getElementById('stopButton').classList.add("hidden");

    // **Beräkna elapsed time korrekt**
    if (startStored) {
        const elapsedTimeMs = closeTime - new Date(Number(startStored));  // Se till att vi konverterar
        const elapsedTimeMin = Math.floor(elapsedTimeMs / 60000);
        score.value = elapsedTimeMin;
        saveActivity(elapsedTimeMin);
    } else {
        console.error("Start time is missing in localStorage.");
    }
}

// Spara aktivitet
function saveActivity(time) {
    document.getElementById('complete-form').classlist.remove ("hidden");
    document.getElementById('elapsedTime').classList.remove ("hidden");
    document.getElementById("scoreValue").value = time; // Använd rätt element-ID
    localStorage.setItem('active', false);
}

function toggleActivityForm() {
    var form = document.getElementById('activityForm');
    if (form) {
        form.style.display = form.style.display = 'flex';
        document.getElementById('startaAktivitet').style.display = 'none';
        document.getElementById('start-timer').style.display = 'block';

    } else {
        console.error('Activity form element not found');
    }
}

function handleActivityClick(element) {
    const actName = element.getAttribute('data-act-name');
    const activityId = element.getAttribute('data-activity-id');
    const newActivity = element.getAttribute('data-start-activity');
    const goalName = element.getAttribute('data-goal-name');

    if (newActivity === "1") {
        startActivity(activityId,actName,goalName);
    } else {
        // Annars omdirigera till todos
        window.location.href = `/pmg/activity/${activityId}/tasks`;
    }
}

function updateEndTime() {
    const locale = 'sv-SE';
    const options = {
        year: 'numeric', month: '2-digit', day: '2-digit',
        hour: '2-digit', minute: '2-digit', second: '2-digit',
        hour12: false
    };

    const startTimeStr = startInput.value;
    const scoreMinutes = parseInt(scoreInput.value, 10) || 0; // Hämta score i minuter, standardvärde 0

    if (!startTimeStr) return; // Avbryt om starttid saknas

    const startTime = new Date(startTimeStr.replace(" ", "T")); // Konvertera till Date-objekt

    if (isNaN(startTime.getTime())) return; // Avbryt om startTime är ogiltigt

    startTime.setMinutes(startTime.getMinutes() + scoreMinutes); // Lägg till score-minuter

    // Uppdatera End Time-fältet i format 'YYYY-MM-DD HH:MM:SS' i lokal tid
    endInput.value = new Intl.DateTimeFormat(locale, options).format(startTime).replace(",", "");
}