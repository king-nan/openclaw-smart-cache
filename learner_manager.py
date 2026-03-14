"""
learner_manager.py - 请求学习器管理工具

用法：
    python learner_manager.py stats      # 查看统计
    python learner_manager.py recs       # 查看推荐
    python learner_manager.py report     # 导出报告
    python learner_manager.py clear      # 清空数据
    python learner_manager.py best "查询贵州茅台最新价"  # 获取最佳工具
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.request_learner import learner


def cmd_stats():
    """查看统计"""
    stats = learner.get_stats()
    
    print("=" * 60)
    print("请求学习统计")
    print("=" * 60)
    print(f"总请求数：{stats['total_requests']}")
    print(f"唯一模式：{stats['unique_patterns']}")
    print(f"常用模式（≥3 次）: {stats['common_patterns']}")
    print(f"最佳解决方案：{stats['best_solutions_count']}")
    print("=" * 60)


def cmd_recs(limit=10):
    """查看推荐"""
    recs = learner.get_recommendations(limit=limit)
    
    if not recs:
        print("暂无常用请求模式")
        return
    
    print("=" * 60)
    print(f"常用请求推荐 (Top {len(recs)})")
    print("=" * 60)
    
    for i, rec in enumerate(recs, 1):
        print(f"\n{i}. {rec['query_pattern']}")
        print(f"   出现次数：{rec['count']}")
        print(f"   成功率：{rec['success_rate']*100:.1f}%")
        print(f"   平均耗时：{rec['avg_duration']:.2f}秒")
        print(f"   最佳工具：{rec['best_tool']}")
        print(f"   工具使用：{rec['tools_used']}")
        print(f"   首次出现：{rec['first_seen']}")
        print(f"   最近使用：{rec['last_seen']}")
    
    print("=" * 60)


def cmd_report():
    """导出报告"""
    report = learner.export_report()
    print(f"报告已导出到 tools/cache/learning_report.json")


def cmd_clear():
    """清空数据"""
    confirm = input("确认清空所有学习数据？(y/N): ")
    if confirm.lower() == 'y':
        learner.clear()
        print("学习数据已清空")
    else:
        print("已取消")


def cmd_best(query: str):
    """获取最佳工具"""
    best = learner.get_best_tool(query)
    
    if best:
        print(f"查询：{query}")
        print(f"最佳工具：{best}")
    else:
        print(f"查询：{query}")
        print("暂无历史数据，无法推荐工具")


def main():
    if len(sys.argv) < 2:
        print("用法：python learner_manager.py <命令> [参数]")
        print("命令:")
        print("  stats         - 查看统计")
        print("  recs [n]      - 查看推荐 (默认前 10 个)")
        print("  report        - 导出报告")
        print("  clear         - 清空数据")
        print("  best \"查询\"   - 获取最佳工具")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == 'stats':
        cmd_stats()
    elif cmd == 'recs':
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        cmd_recs(limit)
    elif cmd == 'report':
        cmd_report()
    elif cmd == 'clear':
        cmd_clear()
    elif cmd == 'best':
        if len(sys.argv) < 3:
            print("错误：请提供查询内容")
            sys.exit(1)
        cmd_best(' '.join(sys.argv[2:]))
    else:
        print(f"未知命令：{cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
