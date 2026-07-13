#!/usr/bin/env python3
"""装修记账系统健康检查与自动修复脚本"""
import os
import sys
import subprocess
import sqlite3
import time
from datetime import datetime

APP_DIR = "/home/shaohua/renovation-tracker"
DB_PATH = "/home/shaohua/renovation-tracker/instance/renovation.db"
VENV_PYTHON = "/home/shaohua/.hermes/hermes-agent/venv/bin/python3"
PORT = 8671
LOG_FILE = "/tmp/renovation_monitor.log"

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def check_db_integrity():
    """检查数据库完整性，确保数据不丢失"""
    if not os.path.exists(DB_PATH):
        log(f"❌ 数据库文件不存在: {DB_PATH}")
        return False
    
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM expenses")
        count = c.fetchone()[0]
        c.execute("SELECT SUM(amount) FROM expenses")
        total = c.fetchone()[0] or 0
        conn.close()
        
        log(f"✅ 数据库完整性检查通过: {count} 条记录, 总额 ¥{total:,.2f}")
        return True
    except Exception as e:
        log(f"❌ 数据库检查失败: {e}")
        return False

def backup_db():
    """备份数据库"""
    import shutil
    backup_dir = "/home/shaohua/renovation-tracker/backups"
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_dir, f"renovation_{timestamp}.db")
    try:
        shutil.copy2(DB_PATH, backup_path)
        log(f"💾 数据库已备份到: {backup_path}")
        return backup_path
    except Exception as e:
        log(f"⚠️ 备份失败: {e}")
        return None

def check_service():
    """检查服务是否正常运行"""
    # 方法1: 检查进程
    result = subprocess.run(
        ["pgrep", "-f", "renovation-tracker/app.py"],
        capture_output=True, text=True
    )
    
    if result.returncode == 0:
        pids = result.stdout.strip().split("\n")
        log(f"✅ 服务进程存在: {pids}")
        return True, pids[0].strip()
    
    return False, None

def start_service():
    """启动服务"""
    try:
        # 先杀掉旧进程
        subprocess.run(["pkill", "-f", "renovation-tracker/app.py"], 
                      capture_output=True)
        time.sleep(1)
        
        # 用正确的venv启动
        cmd = [VENV_PYTHON, "/home/shaohua/renovation-tracker/app.py"]
        proc = subprocess.Popen(cmd, cwd=APP_DIR, 
                              stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL,
                              start_new_session=True)
        
        log(f"🚀 服务已启动, PID: {proc.pid}")
        time.sleep(3)
        
        # 验证启动成功
        result = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", 
             f"http://localhost:{PORT}/api/auth/check"],
            capture_output=True, text=True
        )
        
        if result.stdout == "200":
            log(f"✅ 服务启动成功, HTTP状态码: {result.stdout}")
            return True
        
        log(f"⚠️ 服务可能未完全启动, HTTP状态码: {result.stdout}")
        return False
    except Exception as e:
        log(f"❌ 启动服务失败: {e}")
        return False

def main():
    log("=" * 50)
    log("开始健康检查...")
    
    # 第1步: 检查数据库
    db_ok = check_db_integrity()
    
    # 第2步: 检查服务
    service_running, pid = check_service()
    
    if not service_running:
        log("⚠️ 服务未运行, 尝试重启...")
        # 先备份
        backup_db()
        # 重启服务
        success = start_service()
        if success:
            log("✅ 服务恢复成功!")
        else:
            log("❌ 服务恢复失败, 需要人工介入")
            sys.exit(1)
    else:
        # 服务正常, 但检查是否需要备份
        last_backup = None
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as f:
                for line in reversed(f.readlines()):
                    if "数据库已备份" in line:
                        last_backup = line.strip()
                        break
        
        # 每天备份一次
        if not last_backup:
            log("📅 首次运行, 执行初始备份")
            backup_db()
        elif "今天" not in last_backup:
            log("📅 执行每日备份")
            backup_db()
    
    log("✅ 健康检查完成")
    return 0

if __name__ == "__main__":
    sys.exit(main())
