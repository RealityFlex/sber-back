import time
from datetime import datetime
import os
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, create_engine, ForeignKeyConstraint, \
    UniqueConstraint, exc, and_, desc, Boolean
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
import uuid
from sqlalchemy.dialects.postgresql import UUID

Base = declarative_base()

docker_ip = "62.109.8.64"
docker_port = 9559

class User(Base):
    __tablename__ = 'user'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    username = Column(String(100), nullable=False, default=None)
    token_password = Column(String(100), nullable=False, default=None)
    register_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    img_url = Column(String(100), default=None)

    configurations = relationship('Configuration', back_populates='owner')

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

# Определение модели конфигурации
class Configuration(Base):
    __tablename__ = 'configurations'

    config_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    user_id = Column(UUID, ForeignKey('user.id'), nullable=False)
    config_data = Column(JSON, nullable=False)
    create_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    owner = relationship('User', back_populates='configurations')
    distribution_url = Column(String(100), default=None)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


engine = create_engine(f"postgresql+psycopg2://lct_guest:postgres@{docker_ip}:{docker_port}/lct_user_db")

Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine)

def add_new_user(username: str, token_password: str, img_url: str = None):
    session = Session()
    user = User(username=username, register_at=datetime.now(), img_url=img_url, token_password=token_password)
    session.add(user)
    session.commit()
    session.close()

# Функция для получения пользователя по имени пользователя
def get_user(username: str):
    session = Session(expire_on_commit=False)
    user = session.query(User).filter(User.username == username).first()
    session.close()
    if user is None:
        return None
    return user

# Функция для добавления новой конфигурации
def add_new_configuration(username: str, config_data: dict):
    session = Session()
    user = session.query(User).filter(User.username == username).first()
    config = Configuration(user_id=user.id, config_data=config_data)
    session.add(config)
    session.commit()
    res = config.as_dict()
    session.close()
    return res

# Функция для получения всех конфигураций пользователя по user_id
def get_user_configurations(username: str):
    session = Session(expire_on_commit=False)
    user = session.query(User).filter(User.username == username).first()
    configurations = session.query(Configuration).filter(Configuration.user_id == user.id).all()
    session.close()
    return configurations

def get_user_configuration(config_id: str):
    session = Session(expire_on_commit=False)
    configurations = session.query(Configuration).filter(Configuration.config_id == config_id).first()
    session.close()
    return configurations
