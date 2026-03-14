"""
smart_cache.py - 智能缓存层

功能：
1. 内存缓存（LRU）- 热点数据
2. 磁盘缓存（SQLite）- 大型数据
3. 自动过期清理
4. 缓存统计和管理

用法：
    from smart_cache import cache
    
    # 设置缓存
    cache.set('stock:600519:price', {'price': 1413.64}, ttl=300)
    
    # 获取缓存
    data = cache.get('stock:600519:price')
    
    # 清除缓存
    cache.invalidate('stock:*:price')
    
    # 查看统计
    stats = cache.stats()
"""

import sqlite3
import json
import time
import os
import fnmatch
from datetime import datetime
from collections import OrderedDict
from typing import Any, Optional, Dict, List

# 配置
CACHE_DIR = os.path.join(os.path.dirname(__file__), 'cache')
DB_PATH = os.path.join(CACHE_DIR, 'cache.db')
INDEX_PATH = os.path.join(CACHE_DIR, 'index.json')

# 默认 TTL（秒）
DEFAULT_TTL = {
    'stock:price': 300,        # 股票价格 5 分钟
    'stock:info': 3600,        # 股票信息 1 小时
    'db:stats': 60,            # 数据库统计 1 分钟
    'query:result': 600,       # 查询结果 10 分钟
    'stock:list': 3600,        # 股票列表 1 小时
    'default': 300,            # 默认 5 分钟
}


