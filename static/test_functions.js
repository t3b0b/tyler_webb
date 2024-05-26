var interval;
var openTime, closeTime;
var repetitions = 0;

function startTimer(duration, display) {
    var timer = duration, minutes, seconds;
    openTime = new Date(); // Starta tiden när timern börjar
    interval = setInterval(function () {
        minutes = parseInt(timer / 60, 10);
        seconds = parseInt(timer % 60, 10);

        minutes = minutes < 10 ? "0" + minutes : minutes;
        seconds = seconds < 10 ? "0" + seconds : seconds;

        display.textContent = minutes + ":" + seconds;

        if (--timer < 0) {
            clearInterval(interval);
            display.textContent = "00:00";
            document.getElementById('activityForm').style.display = 'none'
            document.getElementById('stopButton').style.display = 'block';
            document.getElementById('continueButton').style.display = 'block';
        }
    }, 1000);
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

function continueTimer() {
    var display = document.getElementById('start-timer');
    var duration = document.getElementById('timeSelect').value * 60;
    document.getElementById('activityForm').style.display = 'flex'
    document.getElementById('stopButton').style.display = 'none';
    document.getElementById('continueButton').style.display = 'none';
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
    clearInterval(interval); // Stoppa timern
    document.getElementById('activityForm').style.display = 'flex'
    document.getElementById('time-less').style.display = 'none'
    document.getElementById('write-on-time').style.display = 'block'
    document.getElementById('stopButton').style.display = 'none';
    document.getElementById('continueButton').style.display = 'none';
    closeTime = new Date(); // Stoppa tiden när timern stoppas
    console.log(`Timer stängd vid: ${closeTime}`);
    saveActivity();
}

function startTimerFromSelection() {
    var duration = document.getElementById('timeSelect').value * 60; // Konverterar minuter till sekunder
    var display = document.getElementById('start-timer');
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

    startTimer(duration, display);
}
