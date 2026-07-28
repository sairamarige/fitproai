"""
FitPro AI - Flask Application
=============================
Main application module with all routes, authentication, CRUD operations,
AI integration, and dashboard functionality.
"""

import os
import re
import math
from datetime import datetime, date, timedelta
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, abort
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from config import get_config
from database import db, init_db

# ============================================================
# APPLICATION FACTORY
# ============================================================

def create_app():
    """Create and configure Flask application."""
    app = Flask(__name__,
                template_folder='templates',
                static_folder='static')

    # Load configuration
    config = get_config()
    app.config.from_object(config)

    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Initialize database
    init_db(app)

    return app


app = create_app()

# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def login_required(f):
    """Decorator to require login for routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to require admin access."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        user = db.get_user_by_id(session['user_id'])
        if not user or not user.get('is_admin'):
            flash('Admin access required.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def calculate_bmi(weight_kg, height_cm):
    """Calculate BMI value and category."""
    if not weight_kg or not height_cm or height_cm <= 0:
        return None, None
    height_m = height_cm / 100
    bmi = weight_kg / (height_m ** 2)
    bmi = round(bmi, 1)

    if bmi < 18.5:
        category = 'underweight'
    elif bmi < 25:
        category = 'normal'
    elif bmi < 30:
        category = 'overweight'
    else:
        category = 'obese'

    return bmi, category


def calculate_calories_burned(duration_minutes, intensity, weight_kg=70):
    """Estimate calories burned based on duration and intensity."""
    # MET values: low=3, moderate=5, high=8, extreme=12
    met_values = {'low': 3, 'moderate': 5, 'high': 8, 'extreme': 12}
    met = met_values.get(intensity, 5)
    calories = int(met * weight_kg * (duration_minutes / 60))
    return calories


def calculate_daily_calories(age, gender, weight_kg, height_cm, activity_level, goal):
    """Calculate daily calorie needs using Mifflin-St Jeor equation."""
    # BMR calculation
    if gender == 'male':
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161

    # Activity multipliers
    activity_multipliers = {
        'sedentary': 1.2,
        'light': 1.375,
        'moderate': 1.55,
        'active': 1.725,
        'very_active': 1.9
    }
    tdee = bmr * activity_multipliers.get(activity_level, 1.55)

    # Goal adjustment
    goal_adjustments = {
        'weight_loss': -500,
        'muscle_gain': 300,
        'endurance': 0,
        'general_fitness': 0,
        'flexibility': -200
    }
    daily_calories = tdee + goal_adjustments.get(goal, 0)

    return round(daily_calories)


def get_ai_workout_recommendation(fitness_goal, activity_level, available_time=30):
    """Generate AI-style workout recommendation based on user profile."""
    recommendations = {
        'weight_loss': {
            'title': 'Fat Burning HIIT Circuit',
            'description': 'High-intensity interval training designed to maximize calorie burn.',
            'exercises': [
                {'name': 'Burpees', 'sets': '3', 'reps': '15', 'rest': '30s'},
                {'name': 'Jump Squats', 'sets': '3', 'reps': '20', 'rest': '30s'},
                {'name': 'Mountain Climbers', 'sets': '3', 'reps': '30', 'rest': '20s'},
                {'name': 'High Knees', 'sets': '3', 'reps': '45s', 'rest': '15s'},
                {'name': 'Jumping Jacks', 'sets': '3', 'reps': '50', 'rest': '20s'}
            ],
            'duration': min(available_time, 30),
            'intensity': 'high'
        },
        'muscle_gain': {
            'title': 'Hypertrophy Strength Training',
            'description': 'Progressive overload training focused on muscle growth.',
            'exercises': [
                {'name': 'Barbell Squats', 'sets': '4', 'reps': '8-10', 'rest': '90s'},
                {'name': 'Bench Press', 'sets': '4', 'reps': '8-10', 'rest': '90s'},
                {'name': 'Deadlifts', 'sets': '3', 'reps': '6-8', 'rest': '2min'},
                {'name': 'Shoulder Press', 'sets': '3', 'reps': '10-12', 'rest': '60s'},
                {'name': 'Pull-ups', 'sets': '3', 'reps': '8-12', 'rest': '60s'}
            ],
            'duration': min(available_time, 45),
            'intensity': 'high'
        },
        'endurance': {
            'title': 'Cardiovascular Endurance Builder',
            'description': 'Steady-state and interval cardio to build stamina.',
            'exercises': [
                {'name': 'Jogging/Running', 'sets': '1', 'reps': '20min', 'rest': 'N/A'},
                {'name': 'Jump Rope', 'sets': '5', 'reps': '2min', 'rest': '30s'},
                {'name': 'Box Jumps', 'sets': '3', 'reps': '15', 'rest': '45s'},
                {'name': 'Cycling Sprints', 'sets': '6', 'reps': '30s', 'rest': '30s'}
            ],
            'duration': min(available_time, 40),
            'intensity': 'moderate'
        },
        'general_fitness': {
            'title': 'Full Body Conditioning',
            'description': 'Balanced workout combining strength and cardio.',
            'exercises': [
                {'name': 'Push-ups', 'sets': '3', 'reps': '15', 'rest': '30s'},
                {'name': 'Bodyweight Squats', 'sets': '3', 'reps': '20', 'rest': '30s'},
                {'name': 'Plank Hold', 'sets': '3', 'reps': '45s', 'rest': '30s'},
                {'name': 'Lunges', 'sets': '3', 'reps': '12 each', 'rest': '30s'},
                {'name': 'Jumping Jacks', 'sets': '3', 'reps': '30', 'rest': '20s'}
            ],
            'duration': min(available_time, 30),
            'intensity': 'moderate'
        },
        'flexibility': {
            'title': 'Mobility & Flexibility Flow',
            'description': 'Dynamic stretching and yoga-inspired movements.',
            'exercises': [
                {'name': 'Sun Salutation', 'sets': '5', 'reps': 'flow', 'rest': '10s'},
                {'name': 'Pigeon Pose', 'sets': '2', 'reps': '30s each', 'rest': '10s'},
                {'name': 'Warrior Sequence', 'sets': '3', 'reps': 'flow', 'rest': '15s'},
                {'name': 'Foam Rolling', 'sets': '1', 'reps': '5min', 'rest': 'N/A'},
                {'name': 'Cat-Cow Stretch', 'sets': '3', 'reps': '10', 'rest': '10s'}
            ],
            'duration': min(available_time, 25),
            'intensity': 'low'
        }
    }
    return recommendations.get(fitness_goal, recommendations['general_fitness'])


def get_ai_diet_recommendation(fitness_goal, daily_calories):
    """Generate AI-style diet recommendation based on user profile."""
    macro_splits = {
        'weight_loss': {'protein': 40, 'carbs': 30, 'fats': 30},
        'muscle_gain': {'protein': 35, 'carbs': 45, 'fats': 20},
        'endurance': {'protein': 25, 'carbs': 50, 'fats': 25},
        'general_fitness': {'protein': 30, 'carbs': 40, 'fats': 30},
        'flexibility': {'protein': 25, 'carbs': 45, 'fats': 30}
    }

    macros = macro_splits.get(fitness_goal, macro_splits['general_fitness'])

    diet_plans = {
        'weight_loss': {
            'title': 'Calorie Deficit Fat Loss Plan',
            'description': 'High protein, moderate carb approach to preserve muscle while losing fat.',
            'meals': [
                {'name': 'Protein Oatmeal Bowl', 'type': 'breakfast', 'calories': 350, 'protein': 30, 'carbs': 40, 'fats': 8},
                {'name': 'Grilled Chicken Salad', 'type': 'lunch', 'calories': 400, 'protein': 40, 'carbs': 20, 'fats': 15},
                {'name': 'Salmon & Vegetables', 'type': 'dinner', 'calories': 450, 'protein': 35, 'carbs': 25, 'fats': 18},
                {'name': 'Greek Yogurt & Berries', 'type': 'snack', 'calories': 200, 'protein': 15, 'carbs': 20, 'fats': 5}
            ]
        },
        'muscle_gain': {
            'title': 'Lean Muscle Building Plan',
            'description': 'Calorie surplus with emphasis on protein for muscle protein synthesis.',
            'meals': [
                {'name': 'Egg White Omelet + Toast', 'type': 'breakfast', 'calories': 450, 'protein': 30, 'carbs': 45, 'fats': 12},
                {'name': 'Turkey & Rice Bowl', 'type': 'lunch', 'calories': 600, 'protein': 45, 'carbs': 65, 'fats': 12},
                {'name': 'Steak & Sweet Potato', 'type': 'dinner', 'calories': 650, 'protein': 45, 'carbs': 55, 'fats': 20},
                {'name': 'Protein Shake + Banana', 'type': 'snack', 'calories': 300, 'protein': 25, 'carbs': 30, 'fats': 5}
            ]
        },
        'endurance': {
            'title': 'Energy Optimization Plan',
            'description': 'Carbohydrate-focused nutrition for sustained energy.',
            'meals': [
                {'name': 'Whole Grain Pancakes', 'type': 'breakfast', 'calories': 500, 'protein': 15, 'carbs': 80, 'fats': 12},
                {'name': 'Pasta with Marinara', 'type': 'lunch', 'calories': 600, 'protein': 20, 'carbs': 90, 'fats': 10},
                {'name': 'Chicken & Quinoa Bowl', 'type': 'dinner', 'calories': 550, 'protein': 35, 'carbs': 60, 'fats': 15},
                {'name': 'Energy Balls', 'type': 'snack', 'calories': 250, 'protein': 8, 'carbs': 35, 'fats': 10}
            ]
        },
        'general_fitness': {
            'title': 'Balanced Wellness Plan',
            'description': 'Well-rounded nutrition for overall health and fitness maintenance.',
            'meals': [
                {'name': 'Smoothie Bowl', 'type': 'breakfast', 'calories': 400, 'protein': 20, 'carbs': 55, 'fats': 10},
                {'name': 'Buddha Bowl', 'type': 'lunch', 'calories': 500, 'protein': 25, 'carbs': 60, 'fats': 15},
                {'name': 'Fish Tacos', 'type': 'dinner', 'calories': 550, 'protein': 30, 'carbs': 50, 'fats': 18},
                {'name': 'Mixed Nuts & Fruit', 'type': 'snack', 'calories': 200, 'protein': 6, 'carbs': 20, 'fats': 12}
            ]
        },
        'flexibility': {
            'title': 'Anti-Inflammatory Recovery Plan',
            'description': 'Nutrient-dense foods to support recovery and joint health.',
            'meals': [
                {'name': 'Chia Seed Pudding', 'type': 'breakfast', 'calories': 350, 'protein': 12, 'carbs': 40, 'fats': 15},
                {'name': 'Mediterranean Bowl', 'type': 'lunch', 'calories': 450, 'protein': 20, 'carbs': 50, 'fats': 18},
                {'name': 'Miso Salmon Bowl', 'type': 'dinner', 'calories': 500, 'protein': 30, 'carbs': 45, 'fats': 16},
                {'name': 'Turmeric Golden Milk', 'type': 'snack', 'calories': 150, 'protein': 5, 'carbs': 15, 'fats': 8}
            ]
        }
    }

    plan = diet_plans.get(fitness_goal, diet_plans['general_fitness'])
    plan['macros'] = macros
    plan['daily_calories'] = daily_calories
    return plan


# ============================================================
# CONTEXT PROCESSORS
# ============================================================

@app.context_processor
def inject_globals():
    """Inject global variables into all templates."""
    return {
        'app_name': app.config['APP_NAME'],
        'app_version': app.config['APP_VERSION'],
        'now': datetime.now(),
        'min': min,
        'max': max,
        'round': round
    }


# ============================================================
# ERROR HANDLERS
# ============================================================

def get_site_stats():
    """Fetch site-wide stats used on the public landing page."""
    return {
        'total_users': db.fetchone("SELECT COUNT(*) as count FROM users")['count'],
        'total_workouts': db.fetchone("SELECT COUNT(*) as count FROM workouts")['count'],
        'total_meals': db.fetchone("SELECT COUNT(*) as count FROM diet_plans")['count']
    }


@app.errorhandler(404)
def not_found(error):
    return render_template('index.html', error_404=True, stats=get_site_stats()), 404


@app.errorhandler(500)
def server_error(error):
    flash('An unexpected error occurred. Please try again.', 'danger')
    return redirect(url_for('index'))


# ============================================================
# PUBLIC ROUTES
# ============================================================

@app.route('/')
def index():
    """Home page / landing page."""
    stats = get_site_stats()
    return render_template('index.html', stats=stats)


@app.route('/about')
def about():
    """About page."""
    return render_template('index.html', about=True, stats=get_site_stats())


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact page and form submission."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()

        if not all([name, email, message]):
            flash('Please fill in all required fields.', 'warning')
            return redirect(url_for('contact'))

        db.add_contact_message(name, email, subject, message)
        flash('Thank you! Your message has been sent successfully.', 'success')
        return redirect(url_for('index'))

    return render_template('index.html', contact=True, stats=get_site_stats())


# ============================================================
# AUTHENTICATION ROUTES
# ============================================================

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """User registration page."""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        full_name = request.form.get('full_name', '').strip()
        age = request.form.get('age', type=int)
        gender = request.form.get('gender')
        height_cm = request.form.get('height_cm', type=float)
        weight_kg = request.form.get('weight_kg', type=float)
        fitness_goal = request.form.get('fitness_goal', 'general_fitness')
        activity_level = request.form.get('activity_level', 'moderate')

        # Validation
        errors = []
        if not username or len(username) < 3:
            errors.append('Username must be at least 3 characters.')
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            errors.append('Username can only contain letters, numbers, and underscores.')
        if not email or '@' not in email:
            errors.append('Please enter a valid email address.')
        if not password or len(password) < 6:
            errors.append('Password must be at least 6 characters.')
        if password != confirm_password:
            errors.append('Passwords do not match.')
        if age and (age < 10 or age > 120):
            errors.append('Age must be between 10 and 120.')

        # Check existing users
        if db.get_user_by_username(username):
            errors.append('Username already taken.')
        if db.get_user_by_email(email):
            errors.append('Email already registered.')

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('signup.html', form_data=request.form)

        # Create user
        password_hash = generate_password_hash(password)
        user_id = db.create_user(
            username=username, email=email, password_hash=password_hash,
            full_name=full_name, age=age, gender=gender,
            height_cm=height_cm, weight_kg=weight_kg,
            fitness_goal=fitness_goal, activity_level=activity_level
        )

        # Calculate initial BMI if height and weight provided
        if height_cm and weight_kg:
            bmi_value, bmi_category = calculate_bmi(weight_kg, height_cm)
            db.add_bmi_record(user_id, height_cm, weight_kg, bmi_value, bmi_category)

        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page."""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash('Please enter both username and password.', 'warning')
            return render_template('login.html')

        # Find user by username or email
        user = db.get_user_by_username(username)
        if not user:
            user = db.get_user_by_email(username)

        if user and check_password_hash(user['password_hash'], password):
            if not user.get('is_active', True):
                flash('Your account has been deactivated.', 'danger')
                return render_template('login.html')

            session.permanent = True
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = bool(user.get('is_admin', False))

            flash(f'Welcome back, {user["full_name"] or user["username"]}!', 'success')
            return redirect(url_for('dashboard'))

        flash('Invalid username or password.', 'danger')
    return render_template('login.html')


