# Find Items To Sell On FBA (FITS|FBA)
# All Pool Spa Business Application.
# Allows an authorized user to access Amazon Product information
# such as, ranking, lowest price (FBA and non-FBA), product info.
# Also, if the product exists in application database, user can view their cost.

# Python
import json
import os
import sys
from math import ceil
from copy import deepcopy

# Third Party
from amazon.api import AmazonAPI, AmazonProduct
from rq import Queue
from rq.job import Job

# Extensions
from flask import (
    Flask, flash, Response, render_template, request,
    redirect, jsonify, url_for
)
from flask.ext.bcrypt import Bcrypt
from flask.ext.login import (
    LoginManager, login_required,
    login_user, logout_user, current_user
)
from flask.ext.sqlalchemy import SQLAlchemy
from flask.views import View

# Application
import papi
from mws import mws
from forms import LoginForm
from models import Listing, User, Product, Result, db
from utils import dictHelper, sectionize
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
paapi_conn = AmazonAPI(
    os.environ['AMAZON_ACCESS_KEY'], 
    os.environ['AMAZON_SECRET_KEY'], 
    os.environ['AMAZON_ASSOC_TAG']
)

# Amazon Marketplace Web Services API (MWS) configuration
mws_marketplace = os.environ['MWS_MARKETPLACE_ID']
mws_credentials =  {
    'access_key': os.environ['MWS_AWS_ACCESS_KEY_ID'], 
    'seller_id': os.environ['MWS_SELLER_ID'], 
    'secret_key': os.environ['MWS_SECRET_KEY']
}
mws_conn = mws.Products(
    access_key = mws_credentials['access_key'],
    account_id = mws_credentials['seller_id'],
    secret_key = mws_credentials['secret_key'],
)

##########
# Routes #
##########
class HomeView(View):
    """Main page for application. 
    Main view is a Single Page application (SPA)
    All presentation besides login and logout views 
    are presented here.
    """

    @app.route('/', methods=["GET"])
    @login_required
    def home():
        return render_template('index.html')

class UserView(View):
    """Login and Logout endpoints for application."""

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


class JobView(View):
    """There are two endpoints for the application: /start and /result/<job_key>.
    They are handled by their respective functions. 

    Start a job with /start and retrieve it with /result/<job_key>.
    """

    @app.route('/start', methods=['POST'])
    @login_required
    def start():
        """Returns a dict with *job.id* so we can keep track of each job and what it requested.
        TODO: Track who made the job.
        """
        data = json.loads(request.data.decode())
        search_by = data['search_by']
        user_input = data['user_input']
        manufacturer = ''

        # Handle each search with its respective function.
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
    def results(job_key):
        job = Job.fetch(job_key, connection=conn)
        if job.is_finished:
            result = Result.query.filter_by(id=job.result).first()
            return jsonify(result.result_all)
        elif job.is_failed:
            return '', 500
        else:
            return '', 201

# Helper functions
@login_manager.user_loader
def user_loader(user_id):
    """Given *user_id*, return the associated User object.

    :param unicode user_id: user_id (email) user to retrieve
    """
    return User.query.get(user_id)

