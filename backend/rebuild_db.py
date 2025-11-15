#!/usr/bin/env python3
"""
Rebuild database with 8 specific dishes and one week of linear data
"""

import os
import sys
from datetime import date, timedelta
from flask import Flask
import random

# Add current directory to path to import models
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import db, Dish, Day, Serving

# Initialize Flask app for database operations
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, "hackathon_project_test.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

def rebuild_database():
    """Rebuild the entire database with new data"""
    
    with app.app_context():
        # Drop all existing tables and recreate
        db.drop_all()
        db.create_all()
        
        print("Creating 8 dishes...")
        
        # Define 8 dishes with categories
        dishes_data = [
            {"id": 1, "name": "Hamburger", "category": "protein", "image_path": "/images/1.png"},
            {"id": 2, "name": "Pizza", "category": "staple", "image_path": "/images/2.png"},
            {"id": 3, "name": "French fries", "category": "staple", "image_path": "/images/3.png"},
            {"id": 4, "name": "Chicken", "category": "protein", "image_path": "/images/4.png"},
            {"id": 5, "name": "Ice cream", "category": "dairy", "image_path": "/images/5.png"},
            {"id": 6, "name": "Pasta", "category": "staple", "image_path": "/images/6.png"},
            {"id": 7, "name": "Banana", "category": "vegetable", "image_path": "/images/7.png"},
            {"id": 8, "name": "Burrito", "category": "protein", "image_path": "/images/8.png"}
        ]
        
        # Create dishes
        dishes = []
        for dish_data in dishes_data:
            dish = Dish(
                name=dish_data["name"],
                category=dish_data["category"],
                image_path=dish_data["image_path"]
            )
            db.session.add(dish)
            dishes.append(dish)
        
        db.session.flush()  # Get dish IDs
        
        print("Creating one week of data (Nov 10-16, 2025)...")
        
        # Define fixed waste rates for each dish (to ensure linearity)
        # These represent each dish's inherent waste rate
        dish_waste_rates = {
            1: 0.15,  # Hamburger - moderate waste
            2: 0.12,  # Pizza - low waste  
            3: 0.20,  # French fries - higher waste
            4: 0.10,  # Chicken - low waste
            5: 0.25,  # Ice cream - high waste (melts)
            6: 0.08,  # Pasta - very low waste
            7: 0.30,  # Banana - highest waste (spoils quickly)
            8: 0.14   # Burrito - moderate waste
        }
        
        # Create 7 days of data (Nov 10-16, 2025)
        start_date = date(2025, 11, 10)
        
        for day_offset in range(7):
            current_date = start_date + timedelta(days=day_offset)
            
            # Select 6 dishes randomly for each day
            available_dish_ids = list(range(1, 9))  # IDs 1-8
            selected_dish_ids = sorted(random.sample(available_dish_ids, 6))
            
            # Generate serving quantities (20-50 units per dish)
            servings_data = []
            total_waste = 0
            
            for dish_id in selected_dish_ids:
                # Random serving quantity between 20-50
                quantity = round(random.uniform(20, 50), 2)
                
                # Calculate waste based on fixed waste rate
                waste_rate = dish_waste_rates[dish_id]
                dish_waste = quantity * waste_rate
                total_waste += dish_waste
                
                servings_data.append({
                    "dish_id": dish_id,
                    "quantity": quantity,
                    "waste": dish_waste
                })
            
            # Round total waste to 2 decimal places
            total_waste = round(total_waste, 2)
            
            # Create Day record
            day = Day(date=current_date, total_waste=total_waste)
            db.session.add(day)
            db.session.flush()  # Get day ID
            
            # Create Serving records
            for serving_data in servings_data:
                serving = Serving(
                    day_id=day.id,
                    dish_id=serving_data["dish_id"],
                    quantity=serving_data["quantity"]
                )
                db.session.add(serving)
            
            print(f"Day {current_date}: {len(selected_dish_ids)} dishes, total waste: {total_waste}kg")
            print(f"  Dishes: {[dishes[i-1].name for i in selected_dish_ids]}")
        
        # Commit all changes
        db.session.commit()
        print("\nDatabase successfully rebuilt!")
        
        # Verify data
        print(f"\nVerification:")
        print(f"Total dishes: {Dish.query.count()}")
        print(f"Total days: {Day.query.count()}")
        print(f"Total servings: {Serving.query.count()}")
        
        # Show dish categories
        print(f"\nDish categories:")
        for dish in Dish.query.order_by(Dish.id).all():
            print(f"  {dish.id}. {dish.name} ({dish.category}) - {dish.image_path}")

if __name__ == "__main__":
    # Set random seed for reproducible data
    random.seed(42)
    rebuild_database()