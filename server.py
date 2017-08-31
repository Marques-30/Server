from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant, MenuItem

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


@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    code = request.data

    try:
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


@app.route('/restaurants/<int:restaurant_id>/menu/JSON')
def JSON_Restaurant(restaurant_id):
	restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
	items = session.query(MenuItem).filter_by(restaurant_id = restaurant_id).all()
	return jsonify(MenuItems=[i.serialize for i in items])


@app.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/JSON')
def JSON_Menu(restaurant_id, menu_id):
	Item = session.query(MenuItem).filter_by(id=menu_id).one()
	return jsonify(Item = Item.serialize)


@app.route('/restaurants/JSON')
def JSON_Place():
	restaurants = session.query(Restaurant).all()
	return jsonify(restaurants=[r.serialize for r in restaurants])


@app.route("/")
#####################################################
#Restaurant settings
#####################################################

@app.route('/restaurants/')
def showAll():
	restaurants = session.query(Restaurant).all()
	return render_template('restaurants.html', restaurants = restaurants)


@app.route('/restaurants/new/', methods=['GET', 'POST'])
def New():
	if request.method == 'POST':
		Opening = Restaurant(name=request.form['name'])
		session.add(Opening)
		session.commit()
		return redirect(url_for('showAll'))
	else:
		return render_template('new.html')


@app.route('/restaurants/<int:restaurant_id>/edit/', methods=['GET', 'POST'])
def Edit(restaurant_id):
	Update = session.query(Restaurant).filter_by(id=restaurant_id).one()
	if request.method == 'POST':
		if request.form['name']:
			Update.name = request.form['name']
			return redirect(url_for('showAll'))
	else:
		return render_template('edit.html', restaurants=Update)


@app.route('/restaurants/<int:restaurant_id>/delete/', methods=['GET', 'POST'])
def Delete(restaurant_id):
	Remove = session.query(Restaurant).filter_by(id=restaurant_id).one()
	if request.method == 'POST':
		session.delete(Remove)
		session.commit()
		return redirect(url_for('showAll', restaurant_id=restaurant_id))
	else:
		return render_template('removed.html', restaurants=Remove)

################################################################################
# Menu settings

@app.route('/restaurants/<int:restaurant_id>/')
@app.route('/restaurants/<int:restaurant_id>/menu/')
def Menu(restaurant_id):
	restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
	items = session.query(MenuItem).filter_by(restaurant_id=restaurant_id).all()
	return render_template('menu.html', items=items, restaurant=restaurant)

@app.route('/restaurants/<int:restaurant_id>/menu/new', methods=['GET', 'POST'])
def Menu_new(restaurant_id):
	if request.method == 'POST':
		newItem = MenuItem(name=request.form['name'], description=request.form['description'], price=request.form['price'], course=request.form['course'], restaurant_id=restaurant_id)
		session.add(newItem)
		session.commit()
		return redirect(url_for('Menu', restaurant_id=restaurant_id))
	else:
		return render_template('menu_new.html', restaurant_id=restaurant_id)

@app.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/edit', methods=['GET', 'POST'])
def Menu_edit(restaurant_id, menu_id):
	change = session.query(MenuItem).filter_by(id=menu_id).one()
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
		return render_template('menu_edit.html', restaurant_id=restaurant_id, menu_id=menu_id, item=change)


@app.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/delete', methods=['GET', 'POST'])
def Menu_delete(restaurant_id, menu_id):
	item_delete=session.query(MenuItem).filter_by(id=menu_id).one()
	if request.method == 'POST':
		session.delete(item_delete)
		session.commit()
		return redirect(url_for('Menu', restaurant_id=restaurant_id))
	else:
		return render_template('menu_removed.html', item=item_delete, restaurant_id=restaurant_id)


if __name__ == "__main__":
	app.debug = True
	app.run()