# 快速启动指南

> **🔧 重要更新**: 所有代码问题已修复，应用现在可以完全使用！
> 
> 详见 [FIXES.md](./FIXES.md) 了解修复详情。

## 5 分钟快速启动

### 步骤 1: 启动后端

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境（Windows）
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 启动后端
python main.py
```

**预期输出:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     CSR GenAI Backend starting up...
INFO:     Database initialized successfully
```

### 步骤 2: 启动前端（新终端窗口）

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动前端
npm run dev
```

**预期输出:**
```
 ▲ Next.js 14.x.x
 - Local:        http://localhost:3000
```

### 步骤 3: 打开浏览器

访问 `http://localhost:3000`

## 验证安装

1. **后端 API 文档**: 访问 `http://localhost:8000/docs`
2. **前端应用**: 访问 `http://localhost:3000`

## 测试工作流

### 1. 创建项目
```bash
curl -X POST http://localhost:8000/api/projects/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Project", "description": "Testing CSR GenAI"}'
```

### 2. 获取项目 ID
记下返回的 `id`，用于后续操作。

### 3. 上传文档
使用前端界面上传一个 PDF、DOCX 或 XLSX 文件。

### 4. 查看操作日志
访问 `http://localhost:3000/projects/{project_id}` 并点击"操作日志"标签。

## 故障排查

### 后端无法启动
```bash
# 检查 Python 版本
python --version  # 应该是 3.9+

# 检查依赖安装
pip list | grep -E 'fastapi|uvicorn|sqlalchemy'
```

### 前端无法启动
```bash
# 检查 Node.js 版本
node --version  # 应该是 18+

# 清除缓存并重新安装
rm -rf node_modules
npm install
```

### 端口被占用
```bash
# 后端使用不同端口
python main.py --port 8001

# 前端使用不同端口
npm run dev -- -p 3001
```

## 下一步

1. 阅读 [DEVELOPMENT.md](./DEVELOPMENT.md) 获取完整开发指南
2. 查看原始 [plan.md](./plan.md) 了解项目愿景
3. 探索 API: http://localhost:8000/docs

## 获取帮助

- 检查日志文件中的错误信息
- 确保防火墙允许 8000 和 3000 端口访问
- 检查 `.env` 配置（如需要）

祝你使用愉快！🚀
