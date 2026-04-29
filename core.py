"""
CYBER ZONE — Симуляция компьютерного клуба  (v5 — WebSocket архитектура)

Чисто-функциональная архитектура (Hexagonal / Clean):
  L1 DATA       неизменяемые namedtuple-структуры и конфигурация
  L2 FUNCTIONS  чистые переходы состояния (tick_*, apply_command)
  L3 SHELL      WebSocket-сервер (server.py) + браузерный фронтенд (web/index.html)

Этот модуль содержит ТОЛЬКО L1+L2. Никаких побочных эффектов.
"""

import os, math
from collections import namedtuple

# ═══════════════════════════════════════════════════════════════
# L1 — ДАННЫЕ
# ═══════════════════════════════════════════════════════════════

RngState = namedtuple("RngState", ["seed"])
def rng_new(seed):    return RngState(seed=abs(seed) or 1)
def rng_next(rng):
    s = (rng.seed * 48271) % 2147483647
    s = s if s else 1
    return s / 2147483647, RngState(seed=s)
def rng_int(rng, lo, hi):
    v, r = rng_next(rng); return lo + int(v * (hi - lo + 1)), r
def rng_pick(rng, seq):
    if not seq: return None, rng
    idx, r = rng_int(rng, 0, len(seq) - 1); return seq[idx], r
def rng_chance(rng, p):
    v, r = rng_next(rng); return v < p, r

def clamp(v, lo=0, hi=100): return max(lo, min(hi, v))
def fmt_time(mins):          return f"{(mins // 60) % 24:02d}:{mins % 60:02d}"
def fmt_money(n):            return f"{n:.0f}₽"

# ── Конфигурация ─────────────────────────────────────────────────
CONFIG = {
    "open": 7*60, "close": 26*60,   # 07:00 – 02:00
    "pc": 30, "vip": 5, "console": 5,
    "pc_rows": 6, "pc_cols": 5,
    "lounge_cap": 10,
    "rent": 500, "electric": 150,
    "wage_admin": 120, "wage_worker": 90,
}

TARIFFS = {
    "pc": {
        "min":{"name":"Поминутный","duration":None,"price_per_min":2},
        "1h": {"name":"1 Час","duration":60,"fixed":200},
        "2h": {"name":"2 Часа","duration":120,"fixed":350},
        "3h": {"name":"3 Часа","duration":180,"fixed":450},
        "5h": {"name":"5 Часов","duration":300,"fixed":600},
    },
    "console": {
        "min":{"name":"Поминутный","duration":None,"price_per_min":2},
        "1h": {"name":"1 Час","duration":60,"fixed":200},
        "2h": {"name":"2 Часа","duration":120,"fixed":300},
        "3h": {"name":"3 Часа","duration":180,"fixed":500},
        "5h": {"name":"5 Часов","duration":300,"fixed":700},
    },
    "vip": {
        "min":{"name":"Поминутный","duration":None,"price_per_min":5},
        "1h": {"name":"1 Час","duration":60,"fixed":350},
        "2h": {"name":"2 Часа","duration":120,"fixed":500},
        "3h": {"name":"3 Часа","duration":180,"fixed":750},
        "5h": {"name":"5 Часов","duration":300,"fixed":1000},
    },
}
TARIFF_KEYS = ("min","1h","2h","3h","5h")

PROMOTIONS = [
    {"id":"night","name":"Ночная −15%","discount":0.15,
     "from":21*60,"to":26*60,"days":(0,1,2,3,4,5,6),"active":True},
    {"id":"weekday","name":"Будни −10%","discount":0.10,
     "from":7*60,"to":26*60,"days":(0,1,2,3,4),"active":True},
]

Food = namedtuple("Food", ["name","price","prep_time","cost"])
MENU = (
    Food("Энергетик",       85,1, 35),
    Food("Вода",            90,1, 20),
    Food("Лимонад",         80,1, 30),
    Food("Чипсы",           60,1, 25),
    Food("Шоколадный батончик",120,1,45),
    Food("Бургер с картофелем",350,5,150),
)
INITIAL_STOCK = {f.name: 20 for f in MENU}
WAREHOUSE_RESTOCK = {f.name: 30 for f in MENU}

Game = namedtuple("Game", ["name","genre","max_players"])
PC_GAMES = (
    Game("DOTA 2","MOBA",5), Game("League of Legends","MOBA",5),
    Game("CS2","FPS",5), Game("Overwatch 2","FPS",5),
    Game("Minecraft","Sandbox",8), Game("Valorant","FPS",5),
    Game("GTA V","Action",4), Game("PUBG","BR",4),
    Game("Dead by Daylight","Horror",5), Game("Sims 4","Life",1),
    Game("Standoff 2","FPS",5), Game("Genshin Impact","RPG",4),
)
CONSOLE_GAMES = (
    Game("FIFA 24","Sports",2), Game("Tekken 8","Fighting",2),
    Game("Mortal Kombat 1","Fighting",2), Game("It Takes Two","Co-op",2),
    Game("Split Fiction","Co-op",2), Game("The Quarry","Horror",2),
)

