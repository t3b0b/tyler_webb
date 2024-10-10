let repetitions = 1;
let timeEnded = false;
let activeTimer = false;
var activity = 0;
var goal = 0;
let openTime;
let closeTime;

//
function startTimerFromSelection() {
    var duration = document.getElementById('timeSelect').value * 60; // Konverterar minuter till sekunder
    var display = document.getElementById('continueButton');
    openTime = new Date(); // Starta tiden när timern börjar

    let active = true
    goal = document.getElementById('goalSelect')?.value;
    activity = document.getElementById('activitySelect')?.value;

    document.getElementById('aID').value = activity;
    document.getElementById('gID').value = goal;

    localStorage.setItem('activeTimer',true);
    localStorage.setItem('openTime', openTime.toISOString());
    localStorage.setItem('goalId', document.getElementById('goalSelect').value);
    localStorage.setItem('selectedActivityId', document.getElementById('activitySelect').value);
    localStorage.setItem('duration', duration);
    localStorage.setItem('timerStopped', 'false');
    const selectedAct = document.getElementById('activitySelect').value;
    const todoList = document.getElementById('todo-list-' + selectedAct);

    if (todoList) {
        todoList.style.display = 'block';  // Ändra till 'block' för att visa listan
    }
    if (selectedAct !== '----') {
        startTimer(duration, display); // Starta timern
        applyActivityLayout();
    } else {
        alert('Please select a goal before starting the activity.');
    }
}

function applyActivityLayout() {

    document.getElementById('day-section').style.display = 'none';
    document.getElementById('stopButton').style.display = 'block';
    document.getElementById('continueButton').style.display = 'block';
}

function startTimer(duration, display) {
    var timer = duration, minutes, seconds;
    timeEnded = false;
    var interval = setInterval(function () {
        updateTimerDisplay(timer, display);
        if (--timer < 0) {
            clearInterval(interval);
            if (display) {
                display.textContent = "00:00";
            }
            timeEnded = true;
            document.getElementById('stopButton').style.display = 'block';
            document.getElementById('continueButton').style.display = 'block';
            document.getElementById('continueButton').textContent = 'Continue';
        }
    }, 1000);
}

function continueTimer() {
    if (timeEnded) {
        var display = document.getElementById('continueButton');
        var duration = document.getElementById('timeSelect').value * 60;
        document.getElementById('start-timer').style.display = 'none'
        document.getElementById('stopButton').style.display = 'block';
        document.getElementById('continueButton').style.display = 'block';
        repetitions += 1;
        var repetitionsDisplay = document.querySelector('.repetitions h2');
        if (repetitionsDisplay) {
            repetitionsDisplay.textContent = repetitions;
        } else {
            console.error('Repetitions display element not found');
        }
        startTimer(duration, display);
    }
}

function stopTimer() {
    if (timeEnded) {
        var timerStopped = localStorage.getItem('timerStopped'); // Kolla om timern har stoppats
        activeTimer = false;
        localStorage.removeItem('activeTimer');
        localStorage.setItem('activeTimer', activeTimer);

        const selectedAct = document.getElementById('activitySelect').value;
        const todoList = document.getElementById('todo-list-' + selectedAct);

        if (todoList) {
            todoList.style.display = 'none';  // Ändra till 'block' för att visa listan
        }
        document.getElementById('startaAktivitet').style.display = 'none';
        document.getElementById('start-timer').style.display = 'none';
        document.getElementById('stopButton').style.display = 'none';
        document.getElementById('continueButton').style.display = 'none';
        document.getElementById('day-section').style.display = 'grid';

        localStorage.setItem('timerStopped', 'true'); // Flagga för att markera att timern har stoppats

        saveActivity()
    }
}

function saveActivity() {
    closeTime = new Date(); // Stoppa tiden när timern stoppas
    goal = document.getElementById('goalSelect')?.value;
    activity = document.getElementById('activitySelect')?.value;
    document.getElementById('aID').value = activity;
    document.getElementById('gID').value = goal;
    document.getElementById("start").value = new Date(openTime).toISOString().slice(0, 19).replace('T', ' ');
    document.getElementById("end").value = new Date(closeTime).toISOString().slice(0, 19).replace('T', ' ');
    let elapsedTime = (closeTime - openTime) / 1000 / 60; // Konvertera millisekunder till minuter
    elapsedTime = Math.round(elapsedTime);
    document.getElementById('score-disp').textContent = elapsedTime;
    document.getElementById('score').value = elapsedTime;
    document.getElementById('complete-form').style.display = 'block';
}

function updateTimerDisplay(timer, display) {
    var minutes = parseInt(timer / 60, 10);
    var seconds = parseInt(timer % 60, 10);
    if (display) {
        display.textContent = (minutes < 10 ? "0" + minutes : minutes) + ":" + (seconds < 10 ? "0" + seconds : seconds);
    } else {
        console.error('Display element not found');
    }
}

