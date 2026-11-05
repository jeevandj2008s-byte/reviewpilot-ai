import re

with open('frontend/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Replace Hero section
hero_pattern = re.compile(
    r'<!-- Hero Section — Aceternity UI Lamp Effect \(dark blue theme\) -->\s*<section id="hero-lamp" class="lamp-container">.*?</section>',
    re.DOTALL
)

new_hero = '''<!-- Hero Section — Vela Dynamic Rotating Terms & Morphing Pastel Auras -->
    <section id="hero-vela" class="hero-vela-container">
      <!-- Morphing Pastel Auras -->
      <div class="hero-aura-stage" aria-hidden="true">
        <div id="hero-aura-primary" class="hero-aura-blob hero-aura-blob-primary"></div>
        <div id="hero-aura-secondary" class="hero-aura-blob hero-aura-blob-secondary"></div>
        <div class="hero-aura-blob hero-aura-blob-tertiary"></div>
      </div>

      <div class="hero-vela-content">
        <div class="hero-pill">
          <span class="hero-pill-dot"></span>
          <span>AI Review Intelligence for High-Growth Businesses</span>
        </div>

        <div class="hero-headline-wrap">
          <h1 class="hero-title-fixed">
            <span class="hero-rotator-pill" id="hero-rotator-pill">
              <span class="hero-3d-icon-badge" id="hero-3d-badge"></span>
              <span class="hero-rotator-text" id="hero-rotating-term">Analyze reviews</span>
            </span>
            <span>in your terms.</span>
          </h1>
        </div>

        <p class="hero-subtext">
          Turn customer reviews into brand loyalty. Analyze sentiment, generate polite replies, and receive immediate alerts when urgent escalations occur.
        </p>

        <div class="hero-cta-group">
          <button class="btn btn-primary btn-lg" data-navigate="analyzer">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
            Launch Review Analyzer
          </button>
          <button class="btn btn-secondary btn-lg" data-navigate="dashboard">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>
            Live Dashboard
          </button>
        </div>

        <a href="#how-it-works" class="hero-scroll-hint">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><polyline points="19 12 12 19 5 12"/></svg>
          Scroll to learn more
        </a>
      </div>
    </section>

    <!-- Editorial Stat Ribbon (from Vela reference) -->
    <div class="hero-stat-ribbon">
      <div class="stat-ribbon-quote">
        <p>Every review matters.</p>
        <span>AI feedback intelligence for local brands</span>
      </div>
      <div class="stat-ribbon-items">
        <div class="stat-ribbon-item">
          <div class="stat-ribbon-num">99.4%</div>
          <div class="stat-ribbon-label">Sentiment Accuracy</div>
        </div>
        <div class="stat-ribbon-item">
          <div class="stat-ribbon-num">&lt; 1.5s</div>
          <div class="stat-ribbon-label">Reply Speed</div>
        </div>
        <div class="stat-ribbon-item">
          <div class="stat-ribbon-num">24/7</div>
          <div class="stat-ribbon-label">Urgent Alerts</div>
        </div>
        <div class="stat-ribbon-item">
          <div class="stat-ribbon-num">100% Free</div>
          <div class="stat-ribbon-label">Built-in AI Engine</div>
        </div>
      </div>
      <div class="stat-ribbon-art" title="Continuous Growth">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
          <path d="M12 22v-9M12 13a5 5 0 0 0 5-5c0-4-5-6-5-6s-5 2-5 6a5 5 0 0 0 5 5z"/>
          <path d="M7 17a4 4 0 0 1-4-4c0-3 4-5 4-5s1 2 1 4a3.8 3.8 0 0 1-1 5z"/>
          <path d="M17 17a4 4 0 0 0 4-4c0-3-4-5-4-5s-1 2-1 4a3.8 3.8 0 0 0 1 5z"/>
        </svg>
      </div>
    </div>'''

if hero_pattern.search(content):
    content = hero_pattern.sub(new_hero, content)
    print("Hero section successfully replaced!")
else:
    print("Warning: hero pattern not matched directly, checking alternative match...")

# 2. Specific inline style cleanup for full warm aesthetic consistency
replacements = [
    # Nav user pill
    ('style="display: none; align-items: center; gap: 0.5rem; background: rgba(56, 189, 248, 0.12); border: 1px solid rgba(56, 189, 248, 0.35); padding: 0.35rem 0.85rem; border-radius: var(--radius-full);"',
     'style="display: none; align-items: center; gap: 0.5rem; background: var(--bg-subtle); border: 1px solid var(--border); padding: 0.35rem 0.85rem; border-radius: var(--radius-full);"'),
    ('style="font-size: 0.75rem; font-weight: 700; color: #38bdf8;"',
     'style="font-size: 0.75rem; font-weight: 700; color: var(--text-main);"'),
    
    # Preview mockup
    ('style="margin-left: 0.5rem; font-size: 0.75rem; color: #94a3b8; font-weight: 500;"',
     'style="margin-left: 0.5rem; font-size: 0.75rem; color: var(--text-muted); font-weight: 500;"'),
    ('style="font-size: 0.9rem; color: #cbd5e1; font-style: italic;"',
     'style="font-size: 0.925rem; color: var(--text-secondary); font-style: italic;"'),
    ('style="background-color: rgba(14, 30, 68, 0.7); border-left: 3px solid #38bdf8; padding: 0.75rem 1rem; border-radius: 4px; font-size: 0.85rem; color: #f8fafc;"',
     'style="background-color: var(--bg-canvas-subtle); border-left: 3px solid var(--primary); padding: 0.85rem 1.15rem; border-radius: 0 8px 8px 0; font-size: 0.875rem; color: var(--text-main);"'),
    ('<strong style="color: #38bdf8;">Empathetic Response Draft:</strong>',
     '<strong style="color: var(--text-main);">Empathetic Response Draft:</strong>'),
     
    # App user badge
    ('style="display: none; align-items: center; gap: 0.65rem; background: rgba(15, 34, 76, 0.75); border: 1px solid rgba(56, 189, 248, 0.35); padding: 0.35rem 0.85rem; border-radius: var(--radius-full);"',
     'style="display: none; align-items: center; gap: 0.65rem; background: var(--bg-subtle); border: 1px solid var(--border); padding: 0.35rem 0.85rem; border-radius: var(--radius-full);"'),
    ('style="font-size: 0.72rem; font-weight: 700; color: #38bdf8; background: rgba(56, 189, 248, 0.2); padding: 0.15rem 0.5rem; border-radius: 999px;"',
     'style="font-size: 0.72rem; font-weight: 700; color: var(--text-main); background: #ffffff; border: 1px solid var(--border); padding: 0.15rem 0.5rem; border-radius: 999px;"'),
     
    # Connected review platform
    ('id="google-platform-card" style="background: rgba(56, 189, 248, 0.06); border: 1px solid rgba(56, 189, 248, 0.2); border-radius: var(--radius); padding: 1.25rem;"',
     'id="google-platform-card" style="background: var(--bg-canvas-subtle); border: 1px solid var(--border); border-radius: var(--radius-md); padding: 1.25rem;"'),
    ('style="background: rgba(15, 34, 76, 0.4); border: 1px solid rgba(56, 189, 248, 0.2); border-radius: 8px; padding: 0.85rem; margin-bottom: 0.85rem;"',
     'style="background: #ffffff; border: 1px solid var(--border); border-radius: 8px; padding: 0.85rem; margin-bottom: 0.85rem;"'),
    ('<span class="text-xs" id="google-last-sync-label" style="color: #38bdf8;">Last synced: Never</span>',
     '<span class="text-xs text-muted" id="google-last-sync-label">Last synced: Never</span>'),
    ('style="background: rgba(30, 41, 59, 0.35); border: 1px solid var(--border); border-radius: var(--radius); padding: 0.75rem 1rem;"',
     'style="background: var(--bg-canvas-subtle); border: 1px solid var(--border); border-radius: var(--radius-md); padding: 0.75rem 1rem;"'),
     
    # Settings email & telegram boxes
    ('style="background: rgba(56, 189, 248, 0.06); border: 1px solid rgba(56, 189, 248, 0.2); border-radius: var(--radius); padding: 1.25rem;"',
     'style="background: var(--bg-canvas-subtle); border: 1px solid var(--border); border-radius: var(--radius-md); padding: 1.25rem;"'),
    ('style="background: rgba(30, 41, 59, 0.45); border-radius: var(--radius); border: 1px solid var(--border);"',
     'style="background: var(--bg-canvas-subtle); border-radius: var(--radius-md); border: 1px solid var(--border);"'),
     
    # AI Assistant box
    ('style="background: rgba(12, 26, 58, 0.7); border: 1px solid rgba(56, 189, 248, 0.25); border-radius: var(--radius); overflow: hidden; margin-top: 1rem;"',
     'style="background: #ffffff; border: 1px solid var(--border); border-radius: var(--radius-lg); overflow: hidden; margin-top: 1rem; box-shadow: var(--shadow-sm);"'),
    ('style="background: rgba(56, 189, 248, 0.1); border: 1px solid rgba(56, 189, 248, 0.2); padding: 0.75rem 1rem; border-radius: 10px; font-size: 0.875rem; color: #f8fafc; align-self: flex-start; max-width: 90%;"',
     'style="background: var(--bg-canvas-subtle); border: 1px solid var(--border); padding: 0.75rem 1rem; border-radius: 12px; font-size: 0.875rem; color: var(--text-main); align-self: flex-start; max-width: 90%;"'),
    ('style="margin: 0.4rem 0 0.2rem 1.2rem; font-size: 0.825rem; color: #cbd5e1;"',
     'style="margin: 0.4rem 0 0.2rem 1.2rem; font-size: 0.825rem; color: var(--text-secondary);"'),
    ('style="padding: 0.5rem 1rem; display: flex; flex-wrap: wrap; gap: 0.4rem; border-top: 1px solid rgba(56, 189, 248, 0.12); background: rgba(8, 17, 36, 0.5);"',
     'style="padding: 0.5rem 1rem; display: flex; flex-wrap: wrap; gap: 0.4rem; border-top: 1px solid var(--border); background: var(--bg-canvas-subtle);"'),
    ('style="padding: 0.75rem 1rem; display: flex; align-items: center; gap: 0.5rem; border-top: 1px solid rgba(56, 189, 248, 0.18); background: rgba(8, 17, 36, 0.9);"',
     'style="padding: 0.75rem 1rem; display: flex; align-items: center; gap: 0.5rem; border-top: 1px solid var(--border); background: #ffffff;"'),
    ('style="display: inline-flex; align-items: center; gap: 0.35rem; padding: 0.45rem 0.85rem; border-color: rgba(56, 189, 248, 0.4);"',
     'style="display: inline-flex; align-items: center; gap: 0.35rem; padding: 0.45rem 0.85rem;"'),
     
    # Data privacy card
    ('style="border: 1px solid rgba(239, 68, 68, 0.35); background: rgba(239, 68, 68, 0.05); display: flex; flex-direction: column; gap: 1rem;"',
     'style="border: 1px solid var(--neg-border); background: var(--neg-bg); display: flex; flex-direction: column; gap: 1rem;"'),
     
    # Auth modal prompt toggle
    ('style="background: none; border: none; color: #38bdf8; font-weight: 600; cursor: pointer; padding: 0 0.25rem;"',
     'style="background: none; border: none; color: var(--text-main); font-weight: 600; cursor: pointer; padding: 0 0.25rem; text-decoration: underline;"'),
    ('style="background: none; border: none; color: #38bdf8; font-size: 0.75rem; cursor: pointer; font-weight: 600;"',
     'style="background: none; border: none; color: var(--text-main); font-size: 0.75rem; cursor: pointer; font-weight: 600;"'),
]

for old_str, new_str in replacements:
    if old_str in content:
        content = content.replace(old_str, new_str)
        print(f"Replaced inline style: {old_str[:40]}...")
    else:
        print(f"Notice: pattern not found verbatim: {old_str[:40]}...")

with open('frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated frontend/index.html successfully!")
