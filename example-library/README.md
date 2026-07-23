# Folder Example Library

This is the default root for the small, self-contained photonic example
library. Set `PHOTONIC_EXAMPLE_LIBRARY_ROOT` or pass an explicit path to use a
different location.

Do not edit published version directories or `catalog.json` manually. Use
`FolderExampleLibrary.publish()` after G3 review. Rebuild a missing or damaged
catalog from manifests with `FolderExampleLibrary.rebuild_catalog()`.

Legacy or nonconforming cases must first use:

```text
@curate-photonic-example-case/SKILL.md
```

The curator reads the source case without modification, copies it to
`staging/`, removes approved non-library content from the copy, adds only
traceable metadata, and prepares a candidate for G3.
