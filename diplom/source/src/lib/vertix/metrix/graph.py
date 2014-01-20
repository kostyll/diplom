
""" C application static execution graph builder """

import re, helper, functioner


class ExecNode:
    """ An execution node """

    def __init__(self, name, wants_endnode):
        """ Creates ExecNode """

        self.name = name
        self.parents = []
        self.children = []
        self.endnode = None
        self.wants_endnode = wants_endnode


def find_first(text, vals, startindex):
    min_index = -1
    value = None
    for val in vals:
        found = text.find(val, startindex)
        if found >= 0 and (found <= min_index or min_index < 0):
            min_index = found
            value = val
    return (min_index, value)


class ExecGraph:
    """ Build execution graph of application code.
        Code needs to be without function calls.
        Resulting graph can be iterated through execNodes field """
    
    def __init__(self, function_code):
        """ function_code - prepared and cleaned source code to parse """
        
        self.code = function_code
        self.build_graph()
        self.finish_node = None
        self.root_node = None
   

    def build_graph(self):
        """ Rebuilds execution graph """
       
        self.filtered_text = helper.extract_args(self.code)
        self.predicates = 0
        self.filtered_text = functioner.propagate_functions(self.filtered_text)
        self.finish_node = ExecNode('finish', None)
        self.root_node = ExecNode('root', self.finish_node)
        self._build_node(self.filtered_text, self.root_node)

    def print_tree(self):
        self._print(self.root_node, 0)

    def _print(self, node, level):
        if node == None:
            return
        print('*' * level, node.name, ': [')
        if node.name != 'while':
           for c in node.children:
              self._print(c, level+1)
        print('*' * level, ']')
    
    
    def _build_node(self, text, node):
        """ Creates nodes recursively """

        oldnode = None

        index = 0
        
        while True:
            (found, operator) = find_first(text, ['if', 'else', 'elseif', 'while', 'for'], index)
            if found < 0:
                break
            index = found

            if operator == 'if':
                endnode = ExecNode('endif', node.wants_endnode)
                endnode.parents.append(node)
                node.children.append(endnode)
                node.endnode = endnode

                new_node = ExecNode('if', endnode)
                new_node.parents.append(node)
                node.children.append(new_node)
                
                oldnode = node
                node = endnode
                
                block_start = text.find('{', index)
                block_end = block_start + helper.find_adjacent_bracket(text[block_start:], '{}')

                self._build_node(text[block_start:block_end], new_node)

            elif operator == 'else':
                node.parents.pop(node.parents.index(oldnode))
                oldnode.children.pop(oldnode.children.index(node))
                
                elsenode = ExecNode('else', node)

                elsenode.parents.append(oldnode)
                oldnode.children.append(elsenode)

                block_start = text.find('{', index)
                block_end = block_start + helper.find_adjacent_bracket(text[block_start:], '{}')

                self._build_node(text[block_start:block_end], elsenode)
            
            elif operator == 'elseif':
                new_node = ExecNode('elseif', node)
                new_node.parents.append(oldnode)
                oldnode.children.append(new_node)
                
                block_start = text.find('{', index)
                block_end = block_start + helper.find_adjacent_bracket(text[block_start:], '{}')

                self._build_node(text[block_start:block_end], new_node)

            elif operator == 'while' or operator == 'for':
                endnode = ExecNode('endwhile', node.wants_endnode)
                new_node = ExecNode('while', None)
                new_node.wants_endnode = new_node

                endnode.parents.append(new_node)
                new_node.children.append(endnode)
                node.endnode = endnode
                
                node.children.append(new_node)
                new_node.parents.append(new_node)

                node = endnode

                block_start = text.find('{', index)
                block_end = block_start + helper.find_adjacent_bracket(text[block_start:], '{}')

                self._build_node(text[block_start:block_end], new_node)

            index = block_end

        node.endnode = node.wants_endnode
        node.endnode.parents.append(node)
        node.children.append(node.endnode)


# vim:tabstop=4:shiftwidth=4:expandtab

