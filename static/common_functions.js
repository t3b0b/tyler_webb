var repetitions = 1;
var activity = 0;
var goal = 0;
var timeTot = 0;

function startTimer(duration, display) {
    var timer = duration, minutes, seconds;
    var interval = setInterval(function () {
        updateTimerDisplay(timer, display);
        updateAnimation(timer, duration);

        if (--timer < 0) {
            clearInterval(interval);
            display.textContent = "00:00"
            document.getElementById('stopButton').style.display = 'block'
            document.getElementById('continueButton').style.display = 'block'
        }
    }, 1000);
}
function updateTimerDisplay(timer, display) {
    var minutes = parseInt(timer / 60, 10);
    var seconds = parseInt(timer % 60, 10);
    display.textContent = (minutes < 10 ? "0" + minutes : minutes) + ":" + (seconds < 10 ? "0" + seconds : seconds);
}
function updateAnimation(currentTime, totalTime) {
    var circle = document.querySelector('circle');
    var progress = (1 - currentTime / totalTime) * 472; // 472 är det totala stroke-dasharray värdet
    circle.style.strokeDashoffset = 472 - progress;
}
function continueTimer() {
    var params = new URLSearchParams(window.location.search);
    var duration = parseInt(params.get('duration'), 10);
    var display = document.getElementById('timerDisplay');
    var circle = document.querySelector('circle');
    circle.style.animation = 'none';
    setTimeout(function() {
        circle.style.strokeDashoffset = 472;  // Ursprungligt värde
        circle.style.animation = 'anim ' + ogIntervall + 's linear forwards';
    }, 10);
    repetitions += + 1
    document.querySelector('.repetitions h2').textContent = repetitions
    startTimer(duration, display);
}
function stopTimer() {
    var params = new URLSearchParams(window.location.search);
    var duration = parseInt(params.get('duration'), 10);
    timeTot = repetitions * duration / 60
    window.close(); // Stänger popup-fönstret
    saveActivity(timeTot)
}
function startTimerFromSelection() {
    document.getElementById('activityForm').style.display = 'none'
    var duration = document.getElementById('timeSelect').value * 60; // Konverterar minuter till sekunder
    var timerURL = '/pmg/timer?duration=' + duration;
    window.open(timerURL, 'TimerWindow', 'width=400,height=400');
}
function toggleActivityForm() {
    var form = document.getElementById('activityForm');
    form.style.display = form.style.display === 'none' ? 'block' : 'none';
    document.getElementById('startaAktivitet').style.display = 'none'
}
function saveActivity (totTime){
    goal = window.opener.document.getElementById('goalSelect').value;
    activity = window.opener.document.getElementById('activitySelect').value;
    window.opener.document.getElementById('complete-form').style.display = 'block';
    window.opener.document.getElementById('aID').value = activity;
    window.opener.document.getElementById('gID').value = goal;
    window.opener.document.getElementById('score').value = totTime;
}

window.onload = function () {
    var params = new URLSearchParams(window.location.search);
    var duration = parseInt(params.get('duration'), 10);
    var display = document.getElementById('timerDisplay');
    startTimer(duration, display);
    document.getElementById('continueButton').addEventListener('click', continueTimer);
    document.getElementById('stopButton').addEventListener('click', stopTimer);
};