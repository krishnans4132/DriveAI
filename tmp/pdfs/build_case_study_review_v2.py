from pathlib import Path
import re

base = Path(__file__).with_name('build_case_study_review.py').read_text()
out = Path('/Users/krishnansirosh/Desktop/mine/DriveAI/output/pdf')
out.mkdir(parents=True, exist_ok=True)
base = re.sub(r'OUTPUT = .*', 'OUTPUT = ' + repr(str(out / 'DriveAlert_Case_Study_Review_2_15_Papers.pdf')), base, count=1)
base = base.replace('03 SEPTEMBER 2026', '16 SEPTEMBER 2026').replace('3 September 2026', '16 September 2026')
base = base.replace('nine journal articles', 'fifteen journal articles').replace('assigns three papers', 'assigns five papers')
base = base.replace('Allocate three relevant papers', 'Allocate five distinct relevant papers')
base = base.replace('distributes nine recent journal studies', 'distributes fifteen recent journal studies')
# Keep the nine existing paper identifiers stable; move contextual references after the 15 study papers.
base = re.sub(r'\[(10|11|12|13)\]', lambda m: '[' + str(int(m.group(1)) + 6) + ']', base)
base = base.replace('Included: one 2026 implementation paper from a journal listed by SCImago as the primary standard paper.', 'Included: only 2025 or 2026 journal articles in SCImago-listed journals; one 2026 implementation article remains the primary submission paper.')
base = base.replace('The source review was completed on 16 September 2026.', 'The expanded source review was completed on 16 September 2026. Publisher publication years, journal titles, and DOI records were checked separately from journal-level SCImago listing evidence. A 2025 component within a DOI is not necessarily the publication year. Appendix A records journal-listing evidence and access limitations. Research gaps labeled below are this team\'s critical interpretation unless explicitly attributed to the authors.')
base = base.replace('"[1]-[3]", "Lightweight', '"[1]-[3], [10], [11]", "Lightweight')
base = base.replace('"[4]-[6]", "Multi-region', '"[4]-[6], [12], [13]", "Multi-region')
base = base.replace('"[7]-[9]", "Multimodal', '"[7]-[9], [14], [15]", "Multimodal')
base = base.replace('literature [1]-[3];', 'literature [1]-[3], [10], [11];')
base = base.replace('literature [4]-[6];', 'literature [4]-[6], [12], [13];')
base = base.replace('literature [7]-[9];', 'literature [7]-[9], [14], [15];')
base = base.replace('literature spans compact CNNs', 'literature spans compact CNNs')

