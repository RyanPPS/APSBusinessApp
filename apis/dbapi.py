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
class ProductTable(object):

    def __init__(self):
        self.session = db.session()

    def search_by_price(wildcard_manufacturer, price_low, price_high):
        products = self.session.query(Product).filter(
            Product.manufacturer.ilike(wildcard_manufacturer), 
            Product.primary_cost >= price_low, Product.primary_cost <= price_high
        ).all()
        return products


    def search_by_upc(upc):
        products = self.session.query(Product).filter(Product.upc == upc)
        product = products.first()
        return product

    def search_by_manufacturer(manufacturer):
        products = self.session.query(Product).filter(
            Product.manufacturer == manufacturer
        ).all()
        return products

# Catalog Table
class CatalogTable(object):


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
