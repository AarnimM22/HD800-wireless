"""Repair MCP's unconnected output and split it into readable hierarchical sheets.
All pin/net endpoints are checked against the source symbols and exported netlist.
"""
from pathlib import Path
import json,uuid,math,copy,shutil
from sexpr import Atom as A,parse,dump,items,one,pins,resolve
BASE=Path(__file__).resolve().parents[1]
plan=json.loads((BASE/'design/design-plan.json').read_text())
layout=json.loads((BASE/'design/layout-data.json').read_text())
dirs=[str(BASE),r'C:\Program Files\KiCad\10.0\share\kicad\symbols']
def uid(key):return str(uuid.uuid5(uuid.NAMESPACE_URL,'hd800-wireless-draft/'+key))
def s(t):return parse(t)
def q(t):return json.dumps(str(t))
def num(n):return round(float(n),4)
root_uuid='89d30dcd-e991-4e32-b460-83f5b37a2b9e'
proj='HD800-wireless'
symbols={lid:resolve(lid,dirs) for lid in dict.fromkeys(p['lib_ref'] for p in plan['parts'])}
endpoint={(n['refdes'],n['pin']):net['name'] for net in plan['nets'] for n in net['pins']}
source=parse((BASE/'design/mcp-generated.kicad_sch').read_text())
source_instances={str(one(t,'property')[2]):t for t in items(source,'symbol')}

def text(value,x,y,size=1.27):
    return s(f'(text {q(value)} (at {x} {y} 0) (effects (font (size {size} {size})) (justify left top)) (uuid "{uid(value+str(x)+str(y))}"))')
def prop(name,val,x,y,hide=False):
    return s(f'(property {q(name)} {q(val)} (at {x} {y} 0) (effects (font (size 1.27 1.27))'+(' (hide yes)' if hide else '')+'))')
def doc(title,id,paper='A2'):
    return s(f'(kicad_sch (version 20250114) (generator "eeschema") (uuid "{id}") (paper "{paper}") (title_block (title {q(title)}) (date "2026-09-16") (rev "A - REVIEW DRAFT") (comment 1 "NOT FOR FABRICATION - see DESIGN_NOTES.md")) (lib_symbols))')
def label(net,x,y,angle,key):
    justify='right' if angle in [180,270] else 'left'
    return s(f'(global_label {q(net)} (shape bidirectional) (at {x} {y} {angle}) (effects (font (size 1.0 1.0)) (justify {justify})) (uuid "{uid(key)}") (property "Intersheetrefs" "${{INTERSHEET_REFS}}" (at {x} {y} {angle}) (effects (font (size 1 1)) (hide yes))))')
def wire(x,y,xx,yy,key):
    return s(f'(wire (pts (xy {x} {y}) (xy {xx} {yy})) (stroke (width 0) (type default)) (uuid "{uid(key)}"))')
