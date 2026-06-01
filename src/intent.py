"""
意图识别模块
解析用户问题，判断查询类型和数据源
"""
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class QueryType(Enum):
    """查询类型"""
    DB_ONLY = "db_only"           # 仅数据库查询
    KB_ONLY = "kb_only"           # 仅知识库查询
    DB_KB_MIXED = "db_kb_mixed"   # 混合查询
    DB_MULTI_TABLE = "db_multi"   # 多表关联查询
    TIME_RANGE = "time_range"     # 时间范围查询
    FUZZY = "fuzzy"               # 模糊语义查询
    INVALID = "invalid"           # 无效查询


class DataSource(Enum):
    """数据源"""
    EMPLOYEES = "employees"
    PROJECTS = "projects"
    PROJECT_MEMBERS = "project_members"
    ATTENDANCE = "attendance"
    PERFORMANCE = "performance_reviews"
    HR_POLICIES = "hr_policies"
    PROMOTION_RULES = "promotion_rules"
    TECH_DOCS = "tech_docs"
    FINANCE_RULES = "finance_rules"
    FAQ = "faq"
    MEETING_NOTES = "meeting_notes"


@dataclass
class Intent:
    """意图解析结果"""
    query_type: QueryType
    data_sources: List[DataSource]
    entities: Dict[str, str]  # 提取的实体：员工名、部门、时间等
    original_question: str
    needs_time_calculation: bool = False
    needs_promotion_check: bool = False


