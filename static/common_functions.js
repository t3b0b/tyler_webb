let repetitions = 1;
let activity = 0;
let goal = 0;
let timeTot = 0;
let openTime;
let closeTime;

function startTimer(duration, display) {
    var timer = duration, minutes, seconds;
    var interval = setInterval(function () {
        updateTimerDisplay(timer, display);
        updateAnimation(timer, duration);

        if (--timer < 0) {
            clearInterval(interval);
            if (display) {
                display.textContent = "00:00";
            }
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

function updateAnimation(currentTime, totalTime) {
    var circle = document.querySelector('circle');
    if (circle) {
        var progress = (1 - currentTime / totalTime) * 472; // 472 är det totala stroke-dasharray värdet
        circle.style.strokeDashoffset = 472 - progress;
    } else {
        console.error('Circle element not found');
    }
}
function saveActivity(totTime) {
    goal = document.getElementById('goalSelect')?.value;
    activity = document.getElementById('activitySelect')?.value;
    document.getElementById('aID').value = activity;
    document.getElementById('gID').value = goal;
    let elapsedTime = (closeTime - openTime) / 1000 / 60; // Konvertera millisekunder till minuter
    elapsedTime = Math.round(elapsedTime);
    document.getElementById('score').value = elapsedTime;
    document.getElementById('start-timer').textContent = elapsedTime + ' P';
    console.log(`Activity saved with goal: ${goal}, activity: ${activity}, elapsedTime: ${elapsedTime}`);
}

 document.getElementById('startaAktivitet').addEventListener('click', toggleActivityForm);

function continueTimer() {
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

function stopTimer() {
    var params = new URLSearchParams(window.location.search);
    var duration = document.getElementById('timeSelect').value;
    timeTot = repetitions * duration / 60;
    closeTime = new Date();
    window.close(); // Stänger popup-fönstret
    console.log(`Timer stängd vid: ${closeTime}`);
    saveActivity(timeTot);
}

function startTimerFromSelection() {
    var duration = document.getElementById('timeSelect').value * 60; // Konverterar minuter till sekunder
    var display = document.getElementById('continueButton');
        var continueButton = document.getElementById('continueButton');
        if (continueButton) {
            continueButton.addEventListener('click', continueTimer);
        } else {
            console.error('Continue button not found');
        }
        var stopButton = document.getElementById('stopButton');
        if (stopButton) {
            stopButton.addEventListener('click', stopTimer);
        } else {
            console.error('Stop button not found');
        }
    display.style.backgroundColor = 'green'
    document.getElementById('activityForm').style.display='none';
    document.getElementById('stopButton').style.display = 'block';
    document.getElementById('continueButton').style.display = 'block';
    startTimer(duration, display);
}

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

