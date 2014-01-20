# -*- coding: utf8 -*-

from __future__ import unicode_literals
from __future__ import print_function


""" Граничные значения (и пофиг что по русски) """

from functools import reduce

def count_nodes(node, passed, finish):
    if node in passed:
        return 0
    passed.add(node)
    if node == finish:
        return 1
    return reduce(lambda s, n: s + count_nodes(n, passed, finish), node.children, 1)




def node_complexity(node):
    
    if node.name == 'while':
        # Child, which has wants_endnode == self is start of subgraph
        whilenode = None
        complexity = 0
        passed = set()
        for child in node.children:
            if child.name != 'endwhile':
                complexity += count_nodes(child, passed, node)
        return complexity
    elif len(node.children) > 1:
        endnode = None
        complexity = 1
        passed = set()
        for child in node.children:
            if child.name != 'endif' and child.wants_endnode.name == 'endif':
                assert endnode == None or endnode == child.wants_endnode, 'Bad execution graph for if/else clause'
                endnode = child.wants_endnode
                complexity += count_nodes(child, passed, endnode)
        return complexity
    elif node.name == 'finish':
        return 0
    else:
        return 1


class Boundary:
    """ Some stupid metric, using execution graph """

    def __init__(self, exec_graph):
        self.graph = exec_graph
        self.node_count = 0
        self.abs_compxt = 0


    def analyze(self):
        """ Performs analysis
            Returns bullshit """
      
        self.node_count = 0

        passed = set()
        not_passed = set()

        not_passed.add(self.graph.root_node)

        while len(not_passed) != 0:
            node = not_passed.pop()
            passed.add(node)

            self.node_count += 1
         
            self.abs_compxt += node_complexity(node)

            for child in node.children:
                if not (child in passed or child in not_passed) :
                    not_passed.add(child)

    def metric(self):
        return 1 - (self.node_count - 1)/self.abs_compxt


# vim:tabstop=4:shiftwidth=4:expandtab

