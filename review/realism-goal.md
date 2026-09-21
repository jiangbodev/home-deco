# Realism goal — active

User goal (2026-09-21): substantially improve lighting, material quality and realism of the existing home while retaining fast loading and smooth movement. Prefer Blender for mesh changes. Existing authorization includes main merge and GitHub Actions Pages publication.

## Verified baseline

- Release `fb0b3ea0939fddfa44ad22928a8c83cd56e17ef2`, PR #2. Build and Pages deployment succeeded; 19 live manifest/model/lightmap hashes matched local files. Live initial progress produced 109 updates, navigation to master bedroom worked, no browser or HTTP errors.
- 606,721 source triangles; 1,480 mesh nodes / 12 modules; complete model/finish/lighting bundle 8,655,920 bytes. Fixed 20 MB ceiling, identical modular assets on desktop/mobile. Both existing bedding modules protected from incidental changes.
- Existing light uses neutral hemisphere + directional sun, generic RoomEnvironment, two pendant area lights, raycast contact AO and simple direct-window irradiance. It lacks physically traced multibounce diffuse transport.
- Baseline archived locally at `qa/realism-baseline`, including exact assembled `source.glb`. The prior deployment remains untouched during exploration.

## Work and acceptance

1. Produce physically traced Blender Cycles reference views using existing geometry, sky/window direction and actual pendant positions. The workstation has a verified Metal GPU (Apple M4, 10 cores); renderer runs offline.
2. Test physically traced diffuse lightmaps for floor/wall/cabinet receivers. Keep static lighting offline, preserving optional loading/fallback and geometry-version checks. Avoid adding continuous full-scene shadow/reflection/AO passes merely to imitate the reference.
3. Calibrate material response and review silhouette/model deficiencies at room and close distances. Keep believable scale, restrained grain, soft roughness variation and useful geometry. Do not indiscriminately increase polygon counts.
4. Compare the same living, dining, desk, wardrobe, bedding and entry views after all assets/lighting load; measure navigation frame timing, draw counts, shader errors, startup readiness and downloaded resource bytes. Report hardware and measurement limitations. Preserve free walk and controls, state/reset behavior, module loading/retry and mobile layout.
5. Save editable Blender work and deterministic scripts, update README/evidence, publish only the verified result via main and verify the deployed files.

No user approval of a new visual style is inferred from an image. The user authorized improvement of this existing interior; start with natural daylight and warm restrained fixture light, maintaining the current design and furniture arrangement.

## Implemented and checked

- Cycles 4.5.14 LTS / Metal, 1,024 samples, up to five diffuse bounces; Nishita sky + sun + two authored pendants. Exact assembled `fb0b3ea` source, unchanged runtime geometry. 7 floor receivers / 501 box-projected architectural and furniture receivers. Floor 1024×512, wall atlas 2048×4096, log-encoded linear irradiance.
- Original color-map UVs are explicitly pinned while temporary LightingBake UVs target the atlases. Per-face OIDN RT HDR with replicated borders, then 2.5-texel residual-noise filtering and isolated gutter dilation. A whole-atlas denoise prototype visibly spread colors; it was rejected. Room-scale diffuse transport is prioritized over sharp small-object shadows in wall charts.
- Runtime uses 82% traced diffuse + 18% existing fill on wall receivers; floor uses traced diffuse, with a small neutral lift and calibrated gain. Existing specular response is preserved. This is a calibrated approximation, not a byte-exact Cycles beauty render. All optional data only activates after matching module versions and default interaction state.
- Two 1024×512 HDR probes from the same Cycles scene, prefiltered once by PMREM, apply local window/room reflections to 638 lacquer/timber/counter/steel materials. No continuous cube captures or extra render passes. Reflections are position-independent within each zone and are approximate at close distances.
- Budget now **12,798,527 bytes** including model, surface, lightmap, probe and metadata resources; unchanged initial model/texture set **3,476,224 bytes**. JavaScript/decoder/HTTP costs are excluded from that asset budget. Raster textures and prefiltered targets add GPU memory even though geometry stays unchanged.
- [Fixed-camera comparison](realism-comparison.jpg) is made from real Chrome canvases, not reference/render mockups. Desk, dining, rug and wardrobe shown side by side. Seven reviewed camera positions, all 12 modules present, no shader/page errors. The physical Blender reference renders remain local in `qa/cycles-daylight`.
- [Performance evidence](realism-performance.json): Chrome 153, ANGLE Metal Apple M4, 1280×900, DPR 1. Two runs per version, each 480 frames along the same living-to-master-and-back camera path after background loading. Median frame interval 16.7 ms both versions; before P95 16.8/17.6 ms, after 16.8/17.2 ms. No >34 ms samples. Draw calls median 185 / max 309 and triangles median 181,721 / max 293,917 unchanged. CPU submission median before 1.1–1.2 ms, after 1.2–1.3 ms. Local initial ready 681–714 ms before / 807–821 ms after. This is not a public-network loading test, whole-frame GPU timer or phone benchmark. Measurements use untouched shaders/compile pipeline but a deterministic test camera loop.
- [Behavior evidence](realism-behavior.json): normal desktop, deliberately failed new lightmap/HDR requests, and 390×844 mobile emulation. All remain navigable. Furniture toggle sets traced weight and local reflections to zero; reset restores them. Master-bedroom navigation keeps eye height 1.5 m. No page errors. Emulation validates behavior/layout only.
- Production build, real-progress regression and expanded CI asset/version budget check pass. Current immutable before source and live baseline remain available through `fb0b3ea`.

Publication is pending; update this record after PR checks and live verification.
