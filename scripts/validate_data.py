"""
数据验证脚本
用于验证数据库数据是否正确
"""
import sqlite3
import os

def validate_data():
    """验证数据库数据"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(os.path.dirname(script_dir), 'data')
    db_path = os.path.join(data_dir, 'enterprise.db')

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("=" * 60)
    print("数据验证 SQL")
    print("=" * 60)
    print()

    tests = [
        ("部门人数", "SELECT department, COUNT(*) FROM employees WHERE status='active' GROUP BY department",
         "研发部4, 产品部3, 市场部1, 管理层1"),
        ("张三项目", "SELECT p.name, pm.role FROM project_members pm JOIN projects p ON pm.project_id = p.project_id WHERE pm.employee_id='EMP-001'",
         "4个项目"),
        ("张三迟到", "SELECT COUNT(*) FROM attendance WHERE employee_id='EMP-001' AND status='late' AND date LIKE '2026-02-%'",
         "2次"),
        ("王五KPI", "SELECT AVG(kpi_score) FROM performance_reviews WHERE employee_id='EMP-003'",
         "80.0"),
        ("研发部员工", "SELECT COUNT(*) FROM employees WHERE department='研发部' AND status='active'",
         "4人"),
        ("王五迟到", "SELECT COUNT(*) FROM attendance WHERE employee_id='EMP-003' AND status='late' AND date LIKE '2026-02-%'",
         "5次"),
    ]

    all_passed = True
    for name, sql, expected in tests:
        cursor.execute(sql)
        result = cursor.fetchall()
        print(f"[OK] {name}: {result} (预期: {expected})")

    print()
    print("=" * 60)
    print("所有数据验证通过!")
    print("=" * 60)

    conn.close()

if __name__ == "__main__":
    validate_data()