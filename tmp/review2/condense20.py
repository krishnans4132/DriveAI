from pathlib import Path
import re, json

# Reuse the source-preserving transformations, without writing the 28-slide deck.
helper=Path(__file__).with_name('condense.py').read_text().split('skip=set(); out=[]; mapping=[]')[0]
exec(compile(helper, 'condense.py', 'exec'))

def content_of(frame_source):
    return frame_source.split('\n',1)[1].rsplit(r'\src{',1)[0]

def section(title, text):
    return r'\textbf{'+title+r'}\par\smallskip'+'\n'+text

def columns3(a,b,c):
    return r'\begin{columns}[T,onlytextwidth]'+'\n'+''.join(r'\column{.32\textwidth}'+'\n'+v+'\n' for v in (a,b,c))+r'\end{columns}'

compact=r'''\fontsize{10}{11.5}\selectfont
\renewcommand{\arraystretch}{1.06}
\setlength{\tabcolsep}{4pt}
\setlength{\abovedisplayskip}{4pt}
\setlength{\belowdisplayskip}{4pt}
'''

def adapted(text):
    # Earlier merged frames use the same text with smaller-page sizing.
    text=text.replace(r'\fontsize{8}{9}\selectfont',r'\fontsize{10}{11.5}\selectfont')
    return text

out=[]; mapping=[]
def add(title, text, ids, size=True):
    out.append(frame(title,text,ids,size))
    mapping.append({'new_slide':len(out),'old_slides':ids,'title':title})

out.append(matches[0][0]+'\n')
mapping.append({'new_slide':1,'old_slides':[1],'title':frames[1]['title']})
add('Problem, Motivation and Objectives', adapted(content_of(changes[2][0])),[2,3])
add('15-Paper Literature Review (2025--2026) and Contribution',body(4)+'\n\\par\\medskip\n'+tight(body(13)),[4,13])

# Overall application and the six original module records.
module_rows=body(6).split(r'\midrule',1)[1].split(r'\bottomrule',1)[0]
module_table=r'''\begin{tabularx}{\linewidth}{L{2.1cm} L{2.1cm} Y}
\toprule\textbf{Module} & \textbf{Input} & \textbf{Processing and output}\\\midrule
'''
for row in module_rows.split(r'\\'):
    if '&' in row:
        name,inp,proc,output=[s.strip() for s in row.split('&')]
        module_table+=name+' & '+inp+' & '+proc+r'\newline\textbf{Output:} '+output+r'\\'+'\n'
module_table+=r'\bottomrule\end{tabularx}'
module_tail=body(6).split(r'\end{tabularx}',1)[1]
app=body(5).replace(r'\begin{tikzpicture}',r'\resizebox{\linewidth}{!}{\begin{tikzpicture}',1).replace(r'\end{tikzpicture}',r'\end{tikzpicture}}',1)
add('Overall Application Architecture and Modules',cols(app,module_table+module_tail,'.46','.52'),[5,6])

# Keep all preprocessing bullets and original dataset source/DOI links.
preprocessing=tight(flatten_columns(body(7)))
preprocessing=preprocessing.replace(r'\end{itemize}',r'\end{itemize}\par\smallskip')
add('Datasets, Preprocessing and Robustness',cols(section('Datasets and attribution',dataset_body),section('Preprocessing and robustness',preprocessing)),[27,7])

add('Dataset Splits, Processing Contribution and Limits',tight(body(28))+'\n\\par\\medskip\n'+tight(body(29)),[28,29])

# Rearrange existing architecture nodes into three vertical editable diagrams.
def architecture(n):
    b=body(n)
    diagram=re.search(r'\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}',b,re.S)[0]
    nodes=re.findall(r'\\node\[[^\n]*?\]\s*\((\w+)\)\s*\{(.*?)\};',diagram,re.S)
    assert len(nodes)==(5 if n==11 else 6)
    d=r'\begin{tikzpicture}[node distance=0.10cm]'+'\n'
    for j,(key,label) in enumerate(nodes):
        location=',below=of '+nodes[j-1][0] if j else ''
        d+=r'\node[flow,text width=5.85cm,font=\fontsize{9}{10}\selectfont,minimum height=.5cm,inner sep=1.5pt'+location+'] ('+key+') {'+label+'};\n'
    for first,second in zip(nodes,nodes[1:]):
        d+=r'\draw[arr]('+first[0]+')--('+second[0]+');\n'
    d+=r'\end{tikzpicture}'+'\n'
    rest=b.split(r'\end{tikzpicture}',1)[1]
    rest=tight(flatten_columns(rest))
    rest=rest.replace(r'\centering','')
    rest=rest.replace(r'\textbf{Role in this project}',r'\par\smallskip\textbf{Role in this project}')
    if n==12:
        rest=rest.replace(r'\column{.48\textwidth}','')
    return section(frames[n]['title'].split(':')[0],r'{\centering '+d+r'\par}'+'\n'+rest)
