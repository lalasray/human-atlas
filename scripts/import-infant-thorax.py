"""Convert the CC BY 4.0 Tyndall newborn thorax mesh to nine web regions.

Usage: python scripts/import-infant-thorax.py [data/raw/infant-thorax]
Install requirements-infant-thorax.txt first. Input is the published nodal
tetrahedral mesh, not the original CT or a new anatomical segmentation.
"""
import gzip
import hashlib
import json
from pathlib import Path
import platform
import sys

import h5py
import numpy as np
import vtk
from vtk.util.numpy_support import numpy_to_vtk, numpy_to_vtkIdTypeArray, vtk_to_numpy

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'tyndall-newborn-thorax'
URL = 'https://zenodo.org/records/4916863'
HASH = '7de29df4092f47f702b7a27d0c6c3e147f953dcc6db8d8bc3ddda7fd4d9e77a3'
README_HASH = 'cb85dc094b37a4c60c5de2ed13ca24630cae699c935363d600d43bc65017fe50'
REGIONS = [
    ('lungs', 'Lungs (group)', 'respiratory', [1, 10, 11]),
    ('bone', 'Chest bones (group)', 'skeletal', [2]),
    ('cartilage', 'Chest cartilage (group)', 'connective', [3]),
    ('heart', 'Heart', 'cardiac', [4]),
    ('muscle', 'Chest muscles (group)', 'muscular', [5]),
    ('artery', 'Artery (source region)', 'arterial', [6]),
    ('fat', 'Chest fat', 'tissue', [7]),
    ('skin', 'Chest skin', 'integumentary', [8]),
    ('trachea', 'Trachea', 'respiratory', [9]),
]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def edge_count(poly, boundary=False, nonmanifold=False):
    check = vtk.vtkFeatureEdges()
    check.SetInputData(poly)
    check.FeatureEdgesOff()
    check.ManifoldEdgesOff()
    check.SetBoundaryEdges(boundary)
    check.SetNonManifoldEdges(nonmanifold)
    check.Update()
    return check.GetOutput().GetNumberOfCells()


