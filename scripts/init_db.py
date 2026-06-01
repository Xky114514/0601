#!/usr/bin/env python
"""
数据库初始化脚本
用于创建数据库并导入种子数据
"""
import sqlite3
import os
import sys

def init_database():
    """初始化数据库"""
    # 获取数据目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(os.path.dirname(script_dir), 'data')

    db_path = os.path.join(data_dir, 'enterprise.db')
    schema_path = os.path.join(data_dir, 'schema.sql')
    seed_path = os.path.join(data_dir, 'seed_data.sql')

    print("=" * 50)
    print("企业智能问答助手 - 数据库初始化")
    print("=" * 50)
    print()

    # 删除旧数据库
    if os.path.exists(db_path):
        os.remove(db_path)
        print("[OK] 清理旧数据库")

    # 创建新数据库
    conn = sqlite3.connect(db_path)

    # 执行 schema
    with open(schema_path, 'r', encoding='utf-8') as f:
        conn.executescript(f.read())
    print("[OK] 创建表结构")

    # 执行 seed data
    with open(seed_path, 'r', encoding='utf-8') as f:
        conn.executescript(f.read())
    print("[OK] 导入种子数据")

    conn.commit()

    # 验证数据
    print()
    print("=" * 50)
    print("数据验证")
    print("=" * 50)

    cursor = conn.cursor()

    # 员工数
    cursor.execute('SELECT COUNT(*) FROM employees')
    print(f"  员工数: {cursor.fetchone()[0]}")

    # 项目数
    cursor.execute('SELECT COUNT(*) FROM projects')
    print(f"  项目数: {cursor.fetchone()[0]}")

    # 考勤记录
    cursor.execute('SELECT COUNT(*) FROM attendance')
    print(f"  考勤记录: {cursor.fetchone()[0]}")

    # 绩效记录
    cursor.execute('SELECT COUNT(*) FROM performance_reviews')
    print(f"  绩效记录: {cursor.fetchone()[0]}")

    conn.close()

    print()
    print("[OK] 数据库初始化完成: " + db_path)
    print("=" * 50)

if __name__ == "__main__":
    init_database()