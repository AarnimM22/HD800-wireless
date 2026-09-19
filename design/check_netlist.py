from pathlib import Path
import json,xml.etree.ElementTree as E
B=Path(__file__).resolve().parents[1]
p=json.loads((B/'design/design-plan.json').read_text())
r=E.parse(B/'design/HD800-wireless.net.xml').getroot()
actual={n.attrib['name']:{(x.attrib['ref'],x.attrib['pin']) for x in n.findall('node') if not x.attrib['ref'].startswith('#')} for n in r.findall('./nets/net')}
errors=[]
for n in p['nets']:
    expected={(x['refdes'],x['pin']) for x in n['pins']}
    got=actual.get(n['name'],set())
    if expected!=got:errors.append({'net':n['name'],'missing':sorted(expected-got),'extra':sorted(got-expected)})
expected_refs={x['refdes'] for x in p['parts']}
actual_refs={x.attrib['ref'] for x in r.findall('./components/comp')}
if expected_refs!=actual_refs:errors.append({'missing_parts':sorted(expected_refs-actual_refs),'extra_parts':sorted(actual_refs-expected_refs)})
summary={'passed':not errors,'components':len(actual_refs),'planned_nets':len(p['nets']),'planned_pin_connections':sum(len(n['pins']) for n in p['nets']),'errors':errors}
(B/'design/connectivity-check.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2));assert not errors
