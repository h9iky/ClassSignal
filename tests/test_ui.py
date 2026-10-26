def test_homepage_serves_russian_classsignal_interface(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert '<html lang="ru">' in response.text
    assert "ClassSignal" in response.text
    assert "/static/styles.css" in response.text
    assert "/static/app.js" in response.text


def test_frontend_assets_are_served(client):
    stylesheet = client.get("/static/styles.css")
    javascript = client.get("/static/app.js")

    assert stylesheet.status_code == 200
    assert "text/css" in stylesheet.headers["content-type"]
    assert javascript.status_code == 200
    assert "javascript" in javascript.headers["content-type"]
