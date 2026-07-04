#!/usr/bin/env python3
"""Flask application for Renovation Expense Tracker."""
import os
import secrets
from flask import Flask, render_template, session, request, redirect, jsonify
from functools import wraps
from models import init_db

def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///renovation.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", secrets.token_hex(32))
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB
    
    init_db(app)
    
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
        
        # 验证凭据（硬编码，生产环境应使用数据库+密码哈希）
        VALID_USERNAME = "shaohua"
        VALID_PASSWORD = "Lsh@2026"
        
        if username == VALID_USERNAME and password == VALID_PASSWORD:
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
    
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=8671, debug=True)
