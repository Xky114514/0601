"""
意图识别模块测试
"""
import pytest
import sys
import os

# 添加 src 目录到路径
src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
sys.path.insert(0, os.path.abspath(src_path))

from intent import IntentParser, QueryType, DataSource, parse_intent


class TestIntentParser:
    """意图解析器测试"""

    def setup_method(self):
        self.parser = IntentParser()

    def test_parse_employee_query(self):
        """测试员工查询意图"""
        intent = self.parser.parse("张三的部门是什么？")
        assert intent.query_type == QueryType.DB_ONLY
        assert DataSource.EMPLOYEES in intent.data_sources
        assert intent.entities['employee_name'] == '张三'
        assert intent.entities['employee_id'] == 'EMP-001'

    def test_parse_email_query(self):
        """测试邮箱查询意图"""
        intent = self.parser.parse("李四的邮箱是多少？")
        assert intent.query_type == QueryType.DB_ONLY
        assert DataSource.EMPLOYEES in intent.data_sources
        assert intent.entities['employee_name'] == '李四'

    def test_parse_manager_query(self):
        """测试上级查询意图"""
        intent = self.parser.parse("李四的上级是谁？")
        assert intent.query_type == QueryType.DB_ONLY
        assert DataSource.EMPLOYEES in intent.data_sources
        assert intent.entities['employee_name'] == '李四'

    def test_parse_kb_query(self):
        """测试知识库查询意图"""
        intent = self.parser.parse("年假怎么计算？")
        assert intent.query_type == QueryType.KB_ONLY
        assert DataSource.HR_POLICIES in intent.data_sources

    def test_parse_late_policy_query(self):
        """测试迟到扣款政策查询"""
        intent = self.parser.parse("迟到几次扣钱？")
        assert intent.query_type == QueryType.KB_ONLY
        assert DataSource.HR_POLICIES in intent.data_sources

    def test_parse_project_query(self):
        """测试项目查询意图"""
        intent = self.parser.parse("张三负责哪些项目？")
        assert intent.query_type == QueryType.DB_MULTI_TABLE
        assert DataSource.PROJECTS in intent.data_sources
        assert DataSource.PROJECT_MEMBERS in intent.data_sources

    def test_parse_dept_count_query(self):
        """测试部门人数查询"""
        intent = self.parser.parse("研发部有多少人？")
        assert intent.query_type == QueryType.DB_ONLY
        assert DataSource.EMPLOYEES in intent.data_sources
        assert intent.entities['department'] == '研发部'

    def test_parse_promotion_query(self):
        """测试晋升查询"""
        intent = self.parser.parse("王五符合 P5 晋升 P6 条件吗？")
        assert intent.query_type == QueryType.DB_KB_MIXED
        assert intent.needs_promotion_check == True
        assert DataSource.PROMOTION_RULES in intent.data_sources

    def test_parse_late_count_query(self):
        """测试迟到次数查询"""
        intent = self.parser.parse("张三 2 月迟到几次？")
        assert intent.query_type == QueryType.TIME_RANGE
        assert DataSource.ATTENDANCE in intent.data_sources
        assert intent.entities['month'] == '2'

    def test_parse_sql_injection(self):
        """测试 SQL 注入检测"""
        intent = self.parser.parse("SELECT * FROM users WHERE '1'='1'")
        assert intent.query_type == QueryType.INVALID
        assert 'SQL注入' in intent.entities.get('error', '')

    def test_parse_sql_injection_union(self):
        """测试 UNION 注入"""
        intent = self.parser.parse("张三 UNION SELECT * FROM employees")
        assert intent.query_type == QueryType.INVALID

    def test_parse_nonexistent_employee(self):
        """测试不存在员工查询"""
        intent = self.parser.parse("查一下 EMP-999")
        assert intent.entities['employee_id'] == 'EMP-999'

    def test_parse_fuzzy_query(self):
        """测试模糊查询"""
        intent = self.parser.parse("最近有什么事？")
        assert intent.query_type == QueryType.FUZZY

    def test_extract_time_entities(self):
        """测试时间实体提取"""
        intent = self.parser.parse("张三 2026年2月迟到几次？")
        assert intent.entities.get('year') == '2026'
        assert intent.entities.get('month') == '2'

    def test_extract_level_entity(self):
        """测试职级实体提取"""
        intent = self.parser.parse("王五符合 P5 晋升 P6 条件吗？")
        assert intent.entities.get('level') == 'P5'


class TestIntentConvenience:
    """便捷函数测试"""

    def test_parse_intent_function(self):
        """测试 parse_intent 函数"""
        intent = parse_intent("张三的部门是什么？")
        assert intent.query_type == QueryType.DB_ONLY
        assert intent.entities['employee_name'] == '张三'