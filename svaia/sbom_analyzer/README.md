# SBOM-Analyzer component
Currently supporting: 
- Cyclone DX 1.6 JSON [https://cyclonedx.org/docs/1.6/json/]
Expecting to support:
- SPDX 3.0.1 [https://spdx.github.io/spdx-spec/v3.0.1/]

This service analyses SBOMS if a valid project token is given.
After the analysis, the database should be populated with a new enter that correlates the ProjectToken-Timestamp-AnalysisResult