papers = [
    dict(id=10, title='Confidence-driven adaptive time windows (2026)',
         body='Xie and Xiao [10] combine MobileNetV3, attention, a bidirectional LSTM, and Monte Carlo dropout to estimate fatigue and confidence. Confidence controls a 5-30 second observation window. The authors evaluate NTHU-DDD, YawDD, UTA-RLDD, and DROZY, reporting 88.6-91.8% within-dataset accuracy and a 35.2% reduction in false alarms relative to a fixed 15-second baseline.',
         gap='Adaptive temporal warning is already established here and cannot be claimed as unique to DriveAlert. The open question for our project is whether speed and continuous-drive duration add value beyond confidence-based adaptation at a comparable false-alarm rate. Its dataset descriptions and runtime accounting also warrant checking against original dataset documentation before reproducing the study.',
         use='Compare a fixed-window baseline, confidence adaptation, and DriveAlert context adaptation; record detection delay and false alarms per hour.',
         ref='W. Xie and P. Xiao, "Confidence-driven adaptive time window for real-time driver fatigue detection in Level 2-3 autonomous vehicles: a multi-dataset validation study," <i>Frontiers in Neurorobotics</i>, vol. 20, 2026.', doi='10.3389/fnbot.2026.1857548',
         row=['2026', 'RGB face video', 'Confidence-adaptive windows', 'Jetson runtime reported', 'Added value of vehicle context']),
    dict(id=11, title='YOLO-FDCL for complex lighting (2025)',
         body='Liu et al. [11] introduce MobileNetV4 into a YOLOv8 detector and use RepFPN for feature fusion. Their augmented complex-lighting dataset tests sensitivity to brightness and appearance changes. On YawDD, the authors report mAP@0.5 of 98.8% and recall of 97.5%. These are detection-task metrics, not directly comparable with DriveAlert\'s crop-classification accuracy.',
         gap='Synthetic lighting transformations cannot establish robustness to all physical camera effects, glare, infrared illumination, or unseen drivers. The augmented CLDFD data are available on request, which also limits immediate replication. The paper does not establish the effectiveness of spoken rest advice or vehicle-context alert policies.',
         use='Add lighting and camera-quality stress tests to the MobileNet deployment study; measure detection and classification failures separately.',
         ref='G. Liu, K. Wu, W. Lan, and Y. Wu, "YOLO-FDCL: Improved YOLOv8 for Driver Fatigue Detection in Complex Lighting Conditions," <i>Sensors</i>, vol. 25, no. 15, art. 4832, 2025.', doi='10.3390/s25154832',
         row=['2025', 'RGB object detection', 'Not the main contribution', 'MobileNetV4 + RepFPN', 'Synthetic-to-real lighting transfer']),
    dict(id=12, title='EffRes-DrowsyNet: EfficientNetB0 and ResNet50 (2025)',
         body='Al-Gburi et al. [12] combine EfficientNetB0 and ResNet50 in a hybrid visual classifier. They report 97.71% accuracy on SUST-DDD, 92.73% on YawDD, and 95.14% on NTHU-DDD. This is a direct architecture-related study for the EfficientNet member, showing a different use of EfficientNet as one branch of a hybrid model.',
         gap='Results on several datasets do not automatically demonstrate train-on-one, test-on-another transfer. The hybrid also does not establish that its extra computation is justified on the laptop used by DriveAlert. A matched standalone-versus-hybrid ablation with participant-disjoint splits and runtime measurements is needed.',
         use='Explain the difference between efficient standalone deployment and hybrid feature learning; compare accuracy gains against memory and latency costs. ResNet50 evidence must not be presented as direct ResNet-18 evidence.',
         ref='S. H. Al-Gburi et al., "EffRes-DrowsyNet: A Novel Hybrid Deep Learning Model Combining EfficientNetB0 and ResNet50 for Driver Drowsiness Detection," <i>Sensors</i>, vol. 25, no. 12, art. 3711, 2025.', doi='10.3390/s25123711',
         row=['2025', 'RGB video/images', 'Hybrid feature extraction', 'Three dataset evaluations', 'Matched accuracy-runtime trade-off']),
    dict(id=13, title='Hybrid facial features and ensemble learning (2025)',
         body='Xu et al. [13] extract 20 features from eyes, mouth, head pose, and gaze using MediaPipe. Adaptive personal calibration precedes a soft-voting ensemble of random forest, MLP, and XGBoost. On UTA-RLDD, leave-one-participant-out evaluation covers 60 drivers and reports 86.52% video accuracy. SHAP is used to interpret feature contributions.',
         gap='The initial alert-state calibration assumes suitable baseline observations from a new driver. Classification of intermediate fatigue states remains difficult, and video-level aggregation differs from frame accuracy. This method therefore supplies a useful complementary baseline, rather than direct evidence that one CNN architecture is best.',
         use='Benchmark temporal aggregation and the benefit of multiple facial regions; distinguish participant-dependent, participant-independent, frame, and video results in the comparison window.',
         ref='C. Xu, W. Huang, J. Liu, and L. Li, "Detecting Driver Drowsiness Using Hybrid Facial Features and Ensemble Learning," <i>Information</i>, vol. 16, no. 4, art. 294, 2025.', doi='10.3390/info16040294',
         row=['2025', '20 facial features', 'Video aggregation', '60-driver LOPO evaluation', 'Personal calibration and mild fatigue']),
    dict(id=14, title='Attention-enhanced CNN benchmarking (2026)',
         body='El-Nabi et al. [14] compare pretrained CNNs with a custom attention-enhanced network using eye and mouth behavior on NTHU-DDD. The abstract reports 99.63% accuracy and perfect precision, recall, and F1. The article is relevant to Eric\'s benchmark role because it examines whether attention and larger feature extractors improve visual classification.',
         gap='The combination of imperfect accuracy and perfect precision/recall/F1 needs clarification of classes, averaging, splits, and rounding before reuse. The paper also names a "ResNet150" baseline, so implementation details must be checked rather than assuming a standard ResNet-18 comparison. Strong results on one benchmark do not establish cross-driver or on-road reliability.',
         use='Use this paper for critical benchmark reading: request confusion matrices, exact architectures, identical test splits, and measured hardware performance before accepting an accuracy-leader claim.',
         ref='S. Abd El-Nabi et al., "Dynamic driver drowsiness detection with attention enhanced convolutional neural networks for real time monitoring and road safety applications," <i>Scientific Reports</i>, vol. 16, art. 26340, 2026.', doi='10.1038/s41598-025-33727-8',
         row=['2026', 'RGB eye/mouth behavior', 'Attention CNN', 'NTHU-DDD evaluation', 'Metric consistency and generalization']),
    dict(id=15, title='Review of CNN approaches to drowsiness detection (2026)',
         body='Rabbi, Em, and Hossen [15] review CNN approaches including VGG, ResNet, and Inception, and discuss lightweight architectures for constrained devices. The review identifies data bias, overfitting, computational limitations, and environmental variation, and considers multimodal fusion and integration with driver-assistance systems.',
         gap='A review synthesizes other studies; it is not a new controlled experiment demonstrating superiority of a model. Different datasets and evaluation protocols limit direct ranking of the surveyed accuracies. Practical gains from multimodal fusion and intervention require dedicated trials.',
         use='Support the rationale for selecting a compact deployment model alongside a larger residual-network benchmark, and organize discussion of accuracy, resources, robustness, and intervention evidence.',
         ref='R. I. Rabbi, P. P. Em, and M. J. Hossen, "Smart driving with AI: A review of CNN approaches to drowsiness detection," <i>Array</i>, vol. 29, art. 100675, 2026.', doi='10.1016/j.array.2025.100675',
         row=['2026', 'CNN literature review', 'Surveyed methods', 'Edge-computing synthesis', 'No common experimental protocol']),
]

