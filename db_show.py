from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from crawler import Car 

# Database connection
DATABASE_URL = "postgresql://postgres:admin@localhost:5433/crawler"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
db_session = Session()

# Fetch data from the 'cars' table
cars = db_session.query(Car).all()

# Print the data
for car in cars:
    print(f"ID: {car.id}, Title: {car.title}, Price: {car.price}, Image URL: {car.image_url}")

db_session.close()