def add_component(doc,p,x,y,path,unit=1):
    ref=p['refdes'];lid=p['lib_ref'];sy=symbols[lid]
    symbol_pins=[v for v in pins(sy) if v['unit'] in [0,unit]]
    instance=copy.deepcopy(source_instances.get(ref,s('(symbol (in_bom yes) (on_board yes))')))
    instance[:]=[a for a in instance if not(isinstance(a,list) and a and a[0] in ['lib_id','at','unit','property','uuid','instances','pin','dnp'])]
    instance += [s(f'(lib_id {q(lid)})'),s(f'(at {x} {y} 0)'),s(f'(unit {unit})'),s(f'(uuid "{uid(ref+str(unit))}")'),s('(dnp '+('yes' if layout['extra'][ref]['dnp'] else 'no')+')')]
    top=max([float(v['at'][1]) for v in symbol_pins]+[5.08]+[float(one(r,'start')[2]) for u in items(sy,'symbol') for r in items(u,'rectangle')])
    ispassive=ref[0] in ['R','C','L'] and not ref.startswith('LED')
    if ispassive:
        instance+=[prop('Reference',ref,x+4,y-1.27),prop('Value',p['value'].split(' / ')[0],x+4,y+1.27)]
        if ref.startswith('C') and ' / 10V' in p['value']:
            instance.append(prop('Voltage','10V X7R' if 'C0G' not in p['value'] else '10V C0G',x+4,y+3.81))
        for pp in items(instance,'property'):
            one(pp,'effects').append(s('(justify left)'))
    else:
        instance+=[prop('Reference',ref+(chr(64+unit) if len(set(v['unit'] for v in pins(sy)))>1 else ''),x,y-top-5.08),prop('Value',p['value'],x,y-top-2.54)]
    fp=p.get('footprint')
    if not fp:
        fp=next((v[2] for v in items(sy,'property') if v[1]=='Footprint'),'')
    instance.append(prop('Footprint',fp,x,y,True))
    ds=next((v[2] for v in items(sy,'property') if v[1]=='Datasheet'),'')
    if lid.startswith('HD800_Custom:'):
        ds={'CS43131_CNZ':'https://statics.cirrus.com/pubs/proDatasheet/CS43131_DS1155F2.pdf','OPA1688IDR':'https://www.ti.com/lit/ds/symlink/opa1688.pdf','TMUX4827YBHR':'https://www.ti.com/lit/ds/symlink/tmux4827.pdf','IP2312':'https://m.baixingks.com/upload/pdf/DX-IP2312.pdf'}[lid.split(':')[1]]
    instance.append(prop('Datasheet',ds,x,y,True))
    instance.append(prop('Design_note',p['value'],x,y,True))
    instance.append(s(f'(instances (project "{proj}" (path "{path}" (reference "{ref}") (unit {unit}))))'))
    done=set()
    for pin in symbol_pins:
        pn=pin['number'];px,py,pa=map(float,pin['at']); xx=num(x+px);yy=num(y-py)
        instance.append(s(f'(pin {q(pn)} (uuid "{uid(ref+"pin"+pn)}"))'))
        net=endpoint.get((ref,pn));pos=(xx,yy)
        if pos in done:continue
        done.add(pos)
        if not net:
            doc.append(s(f'(no_connect (at {xx} {yy}) (uuid "{uid(ref+pn+"nc")}"))'))
            continue
        dx=-math.cos(math.radians(pa))*5.08;dy=math.sin(math.radians(pa))*5.08
        ex=num(xx+dx);ey=num(yy+dy)
        doc.append(wire(xx,yy,ex,ey,ref+pn+'wire'))
        # Point label toward the pin, with the text extending away from it.
        angle={0:180,180:0,90:270,270:90}[int(pa)]
        if ispassive and pa in [90,270]: angle=0
        doc.append(label(net,ex,ey,angle,ref+pn+'label'))
    doc.append(instance)