function toggleTodoList(button, goalId) {
const todoList = document.getElementById('todo-list-' + goalId);
if (todoList.style.display === 'none' || todoList.style.display === '') {
    todoList.style.display = 'block'; // Ändra till 'block'
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

function deleteGoal(Button, goalId) {
    if (confirm('Är du säker på att du vill radera detta mål?')) {
        const goal = document.getElementById('deleteGoal-' + goalId).value;
        fetch('/pmg/deleteGoal/' + goalId, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()  // Lägg till CSRF-token i headers
            },
            body: JSON.stringify({ goal: goal })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Målet har raderats!');
                location.reload(); // Ladda om sidan för att uppdatera listan
            } else {
                alert('Ett fel inträffade. Försök igen.');
            }
        })
        .catch(error => {
            console.error('Fel vid borttagning av mål:', error);
            alert('Ett nätverksfel inträffade. Försök igen.');
        });
    }
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
        form.style.display = form.style.display === 'none' ? 'block' : 'none';
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

$(document).ready(function () {
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
});

window.addEventListener('load', function() {
    var ActInProg = localStorage.getItem('activeTimer');
    var savedOpenTime = localStorage.getItem('openTime');
    var selectedGoalId = localStorage.getItem('goalId');
    var selectedActivityId = localStorage.getItem('selectedActivityId');
    var savedDuration = localStorage.getItem('duration');
    var timerStopped = localStorage.getItem('timerStopped'); // Kolla om timern har stoppats

    // Kontrollera om alla nödvändiga värden finns
    if (ActInProg && savedOpenTime && selectedGoalId && selectedActivityId && savedDuration) {
        openTime = new Date(savedOpenTime);

        // Beräkna hur mycket tid som har gått
        let now = new Date();
        let elapsedTime = Math.floor((now - openTime) / 1000); // Tid i sekunder
        let remainingTime = savedDuration - elapsedTime;

        // Om tid kvar, återställ aktiviteten
        if (remainingTime > 0) {
            let display = document.getElementById('continueButton');
            document.getElementById('goalSelect').value = selectedGoalId;
            document.getElementById('activitySelect').value = selectedActivityId;

            // Återställ layout för en pågående aktivitet
            applyActivityLayout();
            todoList = document.getElementById('todo-list-' + selectedActivityId);

            if (todoList) {
                todoList.style.display = 'flex';  // Ändra till 'block' för att visa listan
            }
            // Återstarta timern med återstående tid
            startTimer(remainingTime, display);
        } else let todoList;
        if (remainingTime <= 0 && timerStopped !== 'true') {
            console.log("Tiden har gått ut, men timern har inte stoppats. Återställ aktiviteten.");

            // Här kan du återställa aktiviteten, om du har en process för detta
            document.getElementById('goalSelect').value = selectedGoalId;
            document.getElementById('activitySelect').value = selectedActivityId;

            // Återställ layout för en pågående aktivitet
            applyActivityLayout();
            let todoList = document.getElementById('todo-list-' + selectedActivityId);

            if (todoList) {
                todoList.style.display = 'flex';  // Ändra till 'block' för att visa listan
            }

            // Rensa localStorage för att börja om
            localStorage.clear();
            console.log("Aktiviteten återställd och lagringen rensad.");

            // Villkor 3: Om tiden är slut och timern har stoppats, ge möjlighet att återuppta för att spara aktivitet och ladda om sidan
        } else if (remainingTime <= 0 && timerStopped === 'true') {
            console.log("Tiden är slut och timern har stoppats. Du kan återuppta aktiviteten för att spara.");

            // Visa knappen för att slutföra eller återuppta aktiviteten
            var display = document.getElementById('continueButton');
            display.style.display = "block"; // Visa knappen för att återuppta aktiviteten

            // När användaren klickar på knappen kan du t.ex. spara aktiviteten och sedan ladda om sidan
            display.addEventListener('click', function () {
                // Här kan du lägga till logik för att spara den slutförda aktiviteten

                // Ladda om myday.html
                window.location.href = "myday.html"; // Ladda om sidan
            });
        }
    }
});

document.addEventListener('DOMContentLoaded', function() {
    var startaAktivitetButton = document.getElementById('startaAktivitet');
    if (startaAktivitetButton) {
        startaAktivitetButton.addEventListener('click', toggleActivityForm);
    } else {
        console.error('startaAktivitet button not found');
    }

    var continueButton = document.getElementById('continueButton');
    var stopButton = document.getElementById('stopButton');

    if (continueButton) {
        continueButton.addEventListener('click', continueTimer);
    } else {
        console.error('continueButton not found');
    }

    if (stopButton) {
        stopButton.addEventListener('click', stopTimer);
    } else {
        console.error('stopButton not found');
    }
});


document.getElementById('continueButton').addEventListener('click', continueTimer);
document.getElementById('stopButton').addEventListener('click', stopTimer);
document.getElementById('startaAktivitet').addEventListener('click', toggleActivityForm);