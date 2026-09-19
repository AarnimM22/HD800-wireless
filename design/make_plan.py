from pathlib import Path
import json
from sexpr import resolve,pins,one

BASE=Path(__file__).resolve().parents[1]
LIBS=[str(BASE),r'C:\Program Files\KiCad\10.0\share\kicad\symbols']
parts=[]; nets={}; extra={}; counters={'R':1,'C':1,'L':3}
page=''
def add(ref,lib,value,connections,footprint=None,role=None,dnp=False):
    sym=resolve(lib,LIBS)
    legal={p['number'] for p in pins(sym)}
    assert set(connections)<=legal,(ref,set(connections)-legal)
    p={'refdes':ref,'lib_ref':lib,'value':value,'sheet':page}
    if footprint: p['footprint']=footprint
    if role: p['role']=role
    parts.append(p);extra[ref]={'dnp':dnp}
    for pin,net in connections.items():
        if net: nets.setdefault(net,[]).append({'refdes':ref,'pin':pin})
    return ref
def passive(kind,value,a,b,ref=None,dnp=False):
    if not ref:
        ref=kind+str(counters[kind]); counters[kind]+=1
    fp={'R':'Resistor_SMD:R_0402_1005Metric','C':'Capacitor_SMD:C_0402_1005Metric','L':'Inductor_SMD:L_0603_1608Metric'}[kind]
    if ref=='L1': fp='Inductor_SMD:L_0805_2012Metric'
    if ref=='L2': fp=None  # Select a real >=4A part before assigning its footprint.
    if kind=='C' and any(v in value for v in ['10u','15u','22u','4.7u']): fp='Capacitor_SMD:C_0603_1608Metric'
    return add(ref,'Device:'+kind,value,{'1':a,'2':b},fp,dnp=dnp)
def cap(value,a,b='GND'):return passive('C',value+' / 10V',a,b)
def res(value,a,b):return passive('R',value,a,b)
def fet(ref,source,drain,gate):
    add(ref,'Transistor_FET:AO3401A','AO3401A',{'1':gate,'2':source,'3':drain},'Package_TO_SOT_SMD:SOT-23')
def npn(ref,drive,collector):
    add(ref,'Transistor_BJT:MMBT3904','MMBT3904',{'1':drive,'2':'GND','3':collector},'Package_TO_SOT_SMD:SOT-23')

page='01_USB_Charging'
add('J1','Connector:USB_C_Receptacle_USB2.0_16P','USB4105-GF-A',{'A1':'GND','A12':'GND','B1':'GND','B12':'GND','SH':'GND','A4':'VBUS','A9':'VBUS','B4':'VBUS','B9':'VBUS','A5':'CC1','B5':'CC2','A6':'USB_DP','B6':'USB_DP','A7':'USB_DM','B7':'USB_DM'},'Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal')
add('D1','Power_Protection:USBLC6-2SC6','USBLC6-2SC6',{'1':'USB_DP','6':'USB_DP','3':'USB_DM','4':'USB_DM','2':'GND','5':'VBUS'},'Package_TO_SOT_SMD:SOT-23-6')
for ch in (1,2):
    res('5.1k 1%','CC'+str(ch),'GND')
    res('100k 1%','CC'+str(ch),'CC'+str(ch)+'_ADC')
    res('100k 1%','CC'+str(ch)+'_ADC','GND')
    cap('1nF','CC'+str(ch)+'_ADC')
