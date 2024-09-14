let repetitions = 1;
let timeEnded = false;
let activity = 0;
let goal = 0;
let openTime;
let closeTime;

function startTimer(duration, display) {
    var timer = duration, minutes, seconds;
    timeEnded = false;
    openTime = new Date(); // Starta tiden när timern börjar
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

function updateTimerDisplay(timer, display) {
    var minutes = parseInt(timer / 60, 10);
    var seconds = parseInt(timer % 60, 10);
    if (display) {
        display.textContent = (minutes < 10 ? "0" + minutes : minutes) + ":" + (seconds < 10 ? "0" + seconds : seconds);
    } else {
        console.error('Display element not found');
    }
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
        document.getElementById('complete-form').style.display = 'block'
        document.getElementById('stopButton').style.display = 'none';
        document.getElementById('continueButton').style.display = 'none';
        closeTime = new Date(); // Stoppa tiden när timern stoppas
        saveActivity();
    }
}

function formatDateForMySQL(date) {
    return date.toISOString().slice(0, 19).replace('T', ' ');
}

function saveActivity() {
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
    document.getElementById('start-timer').textContent = elapsedTime + 'xp';
    console.log(`Activity saved with goal: ${goal}, activity: ${activity}, elapsedTime: ${elapsedTime}`);
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

function startTimerFromSelection() {
    var duration = document.getElementById('timeSelect').value * 60; // Konverterar minuter till sekunder
    var display = document.getElementById('continueButton');
    display.style.backgroundColor = 'green'
    document.getElementById('activityForm').style.display='none';
    document.getElementById('stopButton').style.display = 'block';
    document.getElementById('continueButton').style.display = 'block';
    startTimer(duration, display);
}
    // Hämta den valda aktiviteten

function toggleActivityForm() {
    var form = document.getElementById('activityForm');
    if (form) {
        form.style.display = form.style.display === 'none' ? 'block' : 'none';
        document.getElementById('startaAktivitet').style.display = 'none';
    } else {
        console.error('Activity form element not found');
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
function fetchNewWord() {
fetch('/get-new-word')
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


document.getElementById('continueButton').addEventListener('click', continueTimer);
document.getElementById('stopButton').addEventListener('click', stopTimer);
document.getElementById('startaAktivitet').addEventListener('click', toggleActivityForm);