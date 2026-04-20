# 📚 CSR GenAI 项目导航指南

**项目名称**: 临床研究报告生成系统 (Clinical Study Report GenAI)  
**版本**: 1.0  
**最后更新**: 2026 年 4 月 16 日  
**状态**: ✅ 所有关键功能已完成并修复

---

## 🗂️ 项目结构

```
CSR_Program/
├── 📄 plan.md                    # 原始项目计划（5 个阶段）
├── 📄 README.md                  # 项目概览
├── 📄 QUICKSTART.md              # ⭐ 快速启动指南
├── 📄 DEVELOPMENT.md             # 开发详细指南
├── 📄 FIXES.md                   # ⭐ 修复总结（必读）
├── 📄 CHECKLIST.md               # 修复验证清单
├── 📋 NAVIGATION.md              # 本文件（项目导航）
│
├── 📁 backend/                   # FastAPI 后端服务
│   ├── main.py                   # 应用入口点
│   ├── requirements.txt           # Python 依赖
│   ├── csr.db                    # SQLite 数据库（运行时自动创建）
│   │
│   ├── app/
│   │   ├── __init__.py
│   │   ├── database.py           # 数据库配置
│   │   │
│   │   ├── models/
│   │   │   └── models.py         # SQLAlchemy ORM 定义
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── projects.py       # 项目管理 API
│   │   │   ├── documents.py      # 文档处理 API
│   │   │   ├── chapters.py       # 结构树管理 API
│   │   │   └── logs.py           # 操作日志 API
│   │   │
│   │   ├── services/
│   │   │   └── document_processor.py  # 文档解析服务
│   │   │
│   │   └── schemas/
│   │       └── schemas.py        # Pydantic 数据模型
│   │
│   └── uploads/                  # 上传文件存储目录（运行时自动创建）
│
├── 📁 frontend/                  # Next.js 14 前端应用
│   ├── package.json              # Node.js 依赖
│   ├── tsconfig.json             # TypeScript 配置
│   ├── next.config.js            # Next.js 配置
│   ├── tailwind.config.ts         # Tailwind CSS 配置
│   │
│   ├── app/
│   │   ├── layout.tsx            # 根布局
│   │   ├── page.tsx              # 主页
│   │   │
│   │   └── projects/
│   │       ├── page.tsx          # 项目列表页
│   │       └── [id]/
│   │           └── page.tsx      # 项目详情页
│   │
│   ├── components/
│   │   ├── DocumentUpload.tsx     # 文档上传组件
│   │   ├── ChapterTree.tsx        # 结构树组件
│   │   └── ActionLog.tsx          # 操作日志组件
│   │
│   └── node_modules/             # 依赖包（运行时自动创建）
│
├── 📁 docs/                      # 文档存储
│   └── [API documentation]
│
├── 🔧 test_api.bat               # Windows API 测试脚本
├── 🔧 test_api.sh                # Unix API 测试脚本
│
└── 📁 .vscode/                   # VS Code 配置

```

---

## 📖 文档导航

### 🚀 入门必读（按顺序）

1. **[QUICKSTART.md](./QUICKSTART.md)** ⭐
   - **目标**: 5 分钟启动应用
   - **内容**: 安装、启动、验证步骤
   - **适合**: 首次使用者
   - **时长**: 5-10 分钟

2. **[FIXES.md](./FIXES.md)** ⭐
   - **目标**: 理解所有已修复的问题
   - **内容**: 发现的 15+ 个问题和解决方案
   - **适合**: 想要理解代码现状
   - **时长**: 10-15 分钟

3. **[DEVELOPMENT.md](./DEVELOPMENT.md)**
   - **目标**: 深入开发指南
   - **内容**: API 文档、数据库模式、开发流程
   - **适合**: 想要参与开发
   - **时长**: 20-30 分钟

### 📋 参考文档

- **[README.md](./README.md)** - 项目概览和技术栈
- **[plan.md](./plan.md)** - 原始项目计划（4 个阶段）
- **[CHECKLIST.md](./CHECKLIST.md)** - 修复验证清单
- **[NAVIGATION.md](./NAVIGATION.md)** - 本文件

---

## 🎯 快速导航

### 我想要...

#### 🚀 快速启动应用
→ 参考 [QUICKSTART.md](./QUICKSTART.md)

#### 🔍 了解有哪些问题被修复了
→ 参考 [FIXES.md](./FIXES.md)

#### 📚 学习项目如何工作
→ 参考 [DEVELOPMENT.md](./DEVELOPMENT.md) + [README.md](./README.md)

#### 🛠️ 进行代码开发/修改
→ 参考 [DEVELOPMENT.md](./DEVELOPMENT.md)

#### ✅ 验证所有修复都已完成
→ 参考 [CHECKLIST.md](./CHECKLIST.md)

#### 🗺️ 了解原始项目计划
→ 参考 [plan.md](./plan.md)

#### 📡 查看 API 文档
→ 启动后端，访问 http://localhost:8000/docs

