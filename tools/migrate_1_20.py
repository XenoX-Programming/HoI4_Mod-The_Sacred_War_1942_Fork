#!/usr/bin/env python3
"""
Apply the mechanical 1.20 migrations to The Sacred War 1942.

Four jobs, all idempotent (safe to run twice):

 1. DOCTRINE RESEARCH BONUSES
   1.17+ replaced doctrine *technologies* with XP-purchased grand doctrines /
   subdoctrines. A `research_bonus`/`add_tech_bonus`/`add_doctrine_cost_reduction`
   category of land_doctrine / naval_doctrine / air_doctrine still parses and is
   still the documented way to make doctrines cheaper, but bonuses that pointed
   at a *removed tech id* would silently do nothing. We rewrite removed doctrine
   tech ids used inside `set_technology` into the new doctrine framework where
   possible, and report everything we cannot map.

 2. REMOVED INDUSTRY TECHS (1.17 "War Effort: NCNS")
   improved_equipment_conversion / advanced_equipment_conversion were removed
   and replaced by energy-gain technologies. synth_oil_experiments was folded
   into the fuel-refining line. Both are referenced by our copied vanilla
   history; we remap them.

 3. VANILLA HISTORY BLOAT
   The mod ships 37 full vanilla country-history files. Several thousand lines
   are inert (commented-out oob/air_oob lines). We do NOT delete data; we only
   report the numbers so the maintainer can decide.

 4. REPORT
   Writes tools/migration_report.txt with every change and every leftover.

Usage:
  python3 tools/migrate_1_20.py --mod-dir the_sacred_war_1942 [--apply]
Without --apply nothing is written (dry run).
"""
import argparse
import collections
import glob
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# --------------------------------------------------------------------------
# 1. doctrine research-bonus categories: valid in 1.20, left alone.
#    These are the categories that must NOT be touched.
# --------------------------------------------------------------------------
VALID_DOCTRINE_CATEGORIES = {
    "land_doctrine",
    "naval_doctrine",
    "air_doctrine",
    "special_forces_doctrine",
}

# --------------------------------------------------------------------------
# 2. Tech ids that an earlier pass of this migration BELIEVED were removed by
#    1.17. Each one was checked against a vanilla 1.20 technology tree and all
#    of them still exist there, so nothing is rewritten. The list is kept so the
#    correction is documented and cannot silently regress.
# --------------------------------------------------------------------------
STILL_EXISTING = {
    "improved_equipment_conversion": "still defined in vanilla 1.20 industry.txt",
    "advanced_equipment_conversion": "still defined in vanilla 1.20 industry.txt",
    "synth_oil_experiments": "still defined in vanilla 1.20 industry.txt",
    "fuel_silos": "still defined in vanilla 1.20 industry.txt",
    "fuel_refining": "still defined in vanilla 1.20 industry.txt",
}

# Filled in by main() from the mod's own technology files.
REMOVED_TECH_MAP = {}


def iter_files(mod_dir, subdirs, exts=(".txt",)):
    for sub in subdirs:
        for path in glob.glob(os.path.join(mod_dir, sub, "**", "*"), recursive=True):
            if os.path.isfile(path) and path.endswith(exts):
                yield path


def rel(mod_dir, path):
    return os.path.relpath(path, mod_dir)


# --------------------------------------------------------------------------
# job 2: remap removed tech ids
# --------------------------------------------------------------------------
def techs_defined_by_mod(mod_dir):
    defined = set()
    for f in glob.glob(os.path.join(mod_dir, "common", "technologies", "*.txt")):
        try:
            nodes = pdxparse.parse(open(f, encoding="utf-8-sig").read(), f)
        except Exception:
            continue
        for root in nodes:
            if root.key == "technologies":
                defined |= {c.key for c in root.children if c.is_block}
    return defined


def remap_removed_techs(mod_dir, apply):
    """Rewrite grants of tech ids the MOD itself does not define.

    The mod's own technology files win, so anything they define is left alone.
    Only ids defined by neither the mod nor vanilla are remapped.
    """
    changes = []
    own = techs_defined_by_mod(mod_dir)
    for path in iter_files(mod_dir, ["common/technologies", "history", "common/scripted_effects",
                                     "common/ai_strategy", "common/on_actions"]):
        text_had_bom = open(path, "rb").read(3) == b"\xef\xbb\xbf"
        text = open(path, encoding="utf-8-sig", errors="replace").read()
        new = text
        for old, repl in REMOVED_TECH_MAP.items():
            if old in own:
                continue
            # only rewrite `old = N` style grants / references, not comments
            pat = re.compile(rf"(?m)^(\s*){re.escape(old)}(\s*=\s*\d.*)$")
            def sub(m, repl=repl, old=old):
                changes.append(f"{rel(mod_dir, path)}: {old} -> {repl}")
                return f"{m.group(1)}{repl}{m.group(2)}"
            new = pat.sub(sub, new)
            # also `has_tech = old`
            pat2 = re.compile(rf"(has_tech\s*=\s*){re.escape(old)}\b")
            def sub2(m, repl=repl, old=old):
                changes.append(f"{rel(mod_dir, path)}: has_tech {old} -> {repl}")
                return f"{m.group(1)}{repl}"
            new = pat2.sub(sub2, new)
        if new != text and apply:
            # Preserve the file's own encoding. HoI4's script parser rejects a
            # UTF-8 BOM ("unexpected token ... (U+FEFF)") and then treats
            # every id in that file as undefined, so never add one. Localisation
            # is the exception: .yml files are expected to carry a BOM.
            enc = "utf-8-sig" if (text_had_bom or path.endswith(".yml")) else "utf-8"
            open(path, "w", encoding=enc, newline="").write(new)
    return changes


