import re


# 1 - cleanup_code, 2 - total number of strings, 3 - number of unique strings
def cleanup_and_get_strings_count(text):
    all_strings = set()
    count = len(re.findall("L?\"(\\\\.|[^\\\\\"])*\"", text))
    cleanup_code = re.sub("L?\"(\\\\.|[^\\\\\"])*\"", lambda match: (all_strings.add(match.group(0))), text)
    return cleanup_code, count, len(all_strings)

def cleanup_strings(text):
    cleanup_code = re.sub("L?\"(\\\\.|[^\\\\\"])*\"", '', text)
    return cleanup_code

def cleanup_comments(text):
    without_comments = re.sub(re.compile("/\*.*?\*/", re.DOTALL), "", text)
    without_comments = re.sub(re.compile("//.*?\n"), "", without_comments)
    return without_comments


def cleanup_sharp(text):
    text = re.compile(r"^\s*#[^\r\n]*$", re.DOTALL | re.MULTILINE).sub("", text)
    return text
