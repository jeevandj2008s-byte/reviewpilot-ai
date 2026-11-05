with open('frontend/js/settings.js', 'r', encoding='utf-8') as f:
    content = f.read()

old_handler = """  async handleGoogleSync() {
    if (!this.activeGoogleConnection) {
      showToast('No active Google connection found.', 'warning');
      return;
    }

    const syncBtn = document.getElementById('google-sync-btn');
    const periodSelect = document.getElementById('google-sync-period');
    const customStart = document.getElementById('google-custom-start');
    const customEnd = document.getElementById('google-custom-end');
    const resultMsg = document.getElementById('google-sync-result-msg');

    const period = periodSelect ? periodSelect.value : '7d';
    const payload = {
      period: period,
      start_date: period === 'custom' && customStart ? customStart.value : null,
      end_date: period === 'custom' && customEnd ? customEnd.value : null,
      tone: AppState.currentTone || 'Friendly',
      notify_telegram: true
    };

    try {
      if (syncBtn) {
        syncBtn.disabled = true;
        syncBtn.innerHTML = `<span class="spinner" style="width: 14px; height: 14px; border-width: 2px;"></span> Fetching...`;
      }
      if (resultMsg) resultMsg.textContent = 'Retrieving customer reviews from Google API and analyzing...';

      const res = await API.syncPlatformReviews(this.activeGoogleConnection.id, payload);

      if (resultMsg) {
        resultMsg.textContent = res.message;
        resultMsg.style.color = '#38bdf8';
      }

      showToast(res.message, 'success');

      // If in Review Analyzer, render newly synced reviews directly into analysis cards
      if (res.results && res.results.length > 0 && window.AnalyzerController) {
        AnalyzerController.currentBatchResults = res.results;
        AnalyzerController.renderBatchSummary({
          total_analyzed: res.new_analyzed || res.results.length,
          positive_count: res.results.filter(r => r.sentiment === 'Positive').length,
          neutral_count: res.results.filter(r => r.sentiment === 'Neutral').length,
          negative_count: res.results.filter(r => r.sentiment === 'Negative').length,
          urgent_count: res.urgent_count || 0,
          telegram_sent_count: res.telegram_sent_count || 0,
          ai_provider: 'ReviewPilot API'
        });
        AnalyzerController.renderFilteredCards();
        const resultsSec = document.getElementById('results-section');
        if (resultsSec) {
          resultsSec.style.display = 'block';
          resultsSec.scrollIntoView({ behavior: 'smooth' });
        }
      }

      // Refresh dashboard analytics so KPI cards, distribution chart, and recent feed reflect newly synced reviews
      if (window.DashboardController && typeof DashboardController.loadStats === 'function') {
        DashboardController.loadStats();
      }

      await this.loadPlatformConnections();
    } catch (err) {
      if (resultMsg) {
        resultMsg.textContent = 'Sync error: ' + err.message;
        resultMsg.style.color = '#f87171';
      }
      showToast('Sync failed: ' + err.message, 'error');
    } finally {
      if (syncBtn) {
        syncBtn.disabled = false;
        syncBtn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg> <span>Sync & Analyze</span>`;
      }
    }
  },"""

