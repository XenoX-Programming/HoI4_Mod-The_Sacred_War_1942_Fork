#!/usr/bin/env python3
"""
Regenerate The Sacred War 1942's land doctrine tree in the HoI4 1.17+ format
from the mod's ORIGINAL technology-tree doctrines.

Structure comes from tools/doctrine_map.py (one source of truth).
Effects are copied VERBATIM from
    Mod/the_sacred_war_1942/common/technologies/land_doctrine.txt
which stays in place as the design record. No modifiers are invented.

Outputs (all overwritten on each run):
    common/doctrines/tracks/sw_land_tracks.txt
    common/doctrines/grand_doctrines/sw_land_grand_doctrines.txt
    common/doctrines/subdoctrines/land/sw_<track>_subdoctrines.txt
    localisation/english/sw_doctrines_l_english.yml

Usage: python3 tools/gen_doctrines.py [--mod-dir Mod/the_sacred_war_1942]
"""
import argparse
import glob
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pdxparse          # noqa: E402
import doctrine_map as M  # noqa: E402

I = "\t"

STRUCTURAL = {
    "doctrine", "research_cost", "xp_research_type", "xp_unlock_cost",
    "doctrine_name", "folder", "categories", "ai_will_do",
    "ai_research_weights", "path", "xor", "allow",
}

# Pretty names for the localisation file. Keyed by old tech id.
PRETTY = {
    "mobile_warfare": "Mobile Warfare",
    "superior_firepower": "Superior Firepower",
    "trench_warfare": "Trench Warfare",
    "mass_assault": "Mass Assault",
    "delay": "Delay", "elastic_defence": "Elastic Defence",
    "mobile_infantry": "Mobile Infantry", "mass_motorization": "Mass Motorisation",
    "mechanised_offensive": "Mechanised Offensive", "kampfgruppe": "Kampfgruppe",
    "firebrigades": "Fire Brigades", "backhand_blow": "Backhand Blow",
    "modern_blitzkrieg": "Modern Blitzkrieg",
    "armored_spearhead": "Armoured Spearhead", "schwerpunk": "Schwerpunkt",
    "blitzkrieg": "Blitzkrieg", "volkssturm": "Volkssturm",
    "nd_conscription": "Total Conscription", "werwolf_guerillas": "Werewolf Guerrillas",
    "masterful_blitz": "Masterful Blitz",
    "sup_delay": "Support Delay", "mobile_defence": "Mobile Defence",
    "intergrated_support": "Integrated Support",
    "regimental_combat_teams": "Regimental Combat Teams",
    "dispersed_support": "Dispersed Support",
    "overwhelming_firepower": "Overwhelming Firepower",
    "centralized_fire_control": "Centralised Fire Control",
    "forward_observers": "Forward Observers",
    "advanced_firebases": "Advanced Fire Bases",
    "shock_and_awe": "Shock and Awe",
    "concentrated_fire_plans": "Concentrated Fire Plans",
    "combined_arms": "Combined Arms", "tactical_control": "Tactical Control",
    "air_land_battle": "Air-Land Battle",
    "sup_mechanized_offensive": "Mechanised Firepower",
    "grand_battle_plan": "Grand Battle Plan", "prepared_defense": "Prepared Defence",
    "grand_assault": "Grand Assault",
    "grand_mechanized_offensive": "Grand Mechanised Offensive",
    "assault_concentration": "Assault Concentration",
    "branch_interoperation": "Branch Inter-operation",
    "assault_breakthrough": "Assault Breakthrough",
    "central_planning": "Central Planning", "c3i_theory": "C3I Theory",
    "infantry_offensive": "Infantry Offensive",
    "armored_operations": "Armoured Operations",
    "infiltration_assault": "Infiltration Assault",
    "night_assault_tactics": "Night Assault Tactics",
    "attritional_containment": "Attritional Containment",
    "infiltration_in_depth": "Infiltration in Depth",
    "pocket_defence": "Pocket Defence", "defence_in_depth": "Defence in Depth",
    "large_front_operations": "Large Front Operations",
    "deep_operations": "Deep Operations",
    "operational_concentration": "Operational Concentration",
    "vast_offensives": "Vast Offensives",
    "breakthrough_priority": "Breakthrough Priority",
    "mechanized_wave": "Mechanised Wave",
    "continuous_offensive": "Continuous Offensive",
    "peoples_army": "People's Army",
    "human_infantry_offensive": "Human Infantry Offensive",
    "large_front_offensive": "Large Front Offensive",
    "human_wave_offensive": "Human Wave Offensive",
    "guerilla_warfare": "Guerrilla Warfare",
}
# Reward loc keys are "<subdoctrine>_<reward>". The reward keys are derived from
# old tech ids, so map them back for pretty text.
REWARD_PRETTY = {f"swd_{k}": v for k, v in PRETTY.items()}

