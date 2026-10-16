"""Игровые данные «Эльдрании»: фракции, классы, герои, монстры, главы, магазин, задания.

Это единственный источник правды. Клиент получает эти данные через GET /api/catalog.
Чтобы добавить героя, достаточно добавить запись в HEROES.
"""

GAME_TITLE = "Эльдрания"
GAME_SUBTITLE = "Сумрачные Врата"

# ---------------------------------------------------------------- фракции
FACTIONS = {
    "dawn": {"name": "Орден Рассвета", "short": "Рассвет", "color": "#f2c46a", "color2": "#7a4f12",
             "desc": "Рыцари-паладины, хранящие последний свет Эльдрании."},
    "grove": {"name": "Изумрудный Круг", "short": "Круг", "color": "#5be3a1", "color2": "#0f4a36",
              "desc": "Друиды и егери древнего леса, говорящие с корнями."},
    "ember": {"name": "Пепельный Легион", "short": "Легион", "color": "#ff7a45", "color2": "#6a1d12",
              "desc": "Наёмники вулканических равнин. Жар в крови, сталь в руках."},
    "tide": {"name": "Хранители Бездны", "short": "Бездна", "color": "#3fe0e0", "color2": "#0b3c5a",
             "desc": "Жрецы и стражи затонувшего храма под лунными водами."},
    "dusk": {"name": "Сумеречный Двор", "short": "Двор", "color": "#b07cff", "color2": "#33196b",
             "desc": "Тайный совет теней, торгующий секретами и судьбами."},
}

# бонусы за сочетание героев одной фракции в отряде: число героев -> (бонус ЗДР, бонус АТК)
FACTION_BONUS = {2: (0.05, 0.00), 3: (0.10, 0.05), 4: (0.15, 0.10), 5: (0.25, 0.15)}

# ---------------------------------------------------------------- классы
CLASSES = {
    "warrior": {"name": "Воин", "desc": "Сильный ближний бой и высокий урон.", "base": (1000, 140, 55, 95)},
    "tank": {"name": "Танк", "desc": "Принимает удары, защищает отряд.", "base": (1500, 90, 90, 80)},
    "mage": {"name": "Маг", "desc": "Урон по площади и проклятия.", "base": (780, 170, 35, 90)},
    "marksman": {"name": "Стрелок", "desc": "Быстро добивает слабейших врагов.", "base": (760, 160, 35, 110)},
    "support": {"name": "Поддержка", "desc": "Лечит и усиливает союзников.", "base": (900, 105, 45, 100)},
}

# ---------------------------------------------------------------- редкости
RARITIES = {
    "common": {"name": "Обычный", "order": 0, "mult": 1.00, "color": "#aab4c6", "glow": "#6e7b92", "dupe_shards": 5},
    "rare": {"name": "Редкий", "order": 1, "mult": 1.12, "color": "#3fe0d0", "glow": "#19a99c", "dupe_shards": 8},
    "epic": {"name": "Эпический", "order": 2, "mult": 1.25, "color": "#b57bff", "glow": "#8a3dff", "dupe_shards": 15},
    "legendary": {"name": "Легендарный", "order": 3, "mult": 1.40, "color": "#ffd57a", "glow": "#ff3d7f", "dupe_shards": 30},
}

# Базовые вероятности призыва (сумма = 1.0). Единственное место, где они заданы.
SUMMON_RATES = {"common": 0.40, "rare": 0.45, "epic": 0.125, "legendary": 0.025}
PITY_EPIC_EVERY = 10      # каждый 10-й призыв без эпика — гарантированный эпик или лучше
PITY_LEGEND_HARD = 50     # 50-й призыв без легендарного — гарантированный легендарный
PITY_SOFT_START = 35      # после 35-го призыва шанс легендарного растёт
PITY_SOFT_STEP = 0.04     # на +4% за каждый следующий призыв
SUMMON_COST = {"tickets": 1, "gems": 150}   # цена одного призыва
SUMMON_X10_DISCOUNT_GEMS = 1350             # x10 за самоцветы дешевле (скидка 10%)

