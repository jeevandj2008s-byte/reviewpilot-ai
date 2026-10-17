/**
 * ReviewPilot Core Application Controller
 */

// Global App State
const AppState = {
  currentView: 'landing', // 'landing' | 'dashboard' | 'analyzer' | 'settings'
  settings: {
    business_name: 'Urban Bistro & Cafe',
    business_type: 'Restaurant / Cafe',
    has_anthropic_key: false,
    telegram_alerts_enabled: false,
    telegram_bot_configured: false
  }
};

// Preset Review Batches for Instant 1-Click Testing
const SAMPLE_PRESETS = {
  cafe: [
    "The oat milk cappuccino was exquisite and the barista remembered my order from yesterday! 10/10",
    "Coffee is decent and plenty of seating to work, but Wi-Fi drops every 15 minutes.",
    "Waited 35 minutes for two plain croissants and the cashier was visibly annoyed when I asked for a status update.",
    "BEWARE: I ordered the egg & ham brioche on Tuesday and came down with severe food poisoning and vomiting that night. Health department needs to inspect this kitchen!"
  ],
  restaurant: [
    "Best wood-fired pizza in town, the burrata was melt-in-your-mouth delicious and service was remarkably fast!",
    "Nice ambience and jazz playlist, though portions were quite small for the steep prices.",
    "The manager was shouting at the young busser right in front of customers, which created a very uncomfortable atmosphere.",
    "Found a dead cockroach inside our pasta salad! The manager refused a refund and threatened to call the police on us when we asked for our money back."
  ],
  salon: [
    "Maria gave me the best balayage and haircut of my life! My hair feels healthier than ever.",
    "The blowout looked pretty good, but the waiting area smelled strongly of harsh chemical acetone.",
    "Booked an appointment 2 weeks in advance but had to wait 45 minutes past my slot before anyone acknowledged me.",
    "The hair colorist left the bleach on for over an hour despite me crying that it was burning. I have severe chemical burns and blisters on my scalp!"
  ],
  gym: [
    "Spacious gym floor, brand new Olympic lifting platforms, and super encouraging trainers!",
    "Good saunas and free parking, but the free weights area gets too crowded between 5pm and 7pm.",
    "Cardio machines have been out of order for three weeks straight and the locker room paper towel dispensers are always empty.",
    "One of the male trainers repeatedly made predatory and harassing comments toward my teenage daughter in the weight room. Unsafe facility!"
  ]
};

// Toast Notifications Helper
function showToast(message, type = 'success', duration = 4000) {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;

  let iconSvg = '';
  if (type === 'success') {
    iconSvg = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2"><path d="M20 6L9 17l-5-5"/></svg>`;
  } else if (type === 'error') {
    iconSvg = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`;
  } else {
    iconSvg = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`;
  }

  toast.innerHTML = `${iconSvg}<span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(8px)';
    toast.style.transition = 'all 0.25s ease';
    setTimeout(() => toast.remove(), 250);
  }, duration);
}

// Router & View Switcher
function navigateTo(viewName) {
  AppState.currentView = viewName;

  const landingView = document.getElementById('landing-view');
  const appView = document.getElementById('app-view');

  if (viewName === 'landing') {
    if (landingView) landingView.style.display = 'block';
    if (appView) appView.style.display = 'none';
    window.location.hash = 'landing';
    window.scrollTo({ top: 0, behavior: 'smooth' });
    return;
  }

  // Inside App Layout
  if (landingView) landingView.style.display = 'none';
  if (appView) appView.style.display = 'block';

  // Toggle app view panels
  const panels = document.querySelectorAll('.view-panel');
  panels.forEach(p => p.classList.remove('active'));

  const targetPanel = document.getElementById(`${viewName}-panel`);
  if (targetPanel) {
    targetPanel.classList.add('active');
  }

  // Update sidebar active buttons
  const navBtns = document.querySelectorAll('.sidebar-nav .nav-item');
  navBtns.forEach(btn => {
    btn.classList.toggle('active', btn.dataset.view === viewName);
  });

  // Update Header title
  const headerTitle = document.getElementById('header-view-title');
  if (headerTitle) {
    if (viewName === 'dashboard') headerTitle.textContent = 'Dashboard & Insights';
    else if (viewName === 'analyzer') headerTitle.textContent = 'Review Analyzer';
    else if (viewName === 'settings') headerTitle.textContent = 'Settings & Integrations';
  }

  window.location.hash = viewName;
  window.scrollTo({ top: 0, behavior: 'smooth' });

  // Trigger view-specific loads
  if (viewName === 'dashboard') {
    DashboardController.loadStats();
  } else if (viewName === 'settings') {
    SettingsController.loadSettings();
  }

  // Close mobile sidebar if open
  closeMobileSidebar();
}

// Sidebar Drawer Control
function toggleSidebar() {
  const sidebar = document.getElementById('app-sidebar');
  if (sidebar) {
    sidebar.classList.toggle('open');
  }
}

function closeMobileSidebar() {
  const sidebar = document.getElementById('app-sidebar');
  if (sidebar && window.innerWidth <= 900) {
    sidebar.classList.remove('open');
  }
}

// Initial Sync & Event Listeners
document.addEventListener('DOMContentLoaded', async () => {
  // Check URL Hash for deep linking
  const hash = window.location.hash.replace('#', '') || 'landing';

  // Fetch initial backend settings
  try {
    const settingsData = await API.getSettings();
    AppState.settings = settingsData;
    updateGlobalBusinessPill(settingsData.business_name, settingsData.business_type);
  } catch (err) {
    console.warn('Could not connect to settings API during boot:', err);
  }

  // Bind Navigation links
  document.querySelectorAll('[data-navigate]').forEach(elem => {
    elem.addEventListener('click', (e) => {
      e.preventDefault();
      const target = elem.getAttribute('data-navigate');
      navigateTo(target);
    });
  });

  // Mobile menu buttons
  const mobileToggle = document.getElementById('mobile-menu-toggle');
  if (mobileToggle) {
    mobileToggle.addEventListener('click', toggleSidebar);
  }

  const sidebarClose = document.getElementById('sidebar-close-btn');
  if (sidebarClose) {
    sidebarClose.addEventListener('click', closeMobileSidebar);
  }

  // Accordion for FAQs
  document.querySelectorAll('.faq-question').forEach(btn => {
    btn.addEventListener('click', () => {
      const item = btn.closest('.faq-item');
      item.classList.toggle('active');
    });
  });

  // Initialize view based on initial hash
  if (hash === 'dashboard' || hash === 'analyzer' || hash === 'settings') {
    navigateTo(hash);
  } else {
    navigateTo('landing');
  }
});

function updateGlobalBusinessPill(name, type) {
  const pillName = document.getElementById('sidebar-business-name');
  if (pillName && name) {
    pillName.textContent = name;
  }
}
