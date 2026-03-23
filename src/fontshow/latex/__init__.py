"""
LaTeX rendering subsystem.

This package contains modules responsible for generating LaTeX output
used by the Fontshow catalog generation pipeline.

Responsibilities
----------------
- Implement rendering helpers used to generate LaTeX documents.
- Provide rendering policies for mapping inventory metadata to LaTeX.
- Support catalog document generation and template processing.

Design principles
-----------------
The LaTeX subsystem transforms normalized inventory metadata into
LaTeX structures but does not perform inventory analysis or metadata
inference. Rendering logic remains separate from pipeline orchestration.

Architectural role
------------------
This package belongs to the **catalog rendering subsystem** and
implements LaTeX document generation used by the `create-catalog`
workflow.
"""
