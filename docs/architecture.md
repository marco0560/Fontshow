# Fontshow architecture

Fontshow follows a strict layered pipeline.

## Layers

- Discovery layer (OS-dependent)
- Inference layer (JSON-only)
- Rendering layer (LaTeX)

## Benefits

- Deterministic output
- Cross-platform consistency
- Clear separation of concerns


The parsing and inference pipeline is platform-independent; OS-specific
logic is confined to the font dumping stage.
