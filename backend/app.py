from flask import Flask, jsonify, request
import numpy as np
from datetime import datetime
import os
import json
from flask_cors import CORS

# ==========================================================
# Initialize Flask and SQLAlchemy
# ==========================================================
app = Flask(__name__)
CORS(
    app,
    resources={r"/*": {"origins": "http://localhost:5173"}}
)
# Ensure database always uses hackathon_project_test.db in backend directory
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, "hackathon_project_test.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# Ensure JSON responses display Chinese characters instead of Unicode escape sequences
app.config['JSON_AS_ASCII'] = False
app.json.ensure_ascii = False

# Use db instance from models.py (avoid duplicate creation)
from models import db
db.init_app(app)

# ==========================================================
# Import models (after db initialization)
# ==========================================================
from models import Dish, Day, Serving


# ==========================================================
# Core computation function: Build P, M and solve W
# ==========================================================
def compute_waste_rates():
    """
    Build from database:
        P: (n_days × n_dishes) serving quantity matrix
        M: (n_days × 1) daily total waste amount
    Constrained least squares solution:
        P W = M
        W = waste rate for each dish (constraint: 0 ≤ W_i ≤ 1)
    
    Use numpy's clip function to constrain waste rates to [0,1] interval, ensuring physical reasonableness
    """
    # --------------------------------------------------
    # 1. Get dish list and fix order
    # --------------------------------------------------
    dishes = Dish.query.order_by(Dish.id).all()
    dish_ids = [d.id for d in dishes]
    n_dishes = len(dishes)

    # --------------------------------------------------
    # 2. Get all dates
    # --------------------------------------------------
    days = Day.query.order_by(Day.id).all()
    n_days = len(days)

    # P: n_days × n_dishes
    P = np.zeros((n_days, n_dishes))
    M = np.zeros(n_days)

    # --------------------------------------------------
    # 3. Build matrices
    # --------------------------------------------------
    for i, day in enumerate(days):
        M[i] = day.total_waste

        # All menu records for this day
        servings = Serving.query.filter_by(day_id=day.id).all()

        for s in servings:
            j = dish_ids.index(s.dish_id)
            P[i, j] = s.quantity

    # --------------------------------------------------
    # 4. Constrained least squares solution for W (each waste rate between 0-1)
    # --------------------------------------------------
    # First perform unconstrained least squares solution
    W_unconstrained, _, _, _ = np.linalg.lstsq(P, M, rcond=None)
    
    # Constrain results to [0,1] interval
    W = np.clip(W_unconstrained, 0, 1)

    return dishes, W


# ==========================================================
# API: Return waste rate for each dish
# ==========================================================
@app.route("/compute_waste_rates")
def get_waste_rates():
    dishes, W = compute_waste_rates()

    result = []
    for dish, w in zip(dishes, W):
        # Prefer stored image path in database, generate default if none
        image_path = dish.image_path if dish.image_path else f"/images/{dish.name}.png"
        result.append({
            "dish_id": dish.id,
            "dish_name": dish.name,
            "waste_rate": float(w),
            "image_path": image_path
        })

    return jsonify(result)


# ==========================================================
# API: Query daily dish serving and waste status
# ==========================================================
@app.route("/days_overview")
def days_overview():
    """
    Return dish serving and waste status for all dates
    Format:
    [
        {
            "day_id": 1,
            "date": "2025-11-14",
            "total_waste": 2.3,
            "servings": [
                {
                    "dish_id": 1,
                    "dish_name": "示例菜品",
                    "quantity": 12.5
                },
                ...
            ]
        },
        ...
    ]
    """
    days = Day.query.order_by(Day.date).all()
    result = []

    for day in days:
        servings = Serving.query.filter_by(day_id=day.id).all()
        servings_list = []
        for s in servings:
            dish = Dish.query.get(s.dish_id)
            #Give priority to using the image paths stored in the database. If not available, generate the default path
            image_path = dish.image_path if dish.image_path else f"/images/{dish.name}.png"
            servings_list.append({
                "dish_id": s.dish_id,
                "dish_name": dish.name,
                "quantity": s.quantity,
                "image_path": image_path
            })

        result.append({
            "day_id": day.id,
            "date": day.date.isoformat(),
            "total_waste": day.total_waste,
            "servings": servings_list
        })

    return jsonify(result)


