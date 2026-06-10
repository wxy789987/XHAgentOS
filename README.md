# XHAgentOS - 智能数据瞭望与数智问数系统

> 一个基于 B/S 架构 + AI 大模型驱动的企业级智能数据平台，集多维度数据采集、AI 深度分析、数字员工对话、3D 可视化大屏于一体。

---

## 📋 项目概述

XHAgentOS 是一套完整的企业智能数据解决方案，包含**管理后台**与**用户前台**双端系统：

- **管理后台**（端口 8001）：面向运维/管理人员，提供模型引擎配置、数字员工管理、瞭望数据采集、技能管理、权限管控、会话监控、3D 数智大屏等功能
- **用户前台**（端口 8000）：面向普通用户，提供数字员工对话、群组协作、好友系统、@提及数字员工、文本/语音问数等功能

---

## 🏗️ 系统架构

```
XHAgentOS/
├── app.py                    # 入口文件（路由注册、双端口启动）
├── app/
│   ├── controllers/          # 控制层（Tornado RequestHandlers）
│   │   ├── user_dialogue.py  # 用户侧好友/群组/@数字员工对话
│   │   ├── ai_model.py       # AI 模型引擎管理 + 对话测试 + Token统计
│   │   ├── employee.py       # 数字员工管理
│   │   ├── skill.py          # 技能管理（普通API/AI技能）
│   │   ├── lookout.py        # 瞭望数据采集管理
│   │   ├── lookout_deep.py   # AI 深度采集（crawl4ai）
│   │   ├── conversation.py   # 会话管理 + 违规监控
│   │   ├── dialogue.py       # 对话管理
│   │   ├── datascreen.py     # 3D 数智大屏
│   │   ├── settings.py       # 系统配置/日志/监控
│   │   ├── auth.py           # 登录/注册/角色认证
│   │   ├── user.py / role.py / feature.py / permission.py  # RBAC 权限管理
│   │   └── base.py           # 基类（Session/权限校验）
│   ├── models/               # 数据层（Repository 模式）
│   │   ├── user_dialogue.py  # 用户侧对话数据访问
│   │   ├── db.py             # SQLite 数据库初始化
│   │   ├── ai_model.py       # AI模型数据访问
│   │   ├── employee.py       # 数字员工 + 调用日志
│   │   └── ...               # 其他模型
│   ├── templates/            # 视图层（Tornado 模板）
│   │   ├── user_chat.html    # 用户侧聊天界面（核心）
│   │   ├── admin.html        # 管理后台主界面
│   │   ├── datascreen_view.html  # 3D 数智大屏
│   │   └── ...               # 其他模板
│   └── static/               # 静态资源
│       └── dist/             # LayUI、ECharts 等第三方库
├── database/
│   └── app.db                # SQLite 数据库文件
└── docs/
    └── codingPrompt.md       # 开发任务文档
```

---

## ✨ 核心功能

### 🔧 管理后台（端口 8001）

| 模块 | 功能说明 |
|------|---------|
| **AI 模型引擎** | 可视化配置满足 OpenAI 接口范式的模型，支持对话测试、Token 统计、30天趋势图表、默认模型设置、批量操作 |
| **数字员工** | 创建/编辑/测试数字员工，关联模型引擎与技能列表，自定义系统提示词约束 |
| **技能管理** | 普通 API 技能 + AI 技能，支持参数定义、调用测试、调用记录查询、AI 自动创建技能 |
| **瞭望管理** | 动态可视化规则配置采集源，搜索引擎式采集界面，采集数据仓库（20条/页），支持筛选导出 |
| **AI 深度采集** | 基于 crawl4ai + 默认模型对已采集数据进行深度挖掘，提供采集日志与 AI 分析报告 |
| **会话管理** | AI 情感分析、主题分析、实体识别，违规关键词/技能调用监控 |
| **对话管理** | 对话记录 CRUD、AI 调用 |
| **数智大屏** | 3D 地球可视化（ECharts-GL），六大洲散点标记、数据统计图表、词云 |
| **RBAC 权限** | 用户/角色/功能三级权限管理，二级联动配置，动态菜单渲染 |
| **系统设置** | 系统配置、操作日志、性能监控、日志分析图表 |

### 👤 用户前台（端口 8000）

| 模块 | 功能说明 |
|------|---------|
| **数字员工对话** | 与数字员工进行文本对话，AI 自动调用关联技能回复 |
| **群组对话** | 创建群组、邀请好友、添加数字员工到群组进行群聊 |
| **好友系统** | 搜索用户、添加好友、好友列表管理 |
| **@数字员工** | 输入 `@员工名称` 触发指定数字员工回复，支持自动补全下拉框 |
| **问数功能** | 文本/语音问数，数字员工根据问题调用对应技能返回结果 |
| **对话管理** | 对话记录查看、导出、分析（对话次数/成功率/响应时间） |

---

## 💻 技术栈

| 层级 | 技术选型 |
|------|---------|
| **后端框架** | Python 3.11 + Tornado 6.5.6（MVC 架构） |
| **数据库** | SQLite 3（Repository 模式） |
| **管理侧 UI** | LayUI 2.x（经典后台布局） |
| **用户侧 UI** | 自定义 HTML5 + CSS3 + JavaScript |
| **数据可视化** | ECharts 5.x + ECharts-GL（3D 地球） |
| **AI 集成** | OpenAI SDK（兼容 qwen3.5-flash、deepseek-v4-flash 等模型） |
| **数据采集** | BeautifulSoup + crawl4ai |
| **认证鉴权** | Cookie/Session + RBAC 三级权限模型 |

---

## 🚀 快速开始

### 环境要求

- Python 3.11+
- pip（Python 包管理工具）

### 安装与运行

```bash
# 1. 克隆仓库
git clone https://github.com/wxy789987/XHAgentOS.git
cd XHAgentOS

# 2. 创建虚拟环境（推荐）
python -m venv venv
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate

# 3. 安装依赖
pip install tornado requests openai beautifulsoup4 crawl4ai echarts

# 4. 初始化数据库（自动创建）
python -c "from app.models.db import init_db; init_db()"

# 5. 启动服务
python app.py
```

### 访问地址

| 端口 | 用途 | 默认登录 |
|------|------|---------|
| [http://localhost:8001](http://localhost:8001) | 管理后台 | admin / admin123 |
| [http://localhost:10086](http://localhost:10086) | 用户前台 | 注册新用户后登录 |

---

## 📚 使用指南

### 管理后台操作流程

```
启动服务 → 访问 http://localhost:8001 → admin/admin123 登录
  ├── 模型引擎 → 添加默认模型（配置 API_KEY 和 base_url）
  ├── 数字员工 → 选择模型、绑定技能、保存
  ├── 技能管理 → 配置采集/分析等技能
  └── 瞭望管理 → 配置采集源 → 执行采集 → 数据仓库查看
```

### 用户前台操作流程

```
访问 http://localhost:10086 → 注册/登录
  ├── 数字员工 → 点击员工进行对话
  ├── 创建群组 → 邀请好友/添加数字员工 → 群组对话
  ├── @数字员工 → 输入 @名称 自动补全 → 发送触发指定员工回复
  └── 问数 → 输入问题 → 数字员工调用技能返回结果
```

---

## 🤝 贡献指南

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/xxx`)
3. 提交更改 (`git commit -m 'feat: 添加xx功能'`)
4. 推送到分支 (`git push origin feature/xxx`)
5. 提交 Pull Request

---

## 📄 开源协议

本项目仅供学习交流使用。
