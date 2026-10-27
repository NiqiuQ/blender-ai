# Interior scene rebuild

## Acceptance criteria
- Three distinct usable camera views; no black or wall-blocked renders.
- No visible mesh intersections, floating objects, or objects embedded in walls/floor.
- Furniture proportions and clearances are plausible.
- Materials have consistent roughness and scale.
- Lighting exposes the room without clipped highlights.
- Every iteration renders all views and is visually reviewed before delivery.

## Generation and review loop

Run the rebuild script from Blender in background mode:

```bash
blender -b --python create_scene_rebuild.py
```

Generation writes the three camera renders to `previews/`, saves
`interior_scene.blend`, then invokes `review_scene.py`. The review rerenders
every camera and records measurable checks (camera count and validity, meshes
below the floor, and non-empty render outputs) in `review_report.json`.
Blender exits with a failure code when any check fails, so CI or an external
orchestrator can reject the iteration and request a regeneration. The PNGs
remain the visual-review artifact for a human pass against the criteria above.

To review an existing blend without regenerating it:

```bash
blender -b interior_scene.blend --python review_scene.py
```
