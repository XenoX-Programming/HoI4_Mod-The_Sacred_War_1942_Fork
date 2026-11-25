"""
Single source of truth for the Sacred War 1942 land-doctrine migration.

Both tools/gen_doctrines.py (which writes common/doctrines/**) and
tools/convert_history_doctrines.py (which seeds countries in history/**)
import this module, so the tree is described in exactly one place.

The structure below is a faithful transcription of the `path/leads_to_tech`
graph in Mod/the_sacred_war_1942/common/technologies/land_doctrine.txt:

    mobile_warfare  --+-- delay -> elastic_defence --+-- mobile_infantry -> mass_motorization
                      |                             |      -> mechanised_offensive -> kampfgruppe
                      |                             |      -> firebrigades -> backhand_blow
                      |                             |      -> modern_blitzkrieg
                      |                             +-- armored_spearhead -> schwerpunk -> blitzkrieg
                      |                                    -> kampfgruppe -> volkssturm
                      |                                    -> nd_conscription -> werwolf_guerillas
    superior_firepower -- sup_delay --+-- mobile_defence -> intergrated_support
                      |               |      -> regimental_combat_teams -> sup_mechanized_offensive
                      |               +-- dispersed_support -> overwhelming_firepower
                      |               +-- concentrated_fire_plans -> combined_arms
                      |                      -> tactical_control -> air_land_battle
                      |               +-- centralized_fire_control -> forward_observers
                      |                      -> advanced_firebases -> shock_and_awe
    trench_warfare  -- grand_battle_plan --+-- prepared_defense -> grand_assault
                      |                    |      -> grand_mechanized_offensive
                      |                    |      -> assault_concentration
                      |                    |      -> branch_interoperation -> assault_breakthrough
                      |                    |      -> central_planning -> c3i_theory
                      |                    +-- infantry_offensive -> armored_operations
                      |                           -> infiltration_assault -> night_assault_tactics
                      |                           -> attritional_containment -> infiltration_in_depth
    mass_assault    -- pocket_defence --+-- defence_in_depth -> large_front_operations
                      |                 |      -> deep_operations -> operational_concentration
                      |                 |      -> vast_offensives -> breakthrough_priority
                      |                 |      -> mechanized_wave -> continuous_offensive
                      |                 +-- peoples_army -> human_infantry_offensive
                      |                        -> large_front_offensive -> human_wave_offensive
                      |                        -> guerilla_warfare
    (orphan) masterful_blitz -- nothing leads to it; folded into the
                mobile-warfare milestone.

New structure per school:
    grand doctrine  = the old root tech + every tech that was a *shared*
                      prerequisite of both branches (the "spine").  Nothing is
                      lost: a player who used to take the root automatically got
                      these, and in the new system the grand doctrine is the
                      only thing bought before the tracks open.
    track           = one old branch.
    subdoctrine     = the first tech of that branch (what you used to buy first).
    rewards (5)     = the next techs, in tree order; surplus tiers are merged
                      into one reward (additive modifiers, so totals are kept).
    milestone       = the branch's terminal tech.

MAX_REWARDS is 5 because 1.17+ hard-codes five reward slots per subdoctrine.
"""

MAX_REWARDS = 5
MASTERY_PER_REWARD = 100     # vanilla default
MASTERY_COMPLETE = 500       # 5 x 100

SCHOOLS = [
    dict(
        id="sw_mobile_warfare",
        old_root="mobile_warfare",
        name="GRAND_DOCTRINE_MOBILE_WARFARE", desc="GRAND_DOCTRINE_MOBILE_WARFARE_DESC",
        icon="GFX_doctrine_mobile_warfare_medium",
        # Techs the old tree required before *either* branch (shared prerequisites),
        # plus the convergence tech both branches had to take (kampfgruppe).
        spine=["delay", "elastic_defence", "kampfgruppe"],
        tracks=[
            dict(id="sw_mw_motorised", name="SWD_TRACK_MOTORISED",
                 bg="GFX_mob_warfare_bg",
                 icon="GFX_doctrine_milestone_infantry_land",
                 chain=["mobile_infantry", "mass_motorization", "mechanised_offensive",
                        "firebrigades", "backhand_blow", "modern_blitzkrieg"]),
            dict(id="sw_mw_armoured", name="SWD_TRACK_ARMOURED",
                 bg="GFX_mob_warfare_bg",
                 icon="GFX_doctrine_milestone_armored_land",
                 chain=["armored_spearhead", "schwerpunk", "blitzkrieg",
                        "volkssturm", "nd_conscription", "werwolf_guerillas"]),
        ],
        extra_milestone_techs={"sw_mw_motorised": ["masterful_blitz"]},
    ),
    dict(
        id="sw_superior_firepower",
        old_root="superior_firepower",
        name="GRAND_DOCTRINE_SUPERIOR_FIREPOWER", desc="GRAND_DOCTRINE_SUPERIOR_FIREPOWER_DESC",
        icon="GFX_doctrine_superior_firepower_medium",
        spine=["sup_delay", "mobile_defence"],
        tracks=[
            dict(id="sw_sf_support", name="SWD_TRACK_SUPPORT",
                 bg="GFX_sup_firepower_bg",
                 icon="GFX_doctrine_milestone_artillery_land",
                 chain=["intergrated_support", "regimental_combat_teams",
                        "dispersed_support", "overwhelming_firepower",
                        "sup_mechanized_offensive"]),
            dict(id="sw_sf_fires", name="SWD_TRACK_FIRES",
                 bg="GFX_sup_firepower_bg",
                 icon="GFX_doctrine_milestone_artillery_land",
                 chain=["centralized_fire_control", "forward_observers", "advanced_firebases",
                        "shock_and_awe", "concentrated_fire_plans", "combined_arms",
                        "tactical_control", "air_land_battle"]),
        ],
    ),
    dict(
        id="sw_grand_battleplan",
        old_root="trench_warfare",
        name="GRAND_DOCTRINE_GRAND_BATTLEPLAN", desc="GRAND_DOCTRINE_GRAND_BATTLEPLAN_DESC",
        icon="GFX_doctrine_grand_battleplan_medium",
        spine=["grand_battle_plan"],
        tracks=[
            dict(id="sw_gb_battleplan", name="SWD_TRACK_BATTLEPLAN",
                 bg="GFX_grand_battleplan_bg",
                 icon="GFX_doctrine_milestone_operations_land",
                 chain=["prepared_defense", "grand_assault", "grand_mechanized_offensive",
                        "assault_concentration", "branch_interoperation",
                        "assault_breakthrough", "central_planning", "c3i_theory"]),
            dict(id="sw_gb_infiltration", name="SWD_TRACK_INFILTRATION",
                 bg="GFX_grand_battleplan_bg",
                 icon="GFX_doctrine_milestone_operations_land",
                 chain=["infantry_offensive", "armored_operations", "infiltration_assault",
                        "night_assault_tactics", "attritional_containment",
                        "infiltration_in_depth"]),
        ],
    ),
    dict(
        id="sw_mass_assault",
        old_root="mass_assault",
        name="GRAND_DOCTRINE_MASS_ASSAULT", desc="GRAND_DOCTRINE_MASS_ASSAULT_DESC",
        icon="GFX_doctrine_mass_assault_medium",
        spine=["pocket_defence"],
        tracks=[
            dict(id="sw_ma_front", name="SWD_TRACK_FRONT",
                 bg="GFX_tac_operation_bg",
                 icon="GFX_doctrine_milestone_infantry_land",
                 chain=["defence_in_depth", "large_front_operations", "deep_operations",
                        "operational_concentration", "vast_offensives",
                        "breakthrough_priority", "mechanized_wave",
                        "continuous_offensive"]),
            dict(id="sw_ma_peoples", name="SWD_TRACK_PEOPLES",
                 bg="GFX_tac_operation_bg",
                 icon="GFX_doctrine_milestone_infantry_land",
                 chain=["peoples_army", "human_infantry_offensive", "large_front_offensive",
                        "human_wave_offensive", "guerilla_warfare"]),
        ],
    ),
]

# Old scripted-effect bundles in common/scripted_effects/sacred_war_effects.txt
# and their equivalent in the new framework.  Each entry:
#   bundle name -> (school id, [(track id, number of old tiers the bundle granted), ...])
# `tiers` counts techs along the branch chain including the subdoctrine root;
# it is converted into mastery so the seeded country keeps its old head start.
BUNDLES = {
    # strict order of the old set_technology block: root, spine, then branch techs
    "trench_warfare_left_technology":  ("sw_grand_battleplan", {"sw_gb_battleplan": 4}),
    "trench_warfare_right_technology": ("sw_grand_battleplan", {"sw_gb_infiltration": 2}),
    "trench_warfare_right2_technology": ("sw_grand_battleplan", {"sw_gb_infiltration": 5}),
    "mass_assault_left_technology":    ("sw_mass_assault", {"sw_ma_front": 5}),
    "mobile_warfare_left_tech":        ("sw_mobile_warfare", {"sw_mw_motorised": 4}),
    "mobile_warfare_right_tech":       ("sw_mobile_warfare", {"sw_mw_armoured": 4}),
    "superior_firepower_right":        ("sw_superior_firepower", {"sw_sf_support": 4}),
}


def plan_branch(chain):
    """chain -> (subdoctrine_tech, [[tech,...], ...] reward groups, milestone_tech).

    1.17+ hard-codes five reward slots per subdoctrine, so exactly five groups
    are always returned. Tracks with extra tiers are merged into the *first*
    group, which is where the surplus tier's benefit would have been bought:

        <= 5 extra tiers : one group per tier, padded with empty groups
        6 tiers          : group1 = tiers 1+2, then one group per later tier
        7 tiers          : group1 = tiers 1+2+3, then one group per later tier
    """
    root = chain[0]
    tail = chain[1:]
    milestone = tail[-1]
    middle = tail[:-1]

    surplus = max(0, len(middle) - MAX_REWARDS)
    groups = []
    first = middle[: surplus + 1]
    if first:
        groups.append(first)
    for t in middle[surplus + 1:]:
        groups.append([t])
    while len(groups) < MAX_REWARDS:
        groups.append([])
    return root, groups, milestone


def track_sequence(track):
    """Ordered list of techs along a track, subdoctrine first, milestone last."""
    root, groups, milestone = plan_branch(track["chain"])
    seq = [root]
    for g in groups:
        seq.extend(g)
    seq.append(milestone)
    return seq


def reward_key(sub_id, group, n):
    """Localisation-safe reward id: <subdoctrine>_<tier n>."""
    return f"{sub_id}_tier{n}"


def mastery_for_tier(tier):
    """tier = how many old techs along the branch the country already had."""
    # tier 1 == subdoctrine only; every further tier unlocks one reward
    return max(0, min(MASTERY_COMPLETE, (tier - 1) * MASTERY_PER_REWARD))


# ---------------------------------------------------------------------------
# reverse lookups
# ---------------------------------------------------------------------------
def tech_to_track():
    """old doctrine tech id -> (school_id, track_id) for chain techs."""
    out = {}
    for s in SCHOOLS:
        for tr in s["tracks"]:
            for t in track_sequence(tr):
                out.setdefault(t, (s["id"], tr["id"]))
    return out


def tech_to_school():
    out = {}
    for s in SCHOOLS:
        out[s["old_root"]] = s["id"]
        for sp in s["spine"]:
            out[sp] = s["id"]
        for tr in s["tracks"]:
            for t in track_sequence(tr):
                out.setdefault(t, s["id"])
    return out


def all_old_techs():
    ids = set()
    for s in SCHOOLS:
        ids.add(s["old_root"])
        ids.update(s["spine"])
        for tr in s["tracks"]:
            ids.update(track_sequence(tr))
            for extra in s.get("extra_milestone_techs", {}).get(tr["id"], []):
                ids.add(extra)
    return ids


def tier_of(techs_present, track):
    """How many techs of the track's sequence the country had (0..len)."""
    seq = track_sequence(track)
    n = 0
    for t in seq:
        if t in techs_present:
            n += 1
        else:
            break
    return n


if __name__ == "__main__":
    # quick self-check
    print(f"{len(SCHOOLS)} schools, {sum(len(s['tracks']) for s in SCHOOLS)} tracks")
    for s in SCHOOLS:
        print(f"  {s['id']}  spine={s['spine']}")
        for tr in s["tracks"]:
            seq = track_sequence(tr)
            print(f"     {tr['id']:18s} {len(seq)} tiers: {seq[0]} ... {seq[-1]}")
    print(f"{len(all_old_techs())} old tech ids covered")


# ---------------------------------------------------------------------------
# 1.17+ also replaced the NAVAL, AIR and SPECIAL-FORCES doctrine technologies,
# which this mod's history grants heavily. The old tech ids below no longer
# exist in 1.20 (verified against a vanilla 1.20 file tree), so a grant of one
# does nothing except spam the error log.
#
# Mapping is by ROLE, not by old tree position:
#   * the old root tech of a branch maps to that branch's grand doctrine,
#   * later techs of the same branch map to the same grand doctrine
#     (a country can hold only one grand doctrine per folder, so duplicates
#     collapse harmlessly),
#   * special-forces techs map to the special-forces grand doctrine plus the
#     subdoctrine vanilla names after them (mountaineers_1/2, rangers_1/2).
# ---------------------------------------------------------------------------
DOCTRINE_TECHS_OTHER = {
    # ---- naval
    "fleet_in_being":                ("GD", "new_fleet_in_being"),
    "battlefleet_concentration":     ("GD", "new_fleet_in_being"),
    "convoy_sailing":                ("GD", "new_fleet_in_being"),
    "convoy_escorts":                ("GD", "new_fleet_in_being"),
    "trade_interdiction":            ("GD", "new_convoy_raiding"),
    "unrestricted_submarine_warfare": ("GD", "new_convoy_raiding"),
    "convoy_interdiction_ti":        ("GD", "new_convoy_raiding"),
    "raider_patrols":                ("GD", "new_convoy_raiding"),
    "submarine_operations":          ("GD", "new_convoy_raiding"),
    "submarine_operations_bs":       ("GD", "new_convoy_raiding"),
    "base_strike":                   ("GD", "new_base_strike"),
    "naval_strike_tactics":          ("GD", "new_base_strike"),
    "carrier_primacy":               ("GD", "new_base_strike"),
    "carrier_task_forces":           ("GD", "new_base_strike"),
    "subsidiary_carrier_role":       ("GD", "new_base_strike"),
    # ---- air
    "air_superiority":               ("GD", "new_operational_integrity"),
    "dogfighting_experience":        ("GD", "new_operational_integrity"),
    "formation_flying":              ("GD", "new_operational_integrity"),
    "fighter_baiting":               ("GD", "new_operational_integrity"),
    "home_defence":                  ("GD", "new_operational_integrity"),
    "infrastructure_destruction":    ("GD", "new_strategic_destruction"),
    "direct_ground_support":         ("GD", "new_battlefield_support"),
    "dive_bombing":                  ("GD", "new_battlefield_support"),
    "low_echelon_support":           ("GD", "new_battlefield_support"),
    "force_rotation":                ("GD", "new_battlefield_support"),
    "dispersed_fighting":            ("GD", "new_battlefield_support"),
    # ---- special forces
    # 1.20's special-forces subdoctrines are keyed on subunits
    # (mountaineers_1/2, rangers_1/2, ...) and gated on vanilla technology
    # (has_tech = tech_mountaineers). This mod's old special-forces techs do not
    # line up one-for-one, so only the grand doctrine is granted: the country
    # keeps the special-forces branch open and spends XP on the subdoctrine it
    # actually wants. Granular restoration is an open question in readme_ai.md.
    "special_forces_mountaineers":   ("GD", "special_forces_quality"),
    "mountaineers_combat_2":         ("GD", "special_forces_quality"),
    "rangers":                       ("GD", "special_forces_quality"),
    "special_forces_recon":          ("GD", "special_forces_quality"),
}

# Techs that 1.17+ deleted with no equivalent this mod can safely stand in for.
# Most are MTG-era renames whose replacement would enable the WRONG equipment
# modules, so they are simply dropped and listed in the migration report rather
# than guessed at. See readme_ai.md "open questions".
DEAD_TECHS = {
    "basic_medium_battery",       # MTG split cruiser batteries into light/heavy
    "early_ship_hull_carrier",    # carrier hulls are basic/improved/advanced now
    "decimetric_radar",           # radar line reduced to centimetric/monopulse
    "improved_decimetric_radar",
    "improved_centimetric_radar",
    "improved_airplane_launcher", # carrier catapults removed
}


def other_doctrine_commands(tech_ids):
    """-> (list of set_grand_doctrine / set_sub_doctrine lines, dead ids)."""
    gds, subs, dead = [], [], []
    for t in sorted(tech_ids):
        spec = DOCTRINE_TECHS_OTHER.get(t)
        if spec is None:
            if t in DEAD_TECHS:
                dead.append(t)
            continue
        if spec[0] == "GD":
            if spec[1] not in gds:
                gds.append(spec[1])
        else:
            if spec[1] not in gds:
                gds.append(spec[1])
            if spec[2] not in subs:
                subs.append(spec[2])
    return ([f"set_grand_doctrine = {g}" for g in gds]
            + [f"set_sub_doctrine = {s}" for s in subs]), dead


# Which folder each grand doctrine belongs to. A country holds one grand
# doctrine per folder, so granting two from the same folder means the second
# replaces the first (and resets that folder's mastery). The converter uses this
# to pick one deterministically instead of letting file order decide.
GD_FOLDER = {
    "sw_mobile_warfare": "land", "sw_superior_firepower": "land",
    "sw_grand_battleplan": "land", "sw_mass_assault": "land",
    "new_fleet_in_being": "naval", "new_convoy_raiding": "naval",
    "new_base_strike": "naval",
    "new_operational_integrity": "air", "new_battlefield_support": "air",
    "new_strategic_destruction": "air",
    "special_forces_quality": "special_forces",
    "special_forces_quantity": "special_forces",
}


def one_per_folder(commands, log, fname):
    """Keep at most one set_grand_doctrine per folder.

    `commands` is an ordered list. When two land in the same folder the FIRST is
    kept (it is the branch the file listed first, i.e. the country's primary
    loyalty in the old tree) and the rest are reported, rather than silently
    letting the last write win and wipe the earlier pick's mastery.
    """
    seen = {}
    out = []
    for c in commands:
        if c.startswith("set_grand_doctrine"):
            gd = c.split("=")[1].strip()
            folder = GD_FOLDER.get(gd)
            if folder in seen:
                if seen[folder] != gd:
                    log.append(f"      dropped {gd}: {folder} already set to"
                               f" {seen[folder]} (one grand doctrine per folder)")
                continue          # an exact repeat is meaningless as well
            seen[folder] = gd
        out.append(c)
    return out


def buys_for_tier(sub_id, tier):
    """Explicit unlock commands for `tier` tiers of a subdoctrine.

    `set_sub_doctrine` takes tier 1. Any further tier is bought with
    `add_mastery`, 100 mastery per tier -- the documented way for country
    history to hand a country the tiers it "already had"; a mature 1.17+ mod
    (Cold War: Iron Curtain) does exactly this in its country history files.
    """
    out = [f"set_sub_doctrine = {sub_id}"]
    if tier > 1:
        out.append(f"add_mastery = {{ amount = {(tier - 1) * 100}"
                   f" sub_doctrine = {sub_id} }}")
    return out


def split_commands_for_history(school_id, tiers):
    """Commands for a country's starting doctrine state."""
    out = [f"set_grand_doctrine = {school_id}"]
    for track_id, tier in tiers:
        if tier >= 1:
            out.extend(buys_for_tier(track_id, tier))
    return out