@app.route('/logout')
def logout():
    """User logout."""
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))


# ============================================================
# DASHBOARD ROUTE
# ============================================================

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard page."""
    user = db.get_user_by_id(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('login'))

    # Get workout stats
    workout_stats = db.get_workout_stats(session['user_id'])

    # Get diet stats
    diet_stats = db.get_diet_stats(session['user_id'])

    # Get water intake
    water_total = db.get_total_water_today(session['user_id'])
    water_percentage = min(100, int((water_total / 2500) * 100))

    # Get sleep data
    last_sleep = db.get_last_sleep(session['user_id'])

    # Get latest BMI
    latest_bmi = db.get_latest_bmi(session['user_id'])

    # Get recent progress for chart
    progress_records = db.get_user_progress(session['user_id'], limit=7)
    progress_data = {
        'dates': [r['record_date'] for r in reversed(progress_records)],
        'weights': [r['weight_kg'] for r in reversed(progress_records) if r['weight_kg']]
    }

    # AI recommendations
    workout_rec = get_ai_workout_recommendation(
        user.get('fitness_goal', 'general_fitness'),
        user.get('activity_level', 'moderate')
    )

    daily_calories = calculate_daily_calories(
        user.get('age') or 30,
        user.get('gender') or 'male',
        user.get('weight_kg') or 70,
        user.get('height_cm') or 170,
        user.get('activity_level') or 'moderate',
        user.get('fitness_goal') or 'general_fitness'
    )

    return render_template(
        'dashboard.html',
        user=user,
        workout_stats=workout_stats,
        diet_stats=diet_stats,
        water_total=water_total,
        water_percentage=water_percentage,
        last_sleep=last_sleep,
        latest_bmi=latest_bmi,
        progress_data=progress_data,
        workout_rec=workout_rec,
        daily_calories=daily_calories
    )


# ============================================================
# PROFILE ROUTES
# ============================================================

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile page."""
    user = db.get_user_by_id(session['user_id'])

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        age = request.form.get('age', type=int)
        gender = request.form.get('gender')
        height_cm = request.form.get('height_cm', type=float)
        weight_kg = request.form.get('weight_kg', type=float)
        fitness_goal = request.form.get('fitness_goal')
        activity_level = request.form.get('activity_level')

        db.update_user(session['user_id'], full_name=full_name, age=age,
                      gender=gender, height_cm=height_cm, weight_kg=weight_kg,
                      fitness_goal=fitness_goal, activity_level=activity_level)

        # Recalculate BMI if height and weight provided
        if height_cm and weight_kg:
            bmi_value, bmi_category = calculate_bmi(weight_kg, height_cm)
            db.add_bmi_record(session['user_id'], height_cm, weight_kg, bmi_value, bmi_category)

        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))

    return render_template('profile.html', user=user)


