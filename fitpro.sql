-- ============================================================
-- FitPro AI - Complete Database Schema
-- ============================================================
-- Database: fitpro
-- Engine: MySQL 8.0+ / SQLite compatible
-- Tables: 8 normalized tables with proper relationships
-- ============================================================

-- Drop tables if they exist (for clean setup)
DROP TABLE IF EXISTS contact_messages;
DROP TABLE IF EXISTS bmi_history;
DROP TABLE IF EXISTS sleep_tracking;
DROP TABLE IF EXISTS water_intake;
DROP TABLE IF EXISTS progress_records;
DROP TABLE IF EXISTS diet_plans;
DROP TABLE IF EXISTS workouts;
DROP TABLE IF EXISTS users;

-- ============================================================
-- 1. USERS TABLE
-- ============================================================
CREATE TABLE users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        VARCHAR(50) NOT NULL UNIQUE,
    email           VARCHAR(100) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    full_name       VARCHAR(100),
    age             INTEGER CHECK (age >= 10 AND age <= 120),
    gender          VARCHAR(10) CHECK (gender IN ('male', 'female', 'other')),
    height_cm       DECIMAL(5,2),
    weight_kg       DECIMAL(5,2),
    fitness_goal    VARCHAR(50) DEFAULT 'general_fitness' 
                    CHECK (fitness_goal IN ('weight_loss', 'muscle_gain', 'endurance', 'general_fitness', 'flexibility')),
    activity_level  VARCHAR(20) DEFAULT 'moderate'
                    CHECK (activity_level IN ('sedentary', 'light', 'moderate', 'active', 'very_active')),
    profile_image   VARCHAR(255),
    is_admin        BOOLEAN DEFAULT FALSE,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 2. WORKOUTS TABLE
-- ============================================================
CREATE TABLE workouts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    name            VARCHAR(100) NOT NULL,
    category        VARCHAR(50) NOT NULL
                    CHECK (category IN ('cardio', 'strength', 'flexibility', 'hiit', 'yoga', 'sports', 'other')),
    description     TEXT,
    duration_minutes INTEGER NOT NULL CHECK (duration_minutes > 0),
    calories_burned INTEGER CHECK (calories_burned >= 0),
    intensity       VARCHAR(20) DEFAULT 'moderate'
                    CHECK (intensity IN ('low', 'moderate', 'high', 'extreme')),
    exercises       TEXT,
    scheduled_date  DATE,
    completed       BOOLEAN DEFAULT FALSE,
    completed_at    TIMESTAMP,
    notes           TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ============================================================