# ==========================================================
# API: Query specific day's dish serving status
# ==========================================================
@app.route("/day/<date_str>")
def day_detail(date_str):
    """
    Query dish serving status for specific date
    URL: /day/2025-11-14
    Return format:
    {
        "day_id": 1,
        "date": "2025-11-14",
        "total_waste": 2.3,
        "servings": [
            {
                "dish_id": 1,
                "dish_name": "示例菜品",
                "quantity": 12.5
            },
            ...
        ]
    }
    """
    from datetime import datetime
    try:
        query_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    day = Day.query.filter_by(date=query_date).first()
    if not day:
        return jsonify({"error": f"No data found for date {date_str}"}), 404

    servings = Serving.query.filter_by(day_id=day.id).all()
    servings_list = []
    for s in servings:
        dish = Dish.query.get(s.dish_id)
        servings_list.append({
            "dish_id": s.dish_id,
            "dish_name": dish.name,
            "quantity": s.quantity
        })

    result = {
        "day_id": day.id,
        "date": day.date.isoformat(),
        "total_waste": day.total_waste,
        "servings": servings_list
    }

    return jsonify(result)


@app.route("/")
def index():
    return "Cafeteria Waste Optimization API running!"


# ==========================================================
# API: Add new day's data (auto-recognize new dishes)
# ==========================================================
@app.route("/add_day", methods=["POST"])
def add_day():
    """
    Add new day's dish serving status and total waste amount
    Request format (JSON):
    {
        "date": "2025-11-15",
        "total_waste": 3.5,
        "servings": [
            {
                "dish_name": "红烧肉",
                "quantity": 15.0,
                "category": "protein",  // Optional field: 'staple', 'vegetable', 'protein', 'dairy'
                "image_path": "/images/红烧肉.jpg"  // Optional field
            },
            {
                "dish_name": "青菜",
                "quantity": 8.5,
                "category": "vegetable",
                "image_path": "/images/青菜.png"
            },
            {
                "dish_name": "新菜品",
                "quantity": 12.0,
                "category": "staple"
                // If image_path not provided, system will auto-generate
            }
        ]
    }
    
    Return format:
    {
        "success": true,
        "message": "Day added successfully",
        "day_id": 2,
        "date": "2025-11-15",
        "new_dishes": ["新菜品"],
        "servings_count": 3
    }
    """
    data = request.get_json()
    print(f"DEBUG: Received data: {data}")
    print(f"DEBUG: Data type: {type(data)}")
    
    # 验证必要字段
    if not data or "date" not in data or "total_waste" not in data or "servings" not in data:
        print(f"DEBUG: Missing fields check - data: {data}")
        return jsonify({"error": "Missing required fields: date, total_waste, servings"}), 400
    
    try:
        query_date = datetime.strptime(data["date"], "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
    
    # Check if this date already exists
    existing_day = Day.query.filter_by(date=query_date).first()
    if existing_day:
        return jsonify({"error": f"Data for date {data['date']} already exists"}), 409
    
    try:
        # Create new Day record
        day = Day(date=query_date, total_waste=data["total_waste"])
        db.session.add(day)
        db.session.flush()  # Get day_id but don't commit
        
        new_dishes_names = []
        servings_count = 0
        
        # Process each dish and serving quantity
        for serving_data in data["servings"]:
            dish_name = serving_data.get("dish_name")
            quantity = serving_data.get("quantity")
            image_path = serving_data.get("image_path")  # Optional field
            category = serving_data.get("category")  # Optional field: category info
            
            if not dish_name or quantity is None:
                db.session.rollback()
                return jsonify({"error": "Each serving must have 'dish_name' and 'quantity'"}), 400
            
            # Validate category if provided
            valid_categories = ['staple', 'vegetable', 'protein', 'dairy']
            if category and category not in valid_categories:
                db.session.rollback()
                return jsonify({
                    "error": f"Invalid category '{category}'. Valid categories are: {valid_categories}"
                }), 400
            
            # Query or create dish
            dish = Dish.query.filter_by(name=dish_name).first()
            if not dish:
                # Generate default path if image_path not provided
                if not image_path:
                    image_path = f"/images/{dish_name}.png"
                
                dish = Dish(name=dish_name, image_path=image_path, category=category)
                db.session.add(dish)
                db.session.flush()  # Get dish_id
                new_dishes_names.append(dish_name)
            else:
                # If dish exists, update related fields (if new values provided)
                if image_path and dish.image_path != image_path:
                    dish.image_path = image_path
                if category and dish.category != category:
                    dish.category = category
            
            # Create serving record
            serving = Serving(day_id=day.id, dish_id=dish.id, quantity=quantity)
            db.session.add(serving)
            servings_count += 1
        
        # Commit all changes
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Day added successfully",
            "day_id": day.id,
            "date": day.date.isoformat(),
            "new_dishes": new_dishes_names,
            "servings_count": servings_count
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to add day: {str(e)}"}), 500


# ==========================================================
# API: Get dish ID, name and waste rate for all foods
# ==========================================================
@app.route("/dishes_waste_rates")
def get_dishes_waste_rates():
    """
    Get dish ID, name and waste rate for all foods, supports sorting
    
    Query parameters:
        sort: Sort order, 'asc' (ascending) or 'desc' (descending), default is 'asc'
        order_by: Sort field, 'waste_rate' (by waste rate) or 'name' (by name), default is 'waste_rate'
    
    Return format (JSON):
    {
        "dishes": [
            {
                "id": 1,
                "name": "红烧肉",
                "waste_rate": 0.25,
                "image_path": "/images/红烧肉.jpg"
            },
            {
                "id": 2, 
                "name": "青椒炒蛋",
                "waste_rate": 0.15,
                "image_path": "/images/青椒炒蛋.jpg"
            }
        ],
        "total_count": 2,
        "sort_order": "asc",
        "order_by": "waste_rate"
    }
    """
    try:
        # Get query parameters
        sort_order = request.args.get('sort', 'asc').lower()
        order_by = request.args.get('order_by', 'waste_rate').lower()
        
        # Validate parameters
        if sort_order not in ['asc', 'desc']:
            return jsonify({"error": "Invalid sort parameter. Use 'asc' or 'desc'"}), 400
        
        if order_by not in ['waste_rate', 'name']:
            return jsonify({"error": "Invalid order_by parameter. Use 'waste_rate' or 'name'"}), 400
        
        # First calculate waste rates
        try:
            dishes, waste_rates = compute_waste_rates()
            
            # Build waste rate dictionary
            waste_rates_dict = {}
            for dish, rate in zip(dishes, waste_rates):
                waste_rates_dict[dish.name] = rate
        except Exception as e:
            return jsonify({"error": f"Failed to compute waste rates: {str(e)}"}), 500
        
        # Get all dishes
        dishes = Dish.query.all()
        
        # Build result list
        dishes_data = []
        for dish in dishes:
            waste_rate = waste_rates_dict.get(dish.name, 0.0)  # Default to 0 if no waste rate calculated
            # Prefer stored image path in database, generate default if none
            image_path = dish.image_path if dish.image_path else f"/images/{dish.name}.png"
            
            dishes_data.append({
                "id": dish.id,
                "name": dish.name,
                "waste_rate": round(waste_rate, 4),  # Keep 4 decimal places
                "image_path": image_path
            })
        
        # Sort
        if order_by == 'waste_rate':
            dishes_data.sort(key=lambda x: x['waste_rate'], reverse=(sort_order == 'desc'))
        else:  # order_by == 'name'
            dishes_data.sort(key=lambda x: x['name'], reverse=(sort_order == 'desc'))
        
        result = {
            "dishes": dishes_data,
            "total_count": len(dishes_data),
            "sort_order": sort_order,
            "order_by": order_by
        }
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": f"Failed to get dishes waste rates: {str(e)}"}), 500


# ==========================================================
# API: Predict impact of adjusting dish serving quantity on total waste
# ==========================================================
@app.route("/predict_waste_impact", methods=["POST"])
def predict_waste_impact():
    """
    Predict impact on total waste amount and rate after adjusting serving quantity of a dish (average of all historical data)
    
    Request format (JSON):
    {
        "dish_name": "红烧肉",
        "adjustment_percentage": 80  // Adjust to 80% of original serving quantity
    }
    
    Return format (JSON):
    {
        "dish_name": "红烧肉",
        "adjustment_percentage": 80,
        "current_waste_rate": 0.25,
        "analysis": {
            "total_days_analyzed": 5,
            "average_original": {
                "dish_serving": 15.0,
                "total_waste": 5.2,
                "total_serving": 45.0,
                "waste_rate": 0.1156
            },
            "average_predicted": {
                "dish_serving": 12.0,
                "total_waste": 4.45,
                "total_serving": 42.0,
                "waste_rate": 0.1060
            },
            "daily_average_changes": {
                "daily_waste_reduction": 0.75,
                "daily_waste_rate_reduction": 0.0096,
                "daily_serving_reduction": 3.0
            }
        }
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or "dish_name" not in data or "adjustment_percentage" not in data:
            return jsonify({"error": "Missing required fields: dish_name, adjustment_percentage"}), 400
        
        dish_name = data["dish_name"]
        adjustment_percentage = data["adjustment_percentage"]
        
        # Validate adjustment percentage range
        if not isinstance(adjustment_percentage, (int, float)) or adjustment_percentage < 0 or adjustment_percentage > 200:
            return jsonify({"error": "adjustment_percentage must be between 0 and 200"}), 400
        
        # Find dish
        dish = Dish.query.filter_by(name=dish_name).first()
        if not dish:
            return jsonify({"error": f"Dish '{dish_name}' not found"}), 404
        
        # Get current waste rate
        try:
            dishes, waste_rates = compute_waste_rates()
            dish_waste_rate = None
            for d, rate in zip(dishes, waste_rates):
                if d.id == dish.id:
                    dish_waste_rate = rate
                    break
            
            if dish_waste_rate is None:
                return jsonify({"error": f"Could not compute waste rate for dish '{dish_name}'"}), 500
        except Exception as e:
            return jsonify({"error": f"Failed to compute current waste rates: {str(e)}"}), 500
        
        # Get all historical dates
        days = Day.query.order_by(Day.date).all()
        
        # Statistical variables
        total_original_dish_serving = 0
        total_original_waste = 0
        total_original_serving = 0
        total_predicted_dish_serving = 0
        total_predicted_waste = 0
        total_predicted_serving = 0
        valid_days = 0
        
        adjustment_factor = adjustment_percentage / 100.0
        
        # Calculate for each day and accumulate
        for day in days:
            # Get dish serving status for this day
            servings = Serving.query.filter_by(day_id=day.id).all()
            
            # Find target dish serving quantity
            target_serving = None
            day_total_serving = 0
            for serving in servings:
                day_total_serving += serving.quantity
                if serving.dish_id == dish.id:
                    target_serving = serving
            
            # Skip if target dish was not served on this day
            if not target_serving:
                continue
            
            valid_days += 1
            
            # Accumulate original data
            original_dish_serving = target_serving.quantity
            original_total_waste = day.total_waste
            original_total_serving = day_total_serving
            
            total_original_dish_serving += original_dish_serving
            total_original_waste += original_total_waste
            total_original_serving += original_total_serving
            
            # Calculate adjusted data and accumulate
            predicted_dish_serving = original_dish_serving * adjustment_factor
            
            # Predict waste change: original serving waste - new serving waste
            original_dish_waste = original_dish_serving * dish_waste_rate
            predicted_dish_waste = predicted_dish_serving * dish_waste_rate
            waste_change = predicted_dish_waste - original_dish_waste
            
            predicted_total_waste = original_total_waste + waste_change
            predicted_total_serving = original_total_serving - original_dish_serving + predicted_dish_serving
            
            total_predicted_dish_serving += predicted_dish_serving
            total_predicted_waste += predicted_total_waste
            total_predicted_serving += predicted_total_serving
        
        if valid_days == 0:
            return jsonify({"error": f"No serving data found for dish '{dish_name}' in any historical records"}), 404
        
        # Calculate averages
        avg_original_dish_serving = total_original_dish_serving / valid_days
        avg_original_waste = total_original_waste / valid_days
        avg_original_serving = total_original_serving / valid_days
        avg_original_waste_rate = avg_original_waste / avg_original_serving if avg_original_serving > 0 else 0
        
        avg_predicted_dish_serving = total_predicted_dish_serving / valid_days
        avg_predicted_waste = total_predicted_waste / valid_days
        avg_predicted_serving = total_predicted_serving / valid_days
        avg_predicted_waste_rate = avg_predicted_waste / avg_predicted_serving if avg_predicted_serving > 0 else 0
        
        # Calculate average change amounts
        avg_waste_reduction = avg_original_waste - avg_predicted_waste
        avg_waste_rate_reduction = avg_original_waste_rate - avg_predicted_waste_rate
        avg_serving_reduction = avg_original_serving - avg_predicted_serving
        
        result = {
            "dish_name": dish_name,
            "adjustment_percentage": adjustment_percentage,
            "current_waste_rate": round(float(dish_waste_rate), 4),
            "analysis": {
                "total_days_analyzed": valid_days,
                "average_original": {
                    "dish_serving": round(avg_original_dish_serving, 2),
                    "total_waste": round(avg_original_waste, 2),
                    "total_serving": round(avg_original_serving, 2),
                    "waste_rate": round(avg_original_waste_rate, 4)
                },
                "average_predicted": {
                    "dish_serving": round(avg_predicted_dish_serving, 2),
                    "total_waste": round(avg_predicted_waste, 2),
                    "total_serving": round(avg_predicted_serving, 2),
                    "waste_rate": round(avg_predicted_waste_rate, 4)
                },
                "daily_average_changes": {
                    "daily_waste_reduction": round(avg_waste_reduction, 2),
                    "daily_waste_rate_reduction": round(avg_waste_rate_reduction, 4),
                    "daily_serving_reduction": round(avg_serving_reduction, 2)
                }
            }
        }
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": f"Failed to predict waste impact: {str(e)}"}), 500


# ==========================================================
# API: Get dish with highest serving quantity for a specific day
# ==========================================================
@app.route("/day/<date_str>/top_dish")
def get_top_dish_by_date(date_str):
    """
    Get dish with highest serving quantity for a specific day
    
    URL: /day/2025-11-15/top_dish
    
    Return format (JSON):
    {
        "date": "2025-11-15",
        "top_dish": {
            "dish_id": 1,
            "dish_name": "红烧肉",
            "quantity": 25.5,
            "image_path": "/images/红烧肉.png"
        },
        "total_dishes": 5,
        "total_serving": 68.2
    }
    """
    try:
        # Validate date format
        try:
            query_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
        
        # Find data for this date
        day = Day.query.filter_by(date=query_date).first()
        if not day:
            return jsonify({"error": f"No data found for date {date_str}"}), 404
        
        # Get all dish serving data for this day
        servings = Serving.query.filter_by(day_id=day.id).all()
        if not servings:
            return jsonify({"error": f"No serving data found for date {date_str}"}), 404
        
        # Find dish with highest serving quantity
        max_serving = max(servings, key=lambda x: x.quantity)
        top_dish = Dish.query.get(max_serving.dish_id)
        
        # Calculate statistics
        total_dishes = len(servings)
        total_serving = sum(serving.quantity for serving in servings)
        
        # Prefer stored image path in database, generate default if none
        image_path = top_dish.image_path if top_dish.image_path else f"/images/{top_dish.name}.png"
        
        result = {
            "date": day.date.isoformat(),
            "top_dish": {
                "dish_id": top_dish.id,
                "dish_name": top_dish.name,
                "quantity": round(max_serving.quantity, 2),
                "image_path": image_path
            },
            "total_dishes": total_dishes,
            "total_serving": round(total_serving, 2)
        }
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": f"Failed to get top dish: {str(e)}"}), 500


# ==========================================================
# API: Menu optimization planning
# ==========================================================
@app.route("/optimize_menu", methods=["POST"])
def optimize_menu():
    """
    Use linear programming to optimize daily dish serving quantities, objective is to minimize waste rate
    
    Request format (JSON):
    {
        "total_quantity_range": [80, 120],          // Total serving quantity range (kg) - required
        "num_dishes": 3,                            // Number of dishes to select from candidates - required
        "dish_constraints": {                       // Serving quantity constraints for all dishes in candidate pool - required
            "1": {"min": 10, "max": 30},           // Dish 1 constraints
            "2": {"min": 15, "max": 25},           // Dish 2 constraints
            "3": {"min": 12, "max": 28},           // Dish 3 constraints
            "4": {"min": 8, "max": 20},            // Dish 4 constraints
            "5": {"min": 18, "max": 35}            // Dish 5 constraints
        },
        "category_requirements": {                  // Optional category requirements
            "require_staple": true,                 // Whether staple food is required
            "require_vegetable": true,              // Whether vegetable is required
            "require_protein": false,               // Whether protein is required
            "require_dairy": false                  // Whether dairy is required
        },
        "available_dishes": [1, 2, 3, 4, 5]       // Candidate dish ID list, optional (default all dishes)
    }
    
    Description:
    - available_dishes=[1,2,3,4,5] defines candidate dish pool (5 dishes)
    - dish_constraints must define constraints for all 5 dishes
    - num_dishes=3 means select 3 dishes from these 5 dishes
    - Algorithm enumerates all C(5,3)=10 combinations, optimizes each with linear programming
    - Finally returns optimal solution with lowest waste rate
    
    Return format (JSON):
    {
        "success": true,
        "optimization_result": {
            "selected_dishes": [
                {
                    "dish_id": 1,
                    "dish_name": "菜品1",
                    "category": "protein", 
                    "quantity": 15.5,
                    "predicted_waste": 3.1,
                    "image_path": "/images/1.png"
                }
            ],
            "total_quantity": 67.5,
            "total_predicted_waste": 8.2,
            "waste_rate": 0.121,
            "optimization_status": "optimal"
        }
    }
    """
    try:
        from scipy.optimize import linprog
        from itertools import combinations
        
        data = request.get_json()
        
        # Validate required fields
        if not data:
            return jsonify({"error": "Missing request body"}), 400
        
        if "total_quantity_range" not in data:
            return jsonify({"error": "Missing required field: total_quantity_range"}), 400
        
        if "num_dishes" not in data:
            return jsonify({"error": "Missing required field: num_dishes"}), 400
            
        if "dish_constraints" not in data:
            return jsonify({"error": "Missing required field: dish_constraints"}), 400
        
        total_qty_min, total_qty_max = data["total_quantity_range"]
        num_dishes = data["num_dishes"]
        dish_constraints = data["dish_constraints"]
        category_requirements = data.get("category_requirements", {})
        available_dish_ids = data.get("available_dishes", None)
        
        # Validate parameter reasonableness
        if total_qty_min >= total_qty_max:
            return jsonify({"error": "Invalid total_quantity_range: min must be less than max"}), 400
        
        if num_dishes <= 0:
            return jsonify({"error": "num_dishes must be positive"}), 400
        
        if not dish_constraints:
            return jsonify({"error": "dish_constraints cannot be empty"}), 400
        
        # Get waste rate data
        try:
            dishes, waste_rates = compute_waste_rates()
        except Exception as e:
            return jsonify({"error": f"Failed to compute waste rates: {str(e)}"}), 500
        
        # Build candidate dish pool
        if available_dish_ids:
            # Use specified dish ID list
            candidate_dishes = []
            candidate_waste_rates = []
            
            for dish_id in available_dish_ids:
                # Find corresponding dish object
                dish_obj = None
                dish_waste_rate = None
                for i, dish in enumerate(dishes):
                    if dish.id == dish_id:
                        dish_obj = dish
                        dish_waste_rate = waste_rates[i]
                        break
                
                if dish_obj is None:
                    return jsonify({"error": f"Dish with ID {dish_id} not found"}), 400
                
                candidate_dishes.append(dish_obj)
                candidate_waste_rates.append(dish_waste_rate)
        else:
            # Use all dishes as candidates
            candidate_dishes = dishes
            candidate_waste_rates = waste_rates
        
        # Validate constraint definitions: each dish in candidate pool must be defined in dish_constraints
        missing_constraints = []
        invalid_constraints = []
        
        for dish in candidate_dishes:
            dish_id_str = str(dish.id)
            if dish_id_str not in dish_constraints:
                missing_constraints.append(dish_id_str)
            else:
                constraint = dish_constraints[dish_id_str]
                if "min" not in constraint or "max" not in constraint:
                    invalid_constraints.append(f"Dish {dish_id_str} missing min or max constraint")
                elif constraint["min"] >= constraint["max"]:
                    invalid_constraints.append(f"Dish {dish_id_str} invalid constraint: min must be less than max")
        
        if missing_constraints:
            return jsonify({
                "error": f"Missing dish_constraints for candidate dishes: {missing_constraints}. "
                        f"All candidate dishes must have constraints defined."
            }), 400
        
        if invalid_constraints:
            return jsonify({"error": f"Invalid constraints: {invalid_constraints}"}), 400
        
        # Check if candidate dish count is sufficient
        if len(candidate_dishes) < num_dishes:
            return jsonify({
                "error": f"Not enough candidate dishes. Need {num_dishes}, have {len(candidate_dishes)} candidate dishes"
            }), 400
        
        # Function to check category requirements
        def check_category_requirements_func(dishes_list):
            if not category_requirements:
                return True
            
            categories_present = set(dish.category for dish in dishes_list if dish.category)
            
            if category_requirements.get("require_staple", False) and "staple" not in categories_present:
                return False
            if category_requirements.get("require_vegetable", False) and "vegetable" not in categories_present:
                return False
            if category_requirements.get("require_protein", False) and "protein" not in categories_present:
                return False
            if category_requirements.get("require_dairy", False) and "dairy" not in categories_present:
                return False
            
            return True
        
        # Enumerate all possible dish combinations (select from candidate dishes)
        best_solution = None
        best_waste_rate = float('inf')
        best_combination = None
        
        # Try all possible dish combinations
        for dish_combination in combinations(candidate_dishes, num_dishes):
            # Check category requirements
            if not check_category_requirements_func(dish_combination):
                continue
            
            # Set up linear programming for current combination
            n_selected = len(dish_combination)
            selected_waste_rates = []
            
            for dish in dish_combination:
                # Find corresponding waste rate
                dish_idx = candidate_dishes.index(dish)
                selected_waste_rates.append(candidate_waste_rates[dish_idx])
            
            # Linear programming setup
            # Objective function: minimize total waste amount
            c = selected_waste_rates
            
            # Inequality constraints A_ub * x <= b_ub
            A_ub = []
            b_ub = []
            
            # Maximum quantity constraint for each dish
            for i, dish in enumerate(dish_combination):
                dish_id_str = str(dish.id)
                constraint = dish_constraints[dish_id_str]
                max_qty = constraint["max"]
                
                constraint_row = [0] * n_selected
                constraint_row[i] = 1
                A_ub.append(constraint_row)
                b_ub.append(max_qty)
            
            # Total quantity upper bound constraint
            A_ub.append([1] * n_selected)
            b_ub.append(total_qty_max)
            
            # Total quantity lower bound constraint (convert to inequality)
            A_ub.append([-1] * n_selected)
            b_ub.append(-total_qty_min)
            
            # Variable bounds (lower bound, upper bound)
            bounds = []
            for dish in dish_combination:
                dish_id_str = str(dish.id)
                constraint = dish_constraints[dish_id_str]
                min_qty = constraint["min"]
                bounds.append((min_qty, None))  # Upper bound handled by inequality constraints
            
            # Solve linear programming
            try:
                result = linprog(
                    c=c,
                    A_ub=A_ub,
                    b_ub=b_ub,
                    bounds=bounds,
                    method='highs'
                )
                
                if result.success and result.x is not None:
                    quantities = result.x
                    total_quantity = sum(quantities)
                    
                    # Validate if solution satisfies all constraints
                    valid_solution = True
                    
                    # Check total quantity constraints
                    if total_quantity < total_qty_min or total_quantity > total_qty_max:
                        valid_solution = False
                    
                    # Check constraints for each dish
                    for i, dish in enumerate(dish_combination):
                        dish_id_str = str(dish.id)
                        constraint = dish_constraints[dish_id_str]
                        if quantities[i] < constraint["min"] or quantities[i] > constraint["max"]:
                            valid_solution = False
                            break
                    
                    if valid_solution:
                        total_waste = sum(quantities[i] * selected_waste_rates[i] for i in range(n_selected))
                        waste_rate = total_waste / total_quantity if total_quantity > 0 else 0
                        
                        if waste_rate < best_waste_rate:
                            best_waste_rate = waste_rate
                            best_combination = dish_combination
                            best_solution = {
                                "quantities": quantities,
                                "total_quantity": total_quantity,
                                "total_waste": total_waste,
                                "waste_rate": waste_rate,
                                "status": result.message
                            }
                            
            except Exception as e:
                # This combination has no solution, continue to next one
                continue
        
        if best_solution is None:
            return jsonify({"error": "No valid solution found. Constraints may be too restrictive."}), 400
        
        # Build response
        selected_dishes_result = []
        for i, dish in enumerate(best_combination):
            dish_idx = candidate_dishes.index(dish)
            image_path = dish.image_path if dish.image_path else f"/images/{dish.name}.png"
            selected_dishes_result.append({
                "dish_id": dish.id,
                "dish_name": dish.name,
                "category": dish.category or "unknown",
                "quantity": round(best_solution["quantities"][i], 2),
                "predicted_waste": round(best_solution["quantities"][i] * candidate_waste_rates[dish_idx], 2),
                "image_path": image_path
            })
        
        result = {
            "success": True,
            "optimization_result": {
                "selected_dishes": selected_dishes_result,
                "total_quantity": round(best_solution["total_quantity"], 2),
                "total_predicted_waste": round(best_solution["total_waste"], 2),
                "waste_rate": round(best_solution["waste_rate"], 4),
                "optimization_status": "optimal"
            }
        }
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": f"Failed to optimize menu: {str(e)}"}), 500


# ==========================================================
# Main program entry
# ==========================================================
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5001)
