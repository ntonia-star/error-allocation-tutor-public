"""Bounded arithmetic only. No eval, filesystem, imports or user code execution."""
import ast, math, operator

OPS={ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.Div:operator.truediv,ast.Pow:operator.pow}
def arithmetic(expression):
    if not isinstance(expression,str) or len(expression)>400: raise ValueError('表达式过长')
    tree=ast.parse(expression,mode='eval')
    if sum(1 for _ in ast.walk(tree))>100: raise ValueError('表达式过于复杂')
    def parse(node):
        if isinstance(node,ast.Expression): return parse(node.body)
        if isinstance(node,ast.Constant) and type(node.value) in (int,float): value=node.value
        elif isinstance(node,ast.Name) and node.id=='pi': value=math.pi
        elif isinstance(node,ast.UnaryOp) and isinstance(node.op,(ast.UAdd,ast.USub)): value=parse(node.operand)*(1 if isinstance(node.op,ast.UAdd) else -1)
        elif isinstance(node,ast.BinOp) and type(node.op) in OPS:
            a,b=parse(node.left),parse(node.right)
            if isinstance(node.op,ast.Pow) and (abs(b)>20 or (a<0 and b%1)): raise ValueError('幂运算超出范围')
            value=OPS[type(node.op)](a,b)
        elif isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='sqrt' and len(node.args)==1 and not node.keywords:
            value=math.sqrt(parse(node.args[0]))
        else: raise ValueError('仅允许数字、pi、sqrt和基本四则幂运算')
        if not math.isfinite(value) or abs(value)>1e100: raise ValueError('结果超出范围')
        return value
    return {'expression':expression,'result':parse(tree)}

def finite(value,name,positive=False):
    if type(value) not in (float,int) or not math.isfinite(value) or abs(value)>1e12 or (value!=0 and abs(value)<1e-12) or (positive and value<=0): raise ValueError(name+'必须为有限有效数值（非零幅值范围1e-12至1e12）')
    return float(value)

def equal_allocation(total,coefficients):
    total=finite(total,'总允许误差',True)
    if not isinstance(coefficients,list) or not 1<=len(coefficients)<=30: raise ValueError('分项数量必须为1—30')
    values=[finite(a,'传递系数') for a in coefficients]
    if any(a==0 for a in values): raise ValueError('零传递系数需重新检查一阶模型，不能直接分配')
    contribution=total/math.sqrt(len(values))
    allocated=[contribution/abs(a) for a in values]
    return {'method':'选定模型等影响幅值分配','assumption':'互不相关、一阶线性化、同一统计合成约定',
            'total':total,'coefficients':values,'contribution':contribution,'allocated':allocated,
            'recombined':math.sqrt(sum((a*e)**2 for a,e in zip(values,allocated)))}

def cylinder(diameter,height,relative_percent,diameter_error=None,height_error=None):
    d=finite(diameter,'直径mm',True); h=finite(height,'高度mm',True); r=finite(relative_percent,'相对误差百分数',True)
    if r>=100: raise ValueError('误差过大，不能在此采用小误差一阶近似')
    volume=3.1416*d*d*h/4; total=volume*r/100; a=3.1416*d*h/2; b=3.1416*d*d/4
    result={'pi':3.1416,'units':{'length':'mm','volume':'mm³','coefficients':'mm²'},'volume':volume,'allowed_error':total,
            'coefficients':[a,b],'initial':equal_allocation(total,[a,b])}
    if (diameter_error is None)!=(height_error is None): raise ValueError('验算时必须同时给出直径和高度误差')
    if diameter_error is not None:
        de=finite(diameter_error,'直径误差'); he=finite(height_error,'高度误差')
        if min(de,he)<0: raise ValueError('误差限幅值不得为负')
        actual=math.hypot(a*de,b*he)
        result.update(actual_error=actual,qualified=actual<=total,relative_diameter_percent=de/d*100,relative_height_percent=he/h*100)
    return result

TOOLS=[{'type':'function','function':{'name':name,'description':desc,'parameters':schema}} for name,desc,schema in [
 ('arithmetic','核实数值表达式，支持sqrt、pi及四则幂运算。单位由回答者检查。',{'type':'object','properties':{'expression':{'type':'string'}},'required':['expression'],'additionalProperties':False}),
 ('equal_allocation','选定模型不相关一阶等影响分配。调用前必须确认适用条件；总量与系数保持单位一致。',{'type':'object','properties':{'total':{'type':'number'},'coefficients':{'type':'array','items':{'type':'number'}}},'required':['total','coefficients'],'additionalProperties':False}),
 ('cylinder','圆柱体例题及同类题计算，长度mm，相对百分数如1表示1%，pi=3.1416；可验算给定量具误差。',{'type':'object','properties':{k:{'type':'number'} for k in ['diameter','height','relative_percent','diameter_error','height_error']},'required':['diameter','height','relative_percent'],'additionalProperties':False})]]

def execute(name,args):
    funcs={'arithmetic':arithmetic,'equal_allocation':equal_allocation,'cylinder':cylinder}
    if name not in funcs: raise ValueError('未知工具')
    return funcs[name](**args)
