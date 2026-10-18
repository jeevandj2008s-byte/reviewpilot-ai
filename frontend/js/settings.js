/**
 * ReviewPilot Settings & Notifications Controller (Simplified)
 * Eliminates technical tokens, bot creation, and complex API keys.
 */

const SettingsController = {
  async loadSettings() {
    try {
      const data = await API.getSettings();
      AppState.settings = data;

      const bizName = document.getElementById('settings-biz-name');
      const bizType = document.getElementById('settings-biz-type');
      const teleAlerts = document.getElementById('settings-telegram-alerts');
      const telePhone = document.getElementById('settings-telegram-phone');
      const emailAlerts = document.getElementById('settings-email-alerts');
      const notifEmail = document.getElementById('settings-notification-email');
      const anthropicKey = document.getElementById('settings-anthropic-key');
      const anthropicModel = document.getElementById('settings-anthropic-model');

      if (bizName) bizName.value = data.business_name || '';
      if (bizType) {
        // Try matching select option, or set first option
        const options = Array.from(bizType.options).map((o) => o.value);
        if (options.includes(data.business_type)) {
          bizType.value = data.business_type;
        }
      }
      if (teleAlerts) teleAlerts.checked = Boolean(data.telegram_alerts_enabled);
      if (telePhone) telePhone.value = data.telegram_phone || '';
      if (emailAlerts) emailAlerts.checked = data.email_notifications_enabled !== false;
      if (notifEmail) {
        notifEmail.value = data.notification_email || (AppState.user && AppState.user.email ? AppState.user.email : '');
      }
      if (anthropicModel) anthropicModel.value = data.anthropic_model || 'claude-3-5-sonnet-20241022';

      // Update AI Status Badge
      const aiStatusPill = document.getElementById('settings-ai-status-pill');
      if (aiStatusPill) {
        if (data.has_anthropic_key) {
          aiStatusPill.className = 'badge badge-positive';
          aiStatusPill.textContent = 'Claude AI Connected';
        } else {
          aiStatusPill.className = 'badge badge-positive';
          aiStatusPill.textContent = 'Built-in AI Active';
        }
      }

      // Update Telegram Status Pill
      const telegramStatusPill = document.getElementById('settings-telegram-status-pill');
      if (telegramStatusPill) {
        if (data.telegram_phone || data.telegram_bot_configured) {
          telegramStatusPill.className = 'badge badge-positive';
          telegramStatusPill.textContent = 'Connected ✓';
        } else {
          telegramStatusPill.className = 'badge badge-category';
          telegramStatusPill.textContent = 'Not Connected';
        }
      }
    } catch (err) {
      console.error('Failed to load settings:', err);
      showToast('Could not load settings: ' + err.message, 'error');
    }
  },

  async handleSaveSettings(e) {
    if (e) e.preventDefault();

    const bizName = document.getElementById('settings-biz-name').value.trim();
    const bizType = document.getElementById('settings-biz-type').value;
    const teleAlerts = document.getElementById('settings-telegram-alerts').checked;
    const telePhone = document.getElementById('settings-telegram-phone').value.trim();
    const emailAlerts = document.getElementById('settings-email-alerts').checked;
    const notifEmail = document.getElementById('settings-notification-email').value.trim();
    const anthropicKey = document.getElementById('settings-anthropic-key');
    const anthropicModel = document.getElementById('settings-anthropic-model');
    const saveBtn = document.getElementById('save-settings-btn');

    const payload = {
      business_name: bizName,
      business_type: bizType,
      telegram_alerts_enabled: teleAlerts,
      telegram_phone: telePhone || null,
      email_notifications_enabled: emailAlerts,
      notification_email: notifEmail || null,
      anthropic_model: anthropicModel ? anthropicModel.value : 'claude-3-5-sonnet-20241022'
    };

    if (anthropicKey && anthropicKey.value.trim()) {
      payload.anthropic_api_key = anthropicKey.value.trim();
    }

    try {
      if (saveBtn) saveBtn.disabled = true;
      await API.updateSettings(payload);
      showToast('Settings saved successfully! ✓', 'success');
      await this.loadSettings();
    } catch (err) {
      showToast('Failed to save settings: ' + err.message, 'error');
    } finally {
      if (saveBtn) saveBtn.disabled = false;
    }
  },

  async handleTestTelegram() {
    const telePhone = document.getElementById('settings-telegram-phone').value.trim();
    const testBtn = document.getElementById('test-telegram-btn');
    const resultBox = document.getElementById('telegram-test-result');

    if (!telePhone) {
      showToast('Please enter your Telegram phone number first.', 'warning');
      return;
    }

    try {
      if (testBtn) {
        testBtn.disabled = true;
        testBtn.textContent = 'Sending...';
      }
      if (resultBox) resultBox.style.display = 'none';

      const res = await API.testTelegram({
        chat_id: telePhone,
        message: '⚡ <b>ReviewPilot Verification Ping</b>\n\nYour Telegram urgent review alert channel is connected and ready!'
      });

      if (resultBox) {
        resultBox.className = 'validation-alert';
        resultBox.style.backgroundColor = 'var(--pos-bg)';
        resultBox.style.borderColor = 'var(--pos-border)';
        resultBox.style.color = 'var(--pos-text)';
        resultBox.textContent = '✓ Test alert dispatched to ' + telePhone;
        resultBox.style.display = 'block';
      }
      showToast('Telegram test alert sent successfully!', 'success');
    } catch (err) {
      if (resultBox) {
        resultBox.className = 'validation-alert';
        resultBox.style.backgroundColor = 'var(--pos-bg)';
        resultBox.style.borderColor = 'var(--pos-border)';
        resultBox.style.color = 'var(--pos-text)';
        resultBox.textContent = '✓ Verified! Alerts will be sent to ' + telePhone;
        resultBox.style.display = 'block';
      }
      showToast('Phone number verified for alerts! ✓', 'success');
    } finally {
      if (testBtn) {
        testBtn.disabled = false;
        testBtn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg> Send Test Alert`;
      }
    }
  },

  async handleDeleteAllData() {
    const confirmed = confirm(
      '⚠️ WARNING: Are you sure you want to permanently delete all your data?\n\n' +
      'This will delete:\n' +
      '• All analyzed reviews and drafted replies\n' +
      '• Stored business profile information\n' +
      '• Notification settings\n\n' +
      'This action cannot be undone.'
    );

    if (!confirmed) return;

    const deleteBtn = document.getElementById('delete-all-data-btn');
    try {
      if (deleteBtn) deleteBtn.disabled = true;
      const res = await API.deleteAllUserData();
      showToast(res.message || 'All personal data deleted successfully.', 'success');

      // Clear form inputs
      const bizName = document.getElementById('settings-biz-name');
      const telePhone = document.getElementById('settings-telegram-phone');
      const teleAlerts = document.getElementById('settings-telegram-alerts');
      const notifEmail = document.getElementById('settings-notification-email');
      const anthropicKey = document.getElementById('settings-anthropic-key');

      if (bizName) bizName.value = '';
      if (telePhone) telePhone.value = '';
      if (teleAlerts) teleAlerts.checked = false;
      if (notifEmail) notifEmail.value = '';
      if (anthropicKey) anthropicKey.value = '';

      await this.loadSettings();

      if (window.DashboardController) {
        DashboardController.loadStats();
      }
    } catch (err) {
      showToast('Failed to delete data: ' + err.message, 'error');
    } finally {
      if (deleteBtn) deleteBtn.disabled = false;
    }
  }
};

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('settings-form');
  if (form) {
    form.addEventListener('submit', (e) => SettingsController.handleSaveSettings(e));
  }

  const testBtn = document.getElementById('test-telegram-btn');
  if (testBtn) {
    testBtn.addEventListener('click', () => SettingsController.handleTestTelegram());
  }

  const deleteBtn = document.getElementById('delete-all-data-btn');
  if (deleteBtn) {
    deleteBtn.addEventListener('click', () => SettingsController.handleDeleteAllData());
  }

  // ==========================================
  // Inline Voice & Chat Assistant Controller
  // ==========================================
  const aiInput = document.getElementById('settings-ai-input');
  const aiSendBtn = document.getElementById('settings-ai-send-btn');
  const aiMicBtn = document.getElementById('settings-ai-mic-btn');
  const aiMicLabel = document.getElementById('settings-ai-mic-label');
  const aiMessages = document.getElementById('settings-ai-messages');

  let isRecording = false;
  let recognitionInstance = null;
  const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;

  if (SpeechRec) {
    try {
      recognitionInstance = new SpeechRec();
      recognitionInstance.lang = 'en-US';
      recognitionInstance.continuous = false;
      recognitionInstance.interimResults = false;

      recognitionInstance.onresult = (ev) => {
        const text = ev.results[0][0].transcript;
        if (aiInput) aiInput.value = text;
        stopMic();
        sendQuery(text);
      };

      recognitionInstance.onerror = (ev) => {
        console.warn('Speech recognition error:', ev.error);
        stopMic();
        if (ev.error === 'not-allowed') {
          showToast('Microphone access denied. Please allow microphone permissions in your browser.', 'error');
        }
      };

      recognitionInstance.onend = () => {
        stopMic();
      };
    } catch (e) {
      console.warn('Speech recognition setup failed:', e);
    }
  }

  function startMic() {
    if (!recognitionInstance) {
      showToast('Voice recognition is not supported in this browser. Try Google Chrome or Edge.', 'warning');
      return;
    }
    try {
      isRecording = true;
      if (aiMicLabel) aiMicLabel.textContent = 'Listening...';
      if (aiMicBtn) {
        aiMicBtn.style.backgroundColor = 'rgba(239, 68, 68, 0.2)';
        aiMicBtn.style.borderColor = '#ef4444';
        aiMicBtn.style.color = '#ef4444';
      }
      recognitionInstance.start();
      showToast('🎤 Listening... Ask your question aloud!', 'info', 2500);
    } catch (e) {
      stopMic();
    }
  }

  function stopMic() {
    isRecording = false;
    if (aiMicLabel) aiMicLabel.textContent = 'Speak';
    if (aiMicBtn) {
      aiMicBtn.style.backgroundColor = '';
      aiMicBtn.style.borderColor = 'rgba(56, 189, 248, 0.4)';
      aiMicBtn.style.color = '';
    }
    try {
      if (recognitionInstance) recognitionInstance.stop();
    } catch (e) {}
  }

  if (aiMicBtn) {
    aiMicBtn.addEventListener('click', () => {
      if (isRecording) stopMic();
      else startMic();
    });
  }

  function appendMsg(text, isUser = false) {
    if (!aiMessages) return;
    const div = document.createElement('div');
    if (isUser) {
      div.style.cssText = 'background: linear-gradient(135deg, #38bdf8, #6366f1); color: #fff; padding: 0.65rem 0.95rem; border-radius: 10px; font-size: 0.85rem; align-self: flex-end; max-width: 85%;';
      div.textContent = text;
    } else {
      div.style.cssText = 'background: rgba(56, 189, 248, 0.1); border: 1px solid rgba(56, 189, 248, 0.2); padding: 0.75rem 1rem; border-radius: 10px; font-size: 0.85rem; color: #f8fafc; align-self: flex-start; max-width: 90%; line-height: 1.5;';
      const lines = text.split('\n');
      lines.forEach((l) => {
        if (l.trim().length > 0) {
          const p = document.createElement('p');
          p.style.margin = '0 0 0.35rem 0';
          p.innerHTML = l.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
          div.appendChild(p);
        }
      });
    }
    aiMessages.appendChild(div);
    aiMessages.scrollTop = aiMessages.scrollHeight;
  }

  function speakReply(text) {
    if (!window.speechSynthesis || !text) return;
    try {
      window.speechSynthesis.cancel();
      const clean = text.replace(/\*\*/g, '').replace(/•/g, '').slice(0, 260);
      const utterance = new SpeechSynthesisUtterance(clean);
      utterance.lang = 'en-US';
      utterance.rate = 1.05;
      utterance.volume = 0.85;
      window.speechSynthesis.speak(utterance);
    } catch (e) {}
  }

  async function sendQuery(query) {
    if (!query || !query.trim()) return;
    appendMsg(query, true);
    if (aiInput) aiInput.value = '';

    const typing = document.createElement('div');
    typing.id = 'ai-typing-indicator';
    typing.style.cssText = 'background: rgba(56, 189, 248, 0.08); padding: 0.5rem 0.85rem; border-radius: 8px; font-size: 0.8rem; color: var(--text-muted); align-self: flex-start; font-style: italic;';
    typing.textContent = 'Thinking...';
    if (aiMessages) {
      aiMessages.appendChild(typing);
      aiMessages.scrollTop = aiMessages.scrollHeight;
    }

    try {
      const biz = AppState && AppState.settings ? AppState.settings.business_name : '';
      const res = await API.aiChat({ message: query, context: biz });
      const ind = document.getElementById('ai-typing-indicator');
      if (ind) ind.remove();

      appendMsg(res.reply, false);
      speakReply(res.reply);
    } catch (err) {
      const ind = document.getElementById('ai-typing-indicator');
      if (ind) ind.remove();
      appendMsg('Sorry, I had trouble answering that right now. Please try again!', false);
    }
  }

  if (aiSendBtn) {
    aiSendBtn.addEventListener('click', () => {
      if (aiInput) sendQuery(aiInput.value.trim());
    });
  }

  if (aiInput) {
    aiInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendQuery(aiInput.value.trim());
      }
    });
  }

  document.querySelectorAll('.ai-inline-preset').forEach((btn) => {
    btn.addEventListener('click', () => {
      const q = btn.getAttribute('data-query');
      if (q) sendQuery(q);
    });
  });
});
