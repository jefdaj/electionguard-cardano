#!/usr/bin/env python3

import pygraphviz as pgv

if __name__ == '__main__':

    G = pgv.AGraph('scripts/verifier_deps.dot')

    # stub out verify_* fns in verifier2
    for node in G.nodes():
        # print('@cache')
        print(f'def verify_{node}(results, pubdir):') # TODO return type?
        for dep_name in G.predecessors(node):
            print(f"    {dep_name} = verify(results, pubdir, '{dep_name}')")
        print('    raise NotImplementedError')
        print()

    # print('dependencies of plaintext_tally:')
    # print(G.predecessors('plaintext_tally'))
