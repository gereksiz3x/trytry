import pytest
from main import RojadirectaScraper
from unittest.mock import Mock, patch

class TestRojadirectaScraper:
    def setup_method(self):
        self.scraper = RojadirectaScraper()
    
    def test_detect_league(self):
        assert self.scraper._detect_league("Galatasaray vs Fenerbahçe Süper Lig") == "SÜPER LİG"
        assert self.scraper._detect_league("Manchester United vs Liverpool Premier League") == "PREMIER LEAGUE"
    
    def test_is_valid_stream_url(self):
        assert self.scraper._is_valid_stream_url("https://example.com/stream") == True
        assert self.scraper._is_valid_stream_url("javascript:void(0)") == False
    
    @patch('main.requests.Session.get')
    def test_get_daily_matches(self, mock_get):
        # Mock response oluştur
        mock_response = Mock()
        mock_response.content = """
        <html>
            <body>
                <div class="match">
                    <a href="/match1">Galatasaray vs Fenerbahçe Süper Lig 20:00</a>
                </div>
            </body>
        </html>
        """
        mock_get.return_value = mock_response
        
        matches = self.scraper.get_daily_matches()
        assert len(matches) > 0
        assert "Süper Lig" in matches[0]['name']

if __name__ == "__main__":
    pytest.main([__file__])