from flask import Flask, jsonify, request
import numpy as np
from datetime import datetime
import os
import json

# ==========================================================
# 初始化 Flask 与 SQLAlchemy
# ==========================================================
app = Flask(__name__)
# 确保数据库总是使用 backend 目录下的 hackathon_project_test.db
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, "hackathon_project_test.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# 确保 JSON 响应显示中文而不是 Unicode 转义序列
app.config['JSON_AS_ASCII'] = False
app.json.ensure_ascii = False

# 使用 models.py 中的 db 实例（避免重复创建）
from models import db
db.init_app(app)

# ==========================================================
# 导入 models（放在 db 初始化之后）
# ==========================================================
from models import Dish, Day, Serving


# ==========================================================
# 核心计算函数：构建 P, M 并求解 W
# ==========================================================
def compute_waste_rates():
    """
    从数据库构建:
        P: (n_days × n_dishes) 投放量矩阵
        M: (n_days × 1) 当天总垃圾量
    最小二乘求解:
        P W = M
        W = 每个菜品的浪费率
    """
    # --------------------------------------------------
    # 1. 获取菜品列表并固定顺序
    # --------------------------------------------------
    dishes = Dish.query.order_by(Dish.id).all()
    dish_ids = [d.id for d in dishes]
    n_dishes = len(dishes)

    # --------------------------------------------------
    # 2. 获取所有日期
    # --------------------------------------------------
    days = Day.query.order_by(Day.id).all()
    n_days = len(days)

    # P: n_days × n_dishes
    P = np.zeros((n_days, n_dishes))
    M = np.zeros(n_days)

    # --------------------------------------------------
    # 3. 构建矩阵
    # --------------------------------------------------
    for i, day in enumerate(days):
        M[i] = day.total_waste

        # 该日的所有菜单记录
        servings = Serving.query.filter_by(day_id=day.id).all()

        for s in servings:
            j = dish_ids.index(s.dish_id)
            P[i, j] = s.quantity

    # --------------------------------------------------
    # 4. 最小二乘求解 W
    # --------------------------------------------------
    W, _, _, _ = np.linalg.lstsq(P, M, rcond=None)

    return dishes, W


# ==========================================================
# API：返回每个菜品的浪费率
# ==========================================================
@app.route("/compute_waste_rates")
def get_waste_rates():
    dishes, W = compute_waste_rates()

    result = []
    for dish, w in zip(dishes, W):
        result.append({
            "dish_id": dish.id,
            "dish_name": dish.name,
            "waste_rate": float(w)
        })

    return jsonify(result)


# ==========================================================
# API：查询每一天的菜品提供情况和浪费情况
# ==========================================================
@app.route("/days_overview")
def days_overview():
    """
    返回所有日期的菜品提供情况和浪费情况
    格式：
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
            servings_list.append({
                "dish_id": s.dish_id,
                "dish_name": dish.name,
                "quantity": s.quantity
            })

        result.append({
            "day_id": day.id,
            "date": day.date.isoformat(),
            "total_waste": day.total_waste,
            "servings": servings_list
        })

    return jsonify(result)


# ==========================================================
# API：查询特定一天的菜品提供情况
# ==========================================================
@app.route("/day/<date_str>")
def day_detail(date_str):
    """
    查询特定日期的菜品提供情况
    URL: /day/2025-11-14
    返回格式：
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
# API：添加新一天的数据（自动识别新菜品）
# ==========================================================
@app.route("/add_day", methods=["POST"])
def add_day():
    """
    添加新一天的菜品投放情况和浪费总量
    请求格式 (JSON):
    {
        "date": "2025-11-15",
        "total_waste": 3.5,
        "servings": [
            {
                "dish_name": "红烧肉",
                "quantity": 15.0
            },
            {
                "dish_name": "青菜",
                "quantity": 8.5
            },
            {
                "dish_name": "新菜品",
                "quantity": 12.0
            }
        ]
    }
    
    返回格式：
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
    
    # 检查该日期是否已存在
    existing_day = Day.query.filter_by(date=query_date).first()
    if existing_day:
        return jsonify({"error": f"Data for date {data['date']} already exists"}), 409
    
    try:
        # 创建新的 Day 记录
        day = Day(date=query_date, total_waste=data["total_waste"])
        db.session.add(day)
        db.session.flush()  # 获取 day_id，但不提交
        
        new_dishes_names = []
        servings_count = 0
        
        # 处理每个菜品和投放量
        for serving_data in data["servings"]:
            dish_name = serving_data.get("dish_name")
            quantity = serving_data.get("quantity")
            
            if not dish_name or quantity is None:
                db.session.rollback()
                return jsonify({"error": "Each serving must have 'dish_name' and 'quantity'"}), 400
            
            # 查询或创建菜品
            dish = Dish.query.filter_by(name=dish_name).first()
            if not dish:
                dish = Dish(name=dish_name)
                db.session.add(dish)
                db.session.flush()  # 获取 dish_id
                new_dishes_names.append(dish_name)
            
            # 创建投放记录
            serving = Serving(day_id=day.id, dish_id=dish.id, quantity=quantity)
            db.session.add(serving)
            servings_count += 1
        
        # 提交所有更改
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
# API：获取所有食物的编号名称和浪费率
# ==========================================================
@app.route("/dishes_waste_rates")
def get_dishes_waste_rates():
    """
    获取所有食物的编号名称和浪费率，支持排序
    
    查询参数:
        sort: 排序方式，'asc'（升序）或 'desc'（降序），默认为 'asc'
        order_by: 排序字段，'waste_rate'（按浪费率）或 'name'（按名称），默认为 'waste_rate'
    
    返回格式 (JSON):
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
        # 获取查询参数
        sort_order = request.args.get('sort', 'asc').lower()
        order_by = request.args.get('order_by', 'waste_rate').lower()
        
        # 验证参数
        if sort_order not in ['asc', 'desc']:
            return jsonify({"error": "Invalid sort parameter. Use 'asc' or 'desc'"}), 400
        
        if order_by not in ['waste_rate', 'name']:
            return jsonify({"error": "Invalid order_by parameter. Use 'waste_rate' or 'name'"}), 400
        
        # 先计算浪费率
        try:
            dishes, waste_rates = compute_waste_rates()
            
            # 构建浪费率字典
            waste_rates_dict = {}
            for dish, rate in zip(dishes, waste_rates):
                waste_rates_dict[dish.name] = rate
        except Exception as e:
            return jsonify({"error": f"Failed to compute waste rates: {str(e)}"}), 500
        
        # 获取所有菜品
        dishes = Dish.query.all()
        
        # 构建结果列表
        dishes_data = []
        for dish in dishes:
            waste_rate = waste_rates_dict.get(dish.name, 0.0)  # 如果没有计算出浪费率，默认为0
            # 生成图片路径：优先使用菜品名称，如果不存在则使用默认图片
            image_filename = f"{dish.name}.png"  # 可以根据需要调整扩展名
            image_path = f"/images/{image_filename}"
            
            dishes_data.append({
                "id": dish.id,
                "name": dish.name,
                "waste_rate": round(waste_rate, 4),  # 保留4位小数
                "image_path": image_path
            })
        
        # 排序
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
# 主程序入口
# ==========================================================
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
