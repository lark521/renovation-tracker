#!/usr/bin/env python3
"""Database models for Renovation Expense Tracker."""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
import sqlalchemy

db = SQLAlchemy()

class Expense(db.Model):
    """装修支出记录"""
    __tablename__ = "expenses"
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), nullable=False, default="待定")
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text, default="")
    status = db.Column(db.String(20), default="进行中")
    priority = db.Column(db.String(20), default="中")
    area = db.Column(db.String(50), default="全屋")  # 区域
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category,
            "amount": self.amount,
            "date": self.date,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "area": self.area,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else "",
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S") if self.updated_at else "",
        }


class KanbanCategory(db.Model):
    """看板分类配置"""
    __tablename__ = "kanban_categories"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    color = db.Column(db.String(20), default="#3498db")
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "color": self.color,
            "sort_order": self.sort_order,
        }


class Budget(db.Model):
    """预算配置"""
    __tablename__ = "budgets"
    
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)
    total_budget = db.Column(db.Float, nullable=False, default=0)
    spent = db.Column(db.Float, nullable=False, default=0)
    
    @property
    def remaining(self):
        return self.total_budget - self.spent
    
    @property
    def usage_rate(self):
        if self.total_budget == 0:
            return 0
        return min(self.spent / self.total_budget * 100, 200)
    
    def to_dict(self):
        return {
            "id": self.id,
            "category": self.category,
            "total_budget": self.total_budget,
            "spent": self.spent,
            "remaining": self.remaining,
            "usage_rate": round(self.usage_rate, 1),
        }


def init_db(app):
    """初始化数据库并创建默认分类"""
    db.init_app(app)
    with app.app_context():
        db.create_all()
        
        default_categories = [
            ("水电改造", "#e74c3c"),
            ("泥瓦工程", "#e67e22"),
            ("木工工程", "#f1c40f"),
            ("油漆工程", "#2ecc71"),
            ("瓷砖铺贴", "#1abc9c"),
            ("家具购置", "#3498db"),
            ("电器采购", "#9b59b6"),
            ("软装搭配", "#e91e63"),
            ("其他支出", "#7f8c8d"),
        ]
        
        for name, color in default_categories:
            if not KanbanCategory.query.filter_by(name=name).first():
                cat = KanbanCategory(name=name, color=color, sort_order=default_categories.index((name, color)))
                db.session.add(cat)
        
        db.session.commit()
        print("Database initialized with default categories.")
