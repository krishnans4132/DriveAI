import json,time,platform,subprocess,csv
from pathlib import Path
import numpy as np
import torch
from torch import nn
from torchvision import models
from backend.model_runtime import MobileNetFatigueRuntime
root=Path.cwd(); torch.set_num_threads(4)
records=[]
for name,fn in [('MobileNetV3-Small',models.mobilenet_v3_small),('EfficientNet-B0',models.efficientnet_b0),('ResNet-18',models.resnet18)]:
 for task,width,outputs in [('eye',192,1),('mouth',160,3)]:
  m=fn(weights=None).eval()
  if name=='ResNet-18': m.fc=nn.Linear(m.fc.in_features,outputs)
  else:
   idx=3 if name=='MobileNetV3-Small' else 1
   m.classifier[idx]=nn.Linear(m.classifier[idx].in_features,outputs)
  mac=[0]; acts=[0]; handles=[]
  def hook(mod,inp,out):
   if isinstance(mod,nn.Conv2d): mac[0]+=out.numel()*(mod.in_channels//mod.groups)*mod.kernel_size[0]*mod.kernel_size[1]
   elif isinstance(mod,nn.Linear): mac[0]+=out.numel()*mod.in_features
   acts[0]=max(acts[0],out.numel())
  for mod in m.modules():
   if isinstance(mod,(nn.Conv2d,nn.Linear)):handles.append(mod.register_forward_hook(hook))
  with torch.inference_mode():m(torch.zeros(1,3,96,width))
  for h in handles:h.remove()
  params=sum(p.numel() for p in m.parameters())
  records.append(dict(architecture=name,task=task,parameters=params,conv_linear_macs=mac[0],fp32_parameter_mib=params*4/1024**2,largest_conv_linear_output_elements=acts[0]))
  del m
runtime=MobileNetFatigueRuntime()
rng=np.random.default_rng(42)
eye=rng.integers(0,256,(96,192,3),dtype=np.uint8);mouth=rng.integers(0,256,(96,160,3),dtype=np.uint8)
for _ in range(20):runtime.predict(eye,mouth)
timings=[]
for _ in range(100):
 t=time.perf_counter();runtime.predict(eye,mouth);timings.append((time.perf_counter()-t)*1000)
result={'models':records,'latency':{'measurement':'Pair of deployed PyTorch CPU classifiers plus crop normalization; synthetic uint8 crops; excludes face detection, JPEG/API and browser','cpu':subprocess.check_output(['sysctl','-n','machdep.cpu.brand_string'],text=True).strip(),'torch_version':torch.__version__,'threads':torch.get_num_threads(),'warmup':20,'runs':100,'median_ms':float(np.median(timings)),'p95_ms':float(np.percentile(timings,95)),'mean_ms':float(np.mean(timings))},'split_counts':{}}
for task in ['eye','mouth']:
 result['split_counts'][task]={};people={}
 for split in ['train','val','test']:
  with (root/f'ml/processed_data_v2/splits/{task}_{split}_provisional.csv').open() as f:rows=list(csv.DictReader(f))
  people[split]={(r['dataset'],r['person_id']) for r in rows}
  result['split_counts'][task][split]={'samples':len(rows),'participants':len(people[split]),'classes':{c:sum(r['label']==c for r in rows) for c in sorted({r['label'] for r in rows})}}
 result['split_counts'][task]['participant_overlaps']={a+'_'+b:len(people[a]&people[b]) for a,b in [('train','val'),('train','test'),('val','test')]}
(root/'presentation_assets/evidence.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
