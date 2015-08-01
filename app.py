# Python
import json
import os
from copy import deepcopy

# Extensions
from flask import (Flask, Response, render_template, request, \
                redirect, jsonify, url_for)
from flask.ext.bcrypt import Bcrypt
from flask.ext.login import (LoginManager, login_required, \
                login_user, logout_user, current_user)
from flask.ext.sqlalchemy import SQLAlchemy

# Application
from amazon.api import AmazonAPI, AmazonProduct
from variables import LISTINGS_SCHEME
from forms import LoginForm
from models import Listing, User, db

# Flask configuration
app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
bcrypt = Bcrypt(app)



# Amazon product advertising API configuration
amazon = AmazonAPI( os.environ['AMAZON_ACCESS_KEY'], 
                    os.environ['AMAZON_SECRET_KEY'], 
                    os.environ['AMAZON_ASSOC_TAG'])


@login_manager.user_loader
def user_loader(user_id):
    """Given *user_id*, return the associated User object.

    :param unicode user_id: user_id (email) user to retrieve
    """
    return User.query.get(user_id)

@app.route("/login", methods=["GET", "POST"])
def login():
    """For GET requests, display the login form. 
    For POSTS, login the current userby processing the form.
    """
    # TODO: I have no LoginForm. Get this.

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.get(form.email.data)
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                user.authenticated = True
                db.session.add(user)
                db.session.commit()
                login_user(user, remember=True)
                return redirect(url_for("home"))
    return render_template("login.html", form=form)

@app.route("/logout", methods=["GET"])
@login_required
def logout():
    """Logout the current user."""
    user = current_user
    print current_user.is_authenticated()
    user.authenticated = False
    db.session.add(user)
    db.session.commit()
    logout_user()
    return render_template("logout.html")


@app.route('/')
@login_required
def home():
    return render_template('index.html')

@app.route('/start', methods=['POST'])
@login_required
def start():
    # TODO: Add jobid when database is set up.
    data = json.loads(request.data.decode())
    return data["user_input"]

@app.route('/itemsearch/<manufacturer>', methods=['GET'])
@login_required
def itemsearch(manufacturer):
    """User can search Amazon's product listings by manufacturer.

    TODO: Allow user to select category. Currently LawnAndGarden. 
    TODO: Enable multiple manufacturer search.

    :param str manufacturer: the manufacturer to search for.
    """
    products = amazon.search(SearchIndex='LawnAndGarden', Manufacturer=manufacturer)
    listings = {'count':'',
                'products':{}}
    count = 0
    for product in products:
        count += 1
        add_product(product, listings)
    listings['count'] = count
    return jsonify(listings)

@app.route('/itemlookup/<upc>', methods=['GET'])
@login_required
def itemlookup(upc):
    listings = {'count':'',
            'products':{}}
    products = amazon.lookup(ItemId=upc, IdType='UPC', SearchIndex='LawnAndGarden')
    for product in products:
        add_product(product, listings)
    return jsonify(listings)

def add_product(product, listings):
    asin = product.asin
    listings['products'][asin] = deepcopy(LISTINGS_SCHEME)
    listing = listings['products'][asin]
    for keyi in listing.keys():
        #TODO: Extend AmazonProduct class to include LowestNewPrice
        # .. :temporary: extend AmazonProduct class
        if keyi == 'LowestNewPrice':
            price = product._safe_get_element_text(
                'OfferSummary.LowestNewPrice.Amount')
            if price:
                print "Price evaulated True"
                print price
                fprice = float(price) / 100 if 'JP' not in product.region else price
            else:
                print "Price evaulated False"
                print price
                fprice = price
            listing[keyi] = fprice
            continue

        # images go in imagelist    
        if isinstance(listing[keyi], dict):
            for keyj in listing[keyi].keys():
                try:
                    listing[keyi][keyj] = product.__getattribute__(keyj)
                except:
                    print("Attribute {0} not found".format(keyj))
            continue

        try:
            listing[keyi] = product.__getattribute__(keyi)
        except:
            print("Attribute {0} not found".format(keyi))


def get_jobid():
    # TODO: Add jobid when database is set up.
    # TODO: Track who made the job.
    """Returns a *job.id* so we can keep track of each job and what it requested.
    """
    job = q.enqueue_call(
        func=itemsearch, args=(manufacturer,), result_ttl=5000
    )
    # return created job id
    return job.get_id()





if __name__ == '__main__': 
    app.debug = True
    app.run()