MAX_STARS = 5
STAR_SHARDS = [10, 20, 40, 80, 150]
STAR_GOLD = [1000, 2500, 5000, 9000, 15000]
EQUIP_MAX = 10
EQUIP_SLOTS = ("weapon", "armor", "relic")
EQUIP_SLOT_INFO = {
    "weapon": {"name": "Оружие", "desc": "+5% АТК за уровень"},
    "armor": {"name": "Броня", "desc": "+5% ЗДР и ЗАЩ за уровень"},
    "relic": {"name": "Реликвия", "desc": "+1 СКР и +2% шанса крита за уровень"},
}
EQUIP_NAMES = {
    "weapon": {"warrior": "Клинок", "tank": "Таранный щит", "mage": "Посох", "marksman": "Лук", "support": "Жезл"},
    "armor": {"warrior": "Латы", "tank": "Бастион", "mage": "Мантия", "marksman": "Плащ следопыта", "support": "Одеяние"},
    "relic": {"dawn": "Солнечный талисман", "grove": "Семя жизни", "ember": "Уголь вечного пламени",
              "tide": "Жемчужина бездны", "dusk": "Лунный осколок"},
}

STARTER_HEROES = ["brann", "lyra", "mira"]
STARTER = {"gold": 5000, "exp": 3000, "gems": 600, "tickets": 10, "idle_head_start": 3600}


# ---------------------------------------------------------------- навыки
def fx(type_, to, turns=0, value=0.0, chance=1.0):
    return {"type": type_, "to": to, "turns": turns, "value": value, "chance": chance}


def sk(name, desc, tgt, n=1, dmg=0.0, heal=0.0, effects=()):
    """tgt: front | lowest | random | all_enemies | allies_lowest | all_allies | self"""
    return {"name": name, "desc": desc, "tgt": tgt, "n": n, "dmg": dmg, "heal": heal, "fx": list(effects)}


