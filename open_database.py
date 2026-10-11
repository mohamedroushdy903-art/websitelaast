import os
import sqlite3
import webbrowser

db_path = os.path.join(os.path.dirname(__file__), 'users.db')
html_path = os.path.join(os.path.dirname(__file__), 'database_table.html')

if not os.path.exists(db_path):
    print("Database users.db does not exist yet. Please run the app and register a user first.")
    input("Press Enter to exit...")
    exit()

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# 1. Fetch Users
cursor.execute("SELECT id, full_name, email, password_hash, created_at FROM users ORDER BY id ASC")
users = cursor.fetchall()

# 2. Fetch Todos
cursor.execute("""
    SELECT t.id, t.user_id, u.full_name as author, t.title, t.description, t.due_date, t.is_done, t.created_at
    FROM todos t
    LEFT JOIN users u ON t.user_id = u.id
    ORDER BY t.id ASC
""")
todos = cursor.fetchall()
conn.close()

user_rows = ""
for u in users:
    user_rows += f"""
    <tr>
        <td><span class="badge">#{u['id']}</span></td>
        <td><strong>{u['full_name']}</strong></td>
        <td><a href="mailto:{u['email']}" style="color: #60a5fa;">{u['email']}</a></td>
        <td><code class="hash">{u['password_hash']}</code></td>
        <td style="color: #94a3b8;">{u['created_at']}</td>
    </tr>
    """

if not users:
    user_rows = "<tr><td colspan='5' style='text-align: center; padding: 1.5rem; color: #94a3b8;'>No users recorded yet.</td></tr>"

todo_rows = ""
for t in todos:
    status_badge = '<span class="badge" style="background: rgba(16,185,129,0.2); color: #6ee7b7;">Done</span>' if t['is_done'] else '<span class="badge" style="background: rgba(245,158,11,0.2); color: #fde047;">Open</span>'
    due = f"<span class='due-tag'>{t['due_date']}</span>" if t['due_date'] else "<span style='color: #64748b;'>None</span>"
    desc = f"<div style='color: #94a3b8; font-size: 0.85rem;'>{t['description']}</div>" if t['description'] else ""
    
    todo_rows += f"""
    <tr>
        <td><span class="badge">#{t['id']}</span></td>
        <td><span class="badge" style="border: 1px solid #f59e0b; color: #fde047;">User #{t['user_id']} ({t['author'] or 'Unknown'})</span></td>
        <td><strong>{t['title']}</strong>{desc}</td>
        <td>{due}</td>
        <td>{status_badge}</td>
        <td style="color: #94a3b8;">{t['created_at']}</td>
    </tr>
    """

if not todos:
    todo_rows = "<tr><td colspan='6' style='text-align: center; padding: 1.5rem; color: #94a3b8;'>No to-do tasks added yet.</td></tr>"

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AuthGuard - ANU Lab 2 Database Tables</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #0b0f19;
            color: #f8fafc;
            margin: 0;
            padding: 2.5rem 1.5rem;
        }}
        .container {{
            max-width: 1100px;
            margin: 0 auto;
            background: rgba(21, 30, 49, 0.85);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            padding: 2.5rem;
            box-shadow: 0 20px 50px rgba(0,0,0,0.5);
        }}
        h1 {{
            margin-top: 0;
            color: #818cf8;
            font-size: 1.8rem;
        }}
        h2 {{
            color: #cbd5e1;
            font-size: 1.3rem;
            margin-top: 2rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            padding-bottom: 0.5rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
            text-align: left;
        }}
        th {{
            background: rgba(255, 255, 255, 0.05);
            padding: 0.9rem;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #94a3b8;
            border-bottom: 2px solid rgba(255, 255, 255, 0.1);
        }}
        td {{
            padding: 0.9rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            font-size: 0.9rem;
        }}
        tr:hover td {{
            background: rgba(255, 255, 255, 0.02);
        }}
        .badge {{
            background: rgba(99, 102, 241, 0.2);
            color: #a5b4fc;
            padding: 0.2rem 0.6rem;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.8rem;
        }}
        .due-tag {{
            background: rgba(59, 130, 246, 0.15);
            color: #93c5fd;
            padding: 0.2rem 0.5rem;
            border-radius: 6px;
            font-size: 0.8rem;
            border: 1px solid rgba(59, 130, 246, 0.3);
        }}
        .hash {{
            background: rgba(0, 0, 0, 0.4);
            color: #a78bfa;
            padding: 0.25rem 0.5rem;
            border-radius: 6px;
            font-size: 0.75rem;
            display: block;
            word-break: break-all;
            max-width: 250px;
        }}
        .footer {{
            margin-top: 2.5rem;
            text-align: center;
            font-size: 0.85rem;
            color: #64748b;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Alexandria National University - Lab 2 Database Viewer</h1>
        <p style="color: #94a3b8;">Database File: <code>{db_path}</code> &bull; Relational SQLite with Foreign Keys</p>

        <!-- Table 1: Users -->
        <h2>
            <span>Table 1: <code>users</code> ({len(users)} records)</span>
            <span class="badge">Primary Key: id</span>
        </h2>
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Full Name</th>
                    <th>Email</th>
                    <th>Password Hash</th>
                    <th>Created At</th>
                </tr>
            </thead>
            <tbody>
                {user_rows}
            </tbody>
        </table>

        <!-- Table 2: Todos -->
        <h2>
            <span>Table 2: <code>todos</code> ({len(todos)} records)</span>
            <span class="badge" style="background: rgba(16,185,129,0.2); color: #6ee7b7;">FK: user_id ➔ users(id) ON DELETE CASCADE</span>
        </h2>
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Foreign Key (Author)</th>
                    <th>Task Title &amp; Description</th>
                    <th>Due Date (Bonus)</th>
                    <th>Status</th>
                    <th>Created At</th>
                </tr>
            </thead>
            <tbody>
                {todo_rows}
            </tbody>
        </table>

        <div class="footer">
            Alexandria National University &bull; Faculty of Engineering &bull; Database Systems Lab 2
        </div>
    </div>
</body>
</html>
"""

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html_content)

print("Opening complete relational database viewer in browser...")
webbrowser.open('file://' + os.path.abspath(html_path))
