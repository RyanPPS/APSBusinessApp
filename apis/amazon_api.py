

import os
from pprint import pprint
from amazon.api import AmazonAPI, AmazonProduct
from mws import mws
# Amazon Product Advertising API
paapi = AmazonAPI(
    os.environ['AMAZON_ACCESS_KEY'], 
    os.environ['AMAZON_SECRET_KEY'], 
    os.environ['AMAZON_ASSOC_TAG']
)

mws_marketplace = os.environ['MWS_MARKETPLACE_ID']

mws_credentials = {
    'access_key': os.environ['MWS_AWS_ACCESS_KEY_ID'],
    'seller_id': os.environ['MWS_SELLER_ID'],
    'secret_key': os.environ['MWS_SECRET_KEY']
}
product_mws = mws.Products(
    access_key=mws_credentials['access_key'], 
    account_id=mws_credentials['seller_id'], 
    secret_key=mws_credentials['secret_key']
)

def product_lookup(search_by, user_input):
    """Handle requests for Amazon's Product Advertising API (PAAPI) 
    product lookup.
    
    :param str search_by: earch by Criteria UPC or ASIN.
    :param str user_input: upc(s)/asin(s).
    """
    if search_by == 'UPC':
        products = paapi.lookup(
            ItemId=user_input, IdType=search_by, SearchIndex='LawnAndGarden'
        )
    elif search_by == 'ASIN':
        products = paapi.lookup(ItemId=user_input, IdType=search_by)
    else:
        products = None
    return products


def products_search(manufacturer):
    """Handle requests for Amazon's Product Advertising API (PAAPI) 
    product search.
    
    :param str manufacturer: the manufacturer to search for.
    """
    return paapi.search(SearchIndex='LawnAndGarden', Manufacturer=manufacturer)


def get_lowest_offer_listings_for_asin(asins):
    if isinstance(asins, list):
        result = product_mws.get_lowest_offer_listings_for_asin(
            mws_marketplace, asins, condition='New'
        )
    else:
        result = product_mws.get_lowest_offer_listings_for_asin(
            mws_marketplace, [asins], condition='New'
        )
    return result

def get_my_price_for_asin(asin):
    if isinstance(asin, list):
        result = product_mws.get_lowest_offer_listings_for_asin(
            mws_marketplace, asin, condition='New'
        )
    else:
        result = product_mws.get_lowest_offer_listings_for_asin(
            mws_marketplace, [asin], condition='New'
        )
    return result