SCHOOL_BLURB = {
    "sw_mobile_warfare":
        "Speed, radio and the armoured thrust. The 1942 doctrine of the fast decision.",
    "sw_superior_firepower":
        "Artillery, support weapons and the fire plan. Win the firefight, then advance.",
    "sw_grand_battleplan":
        "Fortify, prepare and then strike to a timetable under central control.",
    "sw_mass_assault":
        "Depth, manpower and the broad front. Absorb the blow and drown the attacker.",
}

TRACK_BLURB = {
    "sw_mw_motorised": "Trucks, half-tracks and the infantry that rides with the tanks.",
    "sw_mw_armoured": "The panzer arm itself: spearhead, Schwerpunkt and the backhand blow.",
    "sw_sf_support": "Support battalions and the artillery they exist to serve.",
    "sw_sf_fires": "Observation, fire control and the concentration of fire.",
    "sw_gb_battleplan": "The set-piece offensive: plan it, staff it, then break the line.",
    "sw_gb_infiltration": "Infiltration, night work and grinding attrition.",
    "sw_ma_front": "Wide fronts and deep operations with everything you have.",
    "sw_ma_peoples": "The people's army: mass mobilisation and partisan war.",
}


# The old tree contains one dangling reference: the orphan tech `masterful_blitz`
# enables `tactic_masterful_blitz`, which is defined neither in vanilla 1.20's
# common/combat_tactics.txt nor anywhere in this mod. It therefore did nothing
# before the port either. It is dropped rather than invented, because a bogus
# tactic name cannot be made to work without writing a whole tactic definition.
DROPPED_TACTICS = {"tactic_masterful_blitz"}
DROPPED_LOG = []


def _prune(node):
    keep = []
    for c in node.children:
        if c.key == "enable_tactic" and c.value in DROPPED_TACTICS:
            DROPPED_LOG.append(c.value)
            continue
        if c.is_block:
            _prune(c)
        keep.append(c)
    node.children = keep


def load_techs(path):
    nodes = pdxparse.parse(open(path, encoding="utf-8-sig").read(), path)
    assert nodes[0].key == "technologies", nodes[0].key
    techs = {n.key: n for n in nodes[0].children if n.is_block}
    for n in techs.values():
        _prune(n)
    return techs


MERGED_CONFLICTS = []

# Per-battalion modifiers that HoI4 adds together across every doctrine source.
# When two old tiers both raise one of these, the merged reward must carry the
# SUM, otherwise merging silently costs the player a bonus.
ADDITIVE = {
    "max_organisation", "max_strength", "default_morale", "soft_attack",
    "hard_attack", "defense", "breakthrough", "armor", "piercing",
    "combat_width", "maximum_speed", "ap_attack", "air_attack",
    "recon", "suppression", "reliability", "weight", "fuel_capacity",
}


def effects(techs, tech_id, depth):
    node = techs.get(tech_id)
    if node is None:
        raise SystemExit(f"ERROR: old doctrine tech '{tech_id}' not found")
    return _render(node.children, depth)


def _render(children, depth):
    pad = I * depth
    out = []
    for c in children:
        if c.key in STRUCTURAL:
            continue
        if c.is_block:
            out.append(f"{pad}{c.key} = {{")
            out.extend(_render(c.children, depth + 1))
            out.append(f"{pad}}}")
        else:
            out.append(f"{pad}{c.key} = {c.value}")
    return out


def gen_tracks():
    out = [
        "# The Sacred War 1942 - land doctrine tracks",
        "# Game format: HoI4 1.17+ grand-doctrine system",
        "# GENERATED FILE - produced by tools/gen_doctrines.py, do not hand-edit.",
        "# The tree is described in tools/doctrine_map.py.",
        "",
    ]
    for s in M.SCHOOLS:
        for tr in s["tracks"]:
            out += [
                f"{tr['id']} = {{",
                f"{I}name = {tr['name']}",
                f"{I}background = {tr['bg']}",
                f"{I}icon = {tr['icon']}",
                f"{I}icon_frame = GFX_doctrine_decor_land",
                "",
                f"{I}mastery = {{",
                f"{I * 2}multiplier = 1.0",
                f"{I * 2}categories = {{",
                f"{I * 3}category_army",
                f"{I * 2}}}",
                f"{I}}}",
                "}",
                "",
            ]
    return "\n".join(out) + "\n"


