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
        const selectedGoalId = document.getElementById('goalSelect').value;

        const todoList = document.getElementById('todo-list-' + selectedGoalId);
        if (todoList) {
            todoList.style.display = 'none'; // Visa att-göra-listan om den finns
        }
        const daySection = document.getElementById('day-section');
        if (daySection) {
            daySection.style.display = 'grid';
            daySection.style.gridTemplateColumns = '2fr 1fr 2fr'; // Justera kolumn-layout
            daySection.style.marginInline = '5%';
            daySection.style.gap = '20px';
            daySection.style.justifycontent ='space-evenly';
            daySection.style.padding = '20px';
            daySection.style.boxsizing = 'border-box';
        }

        const completeForm = document.getElementById('complete-form');
        if (completeForm) {
            completeForm.style.display = 'block';
            }
        document.getElementById('date-section').style.display = 'block';
        // Visa goal-section, score-section och streak-section igen

        const scoreSection = document.getElementById('score-section');
                scoreSection.style.width = '100%';
                scoreSection.style.fontSize = '22px';
                scoreSection.style.fontWeight = 'bold';
                scoreSection.style.lineHeight = '50px';
                scoreSection.style.textAlign = 'center';
                scoreSection.style.display = 'block';

       const sections = ['goal-section', 'streak-section'];
        sections.forEach(sectionId => {
            const section = document.getElementById(sectionId);
            if (section) {
                section.style.display = 'flex';
                section.style.justifyContent = 'space-evenly';
                section.style.flexDirection = 'column';
                section.style.width = '2fr';
                section.style.padding = '5px';
            }
        });
        // Dölj knapparna för "Stop" och "Continue"
        document.getElementById('stopButton').style.display = 'none';
        document.getElementById('continueButton').style.display = 'none';
        // Spara sluttiden för aktiviteten
        closeTime = new Date(); // Stoppa tiden när timern stoppas
        // Anropa funktionen som sparar aktiviteten
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

    display.style.backgroundColor = 'green';
    document.getElementById('day-section').style.display = 'flex';
    document.getElementById('day-section').style.flexDirection = 'column';
    document.getElementById('date-section').style.display = 'none';
    document.getElementById('goal-section').style.display = 'none';
    document.getElementById('score-section').style.display = 'none';
    document.getElementById('streak-section').style.display = 'none';
    document.getElementById('activityForm').style.display = 'none';
    document.getElementById('stopButton').style.display = 'block';
    document.getElementById('continueButton').style.display = 'block';

    // Hämta valt mål
    const selectedGoalId = document.getElementById('goalSelect').value;
    const todoList = document.getElementById('todo-list-' + selectedGoalId);

    // Visa att-göra-listan för det valda målet
    if (todoList) {
        todoList.style.display = 'block';  // Ändra till 'block' för att visa listan
    }

    // Kolla att ett mål är valt
    if (selectedGoalId !== '----') {
        // Ladda tasks för det valda målet
        loadTasksForGoal(selectedGoalId);
        startTimer(duration, display); // Starta timern
    } else {
        alert('Please select a goal before starting the activity.');
    }
}


// Funktion för att hämta tasks för ett valt mål
function loadTasksForGoal(goalId) {
    // Gör en AJAX-förfrågan till servern för att hämta tasks för valt mål
    fetch(`/get_tasks/${goalId}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
                return;
            }

            // Töm tasks-listan innan nya tasks laddas in
            const taskList = document.getElementById('todo-list');
            taskList.innerHTML = '';  // Tömmer listan

            // Lägg till varje task i listan
            data.tasks.forEach(task => {
                const listItem = document.createElement('li');
                listItem.innerHTML = `
                    <input type="checkbox" ${task.completed ? 'checked' : ''}> ${task.name}
                `;
                taskList.appendChild(listItem);
            });
        })
        .catch(error => {
            console.error('Error fetching tasks:', error);
        });
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