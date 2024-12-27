var activityId;
var openTime;
var closeTime;

function handleActivityClick(element) {

    const activityId = element.getAttribute('data-goal-id');
    const newActivity = element.getAttribute('data-start-activity');

    if (newActivity === "1") {
        startActivity(activityId);

    } else {
        // Annars omdirigera till todos
        window.location.href = `/pmg/activity/${activityId}/tasks`;
    }
}

// Starta aktivitet
function startActivity(actId) {
    openTime = new Date(); // Spara starttiden
    localStorage.setItem('start', openTime.toISOString()); // Spara starttiden i localStorage om sidan laddas om
    localStorage.setItem('active', true);
    localStorage.setItem('selectedActivityId', actId);
    window.location.href = `/pmg/focus_room/${actId}`;
}

// Stoppa aktivitet
function stopActivity() {
    closeTime = new Date(); // Spara stopptiden
    localStorage.setItem('active', false);
    localStorage.setItem('end', closeTime.toISOString()); // Spara stopptiden i localStorage om sidan laddas om

    // Kontrollera att start- och stopptiderna finns i localStorage innan de används
    const startStored = localStorage.getItem('start');
    const endStored = localStorage.getItem('end');
    const activityId = localStorage.getItem('selectedActivityId');

    if (startStored && endStored && activityId) {
        document.getElementById("start").value = new Date(startStored).toISOString().slice(0, 19).replace('T', ' ');
        document.getElementById("end").value = new Date(endStored).toISOString().slice(0, 19).replace('T', ' ');
        document.getElementById("aID").value = activityId;
    }

    document.getElementById('stopButton').style.display = 'none';
    document.getElementById('continueButton').style.display = 'none';

    // Beräkna och visa förfluten tid
    const elapsedTimeMs = closeTime - new Date(startStored);
    const elapsedTimeMin = Math.floor(elapsedTimeMs / 60000);
    saveActivity(elapsedTimeMin);
}

// Spara aktivitet
function saveActivity(time) {
    document.getElementById('completed-form').style.display = "block";
    document.getElementById('complete-form').style.display = "block";
    document.getElementById('elapsedTime').style.display = "block";
    document.getElementById("elapsedTime").value = time; // Använd rätt element-ID
    localStorage.setItem('active', false);
}

function applyActivityLayout() {
    document.getElementById('day-section').style.display = 'none';
    document.getElementById('stopButton').style.display = 'block';
    document.getElementById('continueButton').style.display = 'none';
}


function toggleTodoList(actId) {
    const todoList = document.getElementById('todo-list-' + actId);

    if (todoList.style.display === 'none' || todoList.style.display === '') {
        todoList.style.display = 'flex'; // Ändra till 'block'
    } else {
        todoList.classList.toggle('hidden');
        ;
    }

}


function expandNewStreakForm() {
    document.getElementById('new-streak-button').style.display = 'none';
    document.getElementById('new-streak-form').style.display = 'block';
}

function cancelNewStreakForm() {
    document.getElementById('new-streak-form').style.display = 'none';
    document.getElementById('new-streak-button').style.display = 'block';
}

async function fetchNewWord() {
    try {
        let response = await fetch('/pmg/get-new-word');
        let text = await response.json();
        document.getElementById('ordet-label').textContent = text;
    } catch (error) {
        console.error('Error fetching new word:', error);
    }
}

function editTitle() {
    document.getElementById('ordet-input').style.display = 'block'
    document.getElementById('ordet-label').style.display = 'none'
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

$('#goalSelect').change(function () {
    var goalId = $(this).val();
    $.ajax({
        url: '/pmg/get_activities/' + goalId,
        type: 'GET',
        success: function (response) {
            var activitySelect = $('#activitySelect');
            activitySelect.empty(); // Rensa befintliga optioner
            $.each(response, function (index, activity) {
                activitySelect.append($('<option>').val(activity.id).text(activity.name));
            });
        },
        error: function (error) {
            console.log('Error:', error);
        }
    });
});

document.addEventListener('DOMContentLoaded', function () {
    let savedOpenTime = localStorage.getItem('openTime');
    let savedActiveTimer = localStorage.getItem('active');

    if (savedOpenTime && savedActiveTimer === 'true') {
        openTime = new Date(savedOpenTime);
        if (!isNaN(openTime.getTime())) {  // Kolla om openTime är ett giltigt datum
            let selectedAct = localStorage.getItem('selectedActivityId');
            toggleTodoList(selectedAct);
            applyActivityLayout();
        } else {
            console.error('Invalid openTime:', savedOpenTime);
        }
    }
});


document.addEventListener('DOMContentLoaded', function () {

    let startaAktivitetButton = document.getElementById('startaAktivitet');
    if (startaAktivitetButton) {
        startaAktivitetButton.addEventListener('click', toggleActivityForm);
    } else {
        console.error('startaAktivitet button not found');
    }

    let stopButton = document.getElementById('stopButton');
    if (stopButton) {
        stopButton.addEventListener('click', stopActivity);
    } else {
        console.error('stopButton not found');
    }
});

function showNotification(message) {
        // Skapa en ny notifikations-div
        const notification = document.createElement('div');
        notification.className = 'notification-popup show';
        notification.innerText = message;

        // Lägg till notifikationen i dokumentet
        document.body.appendChild(notification);

        // Ta bort popup efter 7 sekunder
        setTimeout(() => {
        notification.classList.add('hide');
        setTimeout(() => notification.remove(), 500); // Vänta på transition innan den tas bort
    }, 7000);
}

function markNotificationsAsRead() {
        fetch('/pmg/notifications/mark_as_read', { method: 'POST' })
            .then(response => response.json())
            .then(data => console.log(data.message))
            .catch(error => console.error('Error marking notifications as read:', error));
    }

    // Markera som lästa efter popup visas
    setTimeout(markNotificationsAsRead, 7500); // Vänta tills alla popup-notiser har visats


document.querySelectorAll('.add-subtask-form').forEach(form => {
    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        const response = await fetch(form.action, {
            method: 'POST',
            body: new FormData(form)
        });
        if (response.ok) {
            location.reload();
        }
    });
});