# ============================================================
# WORKOUT ROUTES
# ============================================================

@app.route('/workouts', methods=['GET', 'POST'])
@login_required
def workouts():
    """Workout CRUD page."""
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'create':
            name = request.form.get('name', '').strip()
            category = request.form.get('category')
            duration = request.form.get('duration_minutes', type=int)
            intensity = request.form.get('intensity', 'moderate')
            description = request.form.get('description', '').strip()
            exercises = request.form.get('exercises', '').strip()
            scheduled_date = request.form.get('scheduled_date')

            if not all([name, category, duration]):
                flash('Please fill in all required fields.', 'warning')
                return redirect(url_for('workouts'))

            # Calculate calories burned
            user = db.get_user_by_id(session['user_id'])
            calories = calculate_calories_burned(duration, intensity, user.get('weight_kg', 70))

            db.create_workout(
                user_id=session['user_id'], name=name, category=category,
                duration_minutes=duration, calories_burned=calories,
                intensity=intensity, description=description,
                exercises=exercises, scheduled_date=scheduled_date
            )
            flash('Workout added successfully!', 'success')

        elif action == 'update':
            workout_id = request.form.get('workout_id', type=int)
            updates = {
                'name': request.form.get('name', '').strip(),
                'category': request.form.get('category'),
                'duration_minutes': request.form.get('duration_minutes', type=int),
                'intensity': request.form.get('intensity'),
                'description': request.form.get('description', '').strip(),
                'exercises': request.form.get('exercises', '').strip(),
                'scheduled_date': request.form.get('scheduled_date'),
                'completed': request.form.get('completed') == 'on'
            }
            # Recalculate calories if duration or intensity changed
            if updates['duration_minutes'] and updates['intensity']:
                user = db.get_user_by_id(session['user_id'])
                updates['calories_burned'] = calculate_calories_burned(
                    updates['duration_minutes'], updates['intensity'], user.get('weight_kg', 70)
                )

            db.update_workout(workout_id, session['user_id'], **updates)
            flash('Workout updated successfully!', 'success')

        elif action == 'delete':
            workout_id = request.form.get('workout_id', type=int)
            db.delete_workout(workout_id, session['user_id'])
            flash('Workout deleted successfully!', 'info')

        return redirect(url_for('workouts'))

    # GET request
    user_workouts = db.get_user_workouts(session['user_id'])
    workout_stats = db.get_workout_stats(session['user_id'])
    return render_template('workout.html', workouts=user_workouts, stats=workout_stats)


