#!/usr/bin/env python3
"""Clean Foundry cached model variants, keeping only the specified base models.
Usage: python3 scripts/clean_model_cache.py --keep qwen3.5-2b qwen2.5-coder-7b
"""
from foundry_local_sdk import Configuration, FoundryLocalManager
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--keep", nargs="+", required=False, default=["qwen3.5-2b","qwen2.5-coder-7b"], help="Base model ids to keep (default: qwen3.5-2b qwen2.5-coder-7b)")
args = parser.parse_args()

Configuration(app_name='SolVS')
FoundryLocalManager.initialize(Configuration(app_name='SolVS'))
cat = FoundryLocalManager.instance.catalog
keep = set(args.keep)
variants = cat.get_cached_models()
print('Cached variants found:', len(variants))
for v in variants:
    vid = getattr(v,'id',None)
    base = vid.split(':')[0] if vid else str(v)
    if any(k in base for k in keep):
        print('Keeping', vid)
        continue
    print('Removing', vid)
    try:
        if hasattr(v, 'remove_from_cache'):
            v.remove_from_cache()
            print(' Removed', vid)
        else:
            m = cat.get_model(base)
            if m and hasattr(m,'remove_from_cache'):
                m.remove_from_cache()
                print(' Removed via model', base)
            else:
                print(' No remove_from_cache() for', vid)
    except Exception as e:
        print(' Failed to remove', vid, e)
print('Done')
