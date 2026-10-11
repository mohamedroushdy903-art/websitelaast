import os
import re
import sqlite3
from functools import wraps
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    g
)
from werkzeug.security import generate_password_hash, check_password_hash

DATABASE = os.path.join(os.path.dirname(__file__), 'users.db')

app = Flask(__name__)
app.config['DATABASE'] = DATABASE
# Secret key for session management
app.secret_key = os.environ.get('SECRET_KEY', 'anu-lab2-db-systems-fall-2026-secret')

def get_db():
    """Get database connection for the current request context with Foreign Keys enabled."""
    if 'db' not in g:
        db_path = app.config.get('DATABASE', DATABASE)
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
        # Enforce foreign key constraints in SQLite
        g.db.execute("PRAGMA foreign_keys = ON;")
    return g.db

@app.teardown_appcontext
def close_db(exception):
    """Close database connection at end of request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db(db_path=None):
    """Initialize SQLite database tables using database/schema.sql and ensure admin role column."""
    if db_path is None:
        db_path = app.config.get('DATABASE', DATABASE)
    db = sqlite3.connect(db_path)
    db.execute("PRAGMA foreign_keys = ON;")
    
    schema_path = os.path.join(os.path.dirname(__file__), 'database', 'schema.sql')
    if not os.path.exists(schema_path):
        schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
        
    with open(schema_path, 'r', encoding='utf-8') as f:
        db.executescript(f.read())

    # Migrate: Ensure is_admin column exists in users table
    cursor = db.cursor()
    cursor.execute("PRAGMA table_info(users)")
    cols = [r[1] for r in cursor.fetchall()]
    if 'is_admin' not in cols:
        cursor.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0")

    # Automatically grant admin privileges to account #1 and the owner email
    cursor.execute("UPDATE users SET is_admin = 1 WHERE id = 1 OR email = 'mohamedroushdy903@gmail.com' OR email LIKE '%admin%'")

    db.commit()
    db.close()

# Auto-initialize database on application launch
with app.app_context():
    init_db()

def login_required(f):
    """Decorator to protect authenticated routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to restrict access strictly to Administrators (Privacy Protection)."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in as an administrator.', 'warning')
            return redirect(url_for('login'))

        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT is_admin FROM users WHERE id = ?", (session['user_id'],))
        user = cursor.fetchone()

        if not user or not user['is_admin']:
            flash('Access Denied: Only Administrators can inspect the database.', 'danger')
            return redirect(url_for('dashboard'))

        return f(*args, **kwargs)
    return decorated_function

# =========================================================================
# Authentication Routes (R1–R3, R9)
# =========================================================================

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Please fill in all fields.', 'danger')
            return render_template('login.html', email=email)

        db = get_db()
        cursor = db.cursor()
        # Parameterized query preventing SQL injection
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()

        # Generic error message to prevent account enumeration
        if user and check_password_hash(user['password_hash'], password):
            session.clear()
            session['user_id'] = user['id']
            session['user_name'] = user['full_name']
            session['user_email'] = user['email']
            session['is_admin'] = bool(user['is_admin'])
            flash(f'Welcome back, {user["full_name"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'danger')
            return render_template('login.html', email=email)

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Server-side validation
        if not full_name or not email or not password or not confirm_password:
            flash('All fields are required.', 'danger')
            return render_template('register.html', full_name=full_name, email=email)

        email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(email_regex, email):
            flash('Please enter a valid email address.', 'danger')
            return render_template('register.html', full_name=full_name, email=email)

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('register.html', full_name=full_name, email=email)

        if password != confirm_password:
            flash('Passwords do not match. Please try again.', 'danger')
            return render_template('register.html', full_name=full_name, email=email)

        db = get_db()
        cursor = db.cursor()

        # Check for existing email (R2: Email Already Exists)
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            flash('Email Already Exists.', 'danger')
            return render_template('register.html', full_name=full_name, email=email)

        # Secure password hashing (PBKDF2 SHA-256)
        password_hash = generate_password_hash(password, method='pbkdf2:sha256')

        try:
            cursor.execute(
                "INSERT INTO users (full_name, email, password_hash, is_admin) VALUES (?, ?, ?, 0)",
                (full_name, email, password_hash)
            )
            db.commit()
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Email Already Exists.', 'danger')
            return render_template('register.html', full_name=full_name, email=email)

    return render_template('register.html')

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))

# =========================================================================
# To-Do List Routes (R4–R7, R9, Bonus Features)
# =========================================================================