# ============================================================
# DIET ROUTES
# ============================================================

@app.route('/diet', methods=['GET', 'POST'])
@login_required
def diet():
    """Diet planner CRUD page."""
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'create':
            meal_name = request.form.get('meal_name', '').strip()
            meal_type = request.form.get('meal_type')
            calories = request.form.get('calories', type=int)
            protein_g = request.form.get('protein_g', type=float) or 0
            carbs_g = request.form.get('carbs_g', type=float) or 0
            fats_g = request.form.get('fats_g', type=float) or 0
            fiber_g = request.form.get('fiber_g', type=float) or 0
            description = request.form.get('description', '').strip()
            ingredients = request.form.get('ingredients', '').strip()
            scheduled_date = request.form.get('scheduled_date')

            if not all([meal_name, meal_type, calories]):
                flash('Please fill in all required fields.', 'warning')
                return redirect(url_for('diet'))

            db.create_diet_plan(
                user_id=session['user_id'], meal_name=meal_name, meal_type=meal_type,
                calories=calories, protein_g=protein_g, carbs_g=carbs_g,
                fats_g=fats_g, fiber_g=fiber_g, description=description,
                ingredients=ingredients, scheduled_date=scheduled_date
            )
            flash('Meal added successfully!', 'success')

        elif action == 'update':
            diet_id = request.form.get('diet_id', type=int)
            db.update_diet(
                diet_id, session['user_id'],
                meal_name=request.form.get('name', '').strip(),
                meal_type=request.form.get('meal_type'),
                calories=request.form.get('calories', type=int),
                protein_g=request.form.get('protein_g', type=float),
                carbs_g=request.form.get('carbs_g', type=float),
                fats_g=request.form.get('fats_g', type=float),
                fiber_g=request.form.get('fiber_g', type=float),
                description=request.form.get('description', '').strip(),
                ingredients=request.form.get('ingredients', '').strip(),
                scheduled_date=request.form.get('scheduled_date'),
                consumed=request.form.get('consumed') == 'on'
            )
            flash('Meal updated successfully!', 'success')

        elif action == 'delete':
            diet_id = request.form.get('diet_id', type=int)
            db.delete_diet(diet_id, session['user_id'])
            flash('Meal deleted successfully!', 'info')

        return redirect(url_for('diet'))

    # GET request
    user_diet = db.get_user_diet_plans(session['user_id'])
    diet_stats = db.get_diet_stats(session['user_id'])
    return render_template('diet.html', diet_plans=user_diet, stats=diet_stats)


