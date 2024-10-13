var active = false;
var activity = 0;
var goal = 0;
var openTime;
var closeTime;
//

function startActivity() {
    openTime = new Date(); // Spara starttiden
    localStorage.setItem('openTime', openTime.toISOString()); // Spara starttiden i localStorage om sidan laddas om
    localStorage.setItem('active',true);
    localStorage.setItem('goalId', document.getElementById('goalSelect').value);
    localStorage.setItem('selectedActivityId', document.getElementById('activitySelect').value);
    active = true
    activity = localStorage.getItem('selectedActivityId')
    toggleTodoList(activity);

    // Dölja startknappen och visa stop-knappen
    applyActivityLayout()
}

function stopActivity() {
    localStorage.removeItem('active');
    localStorage.setItem('active', false);

    closeTime = new Date(); // Spara stopptiden

    localStorage.setItem('closeTime', closeTime.toISOString()); // Spara stopptiden i localStorage om sidan laddas om

    // Beräkna skillnaden mellan start- och stopptiden
    let elapsedTime = (closeTime - openTime) / 1000 / 60; // Tidsdifferens i minuter
    elapsedTime = Math.round(elapsedTime); // Avrunda till närmsta minut

    document.getElementById('startaAktivitet').style.display = 'none';
    document.getElementById('start-timer').style.display = 'none';
    document.getElementById('day-section').style.display = 'grid';

    // Dölja stop-knappen och visa startknappen för att återställa aktiviteten
    document.getElementById('stopButton').style.display = 'none';
    document.getElementById('continueButton').style.display = 'block';
    // Spara aktivitetstiden eller skicka till servern om det behövs
    saveActivity(elapsedTime);

}

function saveActivity(elapsedTime) {
    document.getElementById("gID").value = localStorage.getItem('goalId');
    document.getElementById("aID").value = localStorage.getItem('selectedActivityId');
    document.getElementById('score-disp').textContent = elapsedTime;
    document.getElementById('score').value = elapsedTime;
    document.getElementById("start").value = new Date(openTime).toISOString().slice(0, 19).replace('T', ' ');
    document.getElementById("end").value = new Date(closeTime).toISOString().slice(0, 19).replace('T', ' ');

    activity = localStorage.getItem('selectedActivityId')
    toggleTodoList(activity);

    // Skicka formuläret om det är ett submit-formulär, annars kan du använda AJAX här
    document.getElementById('complete-form').style.display = "block"; // Exempel på form-submission
    localStorage.removeItem('active');
    localStorage.removeItem('openTime');
    location.reload()
}

function applyActivityLayout() {
    document.getElementById('day-section').style.display = 'none';
    document.getElementById('stopButton').style.display = 'block';
    document.getElementById('continueButton').style.display = 'none';
}


    // Kör funktionen när sidan laddas


function toggleTodoList(actId) {
const todoList = document.getElementById('todo-list-' + actId);

if (todoList.style.display === 'none' || todoList.style.display === '') {
    todoList.style.display = 'flex'; // Ändra till 'block'
} else {
    todoList.style.display = 'none';
}

}

function toggleEditMode(button) {
    const deleteButtons = document.querySelectorAll('.delete-button');
    deleteButtons.forEach(btn => {
        btn.style.display = btn.style.display === 'none' || btn.style.display === '' ? 'inline-block' : 'none';
    });
    button.textContent = button.textContent === '🖉' ? '✔' : '🖉';
}

function formatDateForMySQL(date) {
    return date.toISOString().slice(0, 19).replace('T', ' ');
}

function deleteActivity(activityId) {
    if (confirm('Är du säker på att du vill radera denna aktivitet?')) {
        fetch('/pmg/delete-activity/' + activityId, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ activityId: activityId })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Aktiviteten har raderats!');
                location.reload(); // Ladda om sidan för att uppdatera listan
            } else {
                alert('Ett fel inträffade. Försök igen.');
            }
        });
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

function deleteStreak(streakId) {
    if (confirm('Är du säker på att du vill radera denna streak?')) {
        fetch('/pmg/delete-streak/' + streakId, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ streakId: streakId })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Streaken har raderats!');
                location.reload(); // Ladda om sidan för att uppdatera listan
            } else {
                alert('Ett fel inträffade. Försök igen.');
            }
        });
    }
}

function getCSRFToken() {
    return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
}


function fetchNewWord() {
fetch('/pmg/get-new-word')
    .then(response => response.json())
    .then(text => {
        var wordLabel = document.getElementById('ordet-label');
        wordLabel.textContent = text;  // 'text' ska vara den rena strängen från JSON-svaret
    })
    .catch(error => console.error('Error fetching new word:', error));
}

function editTitle() {
    document.getElementById('ordet-input').style.display = 'block'
    document.getElementById('ordet-label').style.display = 'none'
}

function toggleActivityForm() {
    var form = document.getElementById('activityForm');
    if (form) {
        form.style.display = form.style.display = 'block';
        document.getElementById('startaAktivitet').style.display = 'none';
        document.getElementById('start-timer').style.display = 'block';

    } else {
        console.error('Activity form element not found');
    }
}

function animateCheck(event, form) {
    event.preventDefault();
    const checkbox = form.querySelector('.checkbox');
    const background = form.querySelector('.background');

    checkbox.classList.add('animate-check');
    background.classList.add('animate-bg');

    setTimeout(() => {
        form.submit();
    }, 1000);
}

function updateTaskStatus(taskId, isCompleted) {
    fetch('/pmg/update-task-status/' + taskId, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()  // Använd om du har CSRF-skydd
        },
        body: JSON.stringify({
            completed: isCompleted
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('Task updated successfully');
        } else {
            console.error('Error updating task:', data.error);
        }
    })
    .catch(error => {
        console.error('Network error:', error);
    });
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

document.addEventListener('DOMContentLoaded', function() {
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


document.addEventListener('DOMContentLoaded', function() {

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


document.getElementById('stopButton').addEventListener('click', stopActivity);
document.getElementById('startaAktivitet').addEventListener('click', toggleActivityForm);