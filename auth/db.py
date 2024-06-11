import time
from datetime import datetime
import os
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, create_engine, ForeignKeyConstraint, \
    UniqueConstraint, exc, and_, desc, Boolean
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()

docker_ip = "62.109.8.64"
docker_port = 9559

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True, autoincrement=True)
    # token = Column(String(100), unique=True, nullable=False)
    username = Column(String(100), nullable=False, default=None)
    token_password = Column(String(100), nullable=False, default=None)
    register_at = Column(DateTime, nullable=False, default=None)
    img_url = Column(String(100), default=None)
    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

engine = create_engine(f"postgresql+psycopg2://lct_guest:postgres@{docker_ip}:{docker_port}/lct_user_db")

Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine)

def add_new_user(username: str, token_password: str, img_url:str = None):
    session = Session()
    scene = User(username=username, register_at=datetime.now(), img_url=img_url, token_password=token_password)
    session.add(scene)
    session.commit()


def get_user(username:str):
    session = Session(expire_on_commit=False)
    user = session.query(User).filter(User.username == username).first()
    if user is None:
        return None
    return user