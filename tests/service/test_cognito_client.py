from app.service.cognito_client import get_user_info, CognitoClientError

def test_get_user_info_success(monkeypatch, app):
    class FakeResponse:
        def raise_for_status(self):
            pass
        def json(self):
            return {
                "preferred_username": "michael",
                "email": "michael@test.com",
                "sub": "abc123"
            }

    def fake_requests_get(url, headers):
        assert "oauth2/userInfo" in url
        assert headers["Authorization"] == "Bearer testtoken"
        return FakeResponse()

    monkeypatch.setattr("app.service.cognito_client.requests.get", fake_requests_get)

    app.config["AWS_REGION"] = "us-east-2"
    app.config["AWS_DOMAIN"] = "mydomain"

    with app.app_context():
        result = get_user_info("testtoken")

    assert result["username"] == "michael"
    assert result["attributes"]["email"] == "michael@test.com"


def test_get_user_info_failure(monkeypatch, app):
    def fake_requests_get(url, headers):
        raise Exception("Cognito exploded")

    monkeypatch.setattr("app.service.cognito_client.requests.get", fake_requests_get)

    app.config["AWS_REGION"] = "us-east-2"
    app.config["AWS_DOMAIN"] = "mydomain"

    with app.app_context():
        try:
            get_user_info("badtoken")
            assert False, "Expected CognitoClientError"
        except CognitoClientError as e:
            assert "Failed to get user info" in str(e)