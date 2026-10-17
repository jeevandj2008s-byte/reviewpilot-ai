/**
 * ReviewPilot Review Analyzer Controller
 */

const AnalyzerController = {
  currentTone: 'Friendly',
  currentBatchResults: [],
  currentFilter: 'all',
  currentSearchQuery: '',

  init() {
    this.bindEvents();
    this.updateCounters();
  },

  bindEvents() {
    const textarea = document.getElementById('reviews-textarea');
    if (textarea) {
      textarea.addEventListener('input', () => this.updateCounters());
    }

    // Tone pills
    document.querySelectorAll('.tone-pill-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.tone-pill-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.currentTone = btn.dataset.tone;
      });
    });

    // Preset pills
    document.querySelectorAll('.preset-pill').forEach(pill => {
      pill.addEventListener('click', () => {
        const presetKey = pill.dataset.preset;
        this.loadPreset(presetKey);
      });
    });

    // Clear textarea
    const clearBtn = document.getElementById('clear-input-btn');
    if (clearBtn) {
      clearBtn.addEventListener('click', () => {
        if (textarea) textarea.value = '';
        this.updateCounters();
        this.hideValidationAlert();
      });
    }

    // Submit Analyze button
    const analyzeBtn = document.getElementById('analyze-btn');
    if (analyzeBtn) {
      analyzeBtn.addEventListener('click', () => this.handleAnalyzeSubmit());
    }

    // Result Filter tabs
    document.querySelectorAll('.filter-tab').forEach(tab => {
      tab.addEventListener('click', () => {
        document.querySelectorAll('.filter-tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        this.currentFilter = tab.dataset.filter;
        this.renderFilteredCards();
      });
    });

    // Result Search Input
    const searchInput = document.getElementById('results-search-input');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        this.currentSearchQuery = e.target.value.toLowerCase().trim();
        this.renderFilteredCards();
      });
    }

    // Export Buttons
    const exportCsvBtn = document.getElementById('export-csv-btn');
    if (exportCsvBtn) {
      exportCsvBtn.addEventListener('click', () => {
        window.location.href = API.getExportCsvUrl();
        showToast('Downloading CSV report...', 'success');
      });
    }

    const exportJsonBtn = document.getElementById('export-json-btn');
    if (exportJsonBtn) {
      exportJsonBtn.addEventListener('click', () => {
        window.location.href = API.getExportJsonUrl();
        showToast('Downloading JSON file...', 'success');
      });
    }
  },

  updateCounters() {
    const textarea = document.getElementById('reviews-textarea');
    const lineCounter = document.getElementById('line-counter');
    const charCounter = document.getElementById('char-counter');
    if (!textarea) return;

    const text = textarea.value;
    const lines = text.split('\n').filter(l => l.trim().length > 0);
    const lineCount = lines.length;
    const charCount = text.length;

    if (lineCounter) {
      lineCounter.textContent = `${lineCount} / 20 reviews`;
      if (lineCount > 20) {
        lineCounter.classList.add('limit-exceeded');
        this.showValidationAlert(`Batch limit is 20 reviews. You currently have ${lineCount}. Please remove ${lineCount - 20} review(s).`);
      } else {
        lineCounter.classList.remove('limit-exceeded');
        this.hideValidationAlert();
      }
    }

    if (charCounter) {
      charCounter.textContent = `${charCount} characters`;
    }
  },

  loadPreset(key) {
    const textarea = document.getElementById('reviews-textarea');
    const bizNameInput = document.getElementById('analyzer-biz-name');
    const bizTypeInput = document.getElementById('analyzer-biz-type');

    if (!SAMPLE_PRESETS[key] || !textarea) return;

    textarea.value = SAMPLE_PRESETS[key].join('\n');
    this.updateCounters();
    this.hideValidationAlert();

    // Auto-fill context
    if (key === 'cafe') {
      if (bizNameInput) bizNameInput.value = 'Artisan Roasters Cafe';
      if (bizTypeInput) bizTypeInput.value = 'Cafe & Bakery';
    } else if (key === 'restaurant') {
      if (bizNameInput) bizNameInput.value = 'Trattoria Bella Napoli';
      if (bizTypeInput) bizTypeInput.value = 'Italian Restaurant';
    } else if (key === 'salon') {
      if (bizNameInput) bizNameInput.value = 'Luxe Hair & Spa Lounge';
      if (bizTypeInput) bizTypeInput.value = 'Hair Salon & Spa';
    } else if (key === 'gym') {
      if (bizNameInput) bizNameInput.value = 'IronPulse Fitness Center';
      if (bizTypeInput) bizTypeInput.value = 'Gym & Health Club';
    }

    showToast(`Loaded 4 example reviews for ${key.toUpperCase()}`, 'info');
  },

  showValidationAlert(msg) {
    const alertBox = document.getElementById('validation-alert');
    if (alertBox) {
      alertBox.textContent = msg;
      alertBox.style.display = 'block';
    }
  },

  hideValidationAlert() {
    const alertBox = document.getElementById('validation-alert');
    if (alertBox) {
      alertBox.style.display = 'none';
    }
  },

  async handleAnalyzeSubmit() {
    const textarea = document.getElementById('reviews-textarea');
    const bizNameInput = document.getElementById('analyzer-biz-name');
    const bizTypeInput = document.getElementById('analyzer-biz-type');
    const telegramToggle = document.getElementById('analyzer-telegram-toggle');
    const analyzeBtn = document.getElementById('analyze-btn');
    const progressWrapper = document.getElementById('analyzer-progress');
    const progressText = document.getElementById('progress-status-text');

    if (!textarea) return;

    const rawLines = textarea.value.split('\n');
    const reviews = rawLines.map(l => l.trim()).filter(l => l.length > 0);

    if (reviews.length === 0) {
      this.showValidationAlert('Please enter or paste at least one customer review to analyze.');
      return;
    }

    if (reviews.length > 20) {
      this.showValidationAlert(`Maximum 20 reviews per batch. You provided ${reviews.length}.`);
      return;
    }

    this.hideValidationAlert();

    // UI Loading state
    if (analyzeBtn) analyzeBtn.disabled = true;
    if (progressWrapper) progressWrapper.style.display = 'block';
    if (progressText) progressText.textContent = `Analyzing ${reviews.length} review${reviews.length > 1 ? 's' : ''} in parallel with AI...`;

    const payload = {
      reviews: reviews,
      tone: this.currentTone,
      business_name: bizNameInput ? bizNameInput.value.trim() : null,
      business_type: bizTypeInput ? bizTypeInput.value.trim() : null,
      notify_telegram: telegramToggle ? telegramToggle.checked : true
    };

    try {
      const response = await API.analyzeReviews(payload);
      this.currentBatchResults = response.results || [];

      // Render results
      this.renderBatchSummary(response);
      this.renderFilteredCards();

      // Show Results section
      const resultsSection = document.getElementById('results-section');
      if (resultsSection) {
        resultsSection.style.display = 'block';
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }

      showToast(`Successfully analyzed ${response.total_reviews} reviews!`, 'success');

      // Refresh dashboard in background
      DashboardController.loadStats();

    } catch (err) {
      console.error('Batch analysis failed:', err);
      this.showValidationAlert(`Analysis failed: ${err.message}. Please check your connection or retry.`);
      showToast('Analysis error: ' + err.message, 'error');
    } finally {
      if (analyzeBtn) analyzeBtn.disabled = false;
      if (progressWrapper) progressWrapper.style.display = 'none';
    }
  },

  renderBatchSummary(batchResponse) {
    const totalEl = document.getElementById('batch-stat-total');
    const posEl = document.getElementById('batch-stat-pos');
    const neuEl = document.getElementById('batch-stat-neu');
    const negEl = document.getElementById('batch-stat-neg');
    const urgentEl = document.getElementById('batch-stat-urgent');
    const providerBadge = document.getElementById('batch-ai-provider-badge');
    const telegramBanner = document.getElementById('batch-telegram-alert-banner');
    const urgentTabCount = document.getElementById('filter-urgent-count');

    if (totalEl) totalEl.textContent = batchResponse.total_reviews;
    if (posEl) posEl.textContent = batchResponse.positive_count;
    if (neuEl) neuEl.textContent = batchResponse.neutral_count;
    if (negEl) negEl.textContent = batchResponse.negative_count;
    if (urgentEl) urgentEl.textContent = batchResponse.urgent_count;

    if (urgentTabCount) {
      urgentTabCount.textContent = batchResponse.urgent_count > 0 ? ` (${batchResponse.urgent_count})` : '';
    }

    if (providerBadge) {
      providerBadge.textContent = batchResponse.ai_provider || 'ReviewPilot AI';
    }

    // Telegram notification banner check
    const anyTelegramAlerted = batchResponse.results.some(r => r.telegram_sent);
    if (telegramBanner) {
      if (anyTelegramAlerted) {
        telegramBanner.style.display = 'flex';
      } else {
        telegramBanner.style.display = 'none';
      }
    }
  },

  renderFilteredCards() {
    const container = document.getElementById('results-cards-list');
    if (!container) return;

    container.innerHTML = '';

    // Apply Filter
    let filtered = this.currentBatchResults;

    if (this.currentFilter === 'urgent') {
      filtered = filtered.filter(r => r.is_urgent);
    } else if (this.currentFilter === 'positive') {
      filtered = filtered.filter(r => r.sentiment === 'Positive');
    } else if (this.currentFilter === 'neutral') {
      filtered = filtered.filter(r => r.sentiment === 'Neutral');
    } else if (this.currentFilter === 'negative') {
      filtered = filtered.filter(r => r.sentiment === 'Negative');
    }

    // Apply Search
    if (this.currentSearchQuery) {
      filtered = filtered.filter(r =>
        r.review_text.toLowerCase().includes(this.currentSearchQuery) ||
        r.generated_reply.toLowerCase().includes(this.currentSearchQuery) ||
        r.category.toLowerCase().includes(this.currentSearchQuery)
      );
    }

    if (filtered.length === 0) {
      container.innerHTML = `
        <div class="card text-center" style="padding: 3rem; text-align: center;">
          <p class="text-muted">No reviews match the selected filter criteria.</p>
        </div>
      `;
      return;
    }

    filtered.forEach(item => {
      const card = this.createReviewCard(item);
      container.appendChild(card);
    });
  },

  createReviewCard(item) {
    const card = document.createElement('div');
    card.className = `review-card ${item.is_urgent ? 'urgent-review-card' : ''}`;
    card.id = `card-${item.id}`;

    let sentimentClass = 'badge-neutral';
    if (item.sentiment === 'Positive') sentimentClass = 'badge-positive';
    else if (item.sentiment === 'Negative') sentimentClass = 'badge-negative';

    const confidenceScorePct = Math.round((item.sentiment_score || 0.85) * 100);

    const urgentBadgeHtml = item.is_urgent
      ? `<span class="badge badge-urgent"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/></svg> Urgent Escalation</span>`
      : '';

    const telegramSentHtml = item.telegram_sent
      ? `<span class="badge badge-category" style="color: #0284c7; border-color: #bae6fd; background-color: #f0f9ff;" title="Alert sent via Telegram"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg> Telegram Notified</span>`
      : '';

    const urgencyCalloutHtml = item.is_urgent && item.urgent_reason
      ? `<div class="urgency-callout">
           <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/></svg>
           <span><strong>Why this is urgent:</strong> ${item.urgent_reason}</span>
         </div>`
      : '';

    card.innerHTML = `
      <div class="review-card-header">
        <div class="badges-group">
          <span class="badge ${sentimentClass}">${item.sentiment} (${confidenceScorePct}%)</span>
          <span class="badge badge-category">${item.category}</span>
          ${urgentBadgeHtml}
          ${telegramSentHtml}
        </div>
        <span class="text-xs text-muted">ID: ${item.id.slice(0, 8)}</span>
      </div>

      <div class="review-text-quote">
        "${item.review_text}"
      </div>

      ${urgencyCalloutHtml}

      <div class="generated-reply-box">
        <div class="reply-header-meta">
          <span class="reply-tag">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
            Generated Reply (${item.tone})
          </span>
          <span class="copy-feedback-pill" id="copy-feedback-${item.id}">✓ Copied</span>
        </div>

        <div class="reply-display-area" id="reply-display-${item.id}">
          <p class="reply-body-text" id="reply-text-${item.id}">${item.generated_reply}</p>
        </div>

        <div class="reply-edit-area" id="reply-edit-${item.id}" style="display: none;">
          <textarea class="reply-inline-textarea" id="reply-textarea-${item.id}">${item.generated_reply}</textarea>
          <div style="display: flex; gap: 0.5rem; justify-content: flex-end; margin-top: 0.5rem;">
            <button class="btn btn-secondary btn-sm cancel-edit-btn" data-id="${item.id}">Cancel</button>
            <button class="btn btn-primary btn-sm save-edit-btn" data-id="${item.id}">Save Reply</button>
          </div>
        </div>

        <div class="reply-footer-actions">
          <div class="reply-btn-group">
            <button class="btn btn-primary btn-sm copy-btn" data-id="${item.id}">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
              Copy Reply
            </button>
            <button class="btn btn-secondary btn-sm edit-btn" data-id="${item.id}">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
              Edit
            </button>
            <button class="btn btn-secondary btn-sm regen-btn" data-id="${item.id}">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
              Regenerate
            </button>
          </div>
          <button class="btn btn-outline-danger btn-sm delete-btn" data-id="${item.id}" title="Delete Review Record">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
          </button>
        </div>
      </div>
    `;

    // Bind card buttons
    this.bindCardEvents(card, item);

    return card;
  },

  bindCardEvents(card, item) {
    const copyBtn = card.querySelector('.copy-btn');
    const editBtn = card.querySelector('.edit-btn');
    const regenBtn = card.querySelector('.regen-btn');
    const deleteBtn = card.querySelector('.delete-btn');
    const saveEditBtn = card.querySelector('.save-edit-btn');
    const cancelEditBtn = card.querySelector('.cancel-edit-btn');

    const displayArea = card.querySelector(`#reply-display-${item.id}`);
    const editArea = card.querySelector(`#reply-edit-${item.id}`);
    const textarea = card.querySelector(`#reply-textarea-${item.id}`);
    const textElem = card.querySelector(`#reply-text-${item.id}`);
    const copyPill = card.querySelector(`#copy-feedback-${item.id}`);

    // Copy to clipboard
    if (copyBtn) {
      copyBtn.addEventListener('click', async () => {
        try {
          const currentText = textElem ? textElem.textContent : item.generated_reply;
          await navigator.clipboard.writeText(currentText);

          if (copyPill) {
            copyPill.style.display = 'inline';
            setTimeout(() => { copyPill.style.display = 'none'; }, 2000);
          }
          copyBtn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg> Copied!`;
          setTimeout(() => {
            copyBtn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg> Copy Reply`;
          }, 2000);
          showToast('Reply copied to clipboard!', 'success');
        } catch {
          showToast('Failed to copy text', 'error');
        }
      });
    }

    // Toggle Edit Mode
    if (editBtn) {
      editBtn.addEventListener('click', () => {
        displayArea.style.display = 'none';
        editArea.style.display = 'block';
        if (textarea) textarea.focus();
      });
    }

    if (cancelEditBtn) {
      cancelEditBtn.addEventListener('click', () => {
        if (textarea && textElem) textarea.value = textElem.textContent;
        editArea.style.display = 'none';
        displayArea.style.display = 'block';
      });
    }

    // Save Edited Reply
    if (saveEditBtn) {
      saveEditBtn.addEventListener('click', async () => {
        const newText = textarea.value.trim();
        if (!newText) {
          showToast('Reply text cannot be empty.', 'error');
          return;
        }

        try {
          saveEditBtn.disabled = true;
          await API.updateReviewReply(item.id, newText);
          textElem.textContent = newText;
          item.generated_reply = newText;
          editArea.style.display = 'none';
          displayArea.style.display = 'block';
          showToast('Reply updated successfully!', 'success');
          DashboardController.loadStats();
        } catch (err) {
          showToast('Could not save reply: ' + err.message, 'error');
        } finally {
          saveEditBtn.disabled = false;
        }
      });
    }

    // Regenerate Reply
    if (regenBtn) {
      regenBtn.addEventListener('click', async () => {
        const tones = ['Friendly', 'Professional', 'Empathetic', 'Concise'];
        const chosenTone = prompt(`Choose tone to regenerate: (${tones.join(', ')})`, item.tone || 'Friendly');
        if (!chosenTone) return;

        const matchedTone = tones.find(t => t.toLowerCase() === chosenTone.toLowerCase().trim());
        if (!matchedTone) {
          showToast('Invalid tone option selected.', 'error');
          return;
        }

        try {
          regenBtn.disabled = true;
          regenBtn.textContent = 'Generating...';
          const res = await API.regenerateReply(item.id, matchedTone);
          textElem.textContent = res.generated_reply;
          item.generated_reply = res.generated_reply;
          item.tone = res.tone;

          const tag = card.querySelector('.reply-tag');
          if (tag) tag.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg> Generated Reply (${res.tone})`;

          showToast(`Reply regenerated in ${res.tone} tone!`, 'success');
          DashboardController.loadStats();
        } catch (err) {
          showToast('Regeneration failed: ' + err.message, 'error');
        } finally {
          regenBtn.disabled = false;
          regenBtn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg> Regenerate`;
        }
      });
    }

    // Delete review
    if (deleteBtn) {
      deleteBtn.addEventListener('click', async () => {
        if (confirm('Delete this review record?')) {
          try {
            await API.deleteReview(item.id);
            card.remove();
            this.currentBatchResults = this.currentBatchResults.filter(r => r.id !== item.id);
            showToast('Review deleted.', 'info');
            DashboardController.loadStats();
          } catch (err) {
            showToast('Delete failed: ' + err.message, 'error');
          }
        }
      });
    }
  }
};

document.addEventListener('DOMContentLoaded', () => {
  AnalyzerController.init();
});