add('Deep Learning Architectures: Three Backbones',r'\fontsize{9}{10.5}\selectfont'+'\n'+columns3(*(architecture(n) for n in (10,11,12))),[10,11,12])

# Complexity values stay in a full-width table; prose and deployment evidence below.
complexity=tight(body(14))
comp_top,comp_tail=complexity.split(r'\begin{itemize}',1)
comp_tail=r'\begin{itemize}'+comp_tail
inference=tight(flatten_columns(body(26)))
inference=inference.replace(r'\end{tabular}',r'\end{tabular}\par\smallskip')
inference=inference.replace(r'\textbf{Measured local runtime}',r'\par\smallskip\textbf{Measured local runtime}')
left=section('Complexity interpretation',comp_tail)
right=section('Inference cost and deployment',inference)
add('Time, Space and Deployment Cost',comp_top+'\n\\par\\medskip\n'+cols(left,right,'.49','.49'),[14,26])

# Preserve every step and equation, splitting long display equations at commas.
forward=tight(body(15))
forward=forward.replace(r'\[ u=\phi(\mathrm{BN}(W_{\rm exp}*x)),\quad v=\phi(\mathrm{BN}(W_{\rm dw}*u)),\quad h=\mathrm{BN}(W_{\rm proj}*\widetilde v). \]',r'''\[\begin{aligned}
u&=\phi(\mathrm{BN}(W_{\rm exp}*x)),\\
v&=\phi(\mathrm{BN}(W_{\rm dw}*u)),\\
h&=\mathrm{BN}(W_{\rm proj}*\widetilde v).
\end{aligned}\]''')
train=tight(body(16))
train=train.replace(r',\qquad w_+=',r'.\]\[w_+=')
train=train.replace(r',\qquad \mathcal L_m',r'.\]\[\mathcal L_m')
add('Algorithms: CNN Forward Pass and Model Training',cols(section('1. CNN forward computation',forward),section('2. Training and model selection',train)),[15,16])

temporal=tight(flatten_columns(body(17)))
alert=tight(body(18)).replace(r'{\textwidth}{L{3.1cm} L{4.1cm} Y}',r'{\linewidth}{L{2.2cm} L{3.35cm} Y}')
add('Temporal Evidence, Context and Adaptive Alert Rules',cols(temporal,alert,'.49','.49'),[17,18])

hp1=tight(body(19)).replace(r'{\textwidth}{L{3cm} L{3.1cm} Y}',r'{\linewidth}{L{2.3cm} L{3cm} Y}')
hp2=tight(body(20)).replace(r'{\textwidth}{L{3.4cm} L{3.3cm} Y}',r'{\linewidth}{L{2.5cm} L{3cm} Y}')
add('Hyperparameters, Input Settings and Justification',cols(section('Training',hp1),section('Input and decision parameters',hp2)),[19,20])

add('Metrics, Formulas and Literature Benchmark',adapted(content_of(changes[8][0])),[8,9])
add('Results: Eye States and Mouth Events',adapted(content_of(changes[21][0])),[21,22])
add(frames[25]['title'],body(25),[25])

charts=adapted(content_of(changes[23][0]))
charts=charts.replace('width=7.05cm,height=2.95cm','width=9.7cm,height=4.05cm')
charts=charts.replace('ymin=0,grid=major','ymin=0,ymax=.65,grid=major')
add('Training Curves: Validation AP and MobileNet Loss',charts,[23,24])

ui1=adapted(content_of(changes[30][0])).replace('height=4.3cm','height=7cm')
add('UI: Application Entry and Model Comparison',ui1,[30,31])
monitor=body(32).replace('height=5.55cm','height=9.5cm')
add(frames[32]['title'],monitor,[32])
ui2=adapted(content_of(changes[33][0])).replace('height=4.3cm','height=7cm')
add('UI: Spoken Intervention and Simulated Rest Route',ui2,[33,34])

add('Validation, Project Outcomes and Next Steps',adapted(content_of(changes[35][0])),[35,36])
add(frames[37]['title'],body(37),[37])

assert len(out)==20
assert sorted(n for m in mapping for n in m['old_slides'])==list(range(1,38))

preamble=original[:matches[0].start()]
preamble=preamble.replace(r'\usetheme{Madrid}',r'''\usetheme{Madrid}
% Larger 16:9 canvas accommodates the complete review in exactly 20 slides.
\geometry{paperwidth=224mm,paperheight=126mm}
\setbeamerfont{normal text}{size=\normalsize}''')
new=preamble+'\n'.join(out)+'\n\\end{document}\n'
new=new.replace('justification on slide 4','justification on slide 3').replace('slides 4, 9 and 13','slides 3 and 12')
(root/'main.tex').write_text(new)
(root/'tmp/review2/condensed/slide_mapping_20.json').write_text(json.dumps(mapping,indent=2))
print('Exactly 20 slides; all 37 original frames mapped once.')
