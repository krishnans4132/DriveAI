from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


OUTPUT = "/Users/krishnansirosh/Documents/Codex/2026-08-30/referenced-chatgpt-conversation-this-is-an/outputs/DriveAlert_Case_Study_Review_2_Literature_Survey.pdf"

PAGE_WIDTH, PAGE_HEIGHT = A4
LEFT = 18 * mm
RIGHT = 18 * mm
TOP = 32 * mm
BOTTOM = 17 * mm
CONTENT_WIDTH = PAGE_WIDTH - LEFT - RIGHT

NAVY = colors.HexColor("#10233F")
TEAL = colors.HexColor("#087F8C")
CYAN = colors.HexColor("#10A7B5")
PALE = colors.HexColor("#EAF6F7")
LIGHT = colors.HexColor("#F4F7FA")
MID = colors.HexColor("#D8E1EA")
INK = colors.HexColor("#1D2B3A")
MUTED = colors.HexColor("#536579")
WHITE = colors.white


def draw_first_page(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, PAGE_HEIGHT - 25 * mm, PAGE_WIDTH, 25 * mm, fill=1, stroke=0)
    canvas.setFillColor(CYAN)
    canvas.rect(0, PAGE_HEIGHT - 27 * mm, PAGE_WIDTH, 2 * mm, fill=1, stroke=0)
    canvas.setFont("Helvetica-Bold", 9)
    canvas.setFillColor(WHITE)
    canvas.drawString(LEFT, PAGE_HEIGHT - 15 * mm, "CASE STUDY REVIEW 2")
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(PAGE_WIDTH - RIGHT, PAGE_HEIGHT - 15 * mm, "DRIVEALERT AI | 03 SEPTEMBER 2026")
    canvas.setStrokeColor(MID)
    canvas.line(LEFT, 13 * mm, PAGE_WIDTH - RIGHT, 13 * mm)
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawString(LEFT, 8.5 * mm, "Prepared for academic review - literature survey and research-gap analysis")
    canvas.drawRightString(PAGE_WIDTH - RIGHT, 8.5 * mm, f"Page {doc.page}")
    canvas.restoreState()


def draw_later_page(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(CYAN)
    canvas.setLineWidth(1.2)
    canvas.line(LEFT, PAGE_HEIGHT - 13 * mm, PAGE_WIDTH - RIGHT, PAGE_HEIGHT - 13 * mm)
    canvas.setFillColor(NAVY)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.drawString(LEFT, PAGE_HEIGHT - 9.5 * mm, "DRIVEALERT AI")
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawRightString(PAGE_WIDTH - RIGHT, PAGE_HEIGHT - 9.5 * mm, "Literature Survey and Research-Gap Analysis")
    canvas.setStrokeColor(MID)
    canvas.setLineWidth(0.6)
    canvas.line(LEFT, 13 * mm, PAGE_WIDTH - RIGHT, 13 * mm)
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawString(LEFT, 8.5 * mm, "Case Study Review 2")
    canvas.drawRightString(PAGE_WIDTH - RIGHT, 8.5 * mm, f"Page {doc.page}")
    canvas.restoreState()


doc = BaseDocTemplate(
    OUTPUT,
    pagesize=A4,
    leftMargin=LEFT,
    rightMargin=RIGHT,
    topMargin=TOP,
    bottomMargin=BOTTOM,
    title="Context-Aware Real-Time Driver Fatigue Detection",
    author="DriveAlert AI Team",
    subject="Case Study Review 2 literature survey and research-gap analysis",
)

frame = Frame(LEFT, BOTTOM, CONTENT_WIDTH, PAGE_HEIGHT - TOP - BOTTOM, id="main")
doc.addPageTemplates([
    PageTemplate(id="First", frames=[frame], onPage=draw_first_page),
    PageTemplate(id="Later", frames=[frame], onPage=draw_later_page),
])

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(
    name="PaperTitle",
    parent=styles["Title"],
    fontName="Helvetica-Bold",
    fontSize=22,
    leading=26,
    textColor=NAVY,
    alignment=TA_LEFT,
    spaceAfter=6 * mm,
))
styles.add(ParagraphStyle(
    name="Subtitle",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=10.5,
    leading=15,
    textColor=TEAL,
    spaceAfter=5 * mm,
))
styles.add(ParagraphStyle(
    name="Author",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=9.5,
    leading=13,
    textColor=INK,
    alignment=TA_CENTER,
))
styles.add(ParagraphStyle(
    name="AbstractHead",
    parent=styles["Heading2"],
    fontName="Helvetica-Bold",
    fontSize=10,
    leading=12,
    textColor=WHITE,
    spaceAfter=3 * mm,
))
styles.add(ParagraphStyle(
    name="AbstractBody",
    parent=styles["BodyText"],
    fontName="Times-Roman",
    fontSize=9.5,
    leading=13,
    textColor=INK,
    alignment=TA_JUSTIFY,
))
styles.add(ParagraphStyle(
    name="H1",
    parent=styles["Heading1"],
    fontName="Helvetica-Bold",
    fontSize=15,
    leading=18,
    textColor=NAVY,
    spaceBefore=5 * mm,
    spaceAfter=2.5 * mm,
    keepWithNext=True,
))
styles.add(ParagraphStyle(
    name="H2",
    parent=styles["Heading2"],
    fontName="Helvetica-Bold",
    fontSize=11.2,
    leading=14,
    textColor=TEAL,
    spaceBefore=3.5 * mm,
    spaceAfter=1.5 * mm,
    keepWithNext=True,
))
styles.add(ParagraphStyle(
    name="H3",
    parent=styles["Heading3"],
    fontName="Helvetica-Bold",
    fontSize=9.7,
    leading=12,
    textColor=INK,
    spaceBefore=2.5 * mm,
    spaceAfter=1 * mm,
    keepWithNext=True,
))
styles.add(ParagraphStyle(
    name="Body",
    parent=styles["BodyText"],
    fontName="Times-Roman",
    fontSize=9.4,
    leading=13.2,
    textColor=INK,
    alignment=TA_JUSTIFY,
    spaceAfter=2.3 * mm,
))
styles.add(ParagraphStyle(
    name="BulletText",
    parent=styles["BodyText"],
    fontName="Times-Roman",
    fontSize=9.2,
    leading=12.5,
    leftIndent=5 * mm,
    firstLineIndent=-3.5 * mm,
    textColor=INK,
    spaceAfter=1.2 * mm,
))
styles.add(ParagraphStyle(
    name="Callout",
    parent=styles["BodyText"],
    fontName="Helvetica",
    fontSize=8.8,
    leading=12.2,
    textColor=INK,
    spaceAfter=1.5 * mm,
))
styles.add(ParagraphStyle(
    name="TableHead",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=7.4,
    leading=9,
    textColor=WHITE,
    alignment=TA_LEFT,
))
styles.add(ParagraphStyle(
    name="TableCell",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=7.2,
    leading=9.2,
    textColor=INK,
))
styles.add(ParagraphStyle(
    name="Reference",
    parent=styles["BodyText"],
    fontName="Times-Roman",
    fontSize=8.2,
    leading=11.2,
    leftIndent=7 * mm,
    firstLineIndent=-7 * mm,
    textColor=INK,
    spaceAfter=1.7 * mm,
))
styles.add(ParagraphStyle(
    name="SmallNote",
    parent=styles["Normal"],
    fontName="Helvetica-Oblique",
    fontSize=7.6,
    leading=10,
    textColor=MUTED,
    spaceAfter=2 * mm,
))


