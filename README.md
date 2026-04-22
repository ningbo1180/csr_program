# CSR GenAI 系统

🚀 **专业的临床研究报告（CSR）智能生成平台**

通过整合 Protocol、SAP 和 TFLs 等主流文档，实现报告的自动化撰写、动态结构管理、实时协作以及合规性审计。

## 🎯 快速开始

⚡ **只需 5 分钟！** 请按照 [QUICKSTART.md](./QUICKSTART.md) 的步骤操作。

```bash
# 终端 1: 启动后端
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
python main.py

# 终端 2: 启动前端
cd frontend
npm install
npm run dev

# 访问应用
# 前端: http://localhost:3000
# API文档: http://localhost:8000/docs
```

## 📋 项目结构

```
CSR_Program/
├── frontend/                    # Next.js 前端应用
│   ├── app/                     # 页面和布局
│   ├── components/              # React 组件
│   └── package.json
├── backend/                     # FastAPI 后端服务
│   ├── app/
│   │   ├── models/              # 数据模型
│   │   ├── api/                 # API 路由
│   │   └── services/            # 业务逻辑
│   └── main.py
├── docs/                        # 项目文档
├── plan.md                      # 开发计划
├── QUICKSTART.md                # 快速启动指南
├── DEVELOPMENT.md               # 开发指南
└── README.md                    # 本文件
```

## 🛠 技术栈

| 层级 | 技术 | 版本 |
|------|------|------|
| **前端** | Next.js | 14.0+ |
| | Tailwind CSS | 3.3+ |
| | TypeScript | 5.0+ |
| | TipTap | 2.1+ (阶段 3) |
| **后端** | FastAPI | 0.104+ |
| | SQLAlchemy | 2.0+ |
| | Pydantic | 2.5+ |
| **数据库** | SQLite (开发) / PostgreSQL (生产) | - |
| **文档处理** | PyMuPDF, python-docx, openpyxl | Latest |

## 📚 核心功能

### ✅ 已完成（阶段 0-1）
- [x] 项目初始化与架构设计
- [x] 前后端框架搭建
- [x] 核心数据模型设计
- [x] 基础 CRUD API 框架
- [x] 支持 PDF/DOCX/XLSX 上传
- [x] 智能文档解析服务
- [x] 章节内容提取与表格数据识别

### ✅ 阶段 2：动态结构树与配置中心
- [x] 目录树 CRUD 操作
- [x] 章节层级管理
- [x] 完整操作日志
- [x] 配置中心（语言、表格方向、去重级别、超链接追踪）
- [x] 项目状态与进度统计
- [ ] 权限管理与共享

**相关端点:**
- `POST /api/chapters/{project_id}` - 创建章节
- `GET /api/chapters/{project_id}/tree` - 获取目录树（含内容）
- `PUT /api/chapters/{project_id}/{chapter_id}` - 编辑章节内容
- `GET /api/logs/{project_id}` - 查看操作日志
- `PUT /api/projects/{project_id}/config` - 更新项目配置
- `GET /api/projects/{project_id}/status` - 获取项目状态

### ✅ 阶段 3：专业工作台与章节编辑
- [x] 基于 `csr_index.html` 的专业工作台 UI（深色主题三栏布局）
- [x] 章节内容编辑器（HTML 富文本编辑）
- [x] 自动保存与手动保存
- [x] 面包屑导航与来源标注
- [ ] TipTap 编辑器集成（未来优化）
- [ ] WebSocket 实时协同
- [ ] 修改追踪与差异对比
- [ ] 源文档互链

### 🔄 阶段 4：AI 助手集成
- [x] AI 助手对话交互面板
- [x] 一键生成章节内容（模拟）
- [x] 实时生成进度展示
- [ ] Kimi API 真实集成
- [ ] 一键润色与优化
- [ ] 红线/绿线差异预览

## 🎮 使用场景

### 场景 1: 创建新 CSR 项目
```
1. 点击"新建项目"
2. 输入项目名称（如：STUDY-2024-001）
3. 进入项目工作台
```

### 场景 2: 在工作台上传和解析源文档
```
1. 进入项目工作台
2. 在左侧面板点击"添加更多文档"
3. 选择 Protocol / SAP / TFLs 文件上传
4. 系统自动解析并在左侧面板显示状态
```

### 场景 3: 在工作台构建 CSR 目录结构
```
1. 在中间面板的结构树区域输入章节号（如：10.2）和标题
2. 点击"添加章节"自动生成目录结构树
3. 点击章节在右侧编辑器中查看和编辑内容
4. 在左侧面板操作日志中查看所有修改记录
```

### 场景 4: 使用 AI 助手生成内容
```
1. 在结构树中选择一个章节
2. 在右侧 AI 助手面板点击"生成章节"
3. AI 自动生成章节内容并填充到编辑器
4. 在编辑器中查看、修改并保存内容
```

## 📊 数据库模型

### 核心表
- **projects** - 项目信息
- **documents** - 上传的源文档
- **chapters** - CSR 章节结构
- **action_logs** - 操作审计日志

## 🔗 API 文档

启动后端后，访问 **http://localhost:8000/docs** 查看完整 Swagger API 文档

### 主要分类
- `/api/projects/` - 项目管理
- `/api/documents/` - 文档处理
- `/api/chapters/` - 结构树管理
- `/api/logs/` - 操作日志查询

## 🧪 测试验证清单

### DoD (完成标准)

- [x] **可创建新章节**: 用户可手动增加章节并在编辑器中写入内容
- [x] **操作日志记录**: 操作台日志能准确记录所有章节修改和文档上传操作
- [x] **AI 章节生成**: AI 助手可一键生成章节内容并自动填充到编辑器
- [ ] **AI 差异预览**: AI 助手建议可在差异视图中展示，支持一键应用

## 💡 开发指南

详见 [DEVELOPMENT.md](./DEVELOPMENT.md)

关键命令：
```bash
# 后端数据库重置（开发环境）
cd backend && rm csr.db

# 前端调试
npm run dev -- --debug

# 后端热重载
python main.py
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📝 许可证

MIT License

## 📞 支持

- 📖 完整文档: [DEVELOPMENT.md](./DEVELOPMENT.md)
- ⚡ 快速开始: [QUICKSTART.md](./QUICKSTART.md)
- 📋 开发计划: [plan.md](./plan.md)

## 👤 联系作者

如有问题，请联系作者：

- 📧 邮箱：50955438@qq.com
- 💬 微信：50955438

---

**最后更新**: 2026 年 4 月 22 日

**当前阶段**: 阶段 0-3 ✅ | 阶段 4 🔄