root=doc('HD800 WIRELESS | system overview',root_uuid,'A3')
root.append(text('HD800 WIRELESS',20,18,3.8))
root.append(text('Dual CS43131 / nRF5340 / assembly-configured Eco or Turbo',20,26,1.8))
sheet_ids={sh['name']:uid(sh['name']+'sheet') for sh in plan['sheets']}
for i,sh in enumerate(plan['sheets']):
    name=sh['name'];su=uid(name+'document');sid=sheet_ids[name];path='/'+root_uuid+'/'+sid
    is_dac=name in ['04_DAC_Left','05_DAC_Right']
    d=doc(name.replace('_',' '),su,'A3' if is_dac else 'A2')
    partlist=[p for p in plan['parts'] if p['sheet']==name]
    one(d,'lib_symbols').extend(copy.deepcopy(symbols[l]) for l in dict.fromkeys(p['lib_ref'] for p in partlist))
    d.append(text(name.replace('_',' ').upper(),15,12,2.54))
    d.append(text('REVIEW DRAFT  |  Labels are electrical connections across all sheets',15,20,1.27))
    # Dedicated top row for ICs/connectors. Supporting two-pin parts below.
    large=[p for p in partlist if not(p['refdes'].startswith(('R','C','L','JP')))]
    small=[p for p in partlist if p not in large]
    if is_dac:
        add_component(d,large[0],76.2,81.28,path)
        for j,p in enumerate(small):add_component(d,p,157.48+(j%4)*60.96,50.8+(j//4)*40.64,path)
        d.append(text('Supply filtering, bypass and charge-pump network',139.7,30.48,1.5))
        ny=233.68
    elif name=='03_MCU_RF':
        add_component(d,next(p for p in large if p['refdes']=='U1'),85.09,116.84,path)
        other=[p for p in large if p['refdes']!='U1']
        for j,p in enumerate(other):
            for unit in sorted(set(v['unit'] for v in pins(symbols[p['lib_ref']]))-{0}):
                add_component(d,p,234.95+j*88.9,63.5+(unit-1)*45.72,path,unit)
        for j,p in enumerate(small):add_component(d,p,209.55+(j%5)*71.12,137.16+(j//5)*27.94,path)
        ny=370
    else:
        # Up to six larger symbols across; split into two rows if needed.
        for j,p in enumerate(large):
            x=55.88+(j%6)*91.44; y=76.2+(j//6)*78.74
            for unit in sorted(set(v['unit'] for v in pins(symbols[p['lib_ref']]))-{0}):add_component(d,p,x,y+(unit-1)*30.48,path,unit)
        small_y=152.4 if len(large)<=6 else 223.52
        for j,p in enumerate(small):add_component(d,p,40.64+(j%6)*91.44,small_y+(j//6)*35.56,path)
        ny=max(310,small_y+math.ceil(len(small)/6)*35.56+5)
    for k,note in enumerate(layout['notes'][name]):d.append(text(note,15,ny+k*5.08,1.27))
    d.append(s('(embedded_fonts no)'))
    (BASE/(name+'.kicad_sch')).write_text(dump(d)+'\n',encoding='utf-8')
    x=20+(i%3)*128;y=48+(i//3)*45
    root.append(s(f'(sheet (at {x} {y}) (size 110 27) (stroke (width 0.254) (type default)) (fill (color 0 0 0 0)) (uuid "{sid}") (property "Sheetname" {q(name.replace("_"," "))} (at {x} {y-2} 0) (effects (font (size 1.5 1.5)) (justify left bottom))) (property "Sheetfile" "{name}.kicad_sch" (at {x} {y+29} 0) (effects (font (size 1.0 1.0)) (justify left top))) (instances (project "{proj}" (path "/{root_uuid}" (page "{i+2}")))))'))
root.append(text('SIGNAL FLOW',20,141,2.0))
root.append(text('USB / 2.4GHz -> nRF5340 -> I2S + I2C -> two CS43131 DACs -> 4 balanced audio legs',20,151,1.5))
root.append(text('ECO assembly: DACs -> configuration links -> drivers     TURBO assembly: DACs -> 4 buffers -> links -> drivers',20,160,1.4))
root.append(text('Battery -> 1.8V buck / DAC VP     Turbo only: Q1 -> positive rail + LM2776 negative rail',20,169,1.4))
root.append(text('DESIGN STATUS / REQUIRED BEFORE PCB RELEASE',20,185,2.0))
for i,t in enumerate(['Functional draft: six connected circuit sheets, custom symbols, netlist validation and review notes.', 'No headphone jack or BGA audio muxes: four solder pads wire directly to the installed drivers.', 'RF matching, battery thermal/current limits, USB-C charge policy and amplifier load stability need validation.', '250mW output, 130dBA system performance, <10ms latency and 33/47h runtime are targets, not measurements.', 'See DESIGN_NOTES.md for Eco/Turbo population links, sources and remaining release blockers.']):root.append(text(t,20,196+i*7,1.4))
# Power flags denote real off-sheet sources / pass-through conversion paths.
flag=resolve('power:PWR_FLAG',dirs);one(root,'lib_symbols').append(flag)
for i,net in enumerate(['GND','VBUS','VBAT','VDD_1V8','CHG_5V','AMP_VP','DAC_L_VA','DAC_R_VA']):
    x=25.4+(i%4)*63.5;y=254+(i//4)*10.16;ref='#FLG0'+str(i+1)
    root.append(s(f'(symbol (lib_id "power:PWR_FLAG") (at {x} {y} 0) (unit 1) (in_bom no) (on_board yes) (dnp no) (uuid "{uid(ref)}") (property "Reference" "{ref}" (at {x} {y} 0) (effects (font (size 1 1)) (hide yes))) (property "Value" "PWR_FLAG" (at {x} {y-3} 0) (effects (font (size 1 1)) (hide yes))) (instances (project "{proj}" (path "/{root_uuid}" (reference "{ref}") (unit 1)))))'))
    root.append(label(net,x,y,0,'flag'+net))
root.append(s('(sheet_instances (path "/" (page "1")))'));root.append(s('(embedded_fonts no)'))
target=BASE/'HD800-wireless.kicad_sch'
backup=BASE/'design/original-empty.kicad_sch'
if not backup.exists():shutil.copy2(target,backup)
target.write_text(dump(root)+'\n',encoding='utf-8')
(BASE/'sym-lib-table').write_text('(sym_lib_table (version 7) (lib (name "HD800_Custom") (type "KiCad") (uri "${KIPRJMOD}/HD800_Custom.kicad_sym") (options "") (descr "Project custom symbols from manufacturer pin tables")))\n')
print('Wrote main schematic + 6 connected circuit sheets; source backup retained.')