def paper_code(p):
    return '\n'.join([
        'story.append(P(' + repr('Paper ' + str(p['id']) + ': ' + p['title']) + ', "H3"))',
        'story.append(P(' + repr(p['body']) + '))',
        'story.append(P(' + repr('<b>Research gap:</b> ' + p['gap']) + '))',
        'story.append(P(' + repr('<b>Relevance to DriveAlert:</b> ' + p['use']) + '))',
    ]) + '\n\n'

for marker, pair in [
    ('story.append(P("3.2 ', papers[:2]),
    ('story.append(P("3.3 ', papers[2:4]),
    ('story.append(P("4. Comparative', papers[4:]),
]:
    pos = base.index(marker)
    base = base[:pos] + ''.join(paper_code(p) for p in pair) + base[pos:]

# Add the six new studies to the actual synthesis and bibliography, not just the count.
pos = base.index('\n]\nstory.append(table(comparison')
base = base[:pos] + '\n' + '\n'.join('    ' + repr(['[' + str(p['id']) + ']'] + p['row']) + ',' for p in papers) + base[pos:]
pos = base.index("    '[16] F. Ecarnot")
refs = []
for p in papers:
    refs.append('[' + str(p['id']) + '] ' + p['ref'] + ' <link href="https://doi.org/' + p['doi'] + '">doi:' + p['doi'] + '</link>.')
base = base[:pos] + ''.join('    ' + repr(r) + ',\n' for r in refs) + base[pos:]

base = base.replace('Most systems do not connect vehicle risk or time-on-task to alert sensitivity [8], [9].', 'Confidence-based window adaptation already exists [10]; the added benefit of vehicle speed and drive duration needs evaluation.')
base = base.replace('The literature supports the project\'s use', 'The literature supports the project\'s use')
base = base.replace('Existing studies separately demonstrate accurate visual classification, temporal modeling, efficient hardware, adaptive calibration, multimodal fusion, or driver alerts.', 'Existing studies demonstrate accurate visual classification, temporal modeling, efficient hardware, adaptive calibration, multimodal fusion, and driver alerts. In particular, [10] already combines MobileNetV3, temporal inference, confidence adaptation, and multi-dataset evaluation. Adaptive warning alone is therefore not a new contribution.')
base = base.replace('Comparative synthesis shows that no single reviewed implementation jointly provides', 'Within this targeted selection, no study was identified that evaluates the full DriveAlert combination of')
base = base.replace('The reviewed literature does not jointly demonstrate, under one reproducible participant-disjoint protocol,', 'Within this targeted review, the remaining project-specific question is how to evaluate, under one reproducible participant-disjoint protocol,')
base = base.replace('before effectiveness claims are made.', 'before effectiveness claims are made.')
discussion = '''story.append(P("The expanded evidence narrows the novelty claim. Paper [10] already implements adaptive temporal warning; [11] examines lighting robustness; [12] and [13] examine hybrid models and personal calibration; and [14] and [15] reinforce the need for comparable metrics and deployment evidence. DriveAlert should test whether its speed and continuous-drive policy improves delay and false alarms beyond a fixed policy and a confidence-adaptive policy, then separately test whether the spoken rest intervention changes user response."))\n\n'''
base = base.replace('story.append(P("8. Conclusion", "H1"))', discussion + 'story.append(P("8. Conclusion", "H1"))')
base = base.replace('"A Literature Survey and Research-Gap Analysis for Lightweight Edge Deployment and Proactive Intervention"', '"Literature Survey and Research-Gap Analysis | 15 Journal Papers | Five per Member | 2025-2026"')
base = base.replace('"Funding", "H2"', '"Funding Declaration for Team Confirmation", "H2"').replace('"Conflict of Interest", "H2"', '"Conflict of Interest for Team Confirmation", "H2"')
base = base.replace('The team declares no known conflict of interest relevant to this review.', 'Each member should confirm any relevant conflicts before submission; none have been provided in the project context.')
base = base.replace('The 2026 primary paper is reference [1]. Before final college submission,', 'The selected set contains exactly 15 distinct journal articles from 2025-2026: five per member, including two review articles [8] and [15]. Contextual references [16]-[19] are excluded from the 15-paper count. The primary 2026 paper remains [1]. Before final college submission,')