def main():
    raw = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'data/raw/infant-thorax'
    record = json.loads((raw / 'record.json').read_text())
    assert record['id'] == 4916863 and record['metadata']['license']['id'] == 'cc-by-4.0'
    data = (raw / 'mesh.mat').read_bytes()
    assert digest(data) == HASH and digest((raw / 'readme.md').read_bytes()) == README_HASH
    for name in ['mesh.mat', 'readme.md']:
        source_file = next(f for f in record['files'] if f['key'] == name)
        content = (raw / name).read_bytes()
        assert len(content) == source_file['size']
        assert 'md5:' + hashlib.md5(content).hexdigest() == source_file['checksum']
    with h5py.File(raw / 'mesh.mat') as mat:
        nodes = np.asarray(mat['nodes']).T.copy()
        elements_raw = np.asarray(mat['elements']).T.copy()
        labels = np.asarray(mat['region']).ravel()
    assert nodes.shape == (229363, 3) and elements_raw.shape == (1356069, 4)
    assert np.isfinite(nodes).all() and set(np.unique(labels)) == set(range(1, 12))
    assert np.equal(elements_raw, np.floor(elements_raw)).all()
    elements = np.asarray(elements_raw - 1, dtype=np.int64)
    assert elements.min() == 0 and elements.max() == len(nodes) - 1
    # Reorientation preserves source distances and all inter-organ placement.
    # The published mesh lacks an anatomical orientation header, so laterality
    # is not inferred or used to split its grouped bone/lung/artery regions.
    center = (nodes.min(0) + nodes.max(0)) / 2
    transform = np.array([[-.001, 0, 0, center[0] * .001],
                          [0, 0, .001, .01 - nodes[:, 2].min() * .001],
                          [0, .001, 0, -center[1] * .001], [0, 0, 0, 1]])
    points = vtk.vtkPoints()
    points.SetData(numpy_to_vtk(nodes, deep=True))
    cells = vtk.vtkCellArray()
    cells.SetData(numpy_to_vtkIdTypeArray(np.arange(0, elements.size + 1, 4, dtype=np.int64), deep=True),
                  numpy_to_vtkIdTypeArray(elements.ravel(), deep=True))
    grid = vtk.vtkUnstructuredGrid()
    grid.SetPoints(points)
    grid.SetCells(vtk.VTK_TETRA, cells)
    parts, qa, blob = [], [], bytearray()

    def append(values):
        blob.extend(b'\0' * (-len(blob) % 4))
        offset = len(blob)
        blob.extend(values.tobytes())
        return offset

    for key, name, system, region_ids in REGIONS:
        selected = np.isin(labels, region_ids)
        scalars = numpy_to_vtk(selected.astype(np.float32), deep=True)
        scalars.SetName('region_membership')
        grid.GetPointData().SetScalars(scalars)
        # Interpolate the nodal indicator at 0.5 and retain clipped cell pieces.
        # Extracting their surface also retains the source volume's cut faces.
        clip = vtk.vtkClipDataSet()
        clip.SetInputData(grid)
        clip.SetValue(.5)
        surface = vtk.vtkDataSetSurfaceFilter()
        surface.SetInputConnection(clip.GetOutputPort())
        triangles = vtk.vtkTriangleFilter()
        triangles.SetInputConnection(surface.GetOutputPort())
        clean = vtk.vtkCleanPolyData()
        clean.SetInputConnection(triangles.GetOutputPort())
        clean.SetTolerance(0)
        normals = vtk.vtkPolyDataNormals()
        normals.SetInputConnection(clean.GetOutputPort())
        normals.SplittingOff()
        normals.ConsistencyOn()
        normals.AutoOrientNormalsOn()
        normals.Update()
        poly = normals.GetOutput()
        source_positions = vtk_to_numpy(poly.GetPoints().GetData())
        positions = np.asarray(source_positions @ transform[:3, :3].T + transform[:3, 3], dtype='<f4')
        normal_values = vtk_to_numpy(poly.GetPointData().GetNormals()) @ (transform[:3, :3] * 1000).T
        normal_values = np.asarray(np.clip(np.rint(normal_values * 32767), -32767, 32767), dtype='<i2')
        polygons = poly.GetPolys()
        assert np.all(np.diff(vtk_to_numpy(polygons.GetOffsetsArray())) == 3)
        indices = np.asarray(vtk_to_numpy(polygons.GetConnectivityArray()).reshape(-1, 3), dtype='<u4')
        assert len(positions) > 100 and len(indices) > 100 and np.isfinite(positions).all()
        connectivity = vtk.vtkPolyDataConnectivityFilter()
        connectivity.SetInputData(poly)
        connectivity.SetExtractionModeToAllRegions()
        connectivity.Update()
        measures = {'boundary_edges': edge_count(poly, boundary=True),
                    'nonmanifold_edges': edge_count(poly, nonmanifold=True),
                    'connected_components': connectivity.GetNumberOfExtractedRegions(),
                    'degenerate_faces': int(np.count_nonzero(np.linalg.norm(np.cross(
                        positions[indices[:, 1]] - positions[indices[:, 0]],
                        positions[indices[:, 2]] - positions[indices[:, 0]]), axis=1) < 1e-15)),
                    'self_intersections': 'not measured', 'anatomical_review': 'local conversion unreviewed'}
        identity = SOURCE + ':' + key
        provenance = {'id': identity, 'structure_id': identity, 'source': SOURCE, 'source_asset': key,
            'source_url': URL, 'source_revision': 'Zenodo 4916863 v1.0.0', 'source_chunk_sha256': HASH,
            'source_sex': 'not reported', 'reference_sex': 'not reported',
            'source_donor': 'CUH-newborn-thorax-4916863', 'geometry_type': 'surface_from_published_nodal_tetrahedral_mesh',
            'granularity': 'source tissue region; grouped structures', 'source_region_ids': region_ids,
            'source_node_count': int(selected.sum()), 'display_space': 'newborn thorax display stage, metres',
            'canonical_space': None, 'registration': {'type': 'display rotation and translation only',
                'display_transform_id': 'tyndall-thorax-mm-to-stage', 'transform_id': None,
                'canonical_registration': False, 'review_status': 'not registered to brain or adult anatomy'},
            'confidence': None, 'confidence_basis': 'not independently assessed', 'license': 'CC-BY-4.0',
            'license_url': 'https://creativecommons.org/licenses/by/4.0/',
            'qa_status': 'local surface conversion unreviewed', 'alternatives': [], 'geometry_qa': measures,
            'developmental_stage': 'newborn', 'gestational_age_at_birth_weeks': 36, 'age_at_scan': 'not reported',
            'notes': 'Published CT-derived newborn thorax. Regions are homogeneous and omit fine anatomy. '
                     'Surfaces interpolate nodal tissue membership at 0.5, including source cut faces. '
                     'Lung study regions 1, 10 and 11 are united; these are not anatomical lobes. '
                     'No smoothing, simplification, left/right inference, or registration to the dHCP brain.'}
        part = {'id': identity, 'name': name, 'conceptId': identity, 'system': system, 'chunk': 0,
                'positions': append(positions), 'normals': append(normal_values), 'indices': append(indices),
                'vertexCount': len(positions), 'indexCount': int(indices.size),
                'bounds': [positions.min(0).tolist(), positions.max(0).tolist()], 'provenance': provenance}
        parts.append(part)
        qa.append({'id': identity, 'sourceRegions': region_ids, 'sourceNodes': int(selected.sum()),
                   'vertices': len(positions), 'triangles': len(indices), **measures})
        print(name, len(indices), 'triangles;', measures['connected_components'], 'components', flush=True)
    compressed = gzip.compress(blob, mtime=0)
    geometry_hash = digest(blob)
    for part in parts:
        part['provenance']['derived_chunk_sha256'] = geometry_hash
    models = ROOT / 'public/models'
    (models / 'infant-thorax-0.bin').write_bytes(blob)
    (models / 'infant-thorax-0.bin.gz').write_bytes(compressed)
    display = {'id': 'tyndall-thorax-mm-to-stage', 'matrix': transform.tolist(), 'units': 'metres',
               'scale': 1, 'registration_to_brain': False, 'registration_to_adult': False,
               'anatomical_orientation': 'not verified; source has no orientation header'}
    atlas = {'version': 'Tyndall newborn thorax v1.0.0, web surface conversion', 'source': 'Tyndall / CUH newborn thorax',
        'region': 'thorax', 'default_visible': ['cardiac', 'respiratory', 'arterial', 'skeletal', 'connective'], 'developmental_stage': 'newborn', 'reference_age': 'Newborn; born at 36 weeks gestation',
        'gestational_age_at_birth_weeks': 36, 'age_at_scan': 'not reported', 'population_sex': 'not reported',
        'scope': 'Nine chest organ and tissue regions from one newborn CT-derived mesh. Chest only; '
                 'separate from the dHCP brain reference, with no shared donor or registration.',
        'parts': parts, 'concepts': [{'id': p['id'], 'name': p['name'], 'elements': [p['id']]} for p in parts],
        'triangles': sum(p['indexCount'] // 3 for p in parts), 'display_transform': display,
        'source_url': URL, 'doi': '10.5281/zenodo.4916863', 'license': 'CC-BY-4.0', 'input_sha256': HASH,
        'chunks': [{'url': '/models/infant-thorax-0.bin', 'bytes': len(blob), 'sha256': geometry_hash,
                    'gzip': '/models/infant-thorax-0.bin.gz', 'gzipBytes': len(compressed)}]}
    manifest = json.dumps(atlas, separators=(',', ':')).encode()
    (models / 'atlas-infant-thorax.json').write_bytes(manifest)
    evidence = ROOT / 'public/infant-sources/thorax'
    evidence.mkdir(exist_ok=True, parents=True)
    for name in ['record.json', 'readme.md']:
        (evidence / name).write_bytes((raw / name).read_bytes())
    report = {'source': URL, 'doi': atlas['doi'], 'license': atlas['license'], 'inputSha256': HASH,
        'readmeSha256': README_HASH, 'manifestSha256': digest(manifest), 'geometrySha256': geometry_hash,
        'sourceNodes': len(nodes), 'sourceTetrahedra': len(elements), 'sourceRegionCount': 11,
        'meshes': len(parts), 'concepts': len(parts), 'triangles': atlas['triangles'], 'regions': qa,
        'displayTransform': display, 'software': {'python': platform.python_version(),
            'numpy': np.__version__, 'h5py': h5py.__version__, 'vtk': vtk.vtkVersion.GetVTKVersion()},
        'method': 'Clip each nodal region indicator at 0.5; extract and triangulate clipped volume surface; '
                  'weld coincident points, compute consistent normals; no smoothing or simplification.',
        'remainingGaps': ['Head/skull, arms, hands, pelvis, legs and feet.',
            'Abdominal and pelvic organs, peripheral nerves and complete blood vessels.',
            'Individually labeled bones, muscles, lung lobes and fine organ structures.',
            'No anatomical registration between the separate infant brain and chest references.']}
    (evidence / 'coverage.json').write_text(json.dumps(report, indent=2) + '\n')
    print(f'Imported {len(parts)} newborn chest regions; {len(compressed):,} compressed bytes.')


if __name__ == '__main__':
    main()
