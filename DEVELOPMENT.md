# CSR GenAI 系统开发指南

## 项目概览

这是一个专业的临床研究报告（CSR）智能生成平台，分为四个阶段实现。

### 项目结构

```
CSR_Program/
├── frontend/                 # Next.js 前端应用
│   ├── app/                 # 应用程序目录
│   │   ├── page.tsx         # 主页
│   │   ├── layout.tsx       # 全局布局
│   │   ├── globals.css      # 全局样式
│   │   └── projects/        # 项目相关页面
│   ├── components/          # React 组件
│   │   ├── DocumentUpload.tsx
│   │   ├── ChapterTree.tsx
│   │   └── ActionLog.tsx
│   ├── package.json
│   └── tsconfig.json
│
├── backend/                 # FastAPI 后端服务
│   ├── app/
│   │   ├── models/          # 数据模型
│   │   │   └── models.py
│   │   ├── api/             # API 路由
│   │   │   ├── projects.py
│   │   │   ├── documents.py
│   │   │   ├── chapters.py
│   │   │   └── logs.py
│   │   ├── services/        # 业务逻辑
│   │   │   └── document_processor.py
│   │   └── database.py      # 数据库配置
│   ├── main.py              # 应用入口
│   ├── requirements.txt     # Python 依赖
│   └── .env.example         # 环境变量示例
│
├── docs/                    # 项目文档
├── README.md
└── DEVELOPMENT.md
```

## 技术栈

### 前端
- **Next.js 14**: 全栈 React 框架
- **Tailwind CSS**: 样式框架
- **TypeScript**: 类型安全的 JavaScript
- **TipTap**: 协同编辑器（后续阶段）

### 后端
- **FastAPI**: 高性能 Python 框架
- **SQLAlchemy**: ORM
- **Pydantic**: 数据验证
- **PyMuPDF**: PDF 解析
- **python-docx**: Word 文档解析
- **pandas**: Excel 数据处理

## 快速启动

### 环境要求
- Node.js 18+
- Python 3.9+
- Git

### 后端启动

1. **创建 Python 虚拟环境**
   ```bash
   cd backend
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **配置环境变量**
   ```bash
   cp .env.example .env
   # 编辑 .env 文件配置（如需要）
   ```

4. **启动后端服务**
   ```bash
   python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

   后端将在 `http://localhost:8000` 运行
   API 文档: `http://localhost:8000/docs`

### 前端启动

1. **安装依赖**
   ```bash
   cd frontend
   npm install
   ```

2. **启动开发服务器**
   ```bash
   npm run dev
   ```

   前端将在 `http://localhost:3000` 运行

## 核心 API 端点

### 项目管理
- `POST /api/projects/` - 创建项目
- `GET /api/projects/{project_id}` - 获取项目
- `GET /api/projects/` - 列出项目

### 文档上传与解析（阶段 1）
- `POST /api/documents/{project_id}/upload` - 上传文档
- `POST /api/documents/{document_id}/process` - 处理文档
- `GET /api/documents/{project_id}` - 列出文档
- `DELETE /api/documents/{project_id}/{document_id}` - 删除文档

### 动态结构树（阶段 2）
- `POST /api/chapters/{project_id}` - 创建章节
- `GET /api/chapters/{project_id}/tree` - 获取目录树
- `PUT /api/chapters/{project_id}/{chapter_id}` - 更新章节
- `DELETE /api/chapters/{project_id}/{chapter_id}` - 删除章节

### 操作日志
- `GET /api/logs/{project_id}` - 获取操作日志
- `GET /api/logs/{project_id}/summary` - 获取日志摘要
- `GET /api/logs/{project_id}/search` - 搜索日志

## 开发流程

### 工作流

1. **创建项目** - 在前端创建新 CSR 项目
2. **上传文档** - 上传 Protocol、SAP、TFL 等源文档
3. **解析内容** - 系统自动解析提取文档信息
4. **管理结构** - 构建和调整 CSR 目录结构树
5. **编辑内容** - 在编辑器中编写 CSR 内容
6. **AI 辅助** - 使用 AI 助手优化和完善报告
7. **审核发布** - 最终审核和导出报告

### 阶段划分

#### 阶段 0: 项目初始化 ✅
- [x] 前后端项目结构
- [x] 基础数据模型
- [x] 项目与文件管理框架

#### 阶段 1: 文档上传与解析
- [x] 文件上传接口
- [x] PDF/DOCX/XLSX 解析
- [x] 解析状态反馈
- [ ] 高级文本提取（表格检测、OCR）
- [ ] 源文档版本控制

#### 阶段 2: 动态 CSR 结构树
- [x] 目录树 CRUD 操作
- [x] 自动导入结构模板
- [ ] 配置面板（语言、排版、去重）
- [ ] 团队协作权限管理
- [x] 完整操作日志记录

#### 阶段 3: 协同编辑与生成界面
- [ ] TipTap 编辑器集成
- [ ] 实时多人协同（WebSocket）
- [ ] 修改追踪与差异对比
- [ ] 章节与源文档互链

#### 阶段 4: Kimi CSR Assistant
- [ ] AI 对话接口
- [ ] 快捷命令触发器
- [ ] 红线/绿线差异预览
- [ ] 建议应用与审计日志

## 关键功能验证清单

### DoD (Definition of Done)

- [ ] 用户可手动增加"10.2.6 新增章节"并在编辑器中写入内容
- [ ] 操作台左下角的日志能准确记录"用户 A 修改了 10.2 章节标题"
- [ ] AI 助手能根据用户对话，将修改建议直接渲染到编辑器对比视图中

## 常见问题

### Q: 如何重置数据库？
A: 后端使用 SQLite 数据库（开发环境）。删除 `csr.db` 文件可重置：
```bash
cd backend
rm csr.db
```
重新启动后端会自动创建新数据库。

### Q: 如何切换到 PostgreSQL？
A: 修改 `.env` 文件中的 `DATABASE_URL`：
```
DATABASE_URL=postgresql://user:password@localhost/csr_db
```

### Q: 文件上传大小限制是多少？
A: 默认 50MB，可在 `backend/app/services/document_processor.py` 中修改。

## 参考资源

- [Next.js 文档](https://nextjs.org/docs)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [SQLAlchemy 文档](https://docs.sqlalchemy.org/)
- [Tailwind CSS 文档](https://tailwindcss.com/docs)

## 贡献指南

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License
