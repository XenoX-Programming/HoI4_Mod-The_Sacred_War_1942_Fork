# readme_ai.md — handoff notes for an AI continuing this work

**Project:** The Sacred War – 1942, a Hearts of Iron IV total-conversion mod.
**Task:** make the mod work on the current game version again.
**Target game version:** 1.20.\* (1.20 released 19 Nov 2026).
**Where the work stands:** the mod parses clean, the land-doctrine system has been
ported to the 1.17+ grand-doctrine system, and all dead technology/doctrine ids
have been resolved. It has **not been run in the game** — see
[What is still unverified](#7-what-is-still-unverified). That is the next job.

Read this file top to bottom before changing anything. Section 9 lists the traps
that already cost time once.

---

## 1. TL;DR — what was wrong and what was done

The mod was built for **1.14.6** (the last 1.x that HoI4 wikis list before the
doctrine overhaul). Between 1.14 and 1.20 Paradox replaced two systems the mod
relied on:

| System | Before | 1.17+ |
| --- | --- | --- |
| Land doctrine | 64 technologies in `common/technologies/land_doctrine.txt` bought with research | 4 *grand doctrines* → *tracks* → *subdoctrines* with 5 *rewards* each, bought with army XP and advanced with *mastery* |
| Naval / air / special-forces doctrine | technology lines (`fleet_in_being`, `air_superiority`, `rangers`, …) | also grand doctrines (`new_fleet_in_being`, `new_operational_integrity`, `special_forces_quality`, …) |

Consequences that had to be fixed:

* 64 removed land-doctrine technology ids were still in `common/technologies/`.
* 34 removed naval/air/special-forces doctrine ids were still being granted from
  history and scripted effects.
* 22 history files granted doctrines in ways that no longer resolve.
* `cl_tech` no longer exists (light cruisers merged into `ca_tech`).
* `supply_factor` is no longer a modifier key.
* A stale vanilla `industry.txt` / `artillery.txt` shadowed the modern
  technology trees (see §4.2) — this was costing the mod the whole coal/energy
  branch and 8 artillery technologies.
* Pre-existing syntax errors: two unbalanced-brace files.

What changed, in numbers:

* **+12 new files**: 8 subdoctrine files, 1 track file, 1 grand-doctrine file,
  2 localisation files.
* **−4 removed**: the 64-tech `land_doctrine.txt` (moved to `design_record/`),
  the two stale vanilla technology overrides, two pure-vanilla on_action files.
* **49 files edited**, almost all of them history files.
* **957 files deleted** (`the_sacred_war_1942/3142844611/`, a 50 MB vendored
  copy of an unrelated workshop mod that shipped inside the upload).

---

## 2. Repository layout that matters

```
Mod/
  The Sacred War - 1942.mod         the launcher descriptor (only .mod file now)
  the_sacred_war_1942/              the mod itself (56 MB)
    common/doctrines/                NEW - the ported doctrine tree
      grand_doctrines/sw_land_grand_doctrines.txt
      tracks/sw_land_tracks.txt
      subdoctrines/land/sw_*_subdoctrines.txt   (8 files)
    design_record/
      land_doctrine_1942_original.txt  the OLD 64-tech tree, kept, NOT parsed
    common/technologies/
      special_techs.txt                only file left; 2 mod-only techs
    common/scripted_effects/sacred_war_effects.txt   doctrine "bundles" here
    history/countries/*.txt            37 files, doctrine seeding lives here
    localisation/english|russian/sw_doctrines_l_english.yml / _l_russian.yml

Mod_Development_Tools_&_Files/
  Logs/                             ALL error logs go here (see below)
tools/                              all the machinery, see §3
```

`Mod/the_sacred_war_1942/3142844611/` is gone. Do not restore it: it was a nested
copy of somebody else's mod, 953 files, that the game would try to load twice.

---

## 3. The tools in `tools/`

All are plain Python 3, standard library only, and all are **idempotent** — it is
safe to re-run them. Always run the three checkers after any change.

| Tool | Purpose |
| --- | --- |
| `pdxparse.py` | Minimal PDXscript tokenizer/parser. `Node` has `.key .op .value .children`, `.get()`, `.getall()`, `.is_block`. |
| `check_mod.py` | Brace balance + duplicate top-level id detection across every script file. |
| `check_doctrines.py` | **Doctrine-specific** validation: track references, 5 rewards, one milestone per track, localisation keys, unreachable tracks. |
| `check_vanilla_ids.py` | Cross-checks every technology/doctrine/tactic id the mod references against a dump of vanilla 1.20 ids. |
| `vanilla_1_20_ids.json` | The id dump used by the checker. Regenerate with `check_vanilla_ids.py --vanilla <install path>`. |
| `doctrine_map.py` | **Single source of truth** for the mapping: schools, tracks, chains, spine, the naval/air/SF mapping table, `GD_FOLDER`. |
| `gen_doctrines.py` | Writes `common/doctrines/**` and the doctrine localisation from `design_record/…` + `doctrine_map.py`. |
| `convert_history_doctrines.py` | Rewrites `history/countries/*.txt` and `common/scripted_effects/*.txt`. |
| `migrate_1_20.py` | Reporting + the small mechanical migrations. Writes `migration_report.txt`. |
| `doctrine_conversion_report.txt`, `migration_report.txt` | Generated reports, regenerated on every run. |

Typical loop after changing anything:

```bash
python3 tools/gen_doctrines.py                     # rebuild the tree
python3 tools/convert_history_doctrines.py --apply  # rebuild history seeding
python3 tools/check_mod.py
python3 tools/check_doctrines.py
python3 tools/check_vanilla_ids.py
```

Current expected output: **0 errors, 0 warnings, 0 undefined ids.**

---

## 4. The doctrine port in detail

### 4.1 How the old tree was mapped

The old tree (/tmp-level detail in `design_record/land_doctrine_1942_original.txt`)
was four schools, each with a shared spine and two branches that later converged.

```
mobile_warfare → delay → elastic_defence ─┬→ mobile_infantry → … → modern_blitzkrieg
                                          └→ armored_spearhead → … → werwolf_guerillas
                                                            (kampfgruppe is shared)
superior_firepower → sup_delay → mobile_defence ─┬→ intergrated_support → …
                                                 └→ centralized_fire_control → …
trench_warfare → grand_battle_plan → prepared_defense ─┬→ grand_assault → … → c3i_theory
                                                       └→ infantry_offensive → …
mass_assault → pocket_defence → defence_in_depth ─┬→ large_front_operations → …
                                                  └→ peoples_army → …
```

Mapping rules, all encoded in `tools/doctrine_map.py`:

* **root tech + every shared prerequisite** → the grand doctrine's own effects.
  Nothing is lost: a player who used to take the root automatically got these.
  `kampfgruppe` is shared by both mobile branches, so it is part of the mobile
  grand doctrine rather than of either track.
* **each old branch → one track.**
* **first tech of a branch → the subdoctrine** (what you bought first).
* **next techs → at most five rewards.** 1.17+ allows up to five reward slots.
  Branches with 6–8 tiers merge the surplus into reward 1, which is where the
  surplus tier would have been bought. Branches with fewer than five tiers have
  fewer rewards (3–4); **empty reward blocks are not emitted**, since they buy
  nothing and are structurally unusual.
* **terminal tech → the milestone**, positional to `tracks`.
* `masterful_blitz` was an orphan (nothing led to it). Folded into the mobile
  motorised milestone.

Result: 4 grand doctrines, 8 tracks, 8 subdoctrines, 5 rewards each, 8 milestones.

### 4.2 Modifier merging — read this before editing generated files

Old techs set the same modifier key on the same unit category more than once
(e.g. `max_organisation` on `category_all_infantry`). A HoI4 block cannot hold
two `max_organisation` lines — the game keeps one — so the generator
(`merge_effects`) merges them:

* per-battalion keys in `ADDITIVE` are **summed** (max_organisation, defence,
  breakthrough, …),
* duplicate `enable_tactic` is kept as separate lines (unlocks stack),
* `additional_brigade_column_size` keeps the maximum (it is capped),
* everything else keeps the larger value.

The generator prints any merged key. Currently exactly one exists:
`max_organisation` 15 + 10 → 25 in the mobile-warfare grand doctrine. If that
number looks wrong, fix `merge_effects`, not the generated file.

### 4.3 One dangling reference was dropped

`masterful_blitz` enabled `tactic_masterful_blitz`, which is defined **neither**
in vanilla 1.20's `common/combat_tactics.txt` (51 tactics checked) **nor anywhere
in this mod**. It did nothing before the port either. It is dropped and logged.
If you want it back you must write a real tactic definition — do not just
re-add the id.

### 4.4 Naval, air and special-forces doctrines

The mapping is in `DOCTRINE_TECHS_OTHER` in `doctrine_map.py`, by **role**:

* `fleet_in_being`, `battlefleet_concentration`, `convoy_sailing`,
  `convoy_escorts` → `new_fleet_in_being`
* `trade_interdiction`, `unrestricted_submarine_warfare`,
  `convoy_interdiction_ti`, `raider_patrols`, `submarine_operations*` →
  `new_convoy_raiding`
* `base_strike`, `naval_strike_tactics`, `carrier_primacy`,
  `carrier_task_forces`, `subsidiary_carrier_role` → `new_base_strike`
* `air_superiority`, `dogfighting_experience`, `formation_flying`,
  `fighter_baiting`, `home_defence` → `new_operational_integrity`
* `infrastructure_destruction` → `new_strategic_destruction`
* `direct_ground_support`, `dive_bombing`, `low_echelon_support`,
  `force_rotation`, `dispersed_fighting` → `new_battlefield_support`
* the four special-forces techs → `special_forces_quality` (grand doctrine only)

**A country holds one grand doctrine per folder.** 22 history files wanted two or
three from the same folder; `one_per_folder()` keeps the first and logs the rest.
The decision matters because the last write would otherwise win and silently wipe
the earlier pick (and reset that folder's mastery).

`special_forces` is intentionally only the grand doctrine: 1.20's
special-forces subdoctrines are keyed on subunits (`mountaineers_1`,
`rangers_2`, …) and gated on vanilla technology (`has_tech = tech_mountaineers`).
Mapping the mod's four techs onto specific subdoctrines would have meant guessing.

### 4.5 What was deleted outright

Six ids have no safe 1.20 replacement this mod can stand in for, so the grants
were removed and logged rather than guessed:

`basic_medium_battery`, `early_ship_hull_carrier`, `decimetric_radar`,
`improved_decimetric_radar`, `improved_centimetric_radar`,
`improved_airplane_launcher`.

MTG split cruiser batteries into light/heavy, so `basic_medium_battery` has no
direct equivalent; substituting one would silently enable the wrong equipment
modules in naval designers. See §7 — these are the first things to check in the
error log.

---

## 5. How a country gets a doctrine at game start

1.17+ has no technology-based doctrine research, so doctrine selection is done in
`history/countries/<TAG>.txt` at **top level** (not inside `set_technology`,
whose action list `set_grand_doctrine`, `set_sub_doctrine` and `add_mastery` are
*not* part of). Verified pattern, used by working 1.17+ mods:

```pdx
set_grand_doctrine = sw_grand_battleplan
set_sub_doctrine   = sw_gb_battleplan
add_mastery = { amount = 200 sub_doctrine = sw_gb_battleplan }
```

* `set_grand_doctrine` takes the grand doctrine.
* `set_sub_doctrine` takes tier 1 of that track.
* **Mastery is the only way to advance** (100 per reward, 500 completes a track),
  `add_mastery` is how history buys the tiers a country "already had": 100 per
  extra tier, emitted only when a country starts above tier 1. This is the
  documented form and the one Cold War: Iron Curtain uses in its country
  history. `M.split_commands_for_history()` builds the command list.

The converter inserts these in the file header, after `capital`/`oob`/the first
`set_technology`, and always before the first top-level `if`/`date` block. In
`common/scripted_effects/*.txt` it instead replaces the emptied `set_technology`
block in place, so each scripted effect stays self-contained (converting the
file as a whole would have collapsed all seven doctrine bundles into one).

---

## 6. Non-doctrine changes also included

* **`cl_tech` → `ca_tech`**, 14 focus sites + 2 AI-weight sites. Where a block
  already had `ca_tech` the duplicate line was dropped, and in `ai_focuses/` the
  weights were *summed* so the AI's relative interest in cruisers is preserved.
* **`supply_factor` → `supply_consumption`** (1 site, dynamic modifier).
  `out_of_supply_factor` is a different, still-valid key — do not touch it.
* **`descriptor.mod`** rewritten: `version="2.0.0"`,
  `supported_version="1.20.*"`, no `replace_path` (see §9.1).
* **`common/ideas/SOV.txt`** and **`history/countries/NOR - Norway.txt`**:
  unbalanced braces fixed (one unclosed `ideas = {`, one unclosed `if`).
* **`common/names/sw_add_names.txt`**: an orphan `SND = {` names block renamed;
  `SND` is not a tag this mod (or vanilla) defines.
* **Deleted** `common/on_actions/06_bftb_on_actions.txt` and
  `08_bba_on_actions.txt` — verified pure vanilla (zero mod-specific references),
  and stale copies of vanilla on_actions are a classic source of duplicate/missing
  on_action hooks.
* **Deleted** `common/technologies/industry.txt` and `artillery.txt`. Both were
  stale vanilla copies. `industry.txt` was missing the entire 1.17 coal /
  energy-gain rework; `artillery.txt` was missing 8 technologies including all
  the special-project ones, and used pre-1.19 SP-artillery subunits
  (`light_sp_artillery_brigade`) that no longer exist. Because they have vanilla
  file names they were overriding the real trees. Deleting them restores vanilla.

---

## 6b. Where the error logs live (READ THIS FIRST)

Every error log belongs in **`Mod_Development_Tools_&_Files/Logs/`**. That is the
only place to look for a new one.

Filename convention, given by the user: `error_log_YYMMDD_HHMM.<ext>`, where the
**first number is the date and the second is the hour the log was created**.
So `error_log_251126_1948.log` is 2025-11-26, 19:48 and
`error_log_251126_2005.log` was created at 20:05 the same day. Later logs
therefore sort naturally by name. The original upload was a `.txt`; the user
renamed it, and future logs will be **`.log`**.

Uploads do **not** reach the agent sandbox as files. The user instead commits the
log to this repository through the GitHub web UI. So when a new log is expected:
`git fetch` and look in `Mod_Development_Tools_&_Files/Logs/`.

---

## 7. What is still unverified

> **Known cause of the first crash on load: a UTF-8 BOM.** A real 1.20 error log
> (`error_log_251126_1948.log`) showed `Error: unexpected token in file: ...
> near line: N ( \ufeff )` in ten `common/doctrines/**` files, `common/ideas/
> army_spirits.txt`, `common/ideas/SOV.txt`,
> `common/dynamic_modifiers/0_dynamic_modifiers.txt` and
> `common/scripted_effects/sacred_war_effects.txt`. HoI4's script parser treats
> the BOM as a stray token, so **the whole file fails to load**; every id it
> defines then reads as undefined, which is what produced the flood of
> "Unknown effect-type", "Grand doctrine ﻿ has no folder assigned" and
> "Unknown History Command" errors. Cause: `tools/migrate_1_20.py` rewrote
> matched files with `encoding="utf-8-sig"`. That is fixed, the BOMs are gone,
> and `tools/check_mod.py` now fails on a BOM in `common/doctrines`,
> `common/ideas`, `common/scripted_effects` and `common/dynamic_modifiers`.
> **`localisation/**/*.yml` must keep a BOM** — that is a different parser and
> every other loc file in this mod has one.

### The second log (`error_log_251126_2005.log`, 20:05)

The BOM problem is **fixed and confirmed gone**: the new log contains zero
U+FEFF characters, and the whole cascade it caused has disappeared —

| error | 19:48 log | 20:05 log |
| --- | --- | --- |
| `unexpected token ... ( U+FEFF )` | 13 files | **0** |
| `Grand doctrine has no folder assigned` | yes | **0** |
| `Subdoctrine has no track/rewards` | yes | **0** |
| `Unknown effect-type <scripted effect>` | 6+ | **0** |
| any `sw_*` id mentioned in an error | many | **0** |

What is left is **all pre-existing and unrelated to the port**:

* 562 `unexpected token` — every single one is a **vanilla** file the mod does
  not ship (`events/WUW_*.txt`, `common/scripted_effects/JAP_scripted_effects.txt`,
  `music/aat_songs.txt`, …). This mod overwrites vanilla focus/event files, so
  those files' ids break. Present before the port too.
* 742 `Province with id N is already added to state` + 10 `State ID conflict` —
  `history/states/` overriding vanilla states under different filenames.
* `Malformed token: @chief_experience_gain_medium` (`country_leader/sw_traits.txt`)
  and `Unknown modifier: supply_consumption` (`dynamic_modifiers/0_dynamic_modifiers.txt`)
  — mod-only tokens the engine cannot resolve. Also pre-existing.
* The log **ends** at the normal last line, `The game has loc key collisions`,
  at 20:05:29, i.e. validation completed. So the failure is **after** validation,
  and an error.log alone will not name it. `logs/crash.txt` and the exception
  dump in `logs/` (if present) are what is needed now.

**The mod has never been loaded in HoI4 in this environment.** There is no game
install in the sandbox. Everything below is "should work" logic-checked, not
observed. Ask the user for `error.log` (they were told to drop it in
`Mod_Development_Tools_&_Files/`; it is still absent). Check in this order:

1. **Doctrine load errors.** If `common/doctrines` is malformed the game logs it
   and falls back to vanilla. Symptoms: no new doctrines in the officer corps.
2. **Sprite names.** These are **unverified guesses** and the most likely source
   of missing-art spam. Every one must be checked against a real
   `interface/*.gfx`:
   * `GFX_doctrine_mobile_warfare_medium`
   * `GFX_doctrine_superior_firepower_medium`
   * `GFX_doctrine_grand_battleplan_medium`
   * `GFX_doctrine_mass_assault_medium`
   * `GFX_mob_warfare_bg`, `GFX_sup_firepower_bg`, `GFX_grand_battleplan_bg`,
     `GFX_tac_operation_bg` (track backgrounds)
   * `GFX_doctrine_decor_land` (track `icon_frame`)
   * `GFX_doctrine_milestone_infantry_land`, `_armored_land`, `_artillery_land`,
     `_operations_land` (track icons + milestone art)
   A missing sprite is cosmetic but noisy; a missing *background* can break the
   doctrine screen layout. Fix by pointing at a sprite that does exist (vanilla
   `GFX_doctrine_*`), or add the art.
3. **`track` accepting a single id.** Vanilla uses both forms
   (`track = armor` and `track = { a b }`), so a single id should be fine.
4. **Tracks with fewer than five rewards.** Four subdoctrines have 3–4 rewards
   because their old branch had fewer tiers. Confirm 1.17+ accepts fewer than
   five reward entries (vanilla always has exactly five). If it does not, pad the
   short ones by splitting an existing merged reward.
5. **`add_mastery` in history.** Only 8 of the 34 seeded countries need it
   (tier > 1), at 100 per extra tier. Confirm the tiers actually apply at
   scenario start. The log from the BOM run did not reach history validation
   for the doctrine files, so this is still untested in game.
6. **The six dropped techs** (§4.5) — check nothing downstream (naval designers,
   equipment variants, AI templates) depended on them.
7. **Naval/air grand doctrines.** 34 of the 37 country files now also carry the
   modern naval and air doctrines. If naval combat feels wrong, this is why — it
   is a deliberate behaviour change from "these were techs" to "these are the
   1.20 doctrines".
8. **`special_techs.txt`** defines two mod-only techs
   (`Chinese_Infantry_technology`, `Sniper_Unlock`). Both have
   `allow = { always = no }`, so they are unreachable by design; their subunits
   (`chi_infantry`, `sniper` in `common/units/`) do exist. Verify they are meant
   to be granted rather than researched.

---

## 8. If the user wants something changed

* **Doctrines too strong / too weak** → edit `tools/doctrine_map.py` chains, not
  the generated files, then re-run `gen_doctrines.py`.
* **Hide the vanilla four land grand doctrines** (both sets are currently
  selectable, which is a genuine design choice worth confirming): vanilla's four
  land grand doctrines are `new_mobile_warfare`, `superior_firepower`,
  `grand_battleplan` and `mass_assault`, verified from vanilla 1.20's own
  `common/ideas/army_spirits.txt`, which gates spirit choices on them. Note the
  `new_` on mobile warfare; plain `mobile_warfare` does not exist in 1.20.
  Cleanest way is `replace_path = "common/doctrines/grand_doctrines"` **plus**
  shipping copies of the naval/air/SF grand doctrine files — *not* just the
  replace_path, or those folders' doctrines disappear.
* **Update to a newer patch** → re-dump ids
  (`check_vanilla_ids.py --vanilla <path>`) and re-run the checkers. The dump is
  what caught the naval/air doctrine removal; keep it current.
* **`text`, not `readme`** → no. Keep `readme_ai.md` (this file) and
  `readme.md` (user-facing) in sync.

---

## 9. Traps that already cost time

1. **`replace_path` is a blunt instrument.** An earlier draft had
   `replace_path = "common/technologies"` — which deletes *every* vanilla
   technology the mod does not ship, i.e. almost all of them. It also had
   `replace_path` on `common/doctrines/{grand_doctrines,tracks,subdoctrines}`,
   which deletes vanilla's naval/air/special-forces doctrines. Both removed. The
   mod instead relies on same-file-name overriding, which is how it always worked.
2. **Do not trust "the wiki says it was removed".** An earlier pass believed
   1.17 removed `improved_equipment_conversion`, `synth_oil_experiments`,
   `fuel_silos` and the `fuel_refining` line, and rewrote 24 history files on that
   basis. All of them still exist in vanilla 1.20. Always check an actual file
   tree. `migrate_1_20.py` now hard-codes the correction so it cannot regress.
3. **Do not build a whole-file doctrine conversion.** `sacred_war_effects.txt` has
   seven doctrine bundles in one file. Converting per file collapsed them into a
   single school. Convert per `set_technology` block.
4. **Do not convert by line index.** Insertion indices shift as lines are removed
   and produced commands inside nested `if` blocks. Replace blocks in place.
5. **`git checkout --` will eat uncommitted fixes.** It reverted the NOR brace fix
   twice. Re-apply and re-run `check_mod.py`.
6. **The mod's own technology files win over vanilla.** Before deleting or
   "fixing" a technology, check `common/technologies/` — `synth_oil_experiments`
   and friends are defined there.
7. **`pdxparse` stores the last bare word of a list as a child with `op '='`.**
   `tracks = { a b }` arrives as one child `a` with value `b`. `check_doctrines.py`
   reads the list from raw text for this reason.
8. **Only 1.20 layout differs from 1.14 in `common/ai_templates`** — the
   `templates_SOV.txt` `has_tech` rewrite is the one AI change made; other AI
   files were left alone.

---

## 10. Provenance of the facts in this file

* Patch dates/features: HoI4 wiki `Patches`, `Patch 1.17`, `Patch 1.18`,
  `Patch 1.19`, `Officer corps`.
* Vanilla 1.20 id lists: a vanilla 1.20 stub tree (`data/blank_mod` published by
  Vic3ToHoI4), plus `EaW-Team/equestria_dev` 1.20 doctrine files for the naval /
  air / special-forces grand-doctrine ids, which the stub tree does not contain.
  Caveats are recorded inside `tools/vanilla_1_20_ids.json`.
* 1.17+ doctrine file format and the `set_grand_doctrine` / `set_sub_doctrine` /
  `add_mastery` idioms: `Cold-War-Iron-Curtain-Dev-Team/ColdWarIronCurtain`
  (its `history/countries/USA` uses the exact pattern), vanilla
  `armor_subdoctrines.txt`, and EaW's `_documentation.md`.
* The old doctrine payload (every modifier) is read verbatim from
  `design_record/land_doctrine_1942_original.txt`. **No modifier value in the
  port was invented.**
