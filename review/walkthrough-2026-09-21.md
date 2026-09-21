# Nine-room walkthrough and surface repairs

The user reported severe flicker beside the dining-room television and a transparent-looking ceiling, then asked for an autonomous inspection of every room. This revision includes the approved warm-white 2.32 m three-cushion sofa and repairs discovered during the full-house inspection.

## Findings and Blender repairs

- The TV-side arch and connecting pier had almost coincident outer faces (roughly 0.08–0.30 mm apart). The mirror waterproof backing also overlapped the shared wall on its opposite side. Recessed secondary boundaries by 2 mm while keeping the principal continuous finish.
- Cabinet side-panel and top-cap fronts across the entry, living room, kitchen, bedrooms and bathrooms intersected their beveled door fronts. Recessed those carcass boundaries, preserving door geometry, hinge transforms, materials, module attachment and interaction metadata.
- Separated the entry column/soffit boundary, main-bedroom wall/window-frame joint and bath apron/rim caps.
- The main roof was a zero-thickness upward-facing sheet, rendered DoubleSide. Its underside sampled the sky-facing irradiance chart because chart selection ignored fragment face orientation. Blender now supplies a closed 60 mm slab above the original 2.7 m interior height; both contact and Cycles shaders select the correct back-face chart. Ceiling irradiance charts receive stronger isolated offline smoothing to reduce blotches without changing material textures.
- Main-bath navigation previously stopped outside; its shortcut now starts inside at X=8.95, Z=2.3. Free movement through all walls/furniture remains enabled.

63 meshes repaired; 1,417 unrelated mesh bounds unchanged. The roof has paired manifold edges and upward/downward faces. Total mesh count remains 1,480; triangles are 611,437 (+16 for these repairs, in addition to +4,700 for the third sofa cushion). Decoded glTF validation: zero errors. See [geometry checks](walkthrough-geometry.json), [Blender edits](walkthrough-blender.json) and [integration records](walkthrough-integration.json).

## Inspection and verification

Inspected the entry, living room, dining room, kitchen, main bedroom, second bedroom, children's room, main bathroom and second bathroom. Each room has six directional views with three 25 mm camera offsets: 162 still captures per pass. Separate four-position routes render 180 moving frames per room, including closer approaches to the TV, cabinetry and bath interior: 1,620 frames total. These are instrumented real Chrome/WebGL renders; the diagnostic script controls the camera directly and does not skip shader compilation.

[Room contact sheet](walkthrough-rooms.jpg), in reading order: entry, living, dining / kitchen, main bedroom, second bedroom / children's room, main bath, second bath. [Ceiling comparison](walkthrough-ceiling.jpg): same camera, before left / after right. Full positions and render statistics: [views before](walkthrough-views-before.json), [views after](walkthrough-views-after.json), [moving routes](walkthrough-routes.json).

The repeatable 66,000-ray opaque-surface proximity audit found 722 sub-0.3 mm distinct-surface hits before and 76 after (89.5% reduction). These are diagnostic ray hits, not a count of visibly flickering pixels. The major arch, mirror, cabinet front and tub-apron pairs were removed; residual candidates are mainly small frame joints/shared edges. No claim is made that every possible view or interaction state is free of aliasing. See [raw comparison](walkthrough-overlaps.json).

Final nine-room captures and routes: zero page/shader console errors. M4, desktop Chrome, 960×720, DPR 1: per-room route frame-interval p95 17.6–18.5 ms; maximum 23.8 ms. This short diagnostic route is not a phone benchmark or a guarantee on other hardware. All nine navigation positions have floor support and no wall within 22 cm. Loading-progress checks passed.

All fallback contact/daylight/object maps, Cycles diffuse maps and both HDR probes were regenerated from the exact repaired modular source. The existing low-cost runtime lighting approach is retained; no extra realtime shadow/reflection/AO pass. Production build and manifest/hash/version/budget checks passed. Total model, texture and appearance resources: **12,815,639 bytes / 20,000,000**; model-only resources 7,454,125 bytes. The sofa-only review is an intermediate checkpoint; this document describes the combined final asset set.

## Reproduction

Follow source/README.md. Geometry authoring uses Blender 4.5.14 LTS and immutable post-sofa input. Never rerun the inset script cumulatively. Reassemble the exact modules before every bake and use a fresh raw bake output folder. `check-walkthrough.mjs` verifies bounds, roof topology/normals and glTF validity; room-view and moving-route scripts preserve camera positions for future comparisons. Public release is verified separately after GitHub Actions completes.