class MemoryCache:
    """内存缓存（LRU 策略）"""
    
    def __init__(self, max_size=1000):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if key not in self.cache:
            self.misses += 1
            return None
        
        data, timestamp, ttl = self.cache[key]
        
        # 检查是否过期
        if time.time() - timestamp > ttl:
            del self.cache[key]
            self.misses += 1
            return None
        
        # 移到末尾（最近使用）
        self.cache.move_to_end(key)
        self.hits += 1
        return data
    
    def set(self, key: str, data: Any, ttl: int = 300):
        """设置缓存"""
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = (data, time.time(), ttl)
        
        # LRU 清理
        while len(self.cache) > self.max_size:
            self.cache.popitem(last=False)
    
    def delete(self, key: str):
        """删除缓存"""
        if key in self.cache:
            del self.cache[key]
    
    def clear(self):
        """清空缓存"""
        self.cache.clear()
    
    def keys(self) -> List[str]:
        """获取所有键"""
        return list(self.cache.keys())
    
    def stats(self) -> Dict:
        """获取统计信息"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        return {
            'size': len(self.cache),
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': f"{hit_rate:.1f}%"
        }


class DiskCache:
    """磁盘缓存（SQLite 存储）"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self._init_db()
    
    def _init_db(self):
        """初始化数据库"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.conn = sqlite3.connect(self.db_path, timeout=30)
        c = self.conn.cursor()
        
        c.execute('''CREATE TABLE IF NOT EXISTS cache (
            key TEXT PRIMARY KEY,
            value TEXT,
            timestamp REAL,
            ttl INTEGER
        )''')
        
        c.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON cache(timestamp)')
        self.conn.commit()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        try:
            c = self.conn.cursor()
            c.execute('SELECT value, timestamp, ttl FROM cache WHERE key = ?', (key,))
            row = c.fetchone()
            
            if not row:
                return None
            
            value, timestamp, ttl = row
            
            # 检查是否过期
            if time.time() - timestamp > ttl:
                self.delete(key)
                return None
            
            return json.loads(value)
            
        except Exception as e:
            print(f"DiskCache get error: {e}")
            return None
    
    def set(self, key: str, data: Any, ttl: int = 300):
        """设置缓存"""
        try:
            c = self.conn.cursor()
            value = json.dumps(data, ensure_ascii=False)
            c.execute('''
                INSERT OR REPLACE INTO cache (key, value, timestamp, ttl)
                VALUES (?, ?, ?, ?)
            ''', (key, value, time.time(), ttl))
            self.conn.commit()
        except Exception as e:
            print(f"DiskCache set error: {e}")
    
    def delete(self, key: str):
        """删除缓存"""
        try:
            c = self.conn.cursor()
            c.execute('DELETE FROM cache WHERE key = ?', (key,))
            self.conn.commit()
        except Exception as e:
            print(f"DiskCache delete error: {e}")
    
    def delete_pattern(self, pattern: str):
        """批量删除（支持通配符）"""
        try:
            c = self.conn.cursor()
            c.execute('SELECT key FROM cache')
            keys = [row[0] for row in c.fetchall()]
            
            for key in keys:
                if fnmatch.fnmatch(key, pattern):
                    self.delete(key)
        except Exception as e:
            print(f"DiskCache delete_pattern error: {e}")
    
    def clear(self):
        """清空缓存"""
        try:
            c = self.conn.cursor()
            c.execute('DELETE FROM cache')
            self.conn.commit()
        except Exception as e:
            print(f"DiskCache clear error: {e}")
    
    def count(self) -> int:
        """获取缓存数量"""
        try:
            c = self.conn.cursor()
            c.execute('SELECT COUNT(*) FROM cache')
            return c.fetchone()[0]
        except:
            return 0
    
    def size(self) -> int:
        """获取磁盘占用（字节）"""
        try:
            if os.path.exists(self.db_path):
                return os.path.getsize(self.db_path)
            return 0
        except:
            return 0
    
    def close(self):
        """关闭连接"""
        if self.conn:
            self.conn.close()


class SmartCache:
    """智能缓存（内存 + 磁盘双层）"""
    
    def __init__(self):
        self.memory = MemoryCache(max_size=1000)
        self.disk = DiskCache(DB_PATH)
        self.ttl_config = DEFAULT_TTL.copy()
    
    def _get_ttl(self, key: str) -> int:
        """根据键获取 TTL"""
        for prefix, ttl in self.ttl_config.items():
            if key.startswith(prefix):
                return ttl
        return self.ttl_config['default']
    
    def get(self, key: str, use_disk: bool = True) -> Optional[Any]:
        """
        获取缓存
        
        Args:
            key: 缓存键
            use_disk: 是否查询磁盘缓存
        
        Returns:
            缓存数据，未命中返回 None
        """
        # 先查内存
        data = self.memory.get(key)
        if data is not None:
            return data
        
        # 再查磁盘
        if use_disk:
            data = self.disk.get(key)
            if data is not None:
                # 回写到内存
                ttl = self._get_ttl(key)
                self.memory.set(key, data, ttl)
                return data
        
        return None
    
    def set(self, key: str, data: Any, ttl: int = None, to_disk: bool = True):
        """
        设置缓存
        
        Args:
            key: 缓存键
            data: 缓存数据
            ttl: 过期时间（秒），None 则自动判断
            to_disk: 是否写入磁盘
        """
        if ttl is None:
            ttl = self._get_ttl(key)
        
        # 写入内存
        self.memory.set(key, data, ttl)
        
        # 写入磁盘（大型数据）
        if to_disk:
            self.disk.set(key, data, ttl)
    
    def delete(self, key: str):
        """删除缓存"""
        self.memory.delete(key)
        self.disk.delete(key)
    
    def invalidate(self, pattern: str):
        """
        批量清除缓存（支持通配符）
        
        Args:
            pattern: 通配符模式，如 'stock:*:price'
        """
        # 清除内存
        for key in self.memory.keys():
            if fnmatch.fnmatch(key, pattern):
                self.memory.delete(key)
        
        # 清除磁盘
        self.disk.delete_pattern(pattern)
    
    def clear(self):
        """清空所有缓存"""
        self.memory.clear()
        self.disk.clear()
    
    def stats(self) -> Dict:
        """获取统计信息"""
        mem_stats = self.memory.stats()
        return {
            'memory': mem_stats,
            'disk': {
                'count': self.disk.count(),
                'size_mb': round(self.disk.size() / 1024 / 1024, 2),
            },
            'config': self.ttl_config
        }
    
    def set_ttl(self, prefix: str, ttl: int):
        """设置某类缓存的 TTL"""
        self.ttl_config[prefix] = ttl
    
    def warm_up(self, key: str, data: Any):
        """预热缓存（只写内存，不写磁盘）"""
        ttl = self._get_ttl(key)
        self.memory.set(key, data, ttl)
    
    def close(self):
        """关闭缓存"""
        self.disk.close()


# 全局缓存实例
cache = SmartCache()


# 装饰器：自动缓存函数结果
def cached(ttl: int = None, key_prefix: str = ''):
    """
    缓存装饰器
    
    用法：
        @cached(ttl=300, key_prefix='db:stats')
        def get_db_stats():
            # 耗时操作
            return result
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 生成缓存键
            key = f"{key_prefix}:{func.__name__}"
            if args:
                key += ':' + ':'.join(str(a) for a in args)
            
            # 尝试获取缓存
            result = cache.get(key)
            if result is not None:
                return result
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 写入缓存
            cache.set(key, result, ttl=ttl)
            return result
        
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator


if __name__ == "__main__":
    # 测试
    print("测试智能缓存层...")
    
    # 设置缓存
    cache.set('test:key1', {'data': 'hello'}, ttl=60)
    cache.set('stock:600519:price', {'price': 1413.64}, ttl=300)
    
    # 获取缓存
    print(f"test:key1 = {cache.get('test:key1')}")
    print(f"stock:600519:price = {cache.get('stock:600519:price')}")
    
    # 统计
    stats = cache.stats()
    print(f"\n缓存统计:")
    print(f"  内存：{stats['memory']['size']} 条，命中率 {stats['memory']['hit_rate']}")
    print(f"  磁盘：{stats['disk']['count']} 条，{stats['disk']['size_mb']} MB")
    
    # 清除
    cache.invalidate('test:*')
    print(f"\n清除 test:* 后：{cache.stats()['memory']['size']} 条")
    
    cache.close()
    print("\n测试完成！")
