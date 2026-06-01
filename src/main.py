"""
企业智能问答助手 - 主入口
"""
from typing import Optional

# 支持相对导入和绝对导入
try:
    from .config import get_config, reset_config
    from .intent import parse_intent, Intent, QueryType
    from .db_query import query_database, DatabaseQuery
    from .kb_search import search_knowledge, KnowledgeBaseSearch
    from .fusion import fuse_results, Answer
except ImportError:
    from config import get_config, reset_config
    from intent import parse_intent, Intent, QueryType
    from db_query import query_database, DatabaseQuery
    from kb_search import search_knowledge, KnowledgeBaseSearch
    from fusion import fuse_results, Answer


class EnterpriseQA:
    """企业智能问答助手"""

    def __init__(self, db_path: Optional[str] = None, kb_path: Optional[str] = None):
        """初始化问答助手"""
        # 如果提供了路径，重置配置
        if db_path or kb_path:
            reset_config()
            config = get_config()
            if db_path:
                config.db_path = db_path
            if kb_path:
                config.kb_path = kb_path

        self.config = get_config()

    def ask(self, question: str) -> Answer:
        """回答问题"""
        # 1. 解析意图
        intent = parse_intent(question)

        # 2. 执行数据库查询
        db_results = []
        if intent.query_type in [
            QueryType.DB_ONLY,
            QueryType.DB_KB_MIXED,
            QueryType.DB_MULTI_TABLE,
            QueryType.TIME_RANGE,
            QueryType.FUZZY,
        ]:
            db_results = query_database(intent)

        # 3. 执行知识库检索
        kb_results = []
        if intent.query_type in [
            QueryType.KB_ONLY,
            QueryType.DB_KB_MIXED,
            QueryType.FUZZY,
        ] or intent.needs_promotion_check:
            kb_results = search_knowledge(intent)

        # 4. 融合结果生成答案
        answer = fuse_results(intent, db_results, kb_results)

        return answer

    def format_answer(self, answer: Answer) -> str:
        """格式化答案输出"""
        output = answer.text

        if answer.sources:
            output += "\n\n> 来源：" + ", ".join(answer.sources)

        return output


def ask(question: str) -> str:
    """便捷问答函数"""
    qa = EnterpriseQA()
    answer = qa.ask(question)
    return qa.format_answer(answer)


# CLI 入口
def main():
    """命令行入口"""
    import sys

    if len(sys.argv) < 2:
        print("用法: python -m enterprise_qa <问题>")
        print("示例: python -m enterprise_qa '张三的部门是什么？'")
        sys.exit(1)

    question = sys.argv[1]
    result = ask(question)
    print(result)


if __name__ == '__main__':
    main()