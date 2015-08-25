# All Pool Spa Business Application.

# Python
import json
import os
import sys
from math import ceil
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
from models import Listing, User, Product, Result, db
from utils import dictHelper
from rq import Queue
from rq.job import Job
from worker import conn

# Flask configuration
app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
db.init_app(app)

#login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
bcrypt = Bcrypt(app)

#Redis
q = Queue(connection=conn)

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
@app.route('/')
@login_required
def home():
    return render_template('index.html')

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
    """Returns a *job.id* so we can keep track of each job and what it requested.
    TODO: Add jobid when database is set up.
    TODO: Track who made the job.
    """
    data = json.loads(request.data.decode())
    search_by = data['search_by']
    user_input = data['user_input']
    manufacturer = ''
    if 'manufacturer' in data:
        manufacturer = data['manufacturer']
    if search_by == 'Manufacturer':
        job = q.enqueue_call(
            func=itemsearch, args=(user_input,), result_ttl=5000
        )
    elif search_by == 'UPC' or search_by == 'ASIN':
        job = q.enqueue_call(
            func=itemlookup, args=(search_by, user_input,), result_ttl=5000
        )
    elif search_by == 'Price' and manufacturer:
        job = q.enqueue_call(
            func=price_range_search, args=(user_input, manufacturer,), result_ttl=5000
        ) 
    data['jobid'] = job.get_id() 
    return jsonify(data)

@app.route("/results/<job_key>", methods=['GET'])
@login_required
def get_results(job_key):
    job = Job.fetch(job_key, connection=conn)
    if job.is_finished:
        result = Result.query.filter_by(id=job.result).first()
        return jsonify(result.result_all)
    elif job.is_failed:
        return 'Failed', 500
    else:
        return "Nay!", 202
    return 'Returning something'


# Helper functions 
@login_manager.user_loader
def user_loader(user_id):
    """Given *user_id*, return the associated User object.

    :param unicode user_id: user_id (email) user to retrieve
    """
    return User.query.get(user_id)


# Database handlers 
def add_listings(listings):
    with app.app_context():
        errors = []
        try:
            result = Result(
                result_all=listings,
            )
            db.session.add(result)
            db.session.commit()
            return result.id
        except:
            errors.append("Unable to add item to database.")
            return {"error": errors}

def price_range_search_db(manufacturer, price_low, price_high):
    """User can specify what items to lookup on Amazon from the database.
    User can choose manufacturer and a price range. 
    Price range is optional.
    """
    wildcard_manufacturer = '%' + manufacturer + '%'
    with app.app_context():
        session = db.session()
        products = session.query(Product).filter(Product.manufacturer.ilike(wildcard_manufacturer), 
                                                Product.primary_cost >= price_low,
                                                Product.primary_cost <= price_high).all()
    upclist = []
    part_numberlist = []
    for product in products:
        if product.upc:
            upclist.append(product.upc)
        elif product.part_number:
            part_numberlist.append(product.part_number)

    upc_sections = sectionize(upclist)
    pn_sections = sectionize(part_numberlist)
    return upc_sections

def retrieve_cost(upc, listing):
    """Compares price between lowest price for the product and our cost.

    TODO: add price comparison functionality.

    : ..temporary: currently just grabs our cost.
    :param dict listing: a dictionary representation of a Listing
    """
    with app.app_context():
        session = db.session()
        products = session.query(Product).filter(Product.upc == upc)
        product = products.first()
        if product:
            listing['cost'] = product.primary_cost



# Amazon API Handlers 
def paapi_lookup(search_by, user_input, listings):
    if search_by == 'UPC':
        products = amazon.lookup(ItemId=user_input, IdType=search_by, SearchIndex='LawnAndGarden')
    elif search_by == 'ASIN':
        products = amazon.lookup(ItemId=user_input, IdType=search_by)
    if isinstance(products, list):
        for product in products:
            populate_listings(product, listings)
    else:
        populate_listings(products, listings)


def paapi_search(manufacturer):
    listings = {'count':'',
        'products':{}}
    products = amazon.search(SearchIndex='LawnAndGarden', Manufacturer=manufacturer)
    count = 0
    for product in products:
        count += 1
        populate_listings(product, listings)
    listings['count'] = count
    return listings

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

# This App's API Handlers
def itemsearch(manufacturer):
    """User can search Amazon's product listings by manufacturer.

    TODO: Allow user to select category. Currently LawnAndGarden. 
    TODO: Enable multiple manufacturer search.

    :param str manufacturer: the manufacturer to search for.
    """
    listings = paapi_search(manufacturer)
    return add_listings(listings)


def itemlookup(search_by, user_input):
    """User can search Amazon's product listings by upc."""
    listings = {'count':'',
            'products':{}}
    paapi_lookup(search_by, user_input, listings)
    return add_listings(listings)


def price_range_search(user_input, manufacturer):
    price_low, price_high = user_input.replace(' ','').split(',')
    flow, fhigh = float(price_low), float(price_high)
    upc_sectioned_list = price_range_search_db(manufacturer, flow, fhigh)
    listings = {'count':'',
        'products':{}}
    for upcs in upc_sectioned_list:
        paapi_lookup('UPC', upcs, listings)
    return add_listings(listings)

# Utility functions
def populate_listings(product, listings):
    """Populate a listing with product attributes.

    param obj product: a product from amazon paapi
    param dict listing: dict representation of amazon listing
    """
    # configure the listings
    listings['products'][product.asin] = deepcopy(LISTINGS_SCHEME)
    listing = listings['products'][product.asin]
    set_product_attributes(product, listing)
    if product.upc:
        retrieve_cost(product.upc, listing)
        set_lowest_prices(product.asin, listing)
    else:
        print('{0} has no UPC.'.format(product.title))  
 

def set_product_attributes(product, listing):
    """Add product attributes to the listing.

    param obj product: a product from amazon paapi
    param dict listing: dict representation of amazon listing
    """
    for keyi in listing.keys():
        #TODO: Extend AmazonProduct class to include LowestNewPrice
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

def set_lowest_prices(asin, listing):
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
                    # just use str
                    listing['lowest_price'] = lowest_price
                    print('Unable to convert price for {0}'.format(asin))
            if lowest_fba_price:
                try:
                    listing['lowest_fba_price'] = float(lowest_fba_price)
                except ValueError:
                    # Unable to convert fba price.
                    # Just use the string.
                    listing['lowest_fba_price'] = lowest_fba_price
                    print('Unable to convert FBA price for {0}'.format(asin))
            else:
                print('No FBA price available for {0}.'.format(asin))
                listing['lowest_fba_price'] = 'N/A'
        set_seller(product, listing)
    

def set_seller(product, listing):
    """Sellers are either Merchants or Amazon. 
    This identifies the fulfillment method. FBA or FBM

    :param obj product: product sold on Amazon
    :param obj listing: listing associated with *product*
    """
    for l in product.listings:
        if l.lowest_price or l.price == product.lowest_price:
            listing['seller'] = l.seller

def sectionize(alist):
    """ Amazon only allows 10 asins or upcs at a time. 
    So we make secitons 10.

    :param list alist: a list of upcs or part numbers.
    :return list sections: each item is a comma separated string 
        of at most 10 items from alist.
    """
    items = len(alist)
    beg, end = 0, 9
    sections = []
    while end < (items - 1):
        if beg == end:
            sections.append(alist[beg])
        else:
            sections.append(', '.join(alist[beg:end]))
        if (end + 1) <= (items - 1): 
            beg = end + 1
        if end > items - 1:
            end = items - 1
        else:
            end = end + 10
    return sections






if __name__ == '__main__': 
    app.run()