def P(text, style="Body"):
    return Paragraph(text, styles[style])


def bullet(text):
    return P(f"- {text}", "BulletText")


def table(data, widths, header=True, font_size=None):
    converted = []
    for row_index, row in enumerate(data):
        style_name = "TableHead" if header and row_index == 0 else "TableCell"
        converted.append([
            item if hasattr(item, "wrap") else P(str(item), style_name)
            for item in row
        ])
    result = Table(converted, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    commands = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY if header else LIGHT),
        ("GRID", (0, 0), (-1, -1), 0.45, MID),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    if header:
        commands.extend([
            ("BACKGROUND", (0, 1), (-1, -1), WHITE),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT]),
        ])
    if font_size:
        commands.append(("FONTSIZE", (0, 0), (-1, -1), font_size))
    result.setStyle(TableStyle(commands))
    return result


def callout(title, body):
    content = [[P(title.upper(), "AbstractHead")], [P(body, "Callout")]]
    box = Table(content, colWidths=[CONTENT_WIDTH])
    box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), TEAL),
        ("BACKGROUND", (0, 1), (-1, -1), PALE),
        ("BOX", (0, 0), (-1, -1), 0.8, TEAL),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return box


story = []
story.append(Spacer(1, 18 * mm))
story.append(P("Context-Aware Real-Time Driver Fatigue Detection", "PaperTitle"))
story.append(P("A Literature Survey and Research-Gap Analysis for Lightweight Edge Deployment and Proactive Intervention", "Subtitle"))

authors = [
    [P("Krishnan S", "Author"), P("AdwaithRaveendran", "Author"), P("Eric277-wq", "Author")],
    [P("CB.SC.U4CSE23628", "TableCell"), P("CB.SC.U4CSE23603", "TableCell"), P("CB.SC.U4CSE23717", "TableCell")],
    [P("MobileNetV3-Small", "TableCell"), P("EfficientNet-B0", "TableCell"), P("ResNet-18", "TableCell")],
]
author_table = Table(authors, colWidths=[CONTENT_WIDTH / 3] * 3)
author_table.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
    ("BOX", (0, 0), (-1, -1), 0.7, MID),
    ("INNERGRID", (0, 0), (-1, -1), 0.4, MID),
    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("TOPPADDING", (0, 0), (-1, -1), 6),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
]))
story.append(author_table)
story.append(Spacer(1, 6 * mm))

abstract_text = (
    "Driver drowsiness detection research increasingly reports high classification accuracy, yet practical deployment remains constrained by inconsistent validation protocols, weak cross-driver generalization, environmental sensitivity, compute cost, and limited evaluation of the intervention that follows detection. This review examines nine journal articles published from 2025 to 2026 and assigns three papers to each DriveAlert AI team member. The selected 2026 standard paper compares MobileNetV3-Small and EfficientNet variants for lightweight fatigue recognition and directly supports the project's architecture study. The reviewed literature spans compact CNNs, event-driven hardware, graph and spatial-temporal learning, calibration-free domain adaptation, multimodal monitoring, explainability, and proactive alerts. Comparative synthesis shows that no single reviewed implementation jointly provides participant-disjoint eye and mouth benchmarking, validation-locked operating thresholds, temporal evidence accumulation, speed- and continuous-drive-aware sensitivity, transparent alert progression, and a rest-oriented intervention workflow. The resulting research gap motivates DriveAlert AI: a webcam-based prototype that compares MobileNetV3-Small, EfficientNet-B0, and ResNet-18 under one protocol, deploys the smallest suitable model, and couples its probabilities to a deterministic temporal safety engine. The review also defines the remaining work required before real-world use, including human-verified labels, naturalistic driving trials, low-light and occlusion testing, hardware latency measurement, probability calibration, false-alarm-per-hour evaluation, and human-factors validation of spoken warnings and rerouting prompts."
)
story.append(callout("Abstract", abstract_text))
story.append(Spacer(1, 3.5 * mm))
story.append(P("<b>Keywords:</b> driver drowsiness detection; driver fatigue; MobileNetV3-Small; EfficientNet-B0; ResNet-18; PERCLOS; edge AI; adaptive thresholds; cognitive co-pilot; literature survey", "AbstractBody"))
story.append(Spacer(1, 4 * mm))

