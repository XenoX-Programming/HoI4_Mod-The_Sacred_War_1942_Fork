#!/usr/bin/env python3
"""
Convert The Sacred War 1942's land doctrines from the old technology tree to the
HoI4 1.17+ grand-doctrine / subdoctrine / mastery system.

Verified against working 1.17+ mods (CWIC, EaW) the operational effects are:

    set_grand_doctrine = <grand_doctrine_id>     # takes the GD
    set_sub_doctrine   = <subdoctrine_id>        # takes that track's tier 1
    add_mastery = { amount = N sub_doctrine = <id> }   # N/100 -> tier 1+N

Mastery is the *only* way to advance a track: 100 mastery per reward, 500
completes the track (five rewards).  A country therefore reproduces its old
tech count by taking the subdoctrine and then buying tiers with mastery.

What this tool does:

  * finds every `<old_doctrine_tech> = 1` line that lives inside a
    `set_technology = { ... }` block (in history/countries/*.txt and in
    common/scripted_effects/sacred_war_effects.txt),
  * deletes those lines (the techs no longer exist),
  * drops the now-empty `set_technology = { }` block,
  * appends the equivalent `set_grand_doctrine` / `set_sub_doctrine` /
    `add_mastery` commands after the outermost block it edited,
  * rewrites `has_tech = <old_doctrine_tech>` triggers into
    `has_doctrine = <grand_doctrine>`.

Everything else in the file is left byte-identical.  Idempotent: once converted
there are no doctrine tech lines left, so a second run is a no-op.

Usage:
    python3 tools/convert_history_doctrines.py [--mod-dir the_sacred_war_1942] [--apply]
"""
import argparse
import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import doctrine_map as M  # noqa: E402

GRANT = re.compile(r"^\s*([a-z_0-9]+)\s*=\s*[1-9]\s*$")


def strip_comment(line):
    return line.split("#")[0]


def brace_delta(line):
    code = strip_comment(line)
    return code.count("{") - code.count("}")


def find_blocks(lines, opener_re):
    """Yield (start, end) line indexes of blocks whose header matches opener_re."""
    out = []
    i = 0
    while i < len(lines):
        if opener_re.search(lines[i]) and strip_comment(lines[i]).count("{"):
            depth = 0
            for j in range(i, len(lines)):
                depth += brace_delta(lines[j])
                if depth == 0 and j > i:
                    out.append((i, j))
                    i = j
                    break
                if depth == 0 and j == i and "}" in strip_comment(lines[j]):
                    out.append((i, j))
                    i = j
                    break
            else:
                break
        i += 1
    return out


def top_level_units(lines):
    """Vertical spans of every depth-0 block in the file."""
    units = []
    depth = 0
    start = None
    for j, l in enumerate(lines):
        delta = brace_delta(l)
        if depth == 0 and "{" in strip_comment(l):
            start = j
        depth += delta
        if depth == 0 and start is not None:
            units.append((start, j))
            start = None
    return units


def indent_of(line):
    return re.match(r"\s*", line).group(0)


def doctrine_commands(school_id, tiers):
    """Build the command lines for a school + [(track, tier), ...]."""
    out = [f"set_grand_doctrine = {school_id}"]
    for track_id, tier in tiers:
        if tier < 1:
            continue
        out.append(f"set_sub_doctrine = {track_id}")
        amount = M.mastery_for_tier(tier)
        if amount:
            out.append(f"add_mastery = {{ amount = {amount} sub_doctrine = {track_id} }}")
    return out


def analyse(granted):
    """granted set of old tech ids -> (school_id, [(track_id, tier), ...])."""
    schools = {}
    for t in granted:
        sch = M.tech_to_school().get(t)
        if sch:
            schools[sch] = schools.get(sch, 0) + 1
    if not schools:
        return None
    school_id = max(schools, key=lambda k: (schools[k], k))
    school = next(s for s in M.SCHOOLS if s["id"] == school_id)
    tiers = [(tr["id"], M.tier_of(granted, tr)) for tr in school["tracks"]]
    return school_id, tiers


