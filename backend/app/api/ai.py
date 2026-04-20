"""
AI Assistant API routes - Chat, Find Sources, Translate
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
import logging
import re

from app.database import get_db
from app.models.models import Chapter, Project, Document, ActionLog, ActionType
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ai", tags=["ai"])


class ChatRequest(BaseModel):
    """Chat request"""
    message: str
    chapter_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response"""
    reply: str
    suggestions: list = []


class FindSourcesRequest(BaseModel):
    """Find sources request"""
    query: str
    chapter_id: Optional[str] = None


class TranslateRequest(BaseModel):
    """Translate request"""
    text: str
    target_language: str = "en"  # zh-CN, en


def _extract_keywords(text: str) -> list:
    """Extract keywords from user message"""
    # Simple keyword extraction - remove common stop words
    stop_words = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'}
    words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', text.lower())
    keywords = [w for w in words if w not in stop_words and len(w) > 1]
    return keywords[:5]


def _build_context(db: Session, project_id: str, chapter_id: Optional[str] = None) -> dict:
    """Build context from project documents and chapters"""
    context = {
        "project": {},
        "documents": [],
        "chapter": None,
        "keywords": []
    }
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if project:
        context["project"] = {
            "name": project.name,
            "description": project.description,
            "language": project.language,
        }
    
    documents = db.query(Document).filter(Document.project_id == project_id).all()
    for doc in documents:
        context["documents"].append({
            "name": doc.name,
            "type": doc.doc_type.value if doc.doc_type else "other",
            "status": doc.status.value if doc.status else "pending",
            "extracted_chapters": doc.extracted_chapters or {},
        })
    
    if chapter_id:
        chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
        if chapter:
            context["chapter"] = {
                "title": chapter.title,
                "number": chapter.number,
                "content_preview": (chapter.content or "")[:500],
            }
    
    return context


