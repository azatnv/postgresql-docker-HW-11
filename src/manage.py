from sqlalchemy import create_engine, Table, ForeignKey, Column, Integer, String, DateTime, select, MetaData, UniqueConstraint
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from datetime import date, datetime
from sqlalchemy import func, or_
from random import randrange, sample
from pandas import DataFrame
import os
import sys
import logging

logging.basicConfig(
    datefmt = "%Y-%m-%d %H:%M:%S",
    format = "%(asctime)s.%(msecs)03d | %(levelname)s | %(message)s",
    level = logging.DEBUG
)
formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

file_handler = logging.FileHandler(filename = "logs.txt", encoding = "utf-8")
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(formatter)

root = logging.getLogger("")
root.addHandler(file_handler)
root.addHandler(console_handler)

class WinnerFilter(logging.Filter):
    def filter(self, record):
        return not record.getMessage().endswith("(winner)=(0)")

root_filter = WinnerFilter()
root.addFilter(root_filter)

DATABASE_URL = os.environ['DATABASE_URL']

Base = declarative_base()
engine, meta = create_engine(DATABASE_URL), Base.metadata
meta.reflect(bind=engine)

def add_hero(hname, hside, hbirthday):
    root.debug("add_hero(name=%s, side=%s, birthday=%s)", hname, hside, hbirthday)
    hero = meta.tables['hero']
    if isinstance(hbirthday, str):
        try:
            hbirthday = datetime.strptime(hbirthday, '%d.%m.%Y')
        except ValueError:
            root.error("ValueError: time data ''%s' does not match format 'day.month.year'", hbirthday)
            raise
    with engine.connect() as conn:
        try:
            conn.execute(hero.insert().values(
                name = hname, 
                side = hside, 
                birthday = hbirthday
            ))
            root.info("Hero have added: (name)=(%s), (side)=(%s), (birthday)=(%s)", hname, hside, hbirthday)
        except Exception:
            root.error("UniqueViolation: Key (name)=(%s) already exists!", hname)

def add_slogan(hname, hmoto):
    root.debug("add_slogan(name=%s, moto=%s)", hname, hmoto)
    hero = meta.tables['hero']
    slogan = meta.tables['slogan']

    with engine.connect() as conn:
        query_hero = hero.select().where(hero.c.name == hname)
        try:
            this_hero = conn.execute(query_hero).one()
        except Exception:
            root.error("There is no such hero (name)=(%s)", hname)
            raise
        
        query_slogan = select(func.max(slogan.c.moto_id)).select_from(
            slogan.join(hero, slogan.c.hero_id == hero.c.hero_id)
        ).where(
            hero.c.name == hname
        )
        
        last_moto_id = conn.execute(query_slogan).scalar()
        new_moto_id = 1
        if last_moto_id:
            new_moto_id = last_moto_id + 1
        
        try:
            conn.execute(slogan.insert().values(
                hero_id = this_hero.hero_id, 
                moto_id = new_moto_id, 
                moto = hmoto
            ))
            root.info("Slogan have created: (name)=(%s), (moto)=(%s)", hname, hmoto)
        except Exception:
            root.error("UniqueViolation: Key (moto)=(%s) already exists!", hmoto)

