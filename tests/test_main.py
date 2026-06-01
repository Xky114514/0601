"""
主模块集成测试 - 测试用例 T01-T12
"""
import pytest
import sys
import os

# 设置测试环境变量 - 使用新的项目结构
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.environ['ENTERPRISE_QA_DB_PATH'] = os.path.join(root_path, 'data', 'enterprise.db')
os.environ['ENTERPRISE_QA_KB_PATH'] = os.path.join(root_path, 'data', 'knowledge')

src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
sys.path.insert(0, os.path.abspath(src_path))

from main import EnterpriseQA, ask
from config import reset_config


class TestBasicQueries:
    """基础查询测试 (T01-T04)"""

    def setup_method(self):
        reset_config()
        self.qa = EnterpriseQA()

    # T01: 张三的部门是什么？
    def test_t01_department_query(self):
        """T01: 张三的部门"""
        answer = self.qa.ask("张三的部门是什么？")
        assert "研发部" in answer.text
        assert len(answer.sources) > 0

    # T02: 李四的上级是谁？
    def test_t02_manager_query(self):
        """T02: 李四的上级"""
        answer = self.qa.ask("李四的上级是谁？")
        assert "CEO" in answer.text
        assert answer.sources

    # T03: 年假怎么计算？
    def test_t03_annual_leave_policy(self):
        """T03: 年假计算"""
        answer = self.qa.ask("年假怎么计算？")
        assert "1 年" in answer.text or "5 天" in answer.text
        assert len(answer.sources) > 0

    # T04: 迟到几次扣钱？
    def test_t04_late_penalty_policy(self):
        """T04: 迟到扣款"""
        answer = self.qa.ask("迟到几次扣钱？")
        assert "4" in answer.text or "6" in answer.text or "50" in answer.text
        assert len(answer.sources) > 0


class TestAssociationQueries:
    """关联查询测试 (T05-T08)"""

    def setup_method(self):
        reset_config()
        self.qa = EnterpriseQA()

    # T05: 张三负责哪些项目？
    def test_t05_projects_query(self):
        """T05: 张三的项目"""
        answer = self.qa.ask("张三负责哪些项目？")
        assert "ReMe" in answer.text or "数据分析" in answer.text
        assert len(answer.sources) >= 2  # projects + project_members

    # T06: 研发部有多少人？
    def test_t06_dept_count_query(self):
        """T06: 研发部人数"""
        answer = self.qa.ask("研发部有多少人？")
        assert "4" in answer.text
        assert answer.sources

    # T07: 王五符合 P5 晋升 P6 条件吗？
    def test_t07_promotion_check(self):
        """T07: 王五晋升条件检查"""
        answer = self.qa.ask("王五符合 P5 晋升 P6 条件吗？")
        # 王五不符合：KPI 平均 80 < 85，项目数 1 < 3
        assert "不符合" in answer.text
        assert "KPI" in answer.text or "绩效" in answer.text

    # T08: 张三 2 月迟到几次？
    def test_t08_late_count_query(self):
        """T08: 张三2月迟到次数"""
        answer = self.qa.ask("张三 2 月迟到几次？")
        assert "2" in answer.text
        assert "迟到" in answer.text


class TestBoundaryCases:
    """边界情况测试 (T09-T12)"""

    def setup_method(self):
        reset_config()
        self.qa = EnterpriseQA()

    # T09: 查一下 EMP-999
    def test_t09_nonexistent_employee(self):
        """T09: 不存在员工"""
        answer = self.qa.ask("查一下 EMP-999")
        assert "不存在" in answer.text or "未找到" in answer.text

    # T10: 最近有什么事？
    def test_t10_fuzzy_query(self):
        """T10: 模糊问题"""
        answer = self.qa.ask("最近有什么事？")
        # 应该返回会议或项目信息，或追问
        assert answer.text  # 有回答

    # T11: SQL 注入攻击
    def test_t11_sql_injection(self):
        """T11: SQL注入拦截"""
        answer = self.qa.ask("SELECT * FROM users WHERE '1'='1'")
        assert "拦截" in answer.text or "注入" in answer.text

    # T12: 无相关信息查询
    def test_t12_no_match_query(self):
        """T12: 无匹配内容"""
        answer = self.qa.ask("xyzabc123 怎么报销")
        assert "没有" in answer.text or "未找到" in answer.text or "抱歉" in answer.text


class TestAdditionalQueries:
    """追加问题测试"""

    def setup_method(self):
        reset_config()
        self.qa = EnterpriseQA()

    def test_email_query(self):
        """李四邮箱查询"""
        answer = self.qa.ask("李四的邮箱是什么？")
        assert "lisi@company.com" in answer.text

    def test_product_dept_count(self):
        """产品部人数"""
        answer = self.qa.ask("产品部有多少人？")
        assert "3" in answer.text

    def test_performance_2025(self):
        """2025年绩效查询"""
        answer = self.qa.ask("张三 2025 年绩效如何？")
        assert "KPI" in answer.text or "绩效" in answer.text


class TestAskFunction:
    """便捷函数测试"""

    def setup_method(self):
        reset_config()

    def test_ask_function(self):
        """测试 ask 函数"""
        result = ask("张三的部门是什么？")
        assert "研发部" in result
        assert "来源" in result


class TestFormatAnswer:
    """答案格式测试"""

    def setup_method(self):
        reset_config()
        self.qa = EnterpriseQA()

    def test_format_with_sources(self):
        """测试带来源的格式"""
        answer = self.qa.ask("张三的部门是什么？")
        formatted = self.qa.format_answer(answer)
        assert "来源" in formatted