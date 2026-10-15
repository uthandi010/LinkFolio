from datetime import datetime, timezone


def test_summary_with_no_links_is_all_zero(client, register_user, auth_header):
    user = register_user()

    response = client.get("/api/analytics/summary", headers=auth_header(user["token"]))

    assert response.status_code == 200
    body = response.json()
    assert body["total_clicks"] == 0
    assert body["total_links"] == 0
    assert body["clicks_by_link"] == []
    assert len(body["clicks_by_day"]) == 30


def test_summary_counts_clicks_per_link(client, register_user, auth_header):
    user = register_user()
    headers = auth_header(user["token"])
    popular = client.post(
        "/api/links", json={"title": "Popular", "url": "https://a.example"}, headers=headers
    ).json()
    quiet = client.post(
        "/api/links", json={"title": "Quiet", "url": "https://b.example"}, headers=headers
    ).json()

    client.get(f"/api/public/links/{popular['id']}/go", follow_redirects=False)
    client.get(f"/api/public/links/{popular['id']}/go", follow_redirects=False)
    client.get(f"/api/public/links/{quiet['id']}/go", follow_redirects=False)

    summary = client.get("/api/analytics/summary", headers=headers).json()

    assert summary["total_clicks"] == 3
    assert summary["total_links"] == 2
    by_title = {row["title"]: row["clicks"] for row in summary["clicks_by_link"]}
    assert by_title == {"Popular": 2, "Quiet": 1}


def test_summary_clicks_by_day_includes_todays_clicks(client, register_user, auth_header):
    user = register_user()
    headers = auth_header(user["token"])
    link = client.post(
        "/api/links", json={"title": "GitHub", "url": "https://github.com/me"}, headers=headers
    ).json()
    client.get(f"/api/public/links/{link['id']}/go", follow_redirects=False)

    summary = client.get("/api/analytics/summary", headers=headers).json()

    today_key = datetime.now(timezone.utc).date().isoformat()
    today_row = next(row for row in summary["clicks_by_day"] if row["date"] == today_key)
    assert today_row["clicks"] == 1


def test_summary_does_not_leak_another_users_clicks(client, register_user, auth_header):
    me = register_user(email="me@example.com", username="me")
    other = register_user(email="other@example.com", username="other")
    other_link = client.post(
        "/api/links", json={"title": "Theirs", "url": "https://a.example"}, headers=auth_header(other["token"])
    ).json()
    client.get(f"/api/public/links/{other_link['id']}/go", follow_redirects=False)

    summary = client.get("/api/analytics/summary", headers=auth_header(me["token"])).json()

    assert summary["total_clicks"] == 0
