from models import Listing, Image, User, Product, Result, Company, Catalog, db

def listing_exists(asin):
    try:
        listing = Listing.query.filter_by(asin=asin).first()
    except:
        listing = None

    if listing:
        return True
    else:
        return False


def image_exists(asin):
    try:
        image = Image.query.filter_by(listing_asin=asin).first()
    except:
        image = None

    if image:
        return True
    else:
        return False


def add(item):
    db.session.add(item)
    db.session.commit()

def delete(item):
    db.session.delete(item)
    db.session.commit()

# Product Table
class productTable(object):

    def __init__(self):
        self.session = db.session()

    def search_by_price(self, lprice, hprice, manufacturer=None):
        if manufacturer:
            products = self.session.query(Product).filter(
                Product.manufacturer.ilike(manufacturer),
                Product.primary_cost >= lprice,
                Product.primary_cost <= hprice
            ).all()
        else:
            products = self.session.query(Product).filter(
                Product.primary_cost >= lprice,
                Product.primary_cost <= hprice
            ).all()
        return products


    def search_by_upc(self, upc):
        products = self.session.query(Product).filter(Product.upc == upc)
        product = products.first()
        return product

    def search_by_manufacturer(self, manufacturer):
        products = self.session.query(Product).filter(
            Product.manufacturer == manufacturer
        ).all()
        return products

# Catalog Table
class catalogTable(object):


    def __init__(self):
        self.session = db.session()

def search_by_sku(sku):
    product = db.session().query(Catalog).filter(Catalog.sku).first()
    return product

# Company Table
def get_companies():
    companies = db.session().query(Company).all()
    return companies


def get_user(info):
    user = User.query.get(info)
    return user
