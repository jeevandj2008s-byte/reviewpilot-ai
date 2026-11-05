with open('frontend/js/settings.js', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("resultMsg.style.color = '#38bdf8';", "resultMsg.style.color = 'var(--text-main)';")
content = content.replace("aiMicBtn.style.borderColor = 'rgba(56, 189, 248, 0.4)';", "aiMicBtn.style.borderColor = 'var(--border)';")
content = content.replace(
    "div.style.cssText = 'background: linear-gradient(135deg, #38bdf8, #6366f1); color: #fff; padding: 0.65rem 0.95rem; border-radius: 10px; font-size: 0.85rem; align-self: flex-end; max-width: 85%;';",
    "div.style.cssText = 'background: var(--primary); color: #ffffff; padding: 0.65rem 1rem; border-radius: 12px; font-size: 0.85rem; align-self: flex-end; max-width: 85%; box-shadow: var(--shadow-sm);';"
)
content = content.replace(
    "div.style.cssText = 'background: rgba(56, 189, 248, 0.1); border: 1px solid rgba(56, 189, 248, 0.2); padding: 0.75rem 1rem; border-radius: 10px; font-size: 0.85rem; color: #f8fafc; align-self: flex-start; max-width: 90%; line-height: 1.5;';",
    "div.style.cssText = 'background: var(--bg-canvas-subtle); border: 1px solid var(--border); padding: 0.75rem 1rem; border-radius: 12px; font-size: 0.85rem; color: var(--text-main); align-self: flex-start; max-width: 90%; line-height: 1.5;';"
)
content = content.replace(
    "typing.style.cssText = 'background: rgba(56, 189, 248, 0.08); padding: 0.5rem 0.85rem; border-radius: 8px; font-size: 0.8rem; color: var(--text-muted); align-self: flex-start; font-style: italic;';",
    "typing.style.cssText = 'background: var(--bg-canvas-subtle); border: 1px solid var(--border); padding: 0.5rem 0.85rem; border-radius: 8px; font-size: 0.8rem; color: var(--text-muted); align-self: flex-start; font-style: italic;';"
)

with open('frontend/js/settings.js', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated settings.js colors cleanly")