def add_clash():
    root.debug("add_clash()")
    hero = meta.tables['hero']
    clash = meta.tables['clash']
    slogan = meta.tables['slogan']
    with engine.connect() as conn:
        query_hero_sides = select(hero.c.side).group_by(hero.c.side)
        df_sides = DataFrame(conn.execute(query_hero_sides).all())['side']
        
        try:
            side_1, side_2 = df_sides.take(sample(range(len(df_sides.index)), 2))
        except Exception:
            root.error("There are not enough opposing sides (%s) in the Data Base to make a clash!", df_sides)
            raise
        
        query_heroes = hero.select().where(or_(hero.c.side == side_1, hero.c.side == side_2))
        df_heroes = DataFrame(conn.execute(query_heroes))
        heroes_1 = df_heroes[df_heroes['side'] == side_1]
        heroes_2 = df_heroes[df_heroes['side'] == side_2]
        
        h_1_id = heroes_1.iloc[randrange(len(heroes_1.index))].loc['hero_id']
        h_2_id = heroes_2.iloc[randrange(len(heroes_2.index))].loc['hero_id']
        
        query_slogans = select([slogan.c.slogan_id, slogan.c.hero_id]).select_from(slogan)
        df_slogans = DataFrame(conn.execute(query_slogans))
        slogans_1 = df_slogans[df_slogans['hero_id'] == h_1_id]
        slogans_2 = df_slogans[df_slogans['hero_id'] == h_2_id]
        
        s_1_id = slogans_1.iloc[randrange(len(slogans_1.index))].loc['slogan_id']
        s_2_id = slogans_2.iloc[randrange(len(slogans_2.index))].loc['slogan_id']
        
        win = randrange(3)
        
        conn.execute(clash.insert().values(
            hero_1_id = int(h_1_id), 
            hero_1_slogan_id = int(s_1_id), 
            hero_2_id = int(h_2_id),
            hero_2_slogan_id = int(s_2_id),
            winner = win
        ))
        root.info("Clash have created: (hero_1_id)=(%s), (hero_2_id)=(%s), (winner)=(%s)", h_1_id, h_2_id, win)

def add_story_to_hero(hname, hstory):
    root.debug("add_story_to_hero(name=%s, story=%s)", hname, hstory)
    hero = meta.tables['hero']
    story = meta.tables['story']
    with engine.connect() as conn:
        query_hero = hero.select().where(hero.c.name == hname)
        try:
            this_hero = conn.execute(query_hero).one_or_none()
        except Exception:
            root.critical("Multiple heroes are returned!")
            raise
        if this_hero:
            conn.execute(story.insert().values(
                hero_id = this_hero.hero_id, 
                story = hstory
            ))
            root.info("Story have added: (name)=(%s), (story)=(%s)", hname, hstory)
        else:
            root.info("There is no such hero (name)=(%s) to add story", hname)

def delete_hero(hname):
    root.debug("delete_hero(name=%s)", hname)
    hero = meta.tables['hero']
    session = sessionmaker(bind = engine)
    with session() as sess:
        sess.query(hero).filter(hero.c.name == hname).delete()
        sess.commit()

def create_db():
    meta.drop_all(engine)

    class Hero(Base):
        __tablename__ = 'hero'
        __table_args__ = (UniqueConstraint('name'), {'extend_existing':True},)

        hero_id = Column(Integer, primary_key = True)
        name = Column(String(20), nullable = False)
        side = Column(String(20), nullable = False)
        birthday = Column(DateTime(timezone = True), nullable = False)
        
        slogans = relationship(
            "Slogan", back_populates="heroes",
            passive_deletes = 'all'
        )
        clashes = relationship("Clash", back_populates="heroes")
        stories = relationship(
            "Story", back_populates="heroes", uselist=False,
            passive_deletes = 'all'
        )
    
    class Slogan(Base):
        __tablename__ = 'slogan'
        __table_args__ = (UniqueConstraint('moto'),{'extend_existing':True},)

        slogan_id = Column(Integer, primary_key = True)
        hero_id = Column(Integer, ForeignKey('hero.hero_id', ondelete="CASCADE"))
        moto_id = Column(Integer, nullable = False)
        moto = Column(String(200), nullable = False)

        heroes = relationship("Hero", back_populates="slogans")
        clashes = relationship("Clash", back_populates="slogans")
        
    
    class Clash(Base):
        __tablename__ = 'clash'
        __table_args__ = {'extend_existing':True}

        clash_id = Column(Integer, primary_key = True)
        hero_1_id = Column(Integer, ForeignKey('hero.hero_id', ondelete="set null"))
        hero_1_slogan_id = Column(Integer, ForeignKey('slogan.slogan_id', ondelete="set null"))
        hero_2_id = Column(Integer, ForeignKey('hero.hero_id', ondelete="set null"))
        hero_2_slogan_id = Column(Integer, ForeignKey('slogan.slogan_id', ondelete="set null"))
        winner = Column(Integer, nullable = False) 

        heroes = relationship("Hero", back_populates="clashes")
        slogans = relationship("Slogan", back_populates="clashes")

    class Story(Base):
        __tablename__ = 'story'
        __table_args__ = (UniqueConstraint('hero_id', 'story'),{'extend_existing':True},)

        story_id = Column(Integer, primary_key = True)
        hero_id = Column(Integer, ForeignKey('hero.hero_id', ondelete="CASCADE"))
        story = Column(String(500), nullable = False)
        
        heroes = relationship("Hero", back_populates="stories")
    
    meta.create_all(engine)
    root.info("A new DB have created")

