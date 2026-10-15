def test_public_profile_returns_name_bio_and_active_links(client, register_user, auth_header):
    user = register_user(name="Ada Lovelace", username="ada")
    headers = auth_header(user["token"])
    client.patch("/api/me", json={"bio": "Building things."}, headers=headers)
    visible = client.post(
        "/api/links", json={"title": "GitHub", "url": "https://github.com/ada"}, headers=headers
    ).json()
    hidden = client.post(
        "/api/links", json={"title": "Old Site", "url": "https://old.example"}, headers=headers
    ).json()
    client.patch(f"/api/links/{hidden['id']}", json={"active": False}, headers=headers)

    response = client.get("/api/public/profiles/ada")

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Ada Lovelace"
    assert body["bio"] == "Building things."
    titles = [link["title"] for link in body["links"]]
    assert titles == ["GitHub"]
    assert visible["title"] in titles


def test_public_profile_404s_for_unknown_username(client):
    response = client.get("/api/public/profiles/does-not-exist")

    assert response.status_code == 404


def test_clicking_a_link_redirects_and_records_a_click(client, register_user, auth_header):
    user = register_user()
    headers = auth_header(user["token"])
    link = client.post(
        "/api/links", json={"title": "GitHub", "url": "https://github.com/me"}, headers=headers
    ).json()

    response = client.get(f"/api/public/links/{link['id']}/go", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == "https://github.com/me"

    summary = client.get("/api/analytics/summary", headers=headers).json()
    assert summary["total_clicks"] == 1


def test_clicking_an_inactive_link_404s_and_does_not_redirect(client, register_user, auth_header):
    user = register_user()
    headers = auth_header(user["token"])
    link = client.post(
        "/api/links", json={"title": "GitHub", "url": "https://github.com/me"}, headers=headers
    ).json()
    client.patch(f"/api/links/{link['id']}", json={"active": False}, headers=headers)

    response = client.get(f"/api/public/links/{link['id']}/go", follow_redirects=False)

    assert response.status_code == 404


def test_clicking_an_unknown_link_404s(client):
    response = client.get("/api/public/links/999999/go", follow_redirects=False)

    assert response.status_code == 404


def test_go_refuses_to_redirect_to_a_non_http_url(client, register_user, auth_header, db_session):
    from app import models

    user = register_user()
    link = client.post(
        "/api/links", json={"title": "Ok", "url": "https://example.com"}, headers=auth_header(user["token"])
    ).json()
    # Simulate legacy data that predates URL validation.
    db_session.get(models.Link, link["id"]).url = "javascript:alert(1)"
    db_session.commit()

    response = client.get(f"/api/public/links/{link['id']}/go", follow_redirects=False)
    profile = client.get(f"/api/public/profiles/{user['username']}").json()

    assert response.status_code == 404
    assert profile["links"] == []


def test_repeat_clicks_in_short_window_are_counted_once(client, register_user, auth_header):
    from app.ratelimit import limiter

    user = register_user()
    headers = auth_header(user["token"])
    link = client.post("/api/links", json={"title": "Ok", "url": "https://example.com"}, headers=headers).json()
    limiter.enabled = True

    for _ in range(3):
        assert client.get(f"/api/public/links/{link['id']}/go", follow_redirects=False).status_code == 302

    assert client.get("/api/analytics/summary", headers=headers).json()["total_clicks"] == 1


def test_go_is_rate_limited(client, register_user, auth_header):
    from app.ratelimit import limiter

    user = register_user()
    link = client.post(
        "/api/links", json={"title": "Ok", "url": "https://example.com"}, headers=auth_header(user["token"])
    ).json()
    limiter.enabled = True

    statuses = [
        client.get(f"/api/public/links/{link['id']}/go", follow_redirects=False).status_code for _ in range(61)
    ]

    assert statuses[-1] == 429


def test_referrer_is_capped_and_broken_down_per_link(client, register_user, auth_header):
    user = register_user()
    headers = auth_header(user["token"])
    link = client.post("/api/links", json={"title": "Ok", "url": "https://example.com"}, headers=headers).json()

    client.get(f"/api/public/links/{link['id']}/go", headers={"referer": "https://x.example/" + "a" * 2000}, follow_redirects=False)
    client.get(f"/api/public/links/{link['id']}/go", follow_redirects=False)

    row = client.get("/api/analytics/summary", headers=headers).json()["clicks_by_link"][0]
    referrers = {r["referrer"]: r["clicks"] for r in row["referrers"]}
    assert "(direct)" in referrers
    assert all(len(name) <= 512 for name in referrers)
    assert sum(referrers.values()) == 2
