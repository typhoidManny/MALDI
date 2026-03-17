import numpy as np
from pathlib import Path
import os

def read_acqus(acqus_path):
    params = {}
    with open(acqus_path, 'r', encoding='latin-1') as f:
        for line in f:
            if line.startswith('##$'):
                key, _, val = line[3:].partition('= ')
                params[key.strip()] = val.strip()
    return params

def read_fid(fid_dir):
    fid_dir = Path(fid_dir)
    acqus_path = fid_dir / 'acqus'
    fid_path = fid_dir / 'fid'

    if not acqus_path.exists():
        raise FileNotFoundError(f"acqus not found in {fid_dir}")
    if not fid_path.exists():
        raise FileNotFoundError(f"fid not found in {fid_dir}")

    params = read_acqus(acqus_path)
    td = int(params['TD'])

    with open(fid_path, 'rb') as f:
        data = np.frombuffer(f.read(), dtype=np.int32)

    data = data[:td]
    real = data[0::2]
    imag = data[1::2]

    return params, real, imag

def load_all_fids(master_dir):
    master_dir = Path(master_dir)
    results = []

    for fid_dir in master_dir.rglob('1SLin'):
        if (fid_dir / 'fid').exists() and (fid_dir / 'acqus').exists():
            parts = fid_dir.relative_to(master_dir).parts

            genus      = parts[0] if len(parts) > 0 else 'unknown'
            species    = parts[1] if len(parts) > 1 else 'unknown'
            identifier = parts[2] if len(parts) > 2 else 'unknown'
            spot       = parts[3] if len(parts) > 3 else 'unknown'

            try:
                params, real, imag = read_fid(fid_dir)
                results.append({
                    'path': fid_dir,
                    'genus': genus,
                    'species': species,
                    'identifier': identifier,
                    'spot': spot,
                    'params': params,
                    'real': real,
                    'imag': imag,
                })
                print(f"  Read: {fid_dir}")
            except Exception as e:
                print(f"  Failed: {fid_dir} -> {e}")

    print(f"\nLoaded {len(results)} FIDs from {master_dir}")
    return results

# --- Main ---
while True:
    master_dir = input("Enter path to master directory: ").strip().strip('"').strip("'")
    master_dir = os.path.expanduser(master_dir)
    if os.path.isdir(master_dir):
        break
    print(f"  Directory not found: '{master_dir}'. Please try again.")

results = load_all_fids(master_dir)