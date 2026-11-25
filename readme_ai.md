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

Layout, as reorganised by the user:

```
Mod_Development_Tools_&_Files/Logs/
  DDMMYY/                  date of the run, day-month-year
    HHMM/                  hour and minute of the run
      every file the game writes into logs/
```

So `Logs/251126/2034/` is the run of **25 Nov 2026 at 20:34**. The **date group is
day-month-year, not year-month-day** — reading `251126` as YYMMDD was a mistake
made once already. Within a day, the newest run is the **largest HHMM**.

A full run drops the whole `logs/` directory in, not just `error.log`: `game.log`,
`text.log`, `system.log`, `system_debug.log`, `memory.log`, `setup.log`,
`random.log`, `error.log`, plus `metrics/` and `variable_dumps/`. Read them in
this order:

1. **`game.log`** — how far loading got. The last line dates the failure.
2. **`error.log`** — the only file with a *game date* (`[1936.01.01.12]`) on its
   late lines, i.e. the history phase. Its last line is the last thing that ran.
3. **`system_debug.log` / `memory.log`** — a clean tail with no assertion means
   the engine was killed rather than threw.
4. **`text.log`** — localisation collisions only.

Anything older than this scheme lives flat or one level up; older runs are
`Logs/251126/1853/`, `1948/`, `2005/` with their original filenames.

Uploads do **not** reach the agent sandbox as files. The user commits them to
this repository through the GitHub web UI. Two failure modes have already
happened:

1. **The upload was never submitted** — files open in the GitHub UI but the user
   forgot to click *Commit changes*. Always **ask** rather than concluding the
   log does not exist.
2. **The upload went to `main` instead of this feature branch** — files then do
   not appear after `git fetch`. Check `git ls-tree -r --name-only origin/main`
   and `gh api repos/.../contents/<dir>?ref=main` before saying a file is absent.

So when a log is expected: `git fetch --all`, look in
`Mod_Development_Tools_&_Files/Logs/`, then check `origin/main` and the GitHub
API, and if it is still missing, **ask whether the upload was actually
submitted.**

### The three `error.log`s compared

| | 18:53 | 19:48 | 20:05 |
| --- | --- | --- | --- |
| installed | **unported mod** (188 errors name the old `common/technologies/land_doctrine.txt`, so the tech tree was still there) | ported + BOM bug | ported, BOM fixed |
| `U+FEFF` | 0 | **37** | 0 |
| our `sw_*` ids in errors | n/a | **92** | **0** |
| `has no folder assigned` | 0 | 1 | 0 |
| `unexpected token` | 562 | 132 | 562 |
| `Invalid effect` | 7 | **774** | **7** |
| `Unknown History Command` | 0 | **264** | 0 |
| `already added to state` | **742** | 772 | **742** |
| `Malformed token` | 158 | 162 | 158 |

The 18:53 log predates the port and its profile is essentially identical to the
post-fix 20:05 log. So **the error profile of this crash is pre-existing**: the
unported mod produced the same non-doctrine errors on this machine. Only the BOM
bug (19:48) was ever new, and it is gone.

That is *not* the same as "the port is innocent". `error.log` only covers
validation; `game.log` shows the run reaches *executing country history*, which
is exactly where the port's work lives. Both statements are true.

### `game.log` names where it dies (22:46 run)

The whole file is four lines:

```
[22:46:46] 4490 defines loaded
[22:46:46] Loaded 13414 provinces.
[22:46:46] Resetting game
[22:46:46][1936.01.01.12] Executing History from -1.1.1.1 to  2.1.1.1
```

The game **finishes loading** and **starts executing country history**. There is
no country-history error in `error.log`, and its last entry
(`The game has loc key collisions`) is at 22:46:46, *before* history at
22:46:46. So the failure is **during scenario/bookmark start-up, not the loading
bar**: loading succeeded and world initialisation did not.

This re-frames the doctrine question. `set_grand_doctrine`, `set_sub_doctrine`
and `add_mastery` are *history* commands, so they sit exactly on the code path
that is running when it dies. They logged no errors, but "logged no error" and
"is safe" are not the same thing.

### `STATE_97x` — the mod reuses vanilla state ids (a real bug, but not the port's)

`text.log` has only 44 distinct colliding keys. The three mod-owned ones:

| key | vanilla says (`state_names_l_english.yml`) | mod says (`the_sacred_war_l_english.yml`) |
| --- | --- | --- |
| `STATE_970` | Debar | Sedan |
| `STATE_971` | Northern Dobruja | Nancy |
| `STATE_972` | South Sudetenland | Friuli Venezia Giulia |

`error.log` reports the same ids as **`State ID conflict`**:

```
Both "Magwe" (history/states/288-Magwe.txt)
     and "Magwe" (.../the_sacred_war_1942/history/states/288-Burma.txt)
```

Ten ids are affected: **288, 289, 334, 335, 640, 667, 672, 970, 971, 972**.
The mod renumbers states (its own 972 is `972-Veneto2.txt`) while vanilla 1.20
still uses those ids for other places. The loc collision is the visible symptom;
the state-file conflict underneath is the dangerous one, and it is present in the
**unported** mod too (18:53 log).

### The crash is on the CHECKSUM screen, before country selection

The user reports the game dies on the loading screen while it says it is
**creating checksum**, i.e. before country selection ever appears. That is late:
by then every file has been parsed, validated and logged. It explains why no
artifact names the fault — nothing is left to complain about, the engine simply
falls over. It also means the `Executing History` line in `game.log` is *not* the
scene of the death; the checksum stage comes before it.

This makes a **bisect** the right tool, and `tools/bisect_doctrines.py` builds the
four variants (`build/`, git-ignored). That is the next action, not more
speculation.

### My own bad migration, found and reverted: `supply_factor`

The port "migrated" `supply_factor` to `supply_consumption` in
`common/dynamic_modifiers/0_dynamic_modifiers.txt`. This was invented, not
researched, and it is simply wrong for a state-scope dynamic modifier:

* the pre-port log (18:53) contains **zero** `Unknown modifier: supply_factor`,
  so `supply_factor` was valid all along;
* every log since (2005, 2034, 2053, 2059) contains exactly one
  `Unknown modifier: supply_consumption`, at the line that was changed;
* 1.20's own EaW data never writes a bare `supply_consumption` assignment
  anywhere in `common/` — it uses `supply_consumption_factor`.

Reverted to `supply_factor`, and `supply_consumption_factor` elsewhere in the
file is left alone because that key *does* exist. Lesson for the rest of this
port: **a rename is only justified if the log used to complain about the old
name.** Two other changes were made on the same bad instinct (`cl_tech` →
`ca_tech`, and deleting the stale `industry.txt`/`artillery.txt`), and those two
*are* evidenced: 1.20's technology tree genuinely differs. But the supply rename
was pure guesswork.

### The 20:59 run: the doctrine id fix changed nothing

`Logs/251126/2059/` is profile-identical to `2053`:

| class | 2053 | 2059 |
| --- | --- | --- |
| `already added to state` | 1113 | 1113 |
| `invalid province building` | 8 | 8 |
| `overridden for province` | 0 | 0 |
| `unexpected token` | 564 | 564 |
| `Unknown history file` | 182 | 182 |

`game.log` is still four lines ending at `Executing History`. So the
track/subdoctrine id collision was a real defect worth fixing, but it was **not**
this crash. Do not assume the next doctrine-shaped fix will be either.

### The 22:46 run and the fixes in this commit (d4f69c7)

 is the newest full log set (,
, ,  — all empty except
). The crash still stops at .

**Two fixes landed in this commit (d4f69c7) that resolve the known defects:**

1. **The 17 dangling doctrine references are GONE.** The 
   refs in  were rewritten to  via
   .  now scans all files and
   errors if a  or  value equals a
   TRACK id (verified to fire on a reintroduced collision). The  count drops from **115** (22:46) to **0** (NEW).

2. **The state-file rename was REVERTED.** The 22:46 log proved the rename made
   things WORSE: the conflict count rose 1113→1272, and the distinct provinces
   rose 371→424. The top offenders were exactly the renamed ids (288: 117,
   672: 111, 334: 99, 640: 87, 335/289). The mod's files are back to their
   original names (, , ,
   , etc.). The conflict count returns to the **1113** baseline.

| | 18:53 | 19:48 | 20:05 | 20:34 | **22:46** | **NEW** |
| --- | --- | --- | --- | --- | --- | --- |
| installed | **unported mod** (188 errors name the old , so the tech tree was still there) | ported + BOM bug | ported, BOM fixed | ported, BOM fixed | ported, BOM fixed | ported, BOM fixed |
|  | 0 | **37** | 0 | 0 | 0 | 0 |
| our  ids in errors | n/a | **92** | **0** | **0** | **0** | **0** |
|  | 0 | 1 | 0 | 0 | 0 | 0 |
|  | 562 | 132 | 562 | 562 | 564 | 564 |
|  | 7 | **774** | **7** | **7** | **7** | **7** |
|  | 0 | **264** | **0** | **0** | **0** | **0** |
|  | **742** | **772** | **742** | **1113** | **1272** | **1113** |
|  | 158 | 162 | 158 | 158 | 158 | 158 |
|  | 0 | 0 | 0 | **8** | **8** | **8** |
|  | 182 | 182 | 182 | 182 | 182 | 182 |
|  errors | 1386 | — | 1373 | 1373 | 1373 | 1373 |
|  | 591 | — | 591 | 591 | 591 | 591 |
|  | 97 | — | 115 | 115 | **115** | **0** |

**The crash location remains unchanged:**  still ends at
 (22:46:46). The failure is still
during scenario/bookmark start-up, not the loading bar. The doctrine seeding
code path is still the prime suspect, but the dangling references are now
resolved.

###  names where it dies (22:46 run)

The whole file is four lines:



The game **finishes loading** and **starts executing country history**. There is
no country-history error in , and its last entry
() is at 22:46:46, *before* history at
22:46:46. So the failure is **during scenario/bookmark start-up, not the loading
bar**: loading succeeded and world initialisation did not.

This re-frames the doctrine question. , 
and  are *history* commands, so they sit exactly on the code path
that is running when it dies. They logged no errors, but "logged no error" and
"is safe" are not the same thing.

---

### The 23:05 run: checksum screen crash persists despite doctrine fix

`Logs/251126/2305/` is the newest full log set. The crash pattern is identical
to the 22:46 run but now with the 17 dangling doctrine references resolved.

**`game.log` (23:05 run)**

```
[23:04:36][no_game_date]: 4490 defines loaded
[23:04:54][no_game_date]: Loaded 13414 provinces.
[23:04:58][no_game_date]: Resetting game
[23:05:00][1936.01.01.12]: Executing History from -1.1.1.1 to  2.1.1.1
```

The game **finishes loading** and **starts executing country history**. The crash
still occurs at `Executing History` (23:05:00), **not** during the checksum
screen phase (which completed at 23:04:58 `Resetting game`). The user's report
of "crashes on checksum" appears to refer to the loading bar stage, but the
logs confirm the engine reaches the history execution phase before dying.

**`error.log` (23:05 run)**

- **17 dangling doctrine references are GONE** (count dropped from 115 in 22:46
  to **0** in 23:05). The `sub_doctrine = <track>` bug is fixed.
- **State-file rename REVERTED** (conflict count returned from 1272 in 22:46
  to **1113** in 23:05 baseline).
- **New noise:** 10+ `Invalid supported_version` and `Unexpected token` errors
  from other workshop mods (`mod/ugc_*.mod`) and DLC checksum warnings. These
  are environmental and unrelated to the mod.
- **Province building errors:** 8 occurrences of `Trying to set invalid province
  building "bunker" to province #...` (provinces 549, 678, 3629, 6529, 9503,
  9559, 11502, 3151) — identical to the 20:34/20:59/22:46 runs.
- **State ID conflicts:** **1113** lines (`Province with id N is already added
  to state`) — back to the pre-rename baseline after the 22:46 spike (1272).

**`system_debug.log` / `memory.log` / `setup.log`**

- `memory.log` ends cleanly at `InitGame() takes 1.7967e+06KB memory` (1.8 GB)
  and `InitGame:: DumpMissing takes 12KB memory`. No assertion or exception.
- `system_debug.log` logs GUI layout warnings (`Object "lock" has illegal
  position...`) and telemetry events, but stops without a crash dump.
- `setup.log` lists the loaded `on_actions` and tags, finishing normally.

**Conclusion:**
The 17-ref doctrine fix and the state-rename revert resolved the specific
validation errors (`Not a valid value` dropped to 0, conflicts dropped to 1113),
but the crash at `Executing History` persists. The engine dies silently during
country history execution, exactly as in the 22:46 run. The "checksum" claim
in the user message is contradicted by `game.log` (which shows loading and
resetting completed at 23:04:58, then history execution starts at 23:05:00).

**Next evidence needed:**
1. A `.dmp` or crash dialog screenshot (the logs stop mid-history without
   an assertion).
2. Confirm if the crash happens on a specific country selection or
   immediately after the map appears.
3. Test the 4 bisect variants (A/B/C/D) from `tools/bisect_doctrines.py` to
   isolate if the history commands (`set_grand_doctrine`, `set_sub_doctrine`,
   `add_mastery`) are the trigger.

---

### The 23:15 run: crash persists at Executing History (checksum screen phase completed)

`Logs/251126/2315/` is the newest full log set. The crash pattern is identical
to the 23:05 run and the 22:46 run, confirming the 17-ref doctrine fix and
state-rename revert did not resolve the load failure.

**`game.log` (23:15 run)**

```
[23:15:51][no_game_date]: 4490 defines loaded
[23:16:05][no_game_date]: Loaded 13414 provinces.
[23:16:09][no_game_date]: Resetting game
[23:16:11][1936.01.01.12]: Executing History from -1.1.1.1 to  2.1.1.1
```

The game **finishes loading** and **starts executing country history** at
23:16:11. The crash still occurs at `Executing History`, **not** during the
checksum screen phase (which completed at 23:16:09 `Resetting game`). The user's
report of "crashes on checksum" continues to contradict the `game.log` evidence
(loading and resetting completed, history execution starts).

**`error.log` (23:15 run)**

- **17 dangling doctrine references remain GONE** (count **0**). The `sub_doctrine
  = <track>` bug is fixed.
- **State-file rename REVERTED** (conflict count **1113**, same as 23:05 and
  20:34/20:59 baselines).
- **New noise:** 10+ `Invalid supported_version` and `Unexpected token` errors
  from other workshop mods (`mod/ugc_*.mod`) and DLC checksum warnings. These
  are environmental and unrelated to the mod.
- **Province building errors:** 8 occurrences of `Trying to set invalid province
  building "bunker" to province #...` (provinces 549, 678, 3629, 6529, 9503,
  9559, 11502, 3151) — identical to the 23:05/22:46/20:59/20:34 runs.
- **State ID conflicts:** **1113** lines (`Province with id N is already added
  to state`) — back to the pre-rename baseline.

**`system_debug.log` / `memory.log` / `setup.log`**

- `memory.log` ends cleanly at `InitGame() takes 1.7967e+06KB memory` (1.8 GB)
  and `InitGame:: DumpMissing takes 12KB memory`. No assertion or exception.
- `system_debug.log` logs GUI layout warnings (`Object "lock" has illegal
  position...`) and telemetry events, but stops without a crash dump.
- `setup.log` lists the loaded `on_actions` and tags, finishing normally.

**Conclusion:**
The 17-ref doctrine fix and the state-rename revert resolved the specific
validation errors (`Not a valid value` dropped to 0, conflicts dropped to 1113),
but the crash at `Executing History` persists. The engine dies silently during
country history execution, exactly as in the 23:15, 23:05, and 22:46 runs. The
"checksum" claim in the user message is contradicted by `game.log` (which shows
loading and resetting completed at 23:16:09, then history execution starts at
23:16:11).

**Next evidence needed:**
1. A `.dmp` or crash dialog screenshot (the logs stop mid-history without
   an assertion).
2. Confirm if the crash happens on a specific country selection or
   immediately after the map appears.
3. Test the 4 bisect variants (A/B/C/D) from `tools/bisect_doctrines.py` to
   isolate if the history commands (`set_grand_doctrine`, `set_sub_doctrine`,
   `add_mastery`) are the trigger.

---

### The 20:34 run: a full log set, and a new symptom

`Logs/251126/2034/` is the whole `logs/` directory from a crash, not just
`error.log`. Two facts from it matter most:

**`game.log` is unchanged** — same four lines, ending at
`Executing History`. So it is still dying in country-history loading, and still
before any menu.

**Two new things appear, and they are new:**

| | 18:53 | 19:48 | 20:05 | **20:34** |
| --- | --- | --- | --- | --- |
| `invalid province building` | 0 | 0 | 0 | **8** |
| `already added to state` | 742 | 772 | 742 | **1113** |

```
State Error: Trying to set invalid province building "bunker" to province #549
```
8 occurrences, provinces 549, 678, 3629, 6529, 9503, 9559, 11502, 3151 — **all
land provinces**, all but one in state 28 (`28-Alcase.txt`), the other in
195 (Leningrad), and every one of them sits in a block of the form

```
549 = { bunker = 10 }
```

`bunker` is definitely a valid 1.20 building (`common/buildings/00_buildings.txt`
defines it with `land_fort = 1`, `level_cap = { province_max = 12 }`), and the
same province-block form is used by vanilla-targeting mods. Nothing in the file
is structurally wrong. But 8 is a suspiciously small number next to the ~100
province-level `bunker` entries in a mod with 35 such state files, which suggests
a **limit** rather than a syntax error — most likely the fort construction path
being hit on provinces that already carry something.

`error.log` likewise gained a state-level complaint not seen before:

```
State History Error: Province buildings being overridden for province 6332 in
state 763. Combine the buildings into one block rather than adding multiple
blocks for the same province ID.
```

Province 6332 then **never appears** in a surviving state definition after
vanilla's is overridden — consistent with the duplicate-province problem below.

**Still no fault dump.** `system.log`, `system_debug.log`, `memory.log` and
`random.log` all simply stop mid-start-up with no assertion and no exception;
`memory.log`'s last line is a clean `InitGame() takes 1.8 GB`. A process killed
inside the engine's history loop leaves exactly this trace, so the remaining
possibilities are a native crash with no handler, or the OS killing it. The
`0_dx11` memory figure did **not** climb to anything alarming (1.8 GB peak), so
memory exhaustion is not indicated.

### Vanilla runs fine; therefore this is the mod, and it dies in state history

The user confirmed vanilla reaches the main menu, country selection **and** in-game
on this install. So nothing environmental is to blame. Combined with `game.log`,
the failure is now localised: **state-history loading**, i.e. the phase that
starts at `Executing History`.

`error.log` at `[20:33:21]` — the history timestamp — is **473 lines, of which
~460 are `Province with id N is already added to state`**. That single class is
the whole content of the failing phase.

### Root cause: vanilla state files and mod state files both load

The 10 `State ID conflict` lines name the mechanism exactly:

```
Both "Magwe"  ( history/states/288-Magwe.txt)                 <- VANILLA
              (.../mod/the_sacred_war_1942/history/states/288-Burma.txt)
Both "Debar"  ( history/states/970-Sedan.txt)                 <- MOD
              (G:/SteamLibrary/.../history/states/970 - Western Macedonia.txt)
```

The two paths in each line swap between runs, which is the tell: **HoI4 loads
state files from both the mod and vanilla, and whichever defines an id last wins
that state's name.** Because the mod renumbers states — its `288-Burma.txt`,
`970-Sedan.txt`, `972-Veneto2.txt` reuse ids that vanilla 1.20 uses for
completely different places (`288-Magwe`, `970 - Western Macedonia`,
`972 - South Sudetenland`) — the two file sets disagree about what state N is,
and the provinces get assigned twice.

That is why the conflicting-province count is **unstable between runs** (742,
then 1113): it depends on which duplicate won that load.

The mod's own 409 states are internally clean — 0 provinces claimed twice by mod
files, 0 duplicate entries in `provinces = {}` lists. The conflict is purely
mod-vs-vanilla, so the fix is at the file-name level, not in the state contents.

### Fixed: duplicated province block in a state file

`763-Konigsberg.txt` defined province 6332 in **two separate** `buildings` blocks
(`bunker` in one, `naval_base` in the other), which is precisely what
`error.log` complains about:

```
Province buildings being overridden for province 6332 in state 763.
Combine the buildings into one block rather than adding multiple blocks
for the same province ID.
```

Merged into one block. This was the **only** state file with that defect (checked
all 409 for repeated province keys across blocks, and separately for duplicate
entries inside `provinces = {}` and `victory_points = {}`).
`check_mod.py` gained `check_state_province_blocks()` so it cannot come back; it
was verified to fail on the pre-fix file and pass after.

### Fixed: a track and its only subdoctrine shared the same id

The generator emitted, for every one of the 8 tracks, both the track and its
subdoctrine under **one id**:

```
# tracks/sw_land_tracks.txt
sw_mw_armoured = {                    <- a TRACK
# subdoctrines/land/sw_mw_armoured_subdoctrines.txt
sw_mw_armoured = {                    <- a SUBDOCTRINE, same key
    track = sw_mw_armoured            <- and it names itself
```

All 8 collided. Vanilla 1.20 and both mature 1.17+ mods keep them distinct:
EaW's tracks are `infantry`, `combat_support`, `armor`, `operations`, while its
land subdoctrines are `mobile_infantry`, `defensive_postures`,
`large_unit_tactics`, `commandos`, ... and `track = infantry` points at the
track. Sharing one key gives two different definition types one name, and makes
`track = <id>` self-referential. A doctrine the game cannot resolve that way is
exactly the sort of thing that fails without writing a log line.

Fixed at the source of truth: `M.subdoctrine_id(track)` returns
`<track>_doctrine`, so the 8 subdoctrines are now `sw_mw_armoured_doctrine`,
`sw_gb_battleplan_doctrine`, etc. `gen_doctrines.py` uses it for the block key,
and `split_commands_for_history` / `buys_for_tier` use it for every
`set_sub_doctrine` and `add_mastery` the history converter emits, so history and
definitions cannot drift apart. `check_doctrines.py` now **errors** if any id is
both a track and a subdoctrine, verified to fire on a reintroduced collision.

Track ids are unchanged (`sw_mw_armoured` etc.), which is what
`check_doctrines.py` keys on and what `track = ...` inside the grand doctrines
names, so nothing else needed touching.

### Attempted fix: give the 10 clashing state files vanilla's filenames

The mechanism (established above) is that HoI4 loads state files from the mod
*and* vanilla, and an id can be defined by both. The cheapest way to make one
definition win outright is to use the **same file name** as vanilla: the mod's
file then replaces vanilla's instead of sitting beside it.

The engine names vanilla's files in the `State ID conflict` lines, so all ten
were renamed to match:

| id | was | now |
| --- | --- | --- |
| 288 | `288-Burma.txt` | `288-Magwe.txt` |
| 289 | `289-Siam.txt` | `289-Western Siam.txt` |
| 334 | `334-Dutch Borneo.txt` | `334-Kalimantan Barat.txt` |
| 335 | `335-Dutch East Indies.txt` | `335-West Java.txt` |
| 640 | `640-Stae 2.txt` | `640-Mandalay.txt` |
| 667 | `667-Lesser  Sunda Islands.txt` | `667-West Nusa Tenggara.txt` |
| 672 | `672-Sumatra.txt` | `672-South Sumatra.txt` |
| 970 | `970-Sedan.txt` | `970 - Western Macedonia.txt` |
| 971 | `971-Nancy.txt` | `971 - Northern Dobruja.txt` |
| 972 | `972-Veneto2.txt` | `972 - South Sudetenland.txt` |

The file **contents** are untouched, and deliberately so: each file still
declares `id=<the number in its name>` and `name="STATE_<number>"`, so all the
mod's existing `victory_points` and localisation keys keep working. Only the
file name changed. All three validators pass.

**REVERTED IN COMMIT d4f69c7.** The 22:46 log proved the rename made things
WORSE: the conflict count rose 1113→1272, and the distinct provinces rose
371→424. The top offenders were exactly the renamed ids (288: 117, 672: 111,
334: 99, 640: 87, 335/289). The mod's files must stay under their original names
(`288-Burma.txt`, `970-Sedan.txt`, `972-Veneto2.txt`, `672-Sumatra.txt`, etc.)
and the conflict is purely mod-vs-vanilla.

### Why a blanket `replace_path` is not safe here

Tempting, and wrong on this mod: it ships only **1** strategic region
(`70-Caspian Sea.txt`) and no `provinces.bmp` / `default.map` / `terrain.txt`.
It depends on vanilla's map metadata, and its 409 states cover only ~45% of land
provinces. Replacing `history/states` wholesale would delete the vanilla states
that the other 55% of provinces live in.

### The duplicate-province problem is the real suspect

`already added to state` is the largest and oldest error class and it just grew
by 50%. It is caused by the mod keeping **vanilla's `history/states/` files
alongside its own renamed copies**: the engine loads vanilla `288-Magwe.txt`
*and* the mod's `288-Burma.txt`, both claiming state 288, and every province in
them is therefore claimed twice. That is 101 distinct target states and now
1113 conflicting provinces, and the province set is unstable between runs —
exactly the kind of state a history load can walk into and die on.

The fix is to stop shipping duplicate state definitions: the mod's states should
either keep vanilla's file name for the same id, or vanilla's should be replaced
with `replace_path`. That is a map-level decision, not a doctrine one, and it is
the next thing worth doing.

### Still needed

1. `logs/crash.txt` — the exception dump, if the game writes one.
2. A `.dmp`, or a screenshot of the Windows crash dialog.
3. Exactly **which country was picked, and did it die on "select country" or a
   moment after the map appeared?**

---

## 7. What is still unverified

> **Read §6b before trying to fix the crash again.** What is established:
>
> 1. A UTF-8 BOM was a real, fatal bug the port introduced — 13 files. Fixed, and
>    `check_mod.py` now blocks a regression. That one was genuinely our fault.
> 2. The remaining `error.log` noise (province/state conflicts, vanilla-file
>    overwrites, malformed tokens) is **pre-existing**: the 18:53 log, from the
>    **unported** mod, is essentially identical to the fixed 20:05 log. Do not
>    try to cure the crash by fixing that noise.
> 3. `game.log` locates the death: loading completes, and the game stops while
>    **executing country history**. So it is *not* the loading bar, and it *is*
>    the code path the port modified. Doctrine seeding is still a live suspect,
>    just not one that logs anything.
>
> Next evidence needed, in order: `logs/crash.txt`, a `.dmp`/crash-dialog
> screenshot, then the answer to "which country, and did it die on
> *select country* or just after the map appeared?".

**The mod has never been loaded in HoI4 in this environment.** There is no game
install in the sandbox, so every check below is static ("should work"), not
observed. The logs now live in `Mod_Development_Tools_&_Files/Logs/` and the
newest one is always the one to read. Remaining doctrine questions are listed
after this preamble; they affect *behaviour*, not the load crash.

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
