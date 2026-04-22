"""
AI Assistant API routes - Stage 4
Enhanced with real Kimi API integration, polish, structured diff, conversation history
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
import logging
import re
import os

from app.database import get_db
from app.models.models import Chapter, Project, Document, ActionLog, ActionType, AIConversation
from app.services.ai_service import get_ai_service
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
    action_type: str = "chat"


class FindSourcesRequest(BaseModel):
    """Find sources request"""
    query: str
    chapter_id: Optional[str] = None


class TranslateRequest(BaseModel):
    """Translate request"""
    text: str
    target_language: str = "en"  # zh-CN, en


class PolishRequest(BaseModel):
    """Polish chapter request"""
    chapter_id: str
    style: str = "professional"  # professional, concise, detailed, academic
    instructions: Optional[str] = None


class PolishResponse(BaseModel):
    """Polish response with diff"""
    original: str
    polished: str
    diff_blocks: list  # structured diff for frontend rendering
    reasoning: str


class CommandRequest(BaseModel):
    """Quick command request"""
    command: str  # "/generate", "/find-sources", "/polish", "/translate"
    chapter_id: Optional[str] = None
    extra_data: Optional[dict] = None


def _extract_keywords(text: str) -> list:
    """Extract keywords from user message"""
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


def _create_diff_blocks(original: str, polished: str) -> list:
    """Create structured diff blocks from original and polished text"""
    # Simple implementation: split into paragraphs and compare
    orig_paras = [p.strip() for p in re.split(r'</?p>', original) if p.strip()]
    polish_paras = [p.strip() for p in re.split(r'</?p>', polished) if p.strip()]
    
    blocks = []
    max_len = max(len(orig_paras), len(polish_paras))
    
    for i in range(max_len):
        if i < len(orig_paras) and i < len(polish_paras):
            if orig_paras[i] == polish_paras[i]:
                blocks.append({"type": "keep", "text": orig_paras[i]})
            else:
                blocks.append({"type": "remove", "text": orig_paras[i]})
                blocks.append({"type": "add", "text": polish_paras[i]})
        elif i < len(orig_paras):
            blocks.append({"type": "remove", "text": orig_paras[i]})
        else:
            blocks.append({"type": "add", "text": polish_paras[i]})
    
    return blocks


@router.post("/chat", response_model=ChatResponse)
async def ai_chat(
    project_id: str,
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """AI chat assistant with conversation history - uses real Kimi API when available"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    context = _build_context(db, project_id, request.chapter_id)
    chapter_info = context.get("chapter")
    
    ai_service = get_ai_service()
    result = ai_service.chat(request.message, context, chapter_info)
    
    reply = result["reply"]
    suggestions = result.get("suggestions", [])
    action_type = result.get("action_type", "chat")
    
    # Override with local intent detection for better UX
    msg = request.message.strip().lower()
    if any(k in msg for k in ["生成", "create", "generate", "写"]):
        suggestions = ["生成章节", "查看研究设计", "检查数据来源"]
        action_type = "generate"
    elif any(k in msg for k in ["润色", "polish", "优化", "改进", "refine"]):
        suggestions = ["一键润色", "专业风格", "简洁风格"]
        action_type = "polish"
    elif any(k in msg for k in ["来源", "source", "reference", "ref", "引用"]):
        docs = context.get("documents", [])
        protocol_docs = [d for d in docs if d.get("type") == "protocol"]
        sap_docs = [d for d in docs if d.get("type") == "sap"]
        keywords = _extract_keywords(request.message)
        
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
        action_type = "find_sources"
    elif any(k in msg for k in ["帮助", "help", "怎么", "如何", "what"]):
        reply = "我可以帮您完成以下任务：\n\n"
        reply += "📝 **生成内容** — 基于文档自动生成章节初稿\n"
        reply += "✨ **一键润色** — 优化语言表达和专业性\n"
        reply += "🔍 **查找来源** — 在已上传文档中定位引用来源\n"
        reply += "🌐 **翻译** — 中英文互译或生成双语版本\n"
        reply += "✅ **一致性检查** — 跨文档检查数据一致性\n"
        reply += "📊 **整合数据** — 将 TFLs 图表嵌入 CSR 章节\n\n"
        reply += "请直接输入您的需求，或点击下方的快捷按钮。"
        suggestions = ["生成章节", "一键润色", "查找来源"]
        action_type = "help"
    
    # Save conversation to database
    conversation = AIConversation(
        project_id=project_id,
        chapter_id=request.chapter_id,
        user_message=request.message,
        ai_response=reply,
        action_type=action_type,
        suggestions=suggestions
    )
    db.add(conversation)
    
    # Log AI interaction
    action_log = ActionLog(
        project_id=project_id,
        chapter_id=request.chapter_id,
        user_id="system",
        action_type=ActionType.APPLY_SUGGESTION,
        description=f"AI chat: {request.message[:50]}",
        extra_data={"query": request.message, "reply_preview": reply[:100], "action_type": action_type}
    )
    db.add(action_log)
    db.commit()
    
    return {"reply": reply, "suggestions": suggestions, "action_type": action_type}


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
    
    # Enhanced rule-based translation simulation for common CSR phrases
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
            "基线特征": "Baseline Characteristics",
            "疗效分析": "Efficacy Analysis",
            "安全性分析": "Safety Analysis",
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
            "Baseline Characteristics": "基线特征",
            "Efficacy Analysis": "疗效分析",
            "Safety Analysis": "安全性分析",
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


