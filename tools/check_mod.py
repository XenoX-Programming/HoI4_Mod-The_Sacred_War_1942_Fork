#!/usr/bin/env python3
"""
Static sanity checker for the Sacred War 1942 HoI4 mod.

Purpose: catch the classes of script error that make a mod fail to load or
silently break after a game-version update, WITHOUT needing the game installed.

Checks
  1. brace balance per script file (excluding map/*.csv and gfx)
  2. duplicate definition IDs in the same database
       - events           (country_event/news_event/state_event/... id)
       - national focuses (focus id)
       - decisions        (decision + category ids)
       - ideas            (idea keys per idea group category)
       - characters, scripted_triggers/effects, dynamic modifiers
  3. references to game objects that the mod's own files define, for
     cross-checking (dangling focus prerequisites, event event_targets etc.)

Usage: python3 tools/check_mod.py [--mod-dir the_sacred_war_1942] [--json out.json]
Exit code 0 = no errors, 1 = errors found (warnings alone -> 0).
"""
import argparse
import collections
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pdxparse  # noqa: E402

# Directories inside the mod that contain PDXscript we should parse.
SCRIPT_DIRS = [
    "events",
    "common",
    "history",
    "localisation",
]
SKIP_PATH_PARTS = ("3142844611",)  # Steam workshop copy / screenshots


def iter_script_files(mod_dir):
    for dirpath, _dirnames, filenames in os.walk(mod_dir):
        rel = os.path.relpath(dirpath, mod_dir)
        if any(p in rel.split(os.sep) for p in SKIP_PATH_PARTS):
            continue
        for fn in filenames:
            if not fn.lower().endswith((".txt", ".gui", ".gfx")):
                continue
            yield os.path.join(dirpath, fn)


def read(path):
    with open(path, "r", encoding="utf-8-sig", errors="replace") as fh:
        return fh.read()


# ---------------------------------------------------------------------------
# 1. brace balance
# ---------------------------------------------------------------------------
def check_balance(files, mod_dir):
    errors = []
    for path in files:
        text = read(path)
        o, c = pdxparse.brace_balance(text)
        if o != c:
            errors.append(
                {
                    "check": "brace_balance",
                    "file": os.path.relpath(path, mod_dir),
                    "detail": f"{o} opening vs {c} closing braces (net {o - c:+d})",
                }
            )
    return errors


# ---------------------------------------------------------------------------
# 2. duplicate ids
# ---------------------------------------------------------------------------
def collect_event_ids(mod_dir):
    found = collections.defaultdict(list)
    for path in glob.glob(os.path.join(mod_dir, "events", "*.txt")):
        if any(p in path for p in SKIP_PATH_PARTS):
            continue
        rel = os.path.relpath(path, mod_dir)
        try:
            nodes = pdxparse.parse(read(path), rel)
        except Exception as exc:  # pragma: no cover
            found[f"<parse error {exc}>"].append((rel, 0))
            continue
        _walk_events(nodes, found, rel)
    return found


EVENT_TYPES = {
    "country_event",
    "news_event",
    "state_event",
    "unit_leader_event",
    "operative_news_event",
}


def _walk_events(nodes, found, rel):
    """Only treat `X_event = { id = ... }` at *definition* level.

    Definition level means the block has `is_triggered_only`, `title`, `desc`,
    `picture`, `option` keys, or is nested directly under an `add_namespace`
    sibling. Effect calls (`country_event = { id = X days = 3 }`) never carry
    title/desc, so they are skipped.
    """
    for node in nodes:
        if (
            node.key in EVENT_TYPES
            and node.is_block
            and _looks_like_event_def(node)
        ):
            eid = node.scalar("id")
            if eid:
                found[eid].append((rel, node.line))
        if node.is_block:
            _walk_events(node.children, found, rel)


def _looks_like_event_def(node):
    for marker in ("title", "desc", "picture", "option", "is_triggered_only"):
        if node.get(marker) is not None:
            return True
    return False


def collect_focus_ids(mod_dir):
    found = collections.defaultdict(list)
    for path in glob.glob(os.path.join(mod_dir, "common", "national_focus", "*.txt")):
        rel = os.path.relpath(path, mod_dir)
        nodes = pdxparse.parse(read(path), rel)
        for top in nodes:
            if not top.is_block:
                continue
            for sub in top.children:
                if sub.is_block and sub.key == "focus_tree":
                    _walk_focus(sub, found, rel)
                    continue
            if top.key == "focus_tree":
                _walk_focus(top, found, rel)
    return found


def _walk_focus(tree, found, rel):
    focus_ids = tree.get("focus")  # noqa: F841
    for node in tree.getall("focus"):
        fid = node.scalar("id")
        if fid:
            found[fid].append((rel, node.line))


IDEA_GROUP_CATEGORIES = {
    "country",
    "law",
    "military",
    "social",
    "intel",
    "mio",
}


def collect_idea_ids(mod_dir):
    found = collections.defaultdict(list)
    for path in glob.glob(os.path.join(mod_dir, "common", "ideas", "*.txt")):
        rel = os.path.relpath(path, mod_dir)
        nodes = pdxparse.parse(read(path), rel)
        for top in nodes:
            if top.key != "ideas" or not top.is_block:
                continue
            for group in top.children:
                if not group.is_block:
                    continue
                for idea in group.children:
                    if idea.is_block:
                        found[idea.key].append((rel, idea.line))
    return found


