with open('frontend/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

target1 = """                        <div style="display: flex; align-items: center; justify-content: space-between;">
                          <span id="google-sync-result-msg" class="text-xs text-muted">Ready to fetch reviews.</span>
                          <button type="button" id="google-disconnect-btn" class="btn btn-outline-danger btn-sm" style="font-size: 0.75rem; padding: 0.3rem 0.65rem;">
                            Disconnect Account
                          </button>
                        </div>"""

replacement1 = """                        <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 0.75rem; flex-wrap: wrap; gap: 0.65rem;">
                          <div style="display: flex; align-items: center; gap: 0.65rem; flex-wrap: wrap;">
                            <button type="button" id="google-analyze-btn" class="btn btn-primary btn-sm" style="display: inline-flex; align-items: center; gap: 0.4rem; padding: 0.45rem 0.95rem; font-weight: 600;">
                              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
                              <span>Analyze Google Reviews</span>
                            </button>
                            <span id="google-sync-result-msg" class="text-xs text-muted">Ready to fetch reviews.</span>
                          </div>
                          <button type="button" id="google-disconnect-btn" class="btn btn-outline-danger btn-sm" style="font-size: 0.75rem; padding: 0.3rem 0.65rem;">
                            Disconnect Account
                          </button>
                        </div>"""

if target1 in content:
    content = content.replace(target1, replacement1, 1)
    print("Added google-analyze-btn to frontend/index.html")
else:
    print("Warning: target1 not found")

target2 = """                    </details>
                  </div>
                </div>
              </div>

              <!-- Input Card -->"""

replacement2 = """                    </details>

                    <!-- Overarching Analyze Action Bar for all connected review platforms -->
                    <div style="display: flex; align-items: center; justify-content: space-between; padding-top: 1.15rem; border-top: 1px solid var(--border); margin-top: 0.5rem; flex-wrap: wrap; gap: 0.75rem;">
                      <div>
                        <span style="font-size: 0.9rem; font-weight: 600; color: var(--text-main);">Analyze Reviews from Connected Platforms</span>
                        <p class="text-xs text-muted" style="margin: 0.15rem 0 0 0;">Retrieve verified reviews from your connected accounts and evaluate sentiment, risks, and replies.</p>
                      </div>
                      <button type="button" id="analyze-connected-platforms-btn" class="btn btn-primary" style="display: inline-flex; align-items: center; gap: 0.5rem; padding: 0.6rem 1.35rem; font-weight: 700;">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
                        <span>Analyze Connected Reviews</span>
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Input Card -->"""

if target2 in content:
    content = content.replace(target2, replacement2, 1)
    print("Added analyze-connected-platforms-btn action bar to frontend/index.html")
else:
    print("Warning: target2 not found")

with open('frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Saved frontend/index.html")