cap('1uF','VBUS');cap('100nF','VBUS')
fet('Q3','VBUS','CHG_5V','CHG_GATE')
res('100k','VBUS','CHG_GATE');cap('10nF','CHG_GATE','VBUS')
npn('Q4','CHG_BASE','CHG_GATE');res('10k','CHG_EN','CHG_BASE');res('100k','CHG_BASE','GND')
add('U7','HD800_Custom:IP2312','IP2312 4.20V ONLY',{'2':'CHG_TEST','4':'BAT_NTC','5':'VBAT','6':'CHG_ISET','7':'CHG_SW','8':'CHG_5V','9':'GND'},'Package_SO:SOIC-8-1EP_3.9x4.9mm_P1.27mm_EP2.29x3mm')
res('1k','VBAT','CHG_TEST');res('135k 1% / 1A','CHG_ISET','GND')
add('J4','Connector_Generic:Conn_01x02','BATTERY NTC 100k B3950',{'1':'BAT_NTC','2':'GND'},'Connector_JST:JST_PH_S2B-PH-K_1x02_P2.00mm_Horizontal')
passive('L','1uH / Isat >=4A','CHG_SW','VBAT',ref='L2')
cap('22uF','CHG_5V');cap('100nF','CHG_5V');cap('22uF','VBAT')
add('BAT1','Connector_Generic:Conn_01x02','PROTECTED 1S 4.20V LiPo',{'1':'VBAT','2':'GND'},'Connector_JST:JST_PH_S2B-PH-K_1x02_P2.00mm_Horizontal')

page='02_Power'
add('U6','Regulator_Switching:TLV62568DBV','TLV62568DBVR',{'1':'SYS_EN','2':'GND','3':'BUCK_SW','4':'VBAT','5':'BUCK_FB'},'Package_TO_SOT_SMD:SOT-23-5')
res('100k','VBAT','SYS_EN')
add('SW2','Switch:SW_SPST','SYSTEM OFF (close to turn off)',{'1':'SYS_EN','2':'GND'})
passive('L','2.2uH DFE201210U-2R2M=P2','BUCK_SW','VDD_1V8',ref='L1')
res('200k 1%','VDD_1V8','BUCK_FB');res('100k 1%','BUCK_FB','GND')
cap('10uF','VBAT');cap('100nF','VBAT');cap('10uF','VDD_1V8');cap('100nF','VDD_1V8')
fet('Q1','VBAT','AMP_VP','AMP_GATE')
res('100k','VBAT','AMP_GATE');cap('10nF','AMP_GATE','VBAT')
npn('Q2','AMP_BASE','AMP_GATE');res('10k','AMP_EN','AMP_BASE');res('100k','AMP_BASE','GND')
add('U4','Regulator_SwitchedCapacitor:LM2776','LM2776DBVR',{'1':'AMP_VN','2':'GND','3':'AMP_VP','4':'AMP_VP','5':'PUMP_CP','6':'PUMP_CN'},'Package_TO_SOT_SMD:SOT-23-6')
cap('2.2uF','PUMP_CP','PUMP_CN');cap('2.2uF','AMP_VP');cap('2.2uF','AMP_VN');cap('10uF','AMP_VP');cap('10uF','AMP_VN')
res('100k','AMP_VP','GND');res('100k','AMP_VN','GND')
res('330k 1%','VBAT','VBAT_ADC');res('100k 1%','VBAT_ADC','GND');cap('10nF','VBAT_ADC')

page='03_MCU_RF'
connections={'E1':'VDD_1V8','J1':'VDD_1V8','EP':'GND','A5':'VBUS','B2':'USB_DP','B4':'USB_DM','B6':'DECUSB','A13':'DECA','A23':'DECN','A15':'DECD','A27':'DECR','G31':'DECR','A21':'DCC','B10':'DCCD','C31':'HFXO_1','B30':'HFXO_2','L31':'RF_ANT','AA31':'SWDIO','W31':'SWDCLK','AC31':'MCU_RESET','AL5':'I2S_MCLK_SRC','AK8':'I2S_BCLK_SRC','AK10':'I2S_LRCK_SRC','AL9':'I2S_DATA_SRC','AE1':'I2C_SDA','AF2':'I2C_SCL','AK16':'DAC_RESET','AK18':'DAC_INT_L','AK20':'DAC_INT_R','AL19':'AMP_EN','AK22':'MODE_SENSE','AK24':'CHG_EN','V2':'CC1_ADC','Y2':'CC2_ADC','AB2':'VBAT_ADC'}
for p in pins(resolve('MCU_Nordic:nRF5340-QKxx',LIBS)):
    if p['name']=='VDD':connections[p['number']]='VDD_1V8'
