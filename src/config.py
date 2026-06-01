"""
配置管理模块
支持环境变量和配置文件
"""
import os
from pathlib import Path
from typing import Optional


class Config:
    """企业问答助手配置"""

    def __init__(self):
        # 获取项目根目录
        self.project_root = Path(__file__).parent.parent.resolve()

        # 数据库路径 - 默认使用 data 目录
        self.db_path = os.environ.get(
            'ENTERPRISE_QA_DB_PATH',
            str(self.project_root / 'data' / 'enterprise.db')
        )

        # 知识库路径 - 默认使用 data/knowledge 目录
        self.kb_path = os.environ.get(
            'ENTERPRISE_QA_KB_PATH',
            str(self.project_root / 'data' / 'knowledge')
        )

        # 时区
        self.timezone = os.environ.get('ENTERPRISE_QA_TIMEZONE', 'Asia/Shanghai')

        # 当前日期（用于测试）
        self.current_date = os.environ.get('ENTERPRISE_QA_CURRENT_DATE', '2026-03-27')

    def get_db_path(self) -> Path:
        """获取数据库绝对路径"""
        return Path(self.db_path).resolve()

    def get_kb_path(self) -> Path:
        """获取知识库绝对路径"""
        return Path(self.kb_path).resolve()

    def validate(self) -> bool:
        """验证配置是否有效"""
        db_path = self.get_db_path()
        kb_path = self.get_kb_path()

        if not db_path.exists():
            raise FileNotFoundError(f"数据库文件不存在: {db_path}")

        if not kb_path.exists():
            raise FileNotFoundError(f"知识库目录不存在: {kb_path}")

        return True


# 全局配置实例
_config: Optional[Config] = None

def get_config() -> Config:
    """获取配置实例"""
    global _config
    if _config is None:
        _config = Config()
    return _config

def reset_config():
    """重置配置（用于测试）"""
    global _config
    _config = None