with open('frontend/js/dashboard.js', 'r', encoding='utf-8') as f:
    content = f.read()

target = "font: { family: 'Inter', size: 12 }"
replacement = "color: '#111827', font: { family: 'Inter', size: 12 }"

if target in content:
    content = content.replace(target, replacement, 1)
    with open('frontend/js/dashboard.js', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Successfully updated dashboard.js chart legend color")
else:
    print("Target not found")