# ---------------------------------------------------------------- герои
# look — параметры процедурного портрета (замените на PNG/WebP: static/assets/heroes/<key>.webp)
_HEROES = [
    dict(key="brann", name="Бранн Щитоносец", title="Привратный страж", rarity="common", faction="dawn", cls="tank",
         desc="Ветеран привратной стражи. Не отступил ни разу — даже когда врата уже пали.",
         look=dict(hair="#6b4a2b", skin="#d9a77c", style=0, extra="beard"), mod=(1, 1, 1, 1),
         basic=sk("Удар щитом", "Бьёт ближайшего врага.", "front", dmg=1.0),
         ult=sk("Оплот Рассвета", "Накрывает всех союзников щитом на 3 хода.", "all_allies",
                effects=[fx("shield", "allies", 3, 0.12)])),
    dict(key="lyra", name="Лира Зелёная Стрела", title="Егерь Круга", rarity="common", faction="grove", cls="marksman",
         desc="Стреляет раньше, чем ветер успевает сменить направление.",
         look=dict(hair="#2f7a4a", skin="#e3b890", style=1, extra=None), mod=(1, 1, 1, 1),
         basic=sk("Меткий выстрел", "Стреляет во врага с наименьшим здоровьем.", "lowest", dmg=1.1),
         ult=sk("Град стрел", "Обрушивает стрелы на трёх случайных врагов.", "random", n=3, dmg=1.5)),
    dict(key="mira", name="Мира Приливная", title="Целительница отмелей", rarity="common", faction="tide", cls="support",
         desc="Её песни успокаивают даже штормовые волны — и раны воинов.",
         look=dict(hair="#2aa6c9", skin="#e8c2a0", style=2, extra=None), mod=(1, 1, 1, 1),
         basic=sk("Тихая волна", "Лечит союзника с наименьшим здоровьем (если все целы — бьёт врага).", "allies_lowest", heal=0.9),
         ult=sk("Прилив", "Лечит всех союзников.", "all_allies", heal=0.9)),

    dict(key="tarn", name="Тарн Корнекрут", title="Страж древней рощи", rarity="rare", faction="grove", cls="tank",
         desc="Древний энт в обличье воина. Корни держат его крепче любых цепей.",
         look=dict(hair="#4c6b2a", skin="#a9835a", style=3, extra="scar"), mod=(1.05, 0.95, 1.05, 1),
         basic=sk("Удар корней", "Бьёт ближайшего врага, с шансом оглушить.", "front", dmg=0.9,
                  effects=[fx("stun", "hit", 1, 0, 0.2)]),
         ult=sk("Хватка леса", "Бьёт двух ближайших врагов, оглушает их и защищает себя щитом.", "front", n=2, dmg=1.2,
                effects=[fx("stun", "hit", 1, 0, 1.0), fx("shield", "self", 3, 0.2)])),
    dict(key="gromm", name="Громм Угольный", title="Кузнец войны", rarity="rare", faction="ember", cls="warrior",
         desc="Выковал свой молот из остывшей лавы. Говорят, молот всё ещё помнит жар.",
         look=dict(hair="#3a2a2a", skin="#c98a62", style=0, extra="beard"), mod=(1.05, 1.05, 1, 0.95),
         basic=sk("Тяжёлый удар", "Бьёт ближайшего врага.", "front", dmg=1.15),
         ult=sk("Раскалённый молот", "Мощный удар по ближайшему врагу с шансом оглушить.", "front", dmg=2.6,
                effects=[fx("stun", "hit", 1, 0, 0.7)])),
    dict(key="isel", name="Исель Звёздная Волна", title="Жрица лунных вод", rarity="rare", faction="tide", cls="mage",
         desc="Читает судьбу по отражениям звёзд в морской глади.",
         look=dict(hair="#8fe8ff", skin="#f0d2b8", style=1, extra=None), mod=(1, 1.05, 1, 1.05),
         basic=sk("Звёздный всплеск", "Бьёт двух случайных врагов.", "random", n=2, dmg=0.8),
         ult=sk("Лунный прилив", "Накрывает волной всех врагов.", "all_enemies", dmg=1.3)),
    dict(key="rein", name="Рейн Тень Клинка", title="Убийца Двора", rarity="rare", faction="dusk", cls="warrior",
         desc="Его имя знают лишь те, кто не успел о нём рассказать.",
         look=dict(hair="#1b1630", skin="#cfa07d", style=2, extra="mask"), mod=(0.9, 1.05, 0.9, 1.15),
         basic=sk("Удар в спину", "Атакует врага с наименьшим здоровьем.", "lowest", dmg=1.05),
         ult=sk("Танец теней", "Трижды атакует врагов с наименьшим здоровьем.", "lowest", n=3, dmg=1.25)),

    dict(key="seraphine", name="Серафина Ясный Свет", title="Верховная жрица", rarity="epic", faction="dawn", cls="support",
         desc="Её молитва — последний рассвет для павших союзников.",
         look=dict(hair="#fff0c0", skin="#f3d3b5", style=1, extra="crown"), mod=(1, 1, 1, 1),
         basic=sk("Луч надежды", "Лечит союзника с наименьшим здоровьем (если все целы — бьёт врага).", "allies_lowest", heal=1.0),
         ult=sk("Рассветный нимб", "Лечит всех союзников и усиливает их атаку на 3 хода.", "all_allies", heal=1.1,
                effects=[fx("atk_up", "allies", 3, 0.25)])),
    dict(key="ivara", name="Ивиара Шёпот Листвы", title="Ведьма Чащи", rarity="epic", faction="grove", cls="mage",
         desc="Лес отвечает на её шёпот. Иногда — слишком охотно.",
         look=dict(hair="#7ad46a", skin="#d8b08a", style=3, extra=None), mod=(1, 1, 1, 1),
         basic=sk("Ядовитый шип", "Бьёт случайного врага и отравляет его на 3 хода.", "random", dmg=1.0,
                  effects=[fx("burn", "hit", 3, 0.35)]),
         ult=sk("Цветение", "Поражает всех врагов и накладывает сильный яд на 3 хода.", "all_enemies", dmg=1.1,
                effects=[fx("burn", "hit", 3, 0.4)])),
    dict(key="drake", name="Дрейк Ржавый Волк", title="Охотник Легиона", rarity="epic", faction="ember", cls="marksman",
         desc="Не промахивается по контрактам. Только по друзьям.",
         look=dict(hair="#a34b1f", skin="#c89268", style=0, extra="scar"), mod=(1, 1, 1, 1),
         basic=sk("Бронебойный", "Стреляет во врага с наименьшим здоровьем.", "lowest", dmg=1.2),
         ult=sk("Охота на волка", "Огромный урон слабейшему врагу, +30% АТК на 3 хода.", "lowest", dmg=3.4,
                effects=[fx("atk_up", "self", 3, 0.3)])),
    dict(key="nero", name="Нэро Глубинный Страж", title="Страж подводных врат", rarity="epic", faction="tide", cls="tank",
         desc="Он стоял у врат, пока вода не поднялась. Он стоит и сейчас.",
         look=dict(hair="#1f4f6b", skin="#9fc7d1", style=2, extra="beard"), mod=(1, 1, 1.05, 1),
         basic=sk("Удар трезубцем", "Бьёт ближайшего врага и повышает свою защиту.", "front", dmg=0.9,
                  effects=[fx("def_up", "self", 2, 0.2)]),
         ult=sk("Приливная стена", "Накрывает союзников щитом и повышает их защиту на 3 хода.", "all_allies",
                effects=[fx("shield", "allies", 3, 0.15), fx("def_up", "allies", 3, 0.2)])),

    dict(key="alaric", name="Аларик Золотой Клинок", title="Лорд-командор Рассвета", rarity="legendary", faction="dawn", cls="warrior",
         desc="Последний командор павшего ордена. Его меч всё ещё помнит свет.",
         look=dict(hair="#f0d58a", skin="#ecc8a2", style=0, extra="crown"), mod=(1, 1, 1, 1),
         basic=sk("Рассекающий удар", "Бьёт двух ближайших врагов.", "front", n=2, dmg=0.9),
         ult=sk("Приговор Рассвета", "Обрушивает свет на всех врагов, +25% АТК на 3 хода.", "all_enemies", dmg=1.7,
                effects=[fx("atk_up", "self", 3, 0.25)])),
    dict(key="kaera", name="Каэра Пламя Пепла", title="Чародейка вулкана", rarity="legendary", faction="ember", cls="mage",
         desc="Родилась в кратере. Огонь — её единственный родной язык.",
         look=dict(hair="#ff5a2a", skin="#e3a47e", style=3, extra=None), mod=(1, 1, 1, 1),
         basic=sk("Огненный залп", "Бьёт двух случайных врагов и поджигает их на 2 хода.", "random", n=2, dmg=0.9,
                  effects=[fx("burn", "hit", 2, 0.25)]),
         ult=sk("Метеоритный дождь", "Сокрушает всех врагов и поджигает их на 3 хода.", "all_enemies", dmg=2.0,
                effects=[fx("burn", "hit", 3, 0.4)])),
    dict(key="morvena", name="Морвена Ночная Жрица", title="Хранительница лунного хора", rarity="legendary", faction="dusk", cls="support",
         desc="Её хор слышат на границе жизни и смерти — и возвращаются обратно.",
         look=dict(hair="#d9c2ff", skin="#e9d6e8", style=1, extra="crown"), mod=(1, 1, 1, 1),
         basic=sk("Лунная нить", "Лечит союзника с наименьшим здоровьем (если все целы — бьёт врага).", "allies_lowest", heal=1.1),
         ult=sk("Лунный хор", "Лечит всех союзников и даёт им 30 энергии.", "all_allies", heal=1.0,
                effects=[fx("energy", "allies", 0, 30)])),
    dict(key="nox", name="Нокс Пустотный", title="Стрелок Бездны", rarity="legendary", faction="dusk", cls="marksman",
         desc="Стрела, которую он выпускает, уже находится в вашем сердце.",
         look=dict(hair="#2b2150", skin="#bda7d9", style=2, extra="mask"), mod=(1, 1, 1, 1),
         basic=sk("Тёмная стрела", "Стреляет во врага с наименьшим здоровьем.", "lowest", dmg=1.3),
         ult=sk("Поцелуй пустоты", "Мощный урон двум слабейшим врагам и снижение их защиты.", "lowest", n=2, dmg=2.8,
                effects=[fx("def_down", "hit", 3, 0.3)])),
]


