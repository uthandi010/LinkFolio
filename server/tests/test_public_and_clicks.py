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
