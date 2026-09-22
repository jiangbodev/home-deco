# Whole-house realism goal · 2026-09-22

Baseline: published main `3a64f6871b85b3e4a101cde7d1d4b1d07591a2a2`. User explicitly delegates another overall realism review and goal. Local refinement only; retain the existing apartment plan, all openings, 1.4 m free walk, navy bedding, empty dining tabletop, three-seat warm-white sofa, entry shortcuts and simplified settings. No paid generation or new external assets.

Skill adapter: existing residential walkthrough, custom family. This is a detail refinement of user-approved architecture, not a new room composition. Original circulation/openings remain; no broad new symmetry or 2.4 m entry requirement is applicable to this apartment. The user's autonomous editing instruction governs incremental local design/export review; publication still requires a new request.

First actual browser pass covered entry, living, dining from living, kitchen, both bedrooms, children's room and both bathrooms. Most noticeable issues: entry books remain lacquer-colored solid blocks; entry vessels have coarse silhouettes and unconvincing mouths; indoor leaves read as folded polygons; some open timber shelves lack coherent grain and softened construction; bathroom mirrors reflect a blurry static room probe rather than the actual view. Furniture already improved in the prior pass is retained. No decorative clutter is added to the dining table or the deliberately empty children's room.

## Work and acceptance

- Blender incremental source `source/home-deco-realism-v2.blend`, immutable input `qa/realism-v2-before.glb` and `qa/realism-v2-original`. Script `scripts/blender-realism-v2.py` edits 25 existing nodes; no new scene nodes. Five books receive cover boards, spine and inset paper; two pottery shells have mouth, inner wall and foot; seven leaf meshes have welded smooth normals and satin leaf material; eleven timber shelves receive appropriate grain/edge treatment.
- Module integration must retain all unrelated geometry bounds, transforms, module identities and interaction metadata. `review/realism-v2-validation.json`: 1,387 unrelated bounds retained, 613,469 triangles (+1.54%), no added nodes.
- Rebuild contact, fallback daylight, object shading, Cycles irradiance and HDR probes from the exact final assembled source. Do not bypass stale-version rejection.
- Accurate planar mirrors are enabled only for nearby visible desktop mirrors in high (清晰) quality. At most one 768² reflection capture; auto/low and coarse pointers retain static fallback. Both mirror outlines/perspectives and partition interaction were visually checked. Excluding transmissive panes and blocking auxiliary-pass recursion reduced cost, but default-mode trials still dropped frames; realtime mirrors were therefore rejected for default auto quality. Reflected glazing does not reproduce refraction.
- Final review includes room-scale and close views, support and openings, loading/build/resource validation, and movement samples. Keep remaining approximation and device limits explicit.

Status: completed locally. Final geometry, fresh lighting/probes, browser review, build/resource checks and default-quality movement samples passed. See realism-v2-review.md and realism-v2-performance.json. Not committed or published.
