# All Pool Spa Business Application.

# Python
import pprint
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
from response import Response

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
paapi_conn = AmazonAPI( os.environ['AMAZON_ACCESS_KEY'], 
                    os.environ['AMAZON_SECRET_KEY'], 
                    os.environ['AMAZON_ASSOC_TAG'])

# Amazon Marketplace Web Services API (MWS) configuration
mws_marketplace = os.environ['MWS_MARKETPLACE_ID']
mws_credentials =  {'access_key': os.environ['MWS_AWS_ACCESS_KEY_ID'], 
        'seller_id': os.environ['MWS_SELLER_ID'], 
        'secret_key': os.environ['MWS_SECRET_KEY']}
mws_conn = mws.Products( access_key = mws_credentials['access_key'],
                         account_id = mws_credentials['seller_id'],
                         secret_key = mws_credentials['secret_key'],)

###################
# Route functions #
###################
@app.route('/', methods=["GET"])
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
            func=price_range, args=(user_input, manufacturer,), result_ttl=5000
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


# Helper functions 
@login_manager.user_loader
def user_loader(user_id):
    """Given *user_id*, return the associated User object.

    :param unicode user_id: user_id (email) user to retrieve
    """
    return User.query.get(user_id)


# Database handlers 
def add_listings_to_db(listings):
    with app.app_context():
        errors = []
        try:
            result = Result(
                result_all=listings,
            )
            db.session.add(result)
            db.session.commit()
        except:
            print(sys.exc_info()[0])
            errors.append("Unable to add item to database.")
            return {"error": errors}
        return result.id

def query_price_range_search_db(manufacturer, price_low, price_high):
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
    return products

def make_sections(products):
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

def query_by_upc(upc):
    """Compares price between lowest price for the product and our cost.

    TODO: add price comparison functionality.

    : ..temporary: currently just grabs our cost.
    :param dict listing: a dictionary representation of a Listing
    """
    with app.app_context():
        session = db.session()
        products = session.query(Product).filter(Product.upc == upc)
        product = products.first()
    return product

#goes with query_by_upc
def set_cost(product, listing):
    if product:
        listing['cost'] = product.primary_cost
    # TODO: else: Throw except

# Amazon API Handlers 
def paapi_lookup(search_by, user_input):
    products = None
    if search_by == 'UPC':
        products = paapi_conn.lookup(ItemId=user_input, IdType=search_by, SearchIndex='LawnAndGarden')
    elif search_by == 'ASIN':
        products = paapi_conn.lookup(ItemId=user_input, IdType=search_by)
    return products 

def paapi_search(manufacturer):
    return paapi_conn.search(SearchIndex='LawnAndGarden', Manufacturer=manufacturer)

def paapi_results(products):
    if isinstance(products, list):
        response = Response(products, len(products))
        for product in products:
            populate_listings(product, response)
    else:
        response = Response(products, 1)
        populate_listings(products, response)
    return response.listings

def mws_request(asin):
    result = None
    if isinstance(asin, list):
        result = mws_conn.get_lowest_offer_listings_for_asin(mws_marketplace, asin, condition='New')
    else:
        result = mws_conn.get_lowest_offer_listings_for_asin(mws_marketplace, [asin], condition='New')
    return result


# This App's API endpoints
def itemsearch(manufacturer):
    """User can search Amazon's product listings by manufacturer.

    TODO: Allow user to select category. Currently LawnAndGarden. 
    TODO: Enable multiple manufacturer search.

    :param str manufacturer: the manufacturer to search for.
    """
    products = paapi_search(manufacturer)
    listings = paapi_results(products)
    return add_listings_to_db(listings)


def itemlookup(search_by, user_input):
    """User can search Amazon's product listings by upc."""
    results = paapi_lookup(search_by, user_input)
    listings = paapi_results(results)
    return add_listings_to_db(listings)


def price_range(user_input, manufacturer):
    price_low, price_high = user_input.replace(' ','').split(',')
    flow, fhigh = float(price_low), float(price_high)
    #upc_sectioned_list = query_price_range_search_db(manufacturer, flow, fhigh)
    products = query_price_range_search_db(manufacturer, flow, fhigh)
    upc_sectioned_list = make_sections(products)
    listings = None
    for upcs in upc_sectioned_list:
        results = paapi_lookup('UPC', upcs)
        listings = paapi_results(results)
    return add_listings_to_db(listings)

# Utility functions
###
def populate_listings(product, response):
    """Populate a listing with product attributes.

    param obj product: a product from amazon paapi
    param dict listing: dict representation of amazon listing
    """
    # configure the listings
    print dir(product)
    asin = product.asin
    #!listings['products'][asin] = deepcopy(LISTINGS_SCHEME)
    response.populate_response(product)
    listing = response.listings['products'][asin]
    #!set_product_attributes(product, listing)
    try:
        our_product = query_by_upc(product.upc)
        response.set_cost(asin, our_product.primary_cost)
    except:
        print("{0} has no UPC.".format(product.title))
    #!mws_listing_handler(product.asin, listing)
    result = mws_request(asin)
    mypapi = papi.Papi(result._mydict)
    for product in mypapi.products:
        if product.asin == asin:
            response.set_lowest_price_mws(asin, product.lowest_price)
            response.set_lowest_fba_price_mws(asin, product.lowest_fba_price)
            response.set_seller(asin, get_seller(product))

def get_seller(product):
    seller = None
    for l in product.listings:
        if l.lowest_price or l.price == product.lowest_price:
            seller = l.seller
    return seller 

###

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


def set_lowest_price(product, asin, listing):
    lowest_price = product.lowest_price
    if lowest_price:
        try:
            price = float(lowest_price)
            listing['lowest_price'] = price
        except ValueError:
            # unable to convert price to float
            # just use str
            listing['lowest_price'] = lowest_price
            print('Unable to convert price for {0}'.format(asin))

def set_lowest_fba_price(product, asin, listing):
    lowest_fba_price = product.lowest_fba_price
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