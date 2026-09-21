# Project handoff for future agents

## User workflow

Continue this project in the cloud. The user expects fixes to the existing home-deco walkthrough, not a new site or local setup instructions. Keep the public site anonymous. Use the same modular assets for desktop and mobile and preserve the 20 MB total model budget.

Report concrete progress and blockers promptly, at least once per minute during ongoing work. Explain what failed and what the next attempt will resolve. Do not repeatedly say only that work is being checked. Do not blame model size without evidence.

## Verified workflow and pitfalls (2026-09-19)

- GitHub repository: jiangbodev/home-deco; production branch: main; Pages URL: https://jiangbodev.github.io/home-deco/.
- Public git clone/fetch worked. Ordinary git push had no usable credentials in the execution environment. For writes, prefer the connected GitHub tools: create_blob, create_tree based on the current tree, create_commit with the current parent, then update_ref without force. Inspect current remote state first. Do not repeat failed credential experiments or ask the user for secrets.
- Binary GLB upload succeeded with create_blob using base64. The shell tool truncated a large base64 response near 1 MiB even with a high token budget. Read the local file in 600,000-byte chunks, base64-encode each chunk, collect outputs programmatically without printing them, verify the assembled length is 4*ceil(fileBytes/3), then upload. All non-final chunk sizes must be divisible by 3. Do not expose binary data in chat. Tool-side temporary stores may be unavailable after a new user turn; retain returned SHAs in the task record.
- Default Playwright browser binaries were absent, and CDN installation failed. The working fallback was @sparticuz/chromium installed in scratch. Extract its Brotli chromium binary and SwiftShader archive locally; extracting archives with --no-same-owner avoided chown errors. Use Playwright with that executable and the package's launch arguments. Reuse an available working browser before attempting installation again. Keep these diagnostic dependencies out of production package.json.
- Vite with host 0.0.0.0 failed on network-interface enumeration; 127.0.0.1 worked. Launch Vite and the browser as child processes in the same execution call because execution contexts may not share running services.
- Software-rendered screenshots of the continuously animated full scene timed out. For focused geometry comparisons, the working diagnostic harness used an 800x600 viewport, pixel ratio 1, stopped the animation loop after model readiness, rendered the selected view, and captured canvas.toDataURL immediately. A test-only request interceptor exposed scene/camera/renderer and skipped compileAsync. These are diagnostic changes only: do not ship them or claim they validate untouched startup or mobile performance. Record camera changes and use the same view before and after.
- After publication, check the GitHub Actions result and download the live GLB to compare its hash with the intended local file. Distinguish upload, commit, deployment, and live verification in status messages.

## Bedding regression

The visible bedding is under Blender软床品_main and Blender软床品_second. Child names include fabric 1, White Fabric, Fur_black and their .001 counterparts. Protect the whole group from simplification; name matching for pillow or 枕 missed these objects and protected hidden legacy pillows instead.

Repair commit fd26d8c4c8150213cc3191568da9b347052ca004 restored all six visible bedding meshes from the pre-simplification baseline via scripts/restore-bedding.py. The resulting model is 9,123,564 bytes. Matching before/after Three.js views showed the conspicuous black holes disappeared in both bedrooms. Decoded validation: 0 errors, 235 existing warnings. All other binary payloads, scene nodes, materials, and textures were preserved. The live model hash matched the repair. This is a verified checkpoint, not a substitute for reading current repository state.

## Modular loading update

The user authorized modular loading with adjacent-room prefetch and independent updates. Read README.md and src/modules.js. Production loads assets/modules/manifest.json, not the historical home.glb. Keep base skeleton nodes and collision geometry resident; attach deferred meshes to their original moduleNode via attachTo. Never re-run readStates after attaching a module: that would reset user choices. Keep shared textures content-addressed, retain loaded rooms, deduplicate pending loads, and preserve retry and last-request-wins navigation. Geometry verification accepts the original source path as an argument.

## Loading-time black-frame prevention

