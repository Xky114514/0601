"""
数据库查询模块
使用参数化查询防止 SQL 注入
"""
import sqlite3
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass

# 支持相对导入和绝对导入
try:
    from .config import get_config
except ImportError:
    from config import get_config

from intent import DataSource, Intent


@dataclass
class QueryResult:
    """查询结果"""
    data: List[Dict[str, Any]]
    source: str  # 表名或数据源描述
    query: str   # 执行的查询（脱敏后）
    error: Optional[str] = None


class DatabaseQuery:
    """安全数据库查询器"""

    # 安全查询模板（参数化）
    SAFE_QUERY_TEMPLATES = {
        # 员工查询
        'employee_by_id': """
            SELECT employee_id, name, department, level, hire_date, manager_id, email, status
            FROM employees WHERE employee_id = ?
        """,
        'employee_by_name': """
            SELECT employee_id, name, department, level, hire_date, manager_id, email, status
            FROM employees WHERE name = ?
        """,
        'employee_manager': """
            SELECT e1.name as employee_name, e1.employee_id,
                   e2.name as manager_name, e2.employee_id as manager_id
            FROM employees e1
            LEFT JOIN employees e2 ON e1.manager_id = e2.employee_id
            WHERE e1.employee_id = ? OR e1.name = ?
        """,
        'employees_by_dept': """
            SELECT employee_id, name, department, level, hire_date, status
            FROM employees WHERE department = ? AND status = 'active'
            ORDER BY name
        """,
        'dept_count': """
            SELECT department, COUNT(*) as count
            FROM employees WHERE department = ? AND status = 'active'
        """,
        'employee_email': """
            SELECT employee_id, name, email FROM employees WHERE employee_id = ? OR name = ?
        """,

        # 项目查询
        'projects_by_lead': """
            SELECT p.project_id, p.name, p.status, p.start_date, p.end_date,
                   pm.role, e.name as lead_name
            FROM projects p
            JOIN project_members pm ON p.project_id = pm.project_id
            JOIN employees e ON p.lead_id = e.employee_id
            WHERE pm.employee_id = ?
            ORDER BY p.status, p.start_date DESC
        """,
        'project_members': """
            SELECT p.name as project_name, p.project_id, p.status,
                   pm.role, pm.join_date, e.name as member_name
            FROM project_members pm
            JOIN projects p ON pm.project_id = p.project_id
            JOIN employees e ON pm.employee_id = e.employee_id
            WHERE pm.employee_id = ?
            ORDER BY pm.join_date DESC
        """,
        'projects_by_status': """
            SELECT project_id, name, lead_id, status, start_date, end_date, budget
            FROM projects WHERE status = ?
        """,
        'active_projects': """
            SELECT p.project_id, p.name, p.status, e.name as lead_name
            FROM projects p
            JOIN employees e ON p.lead_id = e.employee_id
            WHERE p.status = 'active'
        """,
        'project_count_by_employee': """
            SELECT e.employee_id, e.name, COUNT(*) as project_count
            FROM project_members pm
            JOIN employees e ON pm.employee_id = e.employee_id
            WHERE e.status = 'active'
            GROUP BY e.employee_id
        """,

        # 考勤查询
        'attendance_by_employee_month': """
            SELECT date, status
            FROM attendance
            WHERE employee_id = ? AND date LIKE ?
            ORDER BY date
        """,
        'late_count_by_employee_month': """
            SELECT COUNT(*) as late_count
            FROM attendance
            WHERE employee_id = ? AND status = 'late' AND date LIKE ?
        """,
        'attendance_stats_by_employee': """
            SELECT
                COUNT(*) as total_days,
                SUM(CASE WHEN status = 'late' THEN 1 ELSE 0 END) as late_count,
                SUM(CASE WHEN status = 'absent' THEN 1 ELSE 0 END) as absent_count,
                SUM(CASE WHEN status = 'on_time' THEN 1 ELSE 0 END) as on_time_count
            FROM attendance
            WHERE employee_id = ? AND date LIKE ?
        """,

        # 绩效查询
        'performance_by_employee': """
            SELECT year, quarter, kpi_score, grade
            FROM performance_reviews
            WHERE employee_id = ?
            ORDER BY year, quarter
        """,
        'performance_avg_by_employee': """
            SELECT AVG(kpi_score) as avg_score, MIN(kpi_score) as min_score, MAX(kpi_score) as max_score
            FROM performance_reviews
            WHERE employee_id = ?
        """,
        'performance_by_employee_year': """
            SELECT year, quarter, kpi_score, grade
            FROM performance_reviews
            WHERE employee_id = ? AND year = ?
            ORDER BY quarter
        """,
        'performance_check_kpi': """
            SELECT kpi_score, grade, quarter, year
            FROM performance_reviews
            WHERE employee_id = ?
            ORDER BY year DESC, quarter DESC
            LIMIT 4
        """,

        # 晋升检查相关
        'employee_full_info': """
            SELECT e.employee_id, e.name, e.department, e.level, e.hire_date, e.status,
                   COUNT(pm.project_id) as project_count
            FROM employees e
            LEFT JOIN project_members pm ON e.employee_id = pm.employee_id
            WHERE e.employee_id = ? OR e.name = ?
            GROUP BY e.employee_id
        """,

        # 研发部查询
        'rd_employees': """
            SELECT employee_id, name, level, hire_date, status
            FROM employees
            WHERE department = '研发部' AND status = 'active'
            ORDER BY level, name
        """,
    }

    def __init__(self):
        self.config = get_config()
        self._conn: Optional[sqlite3.Connection] = None

    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        if self._conn is None:
            db_path = self.config.get_db_path()
            self._conn = sqlite3.connect(str(db_path))
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def close(self):
        """关闭数据库连接"""
        if self._conn:
            self._conn.close()
            self._conn = None

    def execute_safe_query(
        self,
        template_name: str,
        params: Tuple[Any, ...]
    ) -> QueryResult:
        """执行安全的参数化查询"""
        if template_name not in self.SAFE_QUERY_TEMPLATES:
            return QueryResult(
                data=[], source='unknown', query='',
                error=f'未知的查询模板: {template_name}'
            )

        query = self.SAFE_QUERY_TEMPLATES[template_name]

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)

            rows = cursor.fetchall()
            data = [dict(row) for row in rows]

            return QueryResult(
                data=data,
                source=template_name,
                query=f'{template_name} (params: {params})'
            )

        except sqlite3.Error as e:
            return QueryResult(
                data=[], source=template_name, query='',
                error=f'数据库错误: {str(e)}'
            )

    def query_employee_by_id(self, employee_id: str) -> QueryResult:
        """根据员工ID查询员工信息"""
        return self.execute_safe_query('employee_by_id', (employee_id,))

    def query_employee_by_name(self, name: str) -> QueryResult:
        """根据姓名查询员工信息"""
        return self.execute_safe_query('employee_by_name', (name,))

    def query_employee_manager(self, employee_id_or_name: str) -> QueryResult:
        """查询员工的上级"""
        return self.execute_safe_query('employee_manager', (employee_id_or_name, employee_id_or_name))

    def query_employees_by_dept(self, department: str) -> QueryResult:
        """查询部门员工"""
        return self.execute_safe_query('employees_by_dept', (department,))

    def query_dept_count(self, department: str) -> QueryResult:
        """查询部门人数"""
        return self.execute_safe_query('dept_count', (department,))

    def query_employee_email(self, employee_id_or_name: str) -> QueryResult:
        """查询员工邮箱"""
        return self.execute_safe_query('employee_email', (employee_id_or_name, employee_id_or_name))

    def query_projects_by_employee(self, employee_id: str) -> QueryResult:
        """查询员工参与的项目"""
        return self.execute_safe_query('project_members', (employee_id,))

    def query_late_count(self, employee_id: str, year: int, month: int) -> QueryResult:
        """查询迟到次数"""
        date_pattern = f'{year}-{month:02d}%'
        return self.execute_safe_query('late_count_by_employee_month', (employee_id, date_pattern))

    def query_performance(self, employee_id: str) -> QueryResult:
        """查询员工绩效"""
        return self.execute_safe_query('performance_by_employee', (employee_id,))

    def query_performance_avg(self, employee_id: str) -> QueryResult:
        """查询平均绩效"""
        return self.execute_safe_query('performance_avg_by_employee', (employee_id,))

    def query_performance_check(self, employee_id: str) -> QueryResult:
        """查询晋升绩效检查"""
        return self.execute_safe_query('performance_check_kpi', (employee_id,))

    def query_employee_full_info(self, employee_id_or_name: str) -> QueryResult:
        """查询员工完整信息（含项目数）"""
        return self.execute_safe_query('employee_full_info', (employee_id_or_name, employee_id_or_name))

    def query_active_projects(self) -> QueryResult:
        """查询进行中的项目"""
        return self.execute_safe_query('active_projects', tuple())

    def query_rd_employees(self) -> QueryResult:
        """查询研发部员工"""
        return self.execute_safe_query('rd_employees', tuple())

    def execute_intent_query(self, intent: Intent) -> List[QueryResult]:
        """根据意图执行查询"""
        results = []
        entities = intent.entities

        for source in intent.data_sources:
            if source == DataSource.EMPLOYEES:
                if entities.get('employee_id'):
                    # 查询特定员工
                    if '上级' in intent.original_question:
                        results.append(self.query_employee_manager(entities['employee_id']))
                    elif '邮箱' in intent.original_question:
                        results.append(self.query_employee_email(entities['employee_id']))
                    else:
                        results.append(self.query_employee_by_id(entities['employee_id']))
                elif entities.get('department'):
                    if '多少人' in intent.original_question or '人数' in intent.original_question:
                        results.append(self.query_dept_count(entities['department']))
                    else:
                        results.append(self.query_employees_by_dept(entities['department']))
                elif '研发部' in intent.original_question:
                    results.append(self.query_rd_employees())

            elif source == DataSource.PROJECTS or source == DataSource.PROJECT_MEMBERS:
                if entities.get('employee_id'):
                    results.append(self.query_projects_by_employee(entities['employee_id']))
                elif '在研' in intent.original_question or '进行中' in intent.original_question:
                    results.append(self.query_active_projects())

            elif source == DataSource.ATTENDANCE:
                if entities.get('employee_id'):
                    year = int(entities.get('year', 2026))
                    month = int(entities.get('month', 2))
                    results.append(self.query_late_count(entities['employee_id'], year, month))

            elif source == DataSource.PERFORMANCE:
                if entities.get('employee_id'):
                    if '晋升' in intent.original_question or '符合' in intent.original_question:
                        # 晋升检查需要完整员工信息
                        results.append(self.query_employee_full_info(entities.get('employee_name', entities['employee_id'])))
                        results.append(self.query_performance_check(entities['employee_id']))
                        results.append(self.query_performance_avg(entities['employee_id']))
                    else:
                        results.append(self.query_performance(entities['employee_id']))

        return results


def query_database(intent: Intent) -> List[QueryResult]:
    """数据库查询的便捷函数"""
    db = DatabaseQuery()
    try:
        return db.execute_intent_query(intent)
    finally:
        db.close()