@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()

    # User details with is_admin flag
    cursor.execute("SELECT id, full_name, email, is_admin, created_at FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()

    if not user:
        session.clear()
        flash('User session expired. Please log in again.', 'warning')
        return redirect(url_for('login'))

    # Private list: user sees ONLY their own to-dos (R9)
    cursor.execute(
        """
        SELECT id, user_id, title, description, due_date, is_done, created_at
        FROM todos
        WHERE user_id = ?
        ORDER BY is_done ASC, due_date ASC, id DESC
        """,
        (user_id,)
    )
    todos = cursor.fetchall()

    # Bonus: Count stats
    total_count = len(todos)
    open_count = sum(1 for t in todos if t['is_done'] == 0)
    done_count = total_count - open_count

    return render_template(
        'dashboard.html',
        user=user,
        todos=todos,
        total_count=total_count,
        open_count=open_count,
        done_count=done_count
    )

@app.route('/todos/add', methods=['POST'])
@login_required
def add_todo():
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    due_date = request.form.get('due_date', '').strip()

    if not title:
        flash('Task title cannot be empty.', 'danger')
        return redirect(url_for('dashboard'))

    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO todos (user_id, title, description, due_date, is_done) VALUES (?, ?, ?, ?, 0)",
        (session['user_id'], title, description, due_date)
    )
    db.commit()
    flash('Task added successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/todos/<int:todo_id>/toggle', methods=['POST'])
@login_required
def toggle_todo(todo_id):
    db = get_db()
    cursor = db.cursor()
    # Private enforcement: WHERE id = ? AND user_id = ?
    cursor.execute(
        "UPDATE todos SET is_done = CASE WHEN is_done = 1 THEN 0 ELSE 1 END WHERE id = ? AND user_id = ?",
        (todo_id, session['user_id'])
    )
    db.commit()
    flash('Task status updated.', 'info')
    return redirect(url_for('dashboard'))

@app.route('/todos/<int:todo_id>/edit', methods=['POST'])
@login_required
def edit_todo(todo_id):
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    due_date = request.form.get('due_date', '').strip()

    if not title:
        flash('Task title cannot be empty.', 'danger')
        return redirect(url_for('dashboard'))

    db = get_db()
    cursor = db.cursor()
    # Private enforcement: WHERE id = ? AND user_id = ?
    cursor.execute(
        "UPDATE todos SET title = ?, description = ?, due_date = ? WHERE id = ? AND user_id = ?",
        (title, description, due_date, todo_id, session['user_id'])
    )
    db.commit()
    flash('Task updated successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/todos/<int:todo_id>/delete', methods=['POST'])
@login_required
def delete_todo(todo_id):
    db = get_db()
    cursor = db.cursor()
    # Private enforcement: WHERE id = ? AND user_id = ?
    cursor.execute(
        "DELETE FROM todos WHERE id = ? AND user_id = ?",
        (todo_id, session['user_id'])
    )
    db.commit()
    flash('Task deleted successfully.', 'info')
    return redirect(url_for('dashboard'))

# =========================================================================
# Protected Database Inspection Route (Admin Only for Privacy)
# =========================================================================

@app.route('/admin')
@app.route('/users')
@login_required
@admin_required
def admin_users():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, full_name, email, password_hash, is_admin, created_at FROM users ORDER BY id ASC")
    users = cursor.fetchall()
    
    cursor.execute(
        """
        SELECT t.id, t.user_id, u.full_name as author, t.title, t.due_date, t.is_done, t.created_at
        FROM todos t
        JOIN users u ON t.user_id = u.id
        ORDER BY t.id ASC
        """
    )
    todos = cursor.fetchall()
    
    return render_template('admin_users.html', users=users, todos=todos)

@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_user(user_id):
    if user_id == session['user_id']:
        flash('You cannot delete your own active administrator account.', 'warning')
        return redirect(url_for('admin_users'))

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT full_name FROM users WHERE id = ?", (user_id,))
    target_user = cursor.fetchone()

    if target_user:
        # ON DELETE CASCADE automatically removes all child to-do tasks
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        db.commit()
        flash(f'User "{target_user["full_name"]}" and all their associated tasks have been deleted via ON DELETE CASCADE.', 'success')
    else:
        flash('User not found.', 'danger')

    return redirect(url_for('admin_users'))

@app.route('/admin/todos/<int:todo_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_todo(todo_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
    db.commit()
    flash(f'Task #{todo_id} has been deleted by administrator.', 'info')
    return redirect(url_for('admin_users'))

if __name__ == '__main__':
    print("Launching ANU Database Systems Lab 2 App on http://127.0.0.1:5000 (Local) and http://0.0.0.0:5000 (LAN) ...")
    app.run(debug=True, host='0.0.0.0', port=5000)