Adaptive resolution must resize BEFORE rendering the frame. Canvas size changes clear its contents; never end an animation frame by resizing after render. Skip unchanged sizes and redraw immediately for external resize/quality changes. Await serialized module GPU preparation before attaching it, preserve texture sampler/UV/color-space variants when sharing texture objects, and resume the render loop after WebGL context restoration. Do not claim a user's transient black screen has been fully reproduced from this code finding alone.

## Walking into cabinetry regression

The old wall-label-only collision list omitted the entry solid back wall, finishes, and cabinet panels. Reproduced at y=1.5, z=6.4: movement from x=4.5 toward negative x reached x=3.8 inside the entry cabinet; the corrected sweep stops at x=4.25, outside its x=4.064 front. Use world-space mesh bounds for broad-phase filtering and visible mesh surfaces for narrow-phase sweeps with 0.18 m clearance. Refresh bounds after door/furniture state changes, reset, and late module attachment. Do not remove delayed furniture from collision registration. Wait for a destination room's modules before walking into it. Nine room spawn points retained a free exit in the regression check. This fixes an actual collision defect; do not classify every solid-color screenshot as a loading failure.

## Mobile controls layout

Keep thumb movement and navigation in separate zones: portrait joystick bottom = dock bottom + dock height + 34 px; landscape uses a left thumb zone and toolbar starting 42 px to its right. Put the movement label above the joystick. Use safe-area insets, >=44 px fixed tool targets, horizontally scrollable room shortcuts, and keep the selected shortcut visible. Center the knob using CSS and derive travel from actual joystick width. Opening a dialog clears input. Layout checks covered 320x568, 390x844, 430x932, 844x390, 667x375 and 1024x768, plus a simulated 34 px bottom inset, drag/release and dialog access; these were layout-only browser checks, not mobile GPU performance tests.

## Baked contact shading and material calibration

See review/appearance-2026-09-19.md and src/appearance.js. Preserve the original GLB payloads and restored bedding. Contact maps are offline ray-traced from actual source triangles by scripts/bake-floor-contact.mjs; three-mesh-bvh is a build-only dependency, not a runtime import. Floors use world X/Z, fixed axis-aligned walls/cabinets use six projected charts. Exclude doors, moving windows, curtains, ceiling and transparent objects from baking. Keep fixed and default-furniture occlusion separate; disable furniture occlusion when furniture/piano/dining state differs, and restore it with tolerance after toggling back. Only enable baked shading after all modules load and their content-addressed filenames match the bake metadata. Update both metadata and bakes when changing geometry; never simply rewrite their version list to bypass invalidation. Optional image failures must leave the walkthrough usable. Warm GPU uploads and compile shaders before showing geometry. Do not add continuous shadow or full-screen AO passes without a separate mobile performance assessment. Current measurements are software-rendered functional checks, not real-device FPS evidence.

## Wall and cabinet finish follow-up

The user found the first lighting pass still too flat/white. src/surface-finishes.js now distinguishes source material IDs 2/3/4 (plaster) from 8/24/37/38/54/56/62/64/67/85/87 (painted cabinetry). Do not apply finishes by a broad white-color heuristic: it also hits books, porcelain, textiles and stone. Chain finish shaders AFTER the existing contact-occlusion shader, preserving program cache keys and per-object AO uniforms. Shared 256px packed material-data texture has tileable low-frequency variation, micro-height, and roughness; use mipmaps and world-metre projection rather than arbitrary mesh UV scales. Keep plaster relief subtle: the initial 0.7mm/12% trial looked mottled at room distance and was reduced to 0.32mm/5.5%; lacquer relief is 0.12mm with satin roughness 0.43. This is shading only, no displacement or new geometry. Check close views and normal room distance, and capture shader console errors as well as page errors. Texture generation is deterministic via scripts/make-surface-grain.mjs. The shared PNG is included in the 20 MB check.

## Directional daylight and functioning luminaires

