
import os
from amazon.api import AmazonAPI, AmazonProduct
from mws import mws
paapi_conn = AmazonAPI(
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
mws_conn = mws.Products(
    access_key=mws_credentials['access_key'], 
    account_id=mws_credentials['seller_id'], 
    secret_key=mws_credentials['secret_key']
)

def paapi_lookup(search_by, user_input):
    """Handle requests for Amazon's Product Advertising API (PAAPI) 
    product lookup.
    
    :param str search_by: earch by Criteria UPC or ASIN.
    :param str user_input: upc(s)/asin(s).
    """
    products = None
    if search_by == 'UPC':
        products = paapi_conn.lookup(
            ItemId=user_input, IdType=search_by, SearchIndex='LawnAndGarden'
        )
    elif search_by == 'ASIN':
        products = paapi_conn.lookup(ItemId=user_input, IdType=search_by)
    return products


def paapi_search(manufacturer):
    """Handle requests for Amazon's Product Advertising API (PAAPI) 
    product search.
    
    :param str manufacturer: the manufacturer to search for.
    """
    return paapi_conn.search(SearchIndex='LawnAndGarden', Manufacturer=manufacturer)


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
