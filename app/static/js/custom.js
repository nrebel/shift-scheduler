// custom.js

/*$(document).ready(function() {
    var calendarEl = document.getElementById('calendar');
    var calendar = new FullCalendar.Calendar(calendarEl, {
        plugins: ['dayGrid'],
        initialView: 'dayGridMonth'
    });
    calendar.render();

    $('#userScheduleForm').submit(function(e) {
        e.preventDefault();  // This line is crucial to prevent form from actual submission

        var userId = $('#userSelect').val();
        var year = $('#yearSelect').val();
        var month = $('#monthSelect').val();

        // FullCalendar month view adjustment
        calendar.gotoDate(new Date(year, month - 1, 1));

        // AJAX request to server
        $.ajax({
            url: "{{ url_for('fetch_user_schedule') }}",
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify({ user: userId, year: year, month: month }),
            success: function(data) {
                calendar.removeAllEvents();
                data.dates.forEach(function(date) {
                    calendar.addEvent({
                        title: 'Available',
                        start: date,
                        allDay: true,
                        backgroundColor: 'green',  // visually distinct color for availability
                        borderColor: 'green'
                    });
                });
            },
            error: function(xhr) {
                console.error('Error fetching data: ' + xhr.responseText);
            }
        });
    });
});
*/