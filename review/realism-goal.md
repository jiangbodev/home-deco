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
