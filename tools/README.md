# tools

Machinery used to bring The Sacred War – 1942 from game version 1.14.6 to 1.20.
Everything is Python 3, standard library only, and idempotent.

```bash
python3 tools/gen_doctrines.py                      # write common/doctrines/**
python3 tools/convert_history_doctrines.py --apply  # seed doctrines in history/**
python3 tools/migrate_1_20.py --apply               # small mechanical migrations + report
python3 tools/check_mod.py                          # braces, duplicate ids
python3 tools/check_doctrines.py                    # doctrine tree consistency
python3 tools/check_vanilla_ids.py                  # every id exists in vanilla 1.20
```

`check_vanilla_ids.py` needs an id dump at `tools/vanilla_1_20_ids.json`.
To regenerate it from a real install:

```bash
python3 tools/check_vanilla_ids.py --vanilla "/path/to/Hearts of Iron IV"
```

## Files

| File | Role |
| --- | --- |
| `pdxparse.py` | PDXscript tokenizer/parser (`Node`: `.key .op .value .children`). |
| `doctrine_map.py` | **Source of truth** for the doctrine mapping. Edit this, not the generated output. |
| `gen_doctrines.py` | Generates the new doctrine tree, copying modifiers verbatim from `design_record/`. |
| `convert_history_doctrines.py` | Rewrites doctrine grants in history and scripted effects. |
| `migrate_1_20.py` | Mechanical migrations and the migration report. |
| `check_mod.py` | Generic syntax/id checks. |
| `check_doctrines.py` | Doctrine-specific checks (tracks, 5 rewards, milestones, loc keys). |
| `check_vanilla_ids.py` | Validates every referenced id against vanilla. |
| `vanilla_1_20_ids.json` | Cached vanilla id lists. |

See `../readme_ai.md` for the full rationale and the list of traps.
