from flask import Flask, jsonify, request
import numpy as np
from datetime import datetime
import os
import json
from flask_cors import CORS

# ==========================================================
# 初始化 Flask 与 SQLAlchemy
# ==========================================================
app = Flask(__name__)
CORS(
    app,
    resources={r"/*": {"origins": "http://localhost:5173"}}
)
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
# API：预测调整菜品投放量对总浪费的影响
# ==========================================================
@app.route("/predict_waste_impact", methods=["POST"])
def predict_waste_impact():
    """
    预测调整某个菜品投放量后对总浪费量和总浪费率的影响（所有历史数据的平均值）
    
    请求格式 (JSON):
    {
        "dish_name": "红烧肉",
        "adjustment_percentage": 80  // 调整为原投放量的80%
    }
    
    返回格式 (JSON):
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
        
        # 验证必要字段
        if not data or "dish_name" not in data or "adjustment_percentage" not in data:
            return jsonify({"error": "Missing required fields: dish_name, adjustment_percentage"}), 400
        
        dish_name = data["dish_name"]
        adjustment_percentage = data["adjustment_percentage"]
        
        # 验证调整百分比范围
        if not isinstance(adjustment_percentage, (int, float)) or adjustment_percentage < 0 or adjustment_percentage > 200:
            return jsonify({"error": "adjustment_percentage must be between 0 and 200"}), 400
        
        # 查找菜品
        dish = Dish.query.filter_by(name=dish_name).first()
        if not dish:
            return jsonify({"error": f"Dish '{dish_name}' not found"}), 404
        
        # 获取当前浪费率
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
        
        # 获取所有历史日期
        days = Day.query.order_by(Day.date).all()
        
        # 统计变量
        total_original_dish_serving = 0
        total_original_waste = 0
        total_original_serving = 0
        total_predicted_dish_serving = 0
        total_predicted_waste = 0
        total_predicted_serving = 0
        valid_days = 0
        
        adjustment_factor = adjustment_percentage / 100.0
        
        # 对每一天进行计算并累加
        for day in days:
            # 获取该天的菜品投放情况
            servings = Serving.query.filter_by(day_id=day.id).all()
            
            # 找到目标菜品的投放量
            target_serving = None
            day_total_serving = 0
            for serving in servings:
                day_total_serving += serving.quantity
                if serving.dish_id == dish.id:
                    target_serving = serving
            
            # 如果该天没有投放目标菜品，跳过
            if not target_serving:
                continue
            
            valid_days += 1
            
            # 累加原始数据
            original_dish_serving = target_serving.quantity
            original_total_waste = day.total_waste
            original_total_serving = day_total_serving
            
            total_original_dish_serving += original_dish_serving
            total_original_waste += original_total_waste
            total_original_serving += original_total_serving
            
            # 计算调整后的数据并累加
            predicted_dish_serving = original_dish_serving * adjustment_factor
            
            # 预测浪费变化：原投放量产生的浪费 - 新投放量产生的浪费
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
        
        # 计算平均值
        avg_original_dish_serving = total_original_dish_serving / valid_days
        avg_original_waste = total_original_waste / valid_days
        avg_original_serving = total_original_serving / valid_days
        avg_original_waste_rate = avg_original_waste / avg_original_serving if avg_original_serving > 0 else 0
        
        avg_predicted_dish_serving = total_predicted_dish_serving / valid_days
        avg_predicted_waste = total_predicted_waste / valid_days
        avg_predicted_serving = total_predicted_serving / valid_days
        avg_predicted_waste_rate = avg_predicted_waste / avg_predicted_serving if avg_predicted_serving > 0 else 0
        
        # 计算平均变化量
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
# API：获取某一天投放量最多的菜品
# ==========================================================
@app.route("/day/<date_str>/top_dish")
def get_top_dish_by_date(date_str):
    """
    获取某一天投放量最多的菜品信息
    
    URL: /day/2025-11-15/top_dish
    
    返回格式 (JSON):
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
        # 验证日期格式
        try:
            query_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
        
        # 查找该日期的数据
        day = Day.query.filter_by(date=query_date).first()
        if not day:
            return jsonify({"error": f"No data found for date {date_str}"}), 404
        
        # 获取该天的所有菜品投放数据
        servings = Serving.query.filter_by(day_id=day.id).all()
        if not servings:
            return jsonify({"error": f"No serving data found for date {date_str}"}), 404
        
        # 找到投放量最多的菜品
        max_serving = max(servings, key=lambda x: x.quantity)
        top_dish = Dish.query.get(max_serving.dish_id)
        
        # 计算统计信息
        total_dishes = len(servings)
        total_serving = sum(serving.quantity for serving in servings)
        
        # 生成图片路径
        image_filename = f"{top_dish.name}.png"
        image_path = f"/images/{image_filename}"
        
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
# 主程序入口
# ==========================================================
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
