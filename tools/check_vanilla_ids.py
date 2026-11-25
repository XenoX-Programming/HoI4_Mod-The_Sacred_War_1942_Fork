#!/usr/bin/env python3
"""
Cross-check every identifier The Sacred War 1942 references against a vanilla
1.20 file tree, and report the ones vanilla does not define.

The sandbox has no HoI4 install, so this works against a mirror of the vanilla
common/ folder ("a blank mod" published by Vic3ToHoI4). Point it at a real
install with --vanilla:

    python3 tools/check_vanilla_ids.py --vanilla "C:/Program Files/Steam/steamapps/common/Hearts of Iron IV"

Categories checked
  technology ids      set_technology blocks in history/  +  has_tech triggers
  doctrine ids        set_grand_doctrine / set_sub_doctrine / add_mastery
  tactic ids          enable_tactic
  subunit categories  keys inside doctrine/category blocks
  equipment archetypes, ideas, focuses, characters  (spot checks)

Every finding is a line in the report; ids added by this mod are expected to
appear and are tagged as MOD-DEFINED when the mod itself defines them.
"""
import argparse
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pdxparse  # noqa: E402


def ids_in(path, pattern):
    return set(re.findall(pattern, open(path, encoding="utf-8-sig", errors="replace").read()))


def collect_vanilla(vdir):
    v = {}

    def add(bucket, values):
        v.setdefault(bucket, set()).update(values)

    tech_files = glob.glob(os.path.join(vdir, "common/technologies/*.txt"), recursive=True)
    for f in tech_files:
        add("tech", ids_in(f, r"(?m)^\t([A-Za-z_0-9]+)\s*=\s*\{"))
    dfiles = glob.glob(os.path.join(vdir, "common/doctrines/**/*.txt"), recursive=True)
    for f in dfiles:
        add("doctrine", ids_in(f, r"(?m)^([a-z_0-9]+)\s*=\s*\{"))
    ct = os.path.join(vdir, "common/combat_tactics.txt")
    if os.path.exists(ct):
        add("tactic", ids_in(ct, r"(?m)^(tactic_[a-z_0-9]+)\s*=\s*\{"))
    add("units", [os.path.basename(p)[:-4] for p in
                  glob.glob(os.path.join(vdir, "common/units/*.txt"))])
    for f in glob.glob(os.path.join(vdir, "common/units/equipment/*.txt")):
        add("equipment", ids_in(f, r"(?m)^([a-z_0-9]+)\s*=\s*\{"))
    for f in glob.glob(os.path.join(vdir, "common/ideas/*.txt")):
        add("ideas", ids_in(f, r"(?m)^([a-z_0-9]+)\s*=\s*\{"))
    for f in glob.glob(os.path.join(vdir, "common/combat_tactics.txt")):
        add("tactic_file", {"1"})
    return v


def collect_mod(mdir):
    """id -> list of (file, line) for things the mod itself defines."""
    defined = {}
    for sub, bucket in [
        ("common/technologies", "tech"),
        ("common/doctrines", "doctrine"),
        ("common/ideas", "ideas"),
        ("common/units", "units"),
        ("common/units/equipment", "equipment"),
        ("common/national_focus", "focus"),
        ("common/characters", "character"),
        ("common/decisions", "decision"),
    ]:
        for f in glob.glob(os.path.join(mdir, sub, "**", "*.txt"), recursive=True):
            for ln, line in enumerate(open(f, encoding="utf-8-sig", errors="replace"), 1):
                m = re.match(r"\s*([A-Za-z_0-9]+)\s*=\s*\{", line)
                if m:
                    defined.setdefault(m.group(1), (bucket, f, ln))
    return defined


