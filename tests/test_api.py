import asyncio
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import init_db, clear_all_reviews

client = TestClient(app)

def setup_module():
    init_db()
    clear_all_reviews()

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "ReviewPilot"

def test_frontend_serving():
    response = client.get("/")
    assert response.status_code == 200
    assert "ReviewPilot" in response.text
    assert "Every review deserves" in response.text

def test_empty_stats_zero_state():
    clear_all_reviews()
    response = client.get("/api/stats")
    assert response.status_code == 200
    stats = response.json()
    assert stats["total_reviews"] == 0
    assert stats["urgent_count"] == 0
    assert stats["positive_count"] == 0

def test_batch_analyze():
    reviews = [
        "The iced latte and avocado toast were fantastic! The server was so kind.",
        "Average atmosphere, coffee was okay but tables were slightly sticky.",
        "Horrible experience. Waited 45 minutes for a salad and the cashier yelled at me.",
        "URGENT: I got violent food poisoning and was hospitalized after eating here on Tuesday!"
    ]

    payload = {
        "reviews": reviews,
        "tone": "Empathetic",
        "business_name": "Test Cafe & Bistro",
        "business_type": "Cafe",
        "notify_telegram": False
    }

    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["total_reviews"] == 4
    assert len(data["results"]) == 4

    # Verify at least one urgent review was detected
    assert data["urgent_count"] >= 1

    # Verify sentiment and replies
    results = data["results"]
    sentiments = [r["sentiment"] for r in results]
    assert "Positive" in sentiments
    assert "Negative" in sentiments

    for r in results:
        assert len(r["generated_reply"]) > 10
        assert r["category"] is not None

def test_stats_after_analysis():
    response = client.get("/api/stats")
    assert response.status_code == 200
    stats = response.json()
    assert stats["total_reviews"] == 4
    assert stats["positive_count"] >= 1
    assert stats["negative_count"] >= 1
    assert stats["urgent_count"] >= 1
    assert stats["most_common_category"] is not None

def test_export_csv():
    response = client.get("/api/export/csv")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "ID,Created At,Sentiment" in response.text

def test_export_json():
    response = client.get("/api/export/json")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 4

def test_update_reply():
    reviews_res = client.get("/api/reviews")
    assert reviews_res.status_code == 200
    reviews = reviews_res.json()
    target_id = reviews[0]["id"]

    new_reply = "Customized staff response: Thank you for your feedback!"
    patch_res = client.patch(f"/api/reviews/{target_id}/reply", json={"reply_text": new_reply})
    assert patch_res.status_code == 200

    single_res = client.get(f"/api/reviews/{target_id}")
    assert single_res.status_code == 200
    assert single_res.json()["generated_reply"] == new_reply

def test_regenerate_reply():
    reviews_res = client.get("/api/reviews")
    reviews = reviews_res.json()
    target_id = reviews[0]["id"]

    regen_res = client.post(f"/api/reviews/{target_id}/regenerate", json={"tone": "Concise"})
    assert regen_res.status_code == 200
    data = regen_res.json()
    assert data["status"] == "success"
    assert data["tone"] == "Concise"
    assert len(data["generated_reply"]) > 5

def test_settings_endpoints():
    settings_res = client.get("/api/settings")
    assert settings_res.status_code == 200
    data = settings_res.json()
    assert "business_name" in data

    update_res = client.post("/api/settings", json={
        "business_name": "Antigravity Specialty Roasters",
        "business_type": "Specialty Coffee Shop"
    })
    assert update_res.status_code == 200

    settings_after = client.get("/api/settings").json()
    assert settings_after["business_name"] == "Antigravity Specialty Roasters"

def test_delete_all_user_data():
    delete_res = client.delete("/api/data/delete-all")
    assert delete_res.status_code == 200
    data = delete_res.json()
    assert data["status"] == "success"

    # Verify reviews are cleared
    reviews_res = client.get("/api/reviews")
    assert len(reviews_res.json()) == 0

    # Verify stats are reset
    stats_res = client.get("/api/stats")
    assert stats_res.json()["total_reviews"] == 0

if __name__ == "__main__":
    setup_module()
    test_health()
    test_frontend_serving()
    test_empty_stats_zero_state()
    test_batch_analyze()
    test_stats_after_analysis()
    test_export_csv()
    test_export_json()
    test_update_reply()
    test_regenerate_reply()
    test_settings_endpoints()
    test_delete_all_user_data()
    print("All tests passed successfully!")

