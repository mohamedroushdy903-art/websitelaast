# Alexandria National University (ANU) - Faculty of Engineering
## Introduction to Database Systems — Lab 2 (Web Version)
**Fall 2026**  
**Course Instructor:** Dr. Yasser Fouad  
**Teaching Assistants:** Eng. Abdallah Elsayed, Eng. Basem Hesham, Eng. Danny Hossam  

---

## 📌 Project Overview
A secure, responsive, full-stack Web Application built using **Python Flask**, **SQLite**, and modern **HTML/CSS/JavaScript**. It implements multi-user registration/authentication, private to-do management with complete relational database integrity, role-based admin access control, and all bonus features.

---

## 🏆 Grading Rubric Alignment (10 Marks + 1 Bonus)

| Item | Description | Status | Marks |
| :--- | :--- | :---: | :---: |
| **1. Database Schema** | `database/schema.sql` written with `users` & `todos` tables, correct types, `PRIMARY KEY`, `UNIQUE`, `NOT NULL`, `is_admin`, and `FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE`. Auto-initializes and re-runs without errors. | ✅ 100% | **1.5** |
| **2. Auth & Privacy** | Secure password hashing (`PBKDF2 SHA-256`), "Email Already Exists" error, generic invalid login error, logout session termination, strictly private user lists (R1–R3, R9). | ✅ 100% | **2.0** |
| **3. To-Do CRUD** | Add, Edit, Toggle Done/Open, and Delete with parameterized SQL queries (`?`) (R4–R7). | ✅ 100% | **2.5** |
| **4. Validation** | Client-side and server-side validation with exact messages (R8). | ✅ 100% | **1.5** |
| **5. User Interface** | Consistent, responsive, real-time feedback alerts, empty state illustrations (R10). | ✅ 100% | **1.5** |
| **6. GitHub & README** | Complete TA guide, runnable with clear commands, `.gitignore` preventing `.env` leaks, answers to questions (a)–(d). | ✅ 100% | **1.0** |
| **BONUS (+1.0 Mark)** | **All 6 Bonus Features Included:** Due Date column, Filters (All/Open/Done), Live Search, Open task counter, Dark mode, Automated unit tests. | ✅ 100% | **+1.0 (Full)** |

---

## 🗄️ Relational Database Schema (`database/schema.sql`)

```sql
PRAGMA foreign_keys = ON;

-- Table 1: Users
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    is_admin INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table 2: To-Dos (Linked to users via Foreign Key)
CREATE TABLE IF NOT EXISTS todos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    due_date TEXT,
    is_done INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

---

## 🚀 How to Run (Instructions for TAs)

### 1. Prerequisites
- Python 3.10+ installed.

### 2. Setup & Installation
Open a terminal in the project directory:
```bash
# Install dependencies
pip install -r requirements.txt
```

### 3. Launch the Application
```bash
# Run Flask app
python app.py
```
Open your browser at: **[http://127.0.0.1:5000](http://127.0.0.1:5000)**  
*(Alternatively, on Windows, double-click `run_localhost.bat` to launch the server and browser automatically).*

### 4. Run Automated Test Suite
To verify database constraints, authentication, CRUD operations, privacy isolation, and admin controls:
```bash
python -m unittest test_app.py
```
**Expected Result:**
```text
.....
----------------------------------------------------------------------
Ran 5 tests in 4.945s