def gen_grand(techs):
    out = [
        "# The Sacred War 1942 - land grand doctrines",
        "# The mod's four original schools, carried over from the old technology tree.",
        "# GENERATED FILE - produced by tools/gen_doctrines.py.",
        "# Modifier blocks are copied verbatim from",
        "# common/technologies/land_doctrine.txt (kept as the design record).",
        "",
    ]
    for s in M.SCHOOLS:
        out += [
            f"{s['id']} = {{",
            f"{I}folder = land",
            "",
            f"{I}name = {s['name']}",
            f"{I}description = {s['desc']}",
            f"{I}icon = {s['icon']}",
            f"{I}available = {{",
            f"{I * 2}always = yes",
            f"{I}}}",
            "",
            f"{I}xp_cost = 100",
            f"{I}xp_type = army",
            "",
            f"{I}ai_will_do = {{",
            f"{I * 2}base = 5",
            f"{I}}}",
            "",
            f"{I}tracks = {{",
        ]
        for tr in s["tracks"]:
            out.append(f"{I * 2}{tr['id']}")
        out += [f"{I}}}", f"{I}max_track_columns = 2", ""]

        out.append(f"{I}# Effects of the old root tech '{s['old_root']}' plus every"
                   f" shared prerequisite, merged so that no key appears twice.")
        out += merge_effects(techs, [s["old_root"]] + s["spine"], 1)

        out += ["", f"{I}milestones = {{   # one per track, same order as 'tracks'"]
        for tr in s["tracks"]:
            _root, _groups, milestone = M.plan_branch(tr["chain"])
            out.append(f"{I * 2}{{   # {tr['id']} - old branch terminal tech '{milestone}'")
            out += effects(techs, milestone, 3)
            for extra in s.get("extra_milestone_techs", {}).get(tr["id"], []):
                out.append(f"{I * 3}# plus the old orphan tech '{extra}' "
                           f"(present in the file but unreachable in the old tree)")
                out += effects(techs, extra, 3)
            out.append(f"{I * 2}}}")
        out += [f"{I}}}", "}", ""]
    return "\n".join(out) + "\n"


NON_STACKING = {"enable_tactic", "additional_brigade_column_size"}


def merge_effects(techs, tech_list, depth):
    """Concatenate several old techs' effects, merging key by key.

    Naively concatenating two techs' blocks would produce duplicate keys such as

        enable_tactic = tactic_a
        enable_tactic = tactic_b
        max_organisation = 10
        max_organisation = 5

    and HoI4 keeps only one of them (the last), so bonuses would silently be
    lost. Blocks are merged by recursing into the same key, and single-valued
    keys are collected with max() so nothing is lost.
    """
    merged = []          # [(key, payload)] where payload is list of lines or None
    index = {}
    for t in tech_list:
        node = techs[t]
        for c in node.children:
            if c.key in STRUCTURAL:
                continue
            if c.key in NON_STACKING:
                # enable_tactic may legitimately appear more than once (each
                # tactic is unlocked separately); additional_brigade_column_size
                # must not, so only the largest value is kept.
                if c.key not in index:
                    index[c.key] = [c.value]
                    merged.append((c.key, index[c.key]))
                elif c.key == "enable_tactic" and c.value not in index[c.key]:
                    index[c.key].append(c.value)
                elif c.key != "enable_tactic":
                    try:
                        if float(c.value) > float(index[c.key][0]):
                            index[c.key][0] = c.value
                    except (TypeError, ValueError):
                        pass
                continue
            if c.is_block:
                if c.key not in index:
                    index[c.key] = {}
                    merged.append((c.key, index[c.key]))
                _merge_block(index[c.key], c.children)
            else:
                if c.key not in index:
                    index[c.key] = c.value
                    merged.append((c.key, ("scalar", c)))
                else:
                    prev = index[c.key]
                    if isinstance(prev, tuple):
                        index[c.key] = ("scalar", _max_node(prev[1], c))
    pad = I * depth
    out = []
    for key, payload in merged:
        if key in NON_STACKING:
            for v in payload:
                out.append(f"{pad}{key} = {v}")
        elif isinstance(payload, tuple):
            out.append(f"{pad}{key} = {payload[1].value}")
        else:
            out.append(f"{pad}{key} = {{")
            out.extend(_render_merged(payload, depth + 1))
            out.append(f"{pad}}}")
    return out


