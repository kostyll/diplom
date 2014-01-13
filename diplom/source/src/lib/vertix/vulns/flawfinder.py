#!/usr/bin/env python

#SOURCE PROJECT : http://www.dwheeler.com/flawfinder/
#SOURCES : http://www.dwheeler.com/flawfinder/flawfinder

"""flawfinder: Find potential security flaws ("hits") in source code.
 Usage:
   flawfinder [options] [source_code_file]+

 See the man page for a description of the options."""

version="1.27"

# The default output is as follows:
# filename:line_number [risk_level] (type) function_name: message
#   where "risk_level" goes from 0 to 5. 0=no risk, 5=maximum risk.
# The final output is sorted by risk level, most risky first.
# Optionally ":column_number" can be added after the line number.
#
# Currently this program can only analyze C/C++ code.
#
# Copyright (C) 2001-2007 David A. Wheeler
# This is released under the General Public License (GPL):
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from utils.stubs import open as fake_open , insert_file_into_FS

import sys, re, string, getopt
import pickle               # To support load/save/diff of hitlist
import os, glob, operator   # To support filename expansion on Windows
import os.path
import time
# import formatter

# Program Options - these are the default values:
show_context = 0
minimum_level = 1
show_immediately = 0
show_inputs = 0          # Only show inputs?
falsepositive = 0        # Work to remove false positives?
allowlink = 0            # Allow symbolic links?
skipdotdir = 1           # If 1, don't recurse into dirs beginning with "."
                         # Note: This doesn't affect the command line.
num_links_skipped = 0    # Number of links skipped.
num_dotdirs_skipped = 0  # Number of dotdirs skipped.
show_columns = 0
never_ignore = 0         # If true, NEVER ignore problems, even if directed.
list_rules = 0           # If true, list the rules (helpful for debugging)
patch_file = ""          # File containing (unified) diff output.
loadhitlist = None
savehitlist = None
diffhitlist = None
quiet = 0
showheading = 1          # --dataonly turns this off
output_format = 0        # 0 = normal, 1 = html.
single_line = 0          # 1 = singleline (can 't be 0 if html)
omit_time = 0            # 1 = omit time-to-run (needed for testing)

displayed_header = 0    # Have we displayed the header yet?
num_ignored_hits = 0    # Number of ignored hits (used if never_ignore==0)

def error(message):
  sys.stderr.write("Error: %s\n"% message)


# Support routines: find a pattern.
# To simplify the calling convention, several global variables are used
# and these support routines are defined, in an attempt to make the
# actual calls simpler and clearer.
#

filename = ""      # Source filename.
linenumber = 0     # Linenumber from original file.
ignoreline = -1    # Line number to ignore.
sumlines = 0       # Number of lines (total) examined.
sloc = 0           # Physical SLOC
starttime = time.time()  # Used to determine analyzed lines/second.


line_beginning = re.compile( r'(?m)^' )
blank_line     = re.compile( r'(?m)^\s+$' )


# The following code accepts unified diff format from both subversion (svn)
# and GNU diff, which aren't well-documented.  It gets filenames from
# "Index:" if exists, else from the "+++ FILENAME ..." entry.
# Note that this is different than some tools (which will use "+++" in
# preference to "Index:"), but subversion's nonstandard format is easier
# to handle this way.
# Since they aren't well-documented, here's some info on the diff formats:
# GNU diff format:
#    --- OLDFILENAME OLDTIMESTAMP
#    +++ NEWFILENAME NEWTIMESTAMP
#    @@ -OLDSTART,OLDLENGTH +NEWSTART,NEWLENGTH @@
#    ... Changes where preceeding "+" is add, "-" is remove, " " is unchanged.
#
#    ",OLDLENGTH" and ",NEWLENGTH" are optional  (they default to 1).
#    GNU unified diff format doesn't normally output "Index:"; you use
#    the "+++/---" to find them (presuming the diff user hasn't used --label
#    to mess it up).
#
# Subversion format:
#    Index: FILENAME
#    --- OLDFILENAME (comment)
#    +++ NEWFILENAME (comment)
#    @@ -OLDSTART,OLDLENGTH +NEWSTART,NEWLENGTH @@
#
#    In subversion, the "Index:" always occurs, and note that paren'ed
#    comments are in the oldfilename/newfilename, NOT timestamps like
#    everyone else.
#
# Single Unix Spec version 3 (http://www.unix.org/single_unix_specification/)
# does not specify unified format at all; it only defines the older
# (obsolete) context diff format.  That format DOES use "Index:", but
# only when the filename isn't specified otherwise.
# We're only supporting unified format directly; if you have an older diff
# format, use "patch" to apply it, and then use "diff -u" to create a
# unified format.
# 

diff_index_filename = re.compile( r'^Index:\s+(?P<filename>.*)' )
diff_newfile = re.compile( r'^\+\+\+\s(?P<filename>.*)$' )
diff_hunk = re.compile( r'^@@ -\d+(,\d+)?\s+\+(?P<linenumber>\d+)[, ].*@@$' )
diff_line_added = re.compile( r'^\+[^+].*' )
diff_line_del = re.compile( r'^-[^-].*' )
# The "+++" newfile entries have the filename, followed by a timestamp
# or " (comment)" postpended.
# Timestamps can be of these forms:
#   2005-04-24 14:21:39.000000000 -0400
#   Mon Mar 10 15:13:12 1997
# Also, "newfile" can have " (comment)" postpended.  Find and eliminate this.
# Note that the expression below is Y10K (and Y100K) ready. :-).
diff_findjunk = re.compile( r'^(?P<filename>.*)((\s\d\d\d\d+-\d\d-\d\d\s+\d\d:\d[0-9:.]+Z?(\s+[\-\+0-9A-Z]+)?)|(\s[A-Za-z][a-z]+\s[A-za-z][a-z]+\s\d+\s\d+:\d[0-9:.]+Z?(\s[\-\+0-9]*)?\s\d\d\d\d+)|(\s\(.*\)))\s*$')

def is_svn_diff(sLine):
  if (sLine.find('Index:') != -1):
    return True
  return False

def svn_diff_get_filename(sLine):
  return diff_index_filename.match(sLine)

def gnu_diff_get_filename(sLine):
  newfile_match = diff_newfile.match(sLine)
  if (newfile_match):
    patched_filename = string.strip(newfile_match.group('filename'))
    # Clean up filename - remove trailing timestamp and/or (comment).
    return diff_findjunk.match(patched_filename)

  return None


# For each file found in the file patch_file, keep the
# line numbers of the new file (after patch is applied) which are added.
# We keep this information in a hash table for a quick access later.
#
def load_patch_info(patch_file):
  patch={}
  line_counter= 0
  initial_number= 0
  index_statement = False # Set true if we see "Index:".
  try: hPatch = open(patch_file, 'r')
  except:
    print "Error: failed to open", h(patch_file)
    sys.exit(1)

  patched_filename = "" # Name of new file patched by current hunk.

  sLine = hPatch.readline()
  #Heuristic to determine if it's a svn diff or a GNU diff.
  #Read the first line. If it contains 'Index:', it's a svn diff else it is a
  #GNU diff.
  #By default we try to get filename in svn diff
  fn_get_filename=svn_diff_get_filename
  if (is_svn_diff(sLine) == False):
    fn_get_filename=gnu_diff_get_filename

  while True: # Loop-and-half construct.  Read a line, end loop when no more

    # This is really a sequence of if ... elsif ... elsif..., but
    # because Python forbids '=' in conditions, we do it this way.
    filename_match = fn_get_filename(sLine)
    if (filename_match):
      patched_filename = string.strip(filename_match.group('filename'))
      if (patch.has_key(patched_filename) == True):
        error("filename occurs more than once in the patch: %s" %
               patched_filename)
        sys.exit(1)
      else:
        patch[patched_filename] = {}
    else:
      hunk_match = diff_hunk.match(sLine)
      if (hunk_match):
        if (patched_filename == ""):
            error("wrong type of patch file : we have a line number without having seen a filename")
            sys.exit(1)
        initial_number= hunk_match.group('linenumber')
        line_counter= 0
      else:
        line_added_match = diff_line_added.match(sLine)
        if (line_added_match):
          line_added = line_counter + int(initial_number)
          patch[patched_filename][line_added] = True
          # Let's also warn about the lines above and below this one,
          # so that errors that "leak" into adjacent lines are caught.
          # Besides, if you're creating a patch, you had to at least look
          # at adjacent lines, so you're in a position to fix them.
          patch[patched_filename][line_added - 1] = True
          patch[patched_filename][line_added + 1] = True
          line_counter += 1
        else:
          line_del_match = diff_line_del.match(sLine)
          if (line_del_match == None):
            line_counter += 1

    sLine = hPatch.readline()
    if (sLine == ''): break  # Done reading.

  return patch


def htmlize(s):
  # Take s, and return legal (UTF-8) HTML.
  s1 = string.replace(s,"&","&amp;")
  s2 = string.replace(s1,"<","&lt;")
  s3 = string.replace(s2,">","&gt;")
  return s3

