const options = { 
    year: 'numeric', 
    month: '2-digit', 
    day: '2-digit', 
    hour: '2-digit', 
    minute: '2-digit', 
    second: '2-digit',
    hour12: false 
};
const locale = 'sv-SE';

const hiddenIds = [
    "end",
    "start",
    "time",
    "date",
    "complete-form",
    "continueButton",
    "write-on-time"
];
const visibleIds = [
    "stopButton", 
    "time-less"
];

const actId = document.getElementById("aID");
const completeform = document.getElementById("complete-form");
const end = document.getElementById('endValue');
const start = document.getElementById('startValue');
const score = document.getElementById('scoreValue');
const stopBtn = document.getElementById('stopButton');
const timeLessButton = document.getElementById("time-less");
const writeOnTimeButton = document.getElementById("write-on-time");


function startActivity(actId, actName, goalName) {
    let openTime = new Date();
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

    let closeTime = new Date();
    let startStored = localStorage.getItem('start');
    let activityId = localStorage.getItem('selectedActivityId');
    actId.value = activityId;

    if (startStored && activityId) {
    // Tidshantering
        var startTime = new Date(Number(startStored)); 
        var endTime = new Date(Number(closeTime));
        let elapsedTimeMs = closeTime - new Date(Number(startTime));
        let elapsedTimeMin = Math.floor(elapsedTimeMs / 60000);
        start.value = new Intl.DateTimeFormat(locale, options).format(startTime).replace(',', '');
        end.value = new Intl.DateTimeFormat(locale, options).format(endTime).replace(',', '');
        score.value = elapsedTimeMin;
    // Show hidden elements
        for (id of hiddenIds) {
            const element = document.getElementById(id);
            if (element) {
                element.classList.remove("hidden");
            }
        };
    // Hide visible elements
        for (id of visibleIds) {
            const element = document.getElementById(id);
            if (element) {
                element.classList.add("hidden");
            }
        };
        
        localStorage.setItem('active', false);
    }
    
    

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
        window.location.href = `/tasks/activity/${activityId}/tasks`;
    }
}

function updateEndTime() {

    const startTimeStr = startInput.value;
    const scoreMinutes = parseInt(scoreInput.value, 10) || 0; // Hämta score i minuter, standardvärde 0

    if (!startTimeStr) return; // Avbryt om starttid saknas

    const startTime = new Date(startTimeStr.replace(" ", "T")); // Konvertera till Date-objekt

    if (isNaN(startTime.getTime())) return;

    startTime.setMinutes(startTime.getMinutes() + scoreMinutes);
    endInput.value = new Intl.DateTimeFormat(locale, options).format(startTime).replace(",", "");
}