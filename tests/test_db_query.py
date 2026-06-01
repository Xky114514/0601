"""
数据库查询模块测试
"""
import pytest
import sys
import os

# 设置测试环境变量 - 使用新的项目结构
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
db_path = os.path.join(root_path, 'data', 'enterprise.db')
os.environ['ENTERPRISE_QA_DB_PATH'] = db_path

src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
sys.path.insert(0, os.path.abspath(src_path))

from db_query import DatabaseQuery, QueryResult
from config import reset_config


class TestDatabaseQuery:
    """数据库查询测试"""

    def setup_method(self):
        reset_config()
        self.db = DatabaseQuery()

    def teardown_method(self):
        self.db.close()

    def test_query_employee_by_id(self):
        """测试按ID查询员工"""
        result = self.db.query_employee_by_id('EMP-001')
        assert result.error is None
        assert len(result.data) == 1
        assert result.data[0]['name'] == '张三'
        assert result.data[0]['department'] == '研发部'

    def test_query_employee_by_name(self):
        """测试按姓名查询员工"""
        result = self.db.query_employee_by_name('张三')
        assert result.error is None
        assert len(result.data) == 1
        assert result.data[0]['employee_id'] == 'EMP-001'

    def test_query_nonexistent_employee(self):
        """测试查询不存在员工"""
        result = self.db.query_employee_by_id('EMP-999')
        assert result.error is None
        assert len(result.data) == 0

    def test_query_employee_manager(self):
        """测试查询上级"""
        result = self.db.query_employee_manager('EMP-001')
        assert result.error is None
        assert len(result.data) == 1
        # 上级是 CEO
        assert result.data[0]['manager_name'] == 'CEO'

    def test_query_employees_by_dept(self):
        """测试部门员工查询"""
        result = self.db.query_employees_by_dept('研发部')
        assert result.error is None
        assert len(result.data) == 4  # 张三、李四、钱七、周九

    def test_query_dept_count(self):
        """测试部门人数"""
        result = self.db.query_dept_count('研发部')
        assert result.error is None
        assert result.data[0]['count'] == 4

    def test_query_employee_email(self):
        """测试邮箱查询"""
        result = self.db.query_employee_email('EMP-001')
        assert result.error is None
        assert result.data[0]['email'] == 'zhangsan@company.com'

    def test_query_projects_by_employee(self):
        """测试员工项目查询"""
        result = self.db.query_projects_by_employee('EMP-001')
        assert result.error is None
        # 张三参与4个项目
        assert len(result.data) == 4

    def test_query_late_count(self):
        """测试迟到次数"""
        result = self.db.query_late_count('EMP-001', 2026, 2)
        assert result.error is None
        assert result.data[0]['late_count'] == 2

    def test_query_performance(self):
        """测试绩效查询"""
        result = self.db.query_performance('EMP-001')
        assert result.error is None
        assert len(result.data) == 4  # 2025年4个季度

    def test_query_performance_avg(self):
        """测试平均绩效"""
        result = self.db.query_performance_avg('EMP-001')
        assert result.error is None
        avg = result.data[0]['avg_score']
        assert avg == 89.25  # (88+92+87+90)/4

    def test_query_active_projects(self):
        """测试进行中项目"""
        result = self.db.query_active_projects()
        assert result.error is None
        # PRJ-001, PRJ-003
        assert len(result.data) >= 2

    def test_query_rd_employees(self):
        """测试研发部员工"""
        result = self.db.query_rd_employees()
        assert result.error is None
        assert len(result.data) == 4

    def test_query_employee_full_info(self):
        """测试员工完整信息"""
        result = self.db.query_employee_full_info('王五')
        assert result.error is None
        assert len(result.data) == 1
        assert result.data[0]['project_count'] == 1  # 王五只参与1个项目


class TestQueryTemplates:
    """查询模板测试"""

    def test_safe_query_templates_exist(self):
        """测试安全查询模板"""
        db = DatabaseQuery()
        assert 'employee_by_id' in db.SAFE_QUERY_TEMPLATES
        assert 'employee_by_name' in db.SAFE_QUERY_TEMPLATES
        assert 'dept_count' in db.SAFE_QUERY_TEMPLATES
        db.close()

    def test_unknown_template_error(self):
        """测试未知模板错误"""
        db = DatabaseQuery()
        result = db.execute_safe_query('unknown_template', tuple())
        assert result.error is not None
        assert '未知' in result.error
        db.close()