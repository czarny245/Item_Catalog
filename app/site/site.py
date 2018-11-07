from flask import (render_template,
                   request,
                   redirect,
                   url_for,
                   flash,
                   session as login_session,
                   Blueprint)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, WebCategory, WebPage, User
import json
from user_dao import getUserID, getUserInfo

mod = Blueprint('site', __name__)

CLIENT_ID = json.loads(
    open('client_secret.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "ItemCatalog"

# Connect to the database and make session
engine = create_engine('sqlite:///webPages.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# endpoints
@mod.route('/')
@mod.route('/index')
def getAllWebCategories():
    webCategories = session.query(WebCategory).all()
    if 'username' in login_session:
        user_id = getUserID(login_session['email'])
        user = getUserInfo(user_id)
    else:
        user = None
    return render_template(
        'index.html', webCategories=webCategories,
        user=user)


@mod.route('/newCategory', methods=['POST', 'GET'])
def newCategory():
    webCategories = session.query(WebCategory).all()
    if 'username' in login_session:
        user_id = getUserID(login_session['email'])
        user = getUserInfo(user_id)
    else:
        user = None
        return render_template('noAccess.html')
    if request.method == 'POST':
        if request.form['name'] == "":
            flash("You cannot create a category without a name!")
            return redirect(url_for('site.getAllWebCategories'))
        else:
            newCat = WebCategory(name=request.form['name'], creator_id=user_id)
            session.add(newCat)
            session.commit()
            flash("New category added!")
            return redirect(url_for('site.getAllWebCategories'))
    else:
        return render_template('newWebCategory.html',
                               user=user, webCategories=webCategories)


@mod.route('/showPages/<int:webCategory_id>/edit', methods=['GET', 'POST'])
def editCategory(webCategory_id):
    webCategories = session.query(WebCategory).all()
    if 'username' in login_session:
        user_id = getUserID(login_session['email'])
        user = getUserInfo(user_id)
    else:
        user = None
        return render_template('noAccess.html')
    editedCat = session.query(WebCategory).filter_by(id=webCategory_id).one()
    creator = getUserInfo(editedCat.creator_id)
    if login_session['user_id'] != creator.id:
        flash("You can only modify your own category")
        return redirect(url_for('site.getAllWebCategories'))
    if request.method == 'POST':
        editedCat.name = request.form['name']
        session.add(editedCat)
        session.commit()
        flash("You have succesfully edited this category")
        return redirect(url_for('site.getAllWebCategories'))
    else:
        return render_template('editWebCategory.html',
                               webCategory=editedCat,
                               user=user,
                               webCategories=webCategories)


@mod.route('/showPages/<int:webCategory_id>/delete', methods=['GET', 'POST'])
def deleteCategory(webCategory_id):
    webCategories = session.query(WebCategory).all()
    if 'username' in login_session:
        user_id = getUserID(login_session['email'])
        user = getUserInfo(user_id)
    else:
        user = None
        return render_template('noAccess.html')
    catToDel = session.query(WebCategory).filter_by(id=webCategory_id).one()
    webCategories = session.query(WebCategory).all()
    creator = getUserInfo(catToDel.creator_id)
    if login_session['user_id'] != creator.id:
        flash("You can only modify your own category")
        return redirect(url_for('site.getAllWebCategories'))
    if request.method == 'POST':
        session.delete(catToDel)
        session.commit()
        flash('Category removed')
        return redirect(
            url_for('site.getAllWebCategories'))
    else:
        return render_template(
            'deleteWebCategory.html', webCategory=catToDel,
            webCategories=webCategories, user=user)


@mod.route('/showPages/<int:webCategory_id>')
def showPages(webCategory_id):
    webCategories = session.query(WebCategory).all()
    if 'username' in login_session:
        user_id = getUserID(login_session['email'])
        user = getUserInfo(user_id)
    else:
        user = None
    webCategories = session.query(WebCategory).all()
    webCategory = session.query(WebCategory).filter_by(
        id=webCategory_id).one()
    creator = session.query(User).filter_by(id=webCategory.creator_id).one()
    getAllPages = session.query(
        WebPage).filter_by(category_id=webCategory.id)
    return render_template(
        'showPages.html',
        webCategories=webCategories,
        webCategory=webCategory,
        getAllPages=getAllPages,
        user=user,
        creator=creator)


@mod.route('/showPages/<int:webCategory_id>/showDetails/<int:page_id>')
def showPageDetails(webCategory_id, page_id):
    webCategories = session.query(WebCategory).all()
    webCategory = session.query(
        WebCategory).filter_by(id=webCategory_id).one()
    if 'username' in login_session:
        user_id = getUserID(login_session['email'])
        user = getUserInfo(user_id)
    else:
        user = None
    page = session.query(WebPage).filter_by(id=page_id).one()
    return render_template('pageDetails.html',
                           page=page, user=user,
                           webCategory=webCategory,
                           webCategories=webCategories)


@mod.route('/showPages/<int:webCategory_id>/new', methods=['GET', 'POST'])
def addNewPage(webCategory_id):
    webCategories = session.query(WebCategory).all()
    if 'username' in login_session:
        user_id = getUserID(login_session['email'])
        user = getUserInfo(user_id)
    else:
        user = None
        return render_template('noAccess.html')
    webCategory = session.query(
        WebCategory).filter_by(id=webCategory_id).one()
    creator = getUserInfo(webCategory.creator_id)
    if login_session['user_id'] != creator.id:
        flash("You can only modify your own category")
        return redirect(url_for('site.getAllWebCategories'))
    if request.method == 'POST':
        newPage = WebPage(
            name=request.form['name'],
            description=request.form['description'],
            link=request.form['link'],
            image=request.form['image'],
            category_id=webCategory.id)
        session.add(newPage)
        session.commit()
        return redirect(url_for(
            'site.showPages', webCategory_id=webCategory_id))
        flash("New link added")
    else:
        return render_template(
            'newWebPage.html',
            webCategory_id=webCategory_id,
            user=user,
            webCategories=webCategories)


@mod.route('/showPages/<int:webCategory_id>/editWebPage/<int:page_id>',
           methods=['GET', 'POST'])
def editWebPage(webCategory_id, page_id):
    webCategories = session.query(WebCategory).all()
    webCategory = session.query(WebCategory).filter_by(id=webCategory_id).one()
    if 'username' in login_session:
        user_id = getUserID(login_session['email'])
        user = getUserInfo(user_id)
    else:
        user = None
        return render_template('noAccess.html')
    editedPage = session.query(WebPage).filter_by(id=page_id).one()
    creator = getUserInfo(webCategory.creator_id)
    if login_session['user_id'] != creator.id:
        flash("You can only modify your own category")
        return redirect(url_for('site.getAllWebCategories'))
    if request.method == 'POST':
        if request.form['name']:
            editedPage.name = request.form['name']
        if request.form['link']:
            editedPage.link = request.form['link']
        if request.form['description']:
            editedPage.description = request.form['description']
        if request.form['image']:
            editedPage.image = request.form['image']
        session.add(editedPage)
        session.commit()
        return redirect(url_for('site.showPages',
                                webCategory_id=webCategory_id))
        flash("Web site changed")
    else:
        return render_template(
            'editWebPage.html',
            webCategory_id=webCategory_id,
            page_id=page_id,
            page=editedPage,
            user=user,
            webCategories=webCategories)


@mod.route('/showPages/<int:webCategory_id>/deleteWebPage/<int:page_id>',
           methods=['GET', 'POST'])
def deleteWebPage(webCategory_id, page_id):
    webCategories = session.query(WebCategory).all()
    webCategory = session.query(WebCategory).filter_by(id=webCategory_id).one()
    if 'username' in login_session:
        user_id = getUserID(login_session['email'])
        user = getUserInfo(user_id)
    else:
        user = None
        return render_template('noAccess.html')
    pageToDel = session.query(WebPage).filter_by(id=page_id).one()
    creator = getUserInfo(webCategory.creator_id)
    if login_session['user_id'] != creator.id:
        flash("You can only modify your own category")
        return redirect(url_for('site.getAllWebCategories'))
    if request.method == 'POST':
        session.delete(pageToDel)
        session.commit()
        return redirect(url_for('site.showPages',
                                webCategory_id=webCategory_id))
        flash("link has been removed")
    else:
        return render_template(
            'deleteWebPage.html',
            webCategories=webCategories,
            webCategory_id=webCategory_id,
            page_id=page_id,
            page=pageToDel,
            user=user,)