-- 3. DIET PLANS TABLE
-- ============================================================
CREATE TABLE diet_plans (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    meal_name       VARCHAR(100) NOT NULL,
    meal_type       VARCHAR(20) NOT NULL
                    CHECK (meal_type IN ('breakfast', 'lunch', 'dinner', 'snack', 'pre_workout', 'post_workout')),
    description     TEXT,
    calories        INTEGER NOT NULL CHECK (calories >= 0),
    protein_g       DECIMAL(6,2) DEFAULT 0,
    carbs_g         DECIMAL(6,2) DEFAULT 0,
    fats_g          DECIMAL(6,2) DEFAULT 0,
    fiber_g         DECIMAL(6,2) DEFAULT 0,
    ingredients     TEXT,
    scheduled_date  DATE,
    consumed        BOOLEAN DEFAULT FALSE,
    consumed_at     TIMESTAMP,
    notes           TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ============================================================
-- 4. PROGRESS RECORDS TABLE
-- ============================================================
CREATE TABLE progress_records (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    record_date     DATE NOT NULL,
    weight_kg       DECIMAL(5,2),
    body_fat_percent DECIMAL(5,2),
    muscle_mass_kg   DECIMAL(5,2),
    chest_cm        DECIMAL(5,2),
    waist_cm        DECIMAL(5,2),
    hips_cm         DECIMAL(5,2),
    arms_cm         DECIMAL(5,2),
    thighs_cm       DECIMAL(5,2),
    notes           TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ============================================================
-- 5. WATER INTAKE TABLE
-- ============================================================
CREATE TABLE water_intake (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    intake_date     DATE NOT NULL,
    amount_ml       INTEGER NOT NULL CHECK (amount_ml > 0),
    total_daily_goal_ml INTEGER DEFAULT 2500,
    recorded_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ============================================================
-- 6. SLEEP TRACKING TABLE
-- ============================================================
CREATE TABLE sleep_tracking (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    sleep_date      DATE NOT NULL,
    bed_time        TIME,
    wake_time       TIME,
    duration_hours  DECIMAL(4,2),
    quality         VARCHAR(20) CHECK (quality IN ('poor', 'fair', 'good', 'excellent')),
    interruptions   INTEGER DEFAULT 0,
    notes           TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ============================================================
-- 7. BMI HISTORY TABLE
-- ============================================================
CREATE TABLE bmi_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    height_cm       DECIMAL(5,2) NOT NULL,
    weight_kg       DECIMAL(5,2) NOT NULL,
    bmi_value       DECIMAL(5,2) NOT NULL,
    bmi_category    VARCHAR(30) NOT NULL
                    CHECK (bmi_category IN ('underweight', 'normal', 'overweight', 'obese')),
    calculated_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ============================================================
-- 8. CONTACT MESSAGES TABLE
-- ============================================================
CREATE TABLE contact_messages (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            VARCHAR(100) NOT NULL,
    email           VARCHAR(100) NOT NULL,
    subject         VARCHAR(200),
    message         TEXT NOT NULL,
    is_read         BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_workouts_user ON workouts(user_id);
CREATE INDEX IF NOT EXISTS idx_workouts_date ON workouts(scheduled_date);
CREATE INDEX IF NOT EXISTS idx_diet_user ON diet_plans(user_id);
CREATE INDEX IF NOT EXISTS idx_diet_date ON diet_plans(scheduled_date);
CREATE INDEX IF NOT EXISTS idx_progress_user ON progress_records(user_id);
CREATE INDEX IF NOT EXISTS idx_progress_date ON progress_records(record_date);
CREATE INDEX IF NOT EXISTS idx_water_user ON water_intake(user_id);
CREATE INDEX IF NOT EXISTS idx_water_date ON water_intake(intake_date);
CREATE INDEX IF NOT EXISTS idx_sleep_user ON sleep_tracking(user_id);
CREATE INDEX IF NOT EXISTS idx_sleep_date ON sleep_tracking(sleep_date);
CREATE INDEX IF NOT EXISTS idx_bmi_user ON bmi_history(user_id);

-- ============================================================
-- SEED DATA (Default admin and sample data)
-- ============================================================

-- Insert default admin user (password: admin123 - hashed)
INSERT INTO users (username, email, password_hash, full_name, age, gender, is_admin, is_active) 
VALUES ('admin', 'admin@fitpro.ai', 'scrypt:32768:8:1$9FIIkRhMn46EiNJl$4507fa1c221a7c7c5bbbc2d67f6efd4f2ce96e68a442d2f27e9ebe0e78919a92044779472b744c7579a87a2234cca5d559d79b43cc11ab8cce485e8a62cf75fa', 'System Admin', 30, 'male', TRUE, TRUE);

-- Insert sample workout categories reference data
INSERT INTO workouts (user_id, name, category, description, duration_minutes, calories_burned, intensity, exercises) VALUES
(1, 'Morning Cardio Blast', 'cardio', 'High-energy cardio workout to start your day', 30, 300, 'moderate', 'Jumping Jacks, High Knees, Burpees, Mountain Climbers'),
(1, 'Upper Body Strength', 'strength', 'Focus on chest, shoulders, and arms', 45, 250, 'high', 'Push-ups, Dumbbell Press, Shoulder Press, Bicep Curls'),
(1, 'Yoga Flow', 'flexibility', 'Relaxing yoga session for flexibility', 60, 150, 'low', 'Sun Salutation, Warrior Poses, Tree Pose, Child Pose');

-- Insert sample diet entries
INSERT INTO diet_plans (user_id, meal_name, meal_type, description, calories, protein_g, carbs_g, fats_g, fiber_g, ingredients) VALUES
(1, 'Protein Oatmeal', 'breakfast', 'High-protein oatmeal with fruits', 350, 20, 45, 8, 6, 'Oats, Protein Powder, Banana, Almonds, Honey'),
(1, 'Grilled Chicken Salad', 'lunch', 'Lean protein with fresh vegetables', 450, 40, 25, 15, 8, 'Chicken Breast, Mixed Greens, Tomatoes, Cucumber, Olive Oil'),
(1, 'Salmon with Quinoa', 'dinner', 'Omega-3 rich salmon with healthy grains', 550, 35, 40, 20, 5, 'Salmon Fillet, Quinoa, Asparagus, Lemon, Herbs');