def seed_db():
    add_hero('Троцкий', 'красный', date(1879, 11, 7))
    add_hero('Ленин', 'красный', date(1870, 4, 22))
    add_hero('Чапаев', 'красный', date(1887, 1, 28))
    add_hero('Тухачевский', 'красный', date(1893, 2, 16))
    add_hero('Дзержинский', 'красный', date(1877, 9, 11))  
    add_hero('Деникин', 'белый', date(1872, 12, 16))   
    add_hero('Врангель', 'белый', date(1878, 8, 27))
    add_hero('Юденич', 'белый', date(1862, 7, 30))
    
    add_slogan('Троцкий', 'Революционеры сделаны в последнем счете из того же общественного материала, что и другие люди.')
    add_slogan('Троцкий', 'Сталинизм – сгусток всех уродств исторического государства, его зловещая карикатура и отвратительная гримаса.')
    add_slogan('Троцкий', 'Cимволика рабочего государства: красное знамя, серп и молот, красная звезда, рабочий и крестьянин, товарищ, интернационал.')
    add_slogan('Ленин', 'Мы пойдём другим путём')
    add_slogan('Ленин', 'Каждая кухарка должна научиться управлять государством') 
    add_slogan('Ленин', 'Из всех искусств для нас важнейшим является кино') 
    add_slogan('Ленин', 'Учиться, учиться и учиться') 
    add_slogan('Ленин', 'На деле это не мозг, а говно» (о буржуазных интеллигентах') 
    add_slogan('Чапаев', 'Умного учить – только портить.')
    add_slogan('Чапаев', 'Будешь смелым, духом не будешь падать – всегда своего добьёшься.')
    add_slogan('Тухачевский', 'Вперед на Берлин')
    add_slogan('Тухачевский', 'Вперед на Варшаву')
    add_slogan('Дзержинский', 'Жертвуя собой, помогай другим!')
    add_slogan('Деникин', 'Великая, Единая и Неделимая Россия')
    add_slogan('Деникин', 'Русский не тот, кто носит русскую фамилию, а тот, кто любит Россию и считает ее своим отечеством.')
    add_slogan('Деникин', 'Дайте народу грамоту и облик человеческий, а потом социализируйте, национализируйте, коммунизируйте, если… если тогда народ пойдёт за вами.')
    add_slogan('Врангель', 'Не вычеркнуть из русской истории темных страниц настоящей смуты. Не вычеркнуть и светлых белой борьбы')  
    add_slogan('Врангель', 'Верю, что настанет время, и Русская армия, сильная духом своих офицеров и солдат, возрастая, как снежный ком, покатится по родной земле, освобождая её от извергов, не знающих Бога и Отечества.')  
    add_slogan('Юденич', 'Россия - единая и неделимая')
    add_slogan('Юденич', 'Бей красных, пока не побелеют, бей белых, пока не покраснеют')
    
    add_clash(), add_clash(), add_clash(), add_clash(), add_clash(), add_clash(), add_clash(), add_clash()
    add_clash(), add_clash(), add_clash(), add_clash(), add_clash(), add_clash(), add_clash(), add_clash()
    
    add_story_to_hero('Ленин','Российский революционер, крупный теоретик марксизма, советский политический и государственный деятель, создатель Российской социал-демократической рабочей партии (большевиков), главный организатор и руководитель Октябрьской революции 1917 года в России, первый председатель Совета народных комиссаров РСФСР и Совета народных комиссаров СССР, создатель первого в мировой истории социалистического государства.')
    add_story_to_hero('Троцкий','Российский революционер, активный участник российского и международного социалистического и коммунистического движения, советский государственный, партийный и военно-политический деятель, основатель и идеолог троцкизма.')
    add_story_to_hero('Чапаев','Участник Первой мировой и Гражданской войн, начальник дивизии Красной армии. Был и остаётся одной из самых известных исторических личностей эпохи Гражданской войны в России. Увековечен в книге Дмитрия Фурманова «Чапаев» и одноимённом фильме братьев Васильевых, а также в многочисленных анекдотах.')
    add_story_to_hero('Тухачевский','Советский военный деятель, военачальник РККА времён Гражданской войны. Военный теоретик, Маршал Советского Союза. Расстрелян в 1937 году по «делу антисоветской троцкистской военной организации», реабилитирован в 1957 году.')
    add_story_to_hero('Дзержинский','Российский и польский революционер, советский государственный и партийный деятель. Глава ряда народных комиссариатов, основатель и руководитель ВЧК')
    add_story_to_hero('Деникин','Русский военачальник, генерал-лейтенант, публицист, политический и общественный деятель, писатель, мемуарист, военный документалист. Участник Русско-японской войны.')
    add_story_to_hero('Врангель','Русский военачальник, участник Русско-японской и Первой мировой войн, один из главных руководителей Белого движения в годы Гражданской войны. Главнокомандующий Русской армией в Крыму и Польше. Генерального штаба генерал-лейтенант.')
    add_story_to_hero('Юденич','Русский военный деятель, генерал от инфантерии. Один из самых видных генералов Российской империи во время Первой мировой войны, «мастер импровизации». Во время Гражданской войны возглавлял силы, действовавшие против большевиков на Северо-Западе. Последний российский кавалер ордена св. Георгия II степени. ')
    
    root.info("The DB is filled with TEST DATA")


