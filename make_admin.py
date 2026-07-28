"""
FitPro AI - Make a user an admin
================================
Usage:
    python make_admin.py <username>

Example:
    python make_admin.py sairam
"""

import sqlite3
import sys
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fitpro.db')


def main():
    if len(sys.argv) != 2:
        print("Usage: python make_admin.py <username>")
        sys.exit(1)

    username = sys.argv[1]

    if not os.path.exists(DB_PATH):
        print(f"Could not find fitpro.db at {DB_PATH}")
        print("Make sure you run this from your project folder, and that you've run the app at least once.")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT id, username, is_admin FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()

    if not user:
        print(f"No user found with username '{username}'.")
        cursor.execute("SELECT username FROM users")
        all_users = [row[0] for row in cursor.fetchall()]
        print("Available usernames:", ", ".join(all_users) if all_users else "(none found)")
        conn.close()
        sys.exit(1)

    user_id, uname, is_admin = user
    if is_admin:
        print(f"'{uname}' is already an admin.")
    else:
        cursor.execute("UPDATE users SET is_admin = 1 WHERE id = ?", (user_id,))
        conn.commit()
        print(f"Success: '{uname}' (id={user_id}) is now an admin.")
        print("Log out and log back in for the change to take effect.")

    conn.close()


if __name__ == '__main__':
    main()
