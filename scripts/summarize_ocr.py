from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parents[1]
def main():
    inventory=json.loads((ROOT/'knowledge_base/metadata/inventory.json').read_text(encoding='utf-8'))
    report=[];hits=[]
    for item in inventory:
        path=ROOT/'knowledge_base/raw_text'/f"{item['id']}.jsonl"
        rows=[json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
        report.append({'file':item['file'],'pages':len(rows),'ocr_pages':sum(p.get('extraction')=='ocr' for p in rows),'low_text_pages':[p['page'] for p in rows if p['characters']<40]})
        for p in rows:
            if re.search('误差.{0,2}分配|等影响|按可能性',p['text']): hits.append({'file':item['file'],**p})
    (ROOT/'knowledge_base/metadata/ocr_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    (ROOT/'knowledge_base/metadata/keyword_hits.json').write_text(json.dumps(hits,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'sources':len(report),'pages':sum(x['pages'] for x in report),'ocr_pages':sum(x['ocr_pages'] for x in report),'keyword_hit_pages':len(hits),'low_text_pages':sum(len(x['low_text_pages']) for x in report)},ensure_ascii=False))
if __name__=='__main__':main()
