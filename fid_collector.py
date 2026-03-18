import os
import shutil
from pathlib import Path

def collect_fids(master_dir, output_dir):
    master_dir = Path(master_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    found = 0
    skipped = 0

    for fid_dir in master_dir.rglob('1SLin'):
        if not (fid_dir / 'fid').exists():
            print(f"Skipping {fid_dir} (missing 'fid' file)")
            skipped += 1
            continue

        parts = fid_dir.relative_to(master_dir).parts
        genus = parts[0] if len(parts) > 0 else 'unknown_genus'
        species = parts[1] if len(parts) > 1 else 'unknown_species'
        identifier = parts[2] if len(parts) > 2 else 'unknown_id'
        spot = parts[3] if len(parts) > 3 else 'unknown_spot'

        folder_name = f"{genus}_{species}_{identifier}_{spot}"

        dest = output_dir / folder_name

        if dest.exists():
            counter = 1
            while dest.exists():
                dest = output_dir / f"{folder_name}_{counter}"
                counter += 1
            
        shutil.copytree(fid_dir, dest)
        print(f"Copied {fid_dir} to {dest}")
        found += 1
    
    print(f"Finished. Found: {found}, Skipped: {skipped}")
    if skipped:
        print(f"Skipped {skipped} directories due to missing 'fid' file.")

while True:
    master_dir = input("Enter the path to the master directory: ").strip().strip('"').strip("'")
    master_dir = os.path.expanduser(master_dir)
    if os.path.isdir(master_dir):
        break
    print(f"  Directory not found: '{master_dir}'. Please try again.")

while True:
    output_dir = input("Enter path to output directory: ").strip().strip('"').strip("'")
    output_dir = os.path.expanduser(output_dir)
    if output_dir:
        break
    print("  Please enter a valid output path.")

collect_fids(master_dir, output_dir)
