/**
 * ReviewPilot Settings & Integrations Controller
 */

const SettingsController = {
  async loadSettings() {
    try {
      const data = await API.getSettings();
      AppState.settings = data;

      const bizName = document.getElementById('settings-biz-name');
      const bizType = document.getElementById('settings-biz-type');
      const teleToken = document.getElementById('settings-telegram-token');
      const teleChatId = document.getElementById('settings-telegram-chat-id');
      const teleAlerts = document.getElementById('settings-telegram-alerts');
      const anthropicKey = document.getElementById('settings-anthropic-key');
      const anthropicModel = document.getElementById('settings-anthropic-model');

      if (bizName) bizName.value = data.business_name || '';
      if (bizType) bizType.value = data.business_type || '';
      if (teleChatId) teleChatId.value = data.telegram_chat_id || '';
      if (teleAlerts) teleAlerts.checked = Boolean(data.telegram_alerts_enabled);
      if (anthropicModel) anthropicModel.value = data.anthropic_model || 'claude-3-5-sonnet-20241022';

      // Update Integration Badges
      const aiStatusPill = document.getElementById('settings-ai-status-pill');
      if (aiStatusPill) {
        if (data.has_anthropic_key) {
          aiStatusPill.className = 'badge badge-positive';
          aiStatusPill.textContent = 'Anthropic Claude Connected';
          if (anthropicKey) anthropicKey.placeholder = '●●●●●●●●●●●●●●●● (Configured)';
        } else {
          aiStatusPill.className = 'badge badge-neutral';
          aiStatusPill.textContent = 'Local Simulation Mode (Key Optional)';
          if (anthropicKey) anthropicKey.placeholder = 'sk-ant-api03-...';
        }
      }

      const telegramStatusPill = document.getElementById('settings-telegram-status-pill');
      if (telegramStatusPill) {
        if (data.telegram_bot_configured) {
          telegramStatusPill.className = 'badge badge-positive';
          telegramStatusPill.textContent = 'Telegram Configured';
          if (teleToken) teleToken.placeholder = '●●●●●●●●●●●● (Configured)';
        } else {
          telegramStatusPill.className = 'badge badge-category';
          telegramStatusPill.textContent = 'Not Configured';
          if (teleToken) teleToken.placeholder = '123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ';
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
    const bizType = document.getElementById('settings-biz-type').value.trim();
    const teleToken = document.getElementById('settings-telegram-token').value.trim();
    const teleChatId = document.getElementById('settings-telegram-chat-id').value.trim();
    const teleAlerts = document.getElementById('settings-telegram-alerts').checked;
    const anthropicKey = document.getElementById('settings-anthropic-key').value.trim();
    const anthropicModel = document.getElementById('settings-anthropic-model').value;
    const saveBtn = document.getElementById('save-settings-btn');

    const payload = {
      business_name: bizName,
      business_type: bizType,
      telegram_alerts_enabled: teleAlerts,
      anthropic_model: anthropicModel
    };

    if (teleToken) payload.telegram_bot_token = teleToken;
    if (teleChatId) payload.telegram_chat_id = teleChatId;
    if (anthropicKey) payload.anthropic_api_key = anthropicKey;

    try {
      if (saveBtn) saveBtn.disabled = true;
      await API.updateSettings(payload);
      showToast('Settings saved successfully!', 'success');
      updateGlobalBusinessPill(bizName, bizType);
      await this.loadSettings();
    } catch (err) {
      showToast('Failed to save settings: ' + err.message, 'error');
    } finally {
      if (saveBtn) saveBtn.disabled = false;
    }
  },

  async handleTestTelegram() {
    const teleToken = document.getElementById('settings-telegram-token').value.trim();
    const teleChatId = document.getElementById('settings-telegram-chat-id').value.trim();
    const testBtn = document.getElementById('test-telegram-btn');
    const resultBox = document.getElementById('telegram-test-result');

    try {
      if (testBtn) {
        testBtn.disabled = true;
        testBtn.textContent = 'Sending Test...';
      }
      if (resultBox) {
        resultBox.style.display = 'none';
      }

      const res = await API.testTelegram({
        bot_token: teleToken || null,
        chat_id: teleChatId || null,
        message: '⚡ <b>ReviewPilot Verification Ping</b>\n\nYour Telegram urgent review alert channel is connected and ready!'
      });

      if (resultBox) {
        resultBox.className = 'validation-alert';
        resultBox.style.backgroundColor = 'var(--pos-bg)';
        resultBox.style.borderColor = 'var(--pos-border)';
        resultBox.style.color = 'var(--pos-text)';
        resultBox.textContent = '✓ ' + res.message;
        resultBox.style.display = 'block';
      }
      showToast('Telegram test alert sent successfully!', 'success');
    } catch (err) {
      if (resultBox) {
        resultBox.className = 'validation-alert';
        resultBox.style.backgroundColor = 'var(--neg-bg)';
        resultBox.style.borderColor = 'var(--neg-border)';
        resultBox.style.color = 'var(--neg-text)';
        resultBox.textContent = '✗ ' + err.message;
        resultBox.style.display = 'block';
      }
      showToast('Telegram test failed: ' + err.message, 'error');
    } finally {
      if (testBtn) {
        testBtn.disabled = false;
        testBtn.textContent = 'Test Telegram Connection';
      }
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
});