def _build_base(cls, rarity, mod):
    hp, atk, df, spd = CLASSES[cls]["base"]
    m = RARITIES[rarity]["mult"]
    return {"hp": round(hp * m * mod[0]), "atk": round(atk * m * mod[1]),
            "def": round(df * m * mod[2]), "spd": round(spd * mod[3])}


HEROES = {}
for _h in _HEROES:
    _h["base"] = _build_base(_h["cls"], _h["rarity"], _h.pop("mod"))
    HEROES[_h["key"]] = _h
HERO_ORDER = [h["key"] for h in _HEROES]

# ---------------------------------------------------------------- монстры кампании
MONSTERS = {
    "bonewarden": dict(key="bonewarden", name="Костяной страж", cls="tank", mod=(1.0, 1.0, 1.0, 1.0),
                       basic=sk("Костяной удар", "", "front", dmg=0.9),
                       ult=sk("Каменная кожа", "", "self", effects=[fx("shield", "self", 3, 0.15)])),
    "cavebrute": dict(key="cavebrute", name="Пещерный громила", cls="warrior", mod=(1.0, 1.0, 1.0, 1.0),
                      basic=sk("Дубина", "", "front", dmg=1.1),
                      ult=sk("Сокрушение", "", "front", dmg=2.2, effects=[fx("stun", "hit", 1, 0, 0.5)])),
    "whisperwitch": dict(key="whisperwitch", name="Ведьма шёпота", cls="mage", mod=(1.0, 1.0, 1.0, 1.0),
                         basic=sk("Порча", "", "random", dmg=0.9, effects=[fx("burn", "hit", 2, 0.25)]),
                         ult=sk("Проклятый хор", "", "all_enemies", dmg=1.1)),
    "rotarcher": dict(key="rotarcher", name="Гнильный лучник", cls="marksman", mod=(1.0, 1.0, 1.0, 1.0),
                      basic=sk("Гнилая стрела", "", "lowest", dmg=1.0),
                      ult=sk("Залп", "", "random", n=3, dmg=1.2)),
    "decaypriest": dict(key="decaypriest", name="Жрец тлена", cls="support", mod=(1.0, 1.0, 1.0, 1.0),
                        basic=sk("Касание тлена", "", "allies_lowest", heal=0.9),
                        ult=sk("Волна гнили", "", "all_allies", heal=0.8)),
}

