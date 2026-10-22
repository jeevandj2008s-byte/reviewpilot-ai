/**
 * ReviewPilot Core Application Controller
 */

// Global App State
const AppState = {
  currentView: 'landing', // 'landing' | 'dashboard' | 'analyzer' | 'settings'
  user: null, // Logged in user profile & subscription tier
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

  toast.innerHTML = iconSvg;
  const msgSpan = document.createElement('span');
  msgSpan.textContent = message;
  toast.appendChild(msgSpan);
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
  } else if (viewName === 'analyzer') {
    if (window.SettingsController && typeof SettingsController.loadPlatformConnections === 'function') {
      SettingsController.loadPlatformConnections();
    }
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

// Payment & Subscription Checkout Modal Controller
const PaymentModalController = {
  activePlan: 'growth',
  activeAmount: 299,
  activePlanName: 'Growth Plan',
  upiId: '9741481204@axl',
  recipientName: 'ReviewPilot AI',

  open(plan, planName, amount) {
    this.activePlan = plan;
    this.activePlanName = planName;
    this.activeAmount = amount;

    const modal = document.getElementById('payment-modal');
    const planNameEl = document.getElementById('checkout-plan-name');
    const amountEl = document.getElementById('checkout-amount-display');
    const directUpiLink = document.getElementById('direct-upi-link');

    if (planNameEl) planNameEl.textContent = planName;
    if (amountEl) amountEl.textContent = `₹${amount}`;

    // Generate Standard NPCI UPI Deep Link (Compatible with GPay, PhonePe, Paytm, BHIM)
    const encodedName = encodeURIComponent(this.recipientName);
    const encodedNote = encodeURIComponent(`ReviewPilot ${planName}`);
    const upiUri = `upi://pay?pa=${this.upiId}&pn=${encodedName}&am=${amount}&cu=INR&tn=${encodedNote}`;

    if (directUpiLink) {
      directUpiLink.href = upiUri;
    }

    if (modal) {
      modal.classList.add('active');
      modal.setAttribute('aria-hidden', 'false');
      document.body.style.overflow = 'hidden';
    }
  },

  close() {
    const modal = document.getElementById('payment-modal');
    if (modal) {
      modal.classList.remove('active');
      modal.setAttribute('aria-hidden', 'true');
      document.body.style.overflow = '';
    }
  },

  copyUpi() {
    navigator.clipboard.writeText(this.upiId).then(() => {
      const copyBtn = document.getElementById('copy-upi-btn');
      if (copyBtn) {
        copyBtn.innerHTML = `
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
          <span>Copied!</span>
        `;
        setTimeout(() => {
          copyBtn.innerHTML = `
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
            <span>Copy</span>
          `;
        }, 2200);
      }
      showToast('UPI ID copied to clipboard!', 'success');
    }).catch(() => {
      showToast(`UPI ID: ${this.upiId}`, 'info');
    });
  },

  async confirmPayment() {
    const utr = prompt('Please enter your 12-digit UPI Transaction ID / UTR or registered phone number for instant verification:');
    if (utr && utr.trim().length >= 4) {
      if (AppState.user) {
        AppState.user.subscription_plan = this.activePlanName;
        AppState.user.subscription_status = 'active';
        AuthModalController.updateUIForUser(AppState.user);
      }
      showToast(`✓ Verification received for ${this.activePlanName}! Your subscription is now linked to your account.`, 'success');
      this.close();
      setTimeout(() => {
        navigateTo('dashboard');
      }, 1000);
    } else if (utr !== null) {
      showToast('Please enter a valid transaction reference to confirm activation.', 'warning');
    }
  }
};

// Wire Payment Modal Event Listeners
document.addEventListener('DOMContentLoaded', () => {
  // Subscribe buttons in pricing grid
  document.querySelectorAll('.btn-subscribe').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const plan = btn.getAttribute('data-plan') || 'growth';
      const planName = btn.getAttribute('data-plan-name') || 'Growth Plan';
      const amount = btn.getAttribute('data-amount') || '299';
      PaymentModalController.open(plan, planName, amount);
    });
  });

  // Modal close button
  const closeBtn = document.getElementById('payment-modal-close-btn');
  if (closeBtn) {
    closeBtn.addEventListener('click', () => PaymentModalController.close());
  }

  // Backdrop click to close
  const modal = document.getElementById('payment-modal');
  if (modal) {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        PaymentModalController.close();
      }
    });
  }

  // Copy UPI button
  const copyBtn = document.getElementById('copy-upi-btn');
  if (copyBtn) {
    copyBtn.addEventListener('click', () => PaymentModalController.copyUpi());
  }

  // Confirm payment button
  const confirmBtn = document.getElementById('payment-confirm-btn');
  if (confirmBtn) {
    confirmBtn.addEventListener('click', () => PaymentModalController.confirmPayment());
  }

  // Escape key to close modal
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      PaymentModalController.close();
      AuthModalController.close();
    }
  });

  // Init auth state check
  AuthModalController.init();
});

