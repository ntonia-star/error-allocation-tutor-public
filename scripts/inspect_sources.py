"""Read-only source inventory and page extraction. Original documents are never modified."""
from pathlib import Path
import hashlib, json, re
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'knowledge_base'
for folder in ('raw_text', 'metadata', 'structured_knowledge', 'chunks', 'index', 'review'):
    (OUT / folder).mkdir(parents=True, exist_ok=True)

def main():
    inventory, hits = [], []
    roots = [ROOT / name for name in ('knowledge_source', 'knowledge_sourse') if (ROOT / name).exists()]
    for source in sorted({p for root in roots for p in root.rglob('*') if p.suffix.lower() in ('.pdf', '.ppt', '.pptx')}):
        sid = hashlib.sha256(source.read_bytes()).hexdigest()[:16]
        entry = {'id':sid, 'file':source.relative_to(ROOT).as_posix(), 'bytes':source.stat().st_size,
                 'sha256':hashlib.sha256(source.read_bytes()).hexdigest(), 'pages':[], 'issues':[]}
        if source.suffix.lower() == '.pdf':
            reader = PdfReader(source)
            for n, page in enumerate(reader.pages, 1):
                try: text = page.extract_text() or ''
                except Exception as exc:
                    text = ''; entry['issues'].append({'page': n, 'issue':type(exc).__name__})
                row = {'page':n, 'text':text, 'characters':len(text.strip())}
                entry['pages'].append({'page':n, 'characters':len(text.strip())})
                if len(text.strip()) < 40: entry['issues'].append({'page':n,'issue':'文本稀少，需图像/OCR检查'})
                if re.search(r'误差\s*分配|等作用|等精度',text):
                    hits.append({'file':entry['file'], **row})
                with (OUT/'raw_text'/f'{sid}.jsonl').open('a' if n > 1 else 'w',encoding='utf-8') as f:
                    f.write(json.dumps(row,ensure_ascii=False)+'\n')
        elif source.suffix.lower() == '.pptx':
            from pptx import Presentation
            slides = []
            for n, slide in enumerate(Presentation(source).slides, 1):
                text = '\n'.join(shape.text for shape in slide.shapes if shape.has_text_frame)
                slides.append({'page': n,'text':text,'characters':len(text)})
                entry['pages'].append({'page':n,'characters':len(text)})
                entry['issues'].append({'page':n,'issue':'图片、公式、表格需人工核验'})
            (OUT/'raw_text'/f'{sid}.jsonl').write_text('\n'.join(json.dumps(p,ensure_ascii=False) for p in slides),encoding='utf-8')
        else:
            entry['issues'].append({'issue':'旧版PPT需先用Office/LibreOffice转换为PPTX；未自动猜测内容'})
        inventory.append(entry)
        print(source.name, 'pages=',len(entry['pages']), 'sparse=',len(entry['issues']),flush=True)
    (OUT/'metadata'/'inventory.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'metadata'/'keyword_hits.json').write_text(json.dumps(hits,ensure_ascii=False,indent=2),encoding='utf-8')
    print('keyword hits=',len(hits))

if __name__ == '__main__': main()
