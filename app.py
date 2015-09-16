# Find Items To Sell On FBA (FITS|FBA)
# All Pool Spa Business Application.
# Allows an authorized user to access Amazon Product information
# such as, ranking, lowest price (FBA and non-FBA), product info.
# Also, if the product exists in application database, user can view their cost.

# Python
import json
import os

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
import apis.dbapi as dbapi
import apis.amazon_api as amazon_api
from mws import mws
from forms import LoginForm
from models import Listing, Image, User, Product, Result, db
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
        return render_template('fitsfba.html')

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
            user = dbapi.get_user(form.email.data)
            if user:
                if bcrypt.check_password_hash(user.password, form.password.data):
                    user.authenticated = True
                    dbapi.add(user)
                    login_user(user, remember=True)
                    return redirect(url_for("home"))
        return render_template("login.html", form=form)

    @app.route("/logout", methods=["GET"])
    @login_required
    def logout():
        """Logout the current user."""
        user = current_user
        user.authenticated = False
        dbapi.add(user)
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
        if 'manufacturer' in data:
            manufacturer = data['manufacturer']
        else:
            manufacturer = ''
        # Handle each search with its respective function.
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
        else:
            return 'Check search criteria', 500
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
        elif job.is_started:
            return '', 201
        else:
            return '', 202

# Helper functions
@login_manager.user_loader
def user_loader(user_id):
    """Given *user_id*, return the associated User object.

    :param unicode user_id: user_id (email) user to retrieve
    """
    return dbapi.get_user(user_id)

# Database handlers
def add_listings_to_db(listings):
    """add a listing to the database"""
    with app.app_context():
        errors = []
        products = listings['products']
        for listing in products:
            add_listing(listing, products[listing])
            add_images(listing, products[listing]['imagelist'])
        try:
            result = Result(
                result_all=listings,
            )
            dbapi.add(result)
        except:
            errors.append("Unable to add item to database.")
            return {"error": errors}
        return result.id

def add_listing(asin, listing={}):
    # We may need to add a listing with just an asin.
    listing_exists = dbapi.listing_exists(asin)
    if not (listing_exists or listing):
        dbapi.add(Listing(asin=asin))
    elif not listing_exists:
        try:
            fprice = float(listing['lowest_price'])
        except:
            fprice = None
        try:
            l = Listing(
                asin = asin,
                manufacturer = listing['manufacturer'],
                title = listing['title'],
                part_number = listing['part_number'],
                price = fprice,
                upc = listing['upc']
            )
            dbapi.add(l)

        except:
            print('Unable to add listing to db')
    else:
        print('{0} already exists in db'.format(asin))

def add_images(asin, images):
    if not dbapi.listing_exists(asin):
        add_listing(asin)
    if not dbapi.image_exists(asin):
        try:
            image = Image(
                tiny_image = images['tiny_image_url'],
                small_image = images['small_image_url'],
                medium_image = images['medium_image_url'],
                large_image = images['large_image_url'],
                listing_asin = asin
            )
            dbapi.add(image)
        except:
            print('Unable to add {0} to db'.format(asin))
    else:
        print('{0} already exists in db'.format(asin))

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
        products = dbapi.search_by_price(wildcard_manufacturer, price_low, price_high)
        print("Products returned from db:\n{0}".format(products))
    return products

def query_by_upc(upc):
    """Get a product from the database by upc. 
    Should be only one so grab the first one from the query result.

    :param str upc: product upc.
    """
    with app.app_context():
        product = dbapi.search_by_upc(upc)
    return product

# Amazon API Result Handler 
def paapi_result_handler(products, response):
    """Amazon may return one product or many products.
    If it is one Product it will be type AmazonProduct.
    This is how amazon.api module handles it.

    :param obj product: a product from amazon paapi
    :param obj response: Response object for this search.
    """
    if isinstance(products, AmazonProduct):
        populate_listings(products, response)
    else:
        for product in products:
            populate_listings(product, response)

# This App's API response handlers
def itemsearch(manufacturer):
    """Handle request to Amazon's PAAPI itemsearch.

    TODO: Allow user to select category. Currently LawnAndGarden. 

    :param str manufacturer: the manufacturer to search for.
    """
    response = Response()
    products = amazon_api.paapi_search(manufacturer)
    paapi_result_handler(products, response)
    return add_listings_to_db(response.listings)

def itemlookup(search_by, user_input):
    """Handle request to Amazon's PAAPI lookup. 
    Currently the user can search by ASIN and UPC.

    :param str search_by: earch by Criteria UPC or ASIN.
    :param str user_input: upc(s)/asin(s).
    """
    response = Response()
    products = amazon_api.paapi_lookup(search_by, user_input)
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
    flow, fhigh = get_prices(user_input)
    # get products from database
    our_products = query_price_range_search_db(manufacturer, flow, fhigh)
    # Amazon only allows 10 upcs at a time.
    upc_sectioned_list = sectionize(our_products)
    listings = None
    for upcs in upc_sectioned_list:
        #TODO: This is updating listings. Very confusing.
        products = amazon_api.paapi_lookup('UPC', upcs)
        paapi_result_handler(products, response)
    return add_listings_to_db(response.listings)

def get_prices(user_input):
    # TODO: catch bad input from users.
    # get price range and manufacturer
    try:
        price_low, price_high = user_input.replace(' ','').split(',')
        flow, fhigh = float(price_low), float(price_high)
    except:
        return 0.0, 0.0
    return flow, fhigh

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
    result = amazon_api.mws_request(asin)
    mypapi = papi.Papi(result._mydict)
    if asin in mypapi.products:
        product = mypapi.products[asin]
        response.set_lowest_price_mws(asin, product.lowest_price)
        response.set_lowest_fba_price_mws(asin, product.lowest_fba_price)
        response.set_seller(asin, product.get_cheapest_seller())


if __name__ == '__main__': 
    app.run()