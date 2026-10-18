/**
 * ReviewPilot API Service Client
 */
const API = {
  baseUrl: '',

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const defaultHeaders = {
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    };

    const config = {
      ...options,
      headers: {
        ...defaultHeaders,
        ...(options.headers || {})
      }
    };

    try {
      const response = await fetch(url, config);
      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        const errorMsg = data.detail || data.message || `Request failed with status ${response.status}`;
        throw new Error(errorMsg);
      }

      return data;
    } catch (err) {
      console.error(`API Error on [${options.method || 'GET'} ${endpoint}]:`, err);
      throw err;
    }
  },

  // Stats
  async getStats() {
    return this.request('/api/stats');
  },

  // Reviews CRUD
  async getReviews(params = {}) {
    const searchParams = new URLSearchParams();
    if (params.limit) searchParams.set('limit', params.limit);
    if (params.offset) searchParams.set('offset', params.offset);
    if (params.sentiment && params.sentiment !== 'all') searchParams.set('sentiment', params.sentiment);
    if (params.urgent_only) searchParams.set('urgent_only', 'true');
    if (params.search) searchParams.set('search', params.search);

    const query = searchParams.toString() ? `?${searchParams.toString()}` : '';
    return this.request(`/api/reviews${query}`);
  },

  async analyzeReviews(payload) {
    return this.request('/api/analyze', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  async updateReviewReply(reviewId, replyText) {
    return this.request(`/api/reviews/${reviewId}/reply`, {
      method: 'PATCH',
      body: JSON.stringify({ reply_text: replyText })
    });
  },

  async regenerateReply(reviewId, tone, businessName, businessType) {
    return this.request(`/api/reviews/${reviewId}/regenerate`, {
      method: 'POST',
      body: JSON.stringify({
        tone,
        business_name: businessName,
        business_type: businessType
      })
    });
  },

  async deleteReview(reviewId) {
    return this.request(`/api/reviews/${reviewId}`, {
      method: 'DELETE'
    });
  },

  async clearAllReviews() {
    return this.request('/api/reviews', {
      method: 'DELETE'
    });
  },

  // Settings
  async getSettings() {
    return this.request('/api/settings');
  },

  async updateSettings(payload) {
    return this.request('/api/settings', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  async testTelegram(payload) {
    return this.request('/api/telegram/test', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  async deleteAllUserData() {
    return this.request('/api/data/delete-all', {
      method: 'DELETE'
    });
  },

  // Export URLs
  getExportCsvUrl() {
    return '/api/export/csv';
  },

  getExportJsonUrl() {
    return '/api/export/json';
  }
};


