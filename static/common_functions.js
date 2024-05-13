var interval;
var ogIntervall = 0;
var repetitions = 1;
var activity = 0;
var goal = 0;
function startTimer(duration, display) {
    document.getElementById('activityForm').style.display = 'none'
    clearInterval(interval);  // Rensar tidigare intervaller för att förhindra dubbla timers
    var timer = duration, minutes, seconds;
    interval = setInterval(function () {
        minutes = parseInt(timer / 60, 10);
        seconds = parseInt(timer % 60, 10);

        minutes = minutes < 10 ? "0" + minutes : minutes;
        seconds = seconds < 10 ? "0" + seconds : seconds;

        display.textContent = minutes + ":" + seconds;

        if (--timer < 0) {
            clearInterval(interval);
            display.textContent = "00:00";
            document.getElementById('stopButton').style.display = 'block';
            document.getElementById('continueButton').style.display = 'block';
            document.getElementById('activityForm').style.display = 'none';
        }
    }, 1000);
}
function continueTimer() {
    var display = document.querySelector('.circle span'); // Antag att tiden visas här
    repetitions += + 1
    document.querySelector('.repetitions h2').textContent = repetitions
    startTimer(ogIntervall, display); // Fortsätt timern
}
function stopTimer() {
    var timeTot = repetitions * (ogIntervall/60)
    document.getElementById('complete-form').style.display = 'block';
    document.getElementById('aID').value = activity;
    document.getElementById('gID').value = goal;
    document.getElementById('score').value = timeTot;
}
function startTimerFromSelection() {
    var duration = document.getElementById('timeSelect').value * 60; // Konverterar minuter till sekunder
    goal = document.getElementById('goalSelect').value;
    activity = document.getElementById('activitySelect').value;
    ogIntervall = duration
    var display = document.querySelector('.circle span'); // Förutsätter att tiden ska visas här
    if (document.getElementById('activityForm').style.display === 'none') {
        toggleActivityForm(); // Visar formen om den är dold
    }
    startTimer(parseInt(duration), display); // Startar timern
    }
function toggleActivityForm() {
    var form = document.getElementById('activityForm');
    form.style.display = form.style.display === 'none' ? 'block' : 'none';
    document.getElementById('startaAktivitet').style.display = 'none'
}