def h(s):
  # htmlize s if we're generating html, otherwise just return s.
  if output_format: return htmlize(s)
  else:             return s

def print_multi_line(text):
  # Print text as multiple indented lines.
  width = 72
  prefix = " "
  starting_position = len(prefix) + 1
  printed_something = 0  # Have we printed on this line?
  position = starting_position
  nextword = ""

  print prefix,
  for c in text:
    if (c == " "):
      print nextword,
      position = position + 1 # account for space we just printed.
      printed_something = 1
      nextword = ""
    else: # NonSpace.
      nextword = nextword + c
      position = position + 1
      if position > width: # Whups, out of space
        if (printed_something):  # We've printed something out.
          print # Done with this line, move to next.
          print prefix,
          position = starting_position
  print nextword, # Print remainder (can be overlong if no spaces)


class Hit:
  """
  Each instance of Hit is a warning of some kind in a source code file.
  See the rulesets, which define the conditions for triggering a hit.
  Hit is initialized with a tuple containing the following:
    hook: function to call when function name found.
    level: (default) warning level, 0-5. 0=no problem, 5=very risky.
    warning: warning (text saying what's the problem)
    suggestion: suggestion (text suggesting what to do instead)
    category: One of "buffer" (buffer overflow), "race" (race condition),
              "tmpfile" (temporary file creation), "format" (format string).
              Use "" if you don't have a better category.
    url: URL fragment reference.
    other:  A dictionary with other settings.

  Other settings usually set:

    name: function name
    parameter: the function parameters (0th parameter null)
    input: set to 1 if the function inputs from external sources.
    start: start position (index) of the function name (in text)
    end:  end position of the function name (in text)
    filename: name of file
    line: line number in file
    column: column in line in file
    context_text: text surrounding hit"""

  # Set default values:
  source_position = 2 # By default, the second parameter is the source.
  format_position = 1 # By default, the first parameter is the format.
  input = 0           # By default, this doesn't read input.
  note = ""          # No additional notes.
  filename = ""      # Empty string is filename.
  extract_lookahead = 0 # Normally don't extract lookahead.

  def __init__(self, data):
    hook, level, warning, suggestion, category, url, other = data
    self.hook, self.level = hook, level
    self.warning, self.suggestion = warning, suggestion
    self.category, self.url = category, url
    # These will be set later, but I set them here so that
    # analysis tools like PyChecker will know about them.
    self.column = 0
    self.line = 0
    self.name = ""
    self.context_text = ""
    for key in other.keys():
      setattr(self, key, other[key])

  def __cmp__(self, other):
    return (cmp(other.level, self.level) or  # Highest risk first.
            cmp(self.filename, other.filename) or
            cmp(self.line, other.line) or
            cmp(self.column, other.column) or
            cmp(self.name, other.name))

  def __getitem__(self, X):   # Define this so this works: "%(line)" % hit
    return getattr(self, X)

  def show(self):
    if output_format: print "<li>",
    sys.stdout.write(h(self.filename))

    if show_columns: print ":%(line)s:%(column)s:" % self,
    else:            print ":%(line)s:" % self,

    if output_format: print "<b>",
    # Extra space before risk level in text, makes it easier to find:
    print " [%(level)s]" % self,
    if output_format: print "</b>",
    print "(%(category)s)" % self,
    if output_format: print "<i>",
    print h("%(name)s:" % self),
    if single_line:
      print h("%(warning)s." % self),
      if self.suggestion: print h(self.suggestion)+".",
      print h(self.note),
    else:
      main_text = h("%(warning)s. " % self)
      if self.suggestion: main_text = main_text + h(self.suggestion) + ". "
      main_text = main_text + h(self.note)
      print
      print_multi_line(main_text)
    if output_format: print "</i>",
    print
    if show_context:
      if output_format: print "<pre>"
      print h(self.context_text)
      if output_format: print "</pre>"



# The "hitlist" is the list of all hits (warnings) found so far.
# Use add_warning to add to it.

hitlist = []

def add_warning(hit):
  global hitlist, num_ignored_hits
  if show_inputs and not hit.input: return
  if hit.level >= minimum_level:
    if linenumber == ignoreline:
      num_ignored_hits = num_ignored_hits + 1
    else:
      hitlist.append(hit)
      if show_immediately:
        hit.show()

def internal_warn(message):
  print h(message)

# C Language Specific

def extract_c_parameters(text, pos=0):
  "Return a list of the given C function's parameters, starting at text[pos]"
  # '(a,b)' produces ['', 'a', 'b']
  i = pos
  # Skip whitespace and find the "("; if there isn't one, return []:
  while i < len(text):
    if text[i] == '(':                 break
    elif text[i] in string.whitespace: i = i + 1
    else:                              return []
  else:  # Never found a reasonable ending.
    return []
  i = i + 1
  parameters = [""]  # Insert 0th entry, so 1st parameter is parameter[1].
  currentstart = i
  parenlevel = 1
  instring = 0  # 1=in double-quote, 2=in single-quote
  incomment = 0
  while i < len(text):
    c = text[i]
    if instring:
      if c == '"' and instring == 1: instring = 0
      elif c == "'" and instring == 2: instring = 0
      # if \, skip next character too.  The C/C++ rules for
      # \ are actually more complex, supporting \ooo octal and
      # \xhh hexadecimal (which can be shortened), but we don't need to
      # parse that deeply, we just need to know we'll stay in string mode:
      elif c == '\\': i = i + 1
    elif incomment:
      if c == '*' and text[i:i+2]=='*/':
        incomment = 0
        i = i + 1
    else:
      if c == '"': instring = 1
      elif c == "'": instring = 2
      elif c == '/' and text[i:i+2]=='/*':
         incomment = 1
         i = i + 1
      elif c == '/' and text[i:i+2]=='//':
         while i < len(text) and text[i] != "\n":
           i = i + 1
      elif c == '\\' and text[i:i+2]=='\\"': i = i + 1 # Handle exposed '\"'
      elif c == '(': parenlevel = parenlevel + 1
      elif c == ',' and (parenlevel == 1):
        parameters.append(string.strip(
                    p_trailingbackslashes.sub('', text[currentstart:i])))
        currentstart = i + 1
      elif c == ')':
        parenlevel = parenlevel - 1
        if parenlevel <= 0:
            parameters.append(string.strip(
                    p_trailingbackslashes.sub('', text[currentstart:i])))
            # Re-enable these for debugging:
            # print " EXTRACT_C_PARAMETERS: ", text[pos:pos+80]
            # print " RESULTS: ", parameters
            return parameters
      elif c == ';':
          internal_warn("Parsing failed to find end of parameter list; "
                        "semicolon terminated it in %s" % text[pos:pos+200])
          return parameters
    i = i + 1
  internal_warn("Parsing failed to find end of parameter list in %s" %
                text[pos:pos+200])


# These patterns match gettext() and _() for internationalization.
# This is compiled here, to avoid constant recomputation.
# FIXME: assumes simple function call if it ends with ")",
# so will get confused by patterns like  gettext("hi") + function("bye")
# In practice, this doesn't seem to be a problem; gettext() is usually
# wrapped around the entire parameter.
# The ?s makes it posible to match multi-line strings.
gettext_pattern = re.compile(r'(?s)^\s*' + 'gettext' + r'\s*\((.*)\)\s*$')
undersc_pattern = re.compile(r'(?s)^\s*' + '_(T(EXT)?)?' + r'\s*\((.*)\)\s*$')

def strip_i18n(text):
  "Strip any internationalization function calls surrounding 'text', "
  "such as gettext() and _()."
  match = gettext_pattern.search(text)
  if match: return string.strip(match.group(1))
  match = undersc_pattern.search(text)
  if match: return string.strip(match.group(3))
  return text

p_trailingbackslashes = re.compile( r'(\s|\\(\n|\r))*$')

p_c_singleton_string = re.compile( r'^\s*"([^\\]|\\[^0-6]|\\[0-6]+)?"\s*$')

def c_singleton_string(text):
  "Returns true if text is a C string with 0 or 1 character."
  if p_c_singleton_string.search(text): return 1
  else: return 0

# This string defines a C constant.
p_c_constant_string = re.compile( r'^\s*"([^\\]|\\[^0-6]|\\[0-6]+)*"$')

def c_constant_string(text):
  "Returns true if text is a constant C string."
  if p_c_constant_string.search(text): return 1
  else: return 0


# Precompile patterns for speed.


def c_buffer(hit):
  source_position = hit.source_position
  if source_position <= len(hit.parameters)-1:
    source=hit.parameters[source_position]
    if c_singleton_string(source):
      hit.level = 1
      hit.note = "Risk is low because the source is a constant character."
    elif c_constant_string(strip_i18n(source)):
      hit.level = max( hit.level - 2, 1)
      hit.note = "Risk is low because the source is a constant string."
  add_warning(hit)


