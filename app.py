# All Pool Spa Business Application.

# Python
import json
import os
import sys
from copy import deepcopy

# Extensions
from flask import (Flask, flash, Response, render_template, request, \
                redirect, jsonify, url_for)
from flask.ext.bcrypt import Bcrypt
from flask.ext.login import (LoginManager, login_required, \
                login_user, logout_user, current_user)
from flask.ext.sqlalchemy import SQLAlchemy

# Application
import papi
from amazon.api import AmazonAPI, AmazonProduct
from mws import mws
from variables import LISTINGS_SCHEME
from forms import LoginForm
from models import Listing, User, Product, db
from utils import dictHelper


# Flask configuration
app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
bcrypt = Bcrypt(app)



# Amazon product advertising API (PAAPI) configuration
amazon = AmazonAPI( os.environ['AMAZON_ACCESS_KEY'], 
                    os.environ['AMAZON_SECRET_KEY'], 
                    os.environ['AMAZON_ASSOC_TAG'])

# Amazon Marketplace Web Services API (MWS) configuration
mws_marketplace = os.environ['MWS_MARKETPLACE_ID']
mws_credentials =  {'access_key': os.environ['MWS_AWS_ACCESS_KEY_ID'], 
        'seller_id': os.environ['MWS_SELLER_ID'], 
        'secret_key': os.environ['MWS_SECRET_KEY']}


###################
# Route functions #
###################
@login_manager.user_loader
def user_loader(user_id):
    """Given *user_id*, return the associated User object.

    :param unicode user_id: user_id (email) user to retrieve
    """
    return User.query.get(user_id)

@app.route('/')
@login_required
def home():
    return render_template('index.html')

@app.route('/testmws')
@login_required
def testmws():
    """Get missing Product information from Amazon's Product MWS Api.
    Gets lowest price information.

    TODO: Receive ASINs and make request for information to Amazon.

    :..temporary: this is a test version.
    """
    mws_products = mws.Products( access_key = mws_credentials['access_key'],
                         account_id = mws_credentials['seller_id'],
                         secret_key = mws_credentials['secret_key'],)
    #products = mws_products.list_matching_products(mws_marketplace, 'unicel')
    result = mws_products.get_lowest_offer_listings_for_asin(mws_marketplace, ['B000A4TDPO', 'B000BNM25W', 'B000BNM27U'], condition='New')
    dproducts = result._mydict
    p = Papi(dproducts)
    return jsonify(dproducts)


@app.route("/login", methods=["GET", "POST"])
def login():
    """For GET requests, display the login form. 
    For POSTS, login the current userby processing the form.
    """
    # TODO: Make roles.

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
    user.authenticated = False
    db.session.add(user)
    db.session.commit()
    logout_user()
    return render_template("logout.html")

@app.route('/start', methods=['POST'])
@login_required
def start():
    # TODO: Add jobid when database is set up.
    data = json.loads(request.data.decode())
    return jsonify(data)

@app.route('/itemsearch/<manufacturer>', methods=['GET'])
@login_required
def itemsearch(manufacturer):
    """User can search Amazon's product listings by manufacturer.

    TODO: Allow user to select category. Currently LawnAndGarden. 
    TODO: Enable multiple manufacturer search.

    :param str manufacturer: the manufacturer to search for.
    """
    print '#################################'
    print '#################################'
    print manufacturer
    print '#################################'
    print '#################################'
    listings = {'count':'',
        'products':{}}
    products = amazon.search(SearchIndex='LawnAndGarden', Manufacturer=manufacturer)
    count = 0
    for product in products:
        count += 1
        populate_listings(product, listings)
    listings['count'] = count
    return jsonify(listings)

