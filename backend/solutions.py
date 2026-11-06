"""Course-derived numerical solutions rendered from tool results, not model arithmetic."""
import math
def number(value):return format(value,'.8g')
def equal_solution(result,mode):
    n=len(result['allocated']);total=number(result['total']);c=number(result['contribution'])
    values='、'.join(number(x) for x in result['allocated'])
    if mode=='brief':
        return rf'按选定模型等影响原则，{n}项的允许误差幅值依次为 **{values}**；每项影响为{c}，带传递系数合成为{number(result["recombined"])}，满足总允许误差{total}。[S:equal][S:rss]'
    rows='\n'.join(f'| {i+1} | {number(a)} | {number(e)} | {number(abs(a)*e)} |' for i,(a,e) in enumerate(zip(result['coefficients'],result['allocated'])))
    text=rf'''### 1. 已知与适用条件
总允许误差幅值为 {total}，共 {n} 个分项，传递系数依次为 {'、'.join(number(a) for a in result['coefficients'])}。
采用选定模型的一阶、不相关统计合成约定，各量误差口径和单位须一致。[S:rss]

### 2. 按等影响原则分配
以 $e_i$ 统一表示本题的非负误差幅值（标准差或选定模型约定的极限误差，不能混用）：
$$|a_i|e_i=\frac{{e_y}}{{\sqrt{{n}}}},\qquad e_i=\frac{{e_y}}{{\sqrt{{n}}|a_i|}}$$
每项影响为 ${total}/\sqrt{{{n}}}\approx{c}$。表中数值为圆整显示值。[S:equal]

| 分项 | 传递系数 | 输入量允许误差幅值 | 对输出的影响幅值 |
| --- | --- | --- | --- |
{rows}

### 3. 带传递系数合成验算
$$e_{{y,\mathrm{{actual}}}}=\sqrt{{\sum_i(a_i e_i)^2}}=\sqrt{{n c^2}}={number(result['recombined'])}$$
程序使用未圆整数值验算，结果满足给定总允许误差 {total}。

**注意：不能省去传递系数，直接把输入误差的平方相加。**

输入误差与分项影响的单位按题目模型分别确定。[S:rss][S:verification]'''
    if mode=='detailed':text+=r'''

### 4. 原理与方案调整
设每项影响幅值为$c$，则$e_y^2=nc^2$，所以$c=e_y/\sqrt n$；再由$|a_i|e_i=c$解出各输入量误差。负系数按绝对值处理，零系数不能在一阶模型中直接相除。[S:equal][S:derivation]
这是初始分配，不是唯一最优方案。应结合设备能力适当放宽难实现项、提高容易实现项要求，每次调整后重新合成，与允许总误差比较。[S:adjustment][S:verification]'''
    return text

def cylinder_solution(args,r,mode):
    d=number(args['diameter']);h=number(args['height']);pct=number(args['relative_percent'])
    de,he=map(number,r['initial']['allocated']);a,b=map(number,r['coefficients'])
    if mode=='brief':
        result=rf'按选定模型约定，$D={d}$ mm、$h={h}$ mm、体积允许相对误差{pct}%时，初始等影响分配为 $\delta_D={de}$ mm、$\delta_h={he}$ mm。[S:cylinder][S:equal]'
        if 'actual_error' in r:result+=f'给定量具方案合成误差{number(r["actual_error"])} mm³，允许值{number(r["allowed_error"])} mm³，**{"合格" if r["qualified"] else "不合格"}**。[S:verification]'
        return result
    text=rf'''### 1. 已知与模型
$D={d}$ mm，$h={h}$ mm，体积允许相对误差 {pct}%，取$\pi=3.1416$。沿用选定模型一阶、不相关的统计合成约定；以下均为非负误差限幅值，不解释为任意确定性最坏界。[S:cylinder][S:limit]

$$V=\frac{{\pi D^2h}}{{4}}\approx{number(r['volume'])}\,\mathrm{{mm}}^3,\qquad\delta_{{V,\mathrm{{allow}}}}\approx{number(r['allowed_error'])}\,\mathrm{{mm}}^3$$

### 2. 传递系数与等影响初始分配
$$a_D=\frac{{\partial V}}{{\partial D}}=\frac{{\pi Dh}}{{2}}\approx{a}\,\mathrm{{mm}}^2,\qquad a_h=\frac{{\partial V}}{{\partial h}}=\frac{{\pi D^2}}{{4}}\approx{b}\,\mathrm{{mm}}^2$$
共两项，分项影响均为允许体积误差除以$\sqrt2$。[S:equal]
$$\delta_D=\frac{{\delta_{{V,\mathrm{{allow}}}}}}{{\sqrt2|a_D|}}\approx{de}\,\mathrm{{mm}},\qquad\delta_h=\frac{{\delta_{{V,\mathrm{{allow}}}}}}{{\sqrt2|a_h|}}\approx{he}\,\mathrm{{mm}}$$
初始方案带系数合成为 {number(r['initial']['recombined'])} mm³，满足总预算。以上使用未圆整数值计算。[S:cylinder][S:verification]'''
    if 'actual_error' in r:
        actual=number(r['actual_error']);allow=number(r['allowed_error']);sign='\\leq' if r['qualified'] else '>'
        text+=rf'''

### 3. 给定量具方案的实际验算
本次输入 $\delta_D={number(args['diameter_error'])}$ mm，$\delta_h={number(args['height_error'])}$ mm。
$$\delta_{{V,\mathrm{{actual}}}}=\sqrt{{(a_D\delta_D)^2+(a_h\delta_h)^2}}\approx{actual}\,\mathrm{{mm}}^3\ {sign}\ {allow}\,\mathrm{{mm}}^3$$
因此该量具方案**{'合格' if r['qualified'] else '不合格'}**。直径相对误差为 {number(r['relative_diameter_percent'])}%，高度相对误差为 {number(r['relative_height_percent'])}%。[S:verification]

结论只针对本次输入参数；使用不同资料时须分别核对参数与适用条件。[S:conflict]'''
    else:text+='\n\n这是初始分配。选择实际量具并调整误差后，仍须重新合成验算。[S:adjustment][S:verification]'
    if mode=='detailed':text+=r'''

### 推导与易错点
由一阶微分得$dV=(\pi Dh/2)dD+(\pi D^2/4)dh$。不相关统计模型使两项贡献以平方和合成，而不是把输入长度误差直接相加。等影响令$|a_D|\delta_D=|a_h|\delta_h=\delta_{V,\mathrm{allow}}/\sqrt2$，再分别除以传递系数幅值。[S:equal][S:derivation]
直径系数与高度系数单位是mm²，乘长度误差后得到体积误差mm³。输入误差不必相等；量具分度值不能直接当作极限误差，调整方案必须按题目给定的量具误差验算。[S:pitfalls][S:verification]'''
    return text

def deterministic_solution(tool_runs,mode):
    if not tool_runs or any(r['name'] not in ('equal_allocation','cylinder') or 'error' in r['result'] for r in tool_runs):return None
    parts=[]
    for run in tool_runs:
        parts.append(equal_solution(run['result'],mode) if run['name']=='equal_allocation' else cylinder_solution(run['arguments'],run['result'],mode))
    return '\n\n---\n\n'.join(parts)