p_dangerous_strncat = re.compile(r'^\s*sizeof\s*(\(\s*)?[A-Za-z_$0-9]+'  +
                                    r'\s*(\)\s*)?(-\s*1\s*)?$')
# This is a heuristic: constants in C are usually given in all upper case letters.
# Yes, this need not be true, but it's true often enough that it's worth
# using as a heuristic.  strncat better not be passed a constant as the length!
p_looks_like_constant = re.compile(r'^\s*[A-Z][A-Z_$0-9]+\s*(-\s*1\s*)?$')

def c_strncat(hit):
  if len(hit.parameters) > 3:
    # A common mistake is to think that when calling strncat(dest,src,len), that
    # "len" means the ENTIRE length of the destination.  This isn't true, it must
    # be the length of the characters TO BE ADDED at most.  Which is one reason that
    # strlcat is better than strncat.  We'll detect a common case of this error;
    # if the length parameter is of the form "sizeof(dest)", we have this error.
    # Actually, sizeof(dest) is okay if the dest's first character is always \0,
    # but in that case the programmer should use strncpy, NOT strncat.
    # The following heuristic will certainly miss some dangerous cases, but
    # it at least catches the most obvious situation.
    # This particular heuristic is overzealous; it detects ANY sizeof, instead of
    # only the sizeof(dest)  (where dest is given in hit.parameters[1]).
    # However, there aren't many other likely candidates for sizeof; some people
    # use it to capture just the length of the source, but this is just as dangerous,
    # since then it absolutely does NOT take care of the destination maximum length
    # in general.  It also detects if a constant is given as a length, if the
    # constant follows common C naming rules.
    length_text=hit.parameters[3]
    if p_dangerous_strncat.search(length_text) or p_looks_like_constant.search(length_text):
      hit.level = 5
      hit.note = ( "Risk is high; the length parameter appears to be a constant, " +
                 "instead of computing the number of characters left.")
      add_warning(hit)
      return
  c_buffer(hit)

def c_printf(hit):
  format_position = hit.format_position
  if format_position <= len(hit.parameters)-1:
    # Assume that translators are trusted to not insert "evil" formats:
    source = strip_i18n(hit.parameters[format_position])
    if c_constant_string(source):
      # Parameter is constant, so there's no risk of format string problems.
      if hit.name == "snprintf" or hit.name == "vsnprintf":
        hit.level = 1
        hit.warning = \
          "On some very old systems, snprintf is incorrectly implemented " \
          "and permits buffer overflows; there are also incompatible " \
          "standard definitions of it"
        hit.suggestion = "Check it during installation, or use something else"
        hit.category = "port"
      else:
        # We'll pass it on, just in case it's needed, but at level 0 risk.
        hit.level = 0
        hit.note = "Constant format string, so not considered very risky (there's some residual risk, especially in a loop)."
  add_warning(hit)


p_dangerous_sprintf_format = re.compile(r'%-?([0-9]+|\*)?s')

# sprintf has both buffer and format vulnerabilities.
def c_sprintf(hit):
  source_position = hit.source_position
  if source_position <= len(hit.parameters)-1:
    source=hit.parameters[source_position]
    if c_singleton_string(source):
      hit.level = 1
      hit.note = "Risk is low because the source is a constant character."
    else:
      source = strip_i18n(source)
      if c_constant_string(source):
        if not p_dangerous_sprintf_format.search(source):
          hit.level = max( hit.level - 2, 1)
          hit.note = "Risk is low because the source has a constant maximum length."
        # otherwise, warn of potential buffer overflow (the default)
      else:
        # Ho ho - a nonconstant format string - we have a different problem.
        hit.warning = "Potential format string problem"
        hit.suggestion = "Make format string constant"
        hit.level = 4
        hit.category = "format"
        hit.url = ""
  add_warning(hit)

p_dangerous_scanf_format = re.compile(r'%s')
p_low_risk_scanf_format = re.compile(r'%[0-9]+s')

def c_scanf(hit):
  format_position = hit.format_position
  if format_position <= len(hit.parameters)-1:
    # Assume that translators are trusted to not insert "evil" formats;
    # it's not clear that translators will be messing with INPUT formats,
    # but it's possible so we'll account for it.
    source = strip_i18n(hit.parameters[format_position])
    if c_constant_string(source):
      if p_dangerous_scanf_format.search(source): pass # Accept default.
      elif p_low_risk_scanf_format.search(source):
        # This is often okay, but sometimes extremely serious.
        hit.level = 1
        hit.warning = "it's unclear if the %s limit in the format string is small enough"
        hit.suggestion = "Check that the limit is sufficiently small, or use a different input function"
      else:
        # No risky scanf request.
        # We'll pass it on, just in case it's needed, but at level 0 risk.
        hit.level = 0
        hit.note = "No risky scanf format detected."
    else:
        # Format isn't a constant.
        hit.note = "If the scanf format is influenceable by an attacker, it's exploitable."
  add_warning(hit)


p_dangerous_multi_byte = re.compile(r'^\s*sizeof\s*(\(\s*)?[A-Za-z_$0-9]+'  +
                                    r'\s*(\)\s*)?(-\s*1\s*)?$')
p_safe_multi_byte =      re.compile(r'^\s*sizeof\s*(\(\s*)?[A-Za-z_$0-9]+\s*(\)\s*)?' +
                                     r'/\s*sizeof\s*\(\s*?[A-Za-z_$0-9]+\s*' +
                                     r'\[\s*0\s*\]\)\s*(-\s*1\s*)?$')

def c_multi_byte_to_wide_char(hit):
  # Unfortunately, this doesn't detect bad calls when it's a #define or constant
  # set by a sizeof(), but trying to do so would create FAR too many false positives.
  if len(hit.parameters)-1 >= 6:
    num_chars_to_copy=hit.parameters[6]
    if p_dangerous_multi_byte.search(num_chars_to_copy):
      hit.level = 5
      hit.note = ("Risk is high, it appears that the size is given as bytes, but the " +
                 "function requires size as characters.")
    elif p_safe_multi_byte.search(num_chars_to_copy):
      # This isn't really risk-free, since it might not be the destination, or the
      # destination might be a character array (if it's a char pointer, the pattern
      # is actually quite dangerous, but programmers are unlikely to make that error).
      hit.level = 1
      hit.note = "Risk is very low, the length appears to be in characters not bytes."
  add_warning(hit)

p_null_text = re.compile(r'^ *(NULL|0|0x0) *$')

def c_hit_if_null(hit):
  null_position = hit.check_for_null
  if null_position <= len(hit.parameters)-1:
    null_text=hit.parameters[null_position]
    if p_null_text.search(null_text):
      add_warning(hit)
    else:
      return
  add_warning(hit) # If insufficient # of parameters.

p_static_array = re.compile(r'^[A-Za-z_]+\s+[A-Za-z0-9_$,\s\*()]+\[[^]]')

def c_static_array(hit):
  # This is cheating, but it does the job for most real code.
  # In some cases it will match something that it shouldn't.
  # We don't match ALL arrays, just those of certain types (e.g., char).
  # In theory, any array can overflow, but in practice it seems that
  # certain types are far more prone to problems, so we just report those.
  if p_static_array.search(hit.lookahead):
    add_warning(hit) # Found a static array, warn about it.

def normal(hit):
  add_warning(hit)


# "c_ruleset": the rules for identifying "hits" in C (potential warnings).
# It's a dictionary, where the key is the function name causing the hit,
# and the value is a tuple with the following format:
#  (hook, level, warning, suggestion, category, {other})
# See the definition for class "Hit".
# The key can have multiple values separated with "|".