# Database entry points 
def add_listings_to_db(listings):
    """add a listing to the database"""
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

    :param str manufacturer: the manufacturer to search for.
    :param float price_low: minimum price to search for
    :param float price_high: maximum price to search for
    """
    wildcard_manufacturer = '%' + manufacturer + '%'
    with app.app_context():
        session = db.session()
        products = session.query(Product).filter(
            Product.manufacturer.ilike(wildcard_manufacturer), 
            Product.primary_cost >= price_low,
            Product.primary_cost <= price_high
        ).all()
    return products

def query_by_upc(upc):
    """Get a product from the database by upc. 
    Should be only one so grab the first one from the query result.

    :param str upc: product upc.
    """
    with app.app_context():
        session = db.session()
        products = session.query(Product).filter(Product.upc == upc)
        product = products.first()
    return product

# Amazon API Handlers 
def paapi_lookup(search_by, user_input):
    """Handle requests for Amazon's Product Advertising API (PAAPI) 
    product lookup.

    :param str search_by: earch by Criteria UPC or ASIN.
    :param str user_input: upc(s)/asin(s).
    """
    products = None
    if search_by == 'UPC':
        products = paapi_conn.lookup(ItemId=user_input, IdType=search_by, SearchIndex='LawnAndGarden')
    elif search_by == 'ASIN':
        # When searching by ASIN no SearchIndex is accepted
        products = paapi_conn.lookup(ItemId=user_input, IdType=search_by)
    return products

def paapi_search(manufacturer):
    """Handle requests for Amazon's Product Advertising API (PAAPI) 
    product search.

    :param str manufacturer: the manufacturer to search for.
    """
    return paapi_conn.search(
        SearchIndex='LawnAndGarden', Manufacturer=manufacturer
    )

def paapi_result_handler(products, response):
    """Amazon may return one product or many products.
    If it is one Product it will be type AmazonProduct.
    This is how amazon.api module handles it.

    :param obj product: a product from amazon paapi
    :param obj response: Response object for this search.
    """
    if isinstance(products, AmazonProduct):
        populate_listings(products, response)
        response.count = 1
    else:
        count = 0
        for product in products:
            populate_listings(product, response)
            count += 1
        response.count += count

def mws_request(asin):
    if isinstance(asin, list):
        result = mws_conn.get_lowest_offer_listings_for_asin(
            mws_marketplace, asin, condition='New'
        )
    else:
        result = mws_conn.get_lowest_offer_listings_for_asin(
            mws_marketplace, [asin], condition='New'
        )
    return result

# This App's API response handlers
def itemsearch(manufacturer):
    """Handle request to Amazon's PAAPI itemsearch.

    TODO: Allow user to select category. Currently LawnAndGarden. 

    :param str manufacturer: the manufacturer to search for.
    """
    response = Response()
    products = paapi_search(manufacturer)
    paapi_result_handler(products, response)
    return add_listings_to_db(response.listings)

def itemlookup(search_by, user_input):
    """Handle request to Amazon's PAAPI lookup. 
    Currently the user can search by ASIN and UPC.

    :param str search_by: earch by Criteria UPC or ASIN.
    :param str user_input: upc(s)/asin(s).
    """
    response = Response()
    products = paapi_lookup(search_by, user_input)
    paapi_result_handler(products, response)
    return add_listings_to_db(response.listings)

def price_range(user_input, manufacturer):
    """Handle requests to search by price range.
    We actually search the database for products from *manufacturer*
    within *user_input* values.

    :param str user_input: prices separated by comma.
    :param str manufacturer: the manufacturer to search.
    """
    response = Response()
    # get price range and manufacturer
    price_low, price_high = user_input.replace(' ','').split(',')
    flow, fhigh = float(price_low), float(price_high)
    # get products from database
    our_products = query_price_range_search_db(manufacturer, flow, fhigh)
    # Amazon only allows 10 upcs at a time.
    upc_sectioned_list = sectionize(our_products)
    listings = None
    for upcs in upc_sectioned_list:
        #TODO: This is updating listings. Very confusing.
        products = paapi_lookup('UPC', upcs)
        paapi_result_handler(products, response)
    return add_listings_to_db(response.listings)

# Main function to fill response dict *listings*
def populate_listings(product, response):
    """Populate a listing with product attributes.

    :param obj product: a product from amazon paapi
    :param obj response: Response object for this search.
    """
    # configure the listings
    asin = product.asin
    response.populate_response(product)
    listing = response.listings['products'][asin]
    try:
        our_product = query_by_upc(product.upc)
        response.set_cost(asin, our_product.primary_cost)
    except:
        print("{0} has no UPC.".format(product.title))
    set_mws_product_information(asin, response)

def set_mws_product_information(asin, response):
    """ Get product from MWS API.
    Then make a MWS Product API object (Papi).
    Then set lowest price, lowest fba price, and seller in *response*.

    param str asin: Amazon's unique identifier for listing
    param obj response: Response object for this search.
    """
    result = mws_request(asin)
    mypapi = papi.Papi(result._mydict)
    if asin in mypapi.products:
        product = mypapi.products[asin]
        response.set_lowest_price_mws(asin, product.lowest_price)
        response.set_lowest_fba_price_mws(asin, product.lowest_fba_price)
        response.set_seller(asin, product.get_cheapest_seller())


if __name__ == '__main__': 
    app.run()