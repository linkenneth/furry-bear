"""The scheme_tokens module provides functions tokenize_line and tokenize_lines
for converting (iterators producing) strings into (iterators producing)
lists of token descriptors.  A "token descriptor" here refers to a pair (syntax, value), where

   * value is either value denoted by the token (an integer in the case of
     numeric tokens, a boolean value in the case of boolean tokens) or the
     text of the token itself (in all other cases).  the value of the token
     (a string, integer, or boolean value),
   * type indicates the "syntactic category" of the token: whether it
     is a parenthesis, symbol, etc.  The possible types are SYMBOL,
     NUMERAL, BOOLEAN, "(", ")", ".", and "\'".

For example, the tokens in the line
    (define (f x) (if (> x 3) #f bar))
are
    [ (SYMBOL, 'define'), ('(', '('), (SYMBOL, 'f'), (SYMBOL, 'x'), (')', ')'),
      ('(', '('), (SYMBOL, 'if'), ('(', '('), (SYMBOL, '>'), (SYMBOL, 'x'),
      (')', ')'), (NUMERAL, 3), (BOOLEAN, False), (SYMBOL, 'bar')
      (')', ')'), (')', ')') ]
"""

import sys
from scheme_utils import *

_LETTER = char_set('a', 'z') | char_set('A', 'Z')
_DIGIT = char_set('0', '9')

_SYMBOL_STARTS = set('!$%&*/:<=>?@^_~') | _LETTER
_SYMBOL_INNERS = _SYMBOL_STARTS | _DIGIT | set('+-.')
_NUMERAL_STARTS = _DIGIT | set('+-.')
_WHITESPACE = ' \t\n\r'
_DELIM_TOKENS = list("()'" )
_ONECHAR_TOKENS = _DELIM_TOKENS + ['.']
_TOKEN_END = list(_WHITESPACE) + _DELIM_TOKENS

def symbol_escaped(s):
    """The value of S, a symbol name, escaped so that it may used by the
    reader to reconstruct the symbol."""
    for c in s:
        if c not in _SYMBOL_INNERS or c.isupper():
            break
    else:
        return s

    raw = repr(s)
    return "|" + raw[1:-1].replace('|', '\\|') + "|"

def _quoted_token(line, k):
    """Assuming that LINE[K] is a '|', return (tok, k') where
    tok is the text of the token (including '|'s) and K' is the
    index of the following character in LINE.  Within the token, the
    backslash escapes the next character (a non-standard treatment)."""
    # finds matching end "|"
    i = k+1
    while i < len(line):
        if line[i] == '\\':
            # this skips two chars because the char after the "\" is
            # escaped, not because "\\" is two chars long (it's only
            # one because Python escapes the next one)
            i += 2
        elif line[i] == '|':
            return line[k:i+1], i+1
        else:
            i += 1
    raise SchemeError("unterminated symbol")

def _next_candidate_token(line, k):
    """A tuple (tok, k'), where tok is the next substring of LINE at or
    after position K that could be a token (assuming it passes a validity
    check), and k' is the position in LINE following that token.  Returns
    (None, len(line)) when there are no more tokens."""
    while k < len(line):
        c = line[k]
        if c == ';':  # ";" ends expression
            return None, len(line)
        elif c == '|':
            return _quoted_token(line, k)
        elif c in _WHITESPACE:
            k += 1
        elif c in _DELIM_TOKENS:
            return c, k+1
        elif c == '#':  # return this char and the next - for booleans
            # does not give position of eol char
            return line[k:k+2], min(k+2, len(line))
        else:  # finds character/numeric token, seeks the token's end
            # also for unspecified symbols
            j = k
            while j < len(line) and line[j] not in _TOKEN_END:
                j += 1
            return line[k:j], min(j, len(line))
    # only happens when everything after k in _WHITESPACE
    return None, len(line)

SYMBOL  = 1
NUMERAL = 2
BOOLEAN = 3

def _token_to_string(tok):
    """Given that TOK is the text of a non-standard symbol (minus the enclosing
    '|'s), returns the Python string containing the designated sequence of
    characters, with escape sequences suitably replaced."""
    i = 0
    while i < len(tok):
        if tok.startswith('\\|', i):
            tok = tok[0:i] + tok[i+1:]
        elif tok[i] == '\\':
            i += 1
        elif tok[i] == '"':
            tok = tok[0:i] + '\\' + tok[i:]
            i += 1
        i += 1
    return eval('"' + tok + '"')

def tokenize_line(line):
    """The list of Scheme tokens on LINE.  Excludes comments and whitespace."""
    result = []

    i = 0
    while True:
        try:
            text, i = _next_candidate_token(line, i)

            if text is None:
                break
            if text in _ONECHAR_TOKENS:
                result.append((text, text))
            elif text == '+' or text == '-':
                result.append((SYMBOL, text))
            elif text == '#f' or text == '#t':
                result.append((BOOLEAN, text == '#t'))
            elif text[0] == '|':
                result.append((SYMBOL, _token_to_string(text[1:-1])))
            elif text[0] in _NUMERAL_STARTS:
                try: 
                    result.append((NUMERAL, int(text)))
                except ValueError:
                    try:
                        result.append((NUMERAL, float(text)))
                    except ValueError:
                        raise SchemeError("invalid numeral: '{0}'".format(text))
            elif text[0] in _SYMBOL_STARTS:
                result.append((SYMBOL, text.lower()))
            else:  # catches all improper expressions
                raise SchemeError("invalid token: '{0}'".format(text))
        except SchemeError as exc:
            print("warning: " + exc.args[0], file=sys.stderr)
            print("    ", line, file=sys.stderr)
            print(" " * (i+3), "^", file=sys.stderr)

    return result

def tokenize_lines(input):
    """An iterator that returns lists of tokens, one for each line read from
    the file INPUT."""
    return map(tokenize_line, input)