#### 🧪 运行自动化测试
→ 执行 `test_api.bat` (Windows) 或 `test_api.sh` (Linux/Mac)

---

## 🏗️ 项目架构

```
┌─────────────────┐
│   Web Browser   │
│  localhost:3000 │
└────────┬────────┘
         │
         │ HTTP Request
         │
┌────────▼──────────┐
│  Next.js 前端     │
│  (localhost:3000) │
│  ├─ Projects     │
│  ├─ Documents    │
│  ├─ Chapters     │
│  └─ Logs         │
└────────┬──────────┘
         │
         │ REST API
         │
┌────────▼──────────┐
│  FastAPI 后端    │
│  (localhost:8000)│
│  ├─ /api/projects│
│  ├─ /api/documents
│  ├─ /api/chapters│
│  └─ /api/logs    │
└────────┬──────────┘
         │
         │ SQL
         │
┌────────▼──────────┐
│   SQLite DB      │
│   (csr.db)       │
│  ├─ projects     │
│  ├─ documents    │
│  ├─ chapters     │
│  └─ logs         │
└──────────────────┘
```

---

## 🔄 工作流程

### 用户工作流

```
1. 打开应用 (http://localhost:3000)
   │
2. 创建项目
   │
3. 上传文档 (PDF/DOCX/XLSX)
   │
4. 系统自动解析
   │
5. 添加/编辑章节
   │
6. 查看操作日志
   │
7. 导出报告（未来功能）
```

### 数据流

```
上传文件
   ↓
[DocumentUpload] → POST /api/documents/{id}/upload
   ↓
[Backend] 保存文件，触发解析
   ↓
[DocumentProcessor] 提取文本
   ↓
更新数据库
   ↓
[ActionLog] 记录操作
   ↓
前端刷新显示
```

---

## 📊 项目规模

### 代码统计

| 组件 | 文件数 | 代码行数 | 语言 |
|------|-------|---------|------|
| 后端 API | 6 | ~1200 | Python |
| 前端应用 | 6 | ~1500 | TypeScript/JSX |
| 配置文件 | 8 | ~300 | Various |
| 文档 | 7 | ~1500 | Markdown |
| **总计** | **27** | **~4500** | - |

### 功能覆盖

- ✅ **阶段 1**: 项目和文档管理
- ✅ **阶段 2**: 动态结构树
- ⏳ **阶段 3**: 协同编辑（TipTap）
- ⏳ **阶段 4**: AI 助手（Kimi API）

---

## 🔧 常见任务

### 启动应用

```bash
# 终端 1 - 后端
cd backend
python main.py

# 终端 2 - 前端
cd frontend
npm run dev

# 浏览器打开
http://localhost:3000
```

### 查看 API 文档

http://localhost:8000/docs

### 重置数据库

```bash
# 删除数据库文件
rm backend/csr.db

# 重启后端自动重建
cd backend
python main.py
```

### 运行测试

```bash
# Windows
test_api.bat

# Linux/macOS
bash test_api.sh
```

### 安装新依赖

```bash
# Python 依赖
cd backend
pip install <package>
pip freeze > requirements.txt

# Node 依赖
cd frontend
npm install <package>
```

---

## 🐛 故障排查

### 常见问题

| 问题 | 解决方案 |
|------|---------|
| 后端无法启动 | 检查 Python 版本 (3.9+) 和依赖安装 |
| 前端无法启动 | 检查 Node.js 版本 (18+) 和 npm 依赖 |
| API 连接失败 | 确保两个服务都在运行，检查防火墙 |
| 数据库错误 | 删除 `csr.db` 并重启后端 |
| 上传失败 | 检查 `uploads/` 目录权限 |

### 获取帮助

1. 查看 [DEVELOPMENT.md](./DEVELOPMENT.md) 中的故障排查部分
2. 检查后端日志输出
3. 打开浏览器开发者工具 (F12)
4. 查看 http://localhost:8000/docs 的 API 文档

---

## 📞 联系与支持

### 项目信息

- **项目名**: CSR GenAI (Clinical Study Report Generation)
- **类型**: Web 应用
- **技术栈**: Next.js 14 + FastAPI + SQLAlchemy
- **部署**: 本地开发（Docker 即将支持）

### 资源

- 📖 完整文档: 见上文档导航
- 🔗 API: http://localhost:8000/docs (运行时)
- 🧪 测试脚本: `test_api.bat` / `test_api.sh`

---

## ✨ 最后提醒

1. **首次使用**: 按照 [QUICKSTART.md](./QUICKSTART.md) 操作
2. **了解修复**: 阅读 [FIXES.md](./FIXES.md) 了解问题和解决方案
3. **深入开发**: 查看 [DEVELOPMENT.md](./DEVELOPMENT.md)
4. **验证功能**: 运行测试脚本或通过 UI 手动测试

**现在你准备好了！祝你使用愉快！** 🚀

---

## 📅 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0 | 2026-04-16 | 初始版本，修复所有关键问题 |

---

**最后更新**: 2026-04-16  
**维护者**: AI Assistant  
**许可**: MIT
