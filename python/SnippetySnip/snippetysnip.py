import re

SNIPPET_BEGIN = "snippetysnip_begin" 
SNIPPET_END = "snippetysnip_end"
LEGAL_SNIPPET_CHARS = r"0-9a-zA-Z\-_\."

def get_snippet(file_name, snippet_name):
    try:
        assert_legal_snippet_name(snippet_name)
    except ValueError as e:
        return e.message
    snippet = ""

    in_snippet = False
    found_tag = False
    try:
        file = open(file_name, 'r')
    except IOError as e:
        return "ERROR: Couldn't open file: %s\n" % e
    for line in file:
        if matches_snippet_begin(line, snippet_name):
            in_snippet = True
            found_tag = True
            continue
        if SNIPPET_END in line:
            in_snippet = False
        if in_snippet:
            snippet += line

    if not found_tag:
        return "ERROR: Didn't find %s\n" % snippet_begin(snippet_name)
    if in_snippet:
        return "ERROR: Didn't find snippetysnip_end after %s\n" % snippet_begin(snippet_name)
    return snippet

def snippet_begin(snippet_name):
    return "%s:%s" % (SNIPPET_BEGIN, snippet_name)

def assert_legal_snippet_name(snippet_name):
    for char in snippet_name:
        if not re.match("[%s]+" % LEGAL_SNIPPET_CHARS, char):
            raise ValueError("'%s' is not a legal character for a snippet name! Legal characters are'%s'." % (char, LEGAL_SNIPPET_CHARS))

def matches_snippet_begin(line, snippet_name):
    begin_re = "^.*%s[^%s]*$" % (snippet_begin(snippet_name), LEGAL_SNIPPET_CHARS)
    return re.match(begin_re, line) is not None


def find_end_line(lines, file_name, snippet_name):
    snippet_end = "%s:%s:%s" % (SNIPPET_END, file_name, snippet_name)
    for line_no in range(0, len(lines)):
        if snippet_end in lines[line_no]:
            return line_no
    return -1

snippetstring_with_args = '(.*snippetysnip:[^:]*:[^:]*)(:\(.*\))(.*)'

def get_arguments(string):
    arguments_string = re.search(snippetstring_with_args, string)
    extracted_arguments = {}
    if arguments_string:
        args = arguments_string.group(2)
        for arg in ('before', 'after'):
            for quote in ('"', "'"):
                arg_match = re.search(arg+' *= *%s([^%s]*)%s' % (quote, quote, quote), args)
                if arg_match:
                    extracted_arguments[arg] = arg_match.group(1)
    return extracted_arguments

def remove_arguments(string):
    match = re.search(snippetstring_with_args, string)
    if match:
        return match.group(1) + match.group(3)
    else:
        return string

def insert_snippets(old_buffer, snippet_getter=get_snippet):
    snippet_begin = "snippetysnip:([^:]*):([^:]*)[\s:]" 
    new_buffer = []
    line_no = 0
    while line_no < len(old_buffer):
        line = old_buffer[line_no]
        new_buffer.append(line)
        match = re.search(snippet_begin, line)
        if match:
            new_buffer.append('')
            arguments = get_arguments(line)
            file_name, snippet_name = match.groups()
            if arguments.has_key('before'):
                new_buffer.append(arguments['before'])
            new_buffer.extend(snippet_getter(file_name, snippet_name).split("\n")[:-1])
            if arguments.has_key('after'):
                new_buffer.append(arguments['after'])
            new_buffer.append('')
            new_buffer.append(remove_arguments(line).replace("snippetysnip", "snippetysnip_end"))
            end_line = find_end_line(old_buffer[line_no:], file_name, snippet_name)
            if end_line != -1:
                line_no += end_line 
        line_no += 1
    return new_buffer

def line_is_snippet_end(line):
    return re.search(SNIPPET_END, line)

def get_snippet_name_if_line_is_snippet_begin(line):
    match = re.search("%s:(.*)" % SNIPPET_BEGIN, line)
    if match:
        return match.group(1)
    return False

def get_current_snippet_name(buf, current_line):
    for line in range(current_line, 0, -1):
        if line_is_snippet_end(buf[line]):
            raise ValueError('Not in a snippet')
        snippet_name = get_snippet_name_if_line_is_snippet_begin(buf[line])
        if snippet_name:
            return snippet_name
    raise ValueError('Not in a snippet')
