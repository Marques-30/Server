from flask import Flask, render_template, request, redirect
from flask import url_for, flash, jsonify

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant, MenuItem, User

from flask import session as login_session
import random
import string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

app.config['SECRET_KEY'] = 'Wbf2w90Bb0HnRkJYd0Zqgu-N'

CLIENT_ID = json.loads(
    open('JSON_Secret.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Restaurant"

engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def createUser(login_session):
    newUser = User(name=login_session['username'],
                   email=login_session['email'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('JSON_Secret.json', scope='')
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
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
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
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps
                                 ('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

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
    output += ' style = "width: 300px; height: 300px;'
    output += 'border-radius: 150px;'
    output += '-webkit-border-radius: 150px;'
    output += '-moz-border-radius: 150px;" > '
    flash("you are now logged in as %s" % login_session['username'])
    return output
    return render_template('restaurants.html', restaurants=restaurants)


@app.route('/gdisconnect')
def gdisconnect():
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(json.dumps('Current user not connected.'),
                                 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    access_token = credentials.access_token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        del login_session['credentials']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return redirect('/restaurants/')


@app.route('/restaurants/<int:restaurant_id>/menu/JSON')
def JSON_Restaurant(restaurant_id):
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    items = session.query(MenuItem).filter_by(restaurant_id=restaurant_id).all()
    return jsonify(MenuItems=[i.serialize for i in items])


@app.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/JSON')
def JSON_Menu(restaurant_id, menu_id):
    Item = session.query(MenuItem).filter_by(id=menu_id).one()
    return jsonify(Item=Item.serialize)


@app.route('/restaurants/JSON')
def JSON_Place():
    restaurants = session.query(Restaurant).all()
    return jsonify(restaurants=[r.serialize for r in restaurants])


@app.route("/")
# Restaurant settings
@app.route('/restaurants/')
def showAll():
    restaurants = session.query(Restaurant).all()
    return render_template('restaurants.html', restaurants=restaurants)

#Creating new restaurants
@app.route('/restaurants/new/', methods=['GET', 'POST'])
def New():
    #check for login
    if 'username' not in login_session:
        return redirect('/login')
    #Adding new restaurant through POST method
    if request.method == 'POST':
        Opening = Restaurant(name=request.form['name'])
        session.add(Opening)
        session.commit()
        return redirect(url_for('showAll'))
    else:
        return render_template('new.html')

#editing restaurants
@app.route('/restaurants/<int:restaurant_id>/edit/', methods=['GET', 'POST'])
def Edit(restaurant_id):
    #check for login
    Update = session.query(Restaurant).filter_by(id=restaurant_id).one()
    if Update.id != login_session['user_id']:
        flash("You do not have the right access to change %s", restaurant_id)
        return redirect('/restaurants/')
    #query that adds changes to restaurant name from linking database
    if request.method == 'POST':
        if request.form['name']:
            Update.name = request.form['name']
            return redirect(url_for('showAll'))
    else:
        return render_template('edit.html', restaurants=Update)

#deleting restaurants
@app.route('/restaurants/<int:restaurant_id>/delete/', methods=['GET', 'POST'])
def Delete(restaurant_id):
    #check for login
    Remove = session.query(Restaurant).filter_by(id=restaurant_id).one()
    if Remove.id != login_session['user_id']:
        flash("You do not have the right access to change %s", restaurant_id)
        return redirect('/restaurants/')
    #Query that removes restaurants and deletes data from linking database
    if request.method == 'POST':
        session.delete(Remove)
        session.commit()
        return redirect(url_for('showAll', restaurant_id=restaurant_id))
    else:
        return render_template('removed.html', restaurants=Remove)


# Menu settings

@app.route('/restaurants/<int:restaurant_id>/')
@app.route('/restaurants/<int:restaurant_id>/menu/')
def Menu(restaurant_id):
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    items = session.query(MenuItem).filter_by(restaurant_id=restaurant_id).all()
    return render_template('menu.html', items=items, restaurant=restaurant)


@app.route('/restaurants/<int:restaurant_id>/menu/new',
           methods=['GET', 'POST'])
def Menu_new(restaurant_id):
    #check for login
    newItem = MenuItem(name=request.form['name'],
                       description=request.form['description'],
                       price=request.form['price'],
                       course=request.form['course'],
                       restaurant_id=restaurant_id)
    if 'username' not in login_session or newItem.id != login_session['user_id']:
        flash("You do not have the right access to change %s", restaurant_id)
        return redirect('/restaurants/')
    if request.method == 'POST':
        #Query that creates a new menu item for restaurants
        session.add(newItem)
        session.commit()
        return redirect(url_for('Menu', restaurant_id=restaurant_id))
    else:
        return render_template('menu_new.html', restaurant_id=restaurant_id)


@app.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/edit',
           methods=['GET', 'POST'])
def Menu_edit(restaurant_id, menu_id):
    #check for login
    change = session.query(MenuItem).filter_by(id=menu_id).one()
    if change.id != login_session['user_id']:
        flash("You do not have the right access to change %s", restaurant_id)
        return redirect('/restaurants/')
    #Query that creates changes into selected restaurant's menu item
    if request.method == 'POST':
        if request.form['name']:
            change.name = request.form['name']
        if request.form['description']:
            change.description = request.form['description']
        if request.form['price']:
            change.price = request.form['price']
        if request.form['course']:
            change.course = request.form['course']
        session.add(change)
        session.commit()
        return redirect(url_for('Menu', restaurant_id=restaurant_id))
    else:
        return render_template('menu_edit.html', restaurant_id=restaurant_id,
                               menu_id=menu_id, item=change)


@app.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/delete',
           methods=['GET', 'POST'])
def Menu_delete(restaurant_id, menu_id):
    #check for login
    item_delete = session.query(MenuItem).filter_by(id=menu_id).one()
    if item_delete.id != login_session['user_id']:
        flash("You do not have the right access to change %s", restaurant_id)
        return redirect('/restaurants/')
    #Query that deletes data of only the selected menu item
    if request.method == 'POST':
        session.delete(item_delete)
        session.commit()
        return redirect(url_for('Menu', restaurant_id=restaurant_id))
    else:
        return render_template('menu_removed.html',
                               item=item_delete, restaurant_id=restaurant_id)


if __name__ == "__main__":
    app.debug = True
    app.run()