c_ruleset = {
  "strcpy" :
     (c_buffer, 4,
      "Does not check for buffer overflows when copying to destination",
      "Consider using strncpy or strlcpy (warning, strncpy is easily misused)",
      "buffer", "", {}),
  "lstrcpy|wcscpy|_tcscpy|_mbscpy" :
     (c_buffer, 4,
      "Does not check for buffer overflows when copying to destination",
      "Consider using a function version that stops copying at the end of the buffer",
      "buffer", "", {}),
  "memcpy|CopyMemory|bcopy" :
     (normal, 2, # I've found this to have a lower risk in practice.
      "Does not check for buffer overflows when copying to destination",
      "Make sure destination can always hold the source data",
      "buffer", "", {}),
  "strcat" :
     (c_buffer, 4,
      "Does not check for buffer overflows when concatenating to destination",
      "Consider using strncat or strlcat (warning, strncat is easily misused)",
      "buffer", "", {}),
  "lstrcat|wcscat|_tcscat|_mbscat" :
     (c_buffer, 4,
      "Does not check for buffer overflows when concatenating to destination",
      "",
      "buffer", "", {}),
  "strncpy" :
     (c_buffer,
      1, # Low risk level, because this is often used correctly when FIXING security
      # problems, and raising it to a higher risk level would cause many false positives.
      "Easily used incorrectly; doesn't always \\0-terminate or " +
         "check for invalid pointers",
      "",
      "buffer", "", {}),
  "lstrcpyn|wcsncpy|_tcsncpy|_mbsnbcpy" :
     (c_buffer,
      1, # Low risk level, because this is often used correctly when FIXING security
      # problems, and raising it to a higher risk levle would cause many false positives.
      "Easily used incorrectly; doesn't always \\0-terminate or " +
         "check for invalid pointers",
      "",
      "buffer", "", {}),
  "strncat" :
     (c_strncat,
      1, # Low risk level, because this is often used correctly when
         # FIXING security problems, and raising it to a
         # higher risk level would cause many false positives.
      "Easily used incorrectly (e.g., incorrectly computing the correct maximum size to add)",
      "Consider strlcat or automatically resizing strings",
      "buffer", "", {}),
  "lstrcatn|wcsncat|_tcsncat|_mbsnbcat" :
     (c_strncat,
      1, # Low risk level, because this is often used correctly when FIXING security
      # problems, and raising it to a higher risk level would cause many false positives.
      "Easily used incorrectly (e.g., incorrectly computing the correct maximum size to add)",
      "Consider strlcat or automatically resizing strings",
      "buffer", "", {}),
  "strccpy|strcadd":
     (normal, 1,
      "Subject to buffer overflow if buffer is not as big as claimed",
      "Ensure that destination buffer is sufficiently large",
      "buffer", "", {}),
  "char|TCHAR|wchar_t":  # This isn't really a function call, but it works.
     (c_static_array, 2,
      "Statically-sized arrays can be overflowed",
      ("Perform bounds checking, use functions that limit length, " +
        "or ensure that the size is larger than the maximum possible length"),
      "buffer", "", {'extract_lookahead' : 1}),

  "gets|_getts":
     (normal, 5, "Does not check for buffer overflows",
      "Use fgets() instead", "buffer", "", {'input' : 1}),

  # The "sprintf" hook will raise "format" issues instead if appropriate:
  "sprintf|vsprintf|swprintf|vswprintf|_stprintf|_vstprintf":
     (c_sprintf, 4,
      "Does not check for buffer overflows",
      "Use snprintf or vsnprintf",
      "buffer", "", {}),

  # TODO: Add "wide character" versions of these functions.
  "printf|vprintf|vwprintf|vfwprintf|_vtprintf":
     (c_printf, 4,
      "If format strings can be influenced by an attacker, they can be exploited",
      "Use a constant for the format specification",
      "format", "", {}),

  "fprintf|vfprintf|_ftprintf|_vftprintf":
     (c_printf, 4,
      "If format strings can be influenced by an attacker, they can be exploited",
      "Use a constant for the format specification",
      "format", "", { 'format_position' : 2}),

  # The "syslog" hook will raise "format" issues.
  "syslog":
     (c_printf, 4,
      "If syslog's format strings can be influenced by an attacker, " +
      "they can be exploited",
      "Use a constant format string for syslog",
      "format", "", { 'format_position' : 2} ),

  "snprintf|vsnprintf|_snprintf|_sntprintf|_vsntprintf":
     (c_printf, 4,
      "If format strings can be influenced by an attacker, they can be " +
      "exploited, and note that sprintf variations do not always \\0-terminate",
      "Use a constant for the format specification",
      "format", "", { 'format_position' : 3}),

  "scanf|vscanf|wscanf|_tscanf":
     (c_scanf, 4,
      "The scanf() family's %s operation, without a limit specification, " +
        "permits buffer overflows",
      "Specify a limit to %s, or use a different input function",
      "buffer", "", {'input' : 1}),

  "fscanf|sscanf|vsscanf|vfscanf|_ftscanf":
     (c_scanf, 4,
      "The scanf() family's %s operation, without a limit specification, "
      "permits buffer overflows",
      "Specify a limit to %s, or use a different input function",
      "buffer", "", {'input' : 1, 'format_position' : 2}),

  "strlen|wcslen|_tcslen|_mbslen" :
     (normal,
      1, # Often this isn't really a risk, and even when, it usually at worst causes
      # program crash (and nothing worse).
      "Does not handle strings that are not \\0-terminated (it could cause a crash " +
         "if unprotected)",
      "",
      "buffer", "", {}),

  "MultiByteToWideChar" : # Windows
     (c_multi_byte_to_wide_char,
      2, # Only the default - this will be changed in many cases.
      "Requires maximum length in CHARACTERS, not bytes",
      "",
      "buffer", "", {}),

  "streadd|strecpy":
     (normal, 4,
      "This function does not protect against buffer overflows",
      "Ensure the destination has 4 times the size of the source, to leave room for expansion",
      "buffer", "dangers-c", {}),

  "strtrns":
     (normal, 3,
      "This function does not protect against buffer overflows",
      "Ensure that destination is at least as long as the source",
      "buffer", "dangers-c", {}),

  "realpath":
     (normal, 3,
      "This function does not protect against buffer overflows, " +
        "and some implementations can overflow internally",
      "Ensure that the destination buffer is at least of size MAXPATHLEN, and" +
        "to protect against implementation problems, the input argument should also " +
        "be checked to ensure it is no larger than MAXPATHLEN",
      "buffer", "dangers-c", {}),

  "getopt|getopt_long":
     (normal, 3,
     "Some older implementations do not protect against internal buffer overflows ",
      "Check implementation on installation, or limit the size of all string inputs",
      "buffer", "dangers-c", {'input' : 1}),

  "getpass":
     (normal, 3,
     "Some implementations may overflow buffers",
      "",
      "buffer", "dangers-c", {'input' : 1}),

  "getwd":
     (normal, 3,
     "This does not protect against buffer overflows "
     "by itself, so use with caution",
      "Use getcwd instead",
      "buffer", "dangers-c", {'input' : 1}),

  # fread not included here; in practice I think it's rare to mistake it.
  "getchar|fgetc|getc|read|_gettc":
     (normal, 1,
     "Check buffer boundaries if used in a loop", # loops may be via recursion, too.
      "",
      "buffer", "dangers-c", {'input' : 1}),

  "access":        # ???: TODO: analyze TOCTOU more carefully.
     (normal, 4,
      "This usually indicates a security flaw.  If an " +
      "attacker can change anything along the path between the " +
      "call to access() and the file's actual use (e.g., by moving " +
      "files), the attacker can exploit the race condition",
      "Set up the correct permissions (e.g., using setuid()) and " +
      "try to open the file directly",
      "race",
      "avoid-race#atomic-filesystem", {}),
  "chown":
     (normal, 5,
      "This accepts filename arguments; if an attacker " +
      "can move those files, a race condition results. ",
      "Use fchown( ) instead",
      "race", "", {}),
  "chgrp":
     (normal, 5,
      "This accepts filename arguments; if an attacker " +
      "can move those files, a race condition results. ",
      "Use fchgrp( ) instead",
      "race", "", {}),
  "chmod":
     (normal, 5,
      "This accepts filename arguments; if an attacker " +
      "can move those files, a race condition results. ",
      "Use fchmod( ) instead",
      "race", "", {}),
  "vfork":
     (normal, 2,
      "On some old systems, vfork() permits race conditions, and it's " +
      "very difficult to use correctly",
      "Use fork() instead",
      "race", "", {}),
  "readlink":
     (normal, 5,
      "This accepts filename arguments; if an attacker " +
      "can move those files or change the link content, " +
      "a race condition results.  Also, it does not terminate with ASCII NUL",
      # This is often just a bad idea, and it's hard to suggest a
      # simple alternative:
      "Reconsider approach",
      "race", "", {'input' : 1}),

  "tmpfile":
     (normal, 2,
      "Function tmpfile() has a security flaw on some systems (e.g., older System V systems)",
      "",
      "tmpfile", "", {}),
  "tmpnam|tempnam":
     (normal, 3,
      "Temporary file race condition",
      "",
      "tmpfile", "avoid-race", {}),

  # TODO: Detect GNOME approach to mktemp and ignore it.
  "mktemp":
     (normal, 4,
      "Temporary file race condition",
      "",
      "tmpfile", "avoid-race", {}),

  "mkstemp":
     (normal, 2,
     "Potential for temporary file vulnerability in some circumstances.  Some older Unix-like systems create temp files with permission to write by all by default, so be sure to set the umask to override this. Also, some older Unix systems might fail to use O_EXCL when opening the file, so make sure that O_EXCL is used by the library",
      "",
      "tmpfile", "avoid-race", {}),

  "fopen|open":
     (normal, 2,
     "Check when opening files - can an attacker redirect it (via symlinks), force the opening of special file type (e.g., device files), move things around to create a race condition, control its ancestors, or change its contents?",
      "",
      "misc", "", {}),

  "umask":
     (normal, 1,
      "Ensure that umask is given most restrictive possible setting (e.g., 066 or 077)",
      "",
      "access", "", {}),

  # Windows.  TODO: Detect correct usage approaches and ignore it.
  "GetTempFileName":
     (normal, 3,
      "Temporary file race condition in certain cases " +
        "(e.g., if run as SYSTEM in many versions of Windows)",
      "",
      "tmpfile", "avoid-race", {}),

  # TODO: Need to detect varying levels of danger.
  "execl|execlp|execle|execv|execvp|system|popen|WinExec|ShellExecute":
     (normal, 4,
      "This causes a new program to execute and is difficult to use safely",
      "try using a library call that implements the same functionality " +
      "if available",
      "shell", "", {}),

  # TODO: Need to detect varying levels of danger.
  "execl|execlp|execle|execv|execvp|system|popen|WinExec|ShellExecute":
     (normal, 4,
      "This causes a new program to execute and is difficult to use safely",
      "try using a library call that implements the same functionality " +
      "if available",
      "shell", "", {}),

  # TODO: Be more specific.  The biggest problem involves "first" param NULL,
  # second param with embedded space. Windows.
  "CreateProcessAsUser|CreateProcessWithLogon":
     (normal, 3,
      "This causes a new process to execute and is difficult to use safely",
      "Especially watch out for embedded spaces",
      "shell", "", {}),

  # TODO: Be more specific.  The biggest problem involves "first" param NULL,
  # second param with embedded space. Windows.
  "CreateProcess":
     (c_hit_if_null, 3,
      "This causes a new process to execute and is difficult to use safely",
      "Specify the application path in the first argument, NOT as part of the second, " +
        "or embedded spaces could allow an attacker to force a different program to run",
      "shell", "", {'check_for_null' : 1}),

  "atoi|atol":
     (normal, 2,
      "Unless checked, the resulting number can exceed the expected range",
      " If source untrusted, check both minimum and maximum, even if the" +
      " input had no minus sign (large numbers can roll over into negative" +
      " number; consider saving to an unsigned value if that is intended)",
      "integer", "dangers-c", {}),

  # Random values.  Don't trigger on "initstate", it's too common a term.
  "drand48|erand48|jrand48|lcong48|lrand48|mrand48|nrand48|random|seed48|setstate|srand|strfry|srandom":
     (normal, 3,
      "This function is not sufficiently random for security-related functions such as key and nonce creation",
      "use a more secure technique for acquiring random values",
      "random", "", {}),

  "crypt":
     (normal, 4,
      "Function crypt is a poor one-way hashing algorithm; since it only accepts passwords of 8 " +
        "characters or less, and only a two-byte salt, it is excessively vulnerable to " +
        "dictionary attacks given today's faster computing equipment",
      "Use a different algorithm, such as SHA-1, with a larger non-repeating salt",
      "crypto", "", {}),

  # OpenSSL EVP calls to use DES.
  "EVP_des_ecb|EVP_des_cbc|EVP_des_cfb|EVP_des_ofb|EVP_desx_cbc":
     (normal, 4,
      "DES only supports a 56-bit keysize, which is too small given today's computers",
      "Use a different patent-free encryption algorithm with a larger keysize, " +
         "such as 3DES or AES",
      "crypto", "", {}),

  # Other OpenSSL EVP calls to use small keys.
  "EVP_rc4_40|EVP_rc2_40_cbc|EVP_rc2_64_cbc":
     (normal, 4,
      "These keysizes are too small given today's computers",
      "Use a different patent-free encryption algorithm with a larger keysize, " +
        "such as 3DES or AES",
      "crypto", "", {}),

  "chroot":
     (normal, 3,
      "chroot can be very helpful, but is hard to use correctly",
      "Make sure the program immediately chdir(\"/\")," +
      " closes file descriptors," +
      " and drops root privileges, and that all necessary files" +
      " (and no more!) are in the new root",
      "misc", "", {}),

  "getenv|curl_getenv":
     (normal, 3, "Environment variables are untrustable input if they can be" +
                 " set by an attacker.  They can have any content and" +
                 " length, and the same variable can be set more than once",
      "Check environment variables carefully before using them",
      "buffer", "", {'input' : 1}),

  "g_get_home_dir":
     (normal, 3, "This function is synonymous with 'getenv(\"HOME\")';" +
                 "it returns untrustable input if the environment can be" +
                 "set by an attacker.  It can have any content and length, " +
                 "and the same variable can be set more than once",
      "Check environment variables carefully before using them",
      "buffer", "", {'input' : 1}),

  "g_get_tmp_dir":
     (normal, 3, "This function is synonymous with 'getenv(\"TMP\")';" +
                 "it returns untrustable input if the environment can be" +
                 "set by an attacker.  It can have any content and length, " +
                 "and the same variable can be set more than once",
      "Check environment variables carefully before using them",
      "buffer", "", {'input' : 1}),


  # These are Windows-unique:

  # TODO: Should have lower risk if the program checks return value.
  "RpcImpersonateClient|ImpersonateLoggedOnUser|CoImpersonateClient|" +
     "ImpersonateNamedPipeClient|ImpersonateDdeClientWindow|ImpersonateSecurityContext|" +
     "SetThreadToken":
     (normal, 4, "If this call fails, the program could fail to drop heightened privileges",
      "Make sure the return value is checked, and do not continue if a failure is reported",
      "access", "", {}),

  "InitializeCriticalSection":
     (normal, 3, "Exceptions can be thrown in low-memory situations",
      "Use InitializeCriticalSectionAndSpinCount instead",
      "misc", "", {}),

  "EnterCriticalSection":
     (normal, 3, "On some versions of Windows, exceptions can be thrown in low-memory situations",
      "Use InitializeCriticalSectionAndSpinCount instead",
      "misc", "", {}),

  "LoadLibrary|LoadLibraryEx":
     (normal, 3, "Ensure that the full path to the library is specified, or current directory may be used",
      "Use registry entry or GetWindowsDirectory to find library path, if you aren't already",
      "misc", "", {'input' : 1}),

  "SetSecurityDescriptorDacl":
     (c_hit_if_null, 5,
      "Never create NULL ACLs; an attacker can set it to Everyone (Deny All Access), " +
        "which would even forbid administrator access",
      "",
      "misc", "", {'check_for_null' : 3}),

  "AddAccessAllowedAce":
     (normal, 3,
      "This doesn't set the inheritance bits in the access control entry (ACE) header",
      "Make sure that you set inheritance by hand if you wish it to inherit",
      "misc", "", {}),

  "getlogin":
     (normal, 4,
      "It's often easy to fool getlogin.  Sometimes it does not work at all, because some program messed up the utmp file.  Often, it gives only the first 8 characters of the login name. The user currently logged in on the controlling tty of our program need not be the user who started it.  Avoid getlogin() for security-related purposes",
      "Use getpwuid(geteuid()) and extract the desired information instead",
      "misc", "", {}),

  "cuserid":
     (normal, 4,
      "Exactly what cuserid() does is poorly defined (e.g., some systems use the effective uid, like Linux, while others like System V use the real uid). Thus, you can't trust what it does. It's certainly not portable (The cuserid function was included in the 1988 version of POSIX, but removed from the 1990 version).  Also, if passed a non-null parameter, there's a risk of a buffer overflow if the passed-in buffer is not at least L_cuserid characters long",
      "Use getpwuid(geteuid()) and extract the desired information instead",
      "misc", "", {}),

  "getpw":
     (normal, 4,
      "This function is dangerous; it may overflow the provided buffer. It extracts data from a 'protected' area, but most systems have many commands to let users modify the protected area, and it's not always clear what their limits are.  Best to avoid using this function altogether",
      "Use getpwuid() instead",
      "buffer", "", {}),

  "getpass":
     (normal, 4,
      "This function is obsolete and not portable. It was in SUSv2 but removed by POSIX.2.  What it does exactly varies considerably between systems, particularly in where its prompt is displayed and where it gets its data (e.g., /dev/tty, stdin, stderr, etc.)",
      "Make the specific calls to do exactly what you want.  If you continue to use it, or write your own, be sure to zero the password as soon as possible to avoid leaving the cleartext password visible in the process' address space",
      "misc", "", {}),

  "gsignal|ssignal":
     (normal, 2,
      "These functions are considered obsolete on most systems, and very non-poertable (Linux-based systems handle them radically different, basically if gsignal/ssignal were the same as raise/signal respectively, while System V considers them a separate set and obsolete)",
      "Switch to raise/signal, or some other signalling approach",
      "obsolete", "", {}),

  "memalign":
     (normal, 1,
     "On some systems (though not Linux-based systems) an attempt to free() results from memalign() may fail. This may, on a few systems, be exploitable.  Also note that memalign() may not check that the boundary parameter is correct",
      "Use posix_memalign instead (defined in POSIX's 1003.1d).  Don't switch to valloc(); it is marked as obsolete in BSD 4.3, as legacy in SUSv2, and is no longer defined in SUSv3.  In some cases, malloc()'s alignment may be sufficient",
      "free", "", {}),

  "ulimit":
     (normal, 1,
     "This C routine is considered obsolete (as opposed to the shell command by the same name, which is NOT obsolete)",
      "Use getrlimit(2), setrlimit(2), and sysconf(3) instead",
      "obsolete", "", {}),

  "usleep":
     (normal, 1,
     "This C routine is considered obsolete (as opposed to the shell command by the same name).   The interaction of this function with SIGALRM and other timer functions such as sleep(), alarm(), setitimer(), and nanosleep() is unspecified",
      "Use nanosleep(2) or setitimer(2) instead",
      "obsolete", "", {}),


   # Input functions, useful for -I
  "recv|recvfrom|recvmsg|fread|readv":
     (normal, 0, "Function accepts input from outside program",
      "Make sure input data is filtered, especially if an attacker could manipulate it",
      "input", "", {'input' : 1}),


  # TODO: detect C++'s:   cin >> charbuf, where charbuf is a char array; the problem
  #       is that flawfinder doesn't have type information, and ">>" is safe with
  #       many other types.
  # ("send" and friends aren't todo, because they send out.. not input.)
  # TODO: cwd("..") in user's space - TOCTOU vulnerability
  # TODO: There are many more rules to add, esp. for TOCTOU.
  }

