var activityId; // Se till att denna variabel är korrekt inställd
var openTime;
var closeTime;

// Starta aktivitet
function startActivity() {
    openTime = new Date(); // Spara starttiden
    localStorage.setItem('start', openTime.toISOString()); // Spara starttiden i localStorage om sidan laddas om
    localStorage.setItem('active', true);
    activityId = document.getElementById('activitySelect').value;
    localStorage.setItem('selectedActivityId', activityId);
    window.location.href = `/pmg/focus_room/${activityId}`;
}

// Stoppa aktivitet
function stopActivity() {
    closeTime = new Date(); // Spara stopptiden
    localStorage.setItem('active', false);
    localStorage.setItem('end', closeTime.toISOString()); // Spara stopptiden i localStorage om sidan laddas om

    // Kontrollera att start- och stopptiderna finns i localStorage innan de används
    const startStored = localStorage.getItem('start');
    const endStored = localStorage.getItem('end');
    if (startStored && endStored) {
        document.getElementById("start").value = new Date(startStored).toISOString().slice(0, 19).replace('T', ' ');
        document.getElementById("end").value = new Date(endStored).toISOString().slice(0, 19).replace('T', ' ');
    }

    document.getElementById("aID").value = localStorage.getItem('selectedActivityId');
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


    // Kör funktionen när sidan laddas


function toggleTodoList(actId) {
const todoList = document.getElementById('todo-list-' + actId);

if (todoList.style.display === 'none' || todoList.style.display === '') {
    todoList.style.display = 'flex'; // Ändra till 'block'
} else {
    todoList.classList.toggle('hidden');;
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
                'Content-Type': 'application/json',
            }
        })
        .then(response => {
            if (response.ok) {
                return response.text();  // Hämta svaret som text
            } else {
                throw new Error('Request failed with status ' + response.status);
            }
        })
        .then(text => {
            alert(text);  // Visa svaret som är antingen "Success", "Activity not found" eller annat
            location.reload();
        })
        .catch(error => {
            console.error('Network error:', error);
            alert('Ett nätverksfel inträffade. Försök igen.');
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