"""
测试配置
"""
import sys
import os

# 确保 src 目录在路径中
src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# 设置测试数据路径
base_path = os.path.join(os.path.dirname(__file__), '..', '..')
db_path = os.path.join(base_path, 'enterprise-qa-data', 'enterprise.db')
kb_path = os.path.join(base_path, 'enterprise-qa-data', 'knowledge')

os.environ['ENTERPRISE_QA_DB_PATH'] = db_path
os.environ['ENTERPRISE_QA_KB_PATH'] = kb_path