# ============================================================
# BMI ROUTE
# ============================================================

@app.route('/bmi', methods=['GET', 'POST'])
@login_required
def bmi():
    """BMI calculator page."""
    user = db.get_user_by_id(session['user_id'])
    bmi_result = None
    bmi_history = db.get_bmi_history(session['user_id'])

    if request.method == 'POST':
        height_cm = request.form.get('height_cm', type=float)
        weight_kg = request.form.get('weight_kg', type=float)

        if not height_cm or not weight_kg:
            flash('Please enter both height and weight.', 'warning')
        else:
            bmi_value, bmi_category = calculate_bmi(weight_kg, height_cm)
            if bmi_value:
                db.add_bmi_record(session['user_id'], height_cm, weight_kg, bmi_value, bmi_category)

                # Update user profile
                db.update_user(session['user_id'], height_cm=height_cm, weight_kg=weight_kg)

                bmi_result = {
                    'value': bmi_value,
                    'category': bmi_category,
                    'height_cm': height_cm,
                    'weight_kg': weight_kg
                }
                flash(f'Your BMI is {bmi_value} ({bmi_category.replace("_", " ").title()})', 'success')
            else:
                flash('Invalid height or weight values.', 'danger')

    return render_template('bmi.html', user=user, bmi_result=bmi_result, bmi_history=bmi_history)


