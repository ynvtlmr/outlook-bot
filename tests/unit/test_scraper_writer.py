import pytest
import os
from scraper import scrape_messages
# We mock logic, so no real outlook interaction

def test_scrape_messages_success(mocker, mock_raw_applescript_output):
    # Mock OutlookClient
    mock_client_cls = mocker.patch("scraper.OutlookClient")
    mock_client = mock_client_cls.return_value
    mock_client._run_script.return_value = mock_raw_applescript_output
    
    # Mock file writing
    m = mocker.patch("builtins.open", mocker.mock_open())
    mocker.patch("os.makedirs")
    mocker.patch("os.path.exists", return_value=False)
    
    # Mock OUTPUT_DIR import if needed, but it's imported from config
    # We can patch it in scraper
    mocker.patch("scraper.OUTPUT_DIR", "/tmp/mock_output")
    
    threads = scrape_messages("test_script.scpt")
    
    assert len(threads) == 2
    # Verify file write calls
    # 2 threads top 50
    assert m.call_count == 2
    
def test_scrape_messages_error(mocker):
    mock_client_cls = mocker.patch("scraper.OutlookClient")
    mock_client = mock_client_cls.return_value
    mock_client._run_script.side_effect = Exception("Outlook Error")
    
    threads = scrape_messages("test.scpt")
    assert threads is None
