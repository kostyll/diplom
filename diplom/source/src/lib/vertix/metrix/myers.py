# -*- coding: utf8 -*-

from __future__ import unicode_literals
from __future__ import print_function


""" ExecGraph analyzer """

import graph, re


class Myers:

    """ Analyzes ExecGraph """


    def __init__(self, exec_graph, source_text):
        """ Initializes Myers metrics
            execGraph - graph to analyze """

        self.graph = exec_graph
        self.edge_count = 0
        self.node_count = 0
        self.text = source_text
        self.myers_offset = 0
      

    def analyze(self):
        """ Performs analysis
            Returns edgeCount and nodeCount """
      
        self.edge_count = 0
        self.node_count = 0

        passed = set()
        not_passed = set()

        not_passed.add(self.graph.root_node)

        while len(not_passed) != 0:
            node = not_passed.pop()
            passed.add(node)
         
            for child in node.children:
                self.edge_count += 1
            
                if not (child in passed or child in not_passed) :
                    not_passed.add(child)
                    self.node_count += 1
        self.node_count += 1 # correction for head node
        
        operands = re.findall(r'[^\|]\|\|[^\|]|[^&]&&[^&]', self.text, re.MULTILINE)
        self.myers_offset = len(operands)


    def metric(self):
        x = self.edge_count - self.node_count + 2
        return (x, x + self.myers_offset)



# vim:tabstop=4:shiftwidth=4:expandtab