template_ruleset = {
  # This is a template for adding new entries (the key is impossible):
  "9":
     (normal, 2,
      "",
      "",
      "tmpfile", "", {}),
  }


def find_column(text, position):
  "Find column number inside line."
  newline = string.rfind(text, "\n", 0, position)
  if newline == -1:
    return position + 1
  else:
    return position - newline

def get_context(text, position):
  "Get surrounding text line starting from text[position]"
  linestart = string.rfind(text, "\n", 0, position+1) + 1
  lineend   = string.find(text, "\n", position, len(text))
  if lineend == -1: lineend = len(text)
  return text[linestart:lineend]

def c_valid_match(text, position):
  # Determine if this is a valid match, or a false positive.
  # If false positive controls aren't on, always declare it's a match:
  i = position
  while i < len(text):
    c = text[i]
    if c == '(':                 return 1
    elif c in string.whitespace: i = i + 1
    else:
      if falsepositive: return 0       # No following "(", presume invalid.
      if c in "=+-":
        # This is very unlikely to be a function use. If c is '=',
        # the name is followed by an assignment or is-equal operation.
        # Since the names of library functions are really unlikely to be
        # followed by an assignment statement or 'is-equal' test,
        # while this IS common for variable names, let's declare it invalid.
        # It's possible that this is a variable function pointer, pointing
        # to the real library function, but that's really improbable.
        # If c is "+" or "-", we have a + or - operation.
        # In theory "-" could be used for a function pointer difference
        # computation, but this is extremely improbable.
        # More likely: this is a variable in a computation, so drop it.
        return 0
      return 1
  return 0 # Never found anything other than "(" and whitespace.

