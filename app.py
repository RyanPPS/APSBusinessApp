# Find Items To Sell On FBA (FITS|FBA)
# All Pool Spa Business Application.
# Allows an authorized user to access Amazon Product information
# such as, ranking, lowest price (FBA and non-FBA), product info.
# Also, if the product exists in application database, user can view their cost.

# Python
import json
import os
from pprint import pprint

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
from papi import PAPI
import apis.dbapi as dbapi
import apis.amazon_api as amazon_api
from mws import mws
from forms import LoginForm
from models import Listing, Image, User, Product, Result, db
from utils import sectionize_upcs, sectionize_into_lists
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
highq = Queue(name='high', default_timeout=30, connection=conn)
lowq = Queue(name='low', default_timeout=600, connection=conn )
defaultq = Queue(connection=conn)

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
        form = LoginForm(request.form)
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
    """There are two endpoints for the application:
        /start and /result/<job_key>.
    They are handled by their respective functions.

    Start a job with /start and retrieve it with /result/<job_key>.
    """

    @app.route('/start', methods=['POST'])
    @login_required
    def start():
        """Returns a dict with *job.id* so we can keep track
        of each job and what it requested.
        TODO: Track who made the job.
        """
        data = json.loads(request.data.decode())
        search_by = data['search_by']
        user_input = data['user_input']
        if 'low_price' in data and 'high_price' in data:
            low_price = data['low_price']
            high_price = data['high_price']
            price_search = [
                search_by == 'Price',
                low_price,
                high_price,
            ]
        else:
            low_price = 0.0
            high_price = 0.0
        # Handle each search with its respective function.
        if search_by == 'Manufacturer' and user_input:
            job = lowq.enqueue_call(
                func=itemsearch,
                args=(user_input,),
                result_ttl=5000
            )
        elif (search_by == 'UPC' or search_by == 'ASIN') and user_input:
            job = lowq.enqueue_call(
                func=itemlookup,
                args=(search_by, user_input,),
                result_ttl=5000
            )
        elif all(price_search):
            job = lowq.enqueue_call(
                func=price_range,
                args=(user_input, low_price, high_price),
                result_ttl=5000
            )
        else:
            return 'Check search criteria', 500
        data['jobid'] = job.get_id()
        return jsonify(data)

    @app.route("/results/<job_key>", methods=['GET'])
    @login_required
    def results(job_key):
        job = Job.fetch(job_key, connection=conn)
        if job.is_started:
            return 'We are working on your request.', 201
        elif job.is_finished:
            result = Result.query.filter_by(id=job.result).first()
            return jsonify(result.result_all)
        elif job.is_failed:
            return 'There was a problem with your query.', 500
        else:
            return 'We have processed your request.', 202

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
        products = listings['products']
        for listing in products:
            add_listing(listing, products[listing])
            add_images(listing, products[listing]['imagelist'])

def save_listings_to_result(listings, errors=[]):
    errors = errors
    with app.app_context():
        if not errors:
            try:
                result = Result(
                    result_all=listings,
                )
                dbapi.add(result)
            except:
                errors.append("Unable to add item to database.")
                return {"error": errors}
        else:
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
    with app.app_context():
        if manufacturer:
            wildcard_manufacturer = '%' + manufacturer + '%'
            products = dbapi.productTable().search_by_price(
                price_low,
                price_high,
                wildcard_manufacturer
            )
        else:
            products = dbapi.productTable().search_by_price(
                price_low,
                price_high
            )
    return products

def query_by_upc(upc):
    """Get a product from the database by upc.
    Should be only one so grab the first one from the query result.

    :param str upc: product upc.
    """
    with app.app_context():
        product = dbapi.productTable().search_by_upc(upc)
    return product

# Amazon API Result Handler
def populate_response_listings(products, response):
    """Amazon may return one product or many products.
    If it is one Product it will be type AmazonProduct.
    This is how amazon.api module handles it.

    :param obj product: a product from amazon paapi
    :param obj response: Response object for this search.
    """
    if isinstance(products, AmazonProduct):
        populate_listings(products, response)
        set_mws_product_information([products.asin], response)
    else:
        asins = []
        for product in products:
            asins.append(product.asin)
            populate_listings(product, response)
        set_mws_product_information(asins, response)

