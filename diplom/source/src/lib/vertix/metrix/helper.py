
""" Helper functions """

import re


def find_adjacent_bracket(text, open_close_brackets):
    """ Finds the last dangling closing bracket in text """

    brackets = 0

    for i in range(0, len(text)):
        if text[i] == open_close_brackets[0]:
            brackets += 1
        elif text[i] == open_close_brackets[1]:
            brackets -= 1

        if brackets == 0:
            return i+1
        elif brackets < 0:
            break

    raise SyntaxError('Syntax error: unmatched bracket in ' + text)


def parse_operand(text):
    """ returns operand name, args with brackets,
        body with brackets and index of body end """
    
    first_bracket = text.find('(')
    operand_name = text[:first_bracket]
    
    last_bracket = first_bracket + \
            find_adjacent_bracket(text[first_bracket:], '()')
    args = text[first_bracket:last_bracket]
    
    first_curly_bracket = last_bracket + text[last_bracket:].find('{')

    if len(text[last_bracket+1:first_curly_bracket].strip()) != 0:
        first_curly_bracket = last_bracket
        last_curly_bracket = last_bracket + text[last_bracket:].find(';') + 1
    else:
        last_curly_bracket = first_curly_bracket + \
                find_adjacent_bracket(text[first_curly_bracket:], '{}')
    
    body = text[first_curly_bracket:last_curly_bracket]

    return (operand_name, args, body,
            {
                'args_start': first_bracket,
                'args_end': last_bracket,
                'body_start': first_curly_bracket,
                'body_end': last_curly_bracket,
                'end': last_curly_bracket + 1,
            })


def extract_args(text):
    old = ""
    new_text = text
    while old != new_text:
        old = new_text
        new_text = __extract_args(new_text)
    return new_text
    


def __extract_args(text):
    """ Extracts all arguments from operators and function calls """
    
    text = text.replace('else if', 'elseif')

    operand_finder = re.compile(r'^(.+[\s;}])?(if|elseif|while|switch|for)\s*\(', re.MULTILINE)
    funct_finder = re.compile(r'^(.*?[\s;}\(\){])?([a-zA-Z_][0-9a-zA-Z_]*)\s*\(', re.MULTILINE)
    
    while True:
        operator = operand_finder.search(text)
        if operator == None:
            break;

        start = operator.start(2)
        (operand_name, args, body, indices) = parse_operand(text[start:])
        if len(args) != 0:
            # Add curly brackets
            #print(operand_name,args,body)
            if body.strip()[0] != '{':
                body = '{\n' + body.split(';')[0] + '\n}'
            # Move args
            text = text[:start] + '\n' + args + ';\n' + text[start:start+indices['args_start']] + body + text[start+indices['body_end']:]
   
    operand_name = ''
    last_pos = 0
    while True:
        operator = funct_finder.search(text, last_pos)
        if operator == None:
            break;
        
        start = operator.start(2)
        last_pos = operator.end(2)
        (operand_name, args, body, indices) = parse_operand(text[start:])
        if operand_name in ['if', 'while', 'elseif', 'for', 'switch', 'return']: 
            continue
        if len(body.strip()) != 0 and body.strip() != ';':
            # This seems to be a declaration. Not what we are looking for
            continue
        if len(args) != 0:
            # Move args
            if args[-1] == ')':
                args = args[:-1]
            if args[0] == '(':
                args = args[1:]
            text = text[:start] + '\n' + args + ';\n' + text[start:start+indices['args_start']] + text[start+indices['args_end']:]
    
    # Fix else's without brackets
    else_finder = re.compile(r'^(.+[\s;}])?(else)\s+[^{;]*;', re.MULTILINE)

    
    while True:
        operator = else_finder.search(text)
        if operator == None:
            break;
        
        text = text[:operator.end(2)] + ' {\n' + text[operator.end(2):operator.end(0)] + '\n}' + text[operator.end(0):]

    return text
    



# vim:tabstop=4:shiftwidth=4:expandtab

