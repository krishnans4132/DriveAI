import csv,json,shutil
from pathlib import Path
root=Path.cwd();out=root/'presentation_assets'
e=json.loads((out/'evidence.json').read_text())
macs={}
for r in e['models']:
 macs.setdefault(r['architecture'],{})[r['task']]=r
names=[('MobileNetV3-Small','MobileNet','ml/models/eye_v3/drivealert_eye_v3_history.csv'),('EfficientNet-B0','EfficientNet','ml/results/efficientnet_b0/eye/drivealert_eye_efficientnet_b0_v1_history.csv'),('ResNet-18','ResNet','ml/results/resnet18/eye/drivealert_eye_resnet18_v1_history.csv')]
macrow=[]
for name,short,p in names:
 a=macs[name]['eye']; b=macs[name]['mouth']
 macrow.append(f"{name} & {a['parameters']/1e6:.3f} / {b['parameters']/1e6:.3f} & {a['conv_linear_macs']/1e6:.2f} & {b['conv_linear_macs']/1e6:.2f} & {(a['fp32_parameter_mib']+b['fp32_parameter_mib']):.2f} \\\\")
(out/'complexity_rows.tex').write_text('\n'.join(macrow)+'\n')
(out/'benchmark_values.tex').write_text('\\newcommand{\\MedianLatency}{%.2f}\n\\newcommand{\\PninetyfiveLatency}{%.2f}\n'%(e['latency']['median_ms'],e['latency']['p95_ms']))
for task in ['eye','mouth']:
 series=[]
 for idx,(name,short,p) in enumerate(names):
  if task=='mouth':p=p.replace('/eye/','/mouth/').replace('/eye_v3/','/mouth_v1/').replace('_eye_','_mouth_').replace('mouth_v3','mouth_v1')
  with (root/p).open() as f:rows=list(csv.DictReader(f))
  series.append((short,rows))
 colors=['AmritaRed','teal!80!black','DarkSlate']
 plots=[]
 for idx,(short,rows) in enumerate(series):
  key='ap' if task=='eye' else 'macro_ap'
  coords=' '.join('(%s,%.4f)'%(r['epoch'],100*float(r[key])) for r in rows)
  plots.append('\\addplot+[color=%s,mark=%s,thick] coordinates {%s};\\addlegendentry{%s}'%(colors[idx],['*','square*','triangle*'][idx],coords,short))
 (out/f'{task}_ap_plot.tex').write_text('\n'.join(plots)+'\n')
for task,p in [('eye',root/'ml/models/eye_v3/drivealert_eye_v3_history.csv'),('mouth',root/'ml/models/mouth_v1/drivealert_mouth_v1_history.csv')]:
 with p.open() as f:rows=list(csv.DictReader(f))
 lines=[]
 for key,color,label in [('train_loss','AmritaRed','Training'),('loss','DarkSlate','Validation')]:
  coords=' '.join('(%s,%.5f)'%(r['epoch'],float(r[key])) for r in rows)
  lines.append('\\addplot+[color=%s,mark=*,thick] coordinates {%s};\\addlegendentry{%s}'%(color,coords,label))
 (out/f'{task}_loss_plot.tex').write_text('\n'.join(lines)+'\n')
print('Prepared editable plot coordinates and measured values.')