def process_directive():
  "Given a directive, process it."
  global ignoreline, num_ignored_hits
  # TODO: Currently this is just a stub routine that simply removes
  # hits from the current line, if any, and sets a flag if not.
  # Thus, any directive is considered the "ignore" directive.
  # Currently that's okay because we don't have any other directives yet.
  if never_ignore: return
  hitfound = 0
  # Iterate backwards over hits, to be careful about the destructive iterator
  for i in xrange(len(hitlist)-1, -1, -1):
    if hitlist[i].line == linenumber:
      del hitlist[i] # DESTROY - this is a DESTRUCTIVE iterator.
      hitfound = 1   # Don't break, because there may be more than one.
      num_ignored_hits = num_ignored_hits + 1
  if not hitfound:
    ignoreline = linenumber + 1  # Nothing found - ignore next line.

# Characters that can be in a string.
# 0x4, 4.4e4, etc.
numberset=string.hexdigits+"_x.Ee"

# Patterns for various circumstances:
p_whitespace = re.compile( r'[ \t\v\f]+' )
p_include = re.compile( r'#\s*include\s+(<.*?>|".*?")' )
p_digits  = re.compile( r'[0-9]' )
p_alphaunder = re.compile( r'[A-Za-z_]' )  # Alpha chars and underline.
# A "word" in C.  Note that "$" is permitted -- it's not permitted by the
# C standard in identifiers, but gcc supports it as an extension.
p_c_word = re.compile( r'[A-Za-z_][A-Za-z_0-9$]*' )
# We'll recognize ITS4 and RATS ignore directives, as well as our own,
# for compatibility's sake:
p_directive = re.compile( r'(?i)\s*(ITS4|Flawfinder|RATS):\s*([^\*]*)' )

max_lookahead=500  # Lookahead limit for c_static_array.

def process_c_file(f, patch_infos):
  global filename, linenumber, ignoreline, sumlines, num_links_skipped
  global sloc
  filename=f
  linenumber = 1
  ignoreline = -1

  incomment = 0
  instring = 0
  linebegin = 1
  codeinline = 0 # 1 when we see some code (so increment sloc at newline)

  if ((patch_infos != None) and (not patch_infos.has_key(f))):
    # This file isn't in the patch list, so don't bother analyzing it.
    if not quiet:
      if output_format:
        print "Skipping unpatched file ", h(f), "<br>"
      else:
        print "Skipping unpatched file", f
      sys.stdout.flush()
    return


  # print ('111',open(f, 'r').read())
  if f == "-":
   input = sys.stdin
  else:
    # Symlinks should never get here, but just in case...
    if ((not allowlink) and os.path.islink(f)):
      print "BUG! Somehow got a symlink in process_c_file!"
      num_links_skipped = num_links_skipped + 1
      return
    try:
      input = open(f, 'r')
      # print "input",input
      # print "input.read()", dir(input), input.closed
    except: 
      print "Error: failed to open", h(f)
      sys.exit(1)

  # Read ENTIRE file into memory.  Use readlines() to convert \n if necessary.
  # This turns out to be very fast in Python, even on large files, and it
  # eliminates lots of range checking later, making the result faster.
  # We're examining source files, and today, it would be EXTREMELY bad practice
  # to create source files larger than main memory space.
  # Better to load it all in, and get the increased speed and reduced
  # development time that results.
  if not quiet:
    if output_format:
      print "Examining", h(f), "<br>"
    else:
      print "Examining", f
    sys.stdout.flush()

  text = string.join(input.readlines(),"")
  # print ("open",open(f).getvalue())
  # print "text=",text

  i = 0
  while i < len(text):
    # This is a trivial tokenizer that just tries to find "words", which
    # match [A-Za-z_][A-Za-z0-9_]*.  It skips comments & strings.
    # It also skips "#include <...>", which must be handled specially
    # because "<" and ">" aren't usually delimiters.
    # It doesn't bother to tokenize anything else, since it's not used.
    # The following is a state machine with 3 states: incomment, instring,
    # and "normal", and a separate state "linebegin" if at BOL.

    # Skip any whitespace
    m = p_whitespace.match(text,i)
    if m:
      i = m.end(0)

    c = text[i]
    if linebegin:  # If at beginning of line, see if #include is there.
       linebegin = 0
       if c == "#": codeinline = 1  # A directive, count as code.
       m = p_include.match(text,i)
       if m:  # Found #include, skip it.  Otherwise: #include <stdio.h>
         i = m.end(0)
         continue
    if c == "\n":
      linenumber = linenumber + 1
      sumlines = sumlines + 1
      linebegin = 1
      if codeinline: sloc = sloc + 1
      codeinline = 0
      i = i +1
      continue
    i = i + 1   # From here on, text[i] points to next character.
    if i < len(text): nextc = text[i]
    else:             nextc = ''
    if incomment:
       if c=='*' and nextc=='/':
           i = i + 1
           incomment = 0
    elif instring:
       if c == '\\' and (nextc != "\n"): i = i + 1
       elif c == '"' and instring == 1: instring = 0
       elif c == "'" and instring == 2: instring = 0
    else:
      if c=='/' and nextc=='*':
          m = p_directive.match(text, i+1)  # Is there a directive here?
          if m:
            process_directive()
          i = i + 1
          incomment = 1
      elif c=='/' and nextc=='/':  # "//" comments - skip to EOL.
          m = p_directive.match(text, i+1)  # Is there a directive here?
          if m:
            process_directive()
          while i<len(text) and text[i] != "\n":
            i = i + 1
      elif c=='"':
          instring = 1
          codeinline = 1
      elif c=="'":
          instring = 2
          codeinline = 1
      else:
          codeinline = 1  # It's not whitespace, comment, or string.
          m = p_c_word.match(text, i-1)
          if m:                        # Do we have a word?
            startpos=i-1
            endpos = m.end(0)
            i = endpos
            word = text[startpos:endpos]
            # print "Word is:", text[startpos:endpos]
            if c_ruleset.has_key(word) and c_valid_match(text, endpos):
              if ( (patch_infos == None) or ((patch_infos != None) and patch_infos[f].has_key(linenumber))):
        	# FOUND A MATCH, setup & call hook.
        	# print "HIT: #%s#\n" % word
        	# Don't use the tuple assignment form, e.g., a,b=c,d
        	# because Python (least 2.2.2) does that slower
        	# (presumably because it creates & destroys temporary tuples)
        	hit = Hit(c_ruleset[word])
        	hit.name = word
        	hit.start = startpos
        	hit.end = endpos
        	hit.line = linenumber
        	hit.column = find_column(text, startpos)
        	hit.filename=filename
        	hit.context_text = get_context(text, startpos)
        	hit.parameters = extract_c_parameters(text, endpos)
        	if hit.extract_lookahead:
        	  hit.lookahead = text[startpos:startpos+max_lookahead]
        	apply(hit.hook, (hit, ))
          elif p_digits.match(c):
            while i<len(text) and p_digits.match(text[i]): # Process a number.
              i = i + 1
          # else some other character, which we ignore.
  # End of loop through text. Wrap up.
  if codeinline: sloc = sloc + 1
  if incomment: error("File ended while in comment.")
  if instring: error("File ended while in string.")

  # print "hitlist",hitlist