# Имена-запасные (используются если файлы не найдены)
_FALLBACK_NAMES = {
    "m":{"names":["Артём","Дмитрий","Максим","Иван","Александр","Михаил",
                   "Даниил","Кирилл","Егор","Никита","Матвей","Роман",
                   "Лев","Марк","Андрей","Павел","Сергей","Тимур"],
         "surnames":["Иванов","Петров","Сидоров","Козлов","Новиков","Морозов",
                     "Волков","Соколов","Попов","Лебедев","Кузнецов","Смирнов"]},
    "f":{"names":["Алиса","Мария","Анна","София","Ева","Виктория","Полина",
                   "Дарья","Екатерина","Арина","Вероника","Кира","Милана",
                   "Ульяна","Алина","Елена"],
         "surnames":["Иванова","Петрова","Сидорова","Козлова","Новикова","Морозова",
                     "Волкова","Соколова","Попова","Лебедева","Кузнецова","Смирнова"]},
}
_FALLBACK_PHRASES = {
    "chat_questions":["кто-нибудь на мид?","какой билд?","где встречаемся?","кто играет?"],
    "chat_answers":["я возьму мид","потом покажу","встречаемся в лейне","играю я"],
    "chat_emotions":["ура!","вот это да!","огонь!","эх...","ну и ну"],
    "chat_reactions":["согласен","круто","понял","ок","ясно"],
    "live_questions":["как дела?","что играешь?","давно тут?","в какую сегодня?"],
    "live_answers":["нормально","только пришёл","играю в новую","в старую добрую"],
    "live_reactions":["круто","ясно","прикольно","понятно","класс"],
}

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))

def _resolve(path):
    if os.path.isabs(path): return path
    # Search: CWD → CWD/data/ → module dir → module_dir/data/
    for base in [".", os.path.join(".", "data"), _MODULE_DIR, os.path.join(_MODULE_DIR, "data")]:
        candidate = os.path.join(base, path)
        if os.path.exists(candidate):
            return candidate
    return path                      # not found — caller will handle

def load_names_data(nf="names.txt", sf="surnames.txt"):
    out = {"m":{"names":[],"surnames":[]},"f":{"names":[],"surnames":[]}}
    def _p(filename, key):
        rp = _resolve(filename)
        if not os.path.exists(rp):
            return
        try:
            with open(rp, encoding="utf-8") as fh:
                for ln in fh:
                    ln = ln.strip()
                    if not ln or ln.startswith("#"): continue
                    parts = ln.split()
                    if len(parts) < 2: continue
                    tag = parts[-1].lower()
                    g = "m" if tag in ("m","м") else ("f" if tag in ("f","ж") else None)
                    if g: out[g][key].append(" ".join(parts[:-1]))
        except OSError: pass
    _p(nf, "names"); _p(sf, "surnames")
    for g in ("m","f"):
        if not out[g]["names"]:    out[g]["names"]    = list(_FALLBACK_NAMES[g]["names"])
        if not out[g]["surnames"]: out[g]["surnames"] = list(_FALLBACK_NAMES[g]["surnames"])
    return out

def load_phrases(base=None):
    # File names the user is expected to provide.
    # We support two naming conventions simultaneously so either set of files works:
    #   pc_questions.txt  OR  chat_questions.txt  (same data, different name)
    CATS = {
        "chat_questions":  ["pc_questions.txt",   "chat_questions.txt"],
        "chat_answers":    ["pc_answers.txt",      "chat_answers.txt"],
        "chat_emotions":   ["pc_emotions.txt",     "chat_emotions.txt"],
        "chat_reactions":  ["pc_reactions.txt",    "chat_reactions.txt"],
        "live_questions":  ["live_questions.txt"],
        "live_answers":    ["live_answers.txt"],
        "live_reactions":  ["live_reactions.txt"],
    }
    search_bases = [base] if base else [".", os.path.join(".", "data"), _MODULE_DIR, os.path.join(_MODULE_DIR, "data")]
    out = {}
    for cat, filenames in CATS.items():
        lines = []
        for b in search_bases:
            if b is None: continue
            for fn in filenames:
                p = os.path.join(b, fn)
                if os.path.exists(p):
                    try:
                        with open(p, encoding="utf-8") as fh:
                            lines = [l.strip() for l in fh if l.strip()]
                        if lines: break
                    except OSError: pass
            if lines: break
        out[cat] = lines if lines else list(_FALLBACK_PHRASES.get(cat, ["..."]))
    return out

FOOD_TRIGGERS = ["Я хочу заказать {food}","Принесите мне {food}, пожалуйста"]
EXTEND_TRIGGERS = [
    "Я хочу продлить сессию на месте {seat_id} по тарифу {tariff}",
    "Я хочу занять себе новое место {seat_type} по тарифу {tariff}",
]

SHIRT_COLORS=("#FF6B6B","#4ECDC4","#45B7D1","#96CEB4","#FFEAA7","#DDA0DD",
              "#98D8C8","#F7DC6F","#BB8FCE","#85C1E9","#F0B27A","#82E0AA",
              "#FF9FF3","#54A0FF","#5F27CD","#01A3A4","#F368E0","#EE5A24")
SKIN_COLORS=("#FDBCB4","#F1C27D","#E0AC69","#C68642","#8D5524")
HAIR_COLORS=("#2C1810","#4A2C1A","#8B4513","#D2691E","#FFD700","#1A1A2E","#C0C0C0")

Appearance = namedtuple("Appearance",["skin","shirt","hair","glasses","hair_style"])
def make_appearance(rng):
    sk,rng=rng_pick(rng,SKIN_COLORS); sh,rng=rng_pick(rng,SHIRT_COLORS)
    hr,rng=rng_pick(rng,HAIR_COLORS); gl,rng=rng_chance(rng,0.25)
    st,rng=rng_int(rng,0,2)
    return Appearance(sk,sh,hr,gl,st),rng

