import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))


class WebCategory(Base):
    __tablename__ = 'webCategory'

    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)

    @property
    def serialize(self):
        #Returns objects data in easably serializeable format
        return {
            'name' : self.name,
            'id' : self.id,
            }

class WebPage(Base):
    __tablename__ = 'webPage'

    name = Column(String(80), nullable = False)
    id = Column(Integer, primary_key = True)
    link = Column(String(80), nullable = False)
    description = Column(String(250))
    image = Column(String(250))
    category_id = Column(Integer, ForeignKey('webCategory.id'))
    category = relationship(WebCategory)

    @property
    def serialize(self):
        return {
            'name' : self.name,
            'id' : self.id,
            'link' : self.link,
            'description' : self.description,
            'image' : self.image,
            'category_id' : self.category_id,
        }


engine = create_engine('sqlite:///webPages.db')


Base.metadata.create_all(engine)