def expand_ruleset(ruleset):
  # Rulesets can have compressed sets of rules
  # (multiple function names separated by "|".
  # Expand the given ruleset.
  # Note that this for loop modifies the ruleset while it's iterating!
  for rule in ruleset.keys():
    if string.find(rule, "|") != -1:  # We found a rule to expand.
      for newrule in string.split(rule, "|"):
        if ruleset.has_key(newrule):
          print "Error: Rule %s, when expanded, overlaps %s" % ( rule, newrule )
          sys.exit(1)
        ruleset[newrule] = ruleset[rule]
      del ruleset[rule]
  # To print out the set of keys in the expanded ruleset, run:
  #   print `ruleset.keys()`

def display_ruleset(ruleset):
  # First, sort the list by function name:
  sortedkeys = ruleset.keys()
  sortedkeys.sort()
  # Now, print them out:
  for key in sortedkeys:
    print key, ruleset[key][1] # function name and default level.

def initialize_ruleset():
  expand_ruleset(c_ruleset)
  if showheading:
    print "Number of dangerous functions in C/C++ ruleset:", len(c_ruleset)
    if output_format: print "<p>"
  if list_rules:
    display_ruleset(c_ruleset)
    sys.exit(0)


# Show the header, but only if it hasn't been shown yet.
def display_header():
  global displayed_header
  if not showheading: return
  if not displayed_header:
    if output_format:
      print ('<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" ' +
            '"http://www.w3.org/TR/html4/loose.dtd">')
      print "<html>"
      print "<head>"
      print '<meta http-equiv="Content-type" content="text/html; charset=utf8">'
      print "<title>Flawfinder Results</title>"
      print '<meta name="author" content="David A. Wheeler">'
      print '<meta name="keywords" lang="en" content="flawfinder results, security scan">'
      print "</head>"
      print "<body>"
      print "<h1>Flawfinder Results</h1>"
      print "Here are the security scan results from"
      print '<a href="http://www.dwheeler.com/flawfinder">Flawfinder version %s</a>,' % version
      print '(C) 2001-2004 <a href="http://www.dwheeler.com">David A. Wheeler</a>.'
    else:
      print "Flawfinder version %s, (C) 2001-2004 David A. Wheeler." % version
    displayed_header = 1


c_extensions = { '.c' : 1, '.h' : 1,
                 '.ec': 1, '.ecp': 1,  # Informix embedded C.
                 '.pgc': 1,            # Postgres embedded C.
                 '.C': 1, '.cpp': 1, '.CPP': 1, '.cxx': 1, '.cc': 1, # C++
                 '.CC' : 1, '.c++' :1,  # C++.
                 '.pcc': 1,            # Oracle C++
                 '.hpp': 1, '.H' : 1,  # .h - usually C++.
               }


def maybe_process_file(f, patch_infos):
  # process f, but only if (1) it's a directory (so we recurse), or
  # (2) it's source code in a language we can handle.
  # Currently, for files that means only C/C++, and we check if the filename
  # has a known C/C++ filename extension.  If it doesn't, we ignore the file.
  # We accept symlinks only if allowlink is true.
  global num_links_skipped, num_dotdirs_skipped
  if os.path.isdir(f):
    if (not allowlink) and os.path.islink(f):
      if not quiet: print "Warning: skipping symbolic link directory", h(f)
      num_links_skipped = num_links_skipped + 1
      return
    base_filename = os.path.basename(f)
    if (skipdotdir and len(base_filename) > 0 and ("." == base_filename[0])):
      if not quiet: print "Warning: skipping directory with initial dot", h(f)
      num_dotdirs_skipped = num_dotdirs_skipped + 1
      return
    for file in os.listdir(f):
      maybe_process_file(os.path.join(f, file), patch_infos)
  # Now we will FIRST check if the file appears to be a C/C++ file, and
  # THEN check if it's a regular file or symlink.  This is more complicated,
  # but I do it this way so that there won't be a lot of pointless
  # warnings about skipping files we wouldn't have used anyway.
  dotposition = string.rfind(f, ".")
  if dotposition > 1:
    extension = f[dotposition:]
    if c_extensions.has_key(extension):
      # Its name appears to be a C/C++ source code file.
      if (not allowlink) and os.path.islink(f):
        if not quiet: print "Warning: skipping symbolic link file", h(f)
        num_links_skipped = num_links_skipped + 1
      elif not os.path.isfile(f):
        # Skip anything not a normal file.  This is so that
        # device files, etc. won't cause trouble.
        if not quiet: print "Warning: skipping non-regular file", h(f)
      else:
        # We want to know the difference only with files found in the patch.
        if ( (patch_infos == None) or (patch_infos != None and patch_infos.has_key(f) == True) ):
          process_c_file(f, patch_infos)


def process_file_args(files, patch_infos):
  # Process the list of "files", some of which may be directories,
  # which were given on the command line.
  # This is handled differently than anything not found on the command line
  # (i.e. through recursing into a directory) because flawfinder
  # ALWAYS processes normal files given on the command line.
  # This is done to give users control over what's processed;
  # if a user really, really wants to analyze a file, name it!
  # If user wants to process "this directory and down", just say ".".
  # We handle symlinks specially, handle normal files and directories,
  # and skip the rest to prevent security problems. "-" is stdin.
  global num_links_skipped
  for f in files:
    if (not allowlink) and os.path.islink(f):
       if not quiet: print "Warning: skipping symbolic link", h(f)
       num_links_skipped = num_links_skipped + 1
    elif os.path.isfile(f) or f == "-":
       # If on the command line, FORCE processing of it.
       # Currently, we only process C/C++.
       # check if we only want to review a patch
       if ( (patch_infos != None and patch_infos.has_key(f) == True) or (patch_infos == None) ):
        process_c_file(f, patch_infos)
    elif os.path.isdir(f):
       # At one time flawfinder used os.path.walk, but that Python
       # built-in doesn't give us enough control over symbolic links.
       # So, we'll walk the filesystem hierarchy ourselves:
       maybe_process_file(f, patch_infos)
    else:
       if not quiet: print "Warning: skipping non-regular file", h(f)

def usage():
  print """
flawfinder [--help] [--context]  [-c]  [--columns | -C] [--html]
           [--dataonly | -D]
           [--minlevel=X | -m X]
           [--immediate] [-i] [--inputs | -I] [--neverignore | -n]
           [ --patch=F ] [--quiet | -Q] [--singleline | -S ]
           [--loadhitlist=F ] [ --savehitlist=F ] [ --diffhitlist=F ]
           [--listrules]
           [--] [ source code file or source root directory ]+

  --help      Show this usage help

  --allowlink
              Allow symbolic links.
  --followdotdir
              Follow directories whose names begin with ".".

  --context
  -c          Show context (the line having the "hit"/potential flaw)

  --columns   Show  the  column  number  (as well as the file name and
              line number) of each hit; this is shown after the line number
              by adding a colon and the column number in the line (the first
              character in a line is column number 1).
  
  --html      Display as HTML output.

  -m X
  --minlevel=X
              Set minimum risk level to X for inclusion in hitlist.  This
              can be from 0 (``no risk'')  to  5  (``maximum  risk'');  the
              default is 1.

  -S
  --singleline Single-line output.

  --neverignore
  -n          Never ignore security issues, even if they have an ``ignore''
              directive in a comment.

  --immediate
  -i          Immediately display hits (don't just wait until the end).

  --inputs    Show only functions that obtain data from outside the program;
  -I          this also sets minlevel to 0.

  --nolink    Skip symbolic links (ignored).

  --omittime  Omit time to run.

  --patch=F   display information related to the patch F. (patch must be already applied)

  --Q
  --quiet     Don't display status information (i.e., which files are being
              examined) while the analysis is going on.

  --D
  --dataonly  Don't display the headers and footers of the analysis;
              use this along with --quiet to get just the results.
  
  --listrules List the rules in the ruleset (rule database).

  --loadhitlist=F
              Load hits from F instead of analyzing source programs.

  --savehitlist=F
              Save all hits (the "hitlist") to F.

  --diffhitlist=F
              Show only hits (loaded or analyzed) not in F.


  For more information, please consult the manpage or available
  documentation.
"""

