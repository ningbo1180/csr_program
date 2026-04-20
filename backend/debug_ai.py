import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from app.database import SessionLocal
from app.models.models import Project

db = SessionLocal()
try:
    project = db.query(Project).filter(Project.id == '9dc73812-a00f-4feb-a697-e381fd8aa791').first()
    print('project:', project.name if project else 'NOT FOUND')
    
    # Test import of ai module
    from app.api import ai
    print('ai module imported OK')
    
    # Test _build_context
    ctx = ai._build_context(db, '9dc73812-a00f-4feb-a697-e381fd8aa791')
    print('context docs:', len(ctx['documents']))
    
    # Test chat
    from pydantic import BaseModel
    class FakeReq(BaseModel):
        message: str = '帮我生成章节'
        chapter_id: str = None
    
    import asyncio
    async def test():
        result = await ai.ai_chat('9dc73812-a00f-4feb-a697-e381fd8aa791', FakeReq(), db)
        print('result:', result)
    asyncio.run(test())
except Exception as e:
    import traceback
    traceback.print_exc()
finally:
    db.close()
