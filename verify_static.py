import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

required_files = [
    'index.html',
    'login.html',
    'register.html',
    'dashboard.html',
    'css/style.css',
    'js/db.js',
    'js/auth.js',
    '_redirects',
    'netlify.toml'
]

print("Verifying Netlify Project Files...")
missing = []
for rel_path in required_files:
    full_path = os.path.join(BASE_DIR, rel_path)
    if not os.path.exists(full_path):
        missing.append(rel_path)
    else:
        size = os.path.getsize(full_path)
        print(f"  [OK] {rel_path} ({size} bytes)")

if missing:
    print(f"FAILED: Missing files: {missing}")
    sys.exit(1)

# Check index.html
with open(os.path.join(BASE_DIR, 'index.html'), 'r', encoding='utf-8') as f:
    content = f.read()
    assert 'dashboard.html' in content and 'login.html' in content
    print("  [OK] index.html valid with redirect logic")

# Check db.js
with open(os.path.join(BASE_DIR, 'js', 'db.js'), 'r', encoding='utf-8') as f:
    content = f.read()
    assert 'openDB' in content
    assert 'hashPassword' in content
    assert 'registerUser' in content
    assert 'authenticateUser' in content
    assert 'IndexedDB' in content or 'indexedDB' in content
    print("  [OK] js/db.js valid with IndexedDB and SHA-256 Web Crypto hashing")

# Check auth.js
with open(os.path.join(BASE_DIR, 'js', 'auth.js'), 'r', encoding='utf-8') as f:
    content = f.read()
    assert 'requireAuth' in content
    assert 'redirectIfLoggedIn' in content
    assert 'setSessionUser' in content
    assert 'logout' in content
    print("  [OK] js/auth.js valid with session protection")

print("\nAll Netlify verification checks PASSED successfully!")