add('U1','MCU_Nordic:nRF5340-QKxx','nRF5340-QKAA',connections,'Package_DFN_QFN:Nordic_AQFN-94-1EP_7x7mm_P0.4mm')
add('Y1','Device:Crystal_GND24','32MHz / CL=8pF / 10ppm',{'1':'HFXO_1','3':'HFXO_2','2':'GND','4':'GND'},'Crystal:Crystal_SMD_2016-4Pin_2.0x1.6mm')
passive('C','DNP / external load option','HFXO_1','GND',dnp=True);passive('C','DNP / external load option','HFXO_2','GND',dnp=True)
passive('L','10uH / 80mA','DCC','DECR');passive('L','10uH / 80mA','DCCD','DECD')
for value,net in [('1uF','DECR'),('1uF','DECR'),('2.2nF','DECR'),('1uF','DECD'),('100nF','DECN'),('1uF','DECA'),('4.7uF','DECUSB')]:cap(value,net)
for i in range(8):cap('100nF','VDD_1V8')
cap('4.7uF','VDD_1V8')
passive('L','2.2nH / RF C0G reference','RF_ANT','RF_50R')
cap('0.7pF C0G','RF_50R')
res('0R / antenna tuning','RF_50R','ANT_FEED')
passive('C','DNP / tune in enclosure','ANT_FEED','GND',dnp=True)
add('ANT1','Device:Antenna','2450AT43B0100001E',{'1':'ANT_FEED'})
add('J3','Connector_Generic:Conn_01x05','SWD DEBUG / 1.8V',{'1':'VDD_1V8','2':'SWDIO','3':'SWDCLK','4':'MCU_RESET','5':'GND'},'Connector_PinHeader_1.27mm:PinHeader_1x05_P1.27mm_Vertical')
res('10k','VDD_1V8','MCU_RESET');res('10k','VDD_1V8','DAC_RESET')
for n in ['I2C_SDA','I2C_SCL','DAC_INT_L','DAC_INT_R']:res('4.7k','VDD_1V8',n)
for a,b in [('I2S_MCLK_SRC','I2S_MCLK'),('I2S_BCLK_SRC','I2S_BCLK'),('I2S_LRCK_SRC','I2S_LRCK'),('I2S_DATA_SRC','I2S_DATA')]:res('22R',a,b)
add('JP9','Jumper:SolderJumper_3_Open','MODE: 1-2 ECO / 2-3 TURBO',{'1':'GND','2':'MODE_SENSE','3':'VDD_1V8'},'Jumper:SolderJumper-3_P1.3mm_Open_RoundedPad1.0x1.5mm_NumberLabels')
res('100k','MODE_SENSE','GND');cap('10nF','MODE_SENSE')
for n in ['AMP_EN','CHG_EN']:res('100k',n,'GND')

