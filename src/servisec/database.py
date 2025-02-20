from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from contextlib import contextmanager


Base = declarative_base()

class DatabaseService:
    '''Сервис для работы с БД'''

    def __init__(self, database_url):
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def create_tables(self):
        '''Создание всех таблиц в БД'''
        Base.metadata.create_all(self.engine)
    
    @contextmanager
    def get_session(self):
        '''Контекстный менеджер для работы с БД'''
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

#Создание таблиц при запуске
def init_db(database_url):
    db_service = DatabaseService(database_url)
    db_service.create_tables()
    return db_service