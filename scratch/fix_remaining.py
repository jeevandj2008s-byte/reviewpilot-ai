with open('frontend/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

target = '<div style="margin-top: 0.75rem; padding: 1rem; background: rgba(30, 41, 59, 0.45); border-radius: var(--radius); border: 1px solid var(--border);">'
replacement = '<div style="margin-top: 0.75rem; padding: 1rem; background: var(--bg-canvas-subtle); border-radius: var(--radius-md); border: 1px solid var(--border);">'

if target in content:
    content = content.replace(target, replacement)
    with open('frontend/index.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Replaced remaining anthropic background")
else:
    print("Target not found")
