# FitPro AI - Intelligent Fitness Platform

A complete, production-ready fitness tracking web application built with **Flask**, **Bootstrap 5**, and **SQLite** (with MySQL support). Features glassmorphism UI, AI-powered recommendations, and comprehensive CRUD functionality.

## Features

- **User Authentication** - Secure registration/login with password hashing
- **Dashboard** - Interactive widgets with real-time stats
- **Workout Planner** - Full CRUD for exercise tracking
- **Diet Planner** - Meal logging with macro tracking
- **BMI Calculator** - Body Mass Index with history charts
- **Progress Tracker** - Body measurements with Chart.js visualization
- **Water Intake** - Quick-add hydration tracking
- **Sleep Tracker** - Sleep quality and duration logging
- **AI Assistant** - Smart workout & diet recommendations
- **Glassmorphism Design** - Modern dark/light theme UI
- **Responsive Layout** - Works on desktop, tablet, and mobile

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Flask 3.x (Python) |
| Database | SQLite (default) / MySQL |
| Frontend | Bootstrap 5 + Jinja2 |
| Charts | Chart.js |
| Icons | Bootstrap Icons |
| Fonts | Google Fonts (Inter) |

## Project Structure

```
FitProAI/
|
|-- app.py              # Main Flask application
|-- config.py           # Configuration settings
|-- database.py         # Database operations (SQLite/MySQL)
|-- fitpro.sql          # Database schema
|-- requirements.txt    # Python dependencies
|-- fitpro.db           # SQLite database (auto-created)
|
|-- templates/          # Jinja2 HTML templates
|   |-- base.html       # Layout with glassmorphism theme
|   |-- index.html      # Landing page
|   |-- login.html      # Login form
|   |-- signup.html     # Registration form
|   |-- dashboard.html  # Main dashboard
|   |-- workout.html    # Workout CRUD
|   |-- diet.html       # Diet planner CRUD
|   |-- bmi.html        # BMI calculator
|   |-- profile.html    # User profile
|   |-- progress.html   # Progress tracker
|
|-- static/             # Static assets
|   |-- css/            # Custom styles
|   |-- js/             # JavaScript files
|   |-- images/         # Uploaded images
|
|-- uploads/            # User uploads
```

## Quick Start

### 1. Install Dependencies

```bash
pip install Flask Werkzeug python-dotenv pymysql
```

Or use the requirements file:
```bash
pip install -r requirements.txt
```

### 2. Run the Application

```bash
python app.py
```

The application will start at `http://localhost:5000`

### 3. First Login

- Register a new account at `/signup`
- Or login with the default admin: `adminname` / `adminpasword`

## Database Configuration

### SQLite (Default - No setup required)

The app uses SQLite by default. The database file `fitpro.db` is auto-created on first run.

### MySQL (Production)

Set environment variables:
```bash
export DB_TYPE=mysql
export MYSQL_HOST=localhost
export MYSQL_USER=fitpro_user
export MYSQL_PASSWORD=your_password
export MYSQL_DATABASE=fitpro
```

Or create a `.env` file:
```env
DB_TYPE=mysql
MYSQL_HOST=localhost
MYSQL_USER=fitpro_user
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=fitpro
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_ENV` | Environment mode | `development` |
| `SECRET_KEY` | Flask secret key | auto-generated |
| `DB_TYPE` | Database type (`sqlite` or `mysql`) | `sqlite` |
| `MYSQL_HOST` | MySQL host | `localhost` |
| `MYSQL_USER` | MySQL username | `fitpro_user` |
| `MYSQL_PASSWORD` | MySQL password | - |
| `MYSQL_DATABASE` | MySQL database name | `fitpro` |

## API Endpoints

### Authentication
- `POST /signup` - User registration
- `POST /login` - User login
- `GET /logout` - User logout

### Dashboard
- `GET /dashboard` - Main dashboard

### CRUD Operations
- `GET/POST /workouts` - Workout management
- `GET/POST /diet` - Diet plan management
- `GET/POST /progress` - Progress tracking
- `GET/POST /bmi` - BMI calculator
- `GET/POST /profile` - User profile

### API
- `POST /api/water` - Add water intake
- `GET /api/water/today` - Get today's water
- `POST /api/sleep` - Log sleep
- `GET /api/sleep/recent` - Get recent sleep
- `GET /api/ai/workout` - AI workout recommendation
- `GET /api/ai/diet` - AI diet recommendation
- `GET /api/ai/calories` - Calculate daily calories

## Database Schema

### Tables
1. **users** - User accounts and profiles
2. **workouts** - Exercise tracking
3. **diet_plans** - Meal and nutrition logging
4. **progress_records** - Body measurements
5. **water_intake** - Hydration tracking
6. **sleep_tracking** - Sleep monitoring
7. **bmi_history** - BMI calculations
8. **contact_messages** - Contact form submissions

## Deployment

### Development
```bash
python app.py
```

### Production (Gunicorn)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## License

MIT License - Free for personal and commercial use.