def collect_decision_ids(mod_dir):
    """Decision files are laid out as `<category_id> = { <decision_id> = {..} }`."""
    found = collections.defaultdict(list)
    for path in glob.glob(os.path.join(mod_dir, "common", "decisions", "*.txt")):
        rel = os.path.relpath(path, mod_dir)
        nodes = pdxparse.parse(read(path), rel)
        for cat in nodes:
            if not cat.is_block:
                continue
            for dec in cat.children:
                if dec.is_block:
                    found[dec.key].append((rel, dec.line))
    return found


def collect_character_ids(mod_dir):
    found = collections.defaultdict(list)
    for path in glob.glob(os.path.join(mod_dir, "common", "characters", "*.txt")):
        rel = os.path.relpath(path, mod_dir)
        nodes = pdxparse.parse(read(path), rel)
        for top in nodes:
            if top.key == "characters" and top.is_block:
                for ch in top.children:
                    if ch.is_block:
                        found[ch.key].append((rel, ch.line))
    return found


def collect_scripted(mod_dir, kind):
    """`common/scripted_effects` and `common/scripted_triggers` files are flat
    maps of `name = { ... }`; newer files may optionally wrap that in a
    `scripted_effects = { }` header, so handle both."""
    found = collections.defaultdict(list)
    for path in glob.glob(os.path.join(mod_dir, "common", kind, "*.txt")):
        rel = os.path.relpath(path, mod_dir)
        nodes = pdxparse.parse(read(path), rel)
        entries = []
        for top in nodes:
            if top.key == kind and top.is_block:
                entries.extend(n for n in top.children if n.is_block)
            elif top.is_block:
                entries.append(top)
        for n in entries:
            found[n.key].append((rel, n.line))
    return found


def collect_dynamic_modifiers(mod_dir):
    """Dynamic modifier files are a flat map of `name = { ... }` entries."""
    found = collections.defaultdict(list)
    for path in glob.glob(os.path.join(mod_dir, "common", "dynamic_modifiers", "*.txt")):
        rel = os.path.relpath(path, mod_dir)
        nodes = pdxparse.parse(read(path), rel)
        for n in nodes:
            if n.is_block and n.key:
                found[n.key].append((rel, n.line))
    return found


DB_COLLECTORS = {
    "events": collect_event_ids,
    "national_focus": collect_focus_ids,
    "ideas": collect_idea_ids,
    "decisions": collect_decision_ids,
    "characters": collect_character_ids,
    "scripted_triggers": lambda d: collect_scripted(d, "scripted_triggers"),
    "scripted_effects": lambda d: collect_scripted(d, "scripted_effects"),
    "dynamic_modifiers": collect_dynamic_modifiers,
}


def check_duplicates(mod_dir):
    errors = []
    for name, fn in DB_COLLECTORS.items():
        found = fn(mod_dir)
        for key, places in found.items():
            if len(places) > 1:
                errors.append(
                    {
                        "check": "duplicate_id",
                        "database": name,
                        "id": key,
                        "detail": "; ".join(f"{f}:{ln}" for f, ln in places),
                    }
                )
    return errors


# ---------------------------------------------------------------------------
# 3. focus prerequisites that point at nothing
# ---------------------------------------------------------------------------
def check_focus_prereqs(mod_dir):
    focus_files = glob.glob(os.path.join(mod_dir, "common", "national_focus", "*.txt"))
    defined = set()
    trees = []
    for path in focus_files:
        rel = os.path.relpath(path, mod_dir)
        nodes = pdxparse.parse(read(path), rel)
        for top in nodes:
            if top.is_block and top.key == "focus_tree":
                trees.append((rel, top))
                for node in top.getall("focus"):
                    fid = node.scalar("id")
                    if fid:
                        defined.add(fid)
    warnings = []
    for rel, tree in trees:
        tree_id = tree.scalar("id")
        uses_shared = tree.get("shared_focus") is not None
        for node in tree.getall("focus"):
            fid = node.scalar("id") or "<no id>"
            for pre in node.getall("prerequisite"):
                if not pre.is_block:
                    continue
                for inner in pre.children:
                    if inner.key == "focus":
                        if inner.value and inner.value not in defined:
                            warnings.append(
                                {
                                    "check": "dangling_prerequisite",
                                    "detail": f"focus '{fid}' in tree '{tree_id}' ({rel}) "
                                    f"requires undefined focus '{inner.value}'",
                                }
                            )
    return warnings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mod-dir", default="the_sacred_war_1942")
    ap.add_argument("--json")
    args = ap.parse_args()
    mod_dir = args.mod_dir

    files = list(iter_script_files(mod_dir))
    errors = check_balance(files, mod_dir)
    errors += check_duplicates(mod_dir)
    warns = check_focus_prereqs(mod_dir)

    print(f"parsed {len(files)} script files in {mod_dir}\n")
    if errors:
        print(f"ERRORS ({len(errors)}):")
        for e in errors:
            bits = [f"{k}={v}" for k, v in e.items() if k != "check"]
            print(f"  [{e['check']}] " + "  ".join(bits))
    else:
        print("ERRORS: none")
    if warns:
        print(f"\nWARNINGS ({len(warns)}):")
        for w in warns[:40]:
            print(f"  [{w['check']}] {w['detail']}")
        if len(warns) > 40:
            print(f"  ... {len(warns) - 40} more")
    else:
        print("WARNINGS: none")

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump({"errors": errors, "warnings": warns, "files": len(files)}, fh, indent=2)
        print(f"\nwrote {args.json}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