new_handler = """  async handleGoogleSync(forceReanalyze = false) {
    if (!this.activeGoogleConnection) {
      showToast('No active Google connection found. Please connect your Google Business Profile first.', 'warning');
      const googleCard = document.getElementById('google-platform-card');
      if (googleCard) googleCard.scrollIntoView({ behavior: 'smooth' });
      return;
    }

    const syncBtn = document.getElementById('google-sync-btn');
    const googleAnalyzeBtn = document.getElementById('google-analyze-btn');
    const analyzeConnectedBtn = document.getElementById('analyze-connected-platforms-btn');
    const periodSelect = document.getElementById('google-sync-period');
    const customStart = document.getElementById('google-custom-start');
    const customEnd = document.getElementById('google-custom-end');
    const resultMsg = document.getElementById('google-sync-result-msg');
    const progressWrap = document.getElementById('analyzer-progress');
    const progressText = document.getElementById('progress-status-text');

    const period = periodSelect ? periodSelect.value : '7d';
    // Get currently selected tone from Analyzer UI if available
    let currentTone = AppState.currentTone || 'Friendly';
    const activeTonePill = document.querySelector('.tone-pill-btn.active');
    if (activeTonePill && activeTonePill.dataset.tone) {
      currentTone = activeTonePill.dataset.tone;
    }

    const payload = {
      period: period,
      start_date: period === 'custom' && customStart ? customStart.value : null,
      end_date: period === 'custom' && customEnd ? customEnd.value : null,
      tone: currentTone,
      notify_telegram: true,
      force_reanalyze: Boolean(forceReanalyze)
    };

    try {
      if (syncBtn) {
        syncBtn.disabled = true;
        syncBtn.innerHTML = `<span class="spinner" style="width: 14px; height: 14px; border-width: 2px;"></span> Fetching...`;
      }
      if (googleAnalyzeBtn) {
        googleAnalyzeBtn.disabled = true;
        googleAnalyzeBtn.innerHTML = `<span class="spinner" style="width: 14px; height: 14px; border-width: 2px;"></span> Analyzing...`;
      }
      if (analyzeConnectedBtn) {
        analyzeConnectedBtn.disabled = true;
        analyzeConnectedBtn.innerHTML = `<span class="spinner" style="width: 14px; height: 14px; border-width: 2px;"></span> Analyzing Reviews...`;
      }
      if (resultMsg) resultMsg.textContent = 'Retrieving customer reviews from Google API and analyzing...';
      if (progressWrap) progressWrap.style.display = 'block';
      if (progressText) progressText.textContent = 'Retrieving verified customer reviews from Google Business Profile and evaluating sentiment...';

      const res = await API.syncPlatformReviews(this.activeGoogleConnection.id, payload);

      if (resultMsg) {
        resultMsg.textContent = res.message;
        resultMsg.style.color = 'var(--text-main)';
      }

      showToast(res.message, 'success');

      // Populate reviews into Review Analyzer and render cards
      if (res.results && res.results.length > 0 && window.AnalyzerController) {
        // Also populate the textarea with the review text so the user sees them
        const textarea = document.getElementById('reviews-textarea');
        if (textarea) {
          textarea.value = res.results.map(r => r.review_text).join('\\n');
          if (typeof AnalyzerController.updateCounters === 'function') {
            AnalyzerController.updateCounters();
          }
        }

        AnalyzerController.currentBatchResults = res.results;
        AnalyzerController.renderBatchSummary({
          total_analyzed: res.results.length,
          positive_count: res.results.filter(r => r.sentiment === 'Positive').length,
          neutral_count: res.results.filter(r => r.sentiment === 'Neutral').length,
          negative_count: res.results.filter(r => r.sentiment === 'Negative').length,
          urgent_count: res.urgent_count || 0,
          telegram_sent_count: res.telegram_sent_count || 0,
          ai_provider: res.platform ? (res.platform.toUpperCase() + ' API') : 'Google Business API'
        });
        AnalyzerController.renderFilteredCards();
        const resultsSec = document.getElementById('results-section');
        if (resultsSec) {
          resultsSec.style.display = 'block';
          resultsSec.scrollIntoView({ behavior: 'smooth' });
        }
      }

      // Refresh dashboard analytics so KPI cards, distribution chart, and recent feed reflect newly synced reviews
      if (window.DashboardController && typeof DashboardController.loadStats === 'function') {
        DashboardController.loadStats();
      }

      await this.loadPlatformConnections();
    } catch (err) {
      if (resultMsg) {
        resultMsg.textContent = 'Sync error: ' + err.message;
        resultMsg.style.color = '#f87171';
      }
      showToast('Sync failed: ' + err.message, 'error');
    } finally {
      if (progressWrap) progressWrap.style.display = 'none';
      if (syncBtn) {
        syncBtn.disabled = false;
        syncBtn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg> <span>Sync & Analyze</span>`;
      }
      if (googleAnalyzeBtn) {
        googleAnalyzeBtn.disabled = false;
        googleAnalyzeBtn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg> <span>Analyze Google Reviews</span>`;
      }
      if (analyzeConnectedBtn) {
        analyzeConnectedBtn.disabled = false;
        analyzeConnectedBtn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg> <span>Analyze Connected Reviews</span>`;
      }
    }
  },

  async handleAnalyzeAllConnected() {
    try {
      const connections = await API.getPlatformConnections();
      if (!connections || connections.length === 0) {
        showToast('No review platforms connected yet. Connect Google Business Profile to analyze reviews.', 'warning');
        const googleCard = document.getElementById('google-platform-card');
        if (googleCard) googleCard.scrollIntoView({ behavior: 'smooth' });
        return;
      }
      // If Google connection is present, trigger sync & analyze
      const googleConn = connections.find(c => c.platform === 'google' && c.status === 'connected');
      if (googleConn) {
        this.activeGoogleConnection = googleConn;
        await this.handleGoogleSync(true);
      } else {
        // First active connection
        const firstActive = connections.find(c => c.status === 'connected');
        if (firstActive) {
          const payload = {
            period: '7d',
            tone: AppState.currentTone || 'Friendly',
            notify_telegram: true,
            force_reanalyze: true
          };
          const res = await API.syncPlatformReviews(firstActive.id, payload);
          showToast(res.message, 'success');
          if (res.results && res.results.length > 0 && window.AnalyzerController) {
            AnalyzerController.currentBatchResults = res.results;
            AnalyzerController.renderFilteredCards();
            const resultsSec = document.getElementById('results-section');
            if (resultsSec) resultsSec.scrollIntoView({ behavior: 'smooth' });
          }
        } else {
          showToast('No active connections found. Please connect your Google Business Profile.', 'warning');
        }
      }
    } catch (err) {
      showToast('Analyze failed: ' + err.message, 'error');
    }
  },"""