CHAPTERS = [
    dict(id=1, name="Пепельные Холмы", desc="Дымящиеся равнины, где пробудились первые твари.",
         c1="#2a1a3a", c2="#7a3b2e", accent="#ff8a4a",
         boss=dict(key="boss1", name="Угольный Вожак", cls="warrior",
                   basic=sk("Крушение", "", "front", dmg=1.1),
                   ult=sk("Лавовая волна", "", "all_enemies", dmg=1.2, effects=[fx("burn", "hit", 2, 0.3)]))),
    dict(id=2, name="Шепчущий Лес", desc="Деревья здесь слушают. И повторяют.",
         c1="#0d2a2a", c2="#2f6b4f", accent="#5be3a1",
         boss=dict(key="boss2", name="Матерь Корней", cls="mage",
                   basic=sk("Шип", "", "random", dmg=1.0, effects=[fx("burn", "hit", 3, 0.3)]),
                   ult=sk("Лес пробуждается", "", "all_enemies", dmg=1.2, effects=[fx("stun", "hit", 1, 0, 0.4)]))),
    dict(id=3, name="Затонувший Храм", desc="Лунные воды скрывают тех, кто не должен просыпаться.",
         c1="#0a2238", c2="#1b6b8a", accent="#4fd8e8",
         boss=dict(key="boss3", name="Глубинная Горгона", cls="mage",
                   basic=sk("Взгляд", "", "lowest", dmg=1.1),
                   ult=sk("Окаменение", "", "all_enemies", dmg=1.4, effects=[fx("def_down", "hit", 2, 0.25)]))),
    dict(id=4, name="Костяные Копи", desc="Здесь добывали руду. Теперь — кости.",
         c1="#1d1d2b", c2="#58526b", accent="#c9c2e6",
         boss=dict(key="boss4", name="Король Костей", cls="tank",
                   basic=sk("Скипетр", "", "front", dmg=1.0),
                   ult=sk("Костяной трон", "", "front", n=2, dmg=1.8, effects=[fx("shield", "self", 3, 0.08)]))),
    dict(id=5, name="Багровые Шпили", desc="Башни, которые растут из земли, как клыки.",
         c1="#2b0f1f", c2="#8a2347", accent="#ff5c8a",
         boss=dict(key="boss5", name="Багровый Палач", cls="warrior",
                   basic=sk("Казнь", "", "lowest", dmg=1.1),
                   ult=sk("Кровавая жатва", "", "lowest", n=2, dmg=2.2))),
    dict(id=6, name="Врата Сумрака", desc="Конец дороги. Или её начало.",
         c1="#140d2e", c2="#4b2a8a", accent="#a98bff",
         boss=dict(key="boss6", name="Повелитель Сумрака", cls="mage",
                   basic=sk("Тёмный росчерк", "", "random", n=2, dmg=1.0, effects=[fx("def_down", "hit", 2, 0.2)]),
                   ult=sk("Затмение", "", "all_enemies", dmg=1.8, effects=[fx("burn", "hit", 3, 0.35)]))),
]
STAGES_PER_CHAPTER = 10
MAX_STAGE = STAGES_PER_CHAPTER * len(CHAPTERS)