anchor_text = (
    "<b>Selected paper:</b> M. Vimala, M. Nandhini, S. Jasmine, P. Ranjith Kumar, and S. Ramasamy, “Implementation of a lightweight deep learning model for detecting driver fatigue,” <i>Franklin Open</i>, vol. 15, art. 100547, 2026, doi: 10.1016/j.fraope.2026.100547 [1]. "
    "It was selected because it is a 2026 journal article, Franklin Open is listed by SCImago, and its direct comparison of MobileNetV3-Small with EfficientNet variants closely matches the DriveAlert AI model-selection problem."
)
story.append(callout("Recommended 2026 Standard Journal Paper", anchor_text))
story.append(PageBreak())

story.append(P("1. Introduction", "H1"))
story.append(P(
    "Driver fatigue is a progressive safety risk rather than a single-frame visual class. Observable cues such as prolonged eyelid closure, increasing blink duration, repeated yawning, head nodding, and degraded vehicle control can appear at different times and with different reliability. Camera-based systems are attractive because they are non-intrusive and can reuse ordinary in-cabin hardware, but their performance changes with lighting, eyewear, head pose, facial differences, camera quality, and the evaluation protocol used by the researcher [7], [8].",
))
story.append(P(
    "Recent work ranges from compact CNN classifiers to spatial-temporal attention, graph convolution, physiological sensing, multimodal fusion, and explainable decision support. Headline accuracy alone does not establish readiness for a safety-critical application. A deployable system also needs participant-independent evaluation, a threshold fixed before test evaluation, event-level temporal reasoning, measured latency, calibrated false-alarm behavior, sensor-failure handling, and an intervention that is understandable and acceptable to the driver [6]-[9].",
))
story.append(P("1.1 Problem Statement", "H2"))
story.append(P(
    "The literature does not yet provide one reproducible, low-cost pipeline that compares lightweight and heavier visual architectures under the same participant-disjoint protocol and then connects the chosen model to context-aware temporal risk escalation and a proactive rest intervention. The central case-study problem is therefore to determine how a webcam-based fatigue monitor can retain credible detection performance while remaining small, transparent, context-sensitive, and demonstrable on ordinary hardware.",
))
story.append(P("1.2 Review Objectives", "H2"))
for item in [
    "Identify a valid 2026 standard journal paper that directly supports the project topic.",
    "Allocate three relevant papers to each team member according to model and system responsibility.",
    "Compare modalities, temporal reasoning, validation design, deployment evidence, and intervention capability.",
    "Extract defensible research gaps without treating results obtained on different datasets as directly comparable.",
    "Translate the gaps into measurable objectives for the DriveAlert AI case study.",
]:
    story.append(bullet(item))

story.append(P("1.3 Research Questions", "H2"))
for item in [
    "RQ1: Which architecture offers the most defensible accuracy-efficiency trade-off for ordinary-laptop webcam inference?",
    "RQ2: How should frame-level eye and mouth predictions be converted into temporal fatigue evidence without reacting to a normal blink or isolated facial movement?",
    "RQ3: Can vehicle speed and continuous-drive duration adjust alert sensitivity while leaving model probability thresholds locked?",
    "RQ4: Which evaluation and human-factors evidence is still required before the prototype can support real-road claims?",
]:
    story.append(bullet(item))

story.append(P("2. Review Methodology", "H1"))
story.append(P(
    "A targeted narrative review was conducted for Case Study Review 2. Publisher pages and bibliographic records were checked through IEEE Xplore, ScienceDirect, Springer Nature, and SCImago Journal Rank. Searches combined the terms driver drowsiness, driver fatigue, real time, lightweight CNN, MobileNet, EfficientNet, spatial-temporal, multimodal, adaptive threshold, EEG, edge computing, and driver monitoring. The source review was completed on 3 September 2026.",
))
story.append(P("2.1 Inclusion and Exclusion Criteria", "H2"))
for item in [
    "Included: journal articles from 2025-2026 with direct relevance to driver drowsiness, fatigue monitoring, deployment, generalization, or intervention.",
    "Included: one 2026 implementation paper from a journal listed by SCImago as the primary standard paper.",
    "Preferred: original research with quantitative evaluation; two recent survey papers were retained to establish field-wide gaps and reporting recommendations.",
    "Excluded: papers with no driver-state relevance, unverified publication metadata, or conference-only status for the primary-paper requirement.",
    "Interpretation rule: performance values from different datasets and split protocols were not ranked as if they were measured under one common test set.",
]:
    story.append(bullet(item))