User reported the microfinish pass was still visually indistinct and lighting unchanged. scripts/bake-room-lighting.mjs now ray-traces eight actual exterior window apertures (six samples each) and four authored track lenses into the existing world-space atlases, using fixed geometry as blockers. It reuses contact channels, so it requires the contact bake first. The floor's alpha data is biased to 128..255 (not coverage); preserve straight-alpha upload and decode `(a*255-128)/127`. Wall G/B carry day/warm energy. fixtures.json records the shared source positions. Do not substitute generic room-center lamps.

Runtime uses two finite RectAreaLights at the two authored dining bulbs, not point lights (point sources caused distracting sparkles in rippled glass). Their visibility follows the actual source nodes. GLTFLoader strips punctuation: use THREE.PropertyBinding.sanitizeNodeName for suffixed names like 餐桌灯泡.001. Warm track energy is disabled when its fixture is hidden. Baked illumination fades in via appearance.tick, after all modules/maps/version checks pass. Optional metadata fetches are concurrent, time-bounded and revalidated. Preserve AO and microfinish shader composition. The comparison PNG is an actual same-camera browser capture, not a generated render. Lighting remains an artistic realtime approximation: no full global-illumination solution, dynamic occluder shadows or phone-FPS guarantee.

## Tabletops, counters and cabinet surfaces

Surface finishes now use explicit timber IDs 9/15/17/25/32/35/41/45/50/52/65/69/72/75, pale counter 19 and sink steel 80. Preserve scanned base/normal/roughness maps and dark gap backing materials. Reuse the packed grain texture; no additional downloaded texture or geometry. Timber uses restrained satin roughness 0.7, lower normal strength and grain-correlated roughness. Countertops use fine neutral grain, not invented marble veins; steel uses directional micrograin.

Shader-only edge easing is restricted to small sharp axis-aligned box meshes with flat normals; it does not alter silhouettes or collision geometry. Each receiver is cloned for local bounds, explicitly retaining its onBeforeCompile callback and program cache key because Material.clone does not preserve callbacks. Never discard baked-light/AO composition. Distinguish shader edge shading from a real geometry bevel. Additional shader work is not a mobile-FPS guarantee.

## Whole-house finishes and vertex contact (2026-09-20)

Final mapped wood roughness has a 0.52 floor; source normal intensity and plaster grain reduced. Neutral sky/warm ground lighting replaces green-biased fill. `object-contact.js` optionally loads gzip-packed occlusion for 215 dense meshes / 686559 vertices, validating module filenames, vertex counts and position-byte FNV hashes. The bake script preserves original geometry. Avoid sparse panels (<96 vertices or <300 vertices per world bounding-box square metre). Share original attributes/index; add one byte per vertex only. Disable contacts immediately when furniture/piano/dining states differ, fade back on restore. Chain existing AO/finish callbacks and program keys. Handle both HTTP automatic gzip decompression and raw gzip bytes; failures remain optional. No extra shadow pass; not full GI or measured phone FPS.

Commit durable checkpoints to a remote branch during long tasks; an interrupted turn can lose uncommitted scratch changes. A local commit alone does not provide remote persistence.

## User-approved free walk and simplified bedding (2026-09-21)

The user explicitly chose to remove ALL collision checks, including walls and furniture, and deprioritized bedding detail. This supersedes the earlier collision-blocking requirements and the blanket protection of full-resolution bedding. Keep free movement at fixed eye height; do not restore wall/furniture blocking unless requested. Room loading readiness and navigation shortcuts remain.

Both restored bedding modules were reduced from 299,990 to 59,992 triangles in Blender 4.5.14 LTS, with welded vertices and editable Decimate COLLAPSE 0.2 modifiers. The user explicitly requires Blender for model edits. Use scripts/blender-simplify-bedding.py and scripts/import-blender-bedding.mjs with the untouched restored input modules, never recursively simplify the result. source/home-deco-bedding.blend is a local GLB-reconstructed editable scene, not the missing original authoring project. Original pre-change modules remain in commit 8fcd1e1. Shared textures and all other modules were preserved. Reassemble actual decoded modules with assemble-modules.mjs and rerun all three bakes whenever geometry changes; metadata-only rewrites remain prohibited. See review/performance-2026-09-21.md for CPU findings, visual/browser checks and limits.