# ============================================================
# PROGRESS ROUTES
# ============================================================

@app.route('/progress', methods=['GET', 'POST'])
@login_required
def progress():
    """Progress tracking page."""
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'create':
            record_date = request.form.get('record_date')
            weight_kg = request.form.get('weight_kg', type=float)
            body_fat = request.form.get('body_fat_percent', type=float)
            muscle_mass = request.form.get('muscle_mass_kg', type=float)
            chest_cm = request.form.get('chest_cm', type=float)
            waist_cm = request.form.get('waist_cm', type=float)
            hips_cm = request.form.get('hips_cm', type=float)
            arms_cm = request.form.get('arms_cm', type=float)
            thighs_cm = request.form.get('thighs_cm', type=float)
            notes = request.form.get('notes', '').strip()

            if not record_date:
                flash('Please select a date.', 'warning')
                return redirect(url_for('progress'))

            db.create_progress(
                user_id=session['user_id'], record_date=record_date,
                weight_kg=weight_kg, body_fat_percent=body_fat,
                muscle_mass_kg=muscle_mass, chest_cm=chest_cm,
                waist_cm=waist_cm, hips_cm=hips_cm, arms_cm=arms_cm,
                thighs_cm=thighs_cm, notes=notes
            )
            flash('Progress record added!', 'success')

        elif action == 'delete':
            progress_id = request.form.get('progress_id', type=int)
            db.delete_progress(progress_id, session['user_id'])
            flash('Record deleted.', 'info')

        return redirect(url_for('progress'))

    # GET request
    progress_records = db.get_user_progress(session['user_id'])

    # Prepare chart data
    chart_data = {
        'dates': [r['record_date'] for r in reversed(progress_records)],
        'weights': [r['weight_kg'] for r in reversed(progress_records) if r['weight_kg']],
        'body_fat': [r['body_fat_percent'] for r in reversed(progress_records) if r['body_fat_percent']]
    }

    return render_template('progress.html', records=progress_records, chart_data=chart_data)


