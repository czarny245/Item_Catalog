
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import WebCategory, Base, WebPage

engine = create_engine('sqlite:///webPages.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


# Menu for UrbanBurger
restaurant1 = WebCategory(name="Porn")

session.add(restaurant1)
session.commit()

menuItem2 = WebPage(name="Veggie Burger", category_id = restaurant1.id,
                     category=restaurant1)

session.add(menuItem2)
session.commit()

def getAllPages(webCategory_id):
    pages = session.query(WebPage).filter_by(category_id = webCategory_id)
    return jsonify(pages = pages.serialize)


