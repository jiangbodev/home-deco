# TV wall head, tree structure and entry follow-up

The TV wall solid stopped at 2.37 m beneath a 2.7 m ceiling. Blender extends the existing wall to the ceiling and places the front at X=5.5483, separating it from the adjacent arch/soffit faces. Nine edited meshes: one wall and eight woody tree instances. Original pre-collapse branch/trunk topology is restored; reduced foliage and current tree placement remain. Both woody prototypes stay shared. Runtime ivory/PBR face treatment remains in place.

All fallback contact/daylight/object maps, 1024-sample Cycles diffuse atlases and two HDR probes were genuinely regenerated from qa/tv-tree-source.glb. No metadata-only version replacement. Current editable Blender source: source/home-deco-tv-tree.blend.

Validation: 1,386 mesh nodes, 568,029 triangles (+6.6%); 1,373 unrelated mesh bounds preserved. Module validator: 0 errors, exact decoded geometry/transform match. Total model, lighting and finish resources 12,102,363 bytes; about 46 KB above the preceding release, under 20 MB. Chrome/Metal on Apple M4, 300 moving frames, 1920×1080 DPR 2 with auto resolution: median/P95 16.7 ms, maximum 16.8 ms, 0 frames above 25 ms. This is this computer's result, not a mobile guarantee.

Comparisons: [tree structure](tree-structure.jpg), [wall head](tv-wall-head.jpg), before on the left. The large flattened/slivered branch shapes disappear. Simplified foliage remains appropriate to the distant window view.

Entry correction: moving backward along the old view vector placed the main-bath camera inside the wardrobe area and the second-bedroom camera facing the fridge cabinet. Wall/door-only clearance was insufficient. Final positions follow actual door apertures: main bath (10.1, 1.4, 2.5), second bedroom (4.1, 1.4, 3.9), secondary bath (4.9, 1.4, 2.69). Actual browser screenshots show interiors, all nine room labels remain correct after a forward step, and three parallel rays through the first metre of the three requested approaches find no visible opaque obstacle. See entry-paths.json, room-entries.jpg and room-entry-clearance.json. Free walkthrough remains enabled.

Dining is removed only from bottom shortcuts; it remains selectable in the floor plan. New loading design and original lighting-ready gate retained. Build, budget and loading-progress checks passed. These changes are local; no publication performed.
