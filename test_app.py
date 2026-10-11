import unittest
import os
import sqlite3
from app import app, init_db

TEST_DB = os.path.join(os.path.dirname(__file__), 'test_anu_lab2.db')

class ANULab2DatabaseTestCase(unittest.TestCase):
    def setUp(self):
        # Configure isolated test database
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['DATABASE'] = TEST_DB
        self.client = app.test_client()

        # Clean old test DB if present
        if os.path.exists(TEST_DB):
            try:
                os.remove(TEST_DB)
            except Exception:
                pass

        with app.app_context():
            init_db(TEST_DB)

    def tearDown(self):
        # Cleanup isolated test database
        if os.path.exists(TEST_DB):
            try:
                os.remove(TEST_DB)
            except Exception:
                pass

    def test_schema_tables_and_foreign_keys(self):
        """Rubric Item 1: Verify both tables, constraints, and foreign key cascade delete."""
        self.assertTrue(os.path.exists(TEST_DB))
        conn = sqlite3.connect(TEST_DB)
        conn.execute("PRAGMA foreign_keys = ON;")
        cursor = conn.cursor()

        # Check users table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
        self.assertIsNotNone(cursor.fetchone())

        # Check todos table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='todos';")
        self.assertIsNotNone(cursor.fetchone())

        # Test Foreign Key Cascade Delete
        cursor.execute("INSERT INTO users (full_name, email, password_hash) VALUES ('Cascade Test', 'cascade@example.com', 'hash123')")
        user_id = cursor.lastrowid
        cursor.execute("INSERT INTO todos (user_id, title, due_date) VALUES (?, 'Cascade Task', '2026-12-31')", (user_id,))
        conn.commit()

        # Delete user and ensure child todo is automatically deleted
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()

        cursor.execute("SELECT * FROM todos WHERE user_id = ?", (user_id,))
        self.assertIsNone(cursor.fetchone())
        conn.close()

    def test_register_login_and_validation(self):
        """Rubric Item 2 & 4: Register, duplicate rejection, login error, and logout."""
        # Register User
        res = self.client.post('/register', data={
            'full_name': 'Alice Smith',
            'email': 'alice@example.com',
            'password': 'Password123!',
            'confirm_password': 'Password123!'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Registration successful', res.data)

        # Duplicate email registration must return exact error: 'Email Already Exists'
        res_dup = self.client.post('/register', data={
            'full_name': 'Alice Clone',
            'email': 'alice@example.com',
            'password': 'Password123!',
            'confirm_password': 'Password123!'
        }, follow_redirects=True)
        self.assertIn(b'Email Already Exists', res_dup.data)

        # Invalid login must return generic error
        res_invalid = self.client.post('/login', data={
            'email': 'alice@example.com',
            'password': 'WrongPassword'
        }, follow_redirects=True)
        self.assertIn(b'Invalid email or password', res_invalid.data)

        # Valid login
        res_valid = self.client.post('/login', data={
            'email': 'alice@example.com',
            'password': 'Password123!'
        }, follow_redirects=True)
        self.assertIn(b'Welcome back, Alice Smith!', res_valid.data)

        # Logout
        res_logout = self.client.get('/logout', follow_redirects=True)
        self.assertIn(b'logged out successfully', res_logout.data)

    def test_todo_crud_and_privacy_isolation(self):
        """Rubric Item 3 & R9: To-Do CRUD (Add, Edit, Done, Delete) & strict privacy isolation."""
        # 1. Register & Login as User 1 (Bob)
        self.client.post('/register', data={
            'full_name': 'Bob User',
            'email': 'bob@example.com',
            'password': 'BobPassword123!',
            'confirm_password': 'BobPassword123!'
        })
        self.client.post('/login', data={'email': 'bob@example.com', 'password': 'BobPassword123!'})

        # Add To-Do (R4) with Due Date (Bonus)
        add_res = self.client.post('/todos/add', data={
            'title': 'Bob Private Task',
            'description': 'Important assignment',
            'due_date': '2026-11-15'
        }, follow_redirects=True)
        self.assertIn(b'Task added successfully', add_res.data)
        self.assertIn(b'Bob Private Task', add_res.data)

        # Get Bob's todo ID from database
        conn = sqlite3.connect(TEST_DB)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT id, is_done FROM todos WHERE title = 'Bob Private Task'")
        bob_todo = cursor.fetchone()
        self.assertIsNotNone(bob_todo)
        todo_id = bob_todo['id']
        self.assertEqual(bob_todo['is_done'], 0)
        conn.close()

        # Toggle Done (R6)
        self.client.post(f'/todos/{todo_id}/toggle', follow_redirects=True)
        conn = sqlite3.connect(TEST_DB)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT is_done FROM todos WHERE id = ?", (todo_id,))
        self.assertEqual(cursor.fetchone()['is_done'], 1)
        conn.close()

        # Edit To-Do (R5)
        edit_res = self.client.post(f'/todos/{todo_id}/edit', data={
            'title': 'Bob Edited Task',
            'description': 'Updated details',
            'due_date': '2026-11-20'
        }, follow_redirects=True)
        self.assertIn(b'Task updated successfully', edit_res.data)

        # Logout Bob
        self.client.get('/logout')

        # 2. Register & Login as User 2 (Charlie)
        self.client.post('/register', data={
            'full_name': 'Charlie User',
            'email': 'charlie@example.com',
            'password': 'CharliePassword123!',
            'confirm_password': 'CharliePassword123!'
        })
        self.client.post('/login', data={'email': 'charlie@example.com', 'password': 'CharliePassword123!'})

        # Privacy Check: Charlie must NOT see Bob's task (R9)
        dash_res = self.client.get('/dashboard')
        self.assertNotIn(b'Bob Edited Task', dash_res.data)

        # Privacy Check: Charlie cannot toggle, edit, or delete Bob's task
        self.client.post(f'/todos/{todo_id}/toggle')
        self.client.post(f'/todos/{todo_id}/delete')

        # Verify Bob's task is still intact in DB
        conn = sqlite3.connect(TEST_DB)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM todos WHERE id = ?", (todo_id,))
        self.assertIsNotNone(cursor.fetchone())
        conn.close()

        # Logout Charlie & Login Bob again to test Bob's own deletion (R7)
        self.client.get('/logout')
        self.client.post('/login', data={'email': 'bob@example.com', 'password': 'BobPassword123!'})
        delete_res = self.client.post(f'/todos/{todo_id}/delete', follow_redirects=True)
        self.assertIn(b'Task deleted successfully', delete_res.data)

    def test_admin_privacy_protection(self):
        """Verify that normal users cannot access /admin, but admins can."""
        # 1. Register a regular user (is_admin = 0)
        self.client.post('/register', data={
            'full_name': 'Regular User',
            'email': 'regular@example.com',
            'password': 'RegularPass123!',
            'confirm_password': 'RegularPass123!'
        })
        self.client.post('/login', data={'email': 'regular@example.com', 'password': 'RegularPass123!'})

        # Regular user attempts to access /admin -> Access Denied!
        res_denied = self.client.get('/admin', follow_redirects=True)
        self.assertIn(b'Access Denied', res_denied.data)
        self.assertNotIn(b'SQLite Database Inspector', res_denied.data)
        self.client.get('/logout')

        # 2. Grant admin privileges in test DB
        conn = sqlite3.connect(TEST_DB)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_admin = 1 WHERE email = 'regular@example.com'")
        conn.commit()
        conn.close()

        # Admin logs in
        self.client.post('/login', data={'email': 'regular@example.com', 'password': 'RegularPass123!'})
        res_admin = self.client.get('/admin', follow_redirects=True)
        self.assertEqual(res_admin.status_code, 200)
        self.assertIn(b'Administrator Database Panel', res_admin.data)

    def test_admin_delete_functionality(self):
        """Verify that admin can delete users (triggering cascade delete) and tasks."""
        # Setup: Create Admin user and Target user with a task
        conn = sqlite3.connect(TEST_DB)
        conn.execute("PRAGMA foreign_keys = ON;")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (full_name, email, password_hash, is_admin) VALUES ('Super Admin', 'superadmin@example.com', 'hash', 1)")
        admin_id = cursor.lastrowid
        cursor.execute("INSERT INTO users (full_name, email, password_hash, is_admin) VALUES ('Bad User', 'baduser@example.com', 'hash', 0)")
        bad_user_id = cursor.lastrowid
        cursor.execute("INSERT INTO todos (user_id, title) VALUES (?, 'Bad User Task')", (bad_user_id,))
        bad_todo_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Login as Admin
        self.client.post('/login', data={'email': 'superadmin@example.com', 'password': 'hash'})
        # Force session
        with self.client.session_transaction() as sess:
            sess['user_id'] = admin_id
            sess['user_name'] = 'Super Admin'
            sess['is_admin'] = True

        # Admin deletes Bad User
        del_res = self.client.post(f'/admin/users/{bad_user_id}/delete', follow_redirects=True)
        self.assertIn(b'deleted via ON DELETE CASCADE', del_res.data)

        # Verify Bad User and their task are gone from database
        conn = sqlite3.connect(TEST_DB)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (bad_user_id,))
        self.assertIsNone(cursor.fetchone())
        cursor.execute("SELECT * FROM todos WHERE id = ?", (bad_todo_id,))
        self.assertIsNone(cursor.fetchone())
        conn.close()

if __name__ == '__main__':
    unittest.main()
