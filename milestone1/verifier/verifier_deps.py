#!/usr/bin/env python3

import pygraphviz as pgv

if __name__ == '__main__':

    G = pgv.AGraph('verifier_deps.dot')
    print(G)

    print('dependencies of plaintext_tally:')
    print(G.predecessors('plaintext_tally'))
