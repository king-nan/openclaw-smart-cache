# Smart Cache - 智能学习缓存层

> 为 OpenClaw 设计的"小脑"缓存系统 - 自动学习、智能推荐、加速 200,000 倍

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenClaw Skill](https://img.shields.io/badge/OpenClaw-Skill-green.svg)](https://clawhub.com)

## 🚀 特性

- **⚡ 极速缓存** - 重复查询从 2-3 秒降至 0.01ms，加速 **200,000 倍**
- **🧠 自动学习** - 识别 3 次以上的常用请求，自动标记为"常用"
- **🎯 智能推荐** - 记录最佳工具/方案，自动推荐最优解
- **💾 双层架构** - 内存缓存（LRU）+ 磁盘缓存（SQLite）
- **🔧 零依赖** - 仅使用 Python 标准库

## 📦 安装

```bash
# 克隆到 OpenClaw skills 目录
cd C:\Users\Administrator\.openclaw\workspace\skills
git clone https://gitee.com/YOUR_USERNAME/openclaw-smart-cache.git
```

## 🎯 快速开始

### 基础用法

```python
from smart_cache import cache

# 设置缓存（5 分钟）
cache.set('stock:600519:price', {'price': 1413.64}, ttl=300)

# 获取缓存
data = cache.get('stock:600519:price')
```

### 装饰器

```python
from smart_cache import cached

@cached(ttl=60, key_prefix='db')
def get_db_stats():
    return expensive_operation()
```

### 学习器

```python
from request_learner import learner

learner.record_request("查询贵州茅台", "mx_query", 0.01, True)
recs = learner.get_recommendations()
```

## 📊 性能对比

| 操作 | 无缓存 | 有缓存 | 加速 |
|------|--------|--------|------|
| 读取（命中） | 2-3 秒 | 0.01ms | **200,000x** |
| 写入 | - | 10ms/条 | - |

## 📖 文档

- [SKILL.md](SKILL.md) - Skill 详细说明
- [GITEE_PUBLISH.md](GITEE_PUBLISH.md) - Gitee 发布指南
- [examples/](examples/) - 集成示例代码

## 🧪 测试

```bash
cd smart-cache
python tests/test_cache.py
```

## 📁 结构

```
smart-cache/
├── smart_cache.py       # 缓存核心
├── request_learner.py   # 学习器
├── cache_manager.py     # 缓存 CLI
├── learner_manager.py   # 学习 CLI
├── examples/            # 示例
├── tests/               # 测试
└── cache/               # 数据目录（运行时）
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

---

**Made with ❤️ for OpenClaw Community**
