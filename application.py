from flask import (Flask,
                   render_template,
                   request,
                   redirect,
                   url_for,
                   flash,
                   jsonify,
                   make_response,
                   session as login_session)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, WebCategory, WebPage, User
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
import requests
import random
import string
from functools import wraps
from user_dao import createUser, getUserID, getUserInfo

app = Flask(__name__)
CLIENT_ID = json.loads(
    open('client_secret.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "ItemCatalog"

# Connect to the database and make session
engine = create_engine('sqlite:///webPages.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create token
@app.route('/login')
def showLogin():
    state = ''.join(
        random.choice(
            string.ascii_uppercase + string.digits) for x in range(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


# google login api
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate the token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Get authorization code
    request.get_data()
    code = request.data.decode('utf-8')

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secret.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    # Submit request, parse response - Python3 compatible
    h = httplib2.Http()
    response = h.request(url, 'GET')[1]
    str_response = response.decode('utf-8')
    result = json.loads(str_response)

    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Check if the user is already connected
    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-\
        webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    return output


# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
        # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        # Reset the user's sesson.
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# endpoints
@app.route('/')
@app.route('/index')
def getAllWebCategories():
    webCategories = session.query(WebCategory).all()
    if 'username' in login_session:
        user_id = getUserID(login_session['email'])
        user = session.query(User).filter_by(id=user_id).one()
    else:
        user = None
    return render_template(
        'index.html', webCategories=webCategories,
        user=user)


@app.route('/newCategory', methods=['POST', 'GET'])
def newCategory():
    webCategories = session.query(WebCategory).all()
    if 'username' in login_session:
        user_id = getUserID(login_session['email'])
        user = getUserInfo(user_id)
    else:
        user = None
        return render_template('noAccess.html')
    if request.method == 'POST':
        newCat = WebCategory(name=request.form['name'],
                             creator_id=user_id)
        session.add(newCat)
        session.commit()
        return redirect(url_for('getAllWebCategories'))
        flash("New category added!")
    else:
        return render_template('newWebCategory.html',
                               user=user, webCategories=webCategories)


@app.route('/showPages/<int:webCategory_id>/edit', methods=['GET', 'POST'])
def editCategory(webCategory_id):
    webCategories = session.query(WebCategory).all()
    if 'username' in login_session:
        user_id = getUserID(login_session['email'])
        user = session.query(User).filter_by(id=user_id).one()
    else:
        user = None
    editedCat = session.query(WebCategory).filter_by(id=webCategory_id).one()
    if 'username' not in login_session:
        return render_template('noAccess.html')
    if request.method == 'POST':
        editedCat.name = request.form['name']
        session.add(editedCat)
        session.commit()
        flash("You have succesfully edited this category")
        return redirect(url_for('getAllWebCategories'))
    else:
        return render_template('editWebCategory.html',
                               webCategory=editedCat,
                               user=user,
                               webCategories=webCategories)


@app.route('/showPages/<int:webCategory_id>/delete', methods=['GET', 'POST'])
def deleteCategory(webCategory_id):
    webCategories = session.query(WebCategory).all()
    if 'username' in login_session:
        user_id = getUserID(login_session['email'])
        user = session.query(User).filter_by(id=user_id).one()
    else:
        user = None
    catToDel = session.query(WebCategory).filter_by(id=webCategory_id).one()
    webCategories = session.query(WebCategory).all()
    if 'username' not in login_session:
        return render_template('noAccess.html')
    if request.method == 'POST':
        session.delete(catToDel)
        session.commit()
        flash('Category removed')
        return redirect(
            url_for('getAllWebCategories'))
    else:
        return render_template(
            'deleteWebCategory.html', webCategory=catToDel,
            webCategories=webCategories, user=user)


@app.route('/showPages/<int:webCategory_id>')
def showPages(webCategory_id):
    webCategories = session.query(WebCategory).all()
    if 'username' in login_session:
        user_id = getUserID(login_session['email'])
        user = session.query(User).filter_by(id=user_id).one()
    else:
        user = None
    webCategories = session.query(WebCategory).all()
    webCategory = session.query(WebCategory).filter_by(
        id=webCategory_id).one()
    getAllPages = session.query(
        WebPage).filter_by(category_id=webCategory.id)
    return render_template(
        'showPages.html',
        webCategories=webCategories,
        webCategory=webCategory,
        getAllPages=getAllPages,
        user=user)


@app.route('/showPages/<int:webCategory_id>/showDetails/<int:page_id>')
def showPageDetails(webCategory_id, page_id):
    webCategories = session.query(WebCategory).all()
    webCategory = session.query(
        WebCategory).filter_by(id=webCategory_id).one()
    if 'username' in login_session:
        user_id = getUserID(login_session['email'])
        user = session.query(User).filter_by(id=user_id).one()
    else:
        user = None
    page = session.query(WebPage).filter_by(id=page_id).one()
    return render_template('pageDetails.html',
                           page=page, user=user,
                           webCategory=webCategory,
                           webCategories=webCategories)


@app.route('/showPages/<int:webCategory_id>/new', methods=['GET', 'POST'])
def addNewPage(webCategory_id):
    webCategories = session.query(WebCategory).all()
    if 'username' in login_session:
        user_id = getUserID(login_session['email'])
        user = session.query(User).filter_by(id=user_id).one()
    else:
        user = None
    if 'username' not in login_session:
        return render_template('noAccess.html')
    webCategory = session.query(
        WebCategory).filter_by(id=webCategory_id).one()
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
            'showPages', webCategory_id=webCategory_id))
        flash("New link added")
    else:
        return render_template(
            'newWebPage.html', webCategory_id=webCategory_id, user=user,
             webCategories=webCategories)


@app.route('/showPages/<int:webCategory_id>/editWebPage/<int:page_id>',
           methods=['GET', 'POST'])
def editWebPage(webCategory_id, page_id):
    webCategories = session.query(WebCategory).all()
    if 'username' in login_session:
        user_id = getUserID(login_session['email'])
        user = session.query(User).filter_by(id=user_id).one()
    else:
        user = None
    if 'username' not in login_session:
        return render_template('noAccess.html')
    editedPage = session.query(WebPage).filter_by(id=page_id).one()
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
        return redirect(url_for('showPages', webCategory_id=webCategory_id))
        flash("Web site changed")
    else:
        return render_template(
            'editWebPage.html',
            webCategory_id=webCategory_id,
            page_id=page_id,
            page=editedPage,
            user=user,
            webCategories=webCategories)


@app.route('/showPages/<int:webCategory_id>/deleteWebPage/<int:page_id>',
           methods=['GET', 'POST'])
def deleteWebPage(webCategory_id, page_id):
    webCategories = session.query(WebCategory).all()
    if 'username' in login_session:
        user_id = getUserID(login_session['email'])
        user = session.query(User).filter_by(id=user_id).one()
    else:
        user = None
    webCategories = session.query(WebCategory).all()
    if 'username' not in login_session:
        return render_template('noAccess.html')
    pageToDel = session.query(WebPage).filter_by(id=page_id).one()
    if request.method == 'POST':
        session.delete(pageToDel)
        session.commit()
        return redirect(url_for('showPages', webCategory_id=webCategory_id))
        flash("link has been removed")
    else:
        return render_template(
            'deleteWebPage.html',
            webCategories=webCategories,
            webCategory_id=webCategory_id,
            page_id=page_id,
            page=pageToDel,
            user=user,)


# JSON endpoints
@app.route('/showPages/<int:webCategory_id>/JSON')
def showPagesJSON(webCategory_id):
    webCategory = session.query(
        WebCategory).filter_by(id=webCategory_id).one()
    pages = session.query(
        WebPage).filter_by(category_id=webCategory.id).all()
    return jsonify(WebPages=[page.serialize for page in pages])


@app.route('/showPages/<int:webCategory_id>/showDetails/<int:page_id>/JSON')
def pageDetailsJSON(webCategory_id, page_id):
    page = session.query(WebPage).filter_by(id=page_id).one()
    return jsonify(WebPage=page.serialize)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