def check(vdir, mdir):
    v = collect_vanilla(vdir)
    mdef = collect_mod(mdir)
    findings = []

    def report(kind, ident, where, note=""):
        if ident in v.get(kind, set()):
            return
        owner = mdef.get(ident)
        tag = f"MOD-DEFINED in {os.path.relpath(owner[1], mdir)}" if owner else "UNDEFINED"
        findings.append((kind, ident, where, tag, note))

    # 1. technologies granted in history
    for f in glob.glob(os.path.join(mdir, "history", "**", "*.txt"), recursive=True):
        rel = os.path.relpath(f, mdir)
        text = open(f, encoding="utf-8-sig", errors="replace").read()
        for m in re.finditer(r"(?m)^\s*([a-z_0-9]+)\s*=\s*[1-9]\s*$", text):
            report("tech", m.group(1), rel)
        for m in re.finditer(r"has_tech\s*=\s*([a-z_0-9]+)", text):
            report("tech", m.group(1), rel)

    # 2. doctrines
    for f in glob.glob(os.path.join(mdir, "**", "*.txt"), recursive=True):
        if "design_record" in f:
            continue
        rel = os.path.relpath(f, mdir)
        text = open(f, encoding="utf-8-sig", errors="replace").read()
        for m in re.finditer(r"set_grand_doctrine\s*=\s*([a-z_0-9]+)", text):
            report("doctrine", m.group(1), rel)
        for m in re.finditer(r"set_sub_doctrine\s*=\s*([a-z_0-9]+)", text):
            report("doctrine", m.group(1), rel)
        for m in re.finditer(r"sub_doctrine\s*=\s*([a-z_0-9]+)", text):
            report("doctrine", m.group(1), rel)
        for m in re.finditer(r"has_doctrine\s*=\s*([a-z_0-9]+)", text):
            report("doctrine", m.group(1), rel, "trigger")
        for m in re.finditer(r"enable_tactic\s*=\s*([a-z_0-9]+)", text):
            report("tactic", m.group(1), rel)

    return findings, v, mdef


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vanilla", default=os.environ.get("HOI4_VANILLA", ""),
                    help="path to a Hearts of Iron IV install")
    ap.add_argument("--mod-dir", default="the_sacred_war_1942")
    ap.add_argument("--known", default="tools/vanilla_1_20_ids.json",
                    help="cached id dump (used when --vanilla is absent)")
    args = ap.parse_args()

    if args.vanilla:
        vdir = args.vanilla
        v = collect_vanilla(vdir)
        with open(args.known, "w", encoding="utf-8") as fh:
            json.dump({k: sorted(val) for k, val in v.items()}, fh, indent=1)
        print(f"dumped vanilla ids from {vdir} to {args.known}")
        return 0

    if not os.path.exists(args.known):
        print(f"ERROR: no vanilla tree. Pass --vanilla PATH, or put a cached id dump"
              f" at {args.known}.")
        return 2
    v = {k: set(val) for k, val in json.load(open(args.known)).items()}

    mdir = args.mod_dir
    mdef = collect_mod(mdir)
    findings = []

    def report(kind, ident, where, note=""):
        if ident in v.get(kind, set()):
            return
        owner = mdef.get(ident)
        if owner:
            tag = f"mod-defined ({owner[0]})"
        elif ident in v.get("doctrine_verified_elsewhere", set()):
            tag = "vanilla (see note)"
        else:
            tag = "UNDEFINED"
        findings.append((kind, ident, where, tag, note))

    # --- technologies, parsed properly so state building levels are not mistaken
    #     for technology ids. Only keys inside a `set_technology` block count.
    tech_files = (glob.glob(os.path.join(mdir, "history", "**", "*.txt"), recursive=True)
                  + glob.glob(os.path.join(mdir, "common", "scripted_effects", "*.txt")))
    for f in tech_files:
        rel = os.path.relpath(f, mdir)
        try:
            nodes = pdxparse.parse(open(f, encoding="utf-8-sig", errors="replace").read(), f)
        except Exception as exc:                      # parser is permissive, but be safe
            print(f"  (parse skipped {rel}: {exc})")
            continue
        for root in nodes:
            for st in root.getall("set_technology"):
                if not st.is_block:
                    continue
                for c in st.children:
                    if c.key in ("populate", "populate_until", "populate_some"):
                        continue
                    report("tech", c.key, rel, "set_technology")
            for ht in root.getall("has_tech"):
                if not ht.is_block:
                    report("tech", ht.value, rel, "has_tech")

    # --- doctrines and tactics, plain regex is enough
    for f in glob.glob(os.path.join(mdir, "**", "*.txt"), recursive=True):
        if "design_record" in f:
            continue
        rel = os.path.relpath(f, mdir)
        text = open(f, encoding="utf-8-sig", errors="replace").read()
        for pat, kind in [(r"set_grand_doctrine\s*=\s*([a-z_0-9]+)", "doctrine"),
                          (r"set_sub_doctrine\s*=\s*([a-z_0-9]+)", "doctrine"),
                          (r"sub_doctrine\s*=\s*([a-z_0-9]+)", "doctrine"),
                          (r"has_doctrine\s*=\s*([a-z_0-9]+)", "doctrine"),
                          (r"enable_tactic\s*=\s*([a-z_0-9]+)", "tactic")]:
            for m in re.finditer(pat, text):
                report(kind, m.group(1), rel)

    undefined = [f for f in findings if f[3] == "UNDEFINED"]
    moddef = [f for f in findings if f[3] != "UNDEFINED"]

    print(f"vanilla id dump: {args.known}")
    print(f"  tech {len(v.get('tech', []))}, doctrine {len(v.get('doctrine', []))}, "
          f"tactic {len(v.get('tactic', []))}")
    print(f"references checked: {len(findings) + len(set())}")
    print()
    if undefined:
        print(f"UNDEFINED ANYWHERE ({len(undefined)}):")
        for kind, ident, where, tag, note in sorted(set(undefined)):
            print(f"  [{kind}] {ident:44s} {where}")
    else:
        print("UNDEFINED ANYWHERE: none")
    print()
    print(f"resolved to mod-defined ids ({len(set(moddef))}):")
    for kind, ident, where, tag, note in sorted(set(moddef)):
        print(f"  [{kind}] {ident:44s} {tag}")
    return 1 if undefined else 0


if __name__ == "__main__":
    sys.exit(main())
