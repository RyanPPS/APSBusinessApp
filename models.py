# Database models.
# :table listings: amazon listing information
# :table products: product information
# :table images: images for a particular product
# :table user: user information

from app import db
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSON


class Listings(db.Model):
    """An Amazon listing that is related to an images and a product.

    :param str asin: Amazon's unique identifier for listing
    :param str manufacturer: manufacturer of product
    :param str part_number: part_number for the product
    :param str upc: upc code of product of listing
    :param str title: title of listing
    :param float price: lowest price of product
    :param str currency: monetary currency
    :param rel images: relationship to different size images for a listing
    :param json result_all: contains all the listing information.
    """
    __tablename__ = 'listings'

    asin = db.Column(db.String(), primary_key=True)
    manufacturer = db.Column(db.String())
    part_number = db.Column(db.String())
    upc = db.Column(db.String())
    title = db.Column(db.String())
    price = db.Column(db.Float)
    currency = db.Column(db.String())
    result_all = db.Column(JSON)

    # Add relationship: The ForeignKey below expresses that values in 
    # the listings.images_id column should be constrained to those 
    # values in the images.id column, i.e. its primary key.
    images_id = db.Column(db.Integer, db.ForeignKey('images.id'))
    images = db.relationship("Images")
    

    def __init__(self, asin, manufacturer, part_number, upc, title, price, currency, images, images_id, result_all):
        self.asin = asin
        self.manufacturer = manufacturer
        self.part_number = part_number
        self.upc = upc
        self.title = title
        self.price = price
        self.currency = currency
        self.image_id = image_id
        self.images = images
        self.result_all = result_all

    def __repr__(self):
        return '<asin {}>'.format(self.asin)

class Image(db.Model):
    """Images associated with an Amazon Listing

    :param str id: id for the images
    :param str tiny_image: url string for the tiny image
    :param str small_image: url string for the small image
    :param str medium_image: url string for the medium image
    :param str large_image: url string for the large image
    """
    __tablename__ = 'image'

    id = db.Column(db.Integer, primary_key=True autoincrement=True)
    listing_asin = db.Column(db.String() db.ForeignKey('listing.asin'))
    upc = db.Column(db.String() db.ForeignKey('product.upc'))
    tiny_image = db.Column(db.String())
    small_image = db.Column(db.String())
    medium_image = db.Column(db.String())
    large_image = db.Column(db.String())

    def __init__(self, id, listing_asin, upc, tiny_image, small_image, 
            medium_image, large_image):

        self.id = id
        self.listing_asin = listing_asin
        self.upc = upc
        self.tiny_image = tiny_image
        self.small_image = small_image
        self.medium_image = medium_image
        self.large_image = large_image

    def __repr__(self):
        return '<listing_asin {}>'.format(self.listing_asin)


# TODO: Create product table with relationship to listing and image
#class Product(db.Model):
    """A product that is related to listing(s) and image(s).

    :param str upc: upc code
    :param str manufacturer: manufacturer of product
    :param str part_number: part_number for the product
    :param str title: title of listing
    :param float primary_cost: our lowest and main cost, i.e. manufacturer cost.
    :param float secondary_cost: another cost from a secondary source, i.e. distribution
    :param str weight: weight of product
    :param str height: height of product
    :param str width: width of product
    :param str length: length of product
    :param bool available: products availability
    :param rel images: relationship to different size images for a listing
    """
    """
    __tablename__ = 'product'

    upc = db.Column(db.String(), primary_key=True)
    listings = db.relationship("Listing" backref='product')
    manufacturer = db.Column(db.String())
    part_number = db.Column(db.String())
    title = db.Column(db.String())
    primary_cost = db.Column(db.Float)
    secondary_cost = db.Column(db.Float)
    available = db.Column(db.Boolean)
    weight = db.Column(db.String())
    height = db.Column(db.String())
    width = db.Column(db.String())
    length = db.Column(db.String())
    images = db.relationship("Image" backref='product')
    image_id = db.Column(db.Integer, db.ForeignKey('image.id'))
    

    def __init__(self, upc, asin, manufacturer, part_number, title, 
            primary_cost, secondary_cost, available, weight, height, length, images):

        self.upc = upc
        self.asin = asin
        self.manufacturer = manufacturer
        self.part_number = part_number
        self.title = title
        self.primary_cost = primary_cost
        self.secondary_cost = secondary_cost
        self.available = available
        self.weight = weight
        self.height = height
        self.width = width
        self.length = length
        self.images = images

    def __repr__(self):
        return '<upc {}>'.format(self.upc)
    """

class User(db.Model):
    """An admin user capable of viewing reports.

    :param str email: email address of user
    :param str password: encrypted password for the user

    """
    __tablename__ = 'user'

    email = db.Column(db.String, primary_key=True)
    password = db.Column(db.String)
    authenticated = db.Column(db.Boolean, default=False)

    def is_active(self):
        """True, as all users are active."""
        return True

    def get_id(self):
        """Return the email address to satisfy Flask-Login's requirements."""
        return self.email

    def is_authenticated(self):
        """Return True if the user is authenticated."""
        return self.authenticated

    def is_anonymous(self):
        """False, as anonymous users aren't supported."""
        return False







