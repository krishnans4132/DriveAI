# DriveAlert AI case study report

## Open in Overleaf

1. Choose **New Project → Upload Project** and upload `DriveAlert_Overleaf.zip`.
2. Set **Main document** to `main.tex`.
3. Select **pdfLaTeX** and click **Recompile**. Overleaf runs BibTeX automatically.

The archive contains the main manuscript, the bibliography, the official Springer Nature class and bibliography style, and two existing application screenshots. The architecture diagram, tables and training plots are editable directly in `main.tex`. No local absolute paths or external image downloads are needed to compile.

The accompanying PDF was compiled locally using Tectonic (a XeTeX-based compiler). The source uses standard pdfLaTeX-compatible packages and is configured for pdfLaTeX in Overleaf. Small pagination differences between engines are possible.

## Contents

- Title, authors and affiliation, abstract and keywords
- Introduction and related work covering the 15 supplied Review 2 papers
- Methodology, dataset splits, preprocessing, training and temporal policy
- Held-out results, confusion matrices, resource comparison and training graphs
- Application screenshots and temporal integration checks
- Limitations, conclusion, project roles and reproducibility appendix
- Twenty references, including dataset and original architecture papers

## Evidence and scope

The report describes the local DriveAI project inspected on 28 September 2026. It uses the supplied report-format document, `example.pdf`, `driveee.pdf`, the existing Review 2 material, implementation files, training notebooks and saved evaluation artifacts. No models were retrained and no application files were changed.

Results are balanced-accuracy or other explicitly named crop-classification metrics against provisional weak labels. They are not independently validated fatigue-event or road-safety results. Speed, drive duration and rest routing are simulated. The report discloses the current 700 ms capture / 500 ms continuity mismatch and distinguishes saved classifier timing from end-to-end latency.

The author names and roll numbers follow the supplied review materials. Check these academic details before submission. The guide is listed separately from the three student authors; no author email or corresponding-author designation has been invented.

## Editing

Edit prose, equations, tables and plotting coordinates in `main.tex`. Edit references in `references.bib`. The two files under `figures/` are saved application screenshots. Their captions identify them as interface demonstrations.

If the application is later changed, revise the timing findings and results only after new verification. The current report must not silently be treated as evidence for a fixed version.

## Template attribution

`sn-jnl.cls` and `sn-mathphys-num.bst` are unmodified files from Springer Nature's December 2024 authoring package:
https://www.springernature.com/gp/authors/campaigns/latex-author-support/see-where-our-services-will-take-you/18782940

Their upstream license notices remain in the files. The format guide suggested Springer Nature; this academic report does not claim journal submission or acceptance.