# ============================================================
# WATER TRACKER API
# ============================================================

@app.route('/api/water', methods=['POST'])
@login_required
def add_water():
    """API endpoint to add water intake."""
    json_data = request.get_json(silent=True)
    if json_data:
        try:
            amount = int(json_data.get('amount', 250))
        except (TypeError, ValueError):
            amount = None
    else:
        amount = request.form.get('amount', 250, type=int)

    if not amount or amount <= 0:
        return jsonify({'success': False, 'message': 'Invalid amount'}), 400

    db.add_water_intake(session['user_id'], amount)
    total = db.get_total_water_today(session['user_id'])

    return jsonify({
        'success': True,
        'total': total,
        'percentage': min(100, int((total / 2500) * 100))
    })


@app.route('/api/water/today')
@login_required
def get_water_today():
    """Get today's water intake."""
    total = db.get_total_water_today(session['user_id'])
    records = db.get_water_intake(session['user_id'])
    return jsonify({
        'total': total,
        'percentage': min(100, int((total / 2500) * 100)),
        'records': records
    })


# ============================================================
# SLEEP TRACKER API
# ============================================================

@app.route('/api/sleep', methods=['POST'])
@login_required
def add_sleep():
    """API endpoint to add sleep record."""
    data = request.get_json() or request.form

    sleep_date = data.get('sleep_date') if isinstance(data, dict) else request.form.get('sleep_date')
    bed_time = data.get('bed_time') if isinstance(data, dict) else request.form.get('bed_time')
    wake_time = data.get('wake_time') if isinstance(data, dict) else request.form.get('wake_time')
    quality = data.get('quality') if isinstance(data, dict) else request.form.get('quality')
    notes = data.get('notes', '') if isinstance(data, dict) else request.form.get('notes', '')

    # Calculate duration from bed_time and wake_time
    duration_hours = None
    if bed_time and wake_time:
        try:
            bed = datetime.strptime(bed_time, '%H:%M')
            wake = datetime.strptime(wake_time, '%H:%M')
            if wake < bed:
                wake += timedelta(days=1)
            duration_hours = round((wake - bed).total_seconds() / 3600, 1)
        except ValueError:
            pass

    record_id = db.add_sleep_record(
        session['user_id'], sleep_date, bed_time, wake_time,
        duration_hours, quality, notes=notes
    )

    return jsonify({'success': True, 'id': record_id, 'duration': duration_hours})


@app.route('/api/sleep/recent')
@login_required
def get_recent_sleep():
    """Get recent sleep records."""
    records = db.get_sleep_records(session['user_id'])
    return jsonify({'records': records})


# ============================================================
# AI RECOMMENDATION API
# ============================================================

@app.route('/api/ai/workout')
@login_required
def ai_workout():
    """Get AI workout recommendation."""
    user = db.get_user_by_id(session['user_id'])
    available_time = request.args.get('time', 30, type=int)

    recommendation = get_ai_workout_recommendation(
        user.get('fitness_goal', 'general_fitness'),
        user.get('activity_level', 'moderate'),
        available_time
    )
    return jsonify(recommendation)


@app.route('/api/ai/diet')
@login_required
def ai_diet():
    """Get AI diet recommendation."""
    user = db.get_user_by_id(session['user_id'])

    daily_calories = calculate_daily_calories(
        user.get('age') or 30,
        user.get('gender') or 'male',
        user.get('weight_kg') or 70,
        user.get('height_cm') or 170,
        user.get('activity_level') or 'moderate',
        user.get('fitness_goal') or 'general_fitness'
    )

    recommendation = get_ai_diet_recommendation(
        user.get('fitness_goal', 'general_fitness'),
        daily_calories
    )
    return jsonify(recommendation)


@app.route('/api/ai/calories')
@login_required
def ai_calories():
    """Calculate daily calorie needs."""
    user = db.get_user_by_id(session['user_id'])

    daily_calories = calculate_daily_calories(
        user.get('age') or 30,
        user.get('gender') or 'male',
        user.get('weight_kg') or 70,
        user.get('height_cm') or 170,
        user.get('activity_level') or 'moderate',
        user.get('fitness_goal') or 'general_fitness'
    )

    macros = {
        'weight_loss': {'protein': 40, 'carbs': 30, 'fats': 30},
        'muscle_gain': {'protein': 35, 'carbs': 45, 'fats': 20},
        'endurance': {'protein': 25, 'carbs': 50, 'fats': 25},
        'general_fitness': {'protein': 30, 'carbs': 40, 'fats': 30},
        'flexibility': {'protein': 25, 'carbs': 45, 'fats': 30}
    }.get(user.get('fitness_goal', 'general_fitness'))

    return jsonify({
        'daily_calories': daily_calories,
        'macros': macros,
        'breakdown': {
            'protein_g': int((daily_calories * macros['protein'] / 100) / 4),
            'carbs_g': int((daily_calories * macros['carbs'] / 100) / 4),
            'fats_g': int((daily_calories * macros['fats'] / 100) / 9)
        }
    })


