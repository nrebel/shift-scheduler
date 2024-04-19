from flask import render_template, redirect, session, url_for, flash, request, jsonify, session
from flask_login import LoginManager, current_user, login_user, logout_user, login_required

from urllib.parse import urlparse
import pulp as pl

from . import app, db
from .models import User, get_shift_model, initialize_shift_table
from .forms import LoginForm, RegistrationForm, ShiftPreferenceForm
from datetime import datetime
import json

from calendar import monthrange
from sqlalchemy import inspect

@app.route('/')
@app.route('/index')
@login_required
def index():
    return render_template('index.html', title='Home')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        session["user"] = form.username.data  # This is the correct way to access the field's data

        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/schedule', methods=['GET', 'POST'])
@login_required
def schedule():
    selected_year = datetime.now().year
    selected_month = datetime.now().month
    if request.method == 'POST':
        # Try to parse the JSON data sent from the client
        try:
            data = request.get_json(force=True)  # Using force=True to ensure parsing regardless of MIME type
            selected_dates = data['selectedDates']
            year, month = datetime.now().year, datetime.now().month

            # Dynamically get or create the shift model for the current month and year
            ShiftModel = get_shift_model(year, month)
            initialize_shift_table(ShiftModel, current_user.username, year, month, selected_dates)

            return jsonify({'status': 'success', 'message': 'Shift preferences updated successfully.'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 400

    # If it's a GET request, just render the template
    return render_template('schedule.html')

@app.route('/update_preferences', methods=['POST'])
@login_required
def update_preferences():
    data = request.get_json(force=True)  # ensures JSON format even if header is not set
    print(f"data['dates']: {data['dates']}")
    selected_dates = data['dates'] # .split(',')
    year = data['year']
    month = data['month']
    minshifts = data['minShifts']
    maxshifts = data['maxShifts']
    num_days = (datetime(year, month % 12 + 1, 1) - datetime(year, month, 1)).days

    print(f"data: {data}, selected_dates: {selected_dates}, year: {year}, month: {month}.")
    ShiftModel = get_shift_model(year, month)
    existing_entry = ShiftModel.query.filter_by(username=current_user.username, year=year, month=month).first()

    if not existing_entry:
        new_entry = ShiftModel(username=current_user.username, year=year, month=month)
        db.session.add(new_entry)
    else:
        new_entry = existing_entry

    # Reset all days
    for day in range(1, num_days):  # assuming max days in a month is 31
        setattr(new_entry, f'day_{day}', False)

    # Set selected days
    for day in selected_dates:
        print(f"[dbg] day: {day}")
        if day:
            day_num = int(day.split('-')[-1])  # extracting day from 'YYYY-MM-DD'
            setattr(new_entry, f'day_{day_num}', True)

    setattr(new_entry, 'min_shifts', minshifts)
    setattr(new_entry, 'max_shifts', maxshifts)

    db.session.commit()
    return jsonify(success=True, message="Preferences successfully updated!")

@app.route("/preferences", methods=['GET', 'POST'])
@login_required
def preferences():
    form = ShiftPreferenceForm()
    if form.validate_on_submit():
        # Now using form.selected_days instead of form.available_days
        selected_days = form.selected_days.data  
        print("selected days: ",selected_days)
        
        flash('Your shift preferences have been updated.', 'success')
        return redirect(url_for('preferences'))
    return render_template('preferences.html', title='Shift Preferences', form=form)

@app.route("/updatepreferences", methods=['POST'])
@login_required
def updatepreferences():
    data = request.get_json()
    print("data days: ", data)
    print("user: ", session["user"])
    year, month, shift_days = get_days_for_shift(data)
    minshifts = data['minshifts']
    maxshifts = data['maxshifts']
    base_table = get_shift_model(year, month)
    initialize_shift_table(base_table, session["user"], year=year, month=month, true_days=shift_days, minshifts=minshifts, maxshifts=maxshifts)
    return render_template('updatepreferences.html', title='View Shift Preferences', data=data)

def get_days_for_shift(json_data):
    # Initialize the list to hold day numbers
    day_numbers = []

    # Extract the date string from JSON data and split into list
    selected_days_str = json_data['data']
    selected_dates = selected_days_str.split(',')

    # Process the first date outside the loop to get the common year and month
    if selected_dates:
        first_date = datetime.strptime(selected_dates[0], '%Y-%m-%d')
        year = first_date.year
        month = first_date.month

        # Now process all dates to extract day numbers
        for date_str in selected_dates:
            day = datetime.strptime(date_str, '%Y-%m-%d').day
            day_numbers.append(day)

        return year, month, day_numbers
    else:
        return None, None, []  # Return None types if the list is empty
    
@app.route('/view_schedule', methods=['GET', 'POST'])
@login_required
def view_schedule():
    users = User.query.all()
    current_year = datetime.now().year
    current_month = datetime.now().month if request.method == 'GET' else int(request.form.get('month'))

    # These defaults handle POST requests where the form is resubmitted and the year or month might be changed
    selected_user_id = int(request.form.get('user', users[0].id if users else None))
    selected_year = current_year # int(request.form.get('year', current_year))
    selected_month = int(request.form.get('month', current_month))

    return render_template('view_schedule.html', users=users,
                           current_year=current_year, current_month=current_month,
                           selected_user_id=selected_user_id,
                           selected_year=selected_year,
                           selected_month=selected_month)

@app.route('/fetch_user_schedule', methods=['POST', 'GET'])
@login_required
def fetch_user_schedule():
    try:
        data = request.get_json()
        print(data)
        user_name = data['user']
        year = int(data['year'])
        month = int(data['month'])  # JavaScript months are 0-indexed (0 for January)

        print(f"data: {data}, user_name: {user_name}, year: {year}, month: {month}.")

        ShiftModel = get_shift_model(year, month)  # Correct the month when passing to Python backend
        print(f"Using Model: {ShiftModel.__tablename__}")

        user_shifts = ShiftModel.query.filter_by(username=user_name).first()
        print(f"user_shifts: {user_shifts}.")

        days = []
        if user_shifts:
            for day in range(1, 32):  # Handling up to 31 days
                if getattr(user_shifts, f'day_{day}', False):
                    days.append(f"{year}-{str(month).zfill(2)}-{str(day).zfill(2)}")

        print(f"dates: {days}.")

        return jsonify({'dates': days})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/fetch_all_users_schedules', methods=['POST'])
@login_required
def fetch_all_users_schedules():
    data = request.get_json()
    year = int(data['year'])
    month = int(data['month'])

    ShiftModel = get_shift_model(year, month)
    all_user_shifts = ShiftModel.query.all()

    results = []
    for user_shifts in all_user_shifts:
        dates = [f"{year}-{str(month).zfill(2)}-{str(i).zfill(2)}"
                 for i in range(1, 32)
                 if getattr(user_shifts, f'day_{i}', False)]
        if dates:
            results.append({'username': user_shifts.username, 'dates': dates})

    return jsonify(results)


@app.route('/generate_schedule', methods=['POST'])
@login_required
def generate_schedule():
    current_year = datetime.now().year
    current_month = datetime.now().month
    data = request.get_json()
    year = int(data['year'])
    month = int(data['month'])
    days_in_month = monthrange(year, month)[1]

    print(f"data: {data}, year: {year}, month: {month}, days_in_month: {days_in_month}.")
    # Fetch the model for the specific month and year
    ShiftModel = get_shift_model(year, month)
    all_user_preferences = ShiftModel.query.all()

    num_users = len(all_user_preferences)

    # Generate distinct colors
    colors = generate_distinct_colors(num_users)
    user_colors = {user.username: colors[i % num_users] for i, user in enumerate(all_user_preferences)}

    # Problem setup
    prob = pl.LpProblem("Shift_Scheduling", pl.LpMinimize)

    # Variables: shifts[(username, day)] == 1 if user works on 'day', else 0
    shifts = {(user.username, day): pl.LpVariable(f"shift_{user.username}_{day}", cat='Binary')
              for user in all_user_preferences for day in range(1, days_in_month + 1)}
    
    print(f"shifts: {shifts}.")

    # Objective: Dummy objective, could be improved based on further requirements
    prob += 0

    # Constraints
    # Each day exactly one person must work
    for day in range(1, days_in_month + 1):
        prob += pl.lpSum(shifts[(user.username, day)] for user in all_user_preferences) == 1, f"One_user_per_day_{day}"

    # Each person works at least min_shifts and at most max_shifts if available
    for user in all_user_preferences:
        available_days = [day for day in range(1, days_in_month + 1) if getattr(user, f'day_{day}', False)]
        if available_days:
            prob += pl.lpSum(shifts[(user.username, day)] for day in available_days) >= user.min_shifts, f"Min_shifts_{user.username}"
            prob += pl.lpSum(shifts[(user.username, day)] for day in available_days) <= user.max_shifts, f"Max_shifts_{user.username}"
        
        # Set shifts to 0 for days the user is not available
        unavailable_days = set(range(1, days_in_month + 1)) - set(available_days)
        for day in unavailable_days:
            prob += shifts[(user.username, day)] == 0, f"Shift_not_possible_{user.username}_{day}"

    prob.writeLP("out.lp")

    # Solve the problem
    prob.solve()

    # Check if a valid solution exists
    if pl.LpStatus[prob.status] == 'Optimal':
        results = []
        for user in all_user_preferences:
            for day in range(1, days_in_month + 1):
                if pl.value(shifts[(user.username, day)]) == 1:
                    results.append({'username': user.username, 'date': f"{year}-{month:02d}-{day:02d}", 'color': user_colors[user.username]})
        return jsonify({'status': 'success', 'schedule': results})
    else:
        return jsonify({'status': 'failure', 'message': 'Infeasible solution', 'violated_constraints': [c.name for c in prob.constraints.values() if c.pi > 0]})

def generate_distinct_colors(n):
    import colorsys
    colors = []
    step = 360 / n  # Divide the color wheel into n parts
    for i in range(n):
        hue = i * step
        rgb = colorsys.hsv_to_rgb(hue/360, 1.0, 1.0)  # Saturation & Lightness at max for vivid colors
        hex_color = "#{:02x}{:02x}{:02x}".format(int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255))
        colors.append(hex_color)
    return colors

@app.route('/load_user_preferences', methods=['GET'])
@login_required
def load_user_preferences():
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    user_name = session["user"]  # Assuming you are using Flask-Login for user session management

    ShiftModel = get_shift_model(year, month)
    user_prefs = ShiftModel.query.filter_by(username=user_name).first()

    if user_prefs:
        dates = [f"{year}-{str(month).zfill(2)}-{str(day).zfill(2)}"
                 for day in range(1, monthrange(year, month)[1] + 1)
                 if getattr(user_prefs, f'day_{day}', False)]
        min_shifts = user_prefs.min_shifts
        max_shifts = user_prefs.max_shifts
    else:
        dates = []
        min_shifts = 0
        max_shifts = 0

    return jsonify({'dates': dates, 'min_shifts': min_shifts, 'max_shifts': max_shifts})