if __name__ == "__main__":
    AZAT_ENV = os.environ['AZAT_ENV']

    opts = [opt for opt in sys.argv[1:]]
    function_name = opts[0]

    match function_name:
        case 'create_db':
            create_db()
            print('\nA new database has been created.')
        case 'seed_db':
            seed_db()
            print('\nDatabase is filled with TEST DATA.')
        case 'addhero':
            if len(opts) != 4:
                print(f'wrong arguments length {len(opts)}, expected {4}')
                sys.exit(1)
            name = opts[1]
            side = opts[2]
            birthday = opts[3]
            add_hero(name, side, birthday)
        case 'addslogan':
            if len(opts) != 3:
                print(f'wrong arguments length {len(opts)}, expected {3}')
                sys.exit(1)
            name = opts[1]
            moto = opts[2]
            add_slogan(name, moto)
        case 'addclash':
            if len(opts) != 1:
                print(f'wrong arguments length {len(opts)}, expected {1}')
                sys.exit(1)
            add_clash()
        case 'addstory':
            if len(opts) != 3:
                print(f'wrong arguments length {len(opts)}, expected {3}')
                sys.exit(1)
            name = opts[1]
            story = opts[2]
            add_story_to_hero(name, story)
        case 'deletehero':
            if len(opts) != 2:
                print(f'wrong arguments length {len(opts)}, expected {2}')
                sys.exit(1)
            name = opts[1]
            delete_hero(name)
        case _:
            print('Nothing happened.')

    for handler in root.handlers:
        handler.close()
        root.removeHandler(handler)