// Authentication Modal Controller (Email, Google, Phone OTP)
const AuthModalController = {
  isRegisterMode: false,
  activeTab: 'email',

  init() {
    this.checkSession();
    this.bindEvents();
  },

  async checkSession() {
    const token = localStorage.getItem('reviewpilot_token');
    if (!token) {
      this.updateUIForUser(null);
      return;
    }
    try {
      const user = await API.getMyProfile();
      this.updateUIForUser(user);
    } catch (err) {
      console.warn('Session expired or invalid, clearing local session.');
      localStorage.removeItem('reviewpilot_token');
      this.updateUIForUser(null);
    }
  },

  updateUIForUser(user) {
    AppState.user = user;
    const navSignInBtn = document.getElementById('nav-signin-btn');
    const navUserPill = document.getElementById('nav-user-pill');
    const navUserPlan = document.getElementById('nav-user-plan');
    const navUserName = document.getElementById('nav-user-name');

    const appSignInBtn = document.getElementById('app-signin-btn');
    const appUserBadge = document.getElementById('app-user-badge');
    const appUserPlan = document.getElementById('app-user-plan');
    const appUserName = document.getElementById('app-user-name');

    if (user) {
      const planName = (user.subscription_plan || 'Free').toUpperCase();
      const displayName = user.full_name || (user.email ? user.email.split('@')[0] : user.phone);

      if (navSignInBtn) navSignInBtn.style.display = 'none';
      if (navUserPill) {
        navUserPill.style.display = 'inline-flex';
        if (navUserPlan) navUserPlan.textContent = planName;
        if (navUserName) navUserName.textContent = displayName;
      }

      if (appSignInBtn) appSignInBtn.style.display = 'none';
      if (appUserBadge) {
        appUserBadge.style.display = 'inline-flex';
        if (appUserPlan) appUserPlan.textContent = planName;
        if (appUserName) appUserName.textContent = displayName;
      }
    } else {
      if (navSignInBtn) navSignInBtn.style.display = 'inline-block';
      if (navUserPill) navUserPill.style.display = 'none';
      if (appSignInBtn) appSignInBtn.style.display = 'inline-flex';
      if (appUserBadge) appUserBadge.style.display = 'none';
    }
  },

  open(mode = 'login') {
    this.isRegisterMode = (mode === 'register');
    this.updateModeUI();
    const modal = document.getElementById('auth-modal');
    if (modal) {
      modal.classList.add('active');
      modal.setAttribute('aria-hidden', 'false');
      document.body.style.overflow = 'hidden';
    }
  },

  close() {
    const modal = document.getElementById('auth-modal');
    if (modal) {
      modal.classList.remove('active');
      modal.setAttribute('aria-hidden', 'true');
      document.body.style.overflow = '';
    }
  },

  switchTab(tabName) {
    this.activeTab = tabName;
    document.querySelectorAll('.auth-tab-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.tab === tabName);
    });
    document.querySelectorAll('.auth-tab-content').forEach(content => {
      content.style.display = (content.id === `auth-tab-${tabName}`) ? 'block' : 'none';
    });
  },

  toggleRegisterMode() {
    this.isRegisterMode = !this.isRegisterMode;
    this.updateModeUI();
  },

  updateModeUI() {
    const title = document.getElementById('auth-modal-title');
    const submitBtn = document.getElementById('auth-submit-btn');
    const toggleBtn = document.getElementById('auth-toggle-mode-btn');
    const togglePrompt = document.getElementById('auth-toggle-prompt');
    const nameGroup = document.getElementById('auth-name-group');

    if (this.isRegisterMode) {
      if (title) title.textContent = 'Create ReviewPilot Account';
      if (submitBtn) submitBtn.textContent = 'Create Account';
      if (toggleBtn) toggleBtn.textContent = 'Sign in instead';
      if (togglePrompt) togglePrompt.textContent = 'Already have an account?';
      if (nameGroup) nameGroup.style.display = 'block';
    } else {
      if (title) title.textContent = 'Sign In to ReviewPilot';
      if (submitBtn) submitBtn.textContent = 'Sign In with Email';
      if (toggleBtn) toggleBtn.textContent = 'Create one now';
      if (togglePrompt) togglePrompt.textContent = "Don't have an account?";
      if (nameGroup) nameGroup.style.display = 'none';
    }
  },

  signOut() {
    localStorage.removeItem('reviewpilot_token');
    this.updateUIForUser(null);
    showToast('You have signed out successfully.', 'info');
  },

  bindEvents() {
    // Open Sign-in buttons
    const navSignInBtn = document.getElementById('nav-signin-btn');
    if (navSignInBtn) navSignInBtn.addEventListener('click', () => this.open('login'));

    const appSignInBtn = document.getElementById('app-signin-btn');
    if (appSignInBtn) appSignInBtn.addEventListener('click', () => this.open('login'));

    // Sign out buttons (Landing navbar & App header)
    const signOutBtn = document.getElementById('app-signout-btn');
    if (signOutBtn) signOutBtn.addEventListener('click', () => this.signOut());

    const navSignOutBtn = document.getElementById('nav-signout-btn');
    if (navSignOutBtn) navSignOutBtn.addEventListener('click', () => this.signOut());

    // Close button & backdrop
    const closeBtn = document.getElementById('auth-modal-close-btn');
    if (closeBtn) closeBtn.addEventListener('click', () => this.close());

    const authModal = document.getElementById('auth-modal');
    if (authModal) {
      authModal.addEventListener('click', (e) => {
        if (e.target === authModal) this.close();
      });
    }

    // Tab buttons
    document.querySelectorAll('.auth-tab-btn').forEach(btn => {
      btn.addEventListener('click', () => this.switchTab(btn.dataset.tab));
    });

    // Toggle Register / Login mode
    const toggleModeBtn = document.getElementById('auth-toggle-mode-btn');
    if (toggleModeBtn) {
      toggleModeBtn.addEventListener('click', () => this.toggleRegisterMode());
    }

    // Email Form Submission
    const emailForm = document.getElementById('auth-email-form');
    if (emailForm) {
      emailForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('auth-email-input').value.trim();
        const password = document.getElementById('auth-password-input').value;
        const nameInput = document.getElementById('auth-full-name');
        const fullName = nameInput ? nameInput.value.trim() : '';

        if (password.length < 6) {
          showToast('Password must be at least 6 characters long.', 'error');
          return;
        }

        try {
          let res;
          if (this.isRegisterMode) {
            res = await API.register({ email, password, full_name: fullName || email.split('@')[0] });
            showToast(`Account created! Welcome, ${res.user.full_name}`, 'success');
          } else {
            res = await API.login({ identifier: email, password });
            showToast(`Welcome back, ${res.user.full_name}! Active Plan: ${res.user.subscription_plan}`, 'success');
          }

          localStorage.setItem('reviewpilot_token', res.access_token);
          this.updateUIForUser(res.user);
          this.close();
        } catch (err) {
          showToast(err.message, 'error');
        }
      });
    }

    // Google Sign-In Form Action
    const googleForm = document.getElementById('auth-google-form');
    if (googleForm) {
      googleForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const googleEmail = document.getElementById('auth-google-email-input').value.trim();
        const googleNameInput = document.getElementById('auth-google-name-input');
        const googleName = googleNameInput ? googleNameInput.value.trim() : '';

        if (!googleEmail || !googleEmail.includes('@')) {
          showToast('Please enter a valid Google email address.', 'warning');
          return;
        }
        try {
          const res = await API.loginGoogle({
            email: googleEmail,
            full_name: googleName || googleEmail.split('@')[0].replace('.', ' ').toUpperCase()
          });
          localStorage.setItem('reviewpilot_token', res.access_token);
          this.updateUIForUser(res.user);
          showToast(`Signed in as ${res.user.full_name}! Active Plan: ${res.user.subscription_plan}`, 'success');
          this.close();
        } catch (err) {
          showToast(err.message, 'error');
        }
      });
    }

    // Phone OTP Form
    const phoneForm = document.getElementById('auth-phone-form');
    const sendOtpBtn = document.getElementById('auth-send-otp-btn');

    if (sendOtpBtn) {
      sendOtpBtn.addEventListener('click', () => {
        const phone = document.getElementById('auth-phone-input').value.trim();
        if (phone.length < 10) {
          showToast('Please enter a valid 10-digit phone number first.', 'warning');
          return;
        }
        document.getElementById('auth-otp-input').value = '123456';
        showToast(`Verification code sent to ${phone}. (Demo OTP: 123456)`, 'info');
      });
    }

    if (phoneForm) {
      phoneForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const phone = document.getElementById('auth-phone-input').value.trim();
        const otp = document.getElementById('auth-otp-input').value.trim();
        const phoneNameInput = document.getElementById('auth-phone-name-input');
        const phoneName = phoneNameInput ? phoneNameInput.value.trim() : '';

        try {
          const res = await API.loginPhone({ phone, otp, full_name: phoneName || `User ${phone.slice(-4)}` });
          localStorage.setItem('reviewpilot_token', res.access_token);
          this.updateUIForUser(res.user);
          showToast(`Verified! Signed in as ${res.user.full_name}. Plan: ${res.user.subscription_plan}`, 'success');
          this.close();
        } catch (err) {
          showToast(err.message, 'error');
        }
      });
    }
  }
};


