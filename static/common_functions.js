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
    var openerDoc = window.opener.document;
    if (!openerDoc) {
        console.error('Kan inte hitta huvudfönstret.');
        return;
    }

    console.log("Hämtar målet och aktiviteten från huvudfönstret");
    goal = openerDoc.getElementById('goalSelect')?.value;
    activity = openerDoc.getElementById('activitySelect')?.value;

    if (!goal || !activity) {
        console.error('Kan inte hitta målet eller aktiviteten.');
        return;
    }

    console.log("Mål:", goal);
    console.log("Aktivitet:", activity);

    var completeForm = openerDoc.getElementById('complete-form');
    if (!completeForm) {
        console.error('Kan inte hitta complete-form.');
        return;
    }

    completeForm.style.display = 'block';
    openerDoc.getElementById('aID').value = activity;
    openerDoc.getElementById('gID').value = goal;
    let elapsedTime = (closeTime - openTime) / 1000 / 60; // Konvertera millisekunder till minuter
    openerDoc.getElementById('score').value = elapsedTime;

    console.log(`Activity saved with goal: ${goal}, activity: ${activity}, elapsedTime: ${elapsedTime}`);
}

function continueTimer() {
    var params = new URLSearchParams(window.location.search);
    var duration = parseInt(params.get('duration'), 10);
    var display = document.getElementById('timerDisplay');
    var circle = document.querySelector('circle');
    if (circle) {
        circle.style.animation = 'none';
        setTimeout(function() {
            circle.style.strokeDashoffset = 472;  // Ursprungligt värde
            circle.style.animation = 'anim ' + duration + 's linear forwards';
        }, 10);
    }
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
    var duration = parseInt(params.get('duration'), 10);
    timeTot = repetitions * duration / 60;
    closeTime = new Date();
    window.close(); // Stänger popup-fönstret
    console.log(`Timer stängd vid: ${closeTime}`);
    saveActivity(timeTot);
}

function startTimerFromSelection() {
    document.getElementById('activityForm').style.display = 'none';
    var duration = document.getElementById('timeSelect').value * 60; // Konverterar minuter till sekunder
    var timerURL = '/pmg/timer?duration=' + duration;
    window.open(timerURL, 'TimerWindow', 'width=400,height=400');
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


