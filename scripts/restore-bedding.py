"""Restore authored bedding primitives without re-encoding any other geometry.
Usage: python scripts/restore-bedding.py BASELINE.glb CURRENT.glb OUTPUT.glb
The baseline must be the pre-simplification model, not a previously reduced GLB.
"""
import copy, json, struct, sys
from pathlib import Path

def read(path):
    data = Path(path).read_bytes()
    magic, version, length = struct.unpack_from('<III', data)
    assert magic == 0x46546c67 and version == 2 and length == len(data)
    size, kind = struct.unpack_from('<II', data, 12)
    assert kind == 0x4e4f534a
    document = json.loads(data[20:20+size])
    bin_size, kind = struct.unpack_from('<II', data, 20+size)
    assert kind == 0x004e4942
    return document, data[28+size:28+size+bin_size]

source, source_bin = read(sys.argv[1])
target, target_bin = read(sys.argv[2])
result_bin = bytearray(target_bin)
view_map, accessor_map = {}, {}

def copy_view(index):
    if index not in view_map:
        view = copy.deepcopy(source['bufferViews'][index])
        assert view['buffer'] == 0
        result_bin.extend(b'\0' * (-len(result_bin) % 4))
        offset = view.get('byteOffset', 0)
        chunk = source_bin[offset:offset+view['byteLength']]
        assert len(chunk) == view['byteLength']
        view['byteOffset'] = len(result_bin)
        result_bin.extend(chunk)
        view_map[index] = len(target['bufferViews'])
        target['bufferViews'].append(view)
    return view_map[index]

def copy_accessor(index):
    if index not in accessor_map:
        accessor = copy.deepcopy(source['accessors'][index])
        assert 'sparse' not in accessor
        if 'bufferView' in accessor:
            accessor['bufferView'] = copy_view(accessor['bufferView'])
        accessor_map[index] = len(target['accessors'])
        target['accessors'].append(accessor)
    return accessor_map[index]

source_nodes = {n['name']: n for n in source['nodes']}
target_nodes = {n['name']: n for n in target['nodes']}
report = []
for group_name in ['Blender软床品_main', 'Blender软床品_second']:
    group = target_nodes[group_name]
    for node_index in group['children']:
        node = target['nodes'][node_index]
        original = source_nodes[node['name']]
        assert node.get('extras', {}).get('source_id') == original.get('extras', {}).get('source_id')
        mesh = target['meshes'][node['mesh']]
        original_mesh = source['meshes'][original['mesh']]
        assert len(mesh['primitives']) == len(original_mesh['primitives'])
        before = after = 0
        restored = []
        for current, authored in zip(mesh['primitives'], original_mesh['primitives']):
            before += target['accessors'][current['indices']]['count'] // 3
            after += source['accessors'][authored['indices']]['count'] // 3
            assert after >= before, 'Input is not a full-fidelity baseline'
            assert 'targets' not in authored
            primitive = copy.deepcopy(authored)
            primitive['material'] = current['material']
            primitive['attributes'] = {k: copy_accessor(v) for k,v in authored['attributes'].items()}
            primitive['indices'] = copy_accessor(authored['indices'])
            extensions = primitive.get('extensions', {})
            assert set(extensions) <= {'KHR_draco_mesh_compression'}
            if 'KHR_draco_mesh_compression' in extensions:
                draco = extensions['KHR_draco_mesh_compression']
                draco['bufferView'] = copy_view(draco['bufferView'])
            restored.append(primitive)
        mesh['primitives'] = restored
        report.append({'node': node['name'], 'before': before, 'after': after})

target['buffers'][0]['byteLength'] = len(result_bin)
result_bin.extend(b'\0' * (-len(result_bin) % 4))
json_bin = json.dumps(target, ensure_ascii=False, separators=(',', ':')).encode()
json_bin += b' ' * (-len(json_bin) % 4)
output = struct.pack('<III', 0x46546c67, 2, 28+len(json_bin)+len(result_bin))
output += struct.pack('<II', len(json_bin), 0x4e4f534a) + json_bin
output += struct.pack('<II', len(result_bin), 0x004e4942) + result_bin
assert len(output) < 20_000_000
Path(sys.argv[3]).write_bytes(output)
print(json.dumps({'restored': report, 'bytes': len(output)}, ensure_ascii=False, indent=2))
