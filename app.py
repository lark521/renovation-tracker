#!/usr/bin/env python3
"""Flask application for Renovation Expense Tracker."""
import os
import secrets
from flask import Flask, render_template, session, request, redirect, jsonify
from functools import wraps
from models import db, KanbanCategory
import secrets


def _load_env_var(key, app_dir):
    """Load a variable from environment or .env file."""
    val = os.environ.get(key)
    if val:
        return val
    env_path = os.path.join(app_dir, ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if line.startswith(f"{key}="):
                    return line.split("=", 1)[1].strip()
    return None


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///renovation.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
    
    # Load secret key from .env file (persisted across restarts)
    secret_key = _load_env_var("SECRET_KEY", APP_DIR)
    if not secret_key:
        secret_key = secrets.token_hex(32)
        with open(os.path.join(APP_DIR, ".env"), "a") as f:
            f.write(f"SECRET_KEY={secret_key}\n")
    
    app.config["SECRET_KEY"] = secret_key
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB
    
    # Initialize SQLAlchemy with app
    db.init_app(app)
    
    # Initialize database once at app creation time
    with app.app_context():
        db.create_all()
        # Seed default categories
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
    
    from api import api
    app.register_blueprint(api)
    
    # ==================== 登录验证 ====================
    
    @app.route("/")
    def index():
        if not session.get("logged_in"):
            return render_template("login.html")
        return render_template("index.html")
    
    @app.route("/api/auth/login", methods=["POST"])
    def auth_login():
        data = request.get_json()
        if not data:
            return jsonify({"error": "请提供用户名和密码"}), 400
        
        username = data.get("username", "").strip()
        password = data.get("password", "").strip()
        
        # Load credentials from .env file (not hardcoded)
        cred_user = _load_env_var("AUTH_USER", APP_DIR)
        cred_pass = _load_env_var("AUTH_PASS", APP_DIR)
        
        if not cred_user or not cred_pass:
            return jsonify({"error": "系统配置错误：未在.env中找到认证信息"}), 500
        
        if username == cred_user and password == cred_pass:
            session["logged_in"] = True
            session["username"] = username
            return jsonify({"message": "登录成功"})
        
        return jsonify({"error": "用户名或密码错误"}), 401
    
    @app.route("/api/auth/logout", methods=["POST"])
    def auth_logout():
        session.clear()
        return jsonify({"message": "已退出登录"})
    
    @app.route("/api/auth/check", methods=["GET"])
    def auth_check():
        return jsonify({"logged_in": session.get("logged_in", False)})
    
    @app.route("/favicon.ico")
    def favicon():
        return "", 204
    
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=8671, debug=True)
