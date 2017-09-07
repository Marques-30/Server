# Server

A python based script that creates a server and connects a database with web pages to show data from menu items and Restaurants.

### Installation

For this code to work your need to install python 2.7, SQL Database, and several python package psycopg2. To install python package simply enter the text below into command line.
    
    pip install sqlalchemy
    pip install Flask
    pip install oauth2client.client
    pip install jsonify
    pip install httplibs2
    pip install requests

###Start

To start the program first open command line, use the command cd to change directory and type in the folder name. From there type in python database_setup.py to run the file which will create the database that will be use throughout the server. Next type python server.py in run the server program which will display "* Running on http://127.0.0.1:5000/". From there open a internet browser and enter http://127.0.0.1:5000/ within the url which will open the website.

### Results

After running the code it will create the url: http://127.0.0.1:5000 to show a list of restaurants and menu items. You will be able to add Restaurants and menu items to the website through the python link to a database. As well as in the command line show status and data of server and those connected as well as changes they have made. The python lotsofmenuitems.py file contains the original data and writes new data for the database and is linked to server and display within the website.

### Contributors

Udacity had given the Data for the lotofmenuitems.py file to create the original database.