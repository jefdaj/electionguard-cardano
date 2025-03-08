#!/usr/bin/env python3

import pygraphviz as pgv

if __name__ == '__main__':

    G = pgv.AGraph('verifier_deps.dot')

    # stub out verify_* fns in verifier2
    for node in G.nodes():
        print(f'def verify_{node}() -> Optional[str]:\n    return "not implemented yet"\n')

    # print('dependencies of plaintext_tally:')
    # print(G.predecessors('plaintext_tally'))
