"""
Minimal Paradox-script (PDXscript) tokenizer + block-tree builder for Hearts of Iron IV files.

Only what is needed for static checks: comments, quoted strings, operators, braces.
Produces a tree of nodes so callers can locate definitions reliably instead of
regex-matching text (which produces false positives on effect calls like
`country_event = { id = X hours = 1 }`).
"""
import re


class Node:
    __slots__ = ("key", "op", "value", "children", "line", "file")

    def __init__(self, key, op, value, line, file):
        self.key = key
        self.op = op
        self.value = value
        self.children = None  # list[Node] when the value was a block
        self.line = line
        self.file = file

    # -- helpers -------------------------------------------------------
    @property
    def is_block(self):
        return self.children is not None

    def get(self, key):
        for c in self.children or ():
            if c.key == key:
                return c
        return None

    def getall(self, key):
        return [c for c in (self.children or ()) if c.key == key]

    def scalar(self, key, default=None):
        c = self.get(key)
        if c is None or c.is_block:
            return default
        return c.value

    def __repr__(self):
        return f"<Node {self.key} {self.op} {'{...}' if self.is_block else self.value!r} @{self.file}:{self.line}>"


TOKEN_RE = re.compile(
    r"""
      (?P<ws>[ \t\r]+)
    | (?P<nl>\n)
    | (?P<comment>\#[^\n]*)
    | (?P<string>"[^"\n]*")
    | (?P<op>[<>=!?]+)
    | (?P<lbrace>\{)
    | (?P<rbrace>\})
    | (?P<word>[^\s{}=#<>"!]+)
    """,
    re.VERBOSE,
)


def tokenize(text, filename, line_offset=0):
    """Yield (kind, value, line). kind in {'word','string','op','{','}'}."""
    line = 1 + line_offset
    pos = 0
    n = len(text)
    while pos < n:
        m = TOKEN_RE.match(text, pos)
        if not m:
            # unexpected character - skip it so a malformed file still parses
            pos += 1
            continue
        pos = m.end()
        kind = m.lastgroup
        val = m.group()
        if kind == "nl":
            line += 1
            continue
        if kind in ("ws", "comment"):
            continue
        if kind == "string":
            yield ("string", val[1:-1], line)
        elif kind == "lbrace":
            yield ("{", "{", line)
        elif kind == "rbrace":
            yield ("}", "}", line)
        elif kind == "op":
            yield ("op", val, line)
        else:
            yield ("word", val, line)


def parse(text, filename="<string>"):
    """Parse a PDXscript file into a list of top-level Nodes."""
    root = Node(None, None, None, 0, filename)
    root.children = []
    stack = [root]
    pending = None  # Node awaiting a value
    for kind, val, line in tokenize(text, filename):
        cur = stack[-1]
        if kind in ("word", "string"):
            if pending is not None:
                # `key = value` -- value may be a bare word/string or a list of words
                if pending.value is None and not pending.is_block:
                    pending.value = val
                else:
                    pending.value = (pending.value or "") + " " + val
                pending.op = "="
                cur.children.append(pending)
                pending = None
            else:
                pending = Node(val, None, None, line, filename)
        elif kind == "op":
            if pending is None:
                pending = Node(None, val, None, line, filename)
            else:
                pending.op = val
        elif kind == "{":
            if pending is None:
                pending = Node(None, None, None, line, filename)
            node = pending
            node.children = []
            node.op = node.op or "="
            cur.children.append(node)
            stack.append(node)
            pending = None
        elif kind == "}":
            if pending is not None:
                cur.children.append(pending)
                pending = None
            if len(stack) > 1:
                stack.pop()
            # else: stray '}' at top level -> ignore (recorded by balance check)
    if pending is not None:
        stack[-1].children.append(pending)
    return root.children


def brace_balance(text):
    """Return (open_braces, close_braces) ignoring comments and quoted strings."""
    o = c = 0
    for kind, _val, _line in tokenize(text, "<bal>"):
        if kind == "{":
            o += 1
        elif kind == "}":
            c += 1
    return o, c
