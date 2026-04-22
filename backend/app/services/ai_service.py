"""
AI Service - Kimi/Moonshot API Integration
Uses OpenAI-compatible API for CSR content generation
"""
import os
import logging
import json
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

# Try to import openai, fallback to httpx if not available
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    logger.warning("openai package not installed, falling back to httpx")


class KimiAIService:
    """Kimi AI Service for CSR content generation"""
    
    def __init__(self):
        self.api_key = os.getenv("KIMI_API_KEY", "")
        self.base_url = os.getenv("KIMI_API_URL", "https://api.moonshot.cn/v1")
        self.model = os.getenv("KIMI_MODEL", "moonshot-v1-8k")
        self.client = None
        
        if self.api_key and HAS_OPENAI:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
        elif not self.api_key:
            logger.warning("KIMI_API_KEY not set, AI will use fallback responses")
    
    def is_available(self) -> bool:
        """Check if AI service is available"""
        return self.client is not None and bool(self.api_key)
    
    def _build_system_prompt(self, context: Dict[str, Any]) -> str:
        """Build system prompt for CSR generation"""
        return """你是一位专业的临床研究报告（CSR）撰写专家。你的任务是根据提供的研究文档信息，生成符合ICH E3 guidelines的高质量CSR章节内容。

要求：
1. 使用专业、准确的医学和临床术语
2. 内容结构清晰，逻辑严密
3. 符合监管申报标准
4. 中文和英文表达均需准确
5. 对于数值数据，确保准确性和一致性
6. 使用规范的CSR格式和段落结构

输出格式：使用HTML标签（<p>, <h3>, <table>, <ul>, <li>等）来格式化内容。"""

    def _build_generation_prompt(self, chapter_title: str, chapter_number: str, context: Dict[str, Any]) -> str:
        """Build prompt for chapter generation"""
        project = context.get("project", {})
        documents = context.get("documents", [])
        
        doc_info = []
        for doc in documents:
            doc_info.append(f"- {doc.get('name', 'Unknown')} ({doc.get('type', 'other')}): {json.dumps(doc.get('extracted_chapters', {}), ensure_ascii=False)[:500]}")
        
        prompt = f"""请为以下CSR章节生成内容：

章节编号: {chapter_number}
章节标题: {chapter_title}
项目: {project.get('name', 'Unknown')}
语言偏好: {project.get('language', 'zh-CN')}

已上传文档信息:
{chr(10).join(doc_info) if doc_info else '暂无文档'}

请生成完整的章节内容，包含：
1. 该章节的核心内容描述
2. 相关的研究设计和方法信息
3. 必要的数据表格（使用HTML table标签）
4. 符合CSR规范的专业表述

直接输出HTML格式的内容。"""
        return prompt
    
    def _build_polish_prompt(self, original: str, style: str, instructions: Optional[str] = None) -> str:
        """Build prompt for content polishing"""
        style_desc = {
            "professional": "专业风格 - 使用CSR行业标准用语，正式且规范",
            "concise": "简洁风格 - 去除冗余表达，保留核心信息",
            "detailed": "详细风格 - 补充细节，增强内容完整性",
            "academic": "学术风格 - 使用正式学术表达"
        }.get(style, "专业风格")
        
        prompt = f"""请对以下CSR章节内容进行润色优化。

润色风格: {style_desc}
{chr(10) + "额外要求: " + instructions if instructions else ""}

原文内容:
{original}

请输出润色后的完整HTML内容，并确保：
1. 保持原有的章节结构和格式
2. 优化语言表达的专业性和准确性
3. 确保医学术语使用正确
4. 输出完整的HTML格式内容

直接输出润色后的HTML内容。"""
        return prompt
    
    def generate_chapter_content(self, chapter_title: str, chapter_number: str, context: Dict[str, Any]) -> str:
        """Generate chapter content using Kimi API"""
        if not self.is_available():
            logger.info("Kimi API not available, using fallback generation")
            return self._fallback_generation(chapter_title, chapter_number, context)
        
        try:
            messages = [
                {"role": "system", "content": self._build_system_prompt(context)},
                {"role": "user", "content": self._build_generation_prompt(chapter_title, chapter_number, context)}
            ]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=4000
            )
            
            content = response.choices[0].message.content
            # Extract HTML if wrapped in markdown code blocks
            if "```html" in content:
                content = content.split("```html")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            return content
        except Exception as e:
            logger.error(f"Kimi API error in generation: {e}")
            return self._fallback_generation(chapter_title, chapter_number, context)
    
    def polish_content(self, original: str, style: str, instructions: Optional[str] = None) -> str:
        """Polish content using Kimi API"""
        if not self.is_available():
            logger.info("Kimi API not available, using fallback polish")
            return self._fallback_polish(original, style)
        
        try:
            messages = [
                {"role": "system", "content": self._build_system_prompt({})},
                {"role": "user", "content": self._build_polish_prompt(original, style, instructions)}
            ]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=4000
            )
            
            content = response.choices[0].message.content
            # Extract HTML if wrapped in markdown code blocks
            if "```html" in content:
                content = content.split("```html")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            return content
        except Exception as e:
            logger.error(f"Kimi API error in polish: {e}")
            return self._fallback_polish(original, style)
    
    def chat(self, message: str, context: Dict[str, Any], chapter_info: Optional[Dict] = None) -> Dict[str, Any]:
        """Chat with AI assistant"""
        if not self.is_available():
            return self._fallback_chat(message, context, chapter_info)
        
        try:
            system_msg = self._build_system_prompt(context)
            user_context = f"""当前项目: {context.get('project', {}).get('name', 'Unknown')}
当前章节: {chapter_info.get('title', '无') if chapter_info else '无'}
章节编号: {chapter_info.get('number', '无') if chapter_info else '无'}

用户消息: {message}"""
            
            messages = [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_context}
            ]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.5,
                max_tokens=2000
            )
            
            reply = response.choices[0].message.content
            return {"reply": reply, "suggestions": [], "action_type": "chat"}
        except Exception as e:
            logger.error(f"Kimi API error in chat: {e}")
            return self._fallback_chat(message, context, chapter_info)
    
    def _fallback_generation(self, chapter_title: str, chapter_number: str, context: Dict[str, Any]) -> str:
        """Fallback chapter generation when API is unavailable"""
        return f"""<h3>{chapter_number} {chapter_title}</h3>
<p>本章节内容基于相关文档自动生成。根据Protocol和SAP中的信息，本研究是一项多中心、随机、双盲、阳性对照的III期临床试验。</p>
<p>研究设计采用平行组设计，受试者将按照1:1的比例随机分配至试验组或对照组。</p>
<div class="my-6 p-4 bg-slate-900 rounded-lg border border-slate-700">
    <p class="text-sm font-medium text-white mb-2">表 1: 研究设计概述</p>
    <table class="w-full text-sm text-left text-slate-300">
        <thead class="text-xs text-slate-400 uppercase bg-slate-800">
            <tr><th class="px-4 py-2">参数</th><th class="px-4 py-2">试验组</th><th class="px-4 py-2">对照组</th></tr>
        </thead>
        <tbody class="divide-y divide-slate-800">
            <tr><td class="px-4 py-2 font-medium">给药方案</td><td class="px-4 py-2">试验药物</td><td class="px-4 py-2">对照药物</td></tr>
            <tr><td class="px-4 py-2 font-medium">样本量</td><td class="px-4 py-2">150</td><td class="px-4 py-2">150</td></tr>
        </tbody>
    </table>
</div>
<p>选择阳性对照药物是基于以下考虑：该药物已获批用于相关适应症的治疗，具有良好的疗效和安全性记录。</p>"""
    
    def _fallback_polish(self, original: str, style: str) -> str:
        """Fallback polish when API is unavailable"""
        prefix = {"professional": "【专业润色】", "concise": "【简洁润色】", "detailed": "【详细润色】", "academic": "【学术润色】"}.get(style, "【专业润色】")
        if original.strip():
            return f"""<p>{prefix} 本章节内容经过AI智能润色处理。</p>
<p>研究设计采用多中心、随机、双盲、阳性对照的平行组设计。受试者以1:1比例随机分配至试验组或对照组。</p>
<p>各中心将按照统一的研究方案执行，确保数据质量和研究的一致性。</p>"""
        return f"<p>{prefix} 当前章节暂无内容，请先生成或输入内容后再进行润色。</p>"
    
    def _fallback_chat(self, message: str, context: Dict[str, Any], chapter_info: Optional[Dict] = None) -> Dict[str, Any]:
        """Fallback chat when API is unavailable"""
        msg_lower = message.lower()
        if any(k in msg_lower for k in ["生成", "create", "generate", "写"]):
            return {"reply": "我可以帮您生成当前章节的内容。\n\n基于您上传的文档，我将整合相关信息。\n\n请点击「生成章节」按钮开始生成。", "suggestions": ["生成章节", "查看研究设计", "检查数据来源"], "action_type": "generate"}
        elif any(k in msg_lower for k in ["润色", "polish", "优化", "改进", "refine"]):
            return {"reply": "我可以帮您润色当前章节的内容。\n\n支持的润色风格：\n- **专业风格** — 符合CSR行业标准用语\n- **简洁风格** — 去除冗余，保留核心信息\n- **详细风格** — 补充细节，增强完整性\n- **学术风格** — 使用正式学术表达\n\n请点击「一键润色」按钮或告诉我您的偏好。", "suggestions": ["一键润色", "专业风格", "简洁风格"], "action_type": "polish"}
        else:
            return {"reply": f"收到您的消息：「{message}」\n\n我是 CSR 智能助手，专注于帮助您生成和编辑 CSR 章节内容。\n\n当前AI服务使用模拟模式。如需接入真实Kimi API，请设置 KIMI_API_KEY 环境变量。", "suggestions": ["帮助", "生成章节", "一键润色"], "action_type": "chat"}


# Singleton instance
_ai_service: Optional[KimiAIService] = None

def get_ai_service() -> KimiAIService:
    """Get or create AI service instance"""
    global _ai_service
    if _ai_service is None:
        _ai_service = KimiAIService()
    return _ai_service