def _merge_block(dest, children):
    for c in children:
        if c.is_block:
            if c.key not in dest:
                dest[c.key] = {}
                dest[c.key]["__order__"] = [c.key]
            elif not isinstance(dest[c.key], dict):
                dest[c.key] = {}
            _merge_block(dest[c.key], c.children)
        else:
            if c.key not in dest:
                dest[c.key] = ("scalar", c)
            else:
                prev = dest[c.key]
                if isinstance(prev, dict):
                    continue
                dest[c.key] = ("scalar", _max_node(prev[1], c))


def _render_merged(dest, depth):
    pad = I * depth
    out = []
    for key, val in dest.items():
        if key == "__order__":
            continue
        if isinstance(val, dict):
            out.append(f"{pad}{key} = {{")
            out.extend(_render_merged(val, depth + 1))
            out.append(f"{pad}}}")
        else:
            out.append(f"{pad}{key} = {val[1].value}")
    return out


def _max_node(a, b):
    """Pick the larger of two values for the same key.

    Two different old techs can set the same key to different values (e.g. two
    tactics both raising max_organisation by 10 and by 5). A single HoI4 block
    can only hold one, so the larger is kept and the conflict is recorded for
    readme_ai.md rather than being resolved silently.
    """
    if a.key in ADDITIVE:
        try:
            total = float(a.value) + float(b.value)
        except (TypeError, ValueError):
            return a
        MERGED_CONFLICTS.append((a.key, f"{a.value} + {b.value}", f"{total:g}"))
        a.value = f"{total:g}"
        return a
    try:
        if float(a.value) == float(b.value):
            return a
        keep = a if float(a.value) > float(b.value) else b
        dropped = b if keep is a else a
        MERGED_CONFLICTS.append((a.key, dropped.value, keep.value))
        return keep
    except (TypeError, ValueError):
        return a


def gen_subdoctrines(techs):
    files = {}
    for s in M.SCHOOLS:
        for tr in s["tracks"]:
            root, groups, milestone = M.plan_branch(tr["chain"])
            sid = tr["id"]
            # The subdoctrine needs its OWN id; see M.subdoctrine_id().
            sid_doc = M.subdoctrine_id(sid)
            out = [
                f"# The Sacred War 1942 - subdoctrines for track '{sid}'",
                f"# Old branch: {' -> '.join(tr['chain'])}",
                f"# GENERATED FILE - produced by tools/gen_doctrines.py.",
                f"# Effects are copied from design_record/land_doctrine_1942_original.txt.",
                "",
                f"{sid_doc} = {{",
                f"{I}track = {sid}",
                f"{I}name = {sid.upper()}_NAME",
                f"{I}description = {sid.upper()}_DESC",
                f"{I}icon = {s['icon']}",
                "",
                f"{I}xp_cost = 100",
                f"{I}xp_type = army",
                "",
                f"{I}available = {{",
                f"{I * 2}has_doctrine = {s['id']}",
                f"{I}}}",
                f"{I}visible = {{",
                f"{I * 2}has_doctrine = {s['id']}",
                f"{I}}}",
                "",
                f"{I}ai_will_do = {{",
                f"{I * 2}base = 5",
                f"{I}}}",
                "",
                f"{I}# Base effects, from the old first tech of the branch: {root}",
            ]
            out += effects(techs, root, 1) or [f"{I}# (no effect block)"]
            n_groups = sum(1 for g in groups if g)
            out += ["", f"{I}# {n_groups} rewards (1.17+ allows at most {M.MAX_REWARDS};",
                    f"{I}# this branch only had {n_groups} tiers to translate).",
                    f"{I}# 100 mastery each.",
                    f"{I}rewards = {{"]
            for n, group in enumerate(groups, 1):
                if not group:
                    # An empty reward block is structurally unusual and buys
                    # nothing, so it is omitted entirely rather than emitted as
                    # `x = { }`. Tracks whose old branch had fewer than five
                    # tiers therefore have fewer than five rewards.
                    out.append(f"{I * 2}# reward {n}: the old branch had no such tier"
                               f" (branch had fewer than {M.MAX_REWARDS} tiers)")
                    continue
                if len(group) > 1:
                    out.append(f"{I * 2}# reward {n}: merged tiers "
                               f"{', '.join(group)} (branch had more than {M.MAX_REWARDS})")
                else:
                    out.append(f"{I * 2}# reward {n}: old tech {group[0]}")
                out.append(f"{I * 2}{sid}_tier{n} = {{")
                out += merge_effects(techs, group, 3)
                out.append(f"{I * 2}}}")
            out += [f"{I}}}", "}", ""]
            files[f"common/doctrines/subdoctrines/land/{sid}_subdoctrines.txt"] = "\n".join(out) + "\n"
    return files


