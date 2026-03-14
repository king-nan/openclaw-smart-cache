"""
request_learner.py - 请求学习器

功能：
1. 追踪所有请求的频率
2. 记录每次请求的工具调用和结果
3. 3 次以上重复请求自动标记为"常用"
4. 存储最佳解决方案（最快/最成功）
5. 提供智能推荐

用法：
    from request_learner import learner
    
    # 记录请求
    learner.record_request("查询贵州茅台最新价", 
                          tool="mx_query_v2", 
                          duration=2.3,
                          success=True)
    
    # 获取推荐
    recs = learner.get_recommendations()
    
    # 查看统计
    stats = learner.get_stats()
"""

import json
import os
import time
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Optional, Any

# 配置
DATA_DIR = os.path.join(os.path.dirname(__file__), 'cache')
REQUEST_LOG = os.path.join(DATA_DIR, 'request_log.jsonl')
PATTERNS_FILE = os.path.join(DATA_DIR, 'patterns.json')

# 阈值
REPEAT_THRESHOLD = 3  # 3 次以上标记为常用


class RequestLearner:
    def __init__(self):
        self.requests = []  # 所有请求记录
        self.patterns = {}  # 请求模式统计
        self.best_solutions = {}  # 最佳解决方案
        self._load()
    
    def _load(self):
        """加载历史数据"""
        os.makedirs(DATA_DIR, exist_ok=True)
        
        # 加载请求模式
        if os.path.exists(PATTERNS_FILE):
            try:
                with open(PATTERNS_FILE, 'r', encoding='utf-8') as f:
                    self.patterns = json.load(f)
            except:
                self.patterns = {}
        
        # 加载最佳解决方案
        if 'best_solutions' not in self.patterns:
            self.patterns['best_solutions'] = {}
        self.best_solutions = self.patterns['best_solutions']
        
        # 加载最近的请求日志（最多 1000 条）
        if os.path.exists(REQUEST_LOG):
            try:
                with open(REQUEST_LOG, 'r', encoding='utf-8') as f:
                    lines = f.readlines()[-1000:]
                    self.requests = [json.loads(line) for line in lines]
            except:
                self.requests = []
    
    def _save(self):
        """保存数据"""
        # 保存模式
        with open(PATTERNS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.patterns, f, ensure_ascii=False, indent=2)
        
        # 追加请求日志
        with open(REQUEST_LOG, 'a', encoding='utf-8') as f:
            for req in self.requests[-10:]:  # 只保存最近 10 条
                f.write(json.dumps(req, ensure_ascii=False) + '\n')
    
    def record_request(self, 
                       query: str,
                       tool: str = None,
                       duration: float = None,
                       success: bool = True,
                       result: Any = None,
                       metadata: Dict = None):
        """
        记录一次请求
        
        Args:
            query: 请求内容
            tool: 使用的工具
            duration: 耗时（秒）
            success: 是否成功
            result: 结果数据（可选，大型数据不存）
            metadata: 其他元数据
        """
        timestamp = time.time()
        
        # 标准化查询（去除时间等变量）
        normalized = self._normalize_query(query)
        
        # 记录请求
        record = {
            'timestamp': timestamp,
            'query': query,
            'normalized': normalized,
            'tool': tool,
            'duration': duration,
            'success': success,
            'metadata': metadata or {}
        }
        
        self.requests.append(record)
        
        # 更新模式统计
        if normalized not in self.patterns:
            self.patterns[normalized] = {
                'count': 0,
                'total_duration': 0,
                'success_count': 0,
                'tools': defaultdict(int),
                'first_seen': timestamp,
                'last_seen': timestamp,
                'marked_as_common': False
            }
        
        pattern = self.patterns[normalized]
        pattern['count'] += 1
        pattern['last_seen'] = timestamp
        
        if duration:
            pattern['total_duration'] += duration
        
        if success:
            pattern['success_count'] += 1
        
        if tool:
            pattern['tools'][tool] += 1
        
        # 更新最佳解决方案
        self._update_best_solution(normalized, tool, duration, success)
        
        # 检查是否达到常用阈值
        if pattern['count'] >= REPEAT_THRESHOLD and not pattern['marked_as_common']:
            pattern['marked_as_common'] = True
            print(f"[学习] 发现常用请求：{normalized}（已出现 {pattern['count']} 次）")
        
        # 保存
        self._save()
    
    def _normalize_query(self, query: str) -> str:
        """
        标准化查询（去除变量部分）
        
        例如：
        - "查询贵州茅台 2026-03-14 最新价" → "查询股票最新价"
        - "导入数据库第 100 只股票" → "导入数据库股票"
        """
        normalized = query.lower()
        
        # 替换日期
        import re
        normalized = re.sub(r'\d{4}-\d{2}-\d{2}', '{date}', normalized)
        normalized = re.sub(r'\d{8}', '{date}', normalized)
        
        # 替换股票代码
        normalized = re.sub(r'\b[0-9]{6}\b', '{code}', normalized)
        normalized = re.sub(r'\b(sh|sz)\.{code}', '{code}', normalized)
        
        # 替换股票名称（简化）
        stock_names = ['贵州茅台', '宁德时代', '平安银行', '东方财富', '五粮液']
        for name in stock_names:
            normalized = normalized.replace(name, '{stock}')
        
        # 替换数字
        normalized = re.sub(r'\b\d+\b', '{n}', normalized)
        
        return normalized
    
    def _update_best_solution(self, 
                              normalized: str,
                              tool: str,
                              duration: float,
                              success: bool):
        """更新最佳解决方案"""
        if normalized not in self.best_solutions:
            self.best_solutions[normalized] = {
                'tool': None,
                'min_duration': float('inf'),
                'success_rate': 0,
                'attempts': 0
            }
        
        best = self.best_solutions[normalized]
        best['attempts'] += 1
        
        if tool and success:
            # 更新最快工具
            if duration and duration < best['min_duration']:
                best['tool'] = tool
                best['min_duration'] = duration
            
            # 计算成功率
            best['success_rate'] = best['attempts'] / max(1, best['attempts'])
    
    def get_recommendations(self, limit: int = 10) -> List[Dict]:
        """
        获取推荐（常用请求和最佳工具）
        
        Returns:
            推荐列表，按频率排序
        """
        recommendations = []
        
        for normalized, pattern in self.patterns.items():
            count = pattern.get('count', 0)
            if count >= REPEAT_THRESHOLD:
                best = self.best_solutions.get(normalized, {})
                
                recommendations.append({
                    'query_pattern': normalized,
                    'count': count,
                    'success_rate': pattern.get('success_count', 0) / max(1, count),
                    'avg_duration': pattern.get('total_duration', 0) / max(1, count),
                    'best_tool': best.get('tool'),
                    'min_duration': best.get('min_duration'),
                    'tools_used': dict(pattern.get('tools', {})),
                    'first_seen': datetime.fromtimestamp(pattern.get('first_seen', 0)).strftime('%Y-%m-%d %H:%M'),
                    'last_seen': datetime.fromtimestamp(pattern.get('last_seen', 0)).strftime('%Y-%m-%d %H:%M')
                })
        
        # 按频率排序
        recommendations.sort(key=lambda x: x['count'], reverse=True)
        
        return recommendations[:limit]
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        total_requests = len(self.requests)
        common_patterns = sum(1 for p in self.patterns.values() if p.get('marked_as_common', False))
        
        return {
            'total_requests': total_requests,
            'unique_patterns': len(self.patterns),
            'common_patterns': common_patterns,
            'best_solutions_count': len(self.best_solutions)
        }
    
    def get_best_tool(self, query: str) -> Optional[str]:
        """
        根据查询获取最佳工具
        
        Args:
            query: 查询内容
        
        Returns:
            最佳工具名称，或 None
        """
        normalized = self._normalize_query(query)
        
        if normalized in self.best_solutions:
            return self.best_solutions[normalized].get('tool')
        
        return None
    
    def clear(self):
        """清空学习数据"""
        self.requests = []
        self.patterns = {}
        self.best_solutions = {}
        
        # 删除文件
        if os.path.exists(REQUEST_LOG):
            os.remove(REQUEST_LOG)
        if os.path.exists(PATTERNS_FILE):
            os.remove(PATTERNS_FILE)
        
        self._save()
    
    def export_report(self, output_path: str = None):
        """导出学习报告"""
        if output_path is None:
            output_path = os.path.join(DATA_DIR, 'learning_report.json')
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'stats': self.get_stats(),
            'recommendations': self.get_recommendations(limit=50),
            'best_solutions': self.best_solutions
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"学习报告已导出：{output_path}")
        return report