@app.route('/itemlookup', methods=['GET', 'POST'])
@login_required
def itemlookup():
    """User can search Amazon's product listings by upc.

    TODO: Enable multiple upc search.

    :param str upc: the upc to search for.
    """
    search_by = request.args.get('search_by')
    user_input = request.args.get('user_input')
    if not search_by:
        flash('Please select a search by criteria.')
        return render_template('index.html')
    listings = {'count':'',
        'products':{}}
    products = amazon.lookup(ItemId=user_input, IdType=search_by, SearchIndex='LawnAndGarden')
    try:
        for product in products:
            populate_listings(product, listings)
    except:
        populate_listings(products, listings)
    return jsonify(listings)

####################
# Helper functions #
####################
def populate_listings(product, listings):
    """Populate a listing with product attributes.

    param obj product: a product from amazon paapi
    param dict listing: dict representation of amazon listing
    """
    # configure the listings
    listings['products'][product.asin] = deepcopy(LISTINGS_SCHEME)
    listing = listings['products'][product.asin]
    add_product(product, listing)
    if product.upc:
        compare_price(product.upc, listing)
        get_lowest_price(product.asin, listing)
    else:
        print('{0} has no UPC.'.format(product.title))   

def add_product(product, listing):
    """Add product attributes to the listing.

    param obj product: a product from amazon paapi
    param dict listing: dict representation of amazon listing
    """
    for keyi in listing.keys():
        #TODO: Extend AmazonProduct class to include LowestNewPrice
        # .. :temporary: extend AmazonProduct class
        if keyi == 'LowestNewPrice':
            price = product._safe_get_element_text(
                'OfferSummary.LowestNewPrice.Amount')
            if price:
                try:
                    fprice = float(price) / 100 if 'JP' not in product.region else price
                except:
                    fprice = price
            else:
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

def mws_request(asin):
    mws_products = mws.Products( access_key = mws_credentials['access_key'],
                         account_id = mws_credentials['seller_id'],
                         secret_key = mws_credentials['secret_key'],)
    result =  []
    if isinstance(asin, list):
        result = mws_products.get_lowest_offer_listings_for_asin(mws_marketplace, asin, condition='New')
    else:
        result =  mws_products.get_lowest_offer_listings_for_asin(mws_marketplace, [asin], condition='New')
    return result

def get_lowest_price(asin, listing):
    # Get response from Amazon's MWS api.
    result = mws_request(asin)
    # Get products from mws response.
    dproducts = result._mydict
    mypapi = papi.Papi(dproducts)
    for product in mypapi.products:
        if product.asin == asin:
            lowest_price = product.lowest_price
            lowest_fba_price = product.lowest_fba_price
            if lowest_price:
                try:
                    price = float(lowest_price)
                    listing['lowest_price'] = price
                except ValueError:
                    # unable to convert price to float
                    # just send str
                    listing['lowest_price'] = lowest_price
                    print('Unable to convert price for {0}'.format(asin))
            if lowest_fba_price:
                try:
                    listing['lowest_fba_price'] = float(lowest_fba_price)
                except ValueError:
                    # Unable to convert fba price.
                    # Just send the string.
                    listing['lowest_fba_price'] = lowest_fba_price
                    print('Unable to convert FBA price for {0}'.format(asin))
            else:
                print('No FBA price available for {0}.'.format(asin))
                listing['lowest_fba_price'] = 'N/A'
        set_seller(product, listing)

def set_seller(product, listing):
    for l in product.listings:
        if l.lowest_price or l.price == product.lowest_price:
            listing['seller'] = l.seller


def compare_price(upc, listing):
    """Compares price between lowest price for the product and our cost.

    TODO: add price comparison functionality.

    : ..temporary: currently just grabs our cost.
    :param dict listing: a dictionary representation of a Listing
    """
    session = db.session()
    products = session.query(Product).filter(Product.upc == upc)
    product = products.first()
    if product:
        listing['cost'] = product.primary_cost


def get_jobid():
    """Returns a *job.id* so we can keep track of each job and what it requested.
    TODO: Add jobid when database is set up.
    TODO: Track who made the job.
    """
    job = q.enqueue_call(
        func=itemsearch, args=(manufacturer,), result_ttl=5000
    )
    # return created job id
    return job.get_id()





if __name__ == '__main__': 
    app.debug = True
    app.run()