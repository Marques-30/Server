from flask import flask
import flash

app = Flask(__name__)

DBSession = sessionmaker(bind=engine)
session = DBSession()

#Fake Restaurants
restaurant = {'name': 'The CRUDdy Crab', 'id': '1'}

restaurants = [{'name': 'The CRUDdy Crab', 'id': '1'}, {'name':'Blue Burgers', 'id':'2'},{'name':'Taco Hut', 'id':'3'}]


#Fake Menu Items
items = [ {'name':'Cheese Pizza', 'description':'made with fresh cheese', 'price':'$5.99','course' :'Entree', 'id':'1'}, {'name':'Chocolate Cake','description':'made with Dutch Chocolate', 'price':'$3.99', 'course':'Dessert','id':'2'},{'name':'Caesar Salad', 'description':'with fresh organic vegetables','price':'$5.99', 'course':'Entree','id':'3'},{'name':'Iced Tea', 'description':'with lemon','price':'$.99', 'course':'Beverage','id':'4'},{'name':'Spinach Dip', 'description':'creamy dip with fresh spinach','price':'$1.99', 'course':'Appetizer','id':'5'} ]
item =  {'name':'Cheese Pizza','description':'made with fresh cheese','price':'$5.99','course' :'Entree'}



@app.route('/')
@app.route('/restaurants/')
def showAll():
	#Show all restaurants
	return render_template('restaurants.html' restaurants=restaurants)


@app.route('/restaurants/new')
def newRestaurant():
	#Show all restaurants
	return render_template('newRestaurants.html' restaurants=restaurants)


@app.route('/restaurants/restaurant_id/edit')
def editRestaurant():
	#Show all restaurants
	return render_template('editRestaurants.html' restaurants=restaurants)

@app.route('/restaurants/restaurant_id/delete')
def deleteRestaurant():
	#Show all restaurants
	return render_template('deleteRestaurants.html' restaurants=restaurants)


#####################################################################################	
@app.route('/restaurants/restaurant_id/restaurants/restaurants_id/menu')
def showMenu():
	#Show all restaurants
	return render_template('menu.html' restaurants=restaurants)


#Create a new Menu
@app.route('/restaurants/restaurant_id/menu/new', methods=['GET','POST'])
def newMenuItem(restaurant_id):
	
	if request.method == 'POST':
		newItem = MenuItem(name = request.form['name'], description = request.form['description'], price = request.form['price'], course = request.form['course'], restaurant_id = restaurant_id)
		session.add(newItem)
		session.commit()
		flash("This page is for making a new menu item for restaurant %s" restaurant_id)
		return redirect(url_for('restaurantMenu', restaurant_id = restaurant_id))
	else:
		return render_template('newMenuItem.html', restaurant_id = restaurant_id)


#edit menu
@app.route('/restaurants/restaurant_id/menu/menu_id/edit', methods = ['GET', 'POST'])
def editMenuItem(restaurant_id, menu_id):
	editedItem = session.query(MenuItem).filter_by(id = menu_id).one()
	if request.method == 'POST':
		if request.form['name']:
			editedItem.name = request.form['name']
		if request.form['description']:
			editedItem.description = request.form['name']
		if request.form['price']:
			editedItem.price = request.form['price']
		if request.form['course']:
			editedItem.course = request.form['course']
		session.add(editedItem)
		session.commit()
		flash("This page is for editing menu items %s" menu_id)
		return redirect(url_for('restaurantMenu', restaurant_id = restaurant_id))
	else:
		return render_template('editMenuItem.html', restaurant_id = restaurant_id, menu_id = menu_id, item = editedItem)


#Delete Menu
@app.route('/restaurants/restaurant_id/menu/menu_id/delete', methods = ['GET','POST'])
def deleteMenuItem(restaurant_id, menu_id):
	itemToDelete = session.query(MenuItem).filter_by(id = menu_id).one() 
	if request.method == 'POST':
		session.delete(itemToDelete)
		session.commit()
		flash("This page is for deleting menu items %s" menu_id)
		return redirect(url_for('restaurantMenu', restaurant_id = restaurant_id))
	else:
		return render_template('deleteMenuItem.html', item = itemToDelete)


if __name__ == '__main__':
	app.debug = True
	app.run(host = '0.0.0.0', port = 5000)