appendix = '''
story.append(PageBreak())
story.append(P("Appendix A. Journal Listing Evidence", "H1"))
story.append(P("Paper year and journal listing are separate checks. The selected papers carry publisher publication years of 2025 or 2026. SCImago evidence below confirms journal identity where retrievable; an older ranking year is not the publication year of the selected paper. Quartiles are intentionally omitted because they vary by year and subject category. Links were checked on 16 September 2026."))
listing_rows = [
    ["Journal / selected papers", "SCImago evidence"],
    ["Franklin Open [1]", '<link href="https://www.scimagojr.com/journalrank.php?category=2208&amp;country=EU-27&amp;openaccess=true&amp;ord=desc&amp;order=tr">SCImago ranking listing</link>'],
    ["ROBOMECH Journal [2]", '<link href="https://www.scimagojr.com/journalsearch.php?page=373&amp;q=rna&amp;total_size=21207">SCImago journal search listing</link>'],
    ["Alexandria Engineering Journal [3]", '<link href="https://www.scimagojr.com/journalrank.php?country=EU-27&amp;ord=asc&amp;order=sjr&amp;year=2006">SCImago historical listing</link>'],
    ["Expert Systems with Applications [4]", '<link href="https://www.scimagojr.com/journalrank.php?country=GB&amp;min=1&amp;min_type=cd&amp;ord=desc&amp;order=cd&amp;page=2&amp;total_size=6801">SCImago ranking listing</link>'],
    ["Computers and Graphics [5]", '<link href="https://www.scimagojr.com/journalrank.php?category=1709&amp;min=300&amp;min_type=cd&amp;ord=asc&amp;order=tr&amp;page=2&amp;total_size=45">SCImago listing (publisher uses Computers &amp; Graphics)</link>'],
    ["IEEE Transactions on Intelligent Transportation Systems [6]", '<link href="https://www.scimagojr.com/journalrank.php?country=Northern+America&amp;min=100&amp;min_type=cd&amp;ord=desc&amp;order=cd&amp;page=4&amp;total_size=4016">SCImago ranking listing</link>'],
    ["Discover Computing [7]", '<link href="https://www.scimagojr.com/journalsearch.php?q=Computing+in+Science+">SCImago journal search listing</link>; previously Information Retrieval Journal.'],
    ["Artificial Intelligence Review [8]", '<link href="https://www.scimagojr.com/journalrank.php?country=EU-27&amp;ord=desc&amp;order=cpd&amp;year=2023">SCImago historical listing</link>'],
    ["Array [9], [15]", '<link href="https://www.scimagojr.com/journalsearch.php?q=21101080486&amp;tip=sid">SCImago record, source ID 21101080486</link>. Direct fetch blocked; listing corroborated by <link href="https://journalsbase.com/journals/array">JournalsBase</link>.'],
    ["Frontiers in Neurorobotics [10]", '<link href="https://www.scimagojr.com/journalsearch.php?q=21100199837&amp;tip=sid">SCImago record, source ID 21100199837</link>. Direct fetch blocked; SJR corroborated by <link href="https://library.wur.nl/WebQuery/rugbrowser/22476">Wageningen University library</link>.'],
    ["Sensors [11], [12]", '<link href="https://www.scimagojr.com/journalrank.php?area=3100&amp;ord=desc&amp;order=tc">SCImago ranking listing</link>; MDPI, ISSN 1424-8220.'],
    ["Information [13]", '<link href="https://www.scimagojr.com/journalrank.php?country=CH&amp;ord=desc&amp;order=tr&amp;page=5&amp;total_size=877">SCImago listing as Information (Switzerland)</link>.'],
    ["Scientific Reports [14]", '<link href="https://www.scimagojr.com/journalrank.php?country=GB&amp;ord=desc&amp;order=cd">SCImago ranking listing</link>.'],
]
story.append(table(listing_rows, [73 * mm, 100 * mm]))
story.append(Spacer(1, 4 * mm))
story.append(P("Verification limitation: the direct SCImago pages for Array and Frontiers in Neurorobotics rejected automated access. Their journal identities and SJR records were corroborated through the linked catalogues. Open these two SCImago records manually if the college requires a screenshot as submission evidence."))
story.append(P("Appendix B. Five-Paper Reading Checklist", "H1"))
story.append(P("Each member should read their five assigned articles and be ready to explain: the problem; model and data; split protocol; main result and metric; author-stated limitations; their own critical research gap; and the specific experiment DriveAlert could run to address it. The papers are assigned by research responsibility, so not every paper uses that member's exact backbone."))
story.append(table([
    ["Member", "Five distinct paper identifiers"],
    ["CB.SC.U4CSE23628 / MobileNetV3-Small", "1, 2, 3, 10, 11"],
    ["CB.SC.U4CSE23603 / EfficientNet-B0", "4, 5, 6, 12, 13"],
    ["CB.SC.U4CSE23717 / ResNet-18", "7, 8, 9, 14, 15"],
], [105 * mm, 68 * mm]))
'''
base = base.replace('doc.build(story)', appendix + '\ndoc.build(story)')
exec(compile(base, str(Path(__file__).with_name('build_case_study_review.py')), 'exec'))
