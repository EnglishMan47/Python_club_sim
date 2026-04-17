# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the project

```bash
python cyber_zone_sim.py
```

No dependencies beyond Python 3 standard library. No build step, no install.

## Architecture

Single-file functional simulation (`cyber_zone_sim.py`, ~1364 lines) with three explicit layers:

**L1 DATA** — 28 immutable `namedtuple` definitions (lines ~1–200). All domain entities: `World`, `Client`, `Session`, `Seat`, `Needs`, `RngState`, etc. State is never mutated — functions return new instances.

**L2 FUNCTIONS** — Pure state-transition functions (lines ~200–900). Each takes the current `World` state and returns a new `World`. The 8 core tick functions called each simulation step:
- `tick_arrivals` — spawns clients/groups, manages reservations
- `tick_seating` — matches waiting clients to available seats
- `tick_behavior` — updates client needs, chat, match results
- `tick_equipment` — HP degradation and repairs
- `tick_queue` — patience timeout for queued clients
- `calculate_cost` — tariff + promotion pricing (pure, no side effects)
- `active_promotions` — returns currently active promotions by time
- `next_day` — day transition with state carryover

**L3 SHELL** — Single `ClubApp` Tkinter class (lines ~900–1364). Owns the event loop, calls L2 functions on a timer tick, and re-renders. All simulation logic lives in L2; the GUI only reads state and dispatches user actions.

## Key constants (all hardcoded in file, lines ~51–200)

- `CONFIG` — hours (9–23), seat counts (16 PC / 6 VIP / 6 console), costs
- `TARIFFS` — 5 pricing models (per-minute, 1h, 2h, 3h, 5h)
- `PROMOTIONS` — 3 time-based discount rules (Happy Hour, Weekend, Night Owl)
- `RNG` — custom LCG for reproducible randomness (`RngState` namedtuple threaded through all functions)

## Simulation model

- Time unit: 1 simulation minute; day = 9:00–23:00 (840 ticks)
- Arrivals: 2–12 min intervals, rate varies by hour
- Max occupancy: 45 simultaneous people
- Equipment HP: 0–100; breaks at <20 HP; repairs restore 30–60 HP
- Client personalities: 6 archetypes (introvert, extrovert, casual, tryhard, toxic, newbie) with behavioral weights

## Working with the code

- To add a new simulation rule: add a pure function in L2 and call it from `ClubApp._tick`
- To add UI: modify `ClubApp._render` or add a canvas element; never embed logic there
- The `RngState` must be threaded through every function that needs randomness — do not use `random` module directly
- `World` is the single source of truth; never store simulation state in the GUI class
