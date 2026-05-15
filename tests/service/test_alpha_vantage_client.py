from unittest.mock import patch, MagicMock
from app.service.alpha_vantage_client import get_company_name, get_price_data, get_quote, SecurityQuote

def test_get_company_name_success(app):
    with app.app_context():

        # Fake cache
        mock_cache = MagicMock()
        mock_cache.get.return_value = None  # simulate cache miss

        with patch("app.service.alpha_vantage_client._get_cache", return_value=mock_cache):
            with patch("app.service.alpha_vantage_client._get_api_key", return_value="demo-key"):

                # Fake API response
                mock_response = MagicMock()
                mock_response.json.return_value = {
                    "bestMatches": [
                        {"2. name": "Microsoft Corporation"}
                    ]
                }

                with patch("app.service.alpha_vantage_client.requests.get", return_value=mock_response) as mock_get:
                    result = get_company_name("MSFT")

                    assert result == "Microsoft Corporation"
                    mock_get.assert_called_once()
                    mock_cache.set.assert_called_once()



def test_get_price_data_success(app):
    with app.app_context():

        # Fake cache object
        mock_cache = MagicMock()
        mock_cache.get.return_value = None  # simulate cache miss

        # Fake API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "Global Quote": {
                "05. price": "123.45",
                "07. latest trading day": "2025-03-10"
            }
        }

        with patch("app.service.alpha_vantage_client._get_cache", return_value=mock_cache):
            with patch("app.service.alpha_vantage_client._get_api_key", return_value="demo-key"):
                with patch("app.service.alpha_vantage_client._check_rate_limit", return_value=None):
                    with patch("app.service.alpha_vantage_client.requests.get", return_value=mock_response):

                        result = get_price_data("MSFT")

                        assert result == {
                            "price": 123.45,
                            "date": "2025-03-10"
                        }

                        # Ensure caching happened
                        mock_cache.set.assert_called_once()


def test_get_quote_success(app):
    with app.app_context():

        # Mock return values
        mock_company_name = "Microsoft Corporation"
        mock_price_data = {"price": 123.45, "date": "2025-03-10"}

        with patch("app.service.alpha_vantage_client.get_company_name", return_value=mock_company_name):
            with patch("app.service.alpha_vantage_client.get_price_data", return_value=mock_price_data):
                with patch("app.service.alpha_vantage_client.time.sleep", return_value=None):

                    result = get_quote("MSFT")

                    assert isinstance(result, SecurityQuote)
                    assert result.ticker == "MSFT"
                    assert result.issuer == "Microsoft Corporation"
                    assert result.price == 123.45
                    assert result.date == "2025-03-10"