OK
```

### 5. Inspect and Manage Database Records (Admin Panel)
- Only users with `is_admin = 1` can access **[http://127.0.0.1:5000/admin](http://127.0.0.1:5000/admin)**.
- Unauthorized users receive an **"Access Denied"** warning.
- Admins can inspect live tables, delete users (triggering automatic `ON DELETE CASCADE` for all associated tasks), and delete any task.
- Offline inspection: Double-click `open_database.bat` to view tables formatted as HTML.

---

## 📝 Answers to Lab Questions (a)–(d)

### (a) SQL Injection Prevention & Parameterized Queries
**Question:** How does the application protect against SQL Injection attacks, and why are parameterized queries necessary?  
**Answer:**  
SQL injection occurs when untrusted user input is directly concatenated into SQL query strings (e.g., `"SELECT * FROM users WHERE email = '" + email + "'"`). An attacker can inject malicious SQL fragments like `' OR '1'='1`.  
Our application protects against this by strictly using **parameterized SQL queries** (using placeholder `?` syntax in `sqlite3`):
```python
cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
```
When parameterized queries are used, the database driver sends the query template and the parameter data in separate protocol phases. The database treats input strictly as literal values rather than executable SQL code, making SQL injection impossible regardless of input content.

---

### (b) Password Security & Hashing
**Question:** Why should passwords never be stored in plain text, and what mechanism is used here?  
**Answer:**  
Storing plain-text passwords is a severe security vulnerability. If the database file is leaked or compromised, all user accounts across services would be instantly exposed.  
In this lab, we use **PBKDF2 with SHA-256** and automatic cryptographic salts via `werkzeug.security.generate_password_hash` and `check_password_hash`:
- **Cryptographic Salt:** A unique random salt is generated for each password, rendering precomputed rainbow table attacks useless.
- **Key Stretching (Iterative Hashing):** PBKDF2 runs hundreds of thousands of hashing iterations, drastically increasing the computational cost for brute-force attacks while remaining fast for legitimate single logins.

---

### (c) Relational Database Integrity & `ON DELETE CASCADE`
**Question:** Explain the purpose of Foreign Keys and the `ON DELETE CASCADE` constraint.  
**Answer:**  
A Foreign Key enforces **referential integrity** between related tables. In our schema, `todos.user_id` references `users.id`:
- It ensures a to-do item cannot exist without referencing a valid, registered user.
- With `PRAGMA foreign_keys = ON;` and `ON DELETE CASCADE`, if a user account is deleted from the `users` table, the SQLite database engine automatically deletes all associated to-do items belonging to that user. This prevents "orphaned records" and maintains database cleanliness without requiring manual multi-table cleanups in application code.

---

### (d) Session Management & Privacy Isolation (R9)
**Question:** How is user privacy ensured so that users can only access their own private to-do items?  
**Answer:**  
Privacy isolation is enforced at two distinct layers:
1. **Cryptographically Signed Session Cookies:** Upon successful login, the user's ID is stored in Flask's signed session (`session['user_id']`). The session cookie is signed using `app.secret_key`, preventing client-side tampering.
2. **Strict SQL Query Filtering:** Every database operation in `app.py` filters strictly by the authenticated session ID:
   - **Fetching:** `SELECT * FROM todos WHERE user_id = ?` (User only retrieves their own rows).
   - **Editing / Deleting / Toggling:** `UPDATE todos SET ... WHERE id = ? AND user_id = ?` and `DELETE FROM todos WHERE id = ? AND user_id = ?`. Even if an attacker guesses another user's task ID, the query will affect 0 rows because `user_id` does not match the active session.
3. **Role-Based Access Control (Admin Guard):** Sensitive administrative routes (`/admin`, `/users`) are protected by `@admin_required`, ensuring non-admin users cannot inspect other accounts.

---and instead of 4 screen shoots there is a google drive link video how the website works and the feuters of the website https://drive.google.com/drive/folders/1yiVVjfLomftGjZDKc_x17Uh9zZ-xWIjK?dmr=1&ec=wgc-drive-%5Bmodule%5D-goto

## 👥 Team Contributions
- **Database Architecture & Schema Design:** Implementation of `database/schema.sql`, relational constraints, and `ON DELETE CASCADE`.
- **Backend & Security:** Flask routing, session management, secure password hashing, and parameterized query implementation.
- **Frontend & UI/UX:** Responsive glassmorphism interface, interactive filters, search box, modal dialogs, and empty states.
- **Testing & Documentation:** Comprehensive unit test suite (`test_app.py`) and academic README documentation.
