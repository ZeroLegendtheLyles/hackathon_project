from flask_sqlalchemy import SQLAlchemy
from datetime import date

db= SQLAlchemy()

# ========== 1. 菜品表 ==========
class Dish(db.Model):
    __tablename__ = "dishes"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)

    # 一个菜品，可能对应多个 Serving（日投放记录）
    servings = db.relationship("Serving", backref="dish", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name
        }


# ========== 2. 每天的数据 ==========
class Day(db.Model):
    __tablename__ = "days"

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, unique=True, default=date.today)

    # 当天的总厨余垃圾重量（一对一）
    total_waste = db.Column(db.Float, nullable=False)

    # 一天有多个 Serving
    servings = db.relationship("Serving", backref="day", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date.isoformat(),
            "total_waste": self.total_waste
        }


# ========== 3. 每天每个菜品的投放量 ==========
class Serving(db.Model):
    __tablename__ = "servings"

    id = db.Column(db.Integer, primary_key=True)

    # 多对一 → Day
    day_id = db.Column(db.Integer, db.ForeignKey("days.id"), nullable=False)

    # 多对一 → Dish
    dish_id = db.Column(db.Integer, db.ForeignKey("dishes.id"), nullable=False)

    # 当天此菜品的投放数量
    quantity = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "day_id": self.day_id,
            "dish_id": self.dish_id,
            "quantity": self.quantity
        }