for ref,ch,sheet in [('U2','L','04_DAC_Left'),('U3','R','05_DAC_Right')]:
    page=sheet
    pref='DAC_'+ch+'_'
    c={'1':'I2C_SCL','2':'I2S_DATA','4':'VDD_1V8','5':pref+'FILT_P','6':pref+'FILT_N','7':pref+'VA','8':'GND','9':pref+'NEG_VA','10':pref+'FLYP_VA','11':pref+'FLYN_VA','13':'GND','14':'DAC_'+ch+'P','16':'DAC_'+ch+'N','17':'GND','18':pref+'VCPF_N','19':'GND','20':pref+'FLYN_CP','21':pref+'VCPF_P','23':pref+'FLYC_CP','24':pref+'FLYP_CP','25':'VDD_1V8','26':'VBAT','27':'DAC_INT_'+ch,'28':'DAC_RESET','30':'GND' if ch=='L' else 'VDD_1V8','31':'VDD_1V8','34':'I2S_BCLK','35':'GND','36':'GND','37':'I2S_MCLK','38':'I2S_LRCK','39':'I2C_SDA','41':'GND'}
    add(ref,'HD800_Custom:CS43131_CNZ','CS43131-CNZR / '+ch+' mono',c)
    res('2R 1%','VDD_1V8',pref+'VA');cap('10uF',pref+'VA');cap('100nF',pref+'VA')
    for _ in range(3):cap('100nF','VDD_1V8')
    cap('2.2uF','VDD_1V8');cap('4.7uF','VBAT');cap('100nF','VBAT')
    for a,b,v in [('FILT_P','VA','15uF'),('FILT_N','NEG_VA','15uF'),('NEG_VA',None,'2.2uF'),('FLYP_VA','FLYN_VA','2.2uF'),('FLYP_CP','FLYC_CP','2.2uF'),('FLYC_CP','FLYN_CP','2.2uF'),('VCPF_P',None,'2.2uF'),('VCPF_N',None,'2.2uF')]:cap(v,pref+a,pref+b if b else 'GND')

page='06_Balanced_Output'
config_3_fp='Jumper:SolderJumper-3_P1.3mm_Open_RoundedPad1.0x1.5mm_NumberLabels'
config_2_fp='Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm'
for ch,buf in [('L','U5'),('R','U8')]:
    add(buf,'HD800_Custom:OPA1688IDR','OPA1688IDR / '+ch,{'1':'BUF_'+ch+'P_RAW','2':'BUF_'+ch+'P_RAW','3':'BUF_'+ch+'P_IN','4':'AMP_VN','5':'BUF_'+ch+'N_IN','6':'BUF_'+ch+'N_RAW','7':'BUF_'+ch+'N_RAW','8':'AMP_VP'},'Package_SO:SOIC-8_3.9x4.9mm_P1.27mm')
    for sign in ['P','N']:
        leg_index={('L','P'):0,('L','N'):1,('R','P'):2,('R','N'):3}[(ch,sign)]
        res('1R / tune stability','BUF_'+ch+sign+'_RAW','BUF_'+ch+sign)
        add('JP'+str(1+leg_index*2),'Jumper:SolderJumper_3_Open','CONFIG '+ch+sign+': 1-2 ECO / 2-3 TURBO',{'1':'DAC_'+ch+sign,'2':'DRV_'+ch+sign,'3':'BUF_'+ch+sign},config_3_fp)
        add('JP'+str(2+leg_index*2),'Jumper:SolderJumper_2_Open','TURBO INPUT '+ch+sign+': CLOSE',{'1':'DAC_'+ch+sign,'2':'BUF_'+ch+sign+'_IN'},config_2_fp)
    cap('100nF','AMP_VP');cap('100nF','AMP_VN');cap('4.7uF','AMP_VP');cap('4.7uF','AMP_VN')
    for _ in range(2):cap('100nF','VDD_1V8');cap('1uF','VDD_1V8')
for i,(name,net) in enumerate([('LEFT DRIVER +','DRV_LP'),('LEFT DRIVER -','DRV_LN'),('RIGHT DRIVER +','DRV_RP'),('RIGHT DRIVER -','DRV_RN')],1):
    add('TP'+str(i),'Connector:TestPoint',name+' / DIRECT SOLDER',{'1':net},'Connector_Wire:SolderWirePad_1x01_SMD_1.5x3mm')

