"""Import user-curated evidence; never auto-promote raw OCR."""
from pathlib import Path
import argparse,json,re
ROOT=Path(__file__).resolve().parents[1]
def validate(rows):
    if not isinstance(rows,list):raise ValueError('知识库须为JSON数组')
    seen=set()
    for row in rows:
        if not isinstance(row,dict):raise ValueError('每条须为对象')
        ident=row.get('id','')
        if not isinstance(ident,str) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,64}',ident) or ident in seen:raise ValueError('id无效或重复')
        seen.add(ident)
        for k in ('title','category','content','formula','conditions','symbols'):
            if not isinstance(row.get(k),str):raise ValueError('缺少文本字段：'+k)
        if not row['title'].strip() or not row['content'].strip() or row.get('verified') is not True:raise ValueError('内容必须经人工核验')
        if not isinstance(row.get('related'),list) or not all(isinstance(x,str) for x in row['related']):raise ValueError('related须为ID数组')
        if not isinstance(row.get('sources'),list) or not row['sources']:raise ValueError('必须保留真实来源')
        for source in row['sources']:
            if not isinstance(source,dict) or not all(isinstance(source.get(k),str) and source[k].strip() for k in ('file','kind','chapter','url')):raise ValueError('来源字段不完整')
            if not source['url'].startswith('/') or source['url'].startswith('//'):raise ValueError('仅允许同源来源URL')
            for k in ('pdf_page','printed_page','slide'):
                v=source.get(k)
                if v is not None and (type(v) is not int or v<1):raise ValueError('页码须为正整数或null')
    return rows
def main():
    p=argparse.ArgumentParser();p.add_argument('file');args=p.parse_args()
    rows=validate(json.loads(Path(args.file).read_text(encoding='utf-8')))
    for name in ('index/corpus.json','chunks/verified.json','structured_knowledge/course.json'):
        target=ROOT/'knowledge_base'/name;target.parent.mkdir(exist_ok=True,parents=True)
        target.write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
    print('导入核验片段：',len(rows))
if __name__=='__main__':main()