story.append(P("2.2 Selected Paper and Team Allocation", "H2"))
allocation_data = [
    ["Member", "Model responsibility", "Assigned references", "Literature theme"],
    ["CB.SC.U4CSE23628", "MobileNetV3-Small", "[1]-[3]", "Lightweight CNNs, webcam deployment, low-power edge sensing"],
    ["CB.SC.U4CSE23603", "EfficientNet-B0", "[4]-[6]", "Multi-region representation, temporal attention, cross-subject generalization"],
    ["CB.SC.U4CSE23717", "ResNet-18", "[7]-[9]", "Multimodal benchmarking, explainability, intervention and system integration"],
]
story.append(table(allocation_data, [35 * mm, 36 * mm, 28 * mm, 74 * mm]))
story.append(Spacer(1, 2 * mm))
story.append(P(
    "Paper [1] is the recommended submission paper. It was published in 2026 and evaluates MobileNetV3-Small alongside EfficientNet-B0, EfficientNet-B3, EfficientNet-B7, and MobileNetV2. Its subject, model families, edge-deployment objective, and stated need for real in-vehicle validation align closely with DriveAlert AI.",
))

story.append(P("3. Member-Wise Literature Survey", "H1"))
story.append(P("3.1 CB.SC.U4CSE23628 - MobileNetV3-Small and Edge Deployment", "H2"))

story.append(P("Paper 1: Lightweight CNN comparison for driver fatigue (2026)", "H3"))
story.append(P(
    "Vimala et al. [1] compare five transfer-learning architectures on 7,250 Yawn Eye images representing closed eyes, open eyes, yawning, and no-yawn states. MobileNetV3-Small achieved the best reported overall accuracy of 94.69%, with 94.67% precision, 94.66% recall, a 9.9 MB model size, 0.15 GFLOPs, and approximately 8 ms inference latency in the authors' environment. EfficientNet-B0 reached 93.76% accuracy but required more computation. The study is strong evidence that a mobile architecture can be selected through an explicit accuracy-resource trade-off rather than accuracy alone.",
))
story.append(P(
    "<b>Gap:</b> evaluation is based on one image dataset and frame-level classification. The authors identify the need for actual in-car validation and testing on multiple benchmarks. Continuous driving duration, speed-dependent risk, participant-independent temporal events, false alarms per hour, and the post-detection intervention are outside its evaluation. DriveAlert AI adopts the architecture comparison idea but adds separate eye and mouth heads, participant-disjoint splits, temporal evidence, and context-aware escalation.",
))

story.append(P("Paper 2: MobileNet drowsiness detection shield (2025)", "H3"))
story.append(P(
    "Bhanja et al. [2] fine-tune MobileNet for open-versus-closed eye classification using the MRL Eye Dataset and connect it to an OpenCV webcam application. The reported test metrics are 90% accuracy, 100% precision, 83.3% recall, and 90.9% F1. The paper demonstrates a complete path from preprocessing to a live camera alert and confirms the practical appeal of transfer learning for a low-cost system.",
))
story.append(P(
    "<b>Gap:</b> the reported confusion matrix contains only ten test decisions, validation accuracy is 100% while validation loss remains high, and the system uses eye state alone. The paper does not evaluate participant-disjoint generalization, yawning, temporal PERCLOS, calibrated operating thresholds, night conditions, alert fatigue, or vehicle context. These limitations show why a larger held-out protocol and more than one fatigue signal are required.",
))

story.append(P("Paper 3: Event-driven low-power blink tracking (2025)", "H3"))
story.append(P(
    "Choi et al. [3] replace conventional RGB frame processing with a Dynamic Vision Sensor and a hardware-software co-designed blink tracker. Their FPGA prototype reports 200 FPS, a 1,275x blink-detection speedup, a 310-496x eye-region speedup, and an average F1 score near 86% under lighting and noise variation. This paper makes latency, power, and sensor behavior first-class design concerns and demonstrates that efficient drowsiness sensing is a system-level problem, not only a classifier problem.",
))
story.append(P(
    "<b>Gap:</b> specialized event-camera and accelerator hardware reduces accessibility for a webcam-based college prototype. The method focuses on blink events rather than yawning, PERCLOS fusion, continuous-drive risk, or intervention design; rapid movement may invoke server-assisted eye localization. The study motivates future edge benchmarking of DriveAlert while also supporting the present decision to use widely available RGB cameras and compact CNNs.",
))

story.append(P("3.2 CB.SC.U4CSE23603 - EfficientNet-B0 and Robust Representation", "H2"))

story.append(P("Paper 4: Prior-knowledge multi-information graph CNN (2025)", "H3"))
story.append(P(
    "Wei et al. [4] argue that eye- or mouth-only methods lose structured relations and are sensitive to driver differences. Their MIGCN framework extracts multiple prior-informed facial sources, injects class, attention, temporal, and mean-feature information, and models their spatial relationships with a task-driven graph convolutional network. Reported accuracy reaches 94.78% on DROZY and 97.52% on UTA-RLDD, exceeding the compared state of the art by 1.68 and 2.84 percentage points respectively.",
))
story.append(P(
    "<b>Gap:</b> richer feature graphs add architectural and preprocessing complexity, while on-device latency, memory, energy, calibration, and operational false-alarm rates are not the primary evaluation. The results also remain tied to benchmark datasets. The paper motivates multi-signal reasoning but leaves space for a simpler deployed model whose outputs are combined by an explicit and testable temporal policy.",
))

