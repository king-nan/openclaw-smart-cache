"""
mx_query_v2.py - 妙想金融数据查询（带缓存）

改进：
1. 自动缓存查询结果（5 分钟）
2. 缓存命中率统计
3. 支持强制刷新缓存

用法：
    python mx_query_v2.py "贵州茅台最新价"
    python mx_query_v2.py "贵州茅台最新价" --refresh  # 强制刷新
    python mx_query_v2.py --stats  # 查看缓存统计
"""

import requests
import os
import json
import sys
import argparse
import time
from datetime import datetime

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.smart_cache import cache
from tools.request_learner import learner

# API 配置
API_URL = "https://mkapi2.dfcfs.com/finskillshub/api/claw/query"
DEFAULT_APIKEY = "mkt_BPnfu-0nIJjpTR4tYASuHmOLvF9XHDz5tqqrxQuGjxk"


def get_apikey():
    """获取 API Key"""
    return os.environ.get('MX_APIKEY', DEFAULT_APIKEY)


def query_mx_data(query_text: str, apikey: str = None, use_cache: bool = True):
    """
    查询妙想金融数据（带缓存 + 学习）
    
    Args:
        query_text: 自然语言查询语句
        apikey: API Key
        use_cache: 是否使用缓存
    
    Returns:
        dict: 查询结果
    """
    if apikey is None:
        apikey = get_apikey()
    
    start_time = time.time()
    
    # 生成缓存键
    cache_key = f'mx:query:{abs(hash(query_text))}'
    
    # 尝试缓存
    if use_cache:
        cached = cache.get(cache_key)
        if cached:
            # 记录请求（缓存命中）
            duration = time.time() - start_time
            learner.record_request(
                query=query_text,
                tool="mx_query_v2(cache)",
                duration=duration,
                success=True,
                metadata={'from_cache': True}
            )
            return {'data': cached, '_from_cache': True}
    
    # API 查询
    headers = {
        'Content-Type': 'application/json',
        'apikey': apikey
    }
    
    data = {
        'toolQuery': query_text
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        duration = time.time() - start_time
        
        # 缓存结果
        if 'data' in result and use_cache:
            cache.set(cache_key, result['data'], ttl=300)
        
        # 记录请求（API 查询）
        learner.record_request(
            query=query_text,
            tool="mx_query_v2(api)",
            duration=duration,
            success='error' not in result,
            metadata={'from_cache': False}
        )
        
        return result
        
    except requests.exceptions.Timeout:
        duration = time.time() - start_time
        learner.record_request(
            query=query_text,
            tool="mx_query_v2(api)",
            duration=duration,
            success=False,
            metadata={'error': 'timeout'}
        )
        return {'error': '请求超时'}
    except requests.exceptions.RequestException as e:
        duration = time.time() - start_time
        learner.record_request(
            query=query_text,
            tool="mx_query_v2(api)",
            duration=duration,
            success=False,
            metadata={'error': str(e)}
        )
        return {'error': f'请求失败：{str(e)}'}


def format_result(result: dict):
    """格式化查询结果"""
    if 'error' in result:
        return f"[错误] {result['error']}"
    
    from_cache = result.get('_from_cache', False)
    data = result.get('data', {})
    
    if not data:
        return "[错误] 无数据"
    
    table_list = data.get('dataTableDTOList', [])
    if not table_list:
        return "[空] 未查询到数据"
    
    lines = []
    prefix = "[缓存命中]" if from_cache else "[API 查询]"
    
    for table in table_list:
        title = table.get('title', '')
        entity_name = table.get('entityName', '')
        
        lines.append(f"{prefix} {title}")
        lines.append(f"  证券：{entity_name}")
        
        table_data = table.get('table', {})
        name_map = table.get('nameMap', {})
        indicator_order = table.get('indicatorOrder', [])
        head_name = table_data.get('headName', [])
        
        # 输出数据
        if head_name and indicator_order:
            for i, time_val in enumerate(head_name):
                values = []
                for ind in indicator_order:
                    val_list = table_data.get(ind, [])
                    if i < len(val_list):
                        ind_name = name_map.get(ind, ind)
                        values.append(f"{ind_name}: {val_list[i]}")
                lines.append(f"  {time_val}: {', '.join(values)}")
        else:
            for ind in indicator_order:
                val_list = table_data.get(ind, [])
                if val_list:
                    ind_name = name_map.get(ind, ind)
                    lines.append(f"  {ind_name}: {val_list[0]}")
    
    return '\n'.join(lines)


def main():
    # 设置 UTF-8 输出
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
    
    parser = argparse.ArgumentParser(description='妙想金融数据查询（带缓存）')
    parser.add_argument('query', nargs='*', help='查询语句')
    parser.add_argument('--refresh', '-r', action='store_true', help='强制刷新缓存')
    parser.add_argument('--stats', '-s', action='store_true', help='显示缓存统计')
    
    args = parser.parse_args()
    
    if args.stats:
        stats = cache.stats()
        print("=" * 60)
        print("缓存统计")
        print("=" * 60)
        print(f"内存：{stats['memory']['size']} 条")
        print(f"  命中：{stats['memory']['hits']}")
        print(f"  未命中：{stats['memory']['misses']}")
        print(f"  命中率：{stats['memory']['hit_rate']}")
        print(f"磁盘：{stats['disk']['count']} 条，{stats['disk']['size_mb']} MB")
        print("=" * 60)
        cache.close()
        return
    
    if not args.query:
        print("用法：python mx_query_v2.py \"查询语句\" [--refresh]")
        print("示例：python mx_query_v2.py \"贵州茅台最新价\"")
        cache.close()
        return
    
    query_text = ' '.join(args.query)
    print(f"查询：{query_text}")
    print("-" * 60)
    
    result = query_mx_data(query_text, use_cache=not args.refresh)
    formatted = format_result(result)
    print(formatted)
    
    cache.close()


if __name__ == "__main__":
    main()
