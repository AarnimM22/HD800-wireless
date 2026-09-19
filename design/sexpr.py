import json, re

class Atom(str):
    pass

def parse(text):
    tokens = re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+', text)
    stack=[]; root=None
    for t in tokens:
        if t=='(':
            v=[]
            if stack: stack[-1].append(v)
            stack.append(v)
        elif t==')':
            root=stack.pop()
        else:
            stack[-1].append(json.loads(t) if t.startswith('"') else Atom(t))
    return root

def dump(x):
    if isinstance(x,list): return '('+' '.join(dump(y) for y in x)+')'
    if isinstance(x,Atom): return str(x)
    if isinstance(x,str): return json.dumps(x,ensure_ascii=False)
    return str(x)

def items(x,key): return [y for y in x if isinstance(y,list) and y and y[0]==key]
def one(x,key,default=None): return next(iter(items(x,key)),default)

def pins(sym):
    out=[]
    for unit in items(sym,'symbol'):
        for p in items(unit,'pin'):
            out.append({'number':str(one(p,'number')[1]),'name':str(one(p,'name')[1]),'type':str(p[1]),'at':one(p,'at')[1:], 'unit':int(str(unit[1]).rsplit('_',2)[1])})
    return out

def resolve(lid,dirs):
    from pathlib import Path
    lib,name=lid.split(':',1)
    for d in dirs:
        f=Path(d)/(lib+'.kicad_sym')
        if not f.exists(): continue
        root=parse(f.read_text(encoding='utf-8'))
        syms={str(s[1]):s for s in items(root,'symbol')}
        if name not in syms: continue
        s=syms[name]
        if one(s,'extends'):
            parent=resolve(lib+':'+str(one(s,'extends')[1]),dirs)
            base=str(parent[1]).split(':')[-1]
            for u in items(parent,'symbol'):
                u[1]=str(u[1]).replace(base+'_',name+'_',1)
            for prop in items(s,'property'):
                parent[:]=[v for v in parent if not(isinstance(v,list) and v[:2]==prop[:2])]
                parent.append(prop)
            s=parent
        s[1]=lid
        return s
    raise ValueError(lid)

if __name__=='__main__':
    import sys
    ds=[r'C:\Program Files\KiCad\10.0\share\kicad\symbols']
    for lid in sys.argv[1:]:
        s=resolve(lid,ds)
        print(lid,one(s,'property'))
        print(json.dumps(pins(s)))