notes={
'01_USB_Charging':['IP2312 fixed 4.20V variant only; 135k sets nominal 1A. Confirm selected cell permits 1C charge.', 'Q3 default OFF. Enable charging only after valid USB-C >=1.5A advertisement; never assume 2A.', 'No system power path: charge only with playback stopped; verify termination with MCU load.', 'External protected 1S pack required. J4: bonded 100k NTC; confirm thermistor curve and thresholds.', 'L2 changed to 1uH per charger reference; select >=4A saturation part and verify temperature.'],
'02_Power':['TLV62568: 0.6V x (1 + 200k/100k) = 1.8V. L1 remains 2.2uH.', 'AMP_EN high turns Q2/Q1 on; LM2776 generates approximately -VBAT, subject to load droop.', 'Split rails are battery dependent. Limit output in firmware; >250mW into 18 ohms is NOT validated.', 'SW2 closes to force system OFF. Battery charger remains independent.'],
'03_MCU_RF':['Firmware: use HFCLKAUDIO 12.288MHz for 48kHz family; do not feed raw 32MHz to DACs.', 'Configure internal HFXO load for CL=8pF crystal; external loading footprints DNP.', 'Copy Nordic QKAA RF/DC-DC reference layout. Tune antenna in final earcup; RF values preliminary.', 'JP9 is the fixed mode strap: 1-2 Eco, 2-3 Turbo. Firmware enables AMP rails only in Turbo.', 'Normal-voltage nRF supply: VDDH and DCCH tied to VDD. Fit DC/DC inductors and enable regulators.', 'Unused GPIO / unused interfaces explicitly NC; use calibrated LFRC.'],
'04_DAC_Left':['Configure left mono differential mode; HPOUTA=L+, HPOUTB=L-. ADR low.', 'HPREFA/B return to quiet common analog ground; never connect them to opposite output.', 'VP on battery; VA filtered by 2R/10uF; VCP, VD and VL on 1.8V.', 'CS43131 QFN pad and footprint dimensions require independent package verification.'],
'05_DAC_Right':['Configure right mono differential mode; HPOUTA=R+, HPOUTB=R-. ADR high.', 'HPREFA/B return to quiet common analog ground; never connect them to opposite output.', 'VP on battery; VA filtered by 2R/10uF; VCP, VD and VL on 1.8V.', 'Validate reset/interrupt levels against the VP-domain specifications before fabrication.'],
'06_Balanced_Output':['No analog muxes: headphone type is selected once with solder links before installation.', 'ECO / HD800: bridge each 3-pad selector 1-2; leave all four TURBO INPUT links open; JP9=1-2.', 'TURBO / planar: bridge each 3-pad selector 2-3; close all four TURBO INPUT links; JP9=2-3.', 'Eco may omit U5/U8, U4, Q1/Q2 and amplifier support parts entirely. Turbo populates them.', 'TP1-TP4 are direct driver solder pads. There is no jack and no common audio return.', 'L-/R- are driven outputs. OPA1688 current does not establish the original 250mW/18ohm target.', 'Configuration links and JP9 must agree before power-up; this design does not hot-switch modes.']}
plan={'spec':'HD800 wireless conversion from supplied system overview; assembly-configured direct or buffered output.','summary':'Draft circuit for engineering review; see sheet notes and DESIGN_NOTES.md.','sheets':[{'name':s,'title':s.replace('_',' '),'size':'A2'} for s in notes], 'parts':parts,'nets':[{'name':n,'pins':ps,'is_power':n in ['VBAT','VBUS','VDD_1V8','AMP_VP','AMP_VN','CHG_5V'],'is_ground':n=='GND'} for n,ps in nets.items() if len(ps)>1], 'open_questions':['Battery specification; RF tuning; charge termination / USB power policy; output power verification; final driver-wire pad size and strain relief.']}
(BASE/'design'/'design-plan.json').write_text(json.dumps(plan,indent=2),encoding='utf-8')
(BASE/'design'/'layout-data.json').write_text(json.dumps({'extra':extra,'notes':notes},indent=2),encoding='utf-8')
print(json.dumps({'parts':len(parts),'nets':len(plan['nets']),'pages':{s:sum(p['sheet']==s for p in parts) for s in notes}},indent=2))
