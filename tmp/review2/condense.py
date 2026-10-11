from pathlib import Path
import re, json

root = Path('/Users/krishnansirosh/Desktop/mine/DriveAI')
original = (root/'tmp/review2/main.before-condensing.tex').read_text()
matches = list(re.finditer(r'\\begin\{frame\}\[t\]\{([^\n]+)\}\n(.*?)\\end\{frame\}', original, re.S))
assert len(matches) == 37
frames = {i+1: {'title':m[1], 'body':m[2]} for i,m in enumerate(matches)}

def body(n):
    b=frames[n]['body']
    return b[:b.rfind(r'\src{')].strip()

def source(n):
    b=frames[n]['body']
    return b[b.rfind(r'\src{')+5:b.rfind('}')]

def tight(s):
    s=re.sub(r'\\setlength\\itemsep\{[\d.]+mm\}',r'\\setlength\\itemsep{0pt}',s)
    return s.replace(r'\small'+'\n','').replace(r'\par\par\smallskip',r'\par\smallskip')

compact = r'''\fontsize{8}{9}\selectfont
\renewcommand{\arraystretch}{1.06}
\setlength{\tabcolsep}{3pt}
\setlength{\abovedisplayskip}{3pt}
\setlength{\belowdisplayskip}{3pt}
'''

def frame(title, content, ids, size=True):
    content=content.replace(r'\par\smallskip',r'\par\vspace{1pt}')
    content=re.sub(r'\\begin\{(?:exampleblock|block)\}\{([^}]+)\}',r'\\textbf{\1}\\par\\vspace{1pt}',content)
    content=re.sub(r'\\end\{(?:exampleblock|block)\}',r'\\par',content)
    sources=' '.join(source(n) for n in ids)
    return '\\begin{frame}[t]{'+title+'}\n'+(compact if size else '')+content+'\n\\src{'+sources+'}\n\\end{frame}\n'

def cols(left,right,wl='.49',wr='.49'):
    return '\\begin{columns}[T,onlytextwidth]\n\\column{'+wl+'\\textwidth}\n'+left+'\n\\column{'+wr+'\\textwidth}\n'+right+'\n\\end{columns}\n'

def flatten_columns(s):
    s=re.sub(r'\\begin\{columns\}\[T,onlytextwidth\]\s*', '', s)
    s=re.sub(r'\\column\{\.[0-9]+\\textwidth\}\s*', '', s)
    return s.replace(r'\end{columns}','')

changes={}
changes[2]=(frame('Problem, Motivation and Objectives',cols(tight(body(2)),r'\textbf{Objectives and application scope}\par\smallskip'+'\n'+tight(body(3))),[2,3]),[2,3])

changes[6]=(frame('Module Details and Preprocessing',tight(body(6))+'\n\\par\\smallskip\n'+tight(body(7)),[6,7]),[6,7])

# Keep every metric row and all explanatory text. Use one common table header.
b8=body(8); b9=body(9)
rows8=b8.split(r'\midrule',1)[1].split(r'\bottomrule',1)[0]
rows9=b9.split(r'\midrule',1)[1].split(r'\bottomrule',1)[0]
rows8=rows8.replace('Measures detected positive examples; exposes missed closed eyes/yawns.','Detects positive examples; exposes missed closed eyes/yawns.')
rows8=rows8.replace('Measures reliability of positive predictions; exposes false positives.','Positive-prediction reliability; exposes false positives.')
rows9=rows9.replace('Summarizes the precision--recall curve; validation checkpoint criterion.','PR-curve summary used for validation checkpoint selection.')
rows9=rows9.replace('Temporal decision signal over a rolling 60 s window; not a classifier accuracy metric.','Temporal signal over rolling 60 s; not classifier accuracy.')
rows9=rows9.replace('Measures computation time; distinct from browser sampling rate.','Computation time, distinct from browser sampling rate.')
pre8=b8[:b8.index(r'\begin{tabularx}')].replace('\\small\n','')
tail8=b8.split(r'\end{tabularx}',1)[1]
tail9=b9.split(r'\end{tabularx}',1)[1]
table=r'''\begin{tabularx}{\textwidth}{L{3.1cm} L{3.4cm} Y}
\toprule
\textbf{Metric / measure} & \textbf{Formula / definition} & \textbf{Purpose and application fit}\\\midrule
'''+rows8+rows9+r'\bottomrule\end{tabularx}'
changes[8]=(frame('Metrics, Formulas and Literature Benchmark',pre8+table+tail8+tail9,[8,9]),[8,9])

# Two full-width tables, followed by their original discussions in columns.
result_tables=[]; result_discussions=[]
for n in (21,22):
    b=tight(body(n))
    pre,post=b.split(r'\begin{itemize}',1)
    result_tables.append(pre)
    result_discussions.append(r'\begin{itemize}'+post)
changes[21]=(frame('Results: Eye States and Mouth Events',r'\renewcommand{\arraystretch}{1.0}'+'\n'+'\n'.join(result_tables)+cols(*result_discussions),[21,22]),[21,22])

# Four editable plots. Coordinates, axes and legends are retained.
curves=[]; notes=[]
for n in (23,24):
    b=body(n)
    c,tail=b.split(r'\end{columns}',1)
    c+=r'\end{columns}'
    c=c.replace('height=4.9cm','height=2.95cm')
    c=c.replace('legend style={font=\\tiny,at={(.98,.02)},anchor=south east}', 'legend columns=3,legend style={font=\\tiny,at={(.5,.02)},anchor=south}')
    c=c.replace('legend style={font=\\scriptsize,at={(.98,.98)},anchor=north east}', 'legend columns=2,legend style={font=\\tiny,at={(.5,.98)},anchor=north}')
    c=c.replace(r'\textbf{Eye:',r'\textbf{Eye:').replace(r'\smallnote',r'\smallnote')
    curves.append(c)
    notes.append(tail)
changes[23]=(frame('Training Curves: Validation AP and MobileNet Loss','\n'.join(curves)+'\n'+''.join(notes),[23,24]),[23,24])

# Combine attribution with contribution; retain split verification separately.
dataset_body=tight(flatten_columns(body(27))).replace('Official UTA-RLDD source}', 'Official UTA-RLDD source}\\par\\smallskip')
changes[27]=(frame('Datasets, Attribution and Processing Contribution',cols(dataset_body,r'\textbf{Processing contribution and evaluation limits}\par\smallskip'+'\n'+tight(body(29))),[27,29]),[27,29])

def screenshot_pair(a,b,title):
    ba=body(a); bb=body(b)
    # The original entry crop is retained; other images remain uncropped.
    ba=re.sub(r'width=\.96\\textwidth,height=[\d.]+cm',r'width=\\linewidth,height=4.3cm',ba)
    bb=re.sub(r'width=\.96\\textwidth,height=[\d.]+cm',r'width=\\linewidth,height=4.3cm',bb)
    ba=r'\textbf{'+frames[a]['title'].split(': ',1)[1]+r'}\par\smallskip'+'\n'+tight(ba)
    bb=r'\textbf{'+frames[b]['title'].split(': ',1)[1]+r'}\par\smallskip'+'\n'+tight(bb)
    return frame(title,cols(ba,bb),[a,b])

changes[30]=(screenshot_pair(30,31,'UI: Application Entry and Model Comparison'),[30,31])
changes[33]=(screenshot_pair(33,34,'UI: Spoken Intervention and Simulated Rest Route'),[33,34])

b35=tight(body(35)).replace(r'{\textwidth}{L{3.2cm} Y}',r'{\linewidth}{L{1.7cm} Y}')
status_rows=b35.split(r'\midrule',1)[1].split(r'\bottomrule',1)[0]
status_paragraphs=[]
for row in status_rows.split(r'\\'):
    if '&' in row:
        label,detail=row.strip().split('&',1)
        status_paragraphs.append(r'\textbf{'+label.strip()+':} '+detail.strip()+r'\par\vspace{2pt}')
b35=r'\textbf{Validation evidence and observed status}\par\smallskip'+'\n'+'\n'.join(status_paragraphs)+b35.split(r'\end{tabularx}',1)[1]
b36=tight(flatten_columns(body(36)))
changes[35]=(frame('Validation, Project Outcomes and Next Steps',cols(b35,b36),[35,36]),[35,36])

skip=set(); out=[]; mapping=[]
for n in frames:
    if n in skip: continue
    if n in changes:
        content,ids=changes[n]
        skip.update(ids[1:])
    else:
        content=matches[n-1][0]+'\n'
        ids=[n]
    out.append(content)
    mapping.append({'new_slide':len(out),'old_slides':ids,'title':re.search(r'\\begin\{frame\}\[t\]\{(.*?)\}',content)[1]})

assert len(out)==28
new=original[:matches[0].start()]+'\n'.join(out)+'\n\\end{document}\n'
new=new.replace('justification on slide 4','justification on slide 3').replace('slides 4, 9 and 13','slides 3, 6 and 10')
(root/'main.tex').write_text(new)
(root/'tmp/review2/condensed/slide_mapping.json').write_text(json.dumps(mapping,indent=2))
print('Created 28-slide version; all 37 original frames mapped.')
