import re, helper


def get_function_declaration(text):
    # regex group1, name group2, arguments group3
    rproc = r"((?<=[\s:~])(\w+)\s*\(([\w\s,<>\[\].=&':/*]*?)\)\s*(const)?\s*(?={))"
    cppwords = ['if', 'while', 'do', 'for', 'switch']
    functions = [(i.group(1), i.group(2), i.group(3)) for i in re.finditer(rproc, text) if i.group(2) not in cppwords]

    return functions


def find_function_body(text, function):
    position = 0
    while position < len(text):
        position = text.find(function[0], position)
        if position != -1:

            #get first open bracket
            while (not text[position] in ['{', '}', ';']) and position != len(text):
                position += 1
            if text[position] == "{":
                start = position
                end = start + helper.find_adjacent_bracket(text[position:], "{}")
                return text[start:end]
            else:
                continue
    
    raise SyntaxError("Incorrect bracket positions for function {0} in \n----------\n...{1}\n----------\n".format(function, text[position-50:]))



def propagate_functions(text):
    functs = get_function_declaration(text)
    main_f = None

    for f in functs:
        if f[1] == 'main':
            main_f = f
            break

    if main_f == None:
        raise SyntaxError('No entry point present')

    main_body = find_function_body(text, main_f)
    
    counter = 1
    limitter = 0
    while counter != 0:
        counter = 0
        for f in functs:
            if f[1] == 'main':
                continue
            counter += main_body.count(f[1])
            main_body = main_body.replace(f[1], find_function_body(text, f))
        limitter += 1
        if limitter > 400:
            raise SyntaxError('Too complex code')

    return main_body


# vim:tabstop=4:shiftwidth=4:expandtab