def convert_text(text, tech_index, fname, log, hoist):
    """Remove the old doctrine tech grants and emit the new doctrine commands.

    Two shapes are produced, matching what working 1.17+ mods do:

    hoist=True  (country history files, which must start with `capital`, `oob`,
                `set_technology`, ...): the doctrine commands are gathered and
                written once, after the initial `set_technology` block. This is
                exactly how EaW and 1956 do it, e.g.

                    set_technology = { ... }
                    set_grand_doctrine = mass_assault

                A country cannot take two grand doctrines, so a second school
                found in the same file is dropped with a warning in the log.

    hoist=False (scripted effects, where each effect must stay self-contained):
                the commands are written in place of the emptied
                `set_technology` block, at the same indentation, so they run
                inside the same `if` / effect scope as before.
    """
    lines = text.split("\n")
    blocks = find_blocks(lines, re.compile(r"set_technology\s*="))

    remove = set()
    edits = []            # (end_line_index, [payload lines])
    changed = False
    per_school = {}       # school -> {track: max tier}
    hoisted_extra = []    # naval / air / special-forces commands to hoist too
    # hoisted_extra may legitimately contain repeats (each repeat buys a tier)

    for s, e in blocks:
        grants = []
        for j in range(s + 1, e):
            m = GRANT.match(strip_comment(lines[j]))
            if m and m.group(1) in tech_index:
                grants.append((j, m.group(1)))
        if not grants:
            continue
        granted = {t for _j, t in grants}
        other_cmds, dead = M.other_doctrine_commands(granted)
        res = analyse(granted)
        if res is None and not other_cmds and not dead:
            continue
        changed = True
        if res is None:
            # only air / naval / special-forces doctrines and dead techs here
            school_id, tiers, cmds = None, [], list(other_cmds)
        else:
            school_id, tiers = res
            cmds = doctrine_commands(school_id, tiers) + other_cmds
        for d in dead:
            log.append(f"      dropped removed tech {d} (no safe 1.20 replacement)")

        left = [k for k in range(s + 1, e)
                if k not in {j for j, _t in grants} and strip_comment(lines[k]).strip()]
        removed = sorted(granted)

        log.append(f"{fname}: {len(granted)} old techs -> {school_id}")
        log.append(f"      removed: {', '.join(removed)}")

        if hoist:
            # the tech grants are gone either way; only the emission point differs
            remove.update(j for j, _t in grants)
            hoisted_extra.extend(other_cmds)
            if school_id is None:
                continue
            bucket = per_school.setdefault(school_id, {})
            for track_id, tier in tiers:
                bucket[track_id] = max(bucket.get(track_id, 0), tier)
        else:
            pad = indent_of(lines[s])
            payload = ["",
                       pad + "# The Sacred War 1942 land doctrine (HoI4 1.17+ system),",
                       pad + "# converted from the old technology tree:",
                       pad + "#   " + ", ".join(removed)]
            payload += [pad + c for c in cmds]
            if not left:
                for k in range(s, e + 1):
                    remove.add(k)
                edits.append((e, payload))
                log.append("      replaced an emptied set_technology block")
            else:
                remove.update(j for j, _t in grants)
                last = max(left)
                edits.append((last, payload))
                log.append("      kept the block (other technologies remain)")
            for c in cmds:
                log.append(f"      + {c}")

    if not changed:
        return text, None

    if hoist:
        if not per_school and not hoisted_extra:
            return text, None
        # keep the largest school if a file somehow grants two
        if len(per_school) > 1:
            keep = max(per_school, key=lambda k: sum(per_school[k].values()))
            for other in per_school:
                if other != keep:
                    log.append(f"      WARNING {fname}: also found {other}; "
                               f"dropped because a country takes one grand doctrine")
            per_school = {keep: per_school[keep]}
        school_id, bucket = next(iter(per_school.items())) if per_school else (None, {})
        cmds = (M.split_commands_for_history(school_id, sorted(bucket.items()))
                if school_id else []) + hoisted_extra
        cmds = M.one_per_folder(cmds, log, fname)
        payload = ["",
                   "# The Sacred War 1942 land doctrine, HoI4 1.17+ system.",
                   "# Converted from the old technology tree by",
                   "# tools/convert_history_doctrines.py. Old doctrine technologies:",
                   "#   " + ", ".join(sorted({t for j, t in
                                             [(0, x) for x in []] })) or ""]
        payload = ["",
                   "# The Sacred War 1942 land doctrine, HoI4 1.17+ system (converted",
                   "# from the old technology tree by tools/convert_history_doctrines.py).",
                   "# set_sub_doctrine is repeated once per tier of the track the country",
                   "# used to have; each further tier costs 100 mastery in game."]
        payload += cmds
        # Insert at top level, in the file's header of simple commands (after
        # `capital`, `oob`, the first set_technology, ...), which is where EaW
        # and 1956 put their doctrine commands. Everything after the first
        # top-level `if`, `else` or dated block is left alone.
        header_end = len(lines)
        d = 0
        for j, l in enumerate(lines):
            if d == 0 and re.match(r"(if\s*=|else\s*=|\d{4}\.\d)", strip_comment(l).strip()):
                header_end = j
                break
            d += brace_delta(l)
        anchor = 0
        d = 0
        for j in range(header_end):
            code = strip_comment(lines[j]).strip()
            if d == 0 and code and not code.endswith("{") and "=" in code:
                anchor = j
            d += brace_delta(lines[j])
        edits.append((anchor, payload))
        for c in cmds:
            log.append(f"      + {c}")

    out = []
    edits_by_line = {}
    for after, payload in edits:
        edits_by_line.setdefault(after, []).extend(payload)
    for j, l in enumerate(lines):
        if j in edits_by_line:
            out.extend(edits_by_line[j])
        if j not in remove:
            out.append(l)
    if len(lines) in edits_by_line:
        out.extend(edits_by_line[len(lines)])
    return "\n".join(out), None