def process_options():
  global show_context, show_inputs, allowlink, skipdotdir, omit_time
  global output_format, minimum_level, show_immediately, single_line
  global falsepositive
  global show_columns, never_ignore, quiet, showheading, list_rules
  global loadhitlist, savehitlist, diffhitlist
  global patch_file
  try:
    # Note - as a side-effect, this sets sys.argv[].
    optlist, args = getopt.getopt(sys.argv[1:], "cm:nih?CSDQIFP:",
                    ["context", "minlevel=", "immediate", "inputs", "input",
                     "nolink", "falsepositive", "falsepositives",
                     "columns", "listrules", "omittime", "allowlink", "patch=",
                     "followdotdir",
                     "neverignore", "quiet", "dataonly", "html", "singleline",
                     "loadhitlist=", "savehitlist=", "diffhitlist=",
                     "version", "help" ])
    for (opt,value) in optlist:
      if   opt == "--context" or opt == "-c":
        show_context = 1
      elif opt == "--columns" or opt == "-C":
        show_columns = 1
      elif opt == "--quiet" or opt == "-Q":
        quiet = 1
      elif opt == "--dataonly" or opt == "-D":
        showheading = 0
      elif opt == "--inputs" or opt == "--input" or opt == "-I":
        show_inputs = 1
        minimum_level = 0
      elif opt == "--falsepositive" or opt == "falsepositives" or opt == "-F":
        falsepositive = 1
      elif opt == "--nolink":
        allowlink = 0
      elif opt == "--omittime":
        omit_time = 1
      elif opt == "--allowlink":
        allowlink = 1
      elif opt == "--followdotdir":
        skipdotdir = 0
      elif opt == "--listrules":
        list_rules = 1
      elif opt == "--html":
        output_format = 1
        single_line = 0
      elif opt == "--minlevel" or opt == "-m":
        minimum_level = string.atoi(value)
      elif opt == "--singleline" or opt == "-S":
        single_line = 1
      elif opt == "--immediate" or opt == "-i":
        show_immediately = 1
      elif opt == "-n" or opt == "--neverignore":
        never_ignore = 1
      elif opt == "-P" or opt == "--patch":
        # Note: This is -P, so that a future -p1 option can strip away
        # pathname prefixes (with the same option name as "patch").
        patch_file = value
        # If we consider ignore comments we may change a line which was
        # previously ignored but which will raise now a valid warning without
        # noticing it now.  So, set never_ignore.
        never_ignore = 1
      elif opt == "--loadhitlist":
        loadhitlist = value
        display_header()
        if showheading: print "Loading hits from", value
      elif opt == "--savehitlist":
        savehitlist = value
        display_header()
        if showheading: print "Saving hitlist to", value
      elif opt == "--diffhitlist":
        diffhitlist = value
        display_header()
        if showheading: print "Showing hits not in", value
      elif opt == "--version":
        print version
        sys.exit(0)
      elif opt in [ '-h', '-?', '--help' ]:
        usage()
        sys.exit(0)
    # For DOS/Windows, expand filenames; for Unix, DON'T expand them
    # (the shell will expand them for us).  Some sloppy Python programs
    # always call "glob", but that's WRONG -- on Unix-like systems that
    # will expand twice.  Python doesn't have a clean way to detect
    # "has globbing occurred", so this is the best I've found:
    if os.name == "windows" or os.name == "nt" or os.name == "dos":
       sys.argv[1:] = reduce(operator.add, map(glob.glob, args))
    else:
       sys.argv[1:] = args
  # In Python 2 the convention is "getopt.GetoptError", but we
  # use "getopt.error" here so it's compatible with both
  # Python 1.5 and Python 2.
  except getopt.error, text:
    print "*** getopt error:", text
    usage()
    sys.exit(1)



def process_files():
  global hitlist
  if loadhitlist:
    f = open(loadhitlist)
    hitlist = pickle.load(f)
  else:
    patch_infos = None
    if (patch_file != ""):
      patch_infos = load_patch_info(patch_file)
    files = sys.argv[1:]
    if not files:
        print "*** No input files"
        return None
    process_file_args(files, patch_infos)
    return 1


def show_final_results():
  global hitlist
  count = 0
  count_per_level = {}
  count_per_level_and_up = {}
  for i in range(0,6):  # Initialize count_per_level
    count_per_level[i] = 0
  for i in range(0,6):  # Initialize count_per_level
    count_per_level_and_up[i] = 0
  if show_immediately:   # Separate the final results.
    print
    if showheading:
      if output_format:
        print "<h1>Final Results</h1>"
      else:
        print "FINAL RESULTS:"
        print
  hitlist.sort()
  # Display results.  The HTML format now uses
  # <ul> so that the format differentiates each entry.
  # I'm not using <ol>, because its numbers might be confused with
  # the risk levels or line numbers.
  if diffhitlist:
    diff_file = open(diffhitlist)
    diff_hitlist = pickle.load(diff_file)
    if output_format: print "<ul>"
    for h in hitlist:
      if h not in diff_hitlist:
        h.show()
        count_per_level[h.level] = count_per_level[h.level] + 1
        count = count + 1
    if output_format: print "</ul>"
    diff_file.close()
    if showheading:
      if output_format:
        print "<p>"
      if count > 0:
        print "Hits not in original histlist =", count
      else:
        print "No hits found that weren't already in the hitlist."
      if output_format:
        print "<br>"
  else:
    if output_format: print "<ul>"
    for h in hitlist:
      h.show()
      count_per_level[h.level] = count_per_level[h.level] + 1
    if output_format: print "</ul>"
    count = len(hitlist)
    if showheading:
      if output_format:
        print "<p>"
      else:
        print
      if count > 0:
        print "Hits =", count
      else:
        print "No hits found."
      if output_format:
        print "<br>"
  if showheading:
    # Compute the amount of time spent, and lines analyzed/second.
    # By computing time here, we also include the time for
    # producing the list of hits, which is reasonable.
    time_analyzing = time.time() - starttime
    print "Lines analyzed = %d" % sumlines,
    if time_analyzing > 0 and not omit_time:  # Avoid divide-by-zero.
      print "in %.2f seconds (%d lines/second)" % (
             time_analyzing + 0.5,
             (int) (sumlines / time_analyzing + 0.5) )
    else:
      print
    if output_format: print "<br>"
    print "Physical Source Lines of Code (SLOC) = %d" % sloc
    if output_format: print "<br>"
    # Output hits@each level.
    print "Hits@level =",
    for i in range(0,6):
      print "[%d] %3d" % (i, count_per_level[i]),
    if output_format:
      print "<br>"
    else:
      print
    # Compute hits at "level x or higher"
    print "Hits@level+ =",
    for i in range(0,6):
      for j in range(i,6):
        count_per_level_and_up[i] = count_per_level_and_up[i] + count_per_level[j]
    # Display hits at "level x or higher"
    for i in range(0,6):
      print "[%d+] %3d" % (i, count_per_level_and_up[i]),
    if output_format:
      print "<br>"
    else:
      print
    if (sloc > 0):
      print "Hits/KSLOC@level+ =",
      for i in range(0,6):
        print "[%d+] %3g" % (i, count_per_level_and_up[i]*1000.0/sloc),
    if output_format:
      print "<br>"
    else:
      print
    #
    if num_links_skipped:
      print "Symlinks skipped =", num_links_skipped, "(--allowlink overrides but see doc for security issue)"
      if output_format:
        print "<br>"
    if num_dotdirs_skipped:
      print "Dot directories skipped =", num_dotdirs_skipped, "(--followdotdir overrides)"
      if output_format:
        print "<br>"
    if num_ignored_hits > 0:
      print "Suppressed hits =", num_ignored_hits, "(use --neverignore to show them)"
      if output_format:
        print "<br>"
    print "Minimum risk level = %d" % minimum_level
    if output_format: print "<br>"
    if count > 0:
       print "Not every hit is necessarily a security vulnerability."
       if output_format:
         print "<br>"
    print "There may be other security vulnerabilities; review your code!"
    if output_format:
      print "</body>"
      print "</html>"


def save_if_desired():
  # We'll save entire hitlist, even if only differences displayed.
  if savehitlist:
    print "Saving hitlist to", savehitlist
    f = open(savehitlist, "w")
    pickle.dump(hitlist, f)
    f.close()

def flawfind():
  process_options()
  display_header()
  initialize_ruleset()
  if process_files():
    show_final_results()
    save_if_desired()

def process_text(filename, text):
  global open
  old_open = open
  insert_file_into_FS(filename,text)
  open = fake_open
  initialize_ruleset()
  process_c_file(filename, None)
  # show_final_results()

  # print hitlist

  open = old_open
  return len(hitlist)

if __name__ == '__main__':
  try:
    flawfind()
  except KeyboardInterrupt:
    print "*** Flawfinder interrupted"