def pretty_track(tid):
    return {
        "sw_mw_motorised": "Motorised Infantry",
        "sw_mw_armoured": "Armoured Warfare",
        "sw_sf_support": "Combat Support",
        "sw_sf_fires": "Fire Support",
        "sw_gb_battleplan": "Battle Plan",
        "sw_gb_infiltration": "Infiltration",
        "sw_ma_front": "Broad Front",
        "sw_ma_peoples": "People's War",
    }.get(tid, tid)


def gen_loc():
    """Write english + russian localisation.

    Grand doctrines reuse VANILLA keys (GRAND_DOCTRINE_*) so their names and
    descriptions work in every language straight away. Only the things this mod
    adds -- 8 track names, 8 subdoctrine names/descriptions, reward titles and
    the two special-forces doctrines -- need new keys.
    """
    en, ru = [], []
    for s in M.SCHOOLS:
        for tr in s["tracks"]:
            en.append((tr["name"], pretty_track(tr["id"])))
            ru.append((tr["name"], RU_TRACK[tr["id"]]))
            en.append((f'{tr["id"].upper()}_NAME', pretty_track(tr["id"])))
            ru.append((f'{tr["id"].upper()}_NAME', RU_TRACK[tr["id"]]))
            en.append((f'{tr["id"].upper()}_DESC', TRACK_BLURB.get(tr["id"], "")))
            ru.append((f'{tr["id"].upper()}_DESC', RU_BLURB.get(tr["id"], "")))
            _root, groups, _ms = M.plan_branch(tr["chain"])
            for n, group in enumerate(groups, 1):
                key = f'{tr["id"]}_tier{n}'
                if not group:
                    en.append((key, "(unused)"))
                    ru.append((key, "(не используется)"))
                    continue
                title = " + ".join(PRETTY.get(old, old) for old in group)
                rtitle = " + ".join(RU_PRETTY.get(old, PRETTY.get(old, old)) for old in group)
                en.append((key, title))
                ru.append((key, rtitle))
    # special forces / air doctrines that vanilla also defines but which the mod
    # now overrides via replace_path (defensive: keeps names if vanilla's file
    # is ever replaced wholesale).
    out_en = ["l_english:",
              " # The Sacred War 1942 - doctrine localisation (HoI4 1.17+ doctrine system)",
              " # GENERATED FILE - produced by tools/gen_doctrines.py.",
              " # Grand doctrine names/descriptions intentionally reuse the vanilla",
              " # GRAND_DOCTRINE_* keys so they are localised in every supported language.",
              ]
    out_ru = ["l_russian:",
              " # The Sacred War 1942 - локализация доктрин",
              " # СГЕНЕРИРОВАННЫЙ ФАЙЛ - создаётся tools/gen_doctrines.py"]
    seen = set()
    for k, v in en:
        if k in seen:
            continue
        seen.add(k)
        out_en.append(f' {k}:0 "{v}"')
    for k, v in ru:
        out_ru.append(f' {k}:0 "{v}"')
    return "\n".join(out_en) + "\n", "\n".join(out_ru) + "\n"


RU_TRACK = {
    "sw_mw_motorised": "Моторизованная пехота",
    "sw_mw_armoured": "Танковая война",
    "sw_sf_support": "Поддержка боя",
    "sw_sf_fires": "Огневая поддержка",
    "sw_gb_battleplan": "План сражения",
    "sw_gb_infiltration": "Инфильтрация",
    "sw_ma_front": "Широкий фронт",
    "sw_ma_peoples": "Народная война",
}

RU_BLURB = {
    "sw_mw_motorised": "Грузовики, полугусеничные машины и пехота, идущая вместе с танками.",
    "sw_mw_armoured": "Сам танковый род войск: остриё удара, швепункт и удар по тылу.",
    "sw_sf_support": "Батальоны поддержки и артиллерия, которой они служат.",
    "sw_sf_fires": "Наблюдение, управление огнём и сосредоточение огня.",
    "sw_gb_battleplan": "Планомерное наступление: спланировать, подготовить, прорвать фронт.",
    "sw_gb_infiltration": "Инфильтрация, ночные действия и война на истощение.",
    "sw_ma_front": "Широкие фронты и глубокие операции всеми силами.",
    "sw_ma_peoples": "Народная армия: массовая мобилизация и партизанская война.",
}

RU_PRETTY = {
    "mass_motorization": "Массовая моторизация",
    "mechanised_offensive": "Механизированное наступление",
    "firebrigades": "Пожарные бригады",
    "backhand_blow": "Удар с тыла",
    "schwerpunk": "Швепункт",
    "volkssturm": "Фольксштурм",
    "nd_conscription": "Всеобщая мобилизация",
    "regimental_combat_teams": "Полковые боевые группы",
    "dispersed_support": "Распределённая поддержка",
    "overwhelming_firepower": "Подавляющая огневая мощь",
    "forward_observers": "Передовые наблюдатели",
    "advanced_firebases": "Передовые огневые базы",
    "shock_and_awe": "Шок и трепет",
    "concentrated_fire_plans": "Сосредоточенные планы огня",
    "combined_arms": "Общевойсковой бой",
    "tactical_control": "Тактическое управление",
    "grand_assault": "Великий штурм",
    "grand_mechanized_offensive": "Великое механизированное наступление",
    "assault_concentration": "Сосредоточение штурма",
    "branch_interoperation": "Межвидовая взаимодействие",
    "assault_breakthrough": "Штурмовой прорыв",
    "central_planning": "Центральное планирование",
    "armored_operations": "Танковые операции",
    "infiltration_assault": "Инфильтрационный штурм",
    "night_assault_tactics": "Тактика ночного штурма",
    "attritional_containment": "Сдерживание на истощение",
    "large_front_operations": "Операции на широком фронте",
    "deep_operations": "Глубокие операции",
    "operational_concentration": "Оперативное сосредоточение",
    "vast_offensives": "Масштабные наступления",
    "breakthrough_priority": "Приоритет прорыва",
    "mechanized_wave": "Механизированная волна",
    "human_infantry_offensive": "Наступление людской пехоты",
    "large_front_offensive": "Наступление на широком фронте",
    "human_wave_offensive": "Наступление людской волной",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mod-dir", default="Mod/the_sacred_war_1942")
    args = ap.parse_args()
    mod = args.mod_dir
    src = os.path.join(mod, "design_record", "land_doctrine_1942_original.txt")
    techs = load_techs(src)
    print(f"loaded {len(techs)} old doctrine techs from {src}")

    outputs = {
        "common/doctrines/tracks/sw_land_tracks.txt": gen_tracks(),
        "common/doctrines/grand_doctrines/sw_land_grand_doctrines.txt": gen_grand(techs),
    }
    outputs.update(gen_subdoctrines(techs))
    loc_en, loc_ru = gen_loc()
    outputs["localisation/english/sw_doctrines_l_english.yml"] = loc_en
    outputs["localisation/russian/sw_doctrines_l_russian.yml"] = loc_ru

    # remove the earlier mis-named generator output if present
    for stale in glob.glob(os.path.join(mod, "common/doctrines/subdoctrines/land/sw_sw_*")):
        os.remove(stale)
        print(f"  removed stale {os.path.relpath(stale, mod)}")

    if DROPPED_LOG:
        print(f"\n  dropped a dangling tactic reference, undefined in vanilla 1.20"
              f" and in this mod: {', '.join(sorted(set(DROPPED_LOG)))}")
        print(f"    (it had no effect before the port either; see readme_ai.md)")

    if MERGED_CONFLICTS:
        print(f"\n  note: {len(MERGED_CONFLICTS)} duplicate modifier key(s) were"
              f" collapsed to the larger value:")
        for key, dropped, kept in MERGED_CONFLICTS:
            print(f"    {key}: dropped {dropped}, kept {kept}")

    for relpath, content in outputs.items():
        full = os.path.join(mod, relpath)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        # Script files must NOT have a BOM: HoI4's script parser rejects it as a
        # stray token and drops the whole file. Localisation is the opposite --
        # .yml is expected to start with one, like the mod's other loc files.
        enc = "utf-8-sig" if full.endswith(".yml") else "utf-8"
        with open(full, "w", encoding=enc, newline="\n") as fh:
            fh.write(content)
        print(f"  wrote {relpath:66s} {len(content.splitlines()):5d} lines")


if __name__ == "__main__":
    main()
