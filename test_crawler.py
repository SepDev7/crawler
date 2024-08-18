import aiohttp
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from crawler import Car, fetch_page, save_to_db, scrape_page

# Setup for the tests
DATABASE_URL = "sqlite:///:memory:"  # Use an in-memory SQLite database for testing
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
db_session = Session()

@pytest.fixture(scope="module")
def setup_database():
    Car.metadata.create_all(engine)
    yield
    Car.metadata.drop_all(engine)

@pytest.mark.asyncio
async def test_fetch_page_html(setup_database):
    url = "https://example.com"
    html_content = '''
    <html>
        <body>
            <script type="application/json">
                {"data": {"ads": [{"detail": {"title": "Car 1", "image": "url1"}, "price": {"price": "1000"}}]}}
            </script>
        </body>
    </html>
    '''

    async with patch("aiohttp.ClientSession.get", new_callable=AsyncMock) as mock_get:
        mock_response = AsyncMock()
        mock_response.headers = {'Content-Type': 'text/html'}
        mock_response.text.return_value = html_content
        mock_get.return_value = mock_response
        
        async with aiohttp.ClientSession() as session:
            data = await fetch_page(session, url)
            assert data is not None
            assert "data" in data
            assert len(data['data']['ads']) == 1

@pytest.mark.asyncio
async def test_fetch_page_json(setup_database):
    url = "https://example.com"
    json_content = {"data": {"ads": [{"detail": {"title": "Car 1", "image": "url1"}, "price": {"price": "1000"}}]}}

    async with patch("aiohttp.ClientSession.get", new_callable=AsyncMock) as mock_get:
        mock_response = AsyncMock()
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_response.json.return_value = json_content
        mock_get.return_value = mock_response
        
        async with aiohttp.ClientSession() as session:
            data = await fetch_page(session, url)
            assert data == json_content

@pytest.mark.asyncio
async def test_save_to_db(setup_database):
    cars = [
        {"title": "Car 1", "price": "1000", "image_url": "url1"},
        {"title": "Car 2", "price": "2000", "image_url": "url2"}
    ]

    await save_to_db(cars, db_session)
    
    # Query the database to check if data was inserted
    saved_cars = db_session.query(Car).all()
    assert len(saved_cars) == 2
    assert saved_cars[0].title == "Car 1"
    assert saved_cars[1].price == "2000"

@pytest.mark.asyncio
async def test_scrape_page(setup_database):
    url = "https://example.com"
    json_content = {"data": {"ads": [{"detail": {"title": "Car 1", "image": "url1"}, "price": {"price": "1000"}}]}}

    async with patch("aiohttp.ClientSession.get", new_callable=AsyncMock) as mock_get:
        mock_response = AsyncMock()
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_response.json.return_value = json_content
        mock_get.return_value = mock_response

        semaphore = AsyncMock()
        async with aiohttp.ClientSession() as session:
            await scrape_page(session, url, semaphore)
            
            # Check that data was inserted into the database
            saved_cars = db_session.query(Car).all()
            assert len(saved_cars) == 1
            assert saved_cars[0].title == "Car 1"
            assert saved_cars[0].price == "1000"

# Run the tests
if __name__ == "__main__":
    pytest.main()
