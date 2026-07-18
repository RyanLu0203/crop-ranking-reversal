# Import package validation

Validation date: 2026-07-18. Quarantine: `imported_reproducible_assets/`. Aggregate package hash before and after external audit: `577aa1fc5472e59bd3d32d50f5808797156e5746e8e7bd108ed3adb80d9da4d6`.

## Results

- Checksum: PASS; all 197 records in `SHA256SUMS.txt` matched.
- Manifest: PASS; 196 rows, 196 existing paths, zero missing, zero duplicate paths, zero malformed records, and zero unmanifested files after excluding the manifest and checksum manifest themselves.
- Secret scan: PASS; no credential assignment, token, cookie, or private-key signature was detected.
- Teacher baseline: PASS; both canonical TeX and PDF exist. Their pre-audit hashes were `e8885aa89be6a6010f0d3e6f8e40b4b8192a91fc90f6ca4fb16ae9b0aa9dd26c` and `52ac1b4ef21c8d406fd6d722c877935a24d2cc6ea68520a6f35470ba8b334b44`.
- Provenance: PASS WITH LIMITATIONS; branch and commit are recorded and the 165-entry dirty state is captured by status, diff-stat, tracked-file list, and `UNCOMMITTED_BUT_CAPTURED.patch`.
- Historical manuscript contamination: PASS; no historical manuscript was classified or promoted as evidence.

## Duplicates

Four byte-identical pairs were found: expected-versus-generated smoke JSON, expected-versus-generated empirical summary CSV, two identical smoke logs, and two copies of the processed-panel validation JSON. These are explained test/provenance duplicates and were not all promoted.

## Classification and provenance concerns

- The imported package labels the processed panel `VERIFIED_REPRODUCIBLE`, but its manifest gives no exact end-to-end processing command. Canonically it is therefore `REQUIRES_FULL_RERUN`, despite passing schema and checksum checks.
- Raw files are correctly treated as externally downloadable, but the imported raw manifest uses obsolete absolute paths. The canonical manifest rewrites paths only; raw bytes are unchanged.
- The BEA deflator lacks a sidecar download URL/checksum record in the imported raw manifest, so it is retained as a source snapshot but not admissible for substantive results pending provenance repair.
- Repository code has no explicit software license. Canonical use is project-internal pending author clarification.
- Some imported files are verified migration documentation rather than scientific evidence; their classification must not be read as manuscript-claim admissibility.

## Official source inspection

USDA NASS identifies Quick Stats as its comprehensive customizable agricultural database and notes weekday updates. USDA ERS documents Commodity Costs and Returns coverage, methods, regional resolution, update schedule, and limitations. BEA documents the GDP implicit price deflator and warns that archived estimates are revised. These inspections support source ownership, not result admissibility.
