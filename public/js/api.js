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

    const token = localStorage.getItem('reviewpilot_token');
    const authHeader = token ? { 'Authorization': `Bearer ${token}` } : {};

    const config = {
      ...options,
      headers: {
        ...defaultHeaders,
        ...authHeader,
        ...(options.headers || {})
      }
    };

    try {
      const response = await fetch(url, config);
      const isJson = (response.headers.get('content-type') || '').includes('application/json');
      const data = isJson ? await response.json().catch(() => ({})) : null;

      if (!response.ok || data === null) {
        const errorMsg = (data && (data.detail || data.message)) || `API call failed (${response.status})`;
        throw new Error(errorMsg);
      }

      return data;
    } catch (err) {
      console.error(`API Error on [${options.method || 'GET'} ${endpoint}]:`, err);
      throw err;
    }
  },

  // Auth Methods
  async register(payload) {
    return this.request('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  async login(payload) {
    return this.request('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  async loginGoogle(payload) {
    return this.request('/api/auth/google', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  async loginPhone(payload) {
    return this.request('/api/auth/phone', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  async getMyProfile() {
    return this.request('/api/auth/me');
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

  async aiChat(payload) {
    return this.request('/api/ai/chat', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  // Review Platform Integrations
  async getPlatformConnections() {
    return this.request('/api/platforms/connections');
  },

  async getGoogleAuthUrl() {
    return this.request('/api/platforms/google/auth-url');
  },

  async setPlatformLocation(connectionId, locationId, locationName) {
    return this.request(`/api/platforms/${connectionId}/location`, {
      method: 'PUT',
      body: JSON.stringify({ location_id: locationId, location_name: locationName })
    });
  },

  async syncPlatformReviews(connectionId, payload) {
    return this.request(`/api/platforms/${connectionId}/sync`, {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  async connectPlatformApiKey(payload) {
    return this.request('/api/platforms/connect/api-key', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  async disconnectPlatform(connectionId) {
    return this.request(`/api/platforms/${connectionId}`, {
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