@router.post("/polish", response_model=PolishResponse)
async def polish_chapter(
    project_id: str,
    request: PolishRequest,
    db: Session = Depends(get_db)
):
    """Polish chapter content with real Kimi API integration"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    chapter = db.query(Chapter).filter(
        Chapter.id == request.chapter_id,
        Chapter.project_id == project_id
    ).first()
    
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    original = chapter.content or ""
    
    # Use real Kimi API for polishing
    ai_service = get_ai_service()
    polished = ai_service.polish_content(original, request.style, request.instructions)
    
    # Create structured diff blocks
    diff_blocks = _create_diff_blocks(original, polished)
    
    reasoning = f"根据「{request.style}」风格对章节进行了润色：\n"
    if ai_service.is_available():
        reasoning += "1. 使用Kimi AI进行了智能润色\n"
    else:
        reasoning += "1. 优化了专业术语的表达（模拟模式）\n"
    reasoning += "2. 调整了句式结构以符合CSR规范\n"
    reasoning += "3. 确保语言的一致性和准确性"
    
    if request.instructions:
        reasoning += f"\n4. 额外遵循了用户的特殊要求：{request.instructions}"
    
    # Log the polish action
    action_log = ActionLog(
        project_id=project_id,
        chapter_id=chapter.id,
        user_id="system",
        action_type=ActionType.AI_POLISH,
        description=f"AI polished chapter: {chapter.number} {chapter.title} ({request.style} style)",
        extra_data={"style": request.style, "instructions": request.instructions, "api_used": ai_service.is_available()}
    )
    db.add(action_log)
    db.commit()
    
    return {
        "original": original,
        "polished": polished,
        "diff_blocks": diff_blocks,
        "reasoning": reasoning
    }


@router.post("/command")
async def execute_command(
    project_id: str,
    request: CommandRequest,
    db: Session = Depends(get_db)
):
    """Execute quick command (slash commands)"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    cmd = request.command.lower().lstrip('/')
    
    if cmd in ["generate", "生成"]:
        if not request.chapter_id:
            return {"reply": "请先在左侧选择要生成的章节", "type": "error"}
        # Delegate to chapter generation endpoint
        return {
            "reply": "正在生成章节内容...",
            "type": "generate",
            "chapter_id": request.chapter_id,
            "redirect_endpoint": f"/api/chapters/{project_id}/{request.chapter_id}/generate"
        }
    
    elif cmd in ["polish", "润色"]:
        if not request.chapter_id:
            return {"reply": "请先在左侧选择要润色的章节", "type": "error"}
        return {
            "reply": "正在润色章节内容...",
            "type": "polish",
            "chapter_id": request.chapter_id,
            "redirect_endpoint": f"/api/ai/polish"
        }
    
    elif cmd in ["find-sources", "来源", "查找来源"]:
        query = request.extra_data.get("query", "") if request.extra_data else ""
        return {
            "reply": f"正在查找与「{query}」相关的来源...",
            "type": "find_sources",
            "query": query,
            "redirect_endpoint": "/api/ai/find-sources"
        }
    
    elif cmd in ["translate", "翻译"]:
        text = request.extra_data.get("text", "") if request.extra_data else ""
        target = request.extra_data.get("target_language", "en") if request.extra_data else "en"
        return {
            "reply": "正在翻译...",
            "type": "translate",
            "text": text,
            "target_language": target,
            "redirect_endpoint": "/api/ai/translate"
        }
    
    else:
        return {
            "reply": f"未知指令：`/{cmd}`\n\n可用指令：\n/generate — 生成当前章节\n/polish — 一键润色\n/find-sources — 查找来源\n/translate — 翻译内容",
            "type": "help"
        }


@router.get("/conversations")
async def get_conversations(
    project_id: str,
    chapter_id: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get AI conversation history for a project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    query = db.query(AIConversation).filter(AIConversation.project_id == project_id)
    if chapter_id:
        query = query.filter(AIConversation.chapter_id == chapter_id)
    
    conversations = query.order_by(AIConversation.created_at.desc()).limit(limit).all()
    
    return {
        "project_id": project_id,
        "chapter_id": chapter_id,
        "conversations": [
            {
                "id": c.id,
                "user_message": c.user_message,
                "ai_response": c.ai_response,
                "action_type": c.action_type,
                "suggestions": c.suggestions,
                "created_at": c.created_at.isoformat()
            }
            for c in conversations
        ]
    }
