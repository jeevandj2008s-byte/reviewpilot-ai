/**
 * ReviewPilot Dashboard & Analytics Controller
 */

const DashboardController = {
  sentimentChart: null,

  escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  },

  async loadStats() {
    try {
      const stats = await API.getStats();
      this.renderDashboard(stats);
    } catch (err) {
      console.error('Failed to load dashboard stats:', err);
      showToast('Could not load dashboard metrics: ' + err.message, 'error');
    }
  },

  renderDashboard(stats) {
    const zeroState = document.getElementById('dashboard-zero-state');
    const contentState = document.getElementById('dashboard-content-state');

    if (!stats || !stats.total_reviews || stats.total_reviews === 0) {
      if (zeroState) zeroState.style.display = 'block';
      if (contentState) contentState.style.display = 'none';
      return;
    }

    if (zeroState) zeroState.style.display = 'none';
    if (contentState) contentState.style.display = 'block';

    // Update KPI numbers
    this.updateElem('dash-total-reviews', stats.total_reviews);
    this.updateElem('dash-positive-count', stats.positive_count);
    this.updateElem('dash-positive-pct', `${stats.positive_percentage}% of total`);
    this.updateElem('dash-neutral-count', stats.neutral_count);
    this.updateElem('dash-neutral-pct', `${stats.neutral_percentage}% of total`);
    this.updateElem('dash-negative-count', stats.negative_count);
    this.updateElem('dash-negative-pct', `${stats.negative_percentage}% of total`);
    this.updateElem('dash-urgent-count', stats.urgent_count);

    // Complaint highlight
    const complaintBox = document.getElementById('dash-complaint-box');
    const complaintText = document.getElementById('dash-top-complaint-title');
    const complaintSub = document.getElementById('dash-top-complaint-desc');

    if (stats.most_common_complaint) {
      if (complaintBox) complaintBox.style.display = 'flex';
      if (complaintText) complaintText.textContent = `Frequent Concern: ${stats.most_common_complaint}`;
      if (complaintSub) {
        complaintSub.textContent = `Negative reviews frequently point to issues with ${stats.most_common_complaint.toLowerCase()}. Check your team's processes in this area.`;
      }
    } else {
      if (complaintBox) complaintBox.style.display = 'none';
    }

    // Render Charts & Categories
    this.renderSentimentChart(stats);
    this.renderCategoriesList(stats.categories_breakdown, stats.total_reviews);
    this.renderRecentReviews(stats.recent_reviews);
  },

  renderSentimentChart(stats) {
    const canvas = document.getElementById('sentimentDoughnutChart');
    if (!canvas) return;

    if (this.sentimentChart) {
      this.sentimentChart.destroy();
    }

    const pos = stats.positive_count || 0;
    const neu = stats.neutral_count || 0;
    const neg = stats.negative_count || 0;

    const ctx = canvas.getContext('2d');
    this.sentimentChart = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: ['Positive', 'Neutral', 'Negative'],
        datasets: [{
          data: [pos, neu, neg],
          backgroundColor: ['#10b981', '#f59e0b', '#ef4444'],
          borderColor: '#ffffff',
          borderWidth: 3,
          hoverOffset: 4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              boxWidth: 12,
              padding: 16,
              font: { family: 'Inter', size: 12 }
            }
          },
          tooltip: {
            callbacks: {
              label: (context) => {
                const val = context.raw || 0;
                const total = stats.total_reviews || 1;
                const pct = Math.round((val / total) * 100);
                return ` ${context.label}: ${val} (${pct}%)`;
              }
            }
          }
        },
        cutout: '68%'
      }
    });
  },

  renderCategoriesList(categoriesBreakdown, total) {
    const listContainer = document.getElementById('dash-categories-list');
    if (!listContainer) return;

    listContainer.innerHTML = '';

    const entries = Object.entries(categoriesBreakdown || {});
    if (entries.length === 0) {
      listContainer.innerHTML = '<p class="text-muted text-sm">No topics categorized yet.</p>';
      return;
    }

    entries.forEach(([catName, count]) => {
      const pct = Math.round((count / total) * 100);
      const row = document.createElement('div');
      row.className = 'category-row';
      row.innerHTML = `
        <div class="cat-label-row">
          <span>${catName}</span>
          <span class="text-muted">${count} (${pct}%)</span>
        </div>
        <div class="cat-bar-bg">
          <div class="cat-bar-fill" style="width: ${pct}%;"></div>
        </div>
      `;
      listContainer.appendChild(row);
    });
  },

  renderRecentReviews(recentReviews) {
    const feed = document.getElementById('dash-recent-feed');
    if (!feed) return;

    feed.innerHTML = '';

    if (!recentReviews || recentReviews.length === 0) {
      feed.innerHTML = '<p class="text-muted text-sm">No reviews in the feed.</p>';
      return;
    }

    recentReviews.forEach(r => {
      const item = document.createElement('div');
      item.className = 'recent-item';

      let sentimentBadgeClass = 'badge-neutral';
      if (r.sentiment === 'Positive') sentimentBadgeClass = 'badge-positive';
      else if (r.sentiment === 'Negative') sentimentBadgeClass = 'badge-negative';

      const urgentBadgeHtml = r.is_urgent
        ? `<span class="badge badge-urgent"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/></svg> Urgent Alert</span>`
        : '';

      const telegramPill = r.telegram_sent
        ? `<span class="text-xs text-muted" title="Telegram alert dispatched">📱 Alerted</span>`
        : '';

      item.innerHTML = `
        <div class="recent-item-top">
          <div class="recent-badges">
            <span class="badge ${sentimentBadgeClass}">${this.escapeHtml(r.sentiment)}</span>
            <span class="badge badge-category">${this.escapeHtml(r.category)}</span>
            ${urgentBadgeHtml}
            ${telegramPill}
          </div>
          <span class="recent-time">${this.formatTimestamp(r.created_at)}</span>
        </div>
        <p class="recent-review-text">&ldquo;${this.escapeHtml(r.review_text)}&rdquo;</p>
        <div class="recent-reply-box">
          <div class="recent-reply-text">
            <strong>AI Reply (${this.escapeHtml(r.tone)}):</strong> ${this.escapeHtml(r.generated_reply)}
          </div>
          <button class="btn btn-secondary btn-sm copy-recent-btn" data-reply="${encodeURIComponent(r.generated_reply)}">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
            Copy
          </button>
        </div>
      `;

      // Copy reply event
      const copyBtn = item.querySelector('.copy-recent-btn');
      copyBtn.addEventListener('click', async () => {
        try {
          await navigator.clipboard.writeText(decodeURIComponent(copyBtn.dataset.reply));
          copyBtn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg> Copied!`;
          setTimeout(() => {
            copyBtn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg> Copy`;
          }, 2000);
          showToast('Reply copied to clipboard!', 'success');
        } catch (e) {
          showToast('Could not copy to clipboard', 'error');
        }
      });

      feed.appendChild(item);
    });
  },

  updateElem(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
  },

  formatTimestamp(isoString) {
    if (!isoString) return '';
    try {
      const d = new Date(isoString);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) + ' · ' + d.toLocaleDateString([], { month: 'short', day: 'numeric' });
    } catch {
      return '';
    }
  }
};

// Bind dashboard reset button
document.addEventListener('DOMContentLoaded', () => {
  const clearBtn = document.getElementById('clear-all-data-btn');
  if (clearBtn) {
    clearBtn.addEventListener('click', async () => {
      if (confirm('Are you sure you want to delete all analyzed reviews? This will reset the dashboard to zero state.')) {
        try {
          await API.clearAllReviews();
          showToast('All review records cleared. Dashboard reset.', 'success');
          DashboardController.loadStats();
        } catch (err) {
          showToast('Failed to clear reviews: ' + err.message, 'error');
        }
      }
    });
  }
});