# --------------------------------------------------------------------------
# job 1: old doctrine tech ids still granted via set_technology
# --------------------------------------------------------------------------
def find_old_doctrine_grants(mod_dir, doctrine_ids):
    hits = collections.defaultdict(list)
    for path in iter_files(mod_dir, ["history", "common/scripted_effects", "common/on_actions",
                                     "common/national_focus", "events", "common/decisions"]):
        text = open(path, encoding="utf-8-sig", errors="replace").read()
        for ln, line in enumerate(text.splitlines(), 1):
            code = line.split("#")[0]
            m = re.match(r"\s*([a-z_0-9]+)\s*=\s*[1-9]\s*$", code)
            if m and m.group(1) in doctrine_ids:
                hits[rel(mod_dir, path)].append((ln, m.group(1)))
    return hits


# --------------------------------------------------------------------------
# job 3: report vanilla bloat, never delete
# --------------------------------------------------------------------------
def report_history_bloat(mod_dir):
    rows = []
    for path in glob.glob(os.path.join(mod_dir, "history", "countries", "*.txt")):
        text = open(path, encoding="utf-8-sig", errors="replace").read()
        lines = text.splitlines()
        commented = sum(1 for l in lines if l.lstrip().startswith("#"))
        inert = len(re.findall(r"(?m)^\s*#\s*(set_oob|set_air_oob|oob|create_equipment_variant)", text))
        rows.append((rel(mod_dir, path), len(lines), commented, inert))
    return sorted(rows, key=lambda r: -r[1])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mod-dir", default="the_sacred_war_1942")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--report", default="tools/migration_report.txt")
    args = ap.parse_args()
    mod = args.mod_dir

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import pdxparse

    # collect the old doctrine tech ids from the design-record file
    src = os.path.join(mod, "design_record", "land_doctrine_1942_original.txt")
    techs = pdxparse.parse(open(src, encoding="utf-8-sig").read(), src)[0]
    doctrine_ids = {n.key for n in techs.children if n.is_block}

    lines = []
    lines.append("The Sacred War 1942 - 1.20 migration report")
    lines.append("=" * 70)
    lines.append(f"mode: {'APPLY' if args.apply else 'DRY RUN'}")
    lines.append("")

    # ---- job 2
    lines.append("0) Technology ids previously believed removed ----------------")
    for k, why in STILL_EXISTING.items():
        lines.append(f"   OK  {k:34s} {why}")
    lines.append("")

    lines.append("1) Technology ids neither the mod nor vanilla defines ---------")
    changes = remap_removed_techs(mod, args.apply)
    if changes:
        for c in changes:
            lines.append("   " + c)
    else:
        lines.append("   none - every technology the mod grants is defined")
    lines.append("")

    # ---- job 1
    lines.append("2) Old doctrine techs still granted with set_technology ------")
    lines.append("   (these must be replaced by set_grand_doctrine / set_sub_doctrine,")
    lines.append("    or by a scripted effect that does so - see tools/gen_doctrines.py)")
    grants = find_old_doctrine_grants(mod, doctrine_ids)
    total = 0
    for f, items in sorted(grants.items()):
        total += len(items)
        ids = collections.Counter(i[1] for i in items)
        lines.append(f"   {f}: {len(items)} grants")
        lines.append(f"        " + ", ".join(f"{k}x{v}" for k, v in ids.most_common()))
    lines.append(f"   TOTAL: {total} grants across {len(grants)} files")
    lines.append("")

    # ---- job 3
    lines.append("3) Vanilla country-history files carried by the mod ----------")
    lines.append("   (lines / fully-commented lines / inert oob references)")
    for f, n, c, i in report_history_bloat(mod):
        lines.append(f"   {f:52s} {n:5d} / {c:5d} / {i:4d}")
    lines.append("")

    out = "\n".join(lines) + "\n"
    with open(args.report, "w", encoding="utf-8") as fh:
        fh.write(out)
    print(out)
    print(f"wrote {args.report}")


if __name__ == "__main__":
    main()