story.append(P("Paper 5: Stacked landmark heatmaps and spatial-temporal attention (2025)", "H3"))
story.append(P(
    "Qin et al. [5] replace a fixed external landmark-regression stage with trainable stacked landmark heatmap segmentation. A diagonal embedding encodes geometric relationships, and a two-stream module combines 2D and 3D convolutions with multi-head self-attention. Evaluation uses YawDD, NTHU-DDD, and VBDDD, addressing the weakness of methods that classify isolated frames without learning behavior over time. The design is especially relevant to the distinction between a normal blink and a sustained fatigue event.",
))
story.append(P(
    "<b>Gap:</b> the complete pipeline still includes RetinaFace preprocessing plus heatmap, 2D/3D convolution, and attention stages. The journal article does not establish the same ordinary-laptop resource profile as a small MobileNet head, and cross-paper results cannot be directly compared because labels and video segmentation differ. DriveAlert separates compact spatial classification from deterministic temporal accumulation, making thresholds and alert reasons easier to inspect.",
))

story.append(P("Paper 6: Calibration-free cross-subject drowsiness classification (2025)", "H3"))
story.append(P(
    "Kim et al. [6] address a fundamental deployment problem: EEG patterns vary across and within individuals, normally requiring user calibration. Their prototype-based multi-domain mixup augments features from unseen subjects using source-domain prototypes, improving calibration-free generalization. The paper is important methodologically because it treats subject identity as a domain and evaluates whether the model transfers to drivers not seen during training.",
))
story.append(P(
    "<b>Gap:</b> EEG provides direct cognitive evidence but requires electrodes, acquisition hardware, artifact control, and user acceptance. The method therefore does not solve non-intrusive webcam deployment. Its main lesson for DriveAlert is experimental: participant identity must not leak across training and test sets, and cross-driver results should be reported separately from easier subject-mixed evaluation.",
))

story.append(P("3.3 CB.SC.U4CSE23717 - ResNet-18, Multimodality, and Intervention", "H2"))

story.append(P("Paper 7: ViT, CNN, sensor fusion, and RAG interpretability (2026)", "H3"))
story.append(P(
    "Sah et al. [7] integrate ViT-B/16 and CNN baselines with facial landmarks, head pose, emotion analysis, driving-style sensors, LSTM temporal modeling, Grad-CAM, and a retrieval-augmented explanation layer. The study reports 99% within-study drowsiness accuracy and 90.64% after cross-dataset fine-tuning on NTHU-DDD2 and UTA-RLDD. It also emphasizes recall and F1 rather than relying only on accuracy and shows how multiple signals can support human-readable safety recommendations.",
))
story.append(P(
    "<b>Gap:</b> the authors explicitly identify missing formal edge-latency benchmarking, incomplete visible-light versus infrared evaluation, implicit rather than dedicated occlusion handling, limited RAG context recall, and the need for large naturalistic driving validation. The breadth of the pipeline can also raise integration and compute costs. DriveAlert uses a smaller, deterministic decision layer for a transparent college demonstration while retaining future paths toward multimodal and explainable monitoring.",
))

story.append(P("Paper 8: Systematic review of intelligent driver monitoring (2026)", "H3"))
story.append(P(
    "Hassan et al. [8] synthesize vision, physiological, vehicle-behavior, and multimodal driver-monitoring methods using a PRISMA-guided review of 2020-2025 literature. Their central result is that reported performance is strongly dependent on validation design: subject-dependent and within-dataset tests commonly produce optimistic values, while subject-independent and cross-dataset results are rarer and lower. They recommend prevalence-aware PR-AUC, recall at a fixed false-alarm rate, calibration, and time-to-detect, alongside privacy and deployment reporting.",
))
story.append(P(
    "<b>Gap:</b> the field lacks large on-road studies, consistent ground truth, cross-demographic validation, robust occlusion testing, and evidence that alert interfaces reduce risk without excessive annoyance or cognitive load. The review specifically calls for human-machine-interface trials, false alarms per hour, response latency, usability, and near-miss outcomes. These recommendations define the most important validation plan beyond DriveAlert's current prototype.",
))

story.append(P("Paper 9: Neuro-cognitive AI alerts and smart-city integration (2026)", "H3"))
story.append(P(
    "Mahapatra et al. [9] combine CNN spatial features, GRU temporal modeling, EAR-based analysis, adaptive threshold calibration, multimodal sensor fusion, and visual-auditory alerts. The system reports a 93% F1 score and frames drowsiness monitoring as an active safety service that may communicate with traffic-management and emergency platforms. This is closely related to DriveAlert's cognitive co-pilot concept because detection is connected to a user-facing intervention.",
))
story.append(P(
    "<b>Gap:</b> the study's data are confidential, limiting independent reproduction; the accident-detection component remains proposed rather than implemented. It does not provide an openly reproducible comparison of compact architectures, nor does it validate whether alert timing, wording, repetition, or routing improves driver response. DriveAlert can demonstrate the interaction flow, but a controlled human-factors study is still required before effectiveness claims are made.",
))