# ---------------------------------------------------------------- ежедневные задания
QUESTS = [
    dict(id="q_win", name="Победить в 3 сражениях", target=3, reward={"gold": 2000, "exp": 1000}),
    dict(id="q_summon", name="Совершить призыв", target=1, reward={"gems": 40}),
    dict(id="q_upgrade", name="Улучшить героев 3 раза", target=3, reward={"gold": 1500, "tickets": 1}),
    dict(id="q_idle", name="Забрать idle-награды", target=1, reward={"exp": 1500}),
]
DAILY_GIFT = {"gold": 2000, "gems": 20, "tickets": 1}
DAILY_FULL_REWARD_WINS = 40   # после 40 побед за день награда за повторные бои режется до 25%

# ---------------------------------------------------------------- магазин
# kind: free | gems | premium. Премиум-позиции (Telegram Stars) пока недоступны.
SHOP = [
    dict(id="free_daily", cat="free", name="Ежедневный дар", desc="Бесплатный набор раз в сутки.", kind="free", give=DAILY_GIFT),
    dict(id="tickets_1", cat="tickets", name="Билет призыва", desc="1 билет призыва.", kind="gems", price=150, give={"tickets": 1}),
    dict(id="tickets_5", cat="tickets", name="5 билетов призыва", desc="Выгоднее на 7%.", kind="gems", price=700, give={"tickets": 5}),
    dict(id="gold_s", cat="gold", name="Мешок золота", desc="2 500 золота.", kind="gems", price=50, give={"gold": 2500}),
    dict(id="gold_m", cat="gold", name="Сундук золота", desc="12 500 золота.", kind="gems", price=220, give={"gold": 12500}),
    dict(id="gold_l", cat="gold", name="Казна гильдии", desc="25 000 золота.", kind="gems", price=400, give={"gold": 25000}),
    dict(id="exp_s", cat="supplies", name="Свиток опыта", desc="2 000 опыта героев.", kind="gems", price=50, give={"exp": 2000}),
    dict(id="exp_m", cat="supplies", name="Том знаний", desc="10 000 опыта героев.", kind="gems", price=220, give={"exp": 10000}),
    dict(id="frame_gold", cat="cosmetic", name="Золотая рамка", desc="Рамка профиля.", kind="gems", price=300, frame="gold"),
    dict(id="frame_arcane", cat="cosmetic", name="Чародейская рамка", desc="Рамка профиля.", kind="gems", price=450, frame="arcane"),
    dict(id="frame_ember", cat="cosmetic", name="Пепельная рамка", desc="Рамка профиля.", kind="gems", price=450, frame="ember"),
    dict(id="stars_gems", cat="premium", name="Горсть самоцветов", desc="500 самоцветов. Фиксированный набор.", kind="premium", stars=50, give={"gems": 500}),
    dict(id="stars_pack", cat="premium", name="Набор странника", desc="1 000 самоцветов и 5 билетов.", kind="premium", stars=100, give={"gems": 1000, "tickets": 5}),
    dict(id="stars_frame", cat="premium", name="Рамка «Звёздный двор»", desc="Эксклюзивная косметика.", kind="premium", stars=75, frame="stardust"),
]
FRAMES = ["none", "gold", "arcane", "ember", "stardust"]
