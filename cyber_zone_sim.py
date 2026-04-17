"""
CYBER ZONE — Computer Club Simulation
Pure functional architecture with visual GUI

L1 DATA      — Immutable data structures
L2 FUNCTIONS — Pure state transitions
L3 SHELL     — Tkinter GUI with Canvas visualization
"""

import tkinter as tk
from tkinter import scrolledtext
import math
from collections import namedtuple

# ═══════════════════════════════════════════════════════════════
# L1: DATA
# ═══════════════════════════════════════════════════════════════

RngState = namedtuple("RngState", ["seed"])

def rng_new(seed):
    return RngState(seed=abs(seed) or 1)

def rng_next(rng):
    s = (rng.seed * 48271) % 2147483647
    s = s if s else 1          # prevent degenerate zero-state in the LCG
    return s / 2147483647, RngState(seed=s)

def rng_int(rng, lo, hi):
    val, r2 = rng_next(rng)
    return lo + int(val * (hi - lo + 1)), r2

def rng_pick(rng, lst):
    idx, r2 = rng_int(rng, 0, len(lst) - 1)
    return lst[idx], r2

def rng_chance(rng, prob):
    val, r2 = rng_next(rng)
    return val < prob, r2

def clamp(v, lo=0, hi=100):
    return max(lo, min(hi, v))

def fmt_time(mins):
    return f"{(mins // 60) % 24:02d}:{mins % 60:02d}"

def fmt_money(n):
    return f"{n:.0f}₽"

# ── Static configuration ────────────────────────────────────────
CONFIG = {
    "open": 9, "close": 23,
    "pc": 16, "vip": 6, "console": 6,
    "capacity": 45,
    "rent": 500, "electric": 150,
    "wage_admin": 120, "wage_tech": 100, "wage_barista": 80,
}

TARIFFS = {
    "min": {"name": "Per Minute", "duration": None, "price_per_min": 1.2},
    "1h":  {"name": "1 Hour",    "duration":  60,  "fixed":  55},
    "2h":  {"name": "2 Hours",   "duration": 120,  "fixed":  95},
    "3h":  {"name": "3 Hours",   "duration": 180,  "fixed": 130},
    "5h":  {"name": "5 Hours",   "duration": 300,  "fixed": 190},
}

PROMOTIONS = [
    {"id": "happy",   "name": "Happy Hour  −20%", "discount": 0.20,
     "from": 14, "to": 17, "days": (1, 2, 3, 4, 5), "active": True},
    {"id": "weekend", "name": "Weekend    −15%",  "discount": 0.15,
     "from":  9, "to": 23, "days": (5, 6),          "active": True},
    {"id": "night",   "name": "Night Owl  −25%",  "discount": 0.25,
     "from": 21, "to": 23, "days": (0,1,2,3,4,5,6), "active": True},
]

NAMES_M = ("Artyom","Dmitry","Maxim","Ivan","Alexander","Mikhail","Daniel","Kirill",
           "Egor","Nikita","Matvey","Timur","Roman","Lev","Mark","Andrey","Pavel","Sergey")
NAMES_F = ("Alice","Maria","Anna","Sofia","Eva","Victoria","Polina","Daria",
           "Ekaterina","Arina","Veronica","Kira","Milana","Ulyana","Alina","Elena")
LAST_NAMES = ("Ivanov","Petrov","Sidorov","Kozlov","Novikov","Morozov","Volkov","Sokolov",
              "Popov","Lebedev","Kuznetsov","Smirnov","Orlov","Makarov","Belov","Gromov")

Personality = namedtuple("Personality", ["key","emoji","social_trend","chat_chance","patience"])
PERSONALITIES = {
    "introvert": Personality("introvert", "🤫", -0.3, 0.03, 40),
    "extrovert": Personality("extrovert", "🗣️",  0.3, 0.25, 18),
    "casual":    Personality("casual",    "😊",  0.0, 0.10, 25),
    "tryhard":   Personality("tryhard",   "🎯", -0.1, 0.15, 35),
    "toxic":     Personality("toxic",     "😈", -0.2, 0.30, 10),
    "newbie":    Personality("newbie",    "🐣",  0.2, 0.12, 30),
}

Game = namedtuple("Game", ["name","genre","max_players","vip_only"])
PC_GAMES = (
    Game("Cyberpunk 2077",   "RPG",     1, False),
    Game("Dota 2",           "MOBA",    5, False),
    Game("CS2",              "FPS",     5, False),
    Game("Valorant",         "FPS",     5, False),
    Game("GTA V Online",     "Action",  4, False),
    Game("Minecraft",        "Sandbox", 8, False),
    Game("League of Legends","MOBA",    5, False),
    Game("Apex Legends",     "BR",      3, False),
    Game("Fortnite",         "BR",      4, False),
    Game("Overwatch 2",      "FPS",     5, False),
    Game("Baldur's Gate 3",  "RPG",     4, True),
)
CONSOLE_GAMES = (
    Game("FIFA 24",         "Sports",  2, False),
    Game("Spider-Man 2",    "Action",  1, False),
    Game("Tekken 8",        "Fighting",2, False),
    Game("God of War",      "Action",  1, False),
    Game("Mortal Kombat 1", "Fighting",2, False),
    Game("Elden Ring",      "RPG",     1, False),
    Game("Gran Turismo 7",  "Racing",  2, False),
    Game("It Takes Two",    "Co-op",   2, False),
)

Food = namedtuple("Food", ["name","price","emoji","satiation","energy"])
MENU = (
    Food("Energy Drink", 3.5, "⚡", 10, 15),
    Food("Cola",         2.0, "🥤",  5,  5),
    Food("Pizza",        6.0, "🍕", 45,  5),
    Food("Chips",        2.5, "🍟", 15,  0),
    Food("Coffee",       3.0, "☕",  5, 20),
    Food("Sandwich",     5.0, "🥪", 35,  5),
    Food("Water",        1.0, "💧",  0,  3),
    Food("Chocolate",    1.5, "🍫", 10,  8),
    Food("Noodles",      7.0, "🍜", 50, 10),
    Food("Hot Dog",      4.0, "🌭", 30,  5),
)
ENERGY_DRINK = MENU[0]      # named reference — not an index magic number

CHAT_BY_GENRE = {
    "FPS":      ("headshot!", "smoke mid", "rush B!", "cover me!", "sick shot!", "ace!!", "clutch!!"),
    "MOBA":     ("gg wp", "mid diff", "gank top plz", "dragon in 30s", "push lanes", "gg ez?"),
    "RPG":      ("nice loot!", "what build?", "this boss is insane", "need healer", "love this quest"),
    "Sports":   ("GOAAAL!", "nice pass", "red card!", "offside?!", "penalty!"),
    "Fighting": ("gg ez", "that combo!", "lag!", "rematch!", "broken char", "PERFECT!"),
    "BR":       ("land here", "need ammo", "storm coming", "sniper spotted", "squad wipe!!"),
    "Sandbox":  ("nice build!", "CREEPER!!", "found diamonds!", "show me your house", "how to craft?"),
    "Action":   ("what a cutscene", "boss fight!", "loot everything", "that was epic!"),
    "Racing":   ("clean race", "sick drift!", "pit stop!", "slipstream!"),
    "Co-op":    ("wait for me!", "nice teamwork!", "pull the lever!", "tough puzzle"),
}
CHAT_TOXIC   = ("git gud", "uninstall", "ez clap", "trash team", "skill issue")
CHAT_NEWBIE  = ("how to play?", "which button?", "help me!", "first time here!", "is this good?")
CHAT_GENERAL = ("anyone want snacks?", "great atmosphere!", "love this place!", "who's up for a tourney?")

SHIRT_COLORS = ("#FF6B6B","#4ECDC4","#45B7D1","#96CEB4","#FFEAA7","#DDA0DD",
                "#98D8C8","#F7DC6F","#BB8FCE","#85C1E9","#F0B27A","#82E0AA",
                "#FF9FF3","#54A0FF","#5F27CD","#01A3A4","#F368E0","#EE5A24")
SKIN_COLORS  = ("#FDBCB4","#F1C27D","#E0AC69","#C68642","#8D5524")
HAIR_COLORS  = ("#2C1810","#4A2C1A","#8B4513","#D2691E","#FFD700","#1A1A2E","#C0C0C0")

# ── Needs ────────────────────────────────────────────────────────
Needs = namedtuple("Needs", ["hunger","toilet","energy","social","fun","mood"])

def make_needs(rng):
    h, rng = rng_int(rng,  5,  30)
    t, rng = rng_int(rng,  0,  20)
    e, rng = rng_int(rng, 50, 100)
    s, rng = rng_int(rng, 30,  70)
    f, rng = rng_int(rng, 40,  70)
    m, rng = rng_int(rng, 60,  95)
    return Needs(h, t, e, s, f, m), rng

def update_needs(needs, **kw):
    d = needs._asdict()
    for k, v in kw.items():
        if k in d:
            d[k] = clamp(d[k] + v)
    return Needs(**d)

# ── Appearance ───────────────────────────────────────────────────
Appearance = namedtuple("Appearance", ["skin","shirt","hair","glasses","hair_style"])

def make_appearance(rng):
    skin,    rng = rng_pick(rng, SKIN_COLORS)
    shirt,   rng = rng_pick(rng, SHIRT_COLORS)
    hair,    rng = rng_pick(rng, HAIR_COLORS)
    glasses, rng = rng_chance(rng, 0.25)
    style,   rng = rng_int(rng, 0, 2)
    return Appearance(skin, shirt, hair, glasses, style), rng

# ── Seats ────────────────────────────────────────────────────────
Seat = namedtuple("Seat", ["id","type","row","col","status","hp","reserved_for","reserved_time"])

def make_seats(cfg):
    seats = []
    for i in range(1, cfg["pc"] + 1):
        seats.append(Seat(f"PC-{i}",  "pc",      (i-1)//6+1, (i-1)%6+1, "free", 100, None, None))
    for i in range(1, cfg["vip"] + 1):
        seats.append(Seat(f"VIP-{i}", "vip",     (i-1)//3+1, (i-1)%3+1, "free", 100, None, None))
    for i in range(1, cfg["console"] + 1):
        seats.append(Seat(f"CON-{i}", "console", 1, i,                   "free", 100, None, None))
    return tuple(seats)

# ── Staff ────────────────────────────────────────────────────────
Staff = namedtuple("Staff", ["id","role","name","salary"])

def make_staff():
    return (
        Staff("a1", "admin",   "Maria",  120),
        Staff("t1", "tech",    "Victor", 100),
        Staff("b1", "barista", "Lena",    80),
    )

# ── Clients ──────────────────────────────────────────────────────
Client = namedtuple("Client", [
    "id","name","pref","tariff","duration","arrived","game","group",
    "personality","needs","appearance","reservation","reservation_time",
    "extend","leave_early","rank","visits",
])

def make_client(cid, t, rng, group=None, group_game=None, group_pref=None):
    male,    rng = rng_chance(rng, 0.55)
    first,   rng = rng_pick(rng, NAMES_M if male else NAMES_F)
    last,    rng = rng_pick(rng, LAST_NAMES)
    full_name = f"{first} {last[0]}."

    pers_key, rng = rng_pick(rng, list(PERSONALITIES.keys()))

    if group_pref:
        pref = group_pref
    else:
        r1, rng = rng_next(rng)
        pref = "console" if r1 < 0.15 else ("vip" if r1 < 0.30 else "pc")

    if group_game:
        game = group_game
    else:
        pool = (CONSOLE_GAMES if pref == "console"
                else (PC_GAMES if pref == "vip"
                      else tuple(g for g in PC_GAMES if not g.vip_only)))
        game, rng = rng_pick(rng, pool)

    tar_key, rng = rng_pick(rng, list(TARIFFS.keys()))
    duration = TARIFFS[tar_key].get("duration")
    if duration is None:
        duration, rng = rng_int(rng, 30, 240)

    needs,      rng = make_needs(rng)
    appearance, rng = make_appearance(rng)

    has_res, rng = rng_chance(rng, 0.12 if group is None else 0.0)
    res_time = None
    if has_res:
        off, rng = rng_int(rng, 15, 90)
        res_time = t + off

    extend,     rng = rng_chance(rng, 0.25)
    leave_early,rng = rng_chance(rng, 0.12)
    visits,     rng = rng_int(rng, 0, 15)
    rank = ("Legend"  if visits > 20 else
            "Pro"     if visits > 10 else
            "Regular" if visits >  3 else "Newbie")

    return Client(cid, full_name, pref, tar_key, duration, t, game, group, pers_key,
                  needs, appearance, has_res, res_time, extend, leave_early, rank, visits), rng

def make_group(start_id, t, gid, rng):
    size, rng = rng_int(rng, 2, 4)
    r1,   rng = rng_next(rng)
    pref = "console" if r1 < 0.2 else "pc"
    pool  = CONSOLE_GAMES if pref == "console" else tuple(g for g in PC_GAMES if not g.vip_only)
    valid = [g for g in pool if g.max_players >= size]
    game, rng = rng_pick(rng, valid if valid else pool)
    members = []
    for i in range(size):
        client, rng = make_client(start_id + i, t, rng,
                                  group=gid, group_game=game, group_pref=pref)
        members.append(client)
    return tuple(members), rng

# ── Events / world ───────────────────────────────────────────────
Reservation = namedtuple("Reservation", ["client_id","client","time","seat_type"])
Log         = namedtuple("Log",         ["time","text","type"])
ChatMsg     = namedtuple("ChatMsg",     ["time","sender","text","seat","personality"])

Session = namedtuple("Session", [
    "id","client_id","client_name","seat_id","seat_type",
    "game","start","end","tariff","group","personality",
    "needs","appearance","activity","activity_timer",
    "food_bought","chat_cd","extend","leave_early",
    "match_result","rank","complaints",
])

def make_session(sid, client, seat, t):
    return Session(
        sid, client.id, client.name, seat.id, seat.type,
        client.game, t, t + client.duration,
        client.tariff, client.group, client.personality,
        client.needs, client.appearance,
        "playing", 0,
        (), 0, client.extend, client.leave_early,
        None, client.rank, 0,
    )

World = namedtuple("World", [
    "time","day","running","rng",
    "seats","queue","sessions","reservations",
    "staff","revenue","food_revenue","expenses",
    "served","next_client","next_session","next_group",
    "arrival_timer","logs","chats","promotions",
])

def initial_state(seed=42):
    cfg = CONFIG
    return World(
        time=cfg["open"] * 60, day=1, running=False, rng=rng_new(seed),
        seats=make_seats(cfg), queue=(), sessions=(), reservations=(),
        staff=make_staff(), revenue=0.0, food_revenue=0.0, expenses=0.0,
        served=0, next_client=1, next_session=1, next_group=1,
        arrival_timer=3,
        logs=(Log(cfg["open"] * 60, "🏢 CYBER ZONE is open!  Day 1", "system"),),
        chats=(), promotions=tuple(PROMOTIONS),
    )

# ═══════════════════════════════════════════════════════════════
# L2: FUNCTIONS  (pure state transitions)
# ═══════════════════════════════════════════════════════════════

def active_promotions(st):
    hour = (st.time // 60) % 24
    day  = st.day % 7
    return tuple(p for p in st.promotions
                 if p["active"] and p["from"] <= hour < p["to"] and day in p["days"])

def calculate_cost(session, moment, promos):
    tf = TARIFFS[session.tariff]
    price = tf["fixed"] if "fixed" in tf else (moment - session.start) * tf["price_per_min"]
    discount = max((p["discount"] for p in promos), default=0.0)
    return price * (1 - discount)

# ── Arrival tick ─────────────────────────────────────────────────
def tick_arrivals(st):
    t    = st.time
    hour = (t // 60) % 24
    rng  = st.rng
    queue        = list(st.queue)
    nc, ng       = st.next_client, st.next_group
    timer        = st.arrival_timer
    reservations = list(st.reservations)
    logs         = list(st.logs)

    if timer <= 0:
        total = len(queue) + len(st.sessions)
        if total < CONFIG["capacity"]:
            is_group, rng = rng_chance(rng, 0.4)
            if is_group:
                grp, rng = make_group(nc, t, ng, rng)
                queue.extend(grp)
                logs.append(Log(t,
                    f"👥 Group \"{grp[0].name} & friends\" ({len(grp)} ppl) → {grp[0].game.name}",
                    "arrival"))
                nc += len(grp); ng += 1
            else:
                client, rng = make_client(nc, t, rng)
                if client.reservation:
                    reservations.append(
                        Reservation(client.id, client, client.reservation_time, client.pref))
                    logs.append(Log(t,
                        f"📋 {client.name} reserved {client.pref} for {fmt_time(client.reservation_time)}",
                        "reservation"))
                else:
                    pers = PERSONALITIES[client.personality]
                    queue.append(client)
                    logs.append(Log(t,
                        f"→ {client.name} joined queue ({client.pref}, {pers.emoji})",
                        "arrival"))
                nc += 1
            base = 12 if hour < 12 else (5 if hour < 18 else 8)
            timer, rng = rng_int(rng, 2, base)
    else:
        timer -= 1

    # Handle arriving reservations
    arrived   = [r for r in reservations if t >= r.time]
    remaining = [r for r in reservations if t <  r.time]
    for rv in arrived:
        queue.insert(0, rv.client)
        logs.append(Log(t, f"📋 {rv.client.name} arrived via reservation", "reservation"))

    return st._replace(
        queue=tuple(queue), next_client=nc, next_group=ng,
        arrival_timer=timer, reservations=tuple(remaining),
        logs=tuple(logs), rng=rng,
    )

# ── Seating tick ─────────────────────────────────────────────────
def tick_seating(st):
    t        = st.time
    seats    = list(st.seats)
    sessions = list(st.sessions)
    sid      = st.next_session
    logs     = list(st.logs)
    queue_in = list(st.queue)
    new_queue          = []
    seated             = 0
    seated_client_ids  = set()   # track clients placed *this tick* (fixes group re-iteration bug)

    # Mark seats reserved for imminent bookings (≤15 min away)
    for rv in st.reservations:
        if rv.time - t <= 15:
            for i, s in enumerate(seats):
                if s.type == rv.seat_type and s.status == "free" \
                        and s.reserved_for is None and s.hp > 20:
                    seats[i] = s._replace(reserved_for=rv.client_id, reserved_time=rv.time)
                    break

    for client in queue_in:
        if client.id in seated_client_ids:
            continue                     # already placed as part of a group this tick

        if seated >= 3:
            new_queue.append(client)
            continue

        # ── Group logic ──────────────────────────────────────────
        if client.group is not None:
            # Members not yet in any session and not already seated this tick
            group_members = [
                x for x in queue_in
                if x.group == client.group
                and x.id not in seated_client_ids
                and not any(s.client_id == x.id for s in sessions)
            ]

            if not group_members:
                # Already fully placed or orphaned
                continue

            if group_members[0].id != client.id:
                # Wait for the first member to handle placement
                new_queue.append(client)
                continue

            free_seats = [s for s in seats
                          if s.status == "free" and s.reserved_for is None and s.hp > 20]
            by_row = {}
            for s in free_seats:
                by_row.setdefault((s.type, s.row), []).append(s)

            found = []
            for _, v in by_row.items():
                if len(v) >= len(group_members):
                    found = v[:len(group_members)]
                    break
            if not found and len(free_seats) >= len(group_members):
                found = free_seats[:len(group_members)]

            if len(found) >= len(group_members):
                for j, member in enumerate(group_members):
                    s = found[j]
                    sessions.append(make_session(sid, member, s, t)); sid += 1
                    idx = next(k for k, x in enumerate(seats) if x.id == s.id)
                    seats[idx] = s._replace(status="busy", reserved_for=None)
                    seated_client_ids.add(member.id)
                logs.append(Log(t,
                    f"🎮 Group seated: {', '.join(m.name for m in group_members)} ({client.game.name})",
                    "session"))
                seated += 1
            else:
                new_queue.append(client)
            continue

        # ── Single client ─────────────────────────────────────────
        reserved  = next((s for s in seats if s.reserved_for == client.id and s.status == "free"), None)
        preferred = next((s for s in seats
                          if s.type == client.pref and s.status == "free"
                          and s.reserved_for is None and s.hp > 20), None)
        any_free  = next((s for s in seats
                          if s.status == "free" and s.reserved_for is None and s.hp > 20), None)
        chosen = reserved or preferred or any_free

        if chosen:
            sessions.append(make_session(sid, client, chosen, t)); sid += 1
            idx = next(k for k, x in enumerate(seats) if x.id == chosen.id)
            seats[idx] = chosen._replace(status="busy", reserved_for=None, reserved_time=None)
            seated_client_ids.add(client.id)
            tname = TARIFFS[client.tariff]["name"]
            logs.append(Log(t,
                f"✅ {client.name} → {chosen.id}  ({client.game.name}, {tname})",
                "session"))
            seated += 1
        else:
            new_queue.append(client)

    return st._replace(
        queue=tuple(new_queue), sessions=tuple(sessions),
        seats=tuple(seats), next_session=sid, logs=tuple(logs),
    )

# ── Behaviour tick ───────────────────────────────────────────────
def tick_behavior(st):
    t      = st.time
    rng    = st.rng
    promos = active_promotions(st)
    logs   = list(st.logs)
    chats  = list(st.chats)
    seats  = list(st.seats)
    rev      = st.revenue
    food_rev = st.food_revenue
    served   = st.served
    active   = []

    for ses in st.sessions:
        needs    = ses.needs
        pers     = PERSONALITIES[ses.personality]
        elapsed  = t - ses.start
        remaining= ses.end - t
        act      = ses.activity
        act_tmr  = ses.activity_timer
        chat_cd  = max(0, ses.chat_cd - 1)
        food     = list(ses.food_bought)
        match_r  = ses.match_result
        complaints = ses.complaints
        end      = ses.end

        # ── Needs decay ──────────────────────────────────────────
        do_h, rng = rng_chance(rng, 0.12)
        hunger_d = 0
        if do_h:
            hv, rng = rng_int(rng, 1, 3); hunger_d = hv

        do_t, rng = rng_chance(rng, 0.15)
        toilet_d = 0
        if do_t:
            tv, rng = rng_int(rng, 2, 4); toilet_d = tv

        do_e, rng = rng_chance(rng, 0.08)
        energy_d = 0
        if do_e:
            ev, rng = rng_int(rng, 1, 2); energy_d = -ev

        social_d = (0.2 if ses.group else -0.1) + pers.social_trend * 0.1
        fun_d    = 0.3 if act == "playing" else -0.5
        mood_d   = ((0.1 if needs.fun > 60 else -0.1)
                    + (-0.2 if needs.hunger > 70 else 0)
                    + (-0.3 if needs.energy < 20 else 0))

        needs = update_needs(needs,
                             hunger=hunger_d, toilet=toilet_d, energy=energy_d,
                             social=social_d, fun=fun_d, mood=mood_d)

        # ── Activities ───────────────────────────────────────────
        if act == "playing" and needs.toilet > 65:
            go, rng = rng_chance(rng, 0.4)
            if go:
                act = "bathroom"; act_tmr, rng = rng_int(rng, 2, 4)
                needs = update_needs(needs, toilet=-60)
                logs.append(Log(t, f"🚻 {ses.client_name} → bathroom", "activity"))

        if act == "playing" and needs.hunger > 55:
            buy, rng = rng_chance(rng, 0.3)
            if buy:
                item, rng = rng_pick(rng, MENU)
                act = "buying_food"; act_tmr, rng = rng_int(rng, 1, 3)
                food.append(item)
                needs = update_needs(needs,
                                     hunger=-item.satiation, energy=item.energy, mood=3)
                food_rev += item.price
                logs.append(Log(t,
                    f"{item.emoji} {ses.client_name} bought {item.name} ({fmt_money(item.price)})",
                    "food"))

        if act == "playing" and needs.energy < 25:
            grab, rng = rng_chance(rng, 0.4)
            if grab:
                food.append(ENERGY_DRINK)
                needs    = update_needs(needs, energy=ENERGY_DRINK.energy)
                food_rev += ENERGY_DRINK.price
                logs.append(Log(t, f"⚡ {ses.client_name} grabbed an energy drink", "food"))

        # ── Chat ─────────────────────────────────────────────────
        if act == "playing" and chat_cd <= 0:
            talk, rng = rng_chance(rng, pers.chat_chance)
            if talk:
                genre = ses.game.genre
                pool  = CHAT_BY_GENRE.get(genre, CHAT_GENERAL)
                if ses.personality == "toxic":
                    is_t, rng = rng_chance(rng, 0.5)
                    if is_t: pool = CHAT_TOXIC
                elif ses.personality == "newbie":
                    is_n, rng = rng_chance(rng, 0.4)
                    if is_n: pool = CHAT_NEWBIE
                gen, rng = rng_chance(rng, 0.15)
                if gen: pool = CHAT_GENERAL
                msg, rng = rng_pick(rng, pool)
                chats.append(ChatMsg(t, ses.client_name, msg, ses.seat_id, ses.personality))
                chat_cd, rng = rng_int(rng, 5, 20)

        # ── Match result (every 30 sim-min) ─────────────────────
        if act == "playing" and elapsed > 0 and elapsed % 30 == 0:
            match, rng = rng_chance(rng, 0.6)
            if match:
                win_p = 0.6 if ses.personality == "tryhard" else 0.45
                won, rng = rng_chance(rng, win_p)
                match_r = "win" if won else "loss"
                needs = update_needs(needs,
                                     mood=(8 if won else -5), fun=(10 if won else -3))

        # ── Activity timer ───────────────────────────────────────
        if act_tmr > 0:
            act_tmr -= 1
            if act_tmr <= 0:
                act = "playing"

        # ── Complaints ───────────────────────────────────────────
        if needs.mood < 30:
            comp, rng = rng_chance(rng, 0.05)
            if comp:
                complaints += 1
                logs.append(Log(t,
                    f"😤 {ses.client_name} is complaining!  (mood: {int(needs.mood)})",
                    "complaint"))

        # ── Early departure ──────────────────────────────────────
        if ses.leave_early and elapsed > 15:
            leaving = needs.mood < 25
            if not leaving:
                leaving, rng = rng_chance(rng, 0.01)
            if leaving:
                price = calculate_cost(ses, t, promos)
                rev += price; served += 1
                idx = next((j for j, x in enumerate(seats) if x.id == ses.seat_id), None)
                if idx is not None:
                    seats[idx] = seats[idx]._replace(status="free")
                logs.append(Log(t,
                    f"🚪 {ses.client_name} left early.  Paid {fmt_money(price)}",
                    "departure"))
                continue

        # ── Extension ────────────────────────────────────────────
        if ses.extend and remaining == 10:
            will_ext, rng = rng_chance(rng, 0.5)
            if will_ext:
                extra, rng = rng_int(rng, 20, 90)
                end += extra
                logs.append(Log(t,
                    f"⏰ {ses.client_name} extended session +{extra} min",
                    "extension"))

        # ── Natural end ──────────────────────────────────────────
        if t >= end:
            price = calculate_cost(ses, t, promos)
            rev += price; served += 1
            idx = next((j for j, x in enumerate(seats) if x.id == ses.seat_id), None)
            if idx is not None:
                seats[idx] = seats[idx]._replace(status="free")
            tag = " (promo!)" if promos else ""
            logs.append(Log(t,
                f"💰 {ses.client_name} left.  Paid {fmt_money(price)}{tag}",
                "departure"))
            continue

        active.append(ses._replace(
            needs=needs, activity=act, activity_timer=act_tmr,
            food_bought=tuple(food), chat_cd=chat_cd,
            match_result=match_r, complaints=complaints, end=end,
        ))

    return st._replace(
        sessions=tuple(active), seats=tuple(seats),
        revenue=rev, food_revenue=food_rev, served=served,
        logs=tuple(logs), chats=tuple(chats), rng=rng,
    )

# ── Equipment tick ───────────────────────────────────────────────
def tick_equipment(st):
    rng      = st.rng
    t        = st.time
    seats    = list(st.seats)
    expenses = st.expenses
    logs     = list(st.logs)
    has_tech = any(s.role == "tech" for s in st.staff)

    for i, seat in enumerate(seats):
        if seat.status == "busy":
            broken, rng = rng_chance(rng, 0.003)
            if broken:
                dmg, rng = rng_int(rng, 5, 15)
                new_hp   = clamp(seat.hp - dmg)
                seats[i] = seat._replace(hp=new_hp)
                if new_hp < 20:
                    logs.append(Log(t, f"🔧 {seat.id} broke down!  (HP: {new_hp})", "equipment"))

        if seat.hp < 40 and seat.status == "free" and has_tech:
            repair, rng = rng_chance(rng, 0.1)
            if repair:
                cost, rng = rng_int(rng, 20, 80)
                heal, rng = rng_int(rng, 30, 60)
                seats[i]  = seat._replace(hp=clamp(seat.hp + heal))
                expenses  += cost
                logs.append(Log(t, f"🔧 {seat.id} repaired  (−{cost}₽)", "equipment"))

    return st._replace(seats=tuple(seats), expenses=expenses, logs=tuple(logs), rng=rng)

# ── Queue patience tick ──────────────────────────────────────────
def tick_queue(st):
    t     = st.time
    rng   = st.rng
    kept  = []
    logs  = list(st.logs)

    for client in st.queue:
        pers   = PERSONALITIES[client.personality]
        waited = t - client.arrived
        if waited > pers.patience:
            leaves, rng = rng_chance(rng, 0.15)
            if leaves:
                logs.append(Log(t,
                    f"😤 {client.name} left the queue ({waited} min wait)",
                    "leave"))
                continue
        kept.append(client)

    return st._replace(queue=tuple(kept), logs=tuple(logs), rng=rng)

# ── Main tick ────────────────────────────────────────────────────
def pipeline(*fns):
    def combined(st):
        for fn in fns:
            st = fn(st)
        return st
    return combined

def tick(state):
    if not state.running:
        return state

    t    = state.time
    hour = (t // 60) % 24
    cfg  = CONFIG

    if hour >= cfg["close"]:
        total_exp = (cfg["rent"] + cfg["electric"]
                     + sum(s.salary for s in state.staff) + state.expenses)
        profit = state.revenue + state.food_revenue - total_exp
        return state._replace(
            running=False,
            logs=state.logs + (Log(t,
                f"🔒 CLOSED!   Revenue: {fmt_money(state.revenue + state.food_revenue)}   "
                f"Expenses: {fmt_money(total_exp)}   Profit: {fmt_money(profit)}",
                "system"),),
        )

    if hour < cfg["open"]:
        return state._replace(time=t + 1)

    pipe = pipeline(tick_arrivals, tick_seating, tick_behavior, tick_equipment, tick_queue)
    st   = pipe(state)
    # Trim history to prevent unbounded growth
    st   = st._replace(time=t + 1, logs=st.logs[-300:], chats=st.chats[-150:])
    return st

def next_day(state):
    new = initial_state(seed=state.rng.seed + 9999)
    return new._replace(
        day=state.day + 1,
        promotions=state.promotions,
        staff=state.staff,
        logs=(Log(CONFIG["open"] * 60, f"🏢 Day {state.day + 1} begins!", "system"),),
    )

# ═══════════════════════════════════════════════════════════════
# L3: SHELL — Tkinter GUI
# ═══════════════════════════════════════════════════════════════

ZONE_COLORS = {"pc": "#2563EB", "vip": "#D97706", "console": "#059669"}

LOG_TYPE_COLORS = {
    "system":      "#FF4444",
    "arrival":     "#44DD44",
    "session":     "#4488FF",
    "departure":   "#FFBB33",
    "activity":    "#BB88FF",
    "food":        "#FF8833",
    "reservation": "#66BBFF",
    "extension":   "#33DDDD",
    "leave":       "#FF4444",
    "equipment":   "#FFBB33",
    "complaint":   "#FF6666",
}

# ── Hover helper ─────────────────────────────────────────────────
def bind_hover(widget, normal_bg, hover_bg,
               normal_fg="#e0e0e0", hover_fg=None):
    """Add smooth Enter/Leave colour transitions to any tk widget."""
    hfg = hover_fg or normal_fg
    widget.bind("<Enter>", lambda _: widget.config(bg=hover_bg, fg=hfg))
    widget.bind("<Leave>", lambda _: widget.config(bg=normal_bg, fg=normal_fg))


class ClubApp:
    def __init__(self, root):
        self.root   = root
        self.root.title("⚡ CYBER ZONE — Computer Club Simulation")
        self.root.geometry("1300x840")
        self.root.configure(bg="#09091a")
        self.root.minsize(1100, 720)

        self.state       = initial_state()
        # speed=1  →  1 real second = 1 simulation minute  (as required)
        self.speed       = 1
        self.seat_coords = {}

        self._build_ui()

    # ─────────────────────────────────────────────────────────────
    # UI construction
    # ─────────────────────────────────────────────────────────────
    def _build_ui(self):
        # ── Top bar ──────────────────────────────────────────────
        top = tk.Frame(self.root, bg="#0c0c28", pady=7)
        top.pack(fill=tk.X)

        tk.Label(top, text="⚡ CYBER ZONE",
                 fg="#818CF8", bg="#0c0c28",
                 font=("Consolas", 16, "bold")).pack(side=tk.LEFT, padx=16)

        self.label_time = tk.Label(top, text="09:00",
                                   fg="#ffffff", bg="#0c0c28",
                                   font=("Consolas", 23, "bold"))
        self.label_time.pack(side=tk.LEFT, padx=8)

        self.label_day = tk.Label(top, text="Day 1",
                                  fg="#666", bg="#0c0c28",
                                  font=("Consolas", 11))
        self.label_day.pack(side=tk.LEFT, padx=4)

        self.label_promo = tk.Label(top, text="",
                                    fg="#FBBF24", bg="#0c0c28",
                                    font=("Consolas", 9))
        self.label_promo.pack(side=tk.LEFT, padx=10)

        # ── Control buttons (right side of top bar) ──────────────
        btn_row = tk.Frame(top, bg="#0c0c28")
        btn_row.pack(side=tk.RIGHT, padx=10)

        # Speed selector
        self.speed_btns: dict[int, tk.Button] = {}
        for spd, label in [(1,"1×"),(2,"2×"),(5,"5×"),(10,"10×"),(20,"20×")]:
            b = tk.Button(
                btn_row, text=label, width=4,
                command=lambda s=spd: self._set_speed(s),
                bg="#15152a", fg="#555",
                font=("Consolas", 9, "bold"),
                relief="flat", bd=0, cursor="hand2",
                activebackground="#2a2a55", activeforeground="#a5b4fc",
            )
            b.pack(side=tk.LEFT, padx=2)
            bind_hover(b, "#15152a", "#222244", "#555", "#aaa")
            self.speed_btns[spd] = b
        self._refresh_speed_buttons()

        # Start / Live / Closed
        self.btn_start = tk.Button(
            btn_row, text="▶  START", command=self._start,
            bg="#22c55e", fg="#000",
            font=("Consolas", 10, "bold"),
            relief="flat", width=9, cursor="hand2",
            activebackground="#16a34a", activeforeground="#000",
        )
        self.btn_start.pack(side=tk.LEFT, padx=(10, 2))
        bind_hover(self.btn_start, "#22c55e", "#16a34a", "#000")

        # Reset
        self.btn_reset = tk.Button(
            btn_row, text="↺", command=self._reset,
            bg="#1c1c38", fg="#777",
            font=("Consolas", 12), relief="flat", width=3, cursor="hand2",
            activebackground="#2a2a50", activeforeground="#ddd",
        )
        self.btn_reset.pack(side=tk.LEFT, padx=2)
        bind_hover(self.btn_reset, "#1c1c38", "#2a2a50", "#777", "#ddd")

        # New Day (hidden until day ends)
        self.btn_next_day = tk.Button(
            btn_row, text="☀  New Day", command=self._new_day,
            bg="#1c1c38", fg="#FBBF24",
            font=("Consolas", 9, "bold"), relief="flat", cursor="hand2",
            activebackground="#2a2a50", activeforeground="#fde68a",
        )
        bind_hover(self.btn_next_day, "#1c1c38", "#2a2a50", "#FBBF24", "#fde68a")

        # ── Day progress bar ─────────────────────────────────────
        bar_frame = tk.Frame(self.root, bg="#09091a", height=5)
        bar_frame.pack(fill=tk.X, padx=14)
        self.day_bar = tk.Canvas(bar_frame, height=5, bg="#111130", highlightthickness=0)
        self.day_bar.pack(fill=tk.X)

        # ── Body ─────────────────────────────────────────────────
        body = tk.Frame(self.root, bg="#09091a")
        body.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        # Left: canvas + log panel
        left = tk.Frame(body, bg="#09091a")
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(left, bg="#0b0b18",
                                highlightthickness=1, highlightbackground="#1a1a44")
        self.canvas.pack(fill=tk.BOTH, expand=True, pady=(0, 4))

        # Tab bar + text log
        bot = tk.Frame(left, bg="#09091a")
        bot.pack(fill=tk.X)

        tab_bar = tk.Frame(bot, bg="#09091a")
        tab_bar.pack(fill=tk.X)

        self.current_tab = tk.StringVar(value="log")
        for key, label in [("log","📋  Log"),("chat","💬  Chat"),("sessions","🎮  Sessions")]:
            rb = tk.Radiobutton(
                tab_bar, text=label,
                variable=self.current_tab, value=key,
                indicatoron=0,
                bg="#0e0e24", fg="#555",
                selectcolor="#1c1c44",
                activebackground="#1c1c44", activeforeground="#aaa",
                font=("Consolas", 9, "bold"),
                relief="flat", bd=0, padx=14, pady=5, cursor="hand2",
                command=self._update_text_panel,
            )
            rb.pack(side=tk.LEFT, padx=1)
            bind_hover(rb, "#0e0e24", "#1c1c44", "#555", "#aaa")

        self.text_panel = scrolledtext.ScrolledText(
            bot, height=10, bg="#070714",
            fg="#ccc", font=("Consolas", 9),
            insertbackground="#ccc", relief="flat",
            wrap=tk.WORD, state=tk.DISABLED,
        )
        self.text_panel.pack(fill=tk.X, pady=(2, 0))

        for tag, color in {
            **LOG_TYPE_COLORS,
            "chat_intro":   "#94A3B8",
            "chat_extro":   "#FBBF24",
            "chat_toxic":   "#EF4444",
            "chat_newbie":  "#C084FC",
            "chat_default": "#4ADE80",
            "session_row":  "#93c5fd",
            "session_hdr":  "#818CF8",
        }.items():
            self.text_panel.tag_configure(tag, foreground=color)

        # ── Right sidebar ─────────────────────────────────────────
        right = tk.Frame(body, bg="#0c0c20", width=275)
        right.pack(side=tk.RIGHT, fill=tk.Y, padx=(4, 0))
        right.pack_propagate(False)

        # Dashboard
        self._sidebar_header(right, "DASHBOARD")
        self.stat_labels: dict[str, tk.Label] = {}
        for key, label in [
            ("revenue",   "💰  Revenue"),
            ("expenses",  "📉  Expenses"),
            ("profit",    "📊  Profit"),
            ("served",    "👤  Served"),
            ("queue",     "🚶  Queue"),
            ("active",    "🎮  Active"),
            ("occupancy", "📈  Occupancy"),
            ("broken",    "🔧  Broken"),
            ("mood",      "😊  Avg Mood"),
        ]:
            row = tk.Frame(right, bg="#10102a", pady=1)
            row.pack(fill=tk.X, padx=6, pady=1)
            tk.Label(row, text=label, fg="#555", bg="#10102a",
                     font=("Consolas", 9), anchor="w").pack(side=tk.LEFT, padx=6)
            lbl = tk.Label(row, text="—", fg="#e0e0e0", bg="#10102a",
                           font=("Consolas", 10, "bold"), anchor="e")
            lbl.pack(side=tk.RIGHT, padx=6)
            self.stat_labels[key] = lbl

        # Zone bars
        self._sidebar_header(right, "ZONES")
        self.zones_canvas = tk.Canvas(right, height=66, bg="#0c0c20", highlightthickness=0)
        self.zones_canvas.pack(fill=tk.X, padx=6)

        # Staff
        self._sidebar_header(right, "STAFF")
        for s in make_staff():
            icon = {"admin": "👔", "tech": "🔧", "barista": "☕"}.get(s.role, "?")
            tk.Label(right,
                     text=f"  {icon}  {s.name}  [{s.role}]  {s.salary}₽/h",
                     fg="#777", bg="#0c0c20",
                     font=("Consolas", 8)).pack(anchor="w", padx=6)

        # Tariffs
        self._sidebar_header(right, "TARIFFS")
        for tf in TARIFFS.values():
            price = (f"{tf.get('fixed', 0)}₽" if "fixed" in tf
                     else f"{tf['price_per_min']}₽/min")
            dur   = f"  {tf['duration']}min" if tf.get("duration") else ""
            tk.Label(right,
                     text=f"  {tf['name']}: {price}{dur}",
                     fg="#666", bg="#0c0c20",
                     font=("Consolas", 8)).pack(anchor="w", padx=6)

        # Reservations
        self._sidebar_header(right, "RESERVATIONS")
        self.label_reservations = tk.Label(
            right, text="  None", fg="#444", bg="#0c0c20",
            font=("Consolas", 8), justify="left", anchor="w",
        )
        self.label_reservations.pack(anchor="w", padx=6, pady=(0, 4))

        self.last_log_idx  = 0
        self.last_chat_idx = 0

    def _sidebar_header(self, parent, title: str):
        tk.Label(parent, text=f"─── {title} ───",
                 fg="#818CF8", bg="#0c0c20",
                 font=("Consolas", 8, "bold")).pack(anchor="w", padx=6, pady=(8, 2))

    # ─────────────────────────────────────────────────────────────
    # Speed buttons
    # ─────────────────────────────────────────────────────────────
    def _refresh_speed_buttons(self):
        for spd, btn in self.speed_btns.items():
            if spd == self.speed:
                btn.config(bg="#3730a3", fg="#a5b4fc")
            else:
                btn.config(bg="#15152a", fg="#555")

    def _set_speed(self, s: int):
        self.speed = s
        self._refresh_speed_buttons()

    # ─────────────────────────────────────────────────────────────
    # Control actions
    # ─────────────────────────────────────────────────────────────
    def _start(self):
        if not self.state.running:
            self.state = self.state._replace(running=True)
            self.btn_start.config(text="● LIVE", bg="#1a3a1a", fg="#4ADE80",
                                  state=tk.DISABLED)
            self.btn_next_day.pack_forget()
            self._loop()

    def _reset(self):
        self.state = initial_state()
        self.last_log_idx  = 0
        self.last_chat_idx = 0
        self.btn_start.config(text="▶  START", bg="#22c55e", fg="#000",
                              state=tk.NORMAL)
        self.btn_next_day.pack_forget()
        self._render()

    def _new_day(self):
        self.state = next_day(self.state)
        self.state = self.state._replace(running=True)
        self.last_log_idx  = 0
        self.last_chat_idx = 0
        self.btn_start.config(text="● LIVE", bg="#1a3a1a", fg="#4ADE80",
                              state=tk.DISABLED)
        self.btn_next_day.pack_forget()
        self._loop()

    # ─────────────────────────────────────────────────────────────
    # Main loop
    # speed=1  → delay=1000 ms  → 1 sim-minute per real second
    # speed=N  → delay=1000/N ms → N sim-minutes per real second
    # ─────────────────────────────────────────────────────────────
    def _loop(self):
        if self.state.running:
            self.state = tick(self.state)
            self._render()
            delay = max(16, 1000 // self.speed)
            self.root.after(delay, self._loop)
        else:
            self._render()
            self.btn_start.config(text="CLOSED", bg="#1c1c38", fg="#555")
            self.btn_next_day.pack(side=tk.LEFT, padx=5)

    # ─────────────────────────────────────────────────────────────
    # Rendering
    # ─────────────────────────────────────────────────────────────
    def _render(self):
        st = self.state
        self.label_time.config(text=fmt_time(st.time))
        self.label_day.config(text=f"Day {st.day}")

        promos = active_promotions(st)
        self.label_promo.config(
            text=("🎉  " + "  •  ".join(p["name"] for p in promos)) if promos else ""
        )

        # Day progress bar
        hour = (st.time // 60) % 24
        pct  = clamp((hour - CONFIG["open"]) / (CONFIG["close"] - CONFIG["open"]), 0, 1)
        bar_w = self.day_bar.winfo_width() or 1300
        self.day_bar.delete("all")
        self.day_bar.create_rectangle(0, 0, bar_w * pct, 5, fill="#6366f1", outline="")

        # Stats
        cfg = CONFIG
        pc_busy  = sum(1 for s in st.seats if s.type == "pc"      and s.status == "busy")
        vip_busy = sum(1 for s in st.seats if s.type == "vip"     and s.status == "busy")
        con_busy = sum(1 for s in st.seats if s.type == "console" and s.status == "busy")
        total_seats = cfg["pc"] + cfg["vip"] + cfg["console"]
        total_busy  = pc_busy + vip_busy + con_busy
        occ_pct     = round(total_busy / total_seats * 100) if total_seats else 0
        broken      = sum(1 for s in st.seats if s.hp < 20)
        avg_mood    = (round(sum(s.needs.mood for s in st.sessions) / len(st.sessions))
                       if st.sessions else 0)
        total_exp   = (cfg["rent"] + cfg["electric"]
                       + sum(s.salary for s in st.staff) + st.expenses)
        profit      = st.revenue + st.food_revenue - total_exp

        for key, (val, color) in {
            "revenue":   (fmt_money(st.revenue + st.food_revenue), "#4ADE80"),
            "expenses":  (fmt_money(total_exp), "#EF4444"),
            "profit":    (fmt_money(profit), "#4ADE80" if profit >= 0 else "#EF4444"),
            "served":    (str(st.served), "#818CF8"),
            "queue":     (str(len(st.queue)), "#F472B6"),
            "active":    (str(len(st.sessions)), "#3B82F6"),
            "occupancy": (f"{occ_pct}%",
                          "#22D3EE" if occ_pct < 70 else "#FBBF24" if occ_pct < 90 else "#EF4444"),
            "broken":    (str(broken), "#4ADE80" if broken == 0 else "#EF4444"),
            "mood":      (f"{avg_mood}%",
                          "#4ADE80" if avg_mood > 60 else "#FBBF24" if avg_mood > 30 else "#EF4444"),
        }.items():
            self.stat_labels[key].config(text=val, fg=color)

        # Zone bars
        zc  = self.zones_canvas
        zc.delete("all")
        zw  = zc.winfo_width() or 260
        bar_l = 40; bar_r = zw - 40
        for i, (name, total, busy, color) in enumerate([
            ("PC",  cfg["pc"],      pc_busy,  "#3B82F6"),
            ("VIP", cfg["vip"],     vip_busy, "#D97706"),
            ("CON", cfg["console"], con_busy, "#059669"),
        ]):
            y    = i * 22 + 2
            frac = busy / total if total else 0
            zc.create_rectangle(bar_l, y, bar_r, y + 16, fill="#0f0f20", outline="#222244")
            if frac > 0:
                zc.create_rectangle(bar_l, y, bar_l + (bar_r - bar_l) * frac, y + 16,
                                    fill=color, outline="")
            zc.create_text(bar_l - 4, y + 8, text=name, fill=color,
                           font=("Consolas", 8, "bold"), anchor="e")
            zc.create_text(bar_r + 4, y + 8, text=f"{busy}/{total}", fill="#666",
                           font=("Consolas", 8), anchor="w")

        # Reservations
        if st.reservations:
            lines = [f"  {rv.client.name}  {rv.seat_type}  @{fmt_time(rv.time)}"
                     for rv in st.reservations[:5]]
            self.label_reservations.config(text="\n".join(lines))
        else:
            self.label_reservations.config(text="  None")

        self._render_canvas()
        self._update_text_panel()

    # ─────────────────────────────────────────────────────────────
    def _render_canvas(self):
        c  = self.canvas
        c.delete("all")
        W  = c.winfo_width()  or 820
        H  = c.winfo_height() or 440
        st = self.state

        session_map = {s.seat_id: s for s in st.sessions}

        # ── Background ───────────────────────────────────────────
        c.create_rectangle(0, 0, W, H, fill="#0b0b18", outline="")

        # ── Floor strip ──────────────────────────────────────────
        floor_h = 54
        fy      = H - floor_h
        for x1f, x2f, bg, label in [
            (0,       W*0.14, "#0e0e30", "🚻 Restrooms"),
            (W*0.15,  W*0.32, "#180e04", "☕ Snack Bar"),
            (W*0.34,  W*0.52, "#080e18", "🛋️ Lobby"),
            (W*0.54,  W*0.69, "#131308", "🔧 Tech Room"),
            (W*0.71,  W-1,    "#081808", "🚪 Entrance"),
        ]:
            c.create_rectangle(x1f+1, fy+2, x2f-1, H-1, fill=bg, outline="#1e1e44")
            c.create_text((x1f + x2f) / 2, fy + 14,
                          text=label, fill="#444", font=("Consolas", 8))

        # ── Seat zones ───────────────────────────────────────────
        zone_h = H - floor_h - 6
        zones_def = [
            ("pc",      "PC ZONE",      "#3B82F6",  2,        3,       W*0.56, zone_h*0.55 + 3),
            ("vip",     "VIP ZONE",     "#D97706",  W*0.575,  3,       W-1,    zone_h*0.46 + 3),
            ("console", "CONSOLE ZONE", "#059669",  2,        zone_h*0.58+2, W*0.56, zone_h + 3),
        ]

        for typ, name, color, x1, y1, x2, y2 in zones_def:
            c.create_rectangle(x1, y1, x2, y2,
                               fill="#08081a", outline=color, width=1, dash=(4, 3))
            c.create_text(x1 + 9, y1 + 10, text=name, fill=color,
                          font=("Consolas", 8, "bold"), anchor="w")

            zone_seats = [s for s in st.seats if s.type == typ]
            zw2   = x2 - x1 - 14
            zh2   = y2 - y1 - 24
            cols  = max(1, int(zw2 / 52))
            rows  = max(1, math.ceil(len(zone_seats) / cols))
            cw    = zw2 / cols
            ch    = min(50, zh2 / rows) if rows > 0 else 42

            for idx, seat in enumerate(zone_seats):
                r = idx // cols
                col = idx % cols
                mx = x1 + 7 + col * cw + cw / 2
                my = y1 + 21 + r * ch + ch / 2

                self.seat_coords[seat.id] = (mx, my)
                session = session_map.get(seat.id)

                if seat.hp < 20:
                    # Broken
                    c.create_rectangle(mx-21, my-17, mx+21, my+17,
                                       fill="#1a0808", outline="#5a1010", width=1)
                    c.create_text(mx, my - 3, text="💥", font=("", 11))
                    c.create_text(mx, my + 11, text=seat.id,
                                  fill="#5a1010", font=("Consolas", 6))

                elif session:
                    # Occupied — draw mini character
                    c.create_rectangle(mx-21, my-17, mx+21, my+17,
                                       fill="#0f0b1e", outline=color, width=1)
                    ap    = session.appearance
                    mood  = session.needs.mood
                    mc    = ("#4ADE80" if mood > 60 else
                             "#FBBF24" if mood > 30 else "#EF4444")

                    # Head
                    c.create_oval(mx-6, my-15, mx+6, my-3, fill=ap.skin, outline="")
                    # Hair
                    if ap.hair_style == 0:
                        c.create_arc(mx-7, my-18, mx+7, my-8,
                                     start=0, extent=180, fill=ap.hair, outline="")
                    elif ap.hair_style == 1:
                        c.create_rectangle(mx-7, my-18, mx+7, my-12,
                                           fill=ap.hair, outline="")
                    else:
                        c.create_polygon(mx-7, my-11, mx, my-20, mx+7, my-11,
                                         fill=ap.hair, outline="")
                    # Glasses
                    if ap.glasses:
                        c.create_oval(mx-6, my-13, mx-1, my-8, outline="#777", width=1)
                        c.create_oval(mx+1, my-13, mx+6, my-8, outline="#777", width=1)
                    # Body
                    c.create_rectangle(mx-7, my-1, mx+7, my+9, fill=ap.shirt, outline="")
                    # Mood strip
                    c.create_rectangle(mx-5, my+11, mx+5, my+14, fill=mc, outline="")

                    # Activity overlay
                    act_icon = {"bathroom": "🚻", "buying_food": "🍕"}.get(session.activity)
                    if act_icon:
                        c.create_text(mx+15, my-13, text=act_icon, font=("", 7))

                    # Group badge
                    if session.group is not None:
                        c.create_text(mx-15, my-13, text="👥", font=("", 6))

                    # Match result badge
                    if session.match_result == "win":
                        c.create_text(mx+15, my+6, text="🏆", font=("", 6))
                    elif session.match_result == "loss":
                        c.create_text(mx+15, my+6, text="💀", font=("", 6))

                    c.create_text(mx, my+17, text=seat.id, fill="#444", font=("Consolas", 5))

                elif seat.reserved_for is not None:
                    # Reserved
                    c.create_rectangle(mx-21, my-17, mx+21, my+17,
                                       fill="#191400", outline="#4a3800", dash=(2, 2))
                    c.create_text(mx, my - 2, text="📋", font=("", 10))
                    c.create_text(mx, my + 12, text="RSVD",
                                  fill="#D97706", font=("Consolas", 5, "bold"))
                else:
                    # Free
                    c.create_rectangle(mx-21, my-17, mx+21, my+17,
                                       fill="#07180a", outline="#153518")
                    icons = {"pc": "🖥️", "vip": "👑", "console": "🎮"}
                    c.create_text(mx, my - 2, text=icons.get(seat.type, "?"), font=("", 10))
                    c.create_text(mx, my + 12, text=seat.id,
                                  fill="#153518", font=("Consolas", 5))

        # ── Queue display in the entrance area ───────────────────
        if st.queue:
            qx  = W * 0.71 + 6
            qy0 = H - floor_h + 3
            c.create_text(qx, qy0, text=f"Queue: {len(st.queue)}",
                          fill="#F472B6", font=("Consolas", 7, "bold"), anchor="w")
            for i, cl in enumerate(st.queue[:8]):
                px = qx + (i % 4) * 24
                py = qy0 + 12 + (i // 4) * 22
                ap = cl.appearance
                c.create_oval(px, py,     px+10, py+10, fill=ap.skin,  outline="")
                c.create_rectangle(px-1, py+10, px+11, py+18, fill=ap.shirt, outline="")
            if len(st.queue) > 8:
                c.create_text(qx + 105, qy0 + 20, text=f"+{len(st.queue)-8}",
                              fill="#888", font=("Consolas", 7))

    # ─────────────────────────────────────────────────────────────
    def _update_text_panel(self):
        st  = self.state
        tab = self.current_tab.get()
        p   = self.text_panel
        p.config(state=tk.NORMAL)

        if tab == "log":
            for log in st.logs[self.last_log_idx:]:
                tag = log.type if log.type in LOG_TYPE_COLORS else "system"
                p.insert(tk.END, f"[{fmt_time(log.time)}]  {log.text}\n", tag)
            self.last_log_idx = len(st.logs)

        elif tab == "chat":
            tag_map = {
                "introvert": "chat_intro",
                "extrovert": "chat_extro",
                "toxic":     "chat_toxic",
                "newbie":    "chat_newbie",
            }
            for msg in st.chats[self.last_chat_idx:]:
                tag  = tag_map.get(msg.personality, "chat_default")
                pers = PERSONALITIES.get(msg.personality)
                emoji = pers.emoji if pers else "?"
                p.insert(tk.END,
                         f"[{fmt_time(msg.time)}]  {emoji} {msg.sender}  ({msg.seat}):  {msg.text}\n",
                         tag)
            self.last_chat_idx = len(st.chats)

        elif tab == "sessions":
            p.delete("1.0", tk.END)
            if st.sessions:
                hdr = f"{'NAME':<14}  {'SEAT':<6}  {'GAME':<16}  ST  MO  HU  EN  REM\n"
                p.insert(tk.END, hdr, "session_hdr")
                for ses in st.sessions[:25]:
                    rem  = ses.end - st.time
                    pers = PERSONALITIES[ses.personality]
                    act  = {"playing": "▶", "bathroom": "🚻", "buying_food": "🍕"}.get(
                               ses.activity, "?")
                    res  = {"win": "🏆", "loss": "💀"}.get(ses.match_result, " ")
                    row  = (f"{ses.client_name:<14}  {ses.seat_id:<6}  "
                            f"{ses.game.name[:16]:<16}  "
                            f"{act} {pers.emoji} "
                            f"{int(ses.needs.mood):3} "
                            f"{int(ses.needs.hunger):3} "
                            f"{int(ses.needs.energy):3} "
                            f"{rem:4}m {res}\n")
                    p.insert(tk.END, row, "session_row")
            else:
                p.insert(tk.END, "  No active sessions.\n", "system")

        p.see(tk.END)
        p.config(state=tk.DISABLED)


# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    root = tk.Tk()
    app  = ClubApp(root)
    app._render()          # initial paint before the loop starts
    root.mainloop()