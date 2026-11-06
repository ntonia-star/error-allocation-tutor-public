"""Chinese OCR with page provenance; outputs remain UNVERIFIED until visual review."""
from pathlib import Path
import concurrent.futures, json, subprocess, os
import pypdfium2 as pdfium
ROOT = Path(__file__).resolve().parents[1]
TESS = os.environ.get('TESSERACT_CMD', r'C:\Program Files\Tesseract-OCR\tesseract.exe')

def ocr_file(entry):
    if not entry['file'].lower().endswith('.pdf'): return
    target=ROOT/'knowledge_base/raw_text'/f"{entry['id']}.jsonl"
    pdf=pdfium.PdfDocument(ROOT/entry['file'])
    rows=[]
    for n in range(len(pdf)):
        tmp=ROOT/'tmp/pdfs'/f"{entry['id']}-{n}.png"
        pdf[n].render(scale=2).to_pil().save(tmp)
        env=dict(os.environ, OMP_THREAD_LIMIT='1')
        run=subprocess.run([TESS,str(tmp),'stdout','--tessdata-dir',str(ROOT/'tools/tessdata'),'-l','chi_sim+eng','--psm','3'],capture_output=True,env=env)
        text=run.stdout.decode('utf-8',errors='replace')
        rows.append({'page':n+1,'text':text,'characters':len(text),'extraction':'ocr','review_status':'unverified'})
        tmp.unlink(missing_ok=True)
        if n%30==0: print(entry['file'],n+1,'/',len(pdf),flush=True)
    target.write_text('\n'.join(json.dumps(r,ensure_ascii=False) for r in rows),encoding='utf-8')
    print('DONE',entry['file'],flush=True)

if __name__=='__main__':
    inventory=json.loads((ROOT/'knowledge_base/metadata/inventory.json').read_text(encoding='utf-8'))
    # All sources scanned. Parallelize separate files, never share PDF handles.
    with concurrent.futures.ProcessPoolExecutor(max_workers=4) as pool:
        list(pool.map(ocr_file,inventory))