class IntentParser:
    """意图解析器"""

    # 员工姓名映射
    EMPLOYEE_NAMES = {
        '张三': 'EMP-001',
        '李四': 'EMP-002',
        '王五': 'EMP-003',
        '赵六': 'EMP-004',
        '钱七': 'EMP-005',
        '孙八': 'EMP-006',
        '周九': 'EMP-007',
        '吴十': 'EMP-008',
        'CEO': 'EMP-000',
    }

    # 部门列表
    DEPARTMENTS = ['研发部', '产品部', '市场部', '管理层']

    # 项目名称关键词
    PROJECT_KEYWORDS = ['项目', 'ReMe', '智能问答', '移动端', '数据分析', '官网']

    # 知识库关键词映射
    KB_KEYWORDS = {
        DataSource.HR_POLICIES: ['考勤', '迟到', '请假', '年假', '病假', '事假', '调休', '加班', '工作时间', '扣款'],
        DataSource.PROMOTION_RULES: ['晋升', '职级', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9', '晋升条件', '符合'],
        DataSource.TECH_DOCS: ['技术栈', '技术规范', '开发流程', '代码规范', '框架', 'PEP8'],
        DataSource.FINANCE_RULES: ['报销', '差旅', '招待', '财务', '餐补', '酒店', '机票'],
        DataSource.FAQ: ['入职', '试用期', '五险一金', '远程', '体检', '福利'],
        DataSource.MEETING_NOTES: ['会议', '全员大会', '技术同步', '议题', '决议'],
    }

    # SQL 注入检测模式
    SQL_INJECTION_PATTERNS = [
        r"SELECT\s+.*\s+FROM",
        r"INSERT\s+INTO",
        r"UPDATE\s+.*\s+SET",
        r"DELETE\s+FROM",
        r"DROP\s+TABLE",
        r"UNION\s+SELECT",
        r"--",
        r";\s*--",
        r"'\s*OR\s*'",
        r"'\s*AND\s*'",
        r"1\s*=\s*1",
        r"'\s*=\s*'",
    ]

    def parse(self, question: str) -> Intent:
        """解析用户问题"""
        # 先检查 SQL 注入
        if self._detect_sql_injection(question):
            return Intent(
                query_type=QueryType.INVALID,
                data_sources=[],
                entities={'error': 'SQL注入检测'},
                original_question=question
            )

        # 提取实体
        entities = self._extract_entities(question)

        # 判断查询类型和数据源
        query_type, data_sources = self._classify_query(question, entities)

        # 特殊标记
        needs_time_calc = self._needs_time_calculation(question)
        needs_promotion_check = '晋升' in question or '符合' in question and entities.get('employee_name')

        return Intent(
            query_type=query_type,
            data_sources=data_sources,
            entities=entities,
            original_question=question,
            needs_time_calculation=needs_time_calc,
            needs_promotion_check=needs_promotion_check
        )

    def _detect_sql_injection(self, question: str) -> bool:
        """检测 SQL 注入攻击"""
        for pattern in self.SQL_INJECTION_PATTERNS:
            if re.search(pattern, question, re.IGNORECASE):
                return True
        return False

    def _needs_time_calculation(self, question: str) -> bool:
        """判断是否需要时间计算"""
        time_keywords = ['上个月', '去年', '最近', '本月', '今年']
        for kw in time_keywords:
            if kw in question:
                return True
        # 检查是否有具体月份
        if re.search(r'\d+月', question):
            return True
        return False

    def _extract_entities(self, question: str) -> Dict[str, str]:
        """提取问题中的实体"""
        entities = {}

        # 提取员工姓名
        for name, emp_id in self.EMPLOYEE_NAMES.items():
            if name in question:
                entities['employee_name'] = name
                entities['employee_id'] = emp_id
                break

        # 提取员工ID (EMP-XXX 格式)
        emp_id_match = re.search(r'EMP-\d{3}', question)
        if emp_id_match:
            entities['employee_id'] = emp_id_match.group()

        # 提取部门
        for dept in self.DEPARTMENTS:
            if dept in question:
                entities['department'] = dept
                break

        # 提取时间
        time_patterns = [
            (r'(\d{4})年(\d{1,2})月', 'year_month'),
            (r'(\d{1,2})月', 'month_only'),
            (r'上个月', 'last_month'),
            (r'去年', 'last_year'),
            (r'(\d{4})年', 'year_only'),
        ]
        for pattern, key in time_patterns:
            match = re.search(pattern, question)
            if match:
                if key == 'year_month':
                    entities['year'] = match.group(1)
                    entities['month'] = match.group(2)
                elif key == 'month_only':
                    entities['month'] = match.group(1)
                elif key == 'year_only':
                    entities['year'] = match.group(1)
                else:
                    entities['time_ref'] = key
                break

        # 提取项目关键词
        for kw in self.PROJECT_KEYWORDS:
            if kw in question:
                entities['project_keyword'] = kw
                break

        # 提取职级
        level_match = re.search(r'P\d', question)
        if level_match:
            entities['level'] = level_match.group()

        return entities

    def _classify_query(self, question: str, entities: Dict) -> Tuple[QueryType, List[DataSource]]:
        """分类查询类型和数据源"""
        data_sources = []

        # 检查知识库关键词
        kb_sources = []
        for source, keywords in self.KB_KEYWORDS.items():
            for kw in keywords:
                if kw in question:
                    kb_sources.append(source)
                    break

        # 检查数据库关键词
        db_keywords = {
            DataSource.EMPLOYEES: ['邮箱', '部门', '上级', '入职', '职级', '员工', '多少人', '人数'],
            DataSource.PROJECTS: ['项目', '负责', '在研', '进行中', '已完成', '状态'],
            DataSource.PROJECT_MEMBERS: ['成员', '参与', '角色'],
            DataSource.ATTENDANCE: ['迟到', '考勤', '出勤', '旷工'],
            DataSource.PERFORMANCE: ['绩效', 'KPI', '评分', '考核'],
        }

        db_sources = []
        for source, keywords in db_keywords.items():
            for kw in keywords:
                if kw in question:
                    db_sources.append(source)
                    break

        # 特殊处理：晋升检查需要混合查询
        if '晋升' in question or ('符合' in question and entities.get('employee_name')):
            return QueryType.DB_KB_MIXED, [
                DataSource.PROMOTION_RULES,
                DataSource.EMPLOYEES,
                DataSource.PERFORMANCE,
                DataSource.PROJECT_MEMBERS
            ]

        # 特殊处理：员工基础信息查询
        if entities.get('employee_name') or entities.get('employee_id'):
            if '邮箱' in question or '部门' in question or '上级' in question:
                return QueryType.DB_ONLY, [DataSource.EMPLOYEES]
            if '项目' in question or '负责' in question:
                return QueryType.DB_MULTI_TABLE, [DataSource.PROJECTS, DataSource.PROJECT_MEMBERS]
            if '迟到' in question:
                return QueryType.TIME_RANGE, [DataSource.ATTENDANCE]
            if '绩效' in question or 'KPI' in question:
                return QueryType.DB_ONLY, [DataSource.PERFORMANCE]

        # 部门人数查询
        if '多少人' in question or '人数' in question:
            return QueryType.DB_ONLY, [DataSource.EMPLOYEES]

        # 纯知识库查询
        if kb_sources and not db_sources:
            return QueryType.KB_ONLY, kb_sources

        # 纯数据库查询
        if db_sources and not kb_sources:
            if len(db_sources) > 1:
                return QueryType.DB_MULTI_TABLE, db_sources
            return QueryType.DB_ONLY, db_sources

        # 混合查询
        if kb_sources and db_sources:
            return QueryType.DB_KB_MIXED, kb_sources + db_sources

        # 模糊查询
        if '最近' in question or '什么事' in question:
            return QueryType.FUZZY, [DataSource.MEETING_NOTES, DataSource.PROJECTS]

        # 无匹配
        return QueryType.INVALID, []


def parse_intent(question: str) -> Intent:
    """解析意图的便捷函数"""
    parser = IntentParser()
    return parser.parse(question)