"""
结果融合模块
多源信息整合和答案生成
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# 支持相对导入和绝对导入
try:
    from .intent import Intent, QueryType, DataSource
    from .db_query import QueryResult
    from .kb_search import KnowledgeResult
except ImportError:
    from intent import Intent, QueryType, DataSource
    from db_query import QueryResult
    from kb_search import KnowledgeResult


@dataclass
class Answer:
    """最终答案"""
    text: str
    sources: List[str]  # 来源标注
    confidence: float = 1.0
    needs_more_info: bool = False


class ResultFusion:
    """结果融合器"""

    # 员工ID到姓名映射
    EMPLOYEE_NAMES = {
        'EMP-000': 'CEO',
        'EMP-001': '张三',
        'EMP-002': '李四',
        'EMP-003': '王五',
        'EMP-004': '赵六',
        'EMP-005': '钱七',
        'EMP-006': '孙八',
        'EMP-007': '周九',
        'EMP-008': '吴十',
        'EMP-009': '离职员工',
    }

    def fuse(
        self,
        intent: Intent,
        db_results: List[QueryResult],
        kb_results: List[KnowledgeResult]
    ) -> Answer:
        """融合数据库和知识库结果"""

        # 处理无效查询
        if intent.query_type == QueryType.INVALID:
            return self._handle_invalid(intent)

        # 处理边界情况
        if not db_results and not kb_results:
            return self._handle_no_results(intent)

        # 根据查询类型选择处理方式
        if intent.query_type == QueryType.DB_ONLY:
            return self._handle_db_only(intent, db_results)

        if intent.query_type == QueryType.KB_ONLY:
            return self._handle_kb_only(intent, kb_results)

        if intent.query_type in [
            QueryType.DB_KB_MIXED,
            QueryType.DB_MULTI_TABLE,
            QueryType.TIME_RANGE,
        ]:
            return self._handle_mixed(intent, db_results, kb_results)

        if intent.query_type == QueryType.FUZZY:
            return self._handle_fuzzy(intent, db_results, kb_results)

        return Answer(
            text="抱歉，我无法理解这个问题。",
            sources=[],
            confidence=0.0
        )

    def _handle_invalid(self, intent: Intent) -> Answer:
        """处理无效查询"""
        error = intent.entities.get('error', '')

        if 'SQL注入' in error:
            return Answer(
                text="检测到潜在的 SQL 注入攻击，查询已被拦截。请使用正常的自然语言提问。",
                sources=["系统安全检测"],
                confidence=1.0
            )

        return Answer(
            text="抱歉，我无法理解这个问题。请尝试更明确地描述您的问题。",
            sources=[],
            confidence=0.0
        )

    def _handle_no_results(self, intent: Intent) -> Answer:
        """处理无结果情况"""
        # 检查是否查询不存在的员工
        emp_id = intent.entities.get('employee_id')
        if emp_id and emp_id.startswith('EMP-'):
            if emp_id not in self.EMPLOYEE_NAMES:
                return Answer(
                    text=f"未找到员工 {emp_id}，该员工不存在于系统中。",
                    sources=["employees 表"],
                    confidence=1.0
                )

        # 其他无结果情况
        return Answer(
            text=f"抱歉，没有找到与「{intent.original_question}」相关的信息。请尝试其他表述方式。",
            sources=[],
            confidence=0.0,
            needs_more_info=True
        )

    def _handle_db_only(self, intent: Intent, db_results: List[QueryResult]) -> Answer:
        """处理纯数据库查询"""
        if not db_results:
            return self._handle_no_results(intent)

        result = db_results[0]
        if result.error:
            return Answer(
                text=f"查询出错：{result.error}",
                sources=[result.source],
                confidence=0.0
            )

        data = result.data
        if not data:
            return self._handle_no_results(intent)

        # 根据问题类型生成答案
        question = intent.original_question

        # 查询部门
        if '部门' in question:
            emp = data[0]
            return Answer(
                text=f"{emp['name']}的部门是{emp['department']}。",
                sources=[f"employees 表 (employee_id: {emp['employee_id']})"]
            )

        # 查询邮箱
        if '邮箱' in question:
            emp = data[0]
            emp_id = emp.get('employee_id', '')
            return Answer(
                text=f"{emp['name']}的邮箱是 {emp['email']}。",
                sources=[f"employees 表 (employee_id: {emp_id})"]
            )

        # 查询上级
        if '上级' in question:
            emp = data[0]
            manager_name = emp.get('manager_name', '无')
            if manager_name and manager_name != '无':
                return Answer(
                    text=f"{emp['employee_name']}的上级是 {manager_name}（{emp['manager_id']}）。",
                    sources=[f"employees 表 (employee_id: {emp['employee_id']})"]
                )
            return Answer(
                text=f"{emp['employee_name']}没有上级记录。",
                sources=[f"employees 表"]
            )

        # 查询部门人数
        if '多少人' in question or '人数' in question:
            dept = intent.entities.get('department', '')
            if data:
                count = data[0]['count']
                return Answer(
                    text=f"{dept}有 {count} 人。",
                    sources=[f"employees 表 (department: {dept})"]
                )

        # 查询绩效
        if '绩效' in question or 'KPI' in question:
            name = self.EMPLOYEE_NAMES.get(intent.entities.get('employee_id', ''), '')
            scores = [str(r['kpi_score']) for r in data]
            grades = [r['grade'] for r in data]
            avg = sum(r['kpi_score'] for r in data) / len(data) if data else 0

            if '2025' in question:
                return Answer(
                    text=f"{name}2025年绩效情况：KPI分数分别为 {', '.join(scores)}，评级分别为 {', '.join(grades)}，平均 KPI 为 {avg:.2f}。",
                    sources=[f"performance_reviews 表 (employee_id: {intent.entities['employee_id']})"]
                )
            return Answer(
                text=f"{name}的绩效记录：平均 KPI 为 {avg:.2f}，最近评级为 {grades[-1] if grades else '无记录'}。",
                sources=[f"performance_reviews 表 (employee_id: {intent.entities['employee_id']})"]
            )

        # 默认返回
        emp = data[0]
        return Answer(
            text=f"查询结果：{emp.get('name', '')}，部门：{emp.get('department', '')}，职级：{emp.get('level', '')}",
            sources=[f"employees 表 (employee_id: {emp.get('employee_id', '')})"]
        )

    def _handle_kb_only(self, intent: Intent, kb_results: List[KnowledgeResult]) -> Answer:
        """处理纯知识库查询"""
        if not kb_results:
            return Answer(
                text=f"抱歉，没有找到关于「{intent.original_question}」的制度规定。",
                sources=[],
                confidence=0.0
            )

        best_result = kb_results[0]
        source_ref = best_result.source_file
        if best_result.section:
            source_ref += f" §{best_result.section}"

        # 简化内容输出
        content = best_result.content
        # 提取关键信息（排除标题行和空行）
        lines = content.split('\n')
        key_lines = [l for l in lines if l.strip() and not l.startswith('#')]

        # 【新增】检查是否有实际内容
        if not key_lines or len(key_lines) < 2:
            # 内容不足，返回无相关信息
            return Answer(
                text=f"抱歉，没有找到关于「{intent.original_question}」的具体信息。请尝试其他关键词。",
                sources=[],
                confidence=0.0,
                needs_more_info=True
            )

        return Answer(
            text=f"根据《{best_result.source_file.replace('.md', '')}》：\n" + '\n'.join(key_lines[:10]),
            sources=[source_ref]
        )

    def _handle_mixed(
        self,
        intent: Intent,
        db_results: List[QueryResult],
        kb_results: List[KnowledgeResult]
    ) -> Answer:
        """处理混合查询"""

        # 晋升检查
        if intent.needs_promotion_check:
            return self._check_promotion(intent, db_results, kb_results)

        # 项目查询
        if '项目' in intent.original_question or '负责' in intent.original_question:
            return self._handle_projects(intent, db_results)

        # 迟到查询
        if '迟到' in intent.original_question:
            return self._handle_late(intent, db_results)

        # 默认融合
        text_parts = []
        sources = []

        if db_results:
            for r in db_results:
                if r.data:
                    text_parts.append(f"数据库查询到 {len(r.data)} 条记录")
                    sources.append(f"{r.source}")

        if kb_results:
            for r in kb_results[:2]:
                text_parts.append(f"知识库找到：{r.source_file}")
                sources.append(r.source_file)

        return Answer(
            text='\n'.join(text_parts) if text_parts else "未找到相关信息",
            sources=sources
        )

    def _check_promotion(
        self,
        intent: Intent,
        db_results: List[QueryResult],
        kb_results: List[KnowledgeResult]
    ) -> Answer:
        """检查晋升条件"""
        employee_id = intent.entities.get('employee_id', '')
        employee_name = intent.entities.get('employee_name', '')

        if not employee_id:
            return Answer(
                text=f"未找到员工信息，无法判断晋升条件。",
                sources=[]
            )

        # 获取晋升规则
        promotion_rules = ""
        for r in kb_results:
            if 'promotion_rules' in r.source_file:
                promotion_rules = r.content
                break

        # 解析员工数据
        emp_info = None
        perf_data = []
        project_count = 0

        for r in db_results:
            if 'employee_full_info' in r.source:
                if r.data:
                    emp_info = r.data[0]
                    project_count = emp_info.get('project_count', 0)
            elif 'performance' in r.source:
                perf_data = r.data

        if not emp_info:
            return Answer(
                text=f"未找到 {employee_name or employee_id} 的员工信息。",
                sources=["employees 表"]
            )

        # 计算入职年限
        hire_date = emp_info.get('hire_date', '')
        current_level = emp_info.get('level', '')

        # 解析入职日期计算年限
        import datetime
        try:
            hire = datetime.datetime.strptime(hire_date, '%Y-%m-%d')
            now = datetime.datetime.strptime('2026-03-27', '%Y-%m-%d')
            years = (now - hire).days / 365
        except:
            years = 0

        # 计算平均KPI
        kpi_scores = [r['kpi_score'] for r in perf_data if r.get('kpi_score')]
        avg_kpi = sum(kpi_scores) / len(kpi_scores) if kpi_scores else 0
        min_kpi = min(kpi_scores) if kpi_scores else 0

        # P5 -> P6 晋升条件检查
        if current_level == 'P5':
            conditions = {
                '入职年限': {'require': '满1年', 'actual': f'{years:.1f}年', 'pass': years >= 1},
                '连续2季度KPI≥85': {'require': '≥85', 'actual': f'平均{avg_kpi:.1f}, 最低{min_kpi}', 'pass': min_kpi >= 85},
                '项目数≥3个': {'require': '≥3', 'actual': f'{project_count}个', 'pass': project_count >= 3},
                '无重大事故': {'require': '无', 'actual': '暂无记录', 'pass': True},
            }

            passes = sum(1 for c in conditions.values() if c['pass'])
            all_pass = passes == len(conditions)

            result_text = f"{employee_name}目前{'符合' if all_pass else '不符合'} P5→P6 晋升条件。\n\n分析如下：\n"
            result_text += "| 条件 | 要求 | 实际情况 | 结果 |\n"
            result_text += "|------|------|---------|------|\n"
            for name, cond in conditions.items():
                mark = '✓' if cond['pass'] else '✗'
                result_text += f"| {name} | {cond['require']} | {cond['actual']} | {mark} |\n"

            if not all_pass:
                suggestions = []
                if not conditions['连续2季度KPI≥85']['pass']:
                    suggestions.append("提升绩效表现")
                if not conditions['项目数≥3个']['pass']:
                    suggestions.append("争取参与更多项目")
                if not conditions['入职年限']['pass']:
                    suggestions.append("等待入职满1年")

                result_text += f"\n建议：{', '.join(suggestions)}。"

            return Answer(
                text=result_text,
                sources=[
                    "promotion_rules.md §P5→P6",
                    f"performance_reviews 表",
                    f"project_members 表",
                    f"employees 表 (employee_id: {employee_id})"
                ]
            )

        # 其他职级
        return Answer(
            text=f"{employee_name}当前职级为 {current_level}，晋升条件请参考晋升评定标准。",
            sources=["promotion_rules.md", f"employees 表"]
        )

    def _handle_projects(self, intent: Intent, db_results: List[QueryResult]) -> Answer:
        """处理项目查询"""
        employee_name = intent.entities.get('employee_name', '')

        for r in db_results:
            if r.data:
                projects = r.data
                project_list = []
                for p in projects:
                    role = p.get('role', '')
                    proj_name = p.get('project_name', p.get('name', ''))
                    status = p.get('status', '')
                    project_list.append(f"{proj_name}({role}, {status})")

                return Answer(
                    text=f"{employee_name}参与的项目：{', '.join(project_list)}。",
                    sources=[
                        f"projects 表",
                        f"project_members 表 (employee_id: {intent.entities.get('employee_id', '')})"
                    ]
                )

        return Answer(
            text=f"{employee_name}没有参与任何项目。",
            sources=["project_members 表"]
        )

    def _handle_late(self, intent: Intent, db_results: List[QueryResult]) -> Answer:
        """处理迟到查询"""
        employee_name = intent.entities.get('employee_name', '')
        month = intent.entities.get('month', '2')

        for r in db_results:
            if r.data:
                late_count = r.data[0].get('late_count', 0)
                return Answer(
                    text=f"{employee_name}{month}月迟到 {late_count} 次。",
                    sources=[
                        f"attendance 表 (employee_id: {intent.entities.get('employee_id', '')}, date: 2026-02)"
                    ]
                )

        return Answer(
            text=f"{employee_name}该月没有迟到记录。",
            sources=["attendance 表"]
        )

    def _handle_fuzzy(
        self,
        intent: Intent,
        db_results: List[QueryResult],
        kb_results: List[KnowledgeResult]
    ) -> Answer:
        """处理模糊查询"""
        # "最近有什么事"
        if '最近' in intent.original_question and '什么事' in intent.original_question:
            # 返回最近的会议和项目
            text = "最近的事项：\n\n"

            if kb_results:
                for r in kb_results[:2]:
                    meeting_name = r.source_file.replace('.md', '')
                    text += f"- {meeting_name}\n"

            if db_results:
                for r in db_results:
                    if r.data:
                        for p in r.data[:3]:
                            text += f"- 项目「{p.get('name', '')}」状态：{p.get('status', '')}\n"

            return Answer(
                text=text,
                sources=["meeting_notes 目录", "projects 表"]
            )

        return Answer(
            text="请问您具体想了解什么信息？可以尝试更明确地描述您的问题。",
            sources=[],
            needs_more_info=True
        )


def fuse_results(
    intent: Intent,
    db_results: List[QueryResult],
    kb_results: List[KnowledgeResult]
) -> Answer:
    """结果融合的便捷函数"""
    fusion = ResultFusion()
    return fusion.fuse(intent, db_results, kb_results)