Seat = namedtuple("Seat",["id","type","row","col","capacity","occupants"])
def seat_free(s): return s.occupants < s.capacity
def make_seats(cfg):
    seats=[]
    for i in range(1,cfg["pc"]+1):
        seats.append(Seat(f"ПК-{i}","pc",(i-1)//cfg["pc_cols"]+1,(i-1)%cfg["pc_cols"]+1,1,0))
    for i in range(1,cfg["vip"]+1):
        seats.append(Seat(f"ВИП-{i}","vip",1,i,1,0))
    for i in range(1,cfg["console"]+1):
        seats.append(Seat(f"КОНС-{i}","console",1,i,2,0))
    return tuple(seats)

Client = namedtuple("Client",[
    "id","name","gender","pref","tariff","duration",
    "arrived","game","group","appearance",
    "reservation","reservation_time","visits","rank",
])

def generate_identity(rng, nd):
    is_m,rng=rng_chance(rng,0.55); g="m" if is_m else "f"
    first,rng=rng_pick(rng,nd[g]["names"]); last,rng=rng_pick(rng,nd[g]["surnames"])
    return f"{first} {last}", g, rng

def make_client(cid, t, rng, nd, group=None, gg=None, gp=None):
    name, gender, rng = generate_identity(rng, nd)
    if gp:
        pref = gp
    else:
        r, rng = rng_next(rng)
        pref = "console" if r < 0.12 else ("vip" if r < 0.22 else "pc")

    game = gg
    if game is None:
        pool = CONSOLE_GAMES if pref == "console" else PC_GAMES
        game, rng = rng_pick(rng, pool)

    # Only offer tariffs that end at or before closing — this is the authoritative filter.
    valid_keys = get_valid_tariffs(pref, t, CONFIG["close"])
    tk_, rng = rng_pick(rng, valid_keys)
    dur = TARIFFS[pref][tk_].get("duration")
    if dur is None:
        # Per-minute: pick a stay length that doesn't overshoot closing.
        max_stay = max(30, CONFIG["close"] - t)
        hi = min(180, max_stay)
        dur, rng = rng_int(rng, 30, hi)
    # Final safety clamp — should never be needed after the above, but keep for safety.
    dur = min(dur, max(1, CONFIG["close"] - t))

    app, rng = make_appearance(rng)

    has_res, rng = rng_chance(rng, 0.12 if group is None else 0.0)
    res_time = None
    if has_res:
        off, rng = rng_int(rng, 30, 90)
        res_time = t + off
        if res_time >= CONFIG["close"]:
            has_res = False; res_time = None

    visits, rng = rng_int(rng, 0, 15)
    rank = ("Легенда" if visits > 20 else "Про" if visits > 10
            else "Постоянный" if visits > 3 else "Новичок")
    return Client(cid, name, gender, pref, tk_, dur, t, game, group,
                  app, has_res, res_time, visits, rank), rng

def make_group(sid, t, gid, rng, nd):
    size,rng=rng_int(rng,2,4); r,rng=rng_next(rng)
    pref="console" if r<0.25 else "pc"
    if pref=="console": size=min(size,2)
    pool=CONSOLE_GAMES if pref=="console" else PC_GAMES
    valid=[g for g in pool if g.max_players>=size]
    game,rng=rng_pick(rng,valid if valid else pool)
    members=[]
    for i in range(size):
        cl,rng=make_client(sid+i,t,rng,nd,group=gid,gg=game,gp=pref); members.append(cl)
    return tuple(members),rng

Reservation=namedtuple("Reservation",["client_id","client","time","seat_type"])
Log=namedtuple("Log",["time","text","type"])
ChatMsg=namedtuple("ChatMsg",["time","sender","text","seat","kind"])
LoungeSlot=namedtuple("LoungeSlot",["client","arrived_time","patience"])
Order=namedtuple("Order",["id","client_id","session_id","food","status","worker_id"])
HallWorker=namedtuple("HallWorker",["id","name","status","timer","order_id","appearance"])
AdminState=namedtuple("AdminState",["status","timer","target","group_members"])

Session=namedtuple("Session",[
    "id","client_id","client_name","gender",
    "seat_id","seat_type","game",
    "start","end","tariff","group","appearance",
    "fixed_price","promo_discount",
    "food_cooldown","trigger_cooldown","pending_order_id",
    "chat_state","chat_timer","live_timer","leave_at",
])

def _make_session(sid,client,seat,t,fixed_price,promo_disc,leave_at):
    end = t + client.duration
    if end > CONFIG["close"]: end = CONFIG["close"]
    return Session(
        id=sid,client_id=client.id,client_name=client.name,gender=client.gender,
        seat_id=seat.id,seat_type=seat.type,game=client.game,
        start=t,end=end,tariff=client.tariff,
        group=client.group,appearance=client.appearance,
        fixed_price=fixed_price,promo_discount=promo_disc,
        food_cooldown=0,trigger_cooldown=300,pending_order_id=None,
        chat_state="idle",chat_timer=5,live_timer=2,leave_at=leave_at,
    )

FoodStock=namedtuple("FoodStock",["items","warehouse","warehouse_timer","purchase_cost"])

def make_food_stock():
    return FoodStock(
        items=dict(INITIAL_STOCK),
        warehouse=dict(WAREHOUSE_RESTOCK),
        warehouse_timer=7,
        purchase_cost=0.0,
    )

def restock_from_warehouse(fs):
    new_items = dict(fs.items); new_wh = dict(fs.warehouse); cost = fs.purchase_cost
    for f in MENU:
        need = INITIAL_STOCK[f.name] - new_items.get(f.name, 0)
        if need > 0:
            avail = min(need, new_wh.get(f.name, 0))
            new_items[f.name] = new_items.get(f.name, 0) + avail
            new_wh[f.name] = new_wh.get(f.name, 0) - avail
            cost += avail * f.cost
    return fs._replace(items=new_items, warehouse=new_wh, purchase_cost=cost)

def refill_warehouse(fs):
    return fs._replace(warehouse=dict(WAREHOUSE_RESTOCK), warehouse_timer=7)

World=namedtuple("World",[
    "time","day","weekday","running","paused","rng",
    "seats","queue","lounge","sessions","reservations",
    "admin","admin_name","admin_appearance",
    "hall_workers","order_queue","food_stock",
    "revenue","food_revenue","expenses",
    "served","lost_clients",
    "next_client","next_session","next_group","next_order",
    "arrival_timer",
    "logs","chats","promotions",
    "names_data","phrases_data",
    "last_action",
    "bathroom_clients",
])

BathroomClient=namedtuple("BathroomClient",["session_id","client_name","appearance","timer"])

_ADMIN_APPEARANCE = Appearance("#F1C27D","#2563EB","#2C1810",True,0)
_WORKER_APPEARANCES = (
    Appearance("#FDBCB4","#059669","#4A2C1A",False,1),
    Appearance("#E0AC69","#D97706","#1A1A2E",False,2),
)

def initial_state(seed=42, names_data=None, phrases_data=None):
    cfg = CONFIG
    nd = names_data   if names_data   is not None else load_names_data()
    pd = phrases_data if phrases_data is not None else load_phrases()
    # Staff names/appearances use a separate RNG seeded off the main seed
    # so they don't affect the main simulation sequence.
    rng0 = rng_new(seed ^ 0xABCD)
    # Admin: female
    an,  rng0 = rng_pick(rng0, nd["f"]["names"])
    as_, rng0 = rng_pick(rng0, nd["f"]["surnames"])
    admin_name = f"{an} {as_}"
    admin_app, rng0 = make_appearance(rng0)
    # Force a recognisable admin shirt (dark blue) but keep rest random
    admin_app = admin_app._replace(shirt="#1d4ed8")
    # Worker 1 (male)
    wn1, rng0 = rng_pick(rng0, nd["m"]["names"]); ws1, rng0 = rng_pick(rng0, nd["m"]["surnames"])
    wa1, rng0 = make_appearance(rng0)
    # Worker 2 (female)
    wn2, rng0 = rng_pick(rng0, nd["f"]["names"]); ws2, rng0 = rng_pick(rng0, nd["f"]["surnames"])
    wa2, rng0 = make_appearance(rng0)
    return World(
        time=cfg["open"], day=1, weekday=0, running=False, paused=False, rng=rng_new(seed),
        seats=make_seats(cfg),
        queue=(), lounge=(), sessions=(), reservations=(),
        admin=AdminState("idle",0,None,None),
        admin_name=admin_name, admin_appearance=admin_app,
        hall_workers=(
            HallWorker("w1", f"{wn1} {ws1}", "idle", 0, None, wa1),
            HallWorker("w2", f"{wn2} {ws2}", "idle", 0, None, wa2),
        ),
        order_queue=(), food_stock=restock_from_warehouse(make_food_stock()),
        revenue=0.0, food_revenue=0.0, expenses=0.0,
        served=0, lost_clients=0,
        next_client=1, next_session=1, next_group=1, next_order=1,
        arrival_timer=2,
        logs=(Log(cfg["open"], "CYBER ZONE открыт! День 1", "system"),),
        chats=(), promotions=tuple(PROMOTIONS),
        names_data=nd, phrases_data=pd,
        last_action="Клуб открыт",
        bathroom_clients=(),
    )

# ═══════════════════════════════════════════════════════════════
# L2 — ФУНКЦИИ (Без изменений логики, только использование chat_ файлов)
# ═══════════════════════════════════════════════════════════════

def active_promotions(st):
    return tuple(p for p in st.promotions
                 if p["active"] and p["from"]<=st.time<p["to"] and st.weekday in p["days"])

def best_discount(promos):
    return max((p["discount"] for p in promos), default=0.0)

def calculate_price(seat_type, tariff_key, duration, promo_disc):
    tf=TARIFFS[seat_type][tariff_key]
    base=tf["fixed"] if "fixed" in tf else duration*tf["price_per_min"]
    return base*(1-promo_disc)

def get_valid_tariffs(seat_type, t, close, res_time=None):
    limit=close
    if res_time is not None: limit=min(limit,res_time-60)
    valid=[]
    for k in TARIFF_KEYS:
        d=TARIFFS[seat_type][k].get("duration")
        if d is None: valid.append(k)
        elif t+d<=limit: valid.append(k)
    return valid or ["min"]

def _res_count(reservations, stype, t, window=60):
    return sum(1 for r in reservations if r.seat_type==stype and 0<r.time-t<=window)

def _avail_seats(seats, reservations, t, stype):
    free=[s for s in seats if s.type==stype and seat_free(s)]
    blocked=_res_count(reservations,stype,t)
    return free[:max(0,len(free)-blocked)] if blocked else free

def _seat_inc(seats, sid):
    out=list(seats); idx=next(i for i,s in enumerate(out) if s.id==sid)
    out[idx]=out[idx]._replace(occupants=out[idx].occupants+1); return tuple(out)

def _seat_dec(seats, sid):
    out=list(seats); idx=next((i for i,s in enumerate(out) if s.id==sid),None)
    if idx is not None: out[idx]=out[idx]._replace(occupants=max(0,out[idx].occupants-1))
    return tuple(out)

def tick_arrivals(st):
    t=st.time; rng=st.rng
    queue=list(st.queue); resvs=list(st.reservations)
    logs=list(st.logs); lounge=list(st.lounge)
    nc,ng=st.next_client,st.next_group
    timer=st.arrival_timer; lost=st.lost_clients
    last=st.last_action

    total_free=sum(1 for s in st.seats if seat_free(s))
    too_late = t >= CONFIG["close"] - 60

    if timer<=0 and not too_late:
        is_group,rng=rng_chance(rng,0.30)
        if is_group:
            grp,rng=make_group(nc,t,ng,rng,st.names_data)
            if total_free==0 and len(lounge)>=CONFIG["lounge_cap"]:
                lost+=len(grp); logs.append(Log(t,f"❌ Группа из {len(grp)} ушла — клуб полон","leave")); last=f"Группа из {len(grp)} ушла — клуб полон"
            else:
                queue.extend(grp); logs.append(Log(t,f"👥 Группа «{grp[0].name} и друзья» ({len(grp)} чел) → {grp[0].game.name}","arrival")); last=f"Группа «{grp[0].name}» пришла"
            nc+=len(grp); ng+=1
        else:
            cl,rng=make_client(nc,t,rng,st.names_data)
            if cl.reservation:
                resvs.append(Reservation(cl.id,cl,cl.reservation_time,cl.pref)); logs.append(Log(t,f"📋 {cl.name} забронировал {cl.pref} на {fmt_time(cl.reservation_time)}","reservation")); last=f"{cl.name} забронировал место"
            elif total_free==0 and len(lounge)>=CONFIG["lounge_cap"]:
                lost+=1; logs.append(Log(t,f"❌ {cl.name} ушёл — клуб полон","leave")); last=f"{cl.name} ушёл — полон"
            else:
                queue.append(cl); logs.append(Log(t,f"→ {cl.name} в очередь ({cl.pref})","arrival")); last=f"{cl.name} пришёл"
            nc+=1
        
        if 12*60 <= t < 18*60:      base_lo,base_hi = 4, 10
        elif 18*60 <= t < 22*60:    base_lo,base_hi = 3, 8
        elif 22*60 <= t:            base_lo,base_hi = 8, 18
        else:                       base_lo,base_hi = 8, 15
        timer,rng=rng_int(rng,base_lo,base_hi)
    elif not too_late:
        timer-=1

    due=[r for r in resvs if t>=r.time]; remaining=[r for r in resvs if t<r.time]
    for rv in due: queue.insert(0,rv.client); logs.append(Log(t,f"📋 {rv.client.name} пришёл по брони","reservation")); last=f"{rv.client.name} пришёл по брони"

    return st._replace(queue=tuple(queue),reservations=tuple(remaining),lounge=tuple(lounge),lost_clients=lost,next_client=nc,next_group=ng,arrival_timer=timer,logs=tuple(logs),rng=rng,last_action=last)

def tick_lounge(st):
    t=st.time; logs=list(st.logs); kept=[]; last=st.last_action
    for lc in st.lounge:
        if lc.patience<=1: logs.append(Log(t,f"🚪 {lc.client.name} устал ждать и ушёл","leave")); last=f"{lc.client.name} ушёл из лаунжа"
        else: kept.append(lc._replace(patience=lc.patience-1))
    return st._replace(lounge=tuple(kept),logs=tuple(logs),last_action=last)

def _pick_lounge(lounge, seats, resvs, t):
    for i,lc in enumerate(lounge):
        if _avail_seats(seats,resvs,t,lc.client.pref): return i
    return None

def _find_seat(seats, resvs, t, client):
    a=_avail_seats(seats,resvs,t,client.pref)
    if a: return a[0]
    for tp in ("pc","console","vip"):
        if tp==client.pref: continue
        a=_avail_seats(seats,resvs,t,tp)
        if a: return a[0]
    return None

def _find_group_seats(seats, resvs, t, size, pref):
    if pref=="console" and size<=2:
        a=_avail_seats(seats,resvs,t,"console"); return [a[0]] if a else None
    a=_avail_seats(seats,resvs,t,pref)
    if len(a)<size:
        for tp in ("pc","console","vip"):
            if tp==pref: continue
            a=_avail_seats(seats,resvs,t,tp)
            if len(a)>=size: break
        else: return None
    by_row={}
    for s in a: by_row.setdefault(s.row,[]).append(s)
    for rs in by_row.values():
        if len(rs)>=size: return rs[:size]
    return a[:size]

def _start_ses(sid, cl, seat, t, promos, rng):
    pd=best_discount(promos); tf=TARIFFS[seat.type][cl.tariff]
    leave_at=None
    if tf.get("duration") is None:
        la,rng=rng_int(rng,40,120); leave_at=t+la
        if leave_at>CONFIG["close"]: leave_at=CONFIG["close"]
        price=0
    else:
        price=calculate_price(seat.type,cl.tariff,cl.duration,pd)
    return _make_session(sid,cl,seat,t,price,pd,leave_at),rng

def tick_admin(st):
    t=st.time; rng=st.rng; admin=st.admin; queue=list(st.queue); lounge=list(st.lounge); seats=st.seats; sessions=list(st.sessions); sid=st.next_session; logs=list(st.logs); last=st.last_action; promos=active_promotions(st)

    if admin.status=="idle":
        li=_pick_lounge(lounge,seats,st.reservations,t)
        if li is not None:
            lc=lounge.pop(li); admin=AdminState("seating_lounge",1,lc.client,None); logs.append(Log(t,f"👔 Админ обслуживает {lc.client.name} (из лаунжа)","activity")); last=f"Админ обслуживает {lc.client.name}"
        elif queue:
            head=queue[0]
            if head.group is None: queue.pop(0); admin=AdminState("processing",1,head,None)
            else:
                members=[c for c in queue if c.group==head.group]; queue=[c for c in queue if c.group!=head.group]; proc,rng=rng_int(rng,2,3); admin=AdminState("processing",proc,head,members)

    elif admin.status in ("processing","seating_lounge"):
        if admin.timer>1: admin=admin._replace(timer=admin.timer-1)
        else:
            target=admin.target; members=admin.group_members
            if members:
                chosen=_find_group_seats(seats,st.reservations,t,len(members),target.pref)
                if chosen is not None:
                    if len(chosen)==1 and chosen[0].type=="console":
                        sid_=chosen[0].id; members_to_seat = members[:chosen[0].capacity]
                        for m in members_to_seat:
                            seat_now=next(s for s in seats if s.id==sid_); ses,rng=_start_ses(sid,m,seat_now,t,promos,rng); sessions.append(ses); sid+=1; seats=_seat_inc(seats,sid_)
                        for m in members[len(members_to_seat):]:
                            if len(lounge)<CONFIG["lounge_cap"]: pat,rng=rng_int(rng,15,30); lounge.append(LoungeSlot(m,t,pat))
                    else:
                        for m,s in zip(members,chosen): ses,rng=_start_ses(sid,m,s,t,promos,rng); sessions.append(ses); sid+=1; seats=_seat_inc(seats,s.id)
                    logs.append(Log(t,f"🎮 Группа за местами: {', '.join(m.name for m in members)}","session")); last=f"Группа рассажена"
                else:
                    for m in members:
                        if len(lounge)<CONFIG["lounge_cap"]: pat,rng=rng_int(rng,15,30); lounge.append(LoungeSlot(m,t,pat))
                        else: logs.append(Log(t,f"❌ {m.name} ушёл — лаунж полон","leave"))
                    logs.append(Log(t,"🛋️ Группа в лаунж","activity")); last="Группа отправлена в лаунж"
            else:
                cl=target; seat=_find_seat(seats,st.reservations,t,cl)
                if seat is not None:
                    ses,rng=_start_ses(sid,cl,seat,t,promos,rng); sessions.append(ses); sid+=1; seats=_seat_inc(seats,seat.id); tname=TARIFFS[seat.type][cl.tariff]["name"]; ptxt=f" — {fmt_money(ses.fixed_price)}" if ses.fixed_price>0 else ""
                    logs.append(Log(t,f"✅ {cl.name} → {seat.id} ({cl.game.name}, {tname}){ptxt}","session")); last=f"{cl.name} → {seat.id}"
                else:
                    if len(lounge)<CONFIG["lounge_cap"]: pat,rng=rng_int(rng,15,30); lounge.append(LoungeSlot(cl,t,pat)); logs.append(Log(t,f"🛋️ {cl.name} → лаунж (ждёт {cl.pref})","activity")); last=f"{cl.name} в лаунж"
                    else: logs.append(Log(t,f"❌ {cl.name} ушёл — лаунж полон","leave")); last=f"{cl.name} ушёл"
            admin=AdminState("idle",0,None,None)

    return st._replace(admin=admin,queue=tuple(queue),lounge=tuple(lounge),seats=seats,sessions=tuple(sessions),next_session=sid,logs=tuple(logs),rng=rng,last_action=last)

def tick_behavior(st):
    t=st.time; rng=st.rng; promos=active_promotions(st); cur_disc=best_discount(promos); logs=list(st.logs); chats=list(st.chats); seats=st.seats; orders=list(st.order_queue); next_o=st.next_order; rev=st.revenue; served=st.served; kept=[]; ph=st.phrases_data; last=st.last_action; fs=st.food_stock; bathroom=list(st.bathroom_clients)

    new_bath=[]
    for bc in bathroom:
        if bc.timer<=1: pass
        else: new_bath.append(bc._replace(timer=bc.timer-1))

    pc_by_game={}
    for s in st.sessions:
        if s.seat_type=="pc": pc_by_game.setdefault(s.game.name,[]).append(s.id)

    for ses in st.sessions:
        food_cd=max(0,ses.food_cooldown-1); trig_cd=max(0,ses.trigger_cooldown-1); chat_tm=max(0,ses.chat_timer-1); live_tm=max(0,ses.live_timer-1); chat_st=ses.chat_state; pending=ses.pending_order_id; end=ses.end; fixed=ses.fixed_price

        # ПК-чат использует chat_ файлы
        if ses.seat_type=="pc" and chat_tm==0:
            partners=[p for p in pc_by_game.get(ses.game.name,[]) if p!=ses.id]; talk,rng=rng_chance(rng,0.6 if partners else 0.15)
            if talk:
                if chat_st=="idle" and ph["chat_questions"]: msg,rng=rng_pick(rng,ph["chat_questions"]); chats.append(ChatMsg(t,ses.client_name,msg,ses.seat_id,"pc_chat")); chat_st="asked"
                elif chat_st=="asked" and ph["chat_answers"]: msg,rng=rng_pick(rng,ph["chat_answers"]); chats.append(ChatMsg(t,ses.client_name,msg,ses.seat_id,"pc_chat")); chat_st="answered"
                elif ph["chat_reactions"]: msg,rng=rng_pick(rng,ph["chat_reactions"]); chats.append(ChatMsg(t,ses.client_name,msg,ses.seat_id,"pc_chat")); chat_st="idle"
            else:
                emo,rng=rng_chance(rng,0.25)
                if emo and ph["chat_emotions"]: msg,rng=rng_pick(rng,ph["chat_emotions"]); chats.append(ChatMsg(t,ses.client_name,msg,ses.seat_id,"pc_chat"))
            chat_tm=5

        # Живое общение
        if live_tm==0:
            say,rng=rng_chance(rng,0.28)
            if say:
                cat,rng=rng_pick(rng,("live_questions","live_answers","live_reactions")); pool=ph[cat]
                if pool: msg,rng=rng_pick(rng,pool); chats.append(ChatMsg(t,ses.client_name,msg,ses.seat_id,"live_chat"))
            live_tm=2

        # ── Туалет ───────────────────────────────────────────────
        go_bath, rng = rng_chance(rng, 0.008)
        if go_bath and not any(bc.session_id == ses.id for bc in new_bath):
            btm, rng = rng_int(rng, 2, 5)
            # Bathroom visit extends session end — but never past closing time
            new_end = min(end + btm, CONFIG["close"])
            new_bath.append(BathroomClient(ses.id, ses.client_name, ses.appearance, btm))
            end = new_end
            logs.append(Log(t, f"🚻 {ses.client_name} → туалет", "activity"))

        # Триггеры
        if trig_cd==0 and not any(bc.session_id==ses.id for bc in new_bath): 
            fire,rng=rng_chance(rng,0.35)
            if fire:
                want_food,rng=rng_chance(rng,0.6)
                if want_food and pending is None and food_cd==0:
                    available_menu = [f for f in MENU if fs.items.get(f.name, 0) > 0]
                    if available_menu:
                        food,rng=rng_pick(rng,available_menu); stock_items=dict(fs.items); tpl,rng=rng_pick(rng,FOOD_TRIGGERS); msg=tpl.format(food=food.name)
                        chats.append(ChatMsg(t,ses.client_name,msg,ses.seat_id,"trigger_food")); orders.append(Order(next_o,ses.client_id,ses.id,food,"pending",None)); stock_items[food.name]-=1; fs=fs._replace(items=stock_items); pending=next_o; next_o+=1; trig_cd=300
                elif (not want_food and t >= ses.end
                      and TARIFFS[ses.seat_type][ses.tariff].get("duration") is not None):
                    # Extension only allowed if there is real room left before closing.
                    # Require at least 30 minutes of playtime, and no extension in last 90 min.
                    if t < CONFIG["close"] - 90:
                        valid = get_valid_tariffs(ses.seat_type, t, CONFIG["close"])
                        # Filter to tariffs whose duration >= 30 min (don't extend for 1 min)
                        valid = [k for k in valid if (TARIFFS[ses.seat_type][k].get("duration") or 60) >= 30]
                        if valid:
                            tar_key, rng = rng_pick(rng, valid)
                            tf2 = TARIFFS[ses.seat_type][tar_key]
                            dur = tf2.get("duration") or 60
                            if t + dur <= CONFIG["close"]:
                                extra = calculate_price(ses.seat_type, tar_key, dur, cur_disc)
                                tpl, rng = rng_pick(rng, EXTEND_TRIGGERS)
                                msg = tpl.format(seat_id=ses.seat_id, seat_type=ses.seat_type, tariff=tf2["name"])
                                chats.append(ChatMsg(t, ses.client_name, msg, ses.seat_id, "trigger_extend"))
                                end += dur; fixed += extra
                                logs.append(Log(t, f"⏰ {ses.client_name} продлил +{dur}мин (+{fmt_money(extra)})", "extension"))
                                last = f"{ses.client_name} продлил сессию"; trig_cd = 300

        # ── Departure (natural end or per-minute leave_at) ──────────
        leave = False
        tf = TARIFFS[ses.seat_type][ses.tariff]
        if tf.get("duration") is None:
            # Per-minute: leave at the chosen time (already clamped to close in make_client)
            if ses.leave_at is not None and t >= ses.leave_at:
                leave = True
        else:
            # Fixed tariff: leave at session end.
            if t >= end:
                leave = True
            else:
                # Small probabilistic early departure after the midpoint — not near closing.
                total = end - ses.start; half = ses.start + total // 2
                # Never trigger early departure if we're in the last 30 min before close.
                if t > half and t < CONFIG["close"] - 30:
                    p = (t - half) / max(1, total // 2) * 0.004
                    roll, rng = rng_chance(rng, p)
                    if roll: leave = True

        if leave:
            if tf.get("duration") is None: price=(t-ses.start)*tf["price_per_min"]*(1-ses.promo_discount)
            else: price=fixed
            rev+=price; served+=1; seats=_seat_dec(seats,ses.seat_id); tag=" (досрочно)" if (t<end and tf.get("duration") is not None) else ""
            logs.append(Log(t,f"💰 {ses.client_name} ушёл{tag}. Оплата {fmt_money(price)}","departure")); last=f"{ses.client_name} ушёл — {fmt_money(price)}"; continue

        kept.append(ses._replace(end=end,fixed_price=fixed,food_cooldown=food_cd,trigger_cooldown=trig_cd,chat_timer=chat_tm,live_timer=live_tm,chat_state=chat_st,pending_order_id=pending))

    return st._replace(sessions=tuple(kept),seats=seats,order_queue=tuple(orders),next_order=next_o,food_stock=fs,revenue=rev,served=served,logs=tuple(logs),chats=tuple(chats),rng=rng,last_action=last,bathroom_clients=tuple(new_bath))

def tick_staff(st):
    t=st.time; rng=st.rng; workers=list(st.hall_workers); orders=list(st.order_queue); food_rev=st.food_revenue; sessions=list(st.sessions); logs=list(st.logs); last=st.last_action

    for i,w in enumerate(workers):
        if w.status=="idle":
            for j,o in enumerate(orders):
                if o.status=="pending": orders[j]=o._replace(status="preparing",worker_id=w.id); workers[i]=w._replace(status="delivering",timer=o.food.prep_time,order_id=o.id); logs.append(Log(t,f"🛎️ {w.name} готовит #{o.id}: {o.food.name}","activity")); last=f"{w.name} готовит {o.food.name}"; break
        elif w.status=="delivering":
            ntm=w.timer-1
            if ntm<=0:
                oi=next((k for k,o in enumerate(orders) if o.id==w.order_id),None)
                if oi is not None:
                    o=orders.pop(oi); food_rev+=o.food.price; si=next((k for k,s in enumerate(sessions) if s.id==o.session_id),None)
                    if si is not None: cd,rng=rng_int(rng,180,240); sessions[si]=sessions[si]._replace(pending_order_id=None,food_cooldown=cd)
                    logs.append(Log(t,f"✅ {w.name} доставил {o.food.name} (+{fmt_money(o.food.price)})","food")); last=f"{w.name} доставил {o.food.name}"
                workers[i]=w._replace(status="idle",timer=0,order_id=None)
            else: workers[i]=w._replace(timer=ntm)

    return st._replace(hall_workers=tuple(workers),order_queue=tuple(orders),food_revenue=food_rev,sessions=tuple(sessions),logs=tuple(logs),rng=rng,last_action=last)

def tick_queue(st): return st

def pipeline(*fns):
    def run(st):
        for fn in fns: st=fn(st)
        return st
    return run

def _close_all_sessions(state):
    """Collect any sessions that tick_behavior didn't clear on the last tick (should be rare)."""
    t = state.time; rev = state.revenue; served = state.served
    seats = state.seats; logs = list(state.logs)
    for ses in state.sessions:
        tf = TARIFFS[ses.seat_type][ses.tariff]
        if tf.get("duration") is None:
            price = (t - ses.start) * tf["price_per_min"] * (1 - ses.promo_discount)
        else:
            price = ses.fixed_price
        rev += price; served += 1; seats = _seat_dec(seats, ses.seat_id)
        logs.append(Log(t, f"💰 {ses.client_name} ушёл. Оплата {fmt_money(price)}", "departure"))
    return state._replace(sessions=(), seats=seats, revenue=rev, served=served,
                          logs=tuple(logs), queue=(), lounge=(), bathroom_clients=())

def tick(state):
    if not state.running or state.paused: return state
    t=state.time
    if t>=CONFIG["close"]:
        state=_close_all_sessions(state); total_exp=(CONFIG["rent"]+CONFIG["electric"]+CONFIG["wage_admin"]+2*CONFIG["wage_worker"]+state.expenses+state.food_stock.purchase_cost); profit=state.revenue+state.food_revenue-total_exp
        return state._replace(running=False,paused=False,logs=state.logs+(Log(t,f"🔒 ЗАКРЫТО! Выручка: {fmt_money(state.revenue+state.food_revenue)} Расходы: {fmt_money(total_exp)} Прибыль: {fmt_money(profit)}","system"),),last_action=f"День {state.day} завершён. Прибыль: {fmt_money(profit)}")
    if t<CONFIG["open"]: return state._replace(time=t+1)
    pipe=pipeline(tick_arrivals,tick_lounge,tick_admin,tick_behavior,tick_staff,tick_queue)
    st=pipe(state)
    return st._replace(time=t+1,logs=st.logs[-400:],chats=st.chats[-200:])

def next_day(state):
    new = initial_state(seed=state.rng.seed + 9999,
                        names_data=state.names_data, phrases_data=state.phrases_data)
    nd = state.day + 1; wd = (nd - 1) % 7
    fs = state.food_stock
    if fs.warehouse_timer <= 1: fs = refill_warehouse(fs)
    else: fs = fs._replace(warehouse_timer=fs.warehouse_timer - 1)
    fs = restock_from_warehouse(fs._replace(purchase_cost=0.0))
    return new._replace(
        day=nd, weekday=wd, promotions=state.promotions, food_stock=fs,
        logs=(Log(CONFIG["open"], f"День {nd} начинается!", "system"),),
        last_action=f"День {nd} начинается!",
    )

# ═══════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════
# L2b — КОМАНДЫ и СЕРИАЛИЗАЦИЯ  (по-прежнему чистые функции)
# ═══════════════════════════════════════════════════════════════

def cmd_start(state):
    if state.running: return state
    return state._replace(running=True, paused=False, last_action="Старт симуляции")

def cmd_pause(state):
    if not state.running: return state
    return state._replace(paused=not state.paused,
                          last_action=("Пауза" if not state.paused else "Возобновлено"))

def cmd_reset(state):
    return initial_state(seed=state.rng.seed + 1,
                         names_data=state.names_data,
                         phrases_data=state.phrases_data)

def cmd_new_day(state):
    if state.running: return state
    return next_day(state)._replace(running=True, paused=False)

COMMAND_HANDLERS = {
    "start":   cmd_start,
    "pause":   cmd_pause,
    "reset":   cmd_reset,
    "new_day": cmd_new_day,
}

def apply_command(state, action):
    """Pure: reduce a user-intent (dict with 'action' key) into a new state."""
    handler = COMMAND_HANDLERS.get(action.get("action"))
    return handler(state) if handler else state

# ── Сериализация ──────────────────────────────────────────────────
# Convert the immutable World tree into plain dicts/lists for JSON transport.
def _nt_to_dict(obj):
    if isinstance(obj, tuple) and hasattr(obj, "_asdict"):
        return {k: _nt_to_dict(v) for k, v in obj._asdict().items()}
    if isinstance(obj, (list, tuple)):
        return [_nt_to_dict(x) for x in obj]
    if isinstance(obj, dict):
        return {str(k): _nt_to_dict(v) for k, v in obj.items()}
    return obj

def world_to_dict(state, log_tail=80, chat_tail=80):
    """Serialize `state` (a World), trimming large history lists for transport."""
    trimmed = state._replace(
        logs=state.logs[-log_tail:],
        chats=state.chats[-chat_tail:],
        # names_data and phrases_data are static dictionaries — we don't need to
        # push them to the client; save bandwidth.
        names_data=None,
        phrases_data=None,
        # rng is an implementation detail
        rng=None,
    )
    d = _nt_to_dict(trimmed)
    # Extra convenience fields for the UI:
    hour = (state.time // 60) % 24
    d["clock"] = f"{hour:02d}:{state.time % 60:02d}"
    d["config"] = {
        "open":        CONFIG["open"],
        "close":       CONFIG["close"],
        "pc":          CONFIG["pc"],
        "vip":         CONFIG["vip"],
        "console":     CONFIG["console"],
        "pc_rows":     CONFIG["pc_rows"],
        "pc_cols":     CONFIG["pc_cols"],
        "lounge_cap":  CONFIG["lounge_cap"],
    }
    d["promotions_active"] = [p["name"] for p in active_promotions(state)]
    return d