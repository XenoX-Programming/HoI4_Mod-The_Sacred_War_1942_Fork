#!/usr/bin/env python3
"""Build a copy of the mod with parts of the doctrine port removed.

The game dies on the "creating checksum" screen with no log evidence, so the
only way to find the culprit is to take things away and see what starts working.
This produces ready-to-drop copies of the mod under ``build/`` instead of you
having to hand-edit 34 country files.

Usage::

    python3 tools/bisect_doctrines.py            # build every variant
    python3 tools/bisect_doctrines.py --only A   # build just variant A
    python3 tools/bisect_doctrines.py --list

Each variant is a complete ``the_sacred_war_1942`` folder. To test one, put it in
your ``mod`` folder together with the usual ``.mod`` file and start the game the
same way as before. Record whether it reaches the country-selection screen.

Variants, cheapest-to-read first:

  A  no ``common/doctrines/`` at all, and no doctrine commands in history.
     This is the "does the doctrine system have anything to do with it" test.
  B  ``common/doctrines/`` present, but no doctrine commands in history.
     Isolates the history commands from the definitions.
  C  ``common/doctrines/`` present, history commands present, but
     ``add_mastery`` removed (tier > 1 countries simply start at tier 1).
  D  no ``history/states/`` at all. Tests the duplicate-state/province theory
     separately from doctrines.

If **A** works, the fault is the doctrine system, and B/C say which half.
If **A** still crashes but **D** works, it is the state files.
If neither works, it is something else in the port entirely - and that is
equally useful to know.
"""
import argparse
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOD = os.path.join(ROOT, "Mod", "the_sacred_war_1942")
OUT = os.path.join(ROOT, "build")

DOCTRINE_DIRS = [
    "common/doctrines/grand_doctrines",
    "common/doctrines/tracks",
    "common/doctrines/subdoctrines",
]

# The converter writes these as a contiguous header block, then a blank line.
DOCTRINE_CMD = re.compile(
    r"^\s*(set_grand_doctrine|set_sub_doctrine|add_mastery)\s*=.*$")


def strip_doctrine_commands(text, drop_mastery=False):
    """Remove doctrine history commands, and our explanatory header with them."""
    out, removed = [], 0
    in_header = False
    for line in text.split("\n"):
        if line.startswith("# The Sacred War 1942 land doctrine"):
            in_header, removed = True, removed + 1
            continue
        if in_header and line.startswith("#"):
            continue
        if in_header and line.strip() == "":
            in_header = False
            continue
        in_header = False
        if DOCTRINE_CMD.match(line):
            if drop_mastery and not line.strip().startswith("add_mastery"):
                out.append(line)          # keep set_grand/set_sub_doctrine
                continue
            removed += 1
            continue
        out.append(line)
    # collapse the blank line the header left behind
    while out and out[0].strip() == "":
        out.pop(0)
    return "\n".join(out), removed


def copy_mod(dest):
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    shutil.copytree(MOD, dest)
    return dest


def variant_a(dest):
    """No doctrines at all."""
    copy_mod(dest)
    for d in DOCTRINE_DIRS:
        p = os.path.join(dest, d)
        if os.path.isdir(p):
            shutil.rmtree(p)
    root = os.path.join(dest, "common", "doctrines")
    if os.path.isdir(root) and not os.listdir(root):
        os.rmdir(root)
    n = 0
    for base, _dirs, files in os.walk(os.path.join(dest, "history")):
        for f in files:
            if not f.endswith(".txt"):
                continue
            p = os.path.join(base, f)
            blob = open(p, "rb").read()
            bom = blob.startswith(b"\xef\xbb\xbf")
            text = blob.decode("utf-8-sig", errors="replace")
            new, removed = strip_doctrine_commands(text)
            if removed:
                enc = "utf-8-sig" if bom else "utf-8"
                open(p, "w", encoding=enc, newline="").write(new)
                n += removed
    return f"removed common/doctrines/ and {n} doctrine history commands"


def variant_b(dest):
    """Definitions present, no history commands."""
    copy_mod(dest)
    n = 0
    for base, _dirs, files in os.walk(os.path.join(dest, "history")):
        for f in files:
            if not f.endswith(".txt"):
                continue
            p = os.path.join(base, f)
            blob = open(p, "rb").read()
            bom = blob.startswith(b"\xef\xbb\xbf")
            text = blob.decode("utf-8-sig", errors="replace")
            new, removed = strip_doctrine_commands(text)
            if removed:
                enc = "utf-8-sig" if bom else "utf-8"
                open(p, "w", encoding=enc, newline="").write(new)
                n += removed
    return f"removed {n} doctrine history commands, kept common/doctrines/"


def variant_c(dest):
    """Everything, minus add_mastery."""
    copy_mod(dest)
    n = 0
    for base, _dirs, files in os.walk(os.path.join(dest, "history")):
        for f in files:
            if not f.endswith(".txt"):
                continue
            p = os.path.join(base, f)
            blob = open(p, "rb").read()
            bom = blob.startswith(b"\xef\xbb\xbf")
            text = blob.decode("utf-8-sig", errors="replace")
            new, removed = strip_doctrine_commands(text, drop_mastery=True)
            if removed:
                enc = "utf-8-sig" if bom else "utf-8"
                open(p, "w", encoding=enc, newline="").write(new)
                n += removed
    return f"removed {n} add_mastery lines, kept set_*_doctrine"


def variant_d(dest):
    """No state history at all."""
    copy_mod(dest)
    p = os.path.join(dest, "history", "states")
    n = len(os.listdir(p)) if os.path.isdir(p) else 0
    if os.path.isdir(p):
        shutil.rmtree(p)
    return f"removed history/states/ ({n} files)"


VARIANTS = {
    "A": ("A-no-doctrines", variant_a),
    "B": ("B-doctrines-no-history", variant_b),
    "C": ("C-no-add-mastery", variant_c),
    "D": ("D-no-state-history", variant_d),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=sorted(VARIANTS), action="append",
                    help="build only this variant (repeatable)")
    ap.add_argument("--list", action="store_true", help="list variants and exit")
    args = ap.parse_args()

    if args.list:
        for k, (name, fn) in sorted(VARIANTS.items()):
            print(f"  {k}  {name:26s} {fn.__doc__.strip().splitlines()[0]}")
        return 0

    if not os.path.isdir(MOD):
        print(f"error: {MOD} not found; run from the repository root", file=sys.stderr)
        return 1

    keys = args.only or sorted(VARIANTS)
    os.makedirs(OUT, exist_ok=True)
    for k in keys:
        name, fn = VARIANTS[k]
        dest = os.path.join(OUT, name, "the_sacred_war_1942")
        what = fn(dest)
        print(f"{k}  {name}")
        print(f"   {what}")
        print(f"   -> {os.path.relpath(dest, ROOT)}")
    print()
    print("Copy a variant folder into your mod folder as 'the_sacred_war_1942',")
    print("next to 'The Sacred War - 1942.mod', then start the game.")
    print("build/ is git-ignored; delete it whenever you like.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
