"""
cache_manager.py - 缓存管理工具

用法：
    python cache_manager.py stats      # 查看统计
    python cache_manager.py clear      # 清空缓存
    python cache_manager.py keys       # 查看所有键
    python cache_manager.py delete stock:*  # 删除匹配键
"""

import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.smart_cache import cache


def cmd_stats():
    """查看缓存统计"""
    stats = cache.stats()
    
    print("=" * 60)
    print("缓存统计")
    print("=" * 60)
    
    print(f"\n内存缓存:")
    print(f"  条目数：{stats['memory']['size']}")
    print(f"  命中数：{stats['memory']['hits']}")
    print(f"  未命中：{stats['memory']['misses']}")
    print(f"  命中率：{stats['memory']['hit_rate']}")
    
    print(f"\n磁盘缓存:")
    print(f"  条目数：{stats['disk']['count']}")
    print(f"  占用：{stats['disk']['size_mb']} MB")
    
    print(f"\nTTL 配置:")
    for prefix, ttl in stats['config'].items():
        print(f"  {prefix}: {ttl}秒")
    
    print("=" * 60)


def cmd_clear():
    """清空缓存"""
    cache.clear()
    print("缓存已清空")


def cmd_keys():
    """查看所有缓存键"""
    stats = cache.stats()
    keys = cache.memory.keys()
    
    print(f"内存缓存键 ({len(keys)} 条):")
    for key in sorted(keys):
        print(f"  - {key}")
    
    print(f"\n磁盘缓存：{stats['disk']['count']} 条（使用 SQL 查询）")


def cmd_delete(pattern: str):
    """删除匹配的缓存"""
    cache.invalidate(pattern)
    print(f"已删除匹配 '{pattern}' 的缓存")


def cmd_test():
    """测试缓存性能"""
    import time
    
    print("=" * 60)
    print("缓存性能测试")
    print("=" * 60)
    
    # 测试写入
    start = time.time()
    for i in range(100):
        cache.set(f'test:perf:{i}', {'data': i * 100}, ttl=60)
    write_time = (time.time() - start) * 1000
    print(f"写入 100 条：{write_time:.1f}ms ({100/write_time*1000:.0f} 条/秒)")
    
    # 测试读取（命中）
    start = time.time()
    for i in range(100):
        cache.get(f'test:perf:{i}')
    read_hit_time = (time.time() - start) * 1000
    print(f"读取 100 条（命中）：{read_hit_time:.1f}ms ({100/read_hit_time*1000:.0f} 条/秒)")
    
    # 测试读取（未命中）
    start = time.time()
    for i in range(100):
        cache.get(f'test:miss:{i}')
    read_miss_time = (time.time() - start) * 1000
    print(f"读取 100 条（未命中）：{read_miss_time:.1f}ms")
    
    # 清理
    cache.invalidate('test:*')
    
    print("=" * 60)


def main():
    if len(sys.argv) < 2:
        print("用法：python cache_manager.py <命令> [参数]")
        print("命令:")
        print("  stats   - 查看统计")
        print("  clear   - 清空缓存")
        print("  keys    - 查看所有键")
        print("  delete  - 删除匹配键 (如：delete stock:*)")
        print("  test    - 性能测试")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == 'stats':
        cmd_stats()
    elif cmd == 'clear':
        cmd_clear()
    elif cmd == 'keys':
        cmd_keys()
    elif cmd == 'delete':
        if len(sys.argv) < 3:
            print("错误：请指定删除模式，如：delete stock:*")
            sys.exit(1)
        cmd_delete(sys.argv[2])
    elif cmd == 'test':
        cmd_test()
    else:
        print(f"未知命令：{cmd}")
        sys.exit(1)
    
    cache.close()


if __name__ == "__main__":
    main()