if old_handler in content:
    content = content.replace(old_handler, new_handler, 1)
    print("Updated handleGoogleSync and added handleAnalyzeAllConnected in settings.js")
else:
    print("Warning: old_handler not found verbatim")

# Add button listeners in DOMContentLoaded
old_listeners = """  const googleSyncBtn = document.getElementById('google-sync-btn');
  if (googleSyncBtn) {
    googleSyncBtn.addEventListener('click', () => SettingsController.handleGoogleSync());
  }

  const googleDisconnectBtn = document.getElementById('google-disconnect-btn');
  if (googleDisconnectBtn) {
    googleDisconnectBtn.addEventListener('click', () => SettingsController.handleGoogleDisconnect());
  }"""

new_listeners = """  const googleSyncBtn = document.getElementById('google-sync-btn');
  if (googleSyncBtn) {
    googleSyncBtn.addEventListener('click', () => SettingsController.handleGoogleSync(false));
  }

  const googleAnalyzeBtn = document.getElementById('google-analyze-btn');
  if (googleAnalyzeBtn) {
    googleAnalyzeBtn.addEventListener('click', () => SettingsController.handleGoogleSync(true));
  }

  const analyzeConnectedBtn = document.getElementById('analyze-connected-platforms-btn');
  if (analyzeConnectedBtn) {
    analyzeConnectedBtn.addEventListener('click', () => SettingsController.handleAnalyzeAllConnected());
  }

  const googleDisconnectBtn = document.getElementById('google-disconnect-btn');
  if (googleDisconnectBtn) {
    googleDisconnectBtn.addEventListener('click', () => SettingsController.handleGoogleDisconnect());
  }"""

if old_listeners in content:
    content = content.replace(old_listeners, new_listeners, 1)
    print("Added event listeners for google-analyze-btn and analyze-connected-platforms-btn")
else:
    print("Warning: old_listeners not found verbatim")

with open('frontend/js/settings.js', 'w', encoding='utf-8') as f:
    f.write(content)

print("Saved frontend/js/settings.js")
