"""Run MOOSE peripheral bone segmentation on the verified VHF upper-body CT.

Usage: python scripts/segment-female-bones.py /path/to/vhf-fresh-ct.nii.gz /output
Environment used: Python 3.12, moosez 3.2.2, torch 2.14.0+cpu.
The result is automatic and requires review before importing individual labels.
"""
import hashlib
import json
import os
from pathlib import Path
import sys

os.environ.setdefault('OMP_NUM_THREADS', '12')
os.environ.setdefault('nnUNet_compile', 'false')
os.environ.setdefault('MPLCONFIGDIR', '/tmp/anatomy-matplotlib')


def main():
    import nibabel as nib
    import torch
    from moosez.moosez import moose
    source, output = Path(sys.argv[1]), Path(sys.argv[2])
    expected = '5284a87267a83911f0174a07fb3f755301376eb5658daf12d95455cc2ecad26f'
    assert hashlib.sha256(source.read_bytes()).hexdigest() == expected, 'Unexpected CT volume'
    output.mkdir(parents=True, exist_ok=True)
    image = nib.load(source)
    # Head through proximal thighs, retaining the complete upper limbs present in this scan.
    cropped = image.slicer[:, :, :1100]
    target = output / 'CT_vhf_upper.nii.gz'
    nib.save(cropped, target)
    torch.set_num_threads(12)
    print('Running MOOSE peripheral bones; automatic labels, anatomy unreviewed.', flush=True)
    paths, models = moose(str(target), ['clin_ct_peripheral_bones'], str(output), 'cpu')
    report = {'inputSha256': expected, 'crop': [0, 1100], 'sourceShape': list(image.shape),
              'model': 'clin_ct_peripheral_bones', 'moosez': '3.2.2',
              'outputs': [str(p) for p in paths], 'models': [str(m) for m in models],
              'review': 'automatic; anatomical review pending'}
    (output / 'segmentation-run.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
