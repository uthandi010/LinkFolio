def test_create_link_assigns_increasing_position(client, register_user, auth_header):
    user = register_user()
    headers = auth_header(user["token"])

    first = client.post("/api/links", json={"title": "GitHub", "url": "https://github.com/me"}, headers=headers)
    second = client.post("/api/links", json={"title": "Twitter", "url": "https://twitter.com/me"}, headers=headers)

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["position"] == 0
    assert second.json()["position"] == 1


def test_create_link_rejects_blank_title(client, register_user, auth_header):
    user = register_user()
    headers = auth_header(user["token"])

    response = client.post("/api/links", json={"title": "   ", "url": "https://example.com"}, headers=headers)

    assert response.status_code == 422


def test_list_links_only_returns_my_own(client, register_user, auth_header):
    owner = register_user(email="owner@example.com", username="owner")
    other = register_user(email="other@example.com", username="other")
    client.post("/api/links", json={"title": "Mine", "url": "https://example.com/mine"}, headers=auth_header(owner["token"]))
    client.post("/api/links", json={"title": "Theirs", "url": "https://example.com/theirs"}, headers=auth_header(other["token"]))

    response = client.get("/api/links", headers=auth_header(owner["token"]))

    titles = [link["title"] for link in response.json()]
    assert titles == ["Mine"]


def test_cannot_update_someone_elses_link(client, register_user, auth_header):
    owner = register_user(email="owner2@example.com", username="owner2")
    other = register_user(email="other2@example.com", username="other2")
    created = client.post(
        "/api/links", json={"title": "Mine", "url": "https://example.com/mine"}, headers=auth_header(owner["token"])
    ).json()

    response = client.patch(
        f"/api/links/{created['id']}", json={"title": "Hijacked"}, headers=auth_header(other["token"])
    )

    assert response.status_code == 404


def test_cannot_delete_someone_elses_link(client, register_user, auth_header):
    owner = register_user(email="owner3@example.com", username="owner3")
    other = register_user(email="other3@example.com", username="other3")
    created = client.post(
        "/api/links", json={"title": "Mine", "url": "https://example.com/mine"}, headers=auth_header(owner["token"])
    ).json()

    response = client.delete(f"/api/links/{created['id']}", headers=auth_header(other["token"]))

    assert response.status_code == 404


def test_update_link_can_toggle_active(client, register_user, auth_header):
    user = register_user()
    headers = auth_header(user["token"])
    created = client.post("/api/links", json={"title": "GitHub", "url": "https://github.com/me"}, headers=headers).json()

    response = client.patch(f"/api/links/{created['id']}", json={"active": False}, headers=headers)

    assert response.status_code == 200
    assert response.json()["active"] is False


def test_reorder_links_updates_positions(client, register_user, auth_header):
    user = register_user()
    headers = auth_header(user["token"])
    first = client.post("/api/links", json={"title": "First", "url": "https://a.example"}, headers=headers).json()
    second = client.post("/api/links", json={"title": "Second", "url": "https://b.example"}, headers=headers).json()

    response = client.post(
        "/api/links/reorder", json={"link_ids": [second["id"], first["id"]]}, headers=headers
    )

    assert response.status_code == 200
    ordered_titles = [link["title"] for link in response.json()]
    assert ordered_titles == ["Second", "First"]


def test_reorder_rejects_a_list_that_doesnt_match_my_links(client, register_user, auth_header):
    user = register_user()
    headers = auth_header(user["token"])
    client.post("/api/links", json={"title": "Only Link", "url": "https://a.example"}, headers=headers)

    response = client.post("/api/links/reorder", json={"link_ids": [9999]}, headers=headers)

    assert response.status_code == 422


def test_delete_link_removes_it(client, register_user, auth_header):
    user = register_user()
    headers = auth_header(user["token"])
    created = client.post("/api/links", json={"title": "GitHub", "url": "https://github.com/me"}, headers=headers).json()

    delete_response = client.delete(f"/api/links/{created['id']}", headers=headers)
    list_response = client.get("/api/links", headers=headers)

    assert delete_response.status_code == 204
    assert list_response.json() == []


import pytest


@pytest.mark.parametrize(
    "bad_url",
    [
        "javascript:alert(1)",
        "data:text/html;base64,PHNjcmlwdD4=",
        "ftp://example.com/file",
        "//example.com",
        "https://",
        "example.com",
        "https://exa mple.com",
        "https://example.com/" + "a" * 2100,
    ],
)
def test_create_link_rejects_non_http_urls(client, register_user, auth_header, bad_url):
    headers = auth_header(register_user()["token"])

    response = client.post("/api/links", json={"title": "Bad", "url": bad_url}, headers=headers)

    assert response.status_code == 422


def test_update_link_rejects_javascript_url(client, register_user, auth_header):
    headers = auth_header(register_user()["token"])
    created = client.post("/api/links", json={"title": "Ok", "url": "https://example.com"}, headers=headers).json()

    response = client.patch(f"/api/links/{created['id']}", json={"url": "javascript:alert(1)"}, headers=headers)

    assert response.status_code == 422


def test_create_link_rejects_overlong_title(client, register_user, auth_header):
    headers = auth_header(register_user()["token"])

    response = client.post("/api/links", json={"title": "t" * 121, "url": "https://example.com"}, headers=headers)

    assert response.status_code == 422


def test_create_link_strips_whitespace_around_url(client, register_user, auth_header):
    headers = auth_header(register_user()["token"])

    response = client.post("/api/links", json={"title": "Ok", "url": "  https://example.com  "}, headers=headers)

    assert response.status_code == 201
    assert response.json()["url"] == "https://example.com"
