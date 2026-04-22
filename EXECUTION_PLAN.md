# CSR GenAI 遗留模块完成执行计划

## 目标
完成阶段3（协同编辑与生成界面）和阶段4（Kimi CSR Assistant 深度集成），进行全面测试，并在本地完成部署。

---

## 阶段一：后端增强（阶段3&4支撑）

### 1.1 扩展数据库模型
- [ ] Chapter 表添加 `content_json` 字段（存储 TipTap JSON）
- [ ] 新增 `DocumentReference` 表（章节内引用文档溯源）
- [ ] 新增 `AIConversation` 表（AI对话历史持久化）
- [ ] 数据库迁移/重建

### 1.2 增强 API
- [ ] `POST /api/chapters/{id}/diff` - 对比两个版本/AI建议与当前内容
- [ ] `POST /api/ai/polish` - 一键润色章节
- [ ] `POST /api/ai/apply-diff` - 应用AI建议的修改
- [ ] `GET /api/documents/{id}/references` - 获取文档可被引用的段落
- [ ] `POST /api/chapters/{id}/references` - 添加文档引用到章节

### 1.3 真实AI集成（模拟→真实）
- [ ] 接入 Moonshot/Kimi API（用户已有环境）
- [ ] 实现结构化prompt模板
- [ ] AI生成返回 structured diff（新增/删除/修改段落）

---

## 阶段二：前端重构（阶段3 - 协同编辑）

### 2.1 集成 TipTap 编辑器
- [ ] 安装 @tiptap/react, @tiptap/starter-kit, @tiptap/extension-table, @tiptap/extension-placeholder
- [ ] 替换 CenterPanel.tsx 中的 textarea
- [ ] 实现工具栏：粗体/斜体/标题/列表/表格/链接
- [ ] 编辑器内容以 JSON/HTML 双格式保存

### 2.2 结构化交互
- [ ] 章节树点击 → 编辑器定位到对应锚点
- [ ] 编辑器内添加文档引用标记（inline reference）
- [ ] 引用标记点击 → 显示来源文档弹窗

### 2.3 修改追踪与Diff视图
- [ ] 版本历史对比：显示红线（删除）/绿线（新增）
- [ ] AI建议对比：在编辑器旁显示diff面板
- [ ] "应用修改"按钮将AI建议合并到正文

---

## 阶段三：前端增强（阶段4 - AI助手）

### 3.1 指令触发器
- [ ] 快捷指令按钮："/生成当前章节", "/查找来源", "/一键润色"
- [ ] 输入框支持 / 快捷键唤起指令菜单
- [ ] 指令解析路由到对应API

### 3.2 差异化预览
- [ ] DiffViewer 组件：双栏对比 / 内联对比模式
- [ ] AI返回的建议以diff格式展示
- [ ] "接受"/"拒绝"/"部分接受"交互

### 3.3 实时预览面板
- [ ] 实现 RightPanel 的实时预览Tab
- [ ] 预览渲染 TipTap 内容 + 应用样式
- [ ] 导出预览（模拟Word效果）

---

## 阶段四：全面测试

### 4.1 后端测试
- [ ] 新增 API 端点测试（diff, polish, apply-diff, references）
- [ ] AI集成测试（mock API响应）
- [ ] 数据库模型测试

### 4.2 前端测试
- [ ] TipTap 编辑器加载测试
- [ ] DiffViewer 渲染测试
- [ ] 指令触发器交互测试

### 4.3 集成测试
- [ ] 完整工作流：创建项目 → 上传文档 → 添加章节 → AI生成 → Diff预览 → 应用修改 → 导出
- [ ] 手动验证所有功能点

---

## 阶段五：本地部署

### 5.1 环境准备
- [ ] 后端：pip install 所有依赖
- [ ] 前端：npm install + 新增包
- [ ] 数据库初始化

### 5.2 启动服务
- [ ] 启动 FastAPI 后端（localhost:8000）
- [ ] 启动 Next.js 前端（localhost:3000）
- [ ] 验证前后端通信

### 5.3 最终验证
- [ ] 按 DoD 检查清单逐项验证
- [ ] 修复发现的问题

---

## DoD（完成标准）
1. [ ] 用户可以手动增加"10.2.6 新增章节"并成功在编辑器中写入内容
2. [ ] 操作台左下角的日志能准确记录"用户 A 修改了 10.2 章节标题"
3. [ ] AI助手能根据用户对话，将修改建议直接渲染到编辑器对比视图中
4. [ ] 所有API返回正确JSON格式
5. [ ] 前后端本地运行无报错
6. [ ] 完整工作流可手动验证通过

---

**开始执行时间**: 2026-04-22
**预计完成**: 持续执行直至全部完成
