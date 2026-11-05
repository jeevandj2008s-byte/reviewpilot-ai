import re

with open('frontend/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines, 1):
    if 'style="' in line:
        matches = re.findall(r'(#[0-9a-fA-F]{3,8}|rgba?\([^)]+\))', line)
        if matches:
            # Filter out SVG fills that are official brand colors like google
            cleaned = [m for m in matches if m not in ['#4285F4', '#34A853', '#FBBC05', '#EA4335', '#ffffff', '#10b981', '#ef4444']]
            if cleaned:
                print(f"Line {i}: {cleaned} --> {line.strip()[:100]}")
