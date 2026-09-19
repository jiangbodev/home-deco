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
