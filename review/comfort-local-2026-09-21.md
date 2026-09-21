# Local review follow-up — not published

User explicitly asked to keep this round local. No PR, merge or Pages publication is part of this follow-up. Earlier sofa/walkthrough reports describe intermediate snapshots.

## User feedback addressed

- Sofa inner corners: obsolete source AO was painted for two cushions and their original pillow positions. Copying the cushion also copied those dark patches. A same-camera layer comparison isolated the cause: removing the original AO eliminates the false dark corner; current geometry-based vertex contact remains. Blender authoring and modular import remove the obsolete AO from all three upholstery materials without flattening the fabric texture.
- Dark side cabinet / TV console / table: Blender lifts the shared walnut albedo while preserving grain; the runtime wood finish no longer adds a further 10% darkening. Changes remain non-emissive.
- Blotchy cabinet/ceiling illumination: browser layer isolation identified the Cycles irradiance layer. Diffuse charts now use stronger independent spatial filtering and restrained chroma before log encoding, retaining luminance variation without the noisy pink/green patches. This is an intentional visual calibration, not an assertion of exact physical color transport.
- Inconsistent ivory TV wall / niche shelves: the previous axis-alignment threshold excluded the arch and thick curved shelves but included adjacent flat walls and the middle shelf. They used different lighting paths. Explicit architectural curved receivers now participate in the same bake, keeping original material IDs and geometry.
- Brighter interior: higher sky contribution and southeast daylight, with moderate runtime ambient/diffuse lift; global exposure remains 1. No new realtime shadow/reflection pass.
- Bedding: remove bed pillows, throws and hidden legacy replacements. Each bed has a single deep plain navy quilt (linear RGB 0.012 / 0.022 / 0.045), no color texture or inherited sheen, 2,896 triangles. Visible bedding falls from 59,992 to 5,792 triangles (90.3%). The two sofa decorative pillows remain.
- Living-window trees: move the two existing trees 1.8 m outward and 0.9 m upward in Blender; preserve instanced source meshes, leaf density and all triangles. Other trees stay unchanged.
- Niche white vertical slits: ray picking confirmed the short end panels exposed the bright back wall. Blender replaces both zero-thickness panels with closed 12 mm boxes, extending their coverage to close the gaps (+20 triangles). Architectural curved normals are smoothed while retaining sharp caps.
- Eye height: room shortcuts and free walking both use 1.4 m.

## Geometry and validation

Total scene: 1,464 mesh nodes / 539,459 triangles, including hidden legacy geometry. 1,449 unrelated mesh bounds unchanged, six tree parts move by the intended vector, both quilts are texture-free navy, all named removed bedding meshes are absent, and sofa AO is absent. Decoded glTF validation has zero errors. See [geometry evidence](comfort-geometry.json), [Blender operations](comfort-blender.json), [browser evidence](comfort-browser.json).

All fallback and Cycles irradiance/reflection bakes are regenerated from the exact final assembled modular geometry. Local visual QA includes the user's sofa/cabinet, TV wall, niche, cabinet halo and ceiling examples, both beds, window trees and all nine room routes. Performance and final resource totals are recorded after the last verification below.


## Final local verification

- Rebuilt all fallback contact/daylight/object maps, Cycles irradiance (505 architectural receivers) and both HDR probes from `qa/comfort-source.glb`. Model hash manifests pass the budget validator; no metadata-only version overrides.
- Model resources: 6,917,397 bytes. Including every lighting and surface resource: 12,107,006 bytes / 20,000,000. Unreferenced intermediate assets were removed.
- 162 camera captures across nine rooms plus 1,620 moving-route frames; no browser errors, ceilings visible, all nine shortcuts and movement retain 1.4 m height. See [room evidence](comfort-views.json), [route evidence](comfort-routes.json), [room contact sheet](comfort-rooms.jpg) and [detail views](comfort-details.jpg). These checks cover the sampled views, not a claim that no possible viewpoint can show an artifact.
- Final full-lighting Chrome/Metal Apple M4 comparison, 1920×1080 CSS / DPR 2, same 300-frame route: old quality policy had 4 frames above 25 ms, maximum 33.4 ms; revised policy had 0, maximum 16.8 ms. Median 16.7 ms in both. Actual buffer reduced from 2976×1674 to 2065×1161; transmission target scale 1 → 0.5. This trades some high-DPI sharpness for smoothness; explicit high quality remains available. CPU P95 did not improve (3.7 → 4.6 ms), so the evidence supports reduced frame stalls, not a general CPU speedup. See [measurements](comfort-performance.json).
- Production build, loading-progress regression, nine-room navigation checks and decoded geometry validation passed. Vite retains its existing large Three.js chunk warning.
- Changes remain local and uncommitted at the user's request. Pages remains the earlier published version.

## Niche curved fascia follow-up

The user's 20:10 screenshot exposed a remaining sharp brightness seam at the middle of each curved fascia. The six-direction box projection switches atlas faces at the dominant-normal boundary. Adding the curved receivers and smoothing mesh normals did not fix this unsuitable parameterization. Same-camera isolation of both projected contact and irradiance removed the seam.

The three `圆弧包覆实体层0/900/1230` shells now use continuous PBR lighting and reflections, without the box-projected contact/irradiance overrides. Flat niche lining retains its baked lighting. This targeted rendering correction changes no geometry, material asset, bake version or draw pass. Existing genuine bakes remain valid for their active receivers. Three-angle before/after evidence: [comparison, before above / after below](niche-lighting-seams.jpg). No blanket brightness or exposure increase was used.


## Subsequent user corrections (local)

This section supersedes the earlier end-panel closure and resource/geometry snapshot above. Both bright niche end boards are deleted, rather than thickened or hidden. All dining flower leaves, sprigs, petioles, legacy stems and the glass vase are removed. The bathroom privacy partition is split into fixed and sliding panes, defaults open and supports close/reopen/reset; the shower glass remains unchanged. Every room, including 主卫 and 次卫, now appears in the bottom navigation (horizontal scrolling on narrow screens).

Current decoded scene: 1,386 meshes / 532,981 triangles; 1,370 unrelated mesh bounds unchanged, zero glTF validation errors. Fresh fallback maps, Cycles diffuse maps and HDR probes are generated for this exact revision. The earlier performance comparison remains evidence for the rendering-policy change, not a new timing measurement of this revision.


Final verification of these corrections: 6,871,941 model bytes; 12,054,308 bytes including all lighting and surface resources. Version checks, production build and glTF validation pass. Main-bath close/reopen/reset and bottom-navigation clicks at 1280, 800 and 390 px pass, with no page overflow. Latest niche screenshot is `niche-removed-panels.png`; door checks are in `bath-partition.json`, dock checks in `room-dock.json`. These latest values supersede the previous snapshot totals.


Final vase correction: the visible props were `Hollow glass vase` and `Water with visible surface`, separate from the hidden legacy Chinese-named vase. Both visible objects and the remaining legacy leaves are now removed. A rendered tabletop check confirms the empty surface; geometry validation checks every removal explicitly. Lighting is rebaked again after this correction.

最终全屋复查与最新资源数据以 [whole-house-latest.md](whole-house-latest.md) 为准。