story.append(P("4. Comparative Synthesis of the Literature", "H1"))
comparison = [
    ["Ref.", "Year", "Primary modality", "Temporal reasoning", "Deployment evidence", "Main unresolved issue"],
    ["[1]", "2026", "RGB eye/mouth images", "No; frame classes", "Latency and model size", "Single dataset; no real in-car test"],
    ["[2]", "2025", "RGB eye crops", "Closed-eye alert logic", "Live webcam demo", "Very small test; eye only"],
    ["[3]", "2025", "Event camera", "Blink events", "FPGA, power, 200 FPS", "Special hardware; blink only"],
    ["[4]", "2025", "Multi-region face graph", "Temporal information in features", "Benchmark evaluation", "Complexity and edge cost"],
    ["[5]", "2025", "Landmark heatmap video", "2D/3D attention", "Efficiency-oriented design", "Full edge latency not established"],
    ["[6]", "2025", "EEG", "Domain/prototype modeling", "Unseen-subject evaluation", "Intrusive acquisition"],
    ["[7]", "2026", "Vision + sensors + RAG", "LSTM and sustained cues", "Integrated prototype", "Latency, IR, occlusion, naturalistic tests"],
    ["[8]", "2026", "Multi-modality survey", "Evaluation recommendation", "Deployment framework", "Benchmark and field-trial scarcity"],
    ["[9]", "2026", "Vision + sensors", "CNN-GRU", "Alerts and smart-city concept", "Private data; intervention not validated"],
]
story.append(table(comparison, [12 * mm, 14 * mm, 34 * mm, 31 * mm, 36 * mm, 46 * mm]))
story.append(Spacer(1, 2.5 * mm))
story.append(P(
    "The evidence shows three recurring trade-offs. First, lightweight RGB systems are accessible but vulnerable to environment and subject variation. Second, temporal, graph, transformer, and multimodal methods improve representation but increase compute and integration burden. Third, many papers stop at classification or alarm generation; few quantify how context should change urgency or whether the intervention improves behavior. Because datasets, labels, and splits differ, the reported accuracies must be interpreted within each paper rather than used as a universal ranking.",
))

story.append(P("5. Consolidated Research Gaps", "H1"))
gaps = [
    ["Gap", "Evidence from literature", "Requirement for DriveAlert AI"],
    ["G1. Cross-driver and cross-dataset validity", "Subject-mixed evaluation can inflate results; realistic transfer is less common [6], [8].", "Keep participant-disjoint splits; later add cross-dataset and demographic reporting."],
    ["G2. Comparable architecture selection", "Different papers use different data and metrics, preventing fair model ranking [1], [8].", "Train MobileNetV3-Small, EfficientNet-B0, and ResNet-18 under one locked protocol."],
    ["G3. Temporal fatigue instead of frame labels", "Single frames confuse normal blinks with fatigue; temporal models add cost [1], [5].", "Accumulate sustained closure, PERCLOS, and distinct yawn events in a testable policy."],
    ["G4. Context-blind warning thresholds", "Most systems do not connect vehicle risk or time-on-task to alert sensitivity [8], [9].", "Scale temporal thresholds with simulated speed and continuous-drive duration while locking model thresholds."],
    ["G5. Resource-aware deployment", "High-performing models often omit latency, power, and memory evidence [3], [7].", "Deploy the smallest acceptable model; benchmark end-to-end latency on target hardware."],
    ["G6. Environmental and sensor robustness", "Low light, eyewear, pose, and missing signals remain persistent failure modes [3], [7], [8].", "Expose sensor-unavailable state now; later test day/night, eyewear, masks, motion blur, and IR."],
    ["G7. Intervention effectiveness", "Alerts are commonly implemented but wording, timing, annoyance, and response are rarely validated [8], [9].", "Use a transparent alert queue and TTS/rest prompt; conduct simulator-based human-factor trials."],
    ["G8. Reproducibility and label quality", "Private or weakly described data and inconsistent ground truth limit replication [8], [9].", "Publish code, model cards, thresholds, and split evidence; replace provisional weak labels with human verification."],
]
story.append(table(gaps, [39 * mm, 67 * mm, 67 * mm]))

story.append(P("5.1 Principal Research-Gap Statement", "H2"))
story.append(callout(
    "Research Gap",
    "Existing studies separately demonstrate accurate visual classification, temporal modeling, efficient hardware, adaptive calibration, multimodal fusion, or driver alerts. The reviewed literature does not jointly demonstrate, under one reproducible participant-disjoint protocol, a three-architecture eye-and-mouth comparison, deployment-aware model selection, interpretable temporal fatigue accumulation, speed- and continuous-drive-aware sensitivity, an observable alert queue, and a proactive rest-oriented intervention. DriveAlert AI investigates this integration while explicitly treating real-road effectiveness as future validation rather than a completed claim."
))

story.append(P("6. Proposed Case Study: DriveAlert AI", "H1"))
story.append(P("6.1 Proposed Objectives", "H2"))
for item in [
    "Compare MobileNetV3-Small, EfficientNet-B0, and ResNet-18 on the same participant-disjoint eye-state and mouth-event splits.",
    "Lock operating thresholds using validation data before evaluating the held-out test set.",
    "Select a deployment architecture using balanced accuracy, safety recall, model size, and expected latency rather than accuracy alone.",
    "Convert model probabilities into continuous eye-closure duration, 60-second PERCLOS, and five-minute yawn-event evidence.",
    "Increase temporal sensitivity with vehicle speed and continuous driving time while preserving fixed neural-network probability thresholds.",
    "Present alert progression, spoken warnings, and a simulated safe-rest route in a clear real-time interface.",
]:
    story.append(bullet(item))