HAS_TECH = re.compile(r"has_tech\s*=\s*([a-z_0-9]+)")


def convert_has_tech(text, tech_index, log, fname):
    def sub(m):
        old = m.group(1)
        if old not in tech_index:
            return m.group(0)
        sch = M.tech_to_school().get(old)
        if not sch:
            return m.group(0)
        log.append(f"{fname}: has_tech = {old} -> has_doctrine = {sch}")
        return f"has_doctrine = {sch}"
    return HAS_TECH.sub(sub, text)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mod-dir", default="the_sacred_war_1942")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--report", default="tools/doctrine_conversion_report.txt")
    args = ap.parse_args()
    mod = args.mod_dir

    # every tech id this migration may have to touch: the mod's old land
    # doctrine tree, the naval/air/special-forces doctrines vanilla replaced,
    # and the handful of techs 1.17+ deleted outright.
    tech_index = {}
    for t in sorted(M.all_old_techs() | set(M.DOCTRINE_TECHS_OTHER) | M.DEAD_TECHS):
        tech_index[t] = t

    targets = sorted(glob.glob(os.path.join(mod, "history", "countries", "*.txt")))
    targets += sorted(glob.glob(os.path.join(mod, "common", "scripted_effects", "*.txt")))
    targets += sorted(glob.glob(os.path.join(mod, "common", "ideas", "*.txt")))
    targets += sorted(glob.glob(os.path.join(mod, "common", "national_focus", "*.txt")))
    targets += sorted(glob.glob(os.path.join(mod, "events", "*.txt")))
    targets += sorted(glob.glob(os.path.join(mod, "common", "decisions", "**", "*.txt"),
                                 recursive=True))

    log = []
    n_files = 0
    for path in targets:
        raw = open(path, encoding="utf-8-sig", errors="replace").read()
        fname = os.path.relpath(path, mod)
        hoist = '/history/' in path.replace(os.sep, '/')
        new, _s = convert_text(raw, tech_index, fname, log, hoist)
        new = convert_has_tech(new, tech_index, log, fname)
        if new != raw:
            n_files += 1
            if args.apply:
                with open(path, "w", encoding="utf-8-sig", newline="") as fh:
                    fh.write(new)

    head = [
        "The Sacred War 1942 - land doctrine conversion report",
        "=" * 70,
        f"mode: {'APPLY' if args.apply else 'DRY RUN'}",
        f"files changed: {n_files}",
        "",
    ]
    with open(args.report, "w", encoding="utf-8") as fh:
        fh.write("\n".join(head + log) + "\n")
    print("\n".join(head + log))


if __name__ == "__main__":
    main()
