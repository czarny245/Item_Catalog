from flask import jsonify, Blueprint
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, WebCategory, WebPage
import json

mod = Blueprint('api', __name__)

CLIENT_ID = json.loads(
    open('client_secret.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "ItemCatalog"

# Connect to the database and make session
engine = create_engine('sqlite:///webPages.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# JSON endpoints
# return info for a category and its items
@mod.route('/showPages/<int:webCategory_id>/JSON')
def showPagesJSON(webCategory_id):
    webCategory = session.query(
        WebCategory).filter_by(id=webCategory_id).one()
    pages = session.query(
        WebPage).filter_by(category_id=webCategory.id).all()
    return jsonify(WebPages=[page.serialize for page in pages])


# return info about single item
@mod.route('/showPages/<int:webCategory_id>/showDetails/<int:page_id>/JSON')
def pageDetailsJSON(webCategory_id, page_id):
    page = session.query(WebPage).filter_by(id=page_id).one()
    return jsonify(WebPage=page.serialize)