story.append(P("6.2 Current Prototype Evidence", "H2"))
project_results = [
    ["Architecture", "Parameters", "Eye balanced accuracy", "Mouth balanced accuracy", "Project decision"],
    ["MobileNetV3-Small", "1.52 M", "96.93%", "94.41%", "Selected for live deployment"],
    ["EfficientNet-B0", "4.01 M", "96.53%", "94.07%", "Efficiency comparison"],
    ["ResNet-18", "11.18 M", "97.88%", "95.57%", "Accuracy reference"],
]
story.append(table(project_results, [42 * mm, 27 * mm, 35 * mm, 37 * mm, 32 * mm]))
story.append(P(
    "These are internal project results obtained with provisional weak labels and should be reported as prototype evidence, not independently verified real-world performance. MobileNetV3-Small is selected because it stays close to the heavier accuracy leader while using substantially fewer parameters and smaller exported models. The live system uses separate MobileNet eye and mouth heads, webcam crops, a deterministic fatigue engine, simulated speed and drive duration, browser text-to-speech, and a hardcoded offline rest-stop route.",
    "SmallNote",
))

story.append(P("6.3 Validation Plan", "H2"))
validation = [
    ["Phase", "Evaluation", "Primary measures"],
    ["A", "Human verification of sampled weak labels", "Agreement, class balance, label-error rate"],
    ["B", "Locked participant-disjoint re-evaluation", "PR-AUC, balanced accuracy, recall, specificity, calibration"],
    ["C", "Cross-dataset and subgroup stress tests", "Performance by dataset, lighting, eyewear, head pose, demographic group"],
    ["D", "Target-hardware runtime test", "End-to-end latency, FPS, memory, CPU/GPU utilization, energy where available"],
    ["E", "Long-duration simulator study", "False alarms/hour, missed events, time-to-detect, sensor downtime"],
    ["F", "Human-factors intervention study", "Response latency, compliance, annoyance, workload, trust"],
]
story.append(table(validation, [17 * mm, 62 * mm, 94 * mm]))

story.append(P("7. Discussion", "H1"))
story.append(P(
    "The literature supports the project's use of MobileNetV3-Small as a rational deployment candidate, but it also warns against equating a compact model's image accuracy with a validated driver-safety system. Paper [1] supports lightweight architecture comparison; papers [2] and [3] expose the practical importance of webcam integration and hardware efficiency; papers [4]-[6] show why structured multi-region, temporal, and cross-subject reasoning matter; and papers [7]-[9] shift attention toward multimodal context, explainability, deployment reporting, and intervention.",
))
story.append(P(
    "DriveAlert's main contribution is therefore system integration and transparency. Model thresholds are validation-locked, while vehicle speed and continuous-drive time scale only the temporal decision thresholds. This separation makes the context mechanism easier to audit than silently changing the neural classifier threshold. The alert queue further exposes how close sustained closure, PERCLOS, and yawn counts are to escalation. The cognitive co-pilot demonstrates a useful intervention path, but its spoken warning and reroute remain interface features until human response and real-road outcomes are studied.",
))
story.append(P(
    "Several threats to validity remain. Weak labels can bias every architecture similarly and make a fair training protocol appear more reliable than the labels themselves. Participant-disjoint testing reduces identity leakage but does not establish cross-dataset or cross-demographic robustness. Simulated telemetry does not reproduce CAN-bus noise, GPS uncertainty, or real traffic risk. Finally, the hardcoded route is intentionally a demonstration and must not be described as operational navigation. These limitations should be stated clearly during the review.",
))

story.append(P("8. Conclusion", "H1"))
story.append(P(
    "This literature survey identifies a strong 2026 standard journal paper and distributes nine recent journal studies across the three DriveAlert AI team members. The evidence supports a lightweight vision-first prototype but reveals that real deployment depends on more than classifier accuracy. Generalization, temporal event logic, calibration, latency, environmental robustness, false alarms, privacy, and driver response all require explicit evaluation. DriveAlert AI addresses a useful integration gap by comparing three CNN families, deploying MobileNetV3-Small, applying speed- and continuous-drive-aware temporal sensitivity, visualizing alert progression, and demonstrating spoken rest intervention. Its appropriate academic claim is a transparent, working college prototype with a defined validation roadmap - not a certified automotive safety system.",
))

story.append(P("Funding", "H2"))
story.append(P("No external funding has been declared for this case-study review."))
story.append(P("Conflict of Interest", "H2"))
story.append(P("The team declares no known conflict of interest relevant to this review."))
story.append(P("Data and Ethics Statement", "H2"))
story.append(P(
    "No new human-subject data were collected for this literature review. The DriveAlert AI prototype uses locally obtained UTA-RLDD and YawDD data for educational research. Original videos and extracted images are not redistributed. Dataset access, privacy requirements, and use remain subject to the providers' terms [11], [12].",
))
story.append(P("Planned Author Contributions", "H2"))
contrib = [
    ["Member", "Assigned contribution to Case Study Review 2"],
    ["Krishnan S (CB.SC.U4CSE23628)", "MobileNetV3-Small implementation; lightweight and edge-deployment literature [1]-[3]; integration synthesis."],
    ["AdwaithRaveendran (CB.SC.U4CSE23603)", "EfficientNet-B0 comparison; robust representation and generalization literature [4]-[6]; gap extraction."],
    ["Eric277-wq (CB.SC.U4CSE23717)", "ResNet-18 comparison; multimodal, interpretability, and intervention literature [7]-[9]; discussion synthesis."],
    ["All members", "Reference verification, critical revision, presentation preparation, and approval of the submitted version."],
]
story.append(table(contrib, [57 * mm, 116 * mm]))

