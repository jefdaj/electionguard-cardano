#!/usr/bin/env python

# Test code for mutating crypto values in json files

import json
import sys
from pprint import pprint

def json_edit_matching_values(root, keys_to_match, value_edit_fn):
    """For each (key,value) pair nested in the root JSON dict,
    apply value_edit_fn to the pair if the key is in the list.
    Note that value_edit_fn takes the key and value, but only returns
    a new value. The key is mainly for logging.
    """
    if isinstance(root, dict):
        for (k, v) in root.items():
            if k in keys_to_match:
                root[k] = value_edit_fn(k, v)
            json_edit_matching_values(v, keys_to_match, value_edit_fn)
    elif isinstance(root, list):
        for v in root:
            json_edit_matching_values(v, keys_to_match, value_edit_fn)

def example_edit_fn(k, v):
    print(f'example_edit_fn({k}, {v})')
    return 'EDITED'

def walk_json_file(json_path):

    count = 0
    def example_count_fn(k, v):
        print(f'incrementing count for {k}')
        nonlocal count
        count += 1

    with open(json_path, 'r') as f:
        json_dict = json.load(f)

    json_edit_matching_values(
        json_dict,
        ['challenge', 'proof_one_data'],
        example_count_fn
        # lambda k, v: 'EDITED',
    )

    pprint(json_dict)
    print(f'final count: {count}')

if __name__ == '__main__':
    infile = sys.argv[1]
    # print(f'infile: {infile}')
    walk_json_file(infile)
