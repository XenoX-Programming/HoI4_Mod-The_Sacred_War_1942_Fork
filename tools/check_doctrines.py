#!/usr/bin/env python3
"""
Validate The Sacred War 1942's 1.17+ doctrine tree for internal consistency.

tools/check_mod.py checks braces and duplicate ids. It cannot know that
`track = sw_mw_motorised` must name a *track*, that a grand doctrine needs one
milestone per track, or that a subdoctrine must carry exactly five rewards.
This tool does.

Checks
  1. every grand doctrine names an existing folder and 1..N tracks
  2. every track id referenced by a grand doctrine is defined in
     common/doctrines/tracks/
  3. every subdoctrine's `track =` names a defined track
  4. each track has at least one subdoctrine
  5. each subdoctrine has exactly REWARDS (5) rewards
  6. each grand doctrine has one milestone per track (1.17+ positional rule)
  7. no two subdoctrines on the same track share a name key
  8. every name/description key used by a doctrine exists in the
     English localisation (catches missing or mistyped loc keys)
  9. `visible`/`available` of a subdoctrine reference a doctrine that exists

Usage: python3 tools/check_doctrines.py [--mod-dir the_sacred_war_1942]
Exit code 1 if anything fails.
"""
import argparse
import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pdxparse  # noqa: E402

REWARDS = 5


def load_dir(d):
    """Every TOP-LEVEL block in the folder, i.e. one entry per doctrine/track.

    Only top-level blocks count: a doctrine's inner `available`, `rewards`,
    `category_*` blocks are not definitions and must not be indexed.
    """
    out = {}
    for f in glob.glob(os.path.join(d, "**", "*.txt"), recursive=True):
        for node in pdxparse.parse(open(f, encoding="utf-8-sig", errors="replace").read(), f):
            if node.is_block:
                out.setdefault(node.key, (node, f))
    return out


def list_entries(node):
    """Ids listed bare inside a block such as `tracks = { a b }`.

    pdxparse stores the LAST bare word of a list as a child with op '=', so a
    list of two ids arrives as one child whose key is the first id and whose
    value is the second. Reconstruct the list in order from the raw text raised
    to the node's line, which is unambiguous and does not depend on that quirk.
    """
    if node is None or not node.is_block:
        return []
    with open(node.file, encoding="utf-8-sig", errors="replace") as fh:
        lines = fh.read().split("\n")
    body = []
    buf = []
    depth = 0
    for line in lines[node.line - 1:]:
        code = line.split("#")[0]
        for ch in code:
            if ch == "{":
                depth += 1
                if depth == 1:
                    continue
            if ch == "}":
                depth -= 1
                if depth == 0:
                    return body
            if depth > 0 and (ch.isalnum() or ch == "_"):
                buf.append(ch)
            elif depth > 0 and buf:
                word = "".join(buf)
                body.append(word)
                buf = []
        if depth == 0:
            break
    return body


def load_loc(mdir):
    keys = set()
    for f in glob.glob(os.path.join(mdir, "localisation", "english", "*.yml")):
        raw = open(f, encoding="utf-8-sig", errors="replace").read()
        keys |= set(re.findall(r'(?m)^\s*([A-Za-z0-9_.]+):\d*\s*"', raw))
        keys |= set(re.findall(r"(?m)^\s*([A-Za-z0-9_.]+):\d*\s*$", raw))
    return keys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mod-dir", default="the_sacred_war_1942")
    args = ap.parse_args()
    mdir = args.mod_dir

    gds = load_dir(os.path.join(mdir, "common/doctrines/grand_doctrines"))
    tracks = load_dir(os.path.join(mdir, "common/doctrines/tracks"))
    subs = load_dir(os.path.join(mdir, "common/doctrines/subdoctrines"))
    loc = load_loc(mdir)
    # vanilla loc keys are not shipped by the mod
    vanilla_prefixes = ("GRAND_DOCTRINE_", "SUBDOCTRINE_")

    errors = []

    def err(msg):
        errors.append(msg)

    # 5/3: index subdoctrines by track
    by_track = {}
    for sid, (node, f) in subs.items():
        tr = node.get("track")
        if tr is None:
            err(f"subdoctrine '{sid}' has no track")
            continue
        tr_id = tr.value if not tr.is_block else None
        if tr.is_block:
            for c in list_entries(tr):
                if c not in tracks:
                    err(f"subdoctrine '{sid}' names track '{c}' which is not defined")
                by_track.setdefault(c, []).append(sid)
            continue
        if tr_id not in tracks:
            err(f"subdoctrine '{sid}' names track '{tr_id}' which is not defined")
        by_track.setdefault(tr_id, []).append(sid)

        rw = node.get("rewards")
        n = 0 if rw is None else sum(1 for c in rw.children if c.is_block)
        if n != REWARDS:
            err(f"subdoctrine '{sid}' has {n} rewards, expected {REWARDS}")

        for key in ("name", "description"):
            k = node.get(key)
            if k is None:
                err(f"subdoctrine '{sid}' has no {key}")
                continue
            if k.value not in loc and not k.value.startswith(vanilla_prefixes):
                err(f"subdoctrine '{sid}' {key} key '{k.value}' is missing from localisation")

    # 1/2/6: grand doctrines
    for gid, (node, f) in gds.items():
        folder = node.get("folder")
        if folder is None:
            err(f"grand doctrine '{gid}' has no folder")
        t = node.get("tracks")
        listed = list_entries(t)
        if not listed:
            err(f"grand doctrine '{gid}' lists no tracks")
        for t_id in listed:
            if t_id not in tracks:
                err(f"grand doctrine '{gid}' references undefined track '{t_id}'")
            if t_id not in by_track:
                err(f"track '{t_id}' (in '{gid}') has no subdoctrine")
        ms = node.get("milestones")
        n_ms = 0 if ms is None else sum(1 for c in ms.children if c.is_block)
        if n_ms != len(listed):
            err(f"grand doctrine '{gid}' has {n_ms} milestones for {len(listed)} tracks"
                f" (milestones are positional, one per track)")
        for key in ("name", "description"):
            k = node.get(key)
            if k is None:
                err(f"grand doctrine '{gid}' has no {key}")
            elif k.value not in loc and not k.value.startswith(vanilla_prefixes):
                err(f"grand doctrine '{gid}' {key} '{k.value}' missing from localisation")
        for trig in ("available", "visible"):
            v = node.get(trig)
            if v is not None:
                for hd in v.getall("has_doctrine"):
                    if hd.value not in gds and hd.value not in subs:
                        err(f"grand doctrine '{gid}' {trig} references unknown doctrine"
                            f" '{hd.value}'")

    # 9: subdoctrine gates
    for sid, (node, f) in subs.items():
        for trig in ("available", "visible"):
            v = node.get(trig)
            if v is None:
                continue
            for hd in v.getall("has_doctrine"):
                if hd.value not in gds and hd.value not in subs:
                    err(f"subdoctrine '{sid}' {trig} references unknown doctrine"
                        f" '{hd.value}'")

    print(f"{len(gds)} grand doctrines, {len(tracks)} tracks, {len(subs)} subdoctrines")
    referenced = set()
    for gid, (node, f) in gds.items():
        referenced.update(list_entries(node.get("tracks")))
    for t_id in tracks:
        n = len(by_track.get(t_id, []))
        if n == 0:
            err(f"track '{t_id}' is defined but has no subdoctrine")
        if t_id not in referenced:
            err(f"track '{t_id}' is defined but no grand doctrine lists it,"
                f" so it is unreachable")
    if not tracks:
        err("no tracks found")
    if not gds:
        err("no grand doctrines found")

    if errors:
        print(f"\nERRORS ({len(errors)}):")
        for e in errors:
            print("  " + e)
        return 1
    print("ERRORS: none")
    return 0


if __name__ == "__main__":
    sys.exit(main())
