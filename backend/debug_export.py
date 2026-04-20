import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from app.database import SessionLocal
from app.api.export import _build_chapter_tree
from sqlalchemy.orm import Session

db = SessionLocal()
try:
    chapters = _build_chapter_tree(db, '9dc73812-a00f-4feb-a697-e381fd8aa791')
    print('chapters:', len(chapters))
    for ch in chapters[:3]:
        print(f"  {ch['number']} {ch['title']} level={ch['level']} content_len={len(ch['content'])}")
    
    # Test docx generation
    from docx import Document
    from docx.shared import Pt
    from docx.oxml.ns import qn
    doc = Document()
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Calibri'
    font.size = Pt(11)
    style.element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')
    print('docx font setup OK')
    
    import io
    buf = io.BytesIO()
    doc.save(buf)
    print('docx save OK')
except Exception as e:
    import traceback
    traceback.print_exc()
finally:
    db.close()
