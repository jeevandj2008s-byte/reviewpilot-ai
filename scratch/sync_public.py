import shutil
import os

files_to_copy = [
    ('frontend/index.html', 'public/index.html'),
    ('frontend/css/main.css', 'public/css/main.css'),
    ('frontend/css/main.css', 'public/static/css/main.css'),
    ('frontend/css/landing.css', 'public/css/landing.css'),
    ('frontend/css/landing.css', 'public/static/css/landing.css'),
    ('frontend/css/analyzer.css', 'public/css/analyzer.css'),
    ('frontend/css/analyzer.css', 'public/static/css/analyzer.css'),
    ('frontend/css/dashboard.css', 'public/css/dashboard.css'),
    ('frontend/css/dashboard.css', 'public/static/css/dashboard.css'),
    ('frontend/js/lamp.js', 'public/js/lamp.js'),
    ('frontend/js/lamp.js', 'public/static/js/lamp.js'),
    ('frontend/js/dashboard.js', 'public/js/dashboard.js'),
    ('frontend/js/dashboard.js', 'public/static/js/dashboard.js'),
    ('frontend/js/settings.js', 'public/js/settings.js'),
    ('frontend/js/settings.js', 'public/static/js/settings.js'),
]

for src, dst in files_to_copy:
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
    print(f"Copied {src} -> {dst}")

print("Sync to public complete!")
