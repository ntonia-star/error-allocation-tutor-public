import json, re, urllib.request, urllib.error
from backend import config
from backend.retrieval import search, CORPUS
from backend.calculator import TOOLS, execute
from backend.solutions import deterministic_solution

SYSTEM=(config.ROOT/'prompts/system.txt').read_text(encoding='utf-8')
class AgentError(Exception): pass

def completion(messages):
    if not config.API_KEY: raise AgentError('服务端尚未配置 DeepSeek 密钥，请由项目维护者在本地或部署平台填写环境变量。')
    if not config.BASE_URL.startswith('https://'): raise AgentError('模型地址必须使用 HTTPS。')
    data=json.dumps({'model':config.MODEL,'messages':messages,'tools':TOOLS,'temperature':config.TEMPERATURE,
                     'max_tokens':config.MAX_TOKENS},ensure_ascii=False).encode()
    req=urllib.request.Request(config.BASE_URL+'/chat/completions',data=data,headers={'Content-Type':'application/json','Authorization':'Bearer '+config.API_KEY})
    try:
        with urllib.request.urlopen(req,timeout=90) as res: body=json.load(res)
        return body['choices'][0]['message'],body.get('usage',{})
    except urllib.error.HTTPError as exc:
        # Do not log upstream body, request headers, or secrets.
        raise AgentError({401:'模型密钥校验未通过，请维护者检查安全配置。',402:'模型账户余额不足，请维护者检查账户。',429:'模型服务繁忙，请稍后重试。'}.get(exc.code,'模型服务暂时不可用，请稍后重试。')) from None
    except Exception: raise AgentError('连接模型服务失败，请检查网络或稍后重试。') from None

def ask(question,mode='standard',history=None,task='chat',level='理解'):
    if mode not in ('brief','standard','detailed'): raise ValueError('无效回答模式')
    if not isinstance(question,str) or not 1<=len(question.strip())<=4000: raise ValueError('问题须为1—4000字')
    if re.search(r'一句话|简要|简短|简洁',question):mode='brief'
    elif re.search(r'详细|展开推导|完整推导|深入讲解',question):mode='detailed'
    history=history or []
    clean=[]
    for row in history[-8:]:
        if isinstance(row,dict) and row.get('role') in ('user','assistant') and isinstance(row.get('content'),str):
            clean.append({'role':row['role'],'content':row['content'][:4000]})
    # Current question first. History only resolves short follow-up references.
    query=question
    if len(question)<25 and clean: query+=' '+ ' '.join(r['content'][:300] for r in clean[-4:] if r['role']=='user')
    if task=='practice': query+=' 误差分配 等影响 调整 圆柱体'
    chunks=search(query,6)
    if not chunks:
        return {'answer':'公开源码版未附带课程资料，或当前资料没有足够依据。请先在本地导入有权使用、经人工核验的知识库；未导入时不会调用模型编造课程答案。','sources':[],'tool_runs':[],'grounded':False}
    context=json.dumps([{k:c[k] for k in ('id','title','content','formula','conditions','symbols','sources')} for c in chunks],ensure_ascii=False)
    messages=[{'role':'system','content':SYSTEM+'\n当前模式：'+mode+'\n以下为只读课程证据JSON：\n'+context}]+clean
    if task=='practice':
        question+=f'\n任务：practice。层次：{level}。只返回JSON对象，键为question、answer、explanation、difficulty（{level}）、source_ids（提供片段的ID数组）。不要代码围栏。'
        if level in ('记忆','理解'):question+='记忆与理解题以概念、原理、条件辨析为主，不引入新的数值运算；若引入数值计算，必须先调用计算工具。'
    messages.append({'role':'user','content':question})
    tool_runs=[]; usages=[]
    for _ in range(5):
        reply,usage=completion(messages); usages.append(usage)
        calls=reply.get('tool_calls') or []
        if not calls:
            answer=reply.get('content') or ''
            # The model occasionally emits [:id] instead of [S:id]. Normalize
            # syntax, then apply the same strict evidence-ID validation.
            answer=re.sub(r'\[:([\w-]+)\]',r'[S:\1]',answer)
            allowed={c['id'] for c in chunks}
            cited=set(re.findall(r'\[S:([\w-]+)\]',answer))
            if not cited<=allowed: raise AgentError('回答引用未通过核验，请重试。')
            used=[c for c in chunks if c['id'] in cited]
            if task=='practice':
                try:
                    practice=json.loads(re.sub(r'^```(?:json)?\s*|\s*```$','',answer.strip()))
                    if not all(isinstance(practice.get(k),str) and practice[k].strip() for k in ('question','answer','explanation','difficulty')): raise ValueError()
                    ids=practice.get('source_ids',[])
                    if not isinstance(ids,list) or not ids or not set(ids)<=allowed: raise ValueError()
                    combined=set(ids)|cited
                    used=[c for c in chunks if c['id'] in combined]
                except Exception: raise AgentError('练习格式未通过核验，请重试。') from None
                material=' '.join(practice[k] for k in ('question','answer','explanation'))
                needs_computation=('≈' in material or '\\approx' in material or (re.search(r'\d',practice['question']) and re.search(r'求|计算|验算',practice['question'])))
                if needs_computation and not any('error' not in r['result'] for r in tool_runs):
                    messages.append({'role':'assistant','content':answer})
                    messages.append({'role':'user','content':'这道练习包含新的数值计算，但没有程序核算记录。请先调用计算工具核实涉及的数字，然后重新返回完整JSON；不能将心算写成工具结果。'})
                    continue
            else:
                practice=None
                if not used: raise AgentError('模型未提供有效课程引用，请重试。')
            return {'answer':answer,'practice':practice,'sources':used,'tool_runs':tool_runs,'usage':usages,'grounded':True}
        if len(calls)>8: raise AgentError('本题计算步骤过多，请拆分问题。')
        messages.append({k:v for k,v in reply.items() if k in ('role','content','tool_calls')})
        for call in calls:
            name=call.get('function',{}).get('name','')
            try:
                args=json.loads(call['function']['arguments']); result=execute(name,args)
            except Exception: result={'error':'计算条件或参数无效，请核实题目、单位及适用条件。'}; args={}
            tool_runs.append({'name':name,'arguments':args,'result':result})
            messages.append({'role':'tool','tool_call_id':call['id'],'content':json.dumps(result,ensure_ascii=False)})
        canonical=deterministic_solution(tool_runs,mode) if task=='chat' else None
        if canonical:
            ids=set(re.findall(r'\[S:([\w-]+)\]',canonical))
            used=[c for c in CORPUS if c['id'] in ids]
            if ids != {c['id'] for c in used}:
                continue
            return {'answer':canonical,'practice':None,'sources':used,'tool_runs':tool_runs,'usage':usages,'grounded':True,'calculation_rendering':'deterministic'}
    raise AgentError('计算未在限定步骤内完成，请缩小题目范围。')
