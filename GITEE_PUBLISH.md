# Gitee 发布指南

## 准备工作

### 1. 创建 Gitee 仓库

1. 访问 https://gitee.com
2. 点击右上角 "+" → "新建仓库"
3. 填写信息：
   - 仓库名称：`openclaw-smart-cache`
   - 仓库介绍：OpenClaw 智能学习缓存层 - 类似人类小脑的缓存系统
   - 开源协议：MIT
   - 是否公开：公开

### 2. 初始化本地 Git

```bash
cd C:\Users\Administrator\.openclaw\workspace\skills\smart-cache

# 初始化 Git
git init

# 添加所有文件
git add .

# 首次提交
git commit -m "Initial commit: Smart Cache v1.0.0"

# 添加 Gitee 远程仓库
git remote add origin https://gitee.com/YOUR_USERNAME/openclaw-smart-cache.git

# 推送
git push -u origin master
```

### 3. 创建 Gitee Pages（可选）

1. 进入 Gitee 仓库页面
2. 点击 "管理" → "Pages"
3. 选择 `master` 分支
4. 点击 "保存"
5. 访问 `https://YOUR_USERNAME.gitee.io/openclaw-smart-cache`

## 仓库结构

```
openclaw-smart-cache/
├── README.md               # 项目说明（从 SKILL.md 复制）
├── SKILL.md                # OpenClaw Skill 格式
├── smart_cache.py          # 缓存核心
├── request_learner.py      # 请求学习器
├── cache_manager.py        # 缓存管理 CLI
├── learner_manager.py      # 学习器管理 CLI
├── examples/               # 示例代码
│   └── mx_query_v2.py     # 妙想查询集成示例
├── tests/                  # 测试用例（可选）
│   └── test_cache.py
├── requirements.txt        # 依赖说明
└── .gitignore             # Git 忽略文件
```

## 创建 .gitignore

```bash
# 创建 .gitignore
cat > .gitignore << EOF
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# 缓存数据（不提交）
cache/
*.db
*.jsonl
*.log

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db
EOF
```

## 发布到 OpenClaw Skill Hub

### 1. 提交到 ClawHub

访问 https://clawhub.com 提交你的 Skill。

### 2. 填写信息

- **名称**: smart-cache
- **介绍**: 智能学习缓存层，加速重复查询 200,000 倍
- **仓库**: 你的 Gitee 仓库地址
- **标签**: cache, performance, learning, optimization
- **分类**: 工具/效率

### 3. 等待审核

ClawHub 团队会审核你的 Skill，通过后即可被其他用户安装使用。

## 更新维护

### 发布新版本

```bash
# 修改代码后
git add .
git commit -m "v1.0.1: 修复 XXX 问题"
git tag v1.0.1
git push origin master --tags
```

### 更新 Gitee Release

1. 进入 Gitee 仓库
2. 点击 "发布" → "新建发布"
3. 填写版本信息
4. 上传附件（可选）

## 推广建议

### 1. 写技术博客

- 介绍缓存层的设计理念
- 性能对比数据
- 实际使用案例

### 2. 在 OpenClaw 社区分享

- Discord: https://discord.com/invite/clawd
- 论坛：分享使用经验

### 3. 收集反馈

- 在 Gitee 开启 Issues
- 响应用户问题
- 持续改进

## 常见问题

### Q: 如何保证缓存数据安全？

A: 敏感数据不要缓存，或使用加密存储。

### Q: 缓存占用多少空间？

A: 默认内存缓存 1000 条，磁盘缓存根据使用量增长，通常 <100MB。

### Q: 可以自定义缓存策略吗？

A: 可以，修改 `smart_cache.py` 中的 `DEFAULT_TTL` 配置。

## 许可证

MIT License - 可自由使用、修改、分发

---

**祝发布顺利！** 🚀
