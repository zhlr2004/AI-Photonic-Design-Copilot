# Case cleaning policy

The source case is immutable. Inventory and hash it before copying, and verify
the same snapshot after staging preparation. All transforms and exclusions
apply only to the staging copy.

## Include

- V1 platform contracts and traceable metadata.
- Python, LSF, parameter files, `.fsp`, and complete Meep configurations.
- Raw and derived JSON, CSV, NPZ, HDF5, and equivalent solver results.
- PNG, SVG, permitted PDF, Markdown, text reports, and necessary run logs.
- Paper metadata, figures, and supplements whose license permits storage.

## Exclude from staging copies

- `.git`, `.svn`, `.hg`, virtual environments, caches, and build output.
- `__pycache__`, `.pytest_cache`, editor swap/backup files, thumbnails, and
  crash dumps.
- Unreferenced temporary/autosave files and exact duplicates.
- Unrelated installers, downloads, and derived duplicates reproducible from
  retained raw data.

Record every excluded path, source hash, and reason. Never silently discard an
unknown structured field; record it under `removed_fields` or
`unmapped_metadata`.

## Block instead of deleting

- API keys, tokens, passwords, private keys, or license-server credentials.
- Paper full text or third-party data without confirmed storage rights.
- Symlinks/junctions, path traversal, or dependencies outside the source root.
- Machine-specific absolute paths still required for execution.
- Two different sources mapping to the same case-insensitive target path.
- Existing `example_id@version`.
- Uninspectable binary content proposed for public publication.

## Complete only traceable information

- Compute hashes, sizes, MIME guesses, relative URIs, and tree fingerprints.
- Extract metadata only from named files and record the file/JSON Pointer.
- Never infer physical parameters, solver execution, convergence, license,
  quality, reviewer, or sensitivity.
- Missing RunManifest/ValidationReport limits the candidate to `archived`.
- Paper reproduction without Evidence/Targets may be staged but not promoted
  to `validated` or `reviewed`.
- Failure cases require a `failure` tag and cannot exceed `executed`.
