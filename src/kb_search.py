"""
知识库检索模块
支持关键词匹配和文档检索
"""
import os
import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass

# 支持相对导入和绝对导入
try:
    from .config import get_config
except ImportError:
    from config import get_config

from intent import DataSource


@dataclass
class KnowledgeResult:
    """知识库检索结果"""
    content: str
    source_file: str
    section: Optional[str] = None
    relevance_score: float = 0.0


class KnowledgeBaseSearch:
    """知识库检索器"""

    # 文档内容缓存
    _cache: Dict[str, str] = {}

    def __init__(self):
        self.config = get_config()
        self.kb_path = self.config.get_kb_path()

    def _load_document(self, filename: str) -> str:
        """加载文档内容"""
        if filename in self._cache:
            return self._cache[filename]

        filepath = self.kb_path / filename
        if not filepath.exists():
            # 检查子目录
            filepath = self.kb_path / 'meeting_notes' / filename

        if not filepath.exists():
            return ''

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        self._cache[filename] = content
        return content

    def _split_sections(self, content: str) -> Dict[str, str]:
        """将文档按章节分割（支持三级标题）"""
        sections = {}
        current_section = 'root'
        current_subsection = None
        current_content = []

        lines = content.split('\n')
        for line in lines:
            # 检测二级标题（## 开头）
            if line.startswith('## '):
                if current_content:
                    # 保存当前内容
                    key = current_subsection if current_subsection else current_section
                    sections[key] = '\n'.join(current_content).strip()
                current_section = line[3:].strip()
                current_subsection = None
                current_content = [line]
            # 检测三级标题（### 开头）
            elif line.startswith('### '):
                if current_content:
                    # 保存三级标题之前的内容
                    if current_subsection:
                        sections[current_subsection] = '\n'.join(current_content).strip()
                    current_content = []
                current_subsection = line[4:].strip()
                current_content = [line]
            else:
                current_content.append(line)

        # 保存最后的内容
        if current_content:
            key = current_subsection if current_subsection else current_section
            if key:
                sections[key] = '\n'.join(current_content).strip()

        return sections

    def _calculate_relevance(self, content: str, keywords: List[str]) -> float:
        """计算相关度分数"""
        score = 0.0

        for kw in keywords:
            # 精确匹配加分
            if kw in content:
                score += 10
                # 标题匹配额外加分（## 后的章节名）
                section_title_match = re.search(r'##\s+.*' + kw, content)
                if section_title_match:
                    score += 20  # 章节标题匹配权重更高
                # 子标题匹配
                subsection_match = re.search(r'###\s+.*' + kw, content)
                if subsection_match:
                    score += 15
                # 表格内容匹配（年假等在表格中）
                if '|' + kw + '|' in content or kw in content and '|' in content:
                    score += 12

        return score

    def _search_in_document(
        self,
        content: str,
        filename: str,
        keywords: List[str]
    ) -> List[KnowledgeResult]:
        """在文档中搜索关键词"""
        results = []
        sections = self._split_sections(content)

        for section_name, section_content in sections.items():
            score = self._calculate_relevance(section_content, keywords)
            if score > 0:
                results.append(KnowledgeResult(
                    content=section_content,
                    source_file=filename,
                    section=section_name if section_name != 'root' else None,
                    relevance_score=score
                ))

        # 按相关度排序
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        return results

    def search_hr_policies(self, keywords: List[str]) -> List[KnowledgeResult]:
        """搜索人事制度 - 添加关键词优化"""
        content = self._load_document('hr_policies.md')

        # 关键词映射：将问题关键词映射到更精准的搜索关键词
        keyword_mapping = {
            '年假': ['年假', '请假类型', '入职满'],
            '病假': ['病假', '请假类型'],
            '事假': ['事假', '请假类型'],
            '迟到': ['迟到规则', '迟到', '扣款'],
            '扣钱': ['迟到规则', '扣款', '迟到'],
            '加班': ['加班制度', '加班'],
            '调休': ['调休制度', '调休'],
        }

        # 扩展关键词
        expanded_keywords = []
        for kw in keywords:
            expanded_keywords.append(kw)
            if kw in keyword_mapping:
                expanded_keywords.extend(keyword_mapping[kw])

        return self._search_in_document(content, 'hr_policies.md', expanded_keywords)

    def search_promotion_rules(self, keywords: List[str]) -> List[KnowledgeResult]:
        """搜索晋升规则"""
        content = self._load_document('promotion_rules.md')
        return self._search_in_document(content, 'promotion_rules.md', keywords)

    def search_tech_docs(self, keywords: List[str]) -> List[KnowledgeResult]:
        """搜索技术文档"""
        content = self._load_document('tech_docs.md')
        return self._search_in_document(content, 'tech_docs.md', keywords)

    def search_finance_rules(self, keywords: List[str]) -> List[KnowledgeResult]:
        """搜索财务制度"""
        content = self._load_document('finance_rules.md')
        return self._search_in_document(content, 'finance_rules.md', keywords)

    def search_faq(self, keywords: List[str]) -> List[KnowledgeResult]:
        """搜索FAQ"""
        content = self._load_document('faq.md')
        return self._search_in_document(content, 'faq.md', keywords)

    def search_meeting_notes(self, keywords: List[str]) -> List[KnowledgeResult]:
        """搜索会议纪要"""
        results = []

        # 搜索所有会议纪要
        meeting_dir = self.kb_path / 'meeting_notes'
        if meeting_dir.exists():
            for filepath in meeting_dir.glob('*.md'):
                content = self._load_document(filepath.name)
                doc_results = self._search_in_document(
                    content, f'meeting_notes/{filepath.name}', keywords
                )
                results.extend(doc_results)

        return results

    def _search_in_document(
        self,
        content: str,
        filename: str,
        keywords: List[str]
    ) -> List[KnowledgeResult]:
        """在文档中搜索关键词"""
        results = []
        sections = self._split_sections(content)

        for section_name, section_content in sections.items():
            score = self._calculate_relevance(section_content, keywords)
            if score > 0:
                results.append(KnowledgeResult(
                    content=section_content,
                    source_file=filename,
                    section=section_name if section_name != 'root' else None,
                    relevance_score=score
                ))

        # 按相关度排序
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        return results

    def search(self, source: DataSource, keywords: List[str]) -> List[KnowledgeResult]:
        """根据数据源类型搜索"""
        search_funcs = {
            DataSource.HR_POLICIES: self.search_hr_policies,
            DataSource.PROMOTION_RULES: self.search_promotion_rules,
            DataSource.TECH_DOCS: self.search_tech_docs,
            DataSource.FINANCE_RULES: self.search_finance_rules,
            DataSource.FAQ: self.search_faq,
            DataSource.MEETING_NOTES: self.search_meeting_notes,
        }

        func = search_funcs.get(source)
        if func:
            return func(keywords)
        return []

    def search_all(self, keywords: List[str]) -> List[KnowledgeResult]:
        """搜索所有知识库"""
        results = []
        for source in [
            DataSource.HR_POLICIES,
            DataSource.PROMOTION_RULES,
            DataSource.TECH_DOCS,
            DataSource.FINANCE_RULES,
            DataSource.FAQ,
            DataSource.MEETING_NOTES,
        ]:
            results.extend(self.search(source, keywords))
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        return results[:5]  # 返回最相关的5个结果


def search_knowledge(intent) -> List[KnowledgeResult]:
    """知识库检索的便捷函数"""
    kb = KnowledgeBaseSearch()

    # 从问题中提取关键词
    question = intent.original_question
    keywords = []

    # 提取关键词
    keyword_patterns = [
        r'年假', r'迟到', r'请假', r'加班', r'晋升', r'职级',
        r'报销', r'差旅', r'技术栈', r'开发流程', r'入职',
        r'试用期', r'福利', r'考勤', r'扣款', r'会议', r'全员大会'
    ]
    for p in keyword_patterns:
        if re.search(p, question):
            keywords.append(p)

    # 如果没有提取到关键词，使用问题中的词
    if not keywords:
        # 简单分词
        words = re.findall(r'[一-鿿]+', question)
        keywords = [w for w in words if len(w) >= 2][:5]

    results = []
    for source in intent.data_sources:
        if source in [
            DataSource.HR_POLICIES,
            DataSource.PROMOTION_RULES,
            DataSource.TECH_DOCS,
            DataSource.FINANCE_RULES,
            DataSource.FAQ,
            DataSource.MEETING_NOTES,
        ]:
            results.extend(kb.search(source, keywords))

    results.sort(key=lambda x: x.relevance_score, reverse=True)
    return results