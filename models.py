from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    __tablename__ = 'User'
    id = Column(Integer, primary_key=True, autoincrement=True, unique=True, nullable=False)
    name = Column(String, index=True, unique=True, nullable=False)
    email = Column(String, nullable=False)
    password = Column(String, nullable=False)
    api_key = Column(String, nullable=True, unique=True)

    reps = relationship('Repository', backref='user')

class Repository(Base):
    __tablename__ = 'Repository'
    id = Column(Integer, primary_key=True, autoincrement=True, unique=True, nullable=False)
    view_name = Column(String, index=True, nullable=False)
    name = Column(String, index=True, unique=True, nullable=False)
    link = Column(Text, unique=True, nullable=False)
    user_api_key = Column(String, ForeignKey('User.api_key'))

    files = relationship('File', backref='repository')


class File(Base):
    __tablename__ = 'File'
    id = Column(Integer, primary_key=True, autoincrement=True, unique=True, nullable=False)
    view_name = Column(String, index=True, nullable=False)
    name = Column(String, index=True, unique=True, nullable=False)
    download_link = Column(Text, unique=True, nullable=False)
    rep_id = Column(Integer, ForeignKey('Repository.id'))