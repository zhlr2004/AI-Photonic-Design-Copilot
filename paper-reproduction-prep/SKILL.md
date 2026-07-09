---
name: paper-reproduction-prep
description: Prepare physics paper reproduction tasks from markdown papers and image folders. Use when asked to link paper figures, summarize the paper, assess which figures suit FDTD reproduction, or adapt/create instruction.md for lumapi/FDTD-based reproduction workflows.
disable-model-invocation: true
---

# Paper Reproduction Prep

Use this skill to prepare a markdown physics paper for a figure reproduction task. Keep edits scoped to the task root unless the user gives a narrower boundary.

## Workflow

1. Verify paper/image linking first.
   - Locate the main markdown paper and the image folder. If normal file search misses images, use PowerShell recursive enumeration with hidden files, for example `Get-ChildItem -Force -Recurse`.
   - Check whether every supplied paper image is already linked from the markdown, and whether links point to existing image files.
   - If links are missing or broken, inspect figure numbers, captions, image names, and image contents, then insert Markdown image links at the corresponding figure/caption locations.
   - Do not rewrite the paper body while linking figures unless explicitly asked.

2. Write `brief_analysis.md` in the main task folder.
   - Read the paper together with the linked figures.
   - Combine the paper summary and figure analysis in one concise document.
   - For each major figure, state what it shows and whether it is suitable for FDTD reproduction.
   - Be explicit about which panels are direct electromagnetic-field targets and which panels depend mainly on experimental statistics, post-processing, noise, or instrument modeling.

3. Adapt or create `instruction.md`.
   - If `instruction.md` already exists in the main task folder, rewrite it with minimal changes so it matches the current paper, target figures, file names, and deliverables.
   - If `instruction.md` does not exist, copy/adapt one local sample from [`examples/`](examples/).
   - Samples may be named `instruction-example_0.md`, `instruction-example_1.md`, etc. Inspect available samples and choose the closest match to the current reproduction task before adapting it.
   - Preserve the workflow style of the sample where possible.
   - Always require `lumapi`/Lumerical FDTD for electromagnetic-field calculation.
   - Always forbid directly constructing analytical electromagnetic fields to bypass FDTD for final PNG/CSV outputs.
   - Require `.fsp`, reproduced `.png`, and plotting `.csv` outputs under `data/`, with one set per reproduced panel or subfigure and matching basenames.
   - Require implementation scripts under `reproduction/`.

## Quality Checks

- Confirm image links render to files that exist.
- Confirm any selected instruction sample comes from `examples/` and is adapted rather than copied blindly.
- Search the final `instruction.md` for stale title, figure, file-name, or physics terms from a previous paper.
- Confirm the requested reproduction targets, `data/` outputs, and `reproduction/` scripts are named consistently.
- Confirm FDTD/lumapi source-of-data and anti-cheat constraints are still present.