# This App's API response handlers
def itemsearch(manufacturer):
    """Handle request to Amazon's PAAPI itemsearch.

    TODO: Allow user to select category. Currently LawnAndGarden.

    :param str manufacturer: the manufacturer to search for.
    """
    response = Response()
    try:
        products = amazon_api.products_search(manufacturer)
    except:
        print('Unable to process {0}'.format(manufacturer))
        return save_listings_to_result(
            {},
            errors="Unable to perform search"
        )
    populate_response_listings(products, response)
    listings = response.listings
    add_listings_to_db(listings)
    return save_listings_to_result(listings)

def itemlookup(search_by, user_input):
    """Handle request to Amazon's PAAPI lookup.
    Currently the user can search by ASIN and UPC.

    :param str search_by: earch by Criteria UPC or ASIN.
    :param str user_input: upc(s)/asin(s).
    """
    response = Response()
    try:
        products = amazon_api.product_lookup(search_by, user_input)
    except:
        print('Unable to process {0}'.format(user_input))
        return save_listings_to_result(
            {},
            errors="Unable to perform search"
        )
    populate_response_listings(products, response)
    listings = response.listings
    add_listings_to_db(listings)
    return save_listings_to_result(listings)

def price_range(manufacturer, low_price, high_price):
    """Handle requests to search by price range.
    We actually search the database for products from *manufacturer*
    within *user_input* values.

    :param str user_input: prices separated by comma.
    :param str manufacturer: the manufacturer to search.
    """
    response = Response()
    flow, fhigh = get_prices(low_price, high_price)
    # get products from database
    our_products = query_price_range_search_db(
        manufacturer,
        flow,
        fhigh
    )
    # Amazon only allows 10 upcs at a time.
    upc_sectioned_list = sectionize_upcs(our_products)
    for upcs in upc_sectioned_list:
        try:
            products = amazon_api.product_lookup('UPC', upcs)
        except:
            print('Unable to process {0}'.format(upcs))
            # TODO: currently we just throw away the whole section of UPCS
            # we should just filtered out the bad UPC and try again.
            continue
        populate_response_listings(products, response)
    listings = response.listings
    add_listings_to_db(listings)
    return save_listings_to_result(listings)

def get_prices(low_price, high_price):
    # TODO: catch bad input from users.
    # get price range and manufacturer
    try:
        flow, fhigh = float(low_price), float(high_price)
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
    our_cost = get_our_cost(product.upc)
    response.set_cost(asin, our_cost)
    #set_mws_product_information(asin, response)

def get_our_cost(upc):
    if upc is None:
        return None
    our_product = query_by_upc(upc)
    if our_product:
        return our_product.primary_cost
    else:
        print("{0} has no UPC.".format(our_product))
        return None

def set_mws_product_information(asins, response):
    """ Get product from MWS API.
    Then make a MWS Product API object (Papi).
    Then set lowest price, lowest fba price, and seller in *response*.

    param str asins: Amazon's unique identifier for listing
    param obj response: Response object for this search.
    """
    if len(asins) > 10:
        sections = sectionize_into_lists(asins)
    else:
        sections = [asins]
    for section in sections:
        print('searching mws....')
        try:
            result = amazon_api.get_lowest_offer_listings_for_asin(
                section
            )
            pprint(result.parsed)
        except:
            # I need to deal more gracefully with errors in the request.
            # I should find out what asin triggered the error and remove it
            # and try again
            print('Unable to process {0}'.format(section))
            continue
        papi = PAPI(result.parsed)
        papi.make_products()
        for asin in section:
            try:
                product = papi.products[asin]
                response.set_lowest_price_mws(asin, product.lowest_price)
                response.set_lowest_fba_price_mws(
                    asin,
                    product.lowest_fba_price
                )
                response.set_seller(asin, product.get_cheapest_seller())
            except:
                #asin not in papi.products
                pass


if __name__ == '__main__':
    app.run()