# 全局实例
learner = RequestLearner()


if __name__ == "__main__":
    # 测试
    print("测试请求学习器...")
    
    # 模拟请求
    learner.record_request("查询贵州茅台最新价", "mx_query_v2", 2.3, True)
    learner.record_request("查询贵州茅台最新价", "mx_query_v2", 0.01, True)  # 缓存命中
    learner.record_request("查询贵州茅台最新价", "mx_query_v2", 0.01, True)  # 缓存命中
    learner.record_request("查询贵州茅台最新价", "mx_query_v2", 0.01, True)  # 第 4 次
    
    learner.record_request("导入数据库股票", "db_import_stable", 180.5, True)
    learner.record_request("导入数据库股票", "db_import_stable", 180.5, True)
    learner.record_request("导入数据库股票", "db_import_stable", 180.5, True)
    
    # 查看推荐
    print("\n推荐:")
    recs = learner.get_recommendations()
    for rec in recs:
        print(f"  {rec['query_pattern']}: {rec['count']}次，最佳工具：{rec['best_tool']}")
    
    # 查看统计
    print("\n统计:")
    stats = learner.get_stats()
    for k, v in stats.items():
        print(f"  {k}: {v}")
    
    # 获取最佳工具
    best = learner.get_best_tool("查询贵州茅台最新价")
    print(f"\n查询贵州茅台最佳工具：{best}")