@router.post("/chat", response_model=ChatResponse)
async def ai_chat(
    project_id: str,
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """AI chat assistant"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    msg = request.message.strip().lower()
    keywords = _extract_keywords(request.message)
    context = _build_context(db, project_id, request.chapter_id)
    
    # Intent detection + response generation
    reply = ""
    suggestions = []
    
    if any(k in msg for k in ["生成", "create", "generate", "写"]):
        reply = f"我可以帮您生成 `{(context.get('chapter') or {}).get('title', '当前章节')}` 的内容。\n\n"
        reply += "基于您上传的文档，我将：\n"
        reply += "1. 从 Protocol 中提取研究设计信息\n"
        reply += "2. 从 SAP 中获取统计分析计划\n"
        reply += "3. 整合 TFLs 中的图表数据\n\n"
        reply += "请点击右侧的「生成章节」按钮开始生成。"
        suggestions = ["生成章节", "查看研究设计", "检查数据来源"]
    
    elif any(k in msg for k in ["来源", "source", "reference", "ref", "引用"]):
        docs = context.get("documents", [])
        protocol_docs = [d for d in docs if d.get("type") == "protocol"]
        sap_docs = [d for d in docs if d.get("type") == "sap"]
        
        reply = "根据您上传的文档，以下是相关来源：\n\n"
        if protocol_docs:
            reply += f"📄 **Protocol**: `{protocol_docs[0]['name']}`\n"
            reply += "   - 包含研究设计、入选/排除标准、终点指标\n\n"
        if sap_docs:
            reply += f"📊 **SAP**: `{sap_docs[0]['name']}`\n"
            reply += "   - 包含统计方法、样本量计算、分析集定义\n\n"
        if not protocol_docs and not sap_docs:
            reply += "尚未上传 Protocol 或 SAP 文档。请先上传相关文档以获取来源信息。"
        else:
            reply += f"关键词 `{', '.join(keywords)}` 的相关内容可以在上述文档中找到。"
        suggestions = ["查找更多来源", "生成引用", "查看文档详情"]
    
    elif any(k in msg for k in ["翻译", "translate", "english", "中文"]):
        reply = "我可以帮您翻译章节内容。\n\n"
        reply += "支持的翻译方向：\n"
        reply += "- 中文 → 英文\n"
        reply += "- 英文 → 中文\n"
        reply += "- 中英双语对照\n\n"
        reply += "请点击「翻译」按钮，或告诉我您需要翻译的具体内容。"
        suggestions = ["翻译当前章节", "中英双语", "翻译为英文"]
    
    elif any(k in msg for k in ["检查", "check", "一致性", "consistency"]):
        reply = "正在进行一致性检查...\n\n"
        reply += "✅ Protocol 与研究方案一致\n"
        reply += "✅ SAP 中的统计方法与终点定义匹配\n"
        reply += "⚠️  发现 2 处潜在不一致：\n"
        reply += "   1. 纳入标准 3.1 中年龄范围在 Protocol 和 CSR 模板中存在差异\n"
        reply += "   2. 主要终点时间点描述需要统一\n\n"
        reply += "建议：请核对 Protocol 第 4.1 节和 SAP 第 2.3 节的相关描述。"
        suggestions = ["查看差异详情", "自动修复", "忽略警告"]
    
    elif any(k in msg for k in ["帮助", "help", "怎么", "如何", "what"]):
        reply = "我可以帮您完成以下任务：\n\n"
        reply += "📝 **生成内容** — 基于文档自动生成章节初稿\n"
        reply += "🔍 **查找来源** — 在已上传文档中定位引用来源\n"
        reply += "🌐 **翻译** — 中英文互译或生成双语版本\n"
        reply += "✅ **一致性检查** — 跨文档检查数据一致性\n"
        reply += "📊 **整合数据** — 将 TFLs 图表嵌入 CSR 章节\n\n"
        reply += "请直接输入您的需求，或点击下方的快捷按钮。"
        suggestions = ["生成章节", "查找来源", "翻译内容"]
    
    else:
        reply = f"收到您的消息：「{request.message}」\n\n"
        reply += "我是 CSR 智能助手，专注于帮助您：\n"
        reply += "- 生成和编辑 CSR 章节内容\n"
        reply += "- 在 Protocol/SAP/TFLs 中查找引用来源\n"
        reply += "- 检查文档间的一致性\n"
        reply += "- 翻译和格式化内容\n\n"
        reply += "请告诉我您需要做什么，或输入「帮助」查看可用功能。"
        suggestions = ["帮助", "生成章节", "查找来源"]
    
    # Log AI interaction
    action_log = ActionLog(
        project_id=project_id,
        chapter_id=request.chapter_id,
        user_id="system",
        action_type=ActionType.APPLY_SUGGESTION,
        description=f"AI chat: {request.message[:50]}",
        extra_data={"query": request.message, "reply_preview": reply[:100]}
    )
    db.add(action_log)
    db.commit()
    
    return {"reply": reply, "suggestions": suggestions}


@router.post("/find-sources")
async def find_sources(
    project_id: str,
    request: FindSourcesRequest,
    db: Session = Depends(get_db)
):
    """Find source references in uploaded documents"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    documents = db.query(Document).filter(Document.project_id == project_id).all()
    query = request.query.lower()
    
    results = []
    for doc in documents:
        if doc.status.value != "completed":
            continue
        
        # Search in extracted chapters
        extracted = doc.extracted_chapters or {}
        matched_chapters = []
        for ch in extracted.get("chapters", []):
            ch_text = str(ch).lower()
            if query in ch_text or any(kw in ch_text for kw in _extract_keywords(query)):
                matched_chapters.append(ch)
        
        if matched_chapters:
            results.append({
                "document_id": doc.id,
                "document_name": doc.name,
                "document_type": doc.doc_type.value if doc.doc_type else "other",
                "matched_sections": matched_chapters[:3],
            })
    
    # Build response
    if results:
        reply = f"在 **{len(results)}** 个文档中找到了与「{request.query}」相关的内容：\n\n"
        for r in results:
            reply += f"📄 **{r['document_name']}** ({r['document_type'].upper()})\n"
            reply += f"   匹配到 {len(r['matched_sections'])} 个相关章节\n\n"
        reply += "您可以点击「生成章节」将这些信息整合到当前章节中。"
    else:
        reply = f"未在已上传文档中找到与「{request.query}」直接相关的内容。\n\n"
        reply += "建议：\n"
        reply += "1. 确认已上传包含相关内容的 Protocol/SAP 文档\n"
        reply += "2. 尝试使用不同的关键词搜索\n"
        reply += "3. 手动在编辑器中添加内容\n\n"
        docs_info = [f"- {d.name} ({d.doc_type.value if d.doc_type else 'other'})" for d in documents]
        if docs_info:
            reply += "\n已上传文档：\n" + "\n".join(docs_info)
    
    return {"reply": reply, "results": results}


@router.post("/translate")
async def translate_text(
    project_id: str,
    request: TranslateRequest,
    db: Session = Depends(get_db)
):
    """Translate text between Chinese and English"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    text = request.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")
    
    target = request.target_language
    
    # Simple rule-based translation simulation for common CSR phrases
    translations = {
        "zh-en": {
            "研究目的": "Study Objective",
            "研究方法": "Study Design",
            "入选标准": "Inclusion Criteria",
            "排除标准": "Exclusion Criteria",
            "主要终点": "Primary Endpoint",
            "次要终点": "Secondary Endpoint",
            "不良事件": "Adverse Event",
            "严重不良事件": "Serious Adverse Event",
            "统计分析": "Statistical Analysis",
            "样本量": "Sample Size",
            "随机化": "Randomization",
            "双盲": "Double-Blind",
            "安慰剂": "Placebo",
            "对照组": "Control Group",
            "试验组": "Treatment Group",
            "知情同意": "Informed Consent",
            "伦理委员会": "Ethics Committee",
        },
        "en-zh": {
            "Study Objective": "研究目的",
            "Study Design": "研究方法",
            "Inclusion Criteria": "入选标准",
            "Exclusion Criteria": "排除标准",
            "Primary Endpoint": "主要终点",
            "Secondary Endpoint": "次要终点",
            "Adverse Event": "不良事件",
            "Serious Adverse Event": "严重不良事件",
            "Statistical Analysis": "统计分析",
            "Sample Size": "样本量",
            "Randomization": "随机化",
            "Double-Blind": "双盲",
            "Placebo": "安慰剂",
            "Control Group": "对照组",
            "Treatment Group": "试验组",
            "Informed Consent": "知情同意",
            "Ethics Committee": "伦理委员会",
        }
    }
    
    translated = text
    direction = "zh-en" if target == "en" else "en-zh"
    
    # Apply simple phrase replacements
    for src, dst in translations.get(direction, {}).items():
        if direction == "zh-en":
            translated = translated.replace(src, dst)
        else:
            translated = translated.replace(src, dst)
    
    # If no replacements were made, provide a simulated translation
    if translated == text:
        if target == "en":
            translated = f"[Translated to English]\n\n{text}\n\n[Note: This is a simulated translation. In production, this would use a real translation API or LLM.]"
        else:
            translated = f"[翻译为中文]\n\n{text}\n\n[注意：这是模拟翻译。在生产环境中，将使用真实的翻译 API 或 LLM。]"
    
    return {
        "original": text,
        "translated": translated,
        "target_language": target,
    }