story.append(P("References", "H1"))
references = [
    '[1] M. Vimala, M. Nandhini, S. Jasmine, P. Ranjith Kumar, and S. Ramasamy, “Implementation of a lightweight deep learning model for detecting driver fatigue,” <i>Franklin Open</i>, vol. 15, art. 100547, 2026. <link href="https://doi.org/10.1016/j.fraope.2026.100547">doi:10.1016/j.fraope.2026.100547</link>.',
    '[2] A. Bhanja, D. Parhi, D. Gajendra, K. Sinha, and A. K. Sahoo, “Driver drowsiness shield (DDSH): a real-time driver drowsiness detection system,” <i>ROBOMECH Journal</i>, vol. 12, art. 18, 2025. <link href="https://doi.org/10.1186/s40648-025-00307-4">doi:10.1186/s40648-025-00307-4</link>.',
    '[3] J. Choi, E. Choi, S. Choi, and W. Lee, “E-BTS: A low-power event-driven blink tracking system with hardware-software co-optimized design for real-time driver drowsiness detection,” <i>Alexandria Engineering Journal</i>, vol. 128, pp. 867-877, 2025. <link href="https://doi.org/10.1016/j.aej.2025.07.020">doi:10.1016/j.aej.2025.07.020</link>.',
    '[4] F. Wei, J. Yang, Y. Wang, L. Lin, and H. Zhang, “Prior knowledge-guided multi-information graph convolutional network for driver drowsiness detection,” <i>Expert Systems with Applications</i>, vol. 275, art. 127028, 2025. <link href="https://doi.org/10.1016/j.eswa.2025.127028">doi:10.1016/j.eswa.2025.127028</link>.',
    '[5] W. Qin, L. Liu, and L. Sun, “Video-based driver drowsiness detection using stacked landmark heatmaps and spatial-temporal attention,” <i>Computers &amp; Graphics</i>, vol. 131, art. 104336, 2025. <link href="https://doi.org/10.1016/j.cag.2025.104336">doi:10.1016/j.cag.2025.104336</link>.',
    '[6] D.-Y. Kim, D.-K. Han, J.-H. Jeong, and S.-W. Lee, “Calibration-free driver drowsiness classification with prototype-based multi-domain mixup,” <i>IEEE Transactions on Intelligent Transportation Systems</i>, vol. 26, no. 3, pp. 2955-2966, 2025. <link href="https://doi.org/10.1109/TITS.2024.3522308">doi:10.1109/TITS.2024.3522308</link>.',
    '[7] A. Sah, M. Das, A. K. Sony, B. Acharya, A. D. Deferisha, and A. Swetapadma, “An approach for identification of driver drowsiness, emotion state, and behavior patterns based on vision transformers, CNN and multi-modal sensor fusion using RAG-based interpretability,” <i>Discover Computing</i>, vol. 29, art. 341, 2026. <link href="https://doi.org/10.1007/s10791-026-10217-7">doi:10.1007/s10791-026-10217-7</link>.',
    '[8] O. F. Hassan, A. F. Ibrahim, M. A. Makhlouf, B. Hafiz, and A. Gomaa, “Intelligent driver monitoring systems: a survey of drowsiness detection technologies for road safety,” <i>Artificial Intelligence Review</i>, vol. 59, art. 137, 2026. <link href="https://doi.org/10.1007/s10462-026-11505-w">doi:10.1007/s10462-026-11505-w</link>.',
    '[9] C. Mahapatra, S. K. Tripathy, and M. Tripathy, “Neuro-cognitive AI-driven system for preventing road accidents through driver drowsiness alerts,” <i>Array</i>, vol. 29, art. 100631, 2026. <link href="https://doi.org/10.1016/j.array.2025.100631">doi:10.1016/j.array.2025.100631</link>.',
    '[10] F. Ecarnot, M.-F. Seronde, R. Chopard, F. Schiele, and N. Meneveau, “Writing a scientific article: A step-by-step guide for beginners,” <i>European Geriatric Medicine</i>, vol. 6, pp. 573-579, 2015. <link href="https://doi.org/10.1016/j.eurger.2015.08.005">doi:10.1016/j.eurger.2015.08.005</link>.',
    '[11] R. Ghoddoosian, M. Galib, and V. Athitsos, “A realistic dataset and baseline temporal model for early drowsiness detection,” in <i>2019 IEEE/CVF Conference on Computer Vision and Pattern Recognition Workshops</i>, 2019. <link href="https://arxiv.org/abs/1904.07312">arXiv:1904.07312</link>.',
    '[12] S. Abtahi, M. Omidyeganeh, S. Shirmohammadi, and B. Hariri, “YawDD: A yawning detection dataset,” in <i>Proceedings of the 5th ACM Multimedia Systems Conference</i>, pp. 24-28, 2014. <link href="https://doi.org/10.1145/2557642.2563678">doi:10.1145/2557642.2563678</link>.',
    '[13] SCImago Journal &amp; Country Rank, “Franklin Open,” journal listing and 2024 ranking data. Accessed 3 September 2026. <link href="https://www.scimagojr.com/">https://www.scimagojr.com/</link>.',
]
for ref in references:
    story.append(P(ref, "Reference"))

story.append(Spacer(1, 4 * mm))
story.append(callout(
    "Submission Note",
    "The 2026 primary paper is reference [1]. Before final college submission, replace any GitHub-style author identifier with the member's official academic name if required by the institution, and confirm the submission portal's formatting and file-size rules."
))

doc.build(story)
print(OUTPUT)
