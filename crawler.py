import asyncio
import aiohttp
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base
import json
import time

# Database setup
DATABASE_URL = "postgresql://postgres:admin@localhost:5433/crawler"

Base = declarative_base()

class Car(Base):
    __tablename__ = 'cars'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    price = Column(String, nullable=False)
    image_url = Column(String, nullable=True)

# Connect to the database
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
db_session = Session()

# Fetch page data
async def fetch_page(session, url):
    async with session.get(url) as response:
        content_type = response.headers.get('Content-Type', '')
        if 'application/json' in content_type:
            return await response.json()
        elif 'text/html' in content_type:
            html_content = await response.text()
            soup = BeautifulSoup(html_content, 'html.parser')
            script_tag = soup.find('script', type='application/json')
            if script_tag:
                json_data = json.loads(script_tag.string)
                return json_data
            else:
                print("No JSON data found in the HTML response.")
                return None
        else:
            print(f"Unexpected content type: {content_type}")
            return None

# Save data to the database
async def save_to_db(cars, db_session):
    if not cars:
        return
    try:
        db_session.bulk_insert_mappings(Car, cars)
        db_session.commit()
    except Exception as e:
        db_session.rollback()
        print(f"Error saving to database: {e}")

# Scrape a single page
async def scrape_page(session, url, semaphore):
    async with semaphore:
        data = await fetch_page(session, url)
        if data is None:
            return

        cars = []
        for ad in data.get('data', {}).get('ads', []):
            detail = ad.get('detail')
            price_info = ad.get('price')
            
            if detail and price_info:
                title = detail.get('title')
                price = price_info.get('price')
                image_url = detail.get('image')
                
                if title and price and image_url:
                    car = {
                        'title': title,
                        'price': price,
                        'image_url': image_url
                    }
                    cars.append(car)
        
        await save_to_db(cars, db_session)

# Main function to run the crawler
async def main():
    start_time = time.time()

    # Limit the number of concurrent tasks to avoid being throttled
    semaphore = asyncio.Semaphore(10)

    async with aiohttp.ClientSession() as session:
        tasks = []

        for i in range(1, 80):
            url = f"https://bama.ir/cad/api/search?vehicle=pride&pageIndex={i}"
            tasks.append(scrape_page(session, url, semaphore))
        await asyncio.gather(*tasks)

    end_time = time.time()
    print(f"Time taken: {end_time - start_time} seconds")

if __name__ == "__main__":
    Base.metadata.create_all(engine)
    asyncio.run(main())
