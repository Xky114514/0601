"""
知识库检索模块测试
"""
import pytest
import sys
import os

# 设置测试环境变量 - 使用新的项目结构
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
kb_path = os.path.join(root_path, 'data', 'knowledge')
os.environ['ENTERPRISE_QA_KB_PATH'] = kb_path

src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
sys.path.insert(0, os.path.abspath(src_path))

from kb_search import KnowledgeBaseSearch, KnowledgeResult, search_knowledge
from intent import parse_intent, DataSource
from config import reset_config


class TestKnowledgeBaseSearch:
    """知识库检索测试"""

    def setup_method(self):
        reset_config()
        self.kb = KnowledgeBaseSearch()

    def test_search_hr_policies(self):
        """测试人事制度搜索"""
        results = self.kb.search_hr_policies(['年假'])
        assert len(results) > 0
        assert 'hr_policies' in results[0].source_file

    def test_search_promotion_rules(self):
        """测试晋升规则搜索"""
        results = self.kb.search_promotion_rules(['P5', 'P6'])
        assert len(results) > 0
        assert 'promotion_rules' in results[0].source_file

    def test_search_finance_rules(self):
        """测试财务制度搜索"""
        results = self.kb.search_finance_rules(['报销'])
        assert len(results) > 0
        assert 'finance_rules' in results[0].source_file

    def test_search_faq(self):
        """测试FAQ搜索"""
        results = self.kb.search_faq(['入职'])
        assert len(results) > 0
        assert 'faq' in results[0].source_file

    def test_search_meeting_notes(self):
        """测试会议纪要搜索"""
        results = self.kb.search_meeting_notes(['全员大会'])
        assert len(results) > 0

    def test_search_no_match(self):
        """测试无匹配搜索"""
        results = self.kb.search_hr_policies(['xyzabc123'])
        assert len(results) == 0

    def test_relevance_score(self):
        """测试相关度评分"""
        results = self.kb.search_hr_policies(['年假', '入职'])
        if results:
            assert results[0].relevance_score > 0

    def test_search_by_source(self):
        """测试按数据源搜索"""
        results = self.kb.search(DataSource.HR_POLICIES, ['迟到', '扣款'])
        assert len(results) > 0

    def test_search_all(self):
        """测试全局搜索"""
        results = self.kb.search_all(['晋升'])
        assert len(results) > 0


class TestSearchKnowledge:
    """便捷函数测试"""

    def setup_method(self):
        reset_config()

    def test_search_knowledge_function(self):
        """测试 search_knowledge 函数"""
        intent = parse_intent("年假怎么计算？")
        results = search_knowledge(intent)
        assert len(results) > 0