# The Sacred War – 1942

**Version 2.0.0 — updated for Hearts of Iron IV 1.20.\***

This is the maintenance readme: what the 2.0.0 update changed, what you need to
know to play it, and what to do if something looks broken. For the technical
detail see `readme_ai.md`.

---

## What happened

The mod was built for game version **1.14.6**. Since then Paradox replaced two
systems the mod was built on:

* **Land doctrines stopped being technologies.** In the old version you spent
  research on 64 doctrine technologies across four schools. Since patch 1.17 you
  instead pick a *grand doctrine*, choose *tracks* within it, and buy *rewards*
  with army experience.
* **Naval, air and special-forces doctrines changed the same way.** The old
  technology lines for those are gone too.

Because of that, the mod could not load: it was still defining 64 technologies
that the game no longer supports, and countries were being granted doctrines that
no longer existed.

That has been fixed. The mod keeps **all four original schools** — Mobile
Warfare, Superior Firepower, Trench Warfare and Mass Assault — rebuilt in the new
format with the **same modifiers as before**. No bonus was invented, changed or
dropped on purpose.

---

## The doctrine tree now

Each of the four schools has two **tracks**, and each track has a **subdoctrine**
you take first and then **five rewards** you unlock with mastery (100 mastery per
reward, 500 to finish a track).

| School | Tracks |
| --- | --- |
| **Mobile Warfare** | Motorised Infantry · Armoured Warfare |
| **Superior Firepower** | Combat Support · Fire Support |
| **Trench Warfare** | Battle Plan · Infiltration |
| **Mass Assault** | Broad Front · People's War |

The old trees had up to 8 tiers per branch; the new system allows five rewards,
so the extra tiers were merged into the first reward rather than being thrown
away.

Everything that used to be automatic — the school's shared starting techs — is
now simply part of the grand doctrine, so you get it the moment you pick the
school.

34 of the 37 country files start with the doctrines they used to start with
(the other three never had a land doctrine in the old tree). Germany
opens on Armoured Warfare, the USSR on Broad Front, Britain on Battle Plan,
the USA on Superior Firepower, and so on, with their old head start translated
into mastery.

---

## Installing

Both files you need sit side by side in `Mod/` in this repository:

1. Copy the folder `Mod/the_sacred_war_1942` into
   `Documents/Paradox Interactive/Hearts of Iron IV/mod/`.
2. Copy `Mod/The Sacred War - 1942.mod` into that same `mod/` folder, next to
   the folder from step 1.
3. Start the launcher, enable **The Sacred War – 1942**, and play.

The two must end up as siblings under `mod/`:

```
Hearts of Iron IV/mod/
  The Sacred War - 1942.mod
  the_sacred_war_1942/
```

The `.mod` file points at `path="mod/the_sacred_war_1942"`. If you install
somewhere unusual, fix that one line.

**Requires game version 1.20.** The mod sets `supported_version="1.20.*"` and
will show as out of date on other versions. It is designed to run on the current
game with all major DLCs, and it does not require any specific DLC.

---

## Things that changed on purpose

* **Light cruiser research bonuses are now heavy/light cruiser bonuses.** The
  game merged the light-cruiser technology category into the cruiser category
  (`cl_tech` → `ca_tech`), so focuses that boosted light cruisers now boost
  cruisers generally. Where a focus already had both, the duplicate was merged
  instead of being applied twice.
* **`supply_factor` modifier → `supply_consumption`.** One national modifier was
  using a key the game no longer recognises.
* **34 countries now receive modern naval and air doctrines.** Previously these
  were technology grants; now they are the doctrines the game expects. This is
  what makes those countries' navies and air forces behave as designed.
* **Special-forces doctrines are coarser.** The mod's old special-forces techs
  now grant the special-forces grand doctrine, but not a specific
  mountaineer/ranger subdoctrine. You choose that yourself with XP.
* **Six obsolete technology grants were removed.** A few very old naval-module
  tech ids (`basic_medium_battery`, `decimetric_radar` and similar) have no
  equivalent in the modern game. Rather than silently giving you the wrong
  equipment modules, they were removed. The affected ships lose nothing they
  were actually getting before.

---

## Things that are not the mod's doing

* The mod no longer ships a stale copy of the vanilla industry and artillery
  technology trees. That old copy was hiding the modern coal/energy industry
  branch and eight artillery technologies, so you now get the **real** current
  trees. Industry and artillery research will look different from old mod
  versions — that is the base game, not this mod.
* Two duplicate vanilla `on_actions` files were removed. This stops the game
  applying vanilla event hooks twice.

---

## If something looks wrong

The two most likely cosmetic problems are **missing doctrine artwork**: the mod
reuses base-game sprite names for the doctrine icons and backgrounds, and if a
name changed your doctrine screen may show placeholders. It does not affect
gameplay.

If the game misbehaves, the useful file is `error.log` in
`Documents/Paradox Interactive/Hearts of Iron IV/logs/`. Put it in
`Mod_Development_Tools_&_Files/` and it can be diagnosed from that alone.

---

## What was removed from the download

The uploaded mod contained a nested folder, `3142844611/`, holding 953 files
(50 MB) that belong to an unrelated Workshop mod. It was removed — it was not
part of this mod and the game would have tried to load it twice.

---

## Credits and licence

Original mod: **The Sacred War – 1942** (Workshop id 3142844611).
The 2.0.0 compatibility update changes only what the game required. All original
design decisions, modifiers, focus trees, events and artwork are the original
authors'.
