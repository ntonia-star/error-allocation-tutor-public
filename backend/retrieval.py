from pathlib import Path
from collections import Counter
import json, math, re
ROOT=Path(__file__).resolve().parents[1]
CORPUS=json.loads((ROOT/'knowledge_base/index/corpus.json').read_text(encoding='utf-8'))

def tokens(text):
    text=text.lower()
    aliases={'等作用':'等影响','预算':'分配','课本':'教材','ppt':'课件','圆柱':'圆柱体','怎么算':'计算'}
    for old,new in aliases.items(): text=text.replace(old,new)
    parts=re.findall(r'[\u4e00-\u9fff]+|[a-z_]+|\d+(?:\.\d+)?',text)
    return [t for p in parts for t in ([p[i:i+2] for i in range(len(p)-1)] if re.match(r'[\u4e00-\u9fff]',p) and len(p)>1 else [p])]

DOCS=[Counter(tokens(c['title']+' '+c['title']+' '+c['content']+' '+c['conditions'])) for c in CORPUS]
AVG=(sum(sum(d.values()) for d in DOCS)/len(DOCS)) if DOCS else 1.0

def search(query,limit=5):
    terms=set(tokens(query)); scores=[]
    for chunk,doc in zip(CORPUS,DOCS):
        score=0.; matches=0
        for term in terms:
            freq=doc.get(term,0)
            if not freq: continue
            matches+=1
            df=sum(term in d for d in DOCS)
            idf=math.log(1+(len(DOCS)-df+.5)/(df+.5))
            score+=idf*freq*2.5/(freq+1.5*(.25+.75*sum(doc.values())/AVG))
        # Generic incidental words must not cause unrelated questions to reach the LLM.
        if matches>=2 and score>=1.0: scores.append((score,chunk))
    scores.sort(key=lambda r:r[0],reverse=True)
    if re.search(r'流程|步骤|过程|如何.*分配|怎么.*分配',query) and scores:
        # A procedure question needs the complete course chain, not just the
        # most lexically similar definition/cylinder fragments.
        required={'equal','adjustment','verification'}
        top=max(s for s,c in scores)
        scores=[(top+1 if c['id'] in required else s,c) for s,c in scores]
        present={c['id'] for _,c in scores}
        scores.extend((top+1,c) for c in CORPUS if c['id'] in required-present)
        scores.sort(key=lambda r:r[0],reverse=True)
    return [{**chunk,'retrieval_score':round(score,4)} for score,chunk in scores[:limit]]