@app.route('/ai-assistant')
@login_required
def ai_assistant():
    """AI Fitness Assistant page."""
    user = db.get_user_by_id(session['user_id'])

    # Get AI recommendations
    workout_rec = get_ai_workout_recommendation(
        user.get('fitness_goal', 'general_fitness'),
        user.get('activity_level', 'moderate')
    )

    daily_calories = calculate_daily_calories(
        user.get('age') or 30,
        user.get('gender') or 'male',
        user.get('weight_kg') or 70,
        user.get('height_cm') or 170,
        user.get('activity_level') or 'moderate',
        user.get('fitness_goal') or 'general_fitness'
    )

    diet_rec = get_ai_diet_recommendation(
        user.get('fitness_goal', 'general_fitness'),
        daily_calories
    )

    bmi_data = db.get_latest_bmi(session['user_id'])

    return render_template('ai_assistant.html', user=user,
                          workout_rec=workout_rec, diet_rec=diet_rec,
                          daily_calories=daily_calories, bmi_data=bmi_data)


# ============================================================
# ADMIN ROUTES
# ============================================================

@app.route('/admin')
@admin_required
def admin_dashboard():
    """Admin dashboard."""
    # Get all stats
    stats = {
        'total_users': db.fetchone("SELECT COUNT(*) as count FROM users")['count'],
        'total_workouts': db.fetchone("SELECT COUNT(*) as count FROM workouts")['count'],
        'total_meals': db.fetchone("SELECT COUNT(*) as count FROM diet_plans")['count'],
        'total_messages': db.fetchone("SELECT COUNT(*) as count FROM contact_messages")['count'],
        'unread_messages': db.fetchone("SELECT COUNT(*) as count FROM contact_messages WHERE is_read = 0")['count']
    }
    messages = db.get_contact_messages()
    users = db.get_all_users()
    return render_template('admin.html', stats=stats, messages=messages, users=users)


@app.route('/admin/messages/<int:message_id>/read', methods=['POST'])
@admin_required
def mark_message_read(message_id):
    """Mark a contact message as read."""
    db.mark_message_read(message_id)
    return jsonify({'success': True})


@app.route('/admin/users/<int:user_id>/toggle-admin', methods=['POST'])
@admin_required
def toggle_user_admin(user_id):
    """Grant or revoke admin rights for a user."""
    if user_id == session['user_id']:
        flash("You can't change your own admin status.", 'warning')
        return redirect(url_for('admin_dashboard'))

    target = db.get_user_by_id(user_id)
    if not target:
        flash('User not found.', 'danger')
        return redirect(url_for('admin_dashboard'))

    new_status = not bool(target.get('is_admin'))
    db.set_user_admin(user_id, new_status)
    flash(f"{target['username']} is now {'an admin' if new_status else 'a regular user'}.", 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/users/<int:user_id>/toggle-active', methods=['POST'])
@admin_required
def toggle_user_active(user_id):
    """Activate or deactivate a user account."""
    if user_id == session['user_id']:
        flash("You can't deactivate your own account.", 'warning')
        return redirect(url_for('admin_dashboard'))

    target = db.get_user_by_id(user_id)
    if not target:
        flash('User not found.', 'danger')
        return redirect(url_for('admin_dashboard'))

    new_status = not bool(target.get('is_active', True))
    db.set_user_active(user_id, new_status)
    flash(f"{target['username']} has been {'reactivated' if new_status else 'deactivated'}.", 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    """Permanently delete a user account."""
    if user_id == session['user_id']:
        flash("You can't delete your own account.", 'warning')
        return redirect(url_for('admin_dashboard'))

    target = db.get_user_by_id(user_id)
    if not target:
        flash('User not found.', 'danger')
        return redirect(url_for('admin_dashboard'))

    db.delete_user(user_id)
    flash(f"User {target['username']} has been deleted.", 'success')
    return redirect(url_for('admin_dashboard'))


# ============================================================
# MAIN ENTRY POINT
# ============================================================

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)