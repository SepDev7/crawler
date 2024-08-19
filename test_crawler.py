import json
import pytest
import asyncio
from unittest.mock import MagicMock, patch
from aioresponses import aioresponses
import aiohttp
from crawler import fetch_page, scrape_page, save_to_db, Car, db_session

@pytest.mark.asyncio
async def test_fetch_page_html():
    # Mock HTTP response
    mock_response = """
    <html>
        <head><script type="application/json">{"data": {"ads": [{"detail": {"title": "Car Title", "image": "http://example.com/image.jpg"}, "price": {"price": "10000"}}]}}</script></head>
        <body></body>
    </html>
    """

    with aioresponses() as mock:
        mock.get('https://example.com', body=mock_response, headers={'Content-Type': 'text/html'})
        async with aiohttp.ClientSession() as session:
            data = await fetch_page(session, 'https://example.com')
            assert data is not None
            assert data['data']['ads'][0]['detail']['title'] == 'Car Title'
            assert data['data']['ads'][0]['price']['price'] == '10000'

@pytest.mark.asyncio
async def test_scrape_page():
    # Mock HTTP response
    mock_response = {
        "data": {
            "ads": [
                {
                    "detail": {
                        "title": "Car Title",
                        "image": "http://example.com/image.jpg"
                    },
                    "price": {
                        "price": "10000"
                    }
                }
            ]
        }
    }

    # Mock fetch_page to return mock_response
    with patch('crawler.fetch_page', return_value=mock_response) as mock_fetch_page:
        # Mock save_to_db
        with patch('crawler.save_to_db') as mock_save_to_db:
            with aioresponses() as mock:
                mock.get('https://example.com', body=json.dumps(mock_response), headers={'Content-Type': 'application/json'})
                async with aiohttp.ClientSession() as session:
                    semaphore = asyncio.Semaphore(10)
                    await scrape_page(session, 'https://example.com', semaphore)
                    
                    # Check if save_to_db was called
                    assert mock_save_to_db.call_count == 1
                    
                    # Verify the arguments passed to save_to_db
                    args, kwargs = mock_save_to_db.call_args
                    assert args[0] == [
                        {
                            'title': 'Car Title',
                            'price': '10000',
                            'image_url': 'http://example.com/image.jpg'
                        }
                    ]

@pytest.mark.asyncio
async def test_save_to_db():
    cars = [{'title': 'Car Title', 'price': '10000', 'image_url': 'http://example.com/image.jpg'}]
    
    # Mocking the database session
    mock_session = MagicMock()
    mock_session.bulk_insert_mappings = MagicMock()
    mock_session.commit = MagicMock()
    
    await save_to_db(cars, mock_session)
    
    # Ensure bulk_insert_mappings was called with the correct parameters
    mock_session.bulk_insert_mappings.assert_called_once_with(Car, cars)
    mock_session.commit.assert_called_once()
