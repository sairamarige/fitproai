"""
FitPro AI - Database Module
===========================
Handles all database operations with support for both SQLite and MySQL.
Provides connection management, query execution, and schema initialization.
"""

import os
import sqlite3
from datetime import datetime, date
from contextlib import contextmanager
from typing import Optional, List, Dict, Any, Tuple

try:
    import pymysql
    from pymysql.cursors import DictCursor
except ImportError:
    pymysql = None
    DictCursor = None

from config import get_config


class Database:
    """Database manager supporting SQLite and MySQL backends."""

    def __init__(self):
        self.config = get_config()
        self.db_type = self.config.DB_TYPE
        self._connection = None

    # ============================================================
    # CONNECTION MANAGEMENT
    # ============================================================

    def connect(self):
        """Create and return a database connection."""
        if self.db_type == 'mysql':
            if pymysql is None:
                raise RuntimeError(
                    "DB_TYPE is set to 'mysql' but the pymysql package isn't installed. "
                    "Run: pip install pymysql cryptography"
                )
            return pymysql.connect(
                host=self.config.MYSQL_HOST,
                port=self.config.MYSQL_PORT,
                user=self.config.MYSQL_USER,
                password=self.config.MYSQL_PASSWORD,
                database=self.config.MYSQL_DATABASE,
                charset='utf8mb4',
                cursorclass=DictCursor
            )
        else:
            # SQLite
            conn = sqlite3.connect(
                self.config.SQLITE_DB_PATH,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
            )
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            return conn

    @contextmanager
    def get_cursor(self):
        """Context manager for database cursor."""
        conn = self.connect()
        cursor = conn.cursor()
        try:
            yield cursor, conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    def execute(self, query: str, params: tuple = ()) -> int:
        """Execute a single query and return last row id."""
        with self.get_cursor() as (cursor, conn):
            cursor.execute(query, params)
            return cursor.lastrowid

    def fetchone(self, query: str, params: tuple = ()) -> Optional[Dict]:
        """Execute query and return single result as dict."""
        with self.get_cursor() as (cursor, conn):
            cursor.execute(query, params)
            row = cursor.fetchone()
            if row is None:
                return None
            if self.db_type == 'mysql':
                return dict(row)
            return dict(row)

    def fetchall(self, query: str, params: tuple = ()) -> List[Dict]:
        """Execute query and return all results as list of dicts."""
        with self.get_cursor() as (cursor, conn):
            cursor.execute(query, params)
            rows = cursor.fetchall()
            if self.db_type == 'mysql':
                return [dict(row) for row in rows]
            return [dict(row) for row in rows]

    # ============================================================
    # SCHEMA INITIALIZATION
    # ============================================================

    def init_schema(self):
        """Initialize database schema from fitpro.sql file.
        Only creates tables if they don't already exist."""
        schema_path = os.path.join(os.path.dirname(__file__), 'fitpro.sql')
        with open(schema_path, 'r') as f:
            schema_sql = f.read()

        conn = self.connect()
        cursor = conn.cursor()
        try:
            # Check if tables already exist (check users table as reference)
            try:
                cursor.execute("SELECT 1 FROM users LIMIT 1")
                print(f"Database already initialized ({self.db_type})")
                return  # Skip initialization if tables exist
            except:
                pass  # Table doesn't exist, proceed with initialization

            # Remove DROP TABLE statements to avoid data loss
            import re
            clean_sql = re.sub(r'DROP TABLE IF EXISTS \w+;?\s*', '', schema_sql, flags=re.IGNORECASE)

            # Execute schema creation
            cursor.executescript(clean_sql)
            conn.commit()
            print(f"Database schema initialized ({self.db_type})")
        except Exception as e:
            print(f"Schema initialization warning: {e}")
        finally:
            cursor.close()
            conn.close()

    def init_app(self, app):
        """Initialize database with Flask app context."""
        self.init_schema()

    # ============================================================
    # USER OPERATIONS
    # ============================================================

    def create_user(self, username: str, email: str, password_hash: str,
                    full_name: str = None, age: int = None, gender: str = None,
                    height_cm: float = None, weight_kg: float = None,
                    fitness_goal: str = None, activity_level: str = None) -> int:
        """Create a new user and return the user ID."""
        query = """
            INSERT INTO users (username, email, password_hash, full_name, age, gender,
                             height_cm, weight_kg, fitness_goal, activity_level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        return self.execute(query, (username, email, password_hash, full_name,
                                    age, gender, height_cm, weight_kg,
                                    fitness_goal, activity_level))

    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user by ID."""
        return self.fetchone("SELECT * FROM users WHERE id = ?", (user_id,))

    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username."""
        return self.fetchone("SELECT * FROM users WHERE username = ?", (username,))

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email."""
        return self.fetchone("SELECT * FROM users WHERE email = ?", (email,))

    def update_user(self, user_id: int, **kwargs) -> bool:
        """Update user fields dynamically."""
        allowed_fields = ['full_name', 'age', 'gender', 'height_cm', 'weight_kg',
                         'fitness_goal', 'activity_level', 'profile_image']
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields and v is not None}
        if not updates:
            return False

        set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
        query = f"UPDATE users SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
        self.execute(query, tuple(updates.values()) + (user_id,))
        return True

    def get_all_users(self) -> List[Dict]:
        """Get all users, most recently created first."""
        return self.fetchall("SELECT * FROM users ORDER BY created_at DESC")

    def set_user_admin(self, user_id: int, is_admin: bool) -> bool:
        """Grant or revoke admin rights for a user."""
        self.execute(
            "UPDATE users SET is_admin = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (1 if is_admin else 0, user_id)
        )
        return True

    def set_user_active(self, user_id: int, is_active: bool) -> bool:
        """Activate or deactivate (soft-disable) a user account."""
        self.execute(
            "UPDATE users SET is_active = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (1 if is_active else 0, user_id)
        )
        return True

    def delete_user(self, user_id: int) -> bool:
        """Permanently delete a user and all their related records."""
        self.execute("DELETE FROM users WHERE id = ?", (user_id,))
        return True

    # ============================================================
    # WORKOUT OPERATIONS
    # ============================================================

    def create_workout(self, user_id: int, name: str, category: str,
                       duration_minutes: int, calories_burned: int = None,
                       intensity: str = 'moderate', description: str = None,
                       exercises: str = None, scheduled_date: str = None) -> int:
        """Create a new workout entry."""
        query = """
            INSERT INTO workouts (user_id, name, category, description, duration_minutes,
                                calories_burned, intensity, exercises, scheduled_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        return self.execute(query, (user_id, name, category, description,
                                    duration_minutes, calories_burned, intensity,
                                    exercises, scheduled_date))

    def get_user_workouts(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get all workouts for a user."""
        return self.fetchall(
            "SELECT * FROM workouts WHERE user_id = ? ORDER BY scheduled_date DESC, created_at DESC LIMIT ?",
            (user_id, limit)
        )

    def get_workout_by_id(self, workout_id: int, user_id: int = None) -> Optional[Dict]:
        """Get workout by ID, optionally filtered by user."""
        if user_id:
            return self.fetchone(
                "SELECT * FROM workouts WHERE id = ? AND user_id = ?",
                (workout_id, user_id)
            )
        return self.fetchone("SELECT * FROM workouts WHERE id = ?", (workout_id,))

    def update_workout(self, workout_id: int, user_id: int, **kwargs) -> bool:
        """Update workout fields."""
        allowed = ['name', 'category', 'description', 'duration_minutes',
                  'calories_burned', 'intensity', 'exercises', 'scheduled_date',
                  'completed', 'completed_at', 'notes']
        updates = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
        if not updates:
            return False

        set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
        query = f"UPDATE workouts SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?"
        self.execute(query, tuple(updates.values()) + (workout_id, user_id))
        return True

    def delete_workout(self, workout_id: int, user_id: int) -> bool:
        """Delete a workout."""
        self.execute("DELETE FROM workouts WHERE id = ? AND user_id = ?", (workout_id, user_id))
        return True

    def get_workout_stats(self, user_id: int) -> Dict:
        """Get workout statistics for dashboard."""
        today = date.today().isoformat()
        # Total workouts
        total = self.fetchone(
            "SELECT COUNT(*) as count FROM workouts WHERE user_id = ?",
            (user_id,)
        )
        # Completed workouts
        completed = self.fetchone(
            "SELECT COUNT(*) as count FROM workouts WHERE user_id = ? AND completed = 1",
            (user_id,)
        )
        # Today's workout
        today_workout = self.fetchone(
            "SELECT * FROM workouts WHERE user_id = ? AND scheduled_date = ? ORDER BY created_at DESC LIMIT 1",
            (user_id, today)
        )
        # Total calories burned
        calories = self.fetchone(
            "SELECT COALESCE(SUM(calories_burned), 0) as total FROM workouts WHERE user_id = ? AND completed = 1",
            (user_id,)
        )
        # This week's workouts
        week_workouts = self.fetchone(
            """SELECT COUNT(*) as count FROM workouts 
               WHERE user_id = ? AND scheduled_date >= date('now', '-7 days')""",
            (user_id,)
        )

        return {
            'total_workouts': total['count'] if total else 0,
            'completed_workouts': completed['count'] if completed else 0,
            'today_workout': today_workout,
            'total_calories': calories['total'] if calories else 0,
            'week_workouts': week_workouts['count'] if week_workouts else 0
        }

    # ============================================================
    # DIET OPERATIONS
    # ============================================================

    def create_diet_plan(self, user_id: int, meal_name: str, meal_type: str,
                         calories: int, protein_g: float = 0, carbs_g: float = 0,
                         fats_g: float = 0, fiber_g: float = 0, description: str = None,
                         ingredients: str = None, scheduled_date: str = None) -> int:
        """Create a new diet plan entry."""
        query = """
            INSERT INTO diet_plans (user_id, meal_name, meal_type, description, calories,
                                   protein_g, carbs_g, fats_g, fiber_g, ingredients, scheduled_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        return self.execute(query, (user_id, meal_name, meal_type, description,
                                    calories, protein_g, carbs_g, fats_g, fiber_g,
                                    ingredients, scheduled_date))

    def get_user_diet_plans(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get all diet plans for a user."""
        return self.fetchall(
            "SELECT * FROM diet_plans WHERE user_id = ? ORDER BY scheduled_date DESC, created_at DESC LIMIT ?",
            (user_id, limit)
        )

    def get_diet_by_id(self, diet_id: int, user_id: int) -> Optional[Dict]:
        """Get diet plan by ID."""
        return self.fetchone(
            "SELECT * FROM diet_plans WHERE id = ? AND user_id = ?",
            (diet_id, user_id)
        )

    def update_diet(self, diet_id: int, user_id: int, **kwargs) -> bool:
        """Update diet plan fields."""
        allowed = ['meal_name', 'meal_type', 'description', 'calories',
                  'protein_g', 'carbs_g', 'fats_g', 'fiber_g', 'ingredients',
                  'scheduled_date', 'consumed', 'consumed_at', 'notes']
        updates = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
        if not updates:
            return False

        set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
        query = f"UPDATE diet_plans SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?"
        self.execute(query, tuple(updates.values()) + (diet_id, user_id))
        return True

    def delete_diet(self, diet_id: int, user_id: int) -> bool:
        """Delete a diet plan."""
        self.execute("DELETE FROM diet_plans WHERE id = ? AND user_id = ?", (diet_id, user_id))
        return True

    def get_diet_stats(self, user_id: int) -> Dict:
        """Get diet statistics for dashboard."""
        today = date.today().isoformat()
        # Total meals logged
        total = self.fetchone(
            "SELECT COUNT(*) as count FROM diet_plans WHERE user_id = ?",
            (user_id,)
        )
        # Today's calories
        today_calories = self.fetchone(
            "SELECT COALESCE(SUM(calories), 0) as total FROM diet_plans WHERE user_id = ? AND scheduled_date = ?",
            (user_id, today)
        )
        # Macros today
        today_macros = self.fetchone(
            """SELECT COALESCE(SUM(protein_g), 0) as protein, COALESCE(SUM(carbs_g), 0) as carbs, 
                      COALESCE(SUM(fats_g), 0) as fats 
               FROM diet_plans WHERE user_id = ? AND scheduled_date = ?""",
            (user_id, today)
        )

        return {
            'total_meals': total['count'] if total else 0,
            'today_calories': today_calories['total'] if today_calories else 0,
            'today_protein': today_macros['protein'] if today_macros else 0,
            'today_carbs': today_macros['carbs'] if today_macros else 0,
            'today_fats': today_macros['fats'] if today_macros else 0
        }

    # ============================================================
    # PROGRESS OPERATIONS
    # ============================================================

    def create_progress(self, user_id: int, record_date: str, weight_kg: float = None,
                        body_fat_percent: float = None, muscle_mass_kg: float = None,
                        chest_cm: float = None, waist_cm: float = None,
                        hips_cm: float = None, arms_cm: float = None,
                        thighs_cm: float = None, notes: str = None) -> int:
        """Create a new progress record."""
        query = """
            INSERT INTO progress_records (user_id, record_date, weight_kg, body_fat_percent,
                                         muscle_mass_kg, chest_cm, waist_cm, hips_cm, arms_cm, thighs_cm, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        return self.execute(query, (user_id, record_date, weight_kg, body_fat_percent,
                                    muscle_mass_kg, chest_cm, waist_cm, hips_cm, arms_cm, thighs_cm, notes))

    def get_user_progress(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get all progress records for a user."""
        return self.fetchall(
            "SELECT * FROM progress_records WHERE user_id = ? ORDER BY record_date DESC LIMIT ?",
            (user_id, limit)
        )

    def get_progress_by_id(self, progress_id: int, user_id: int) -> Optional[Dict]:
        """Get progress record by ID."""
        return self.fetchone(
            "SELECT * FROM progress_records WHERE id = ? AND user_id = ?",
            (progress_id, user_id)
        )

    def update_progress(self, progress_id: int, user_id: int, **kwargs) -> bool:
        """Update progress record fields."""
        allowed = ['record_date', 'weight_kg', 'body_fat_percent', 'muscle_mass_kg',
                  'chest_cm', 'waist_cm', 'hips_cm', 'arms_cm', 'thighs_cm', 'notes']
        updates = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
        if not updates:
            return False

        set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
        query = f"UPDATE progress_records SET {set_clause} WHERE id = ? AND user_id = ?"
        self.execute(query, tuple(updates.values()) + (progress_id, user_id))
        return True

    def delete_progress(self, progress_id: int, user_id: int) -> bool:
        """Delete a progress record."""
        self.execute("DELETE FROM progress_records WHERE id = ? AND user_id = ?", (progress_id, user_id))
        return True

    # ============================================================
    # WATER INTAKE OPERATIONS
    # ============================================================

    def add_water_intake(self, user_id: int, amount_ml: int, intake_date: str = None) -> int:
        """Add water intake record."""
        if not intake_date:
            intake_date = date.today().isoformat()
        query = "INSERT INTO water_intake (user_id, intake_date, amount_ml) VALUES (?, ?, ?)"
        return self.execute(query, (user_id, intake_date, amount_ml))

    def get_water_intake(self, user_id: int, intake_date: str = None) -> List[Dict]:
        """Get water intake for a specific date."""
        if not intake_date:
            intake_date = date.today().isoformat()
        return self.fetchall(
            "SELECT * FROM water_intake WHERE user_id = ? AND intake_date = ? ORDER BY recorded_at",
            (user_id, intake_date)
        )

    def get_total_water_today(self, user_id: int) -> int:
        """Get total water intake for today."""
        today = date.today().isoformat()
        result = self.fetchone(
            "SELECT SUM(amount_ml) as total FROM water_intake WHERE user_id = ? AND intake_date = ?",
            (user_id, today)
        )
        return result['total'] if result and result['total'] else 0

    def delete_water_entry(self, entry_id: int, user_id: int) -> bool:
        """Delete a water intake entry."""
        self.execute("DELETE FROM water_intake WHERE id = ? AND user_id = ?", (entry_id, user_id))
        return True

    # ============================================================
    # SLEEP TRACKING OPERATIONS
    # ============================================================

    def add_sleep_record(self, user_id: int, sleep_date: str, bed_time: str = None,
                         wake_time: str = None, duration_hours: float = None,
                         quality: str = None, interruptions: int = 0, notes: str = None) -> int:
        """Add sleep tracking record."""
        query = """
            INSERT INTO sleep_tracking (user_id, sleep_date, bed_time, wake_time,
                                       duration_hours, quality, interruptions, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        return self.execute(query, (user_id, sleep_date, bed_time, wake_time,
                                    duration_hours, quality, interruptions, notes))

    def get_sleep_records(self, user_id: int, limit: int = 30) -> List[Dict]:
        """Get sleep records for a user."""
        return self.fetchall(
            "SELECT * FROM sleep_tracking WHERE user_id = ? ORDER BY sleep_date DESC LIMIT ?",
            (user_id, limit)
        )

    def get_last_sleep(self, user_id: int) -> Optional[Dict]:
        """Get most recent sleep record."""
        return self.fetchone(
            "SELECT * FROM sleep_tracking WHERE user_id = ? ORDER BY sleep_date DESC LIMIT 1",
            (user_id,)
        )

    def delete_sleep_record(self, record_id: int, user_id: int) -> bool:
        """Delete a sleep record."""
        self.execute("DELETE FROM sleep_tracking WHERE id = ? AND user_id = ?", (record_id, user_id))
        return True

    # ============================================================
    # BMI OPERATIONS
    # ============================================================

    def add_bmi_record(self, user_id: int, height_cm: float, weight_kg: float,
                       bmi_value: float, bmi_category: str) -> int:
        """Add BMI calculation record."""
        query = """
            INSERT INTO bmi_history (user_id, height_cm, weight_kg, bmi_value, bmi_category)
            VALUES (?, ?, ?, ?, ?)
        """
        return self.execute(query, (user_id, height_cm, weight_kg, bmi_value, bmi_category))

    def get_bmi_history(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get BMI history for a user."""
        return self.fetchall(
            "SELECT * FROM bmi_history WHERE user_id = ? ORDER BY calculated_at DESC LIMIT ?",
            (user_id, limit)
        )

    def get_latest_bmi(self, user_id: int) -> Optional[Dict]:
        """Get latest BMI record."""
        return self.fetchone(
            "SELECT * FROM bmi_history WHERE user_id = ? ORDER BY calculated_at DESC LIMIT 1",
            (user_id,)
        )

    # ============================================================
    # CONTACT MESSAGES
    # ============================================================

    def add_contact_message(self, name: str, email: str, subject: str, message: str) -> int:
        """Add contact form submission."""
        query = "INSERT INTO contact_messages (name, email, subject, message) VALUES (?, ?, ?, ?)"
        return self.execute(query, (name, email, subject, message))

    def get_contact_messages(self, limit: int = 100) -> List[Dict]:
        """Get all contact messages (admin)."""
        return self.fetchall(
            "SELECT * FROM contact_messages ORDER BY created_at DESC LIMIT ?",
            (limit,)
        )

    def mark_message_read(self, message_id: int) -> bool:
        """Mark contact message as read."""
        self.execute("UPDATE contact_messages SET is_read = TRUE WHERE id = ?", (message_id,))
        return True


# Global database instance
db = Database()


def init_db(app):
    """Initialize database with Flask app."""
    db.init_app(app)

