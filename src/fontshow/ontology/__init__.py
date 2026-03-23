"""
Ontology subsystem package.

This package contains the static linguistic and Unicode ontology used
by Fontshow for script analysis and language inference.

Responsibilities
----------------
- Provide authoritative tables describing writing systems.
- Define language inference profiles used by the inventory pipeline.
- Supply canonical specimen samples and metadata for scripts.

Design principles
-----------------
Ontology tables are static, deterministic data structures derived from
standards such as ISO 15924 and Unicode. They contain no runtime logic
and must remain stable to ensure reproducible analysis results.

Architectural role
------------------
This package belongs to the **ontology subsystem** and provides the
knowledge base used by inventory processing and catalog rendering.
"""
