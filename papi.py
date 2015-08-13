# papi is an acronym for MWS's Product API. 
# Receives a dictWrapper of the MWS response.
# For each response take the listings and products.
from utils import dictHelper

class Papi(object):
    """A papi takes in a response from Amazon's mws product api.

    :attribute dict response: _mydict (dictWrapper) of response
    :attribute list _products: Product objects associated with this response
    :attribute list _listings: Listing objects associated with this response
    """

    def __init__(self, response):
        self.response = response
        self._products = []
        self._listings = []
        #Auto populates _products and _listings
        self.make_products_and_listings()


    
    def make_products_and_listings(self):
        """Makes Listing and Product objects.
        Auto populate _listings and _products.
        Calls _retrieve_listings_and_products()
        """
        dlistings, dproducts = self._retrieve_listings_and_products()
        for asin, vals in dlistings.items():
            tlisting = Listing(asin, vals['price'], vals['shipping'], 
                                vals['seller'], vals['lowest_price'])
            self._listings.append(tlisting)
            dproducts[asin]['listings'].append(tlisting)
        for asin, vals in dproducts.items():
            self._products.append(Product(asin, vals['listings'], 
                                    vals['lowest_price'], 
                                    vals['shipping'],
                                    vals['lowest_fba_price']))

    @property 
    def products(self):
        """:return list self._products:"""
        return self._products

    @property
    def listings(self):
        """:return list self._listings:"""
        return self._listings
    


    def _retrieve_products_from_response(self):
        """Search for all values of Product dict in self.response.

        :return obj: values associated with Product key in self.response
        """
        return self._safe_dsearch(self.response, 'Product')

    def _retrieve_listings_and_products(self):
        """Make a dictionary out of the listings in the response

        :return dict dlistings: dictionary of Listing objects.
        :return dict dproducts: dictionary of Product objects.
        """
        dlistings = {}
        dproducts = {}
        for product in self._retrieve_products_from_response():
            if not product:
                continue
            asin = product['Identifiers']['MarketplaceASIN']['ASIN']['value']
            dproducts[asin] = { 'listings': [],
                                'lowest_price': '',
                                'shipping': '',
                                'lowest_fba_price': ''}
            dlistings[asin] = { 'price':'',
                                'shipping': '',
                                'seller': '',
                                'lowest_price': False}
            current_product = dproducts[asin]
            current_listing = dlistings[asin]
            try:
                lowest_offer_listing = self._safe_dsearch(product, 'LowestOfferListing')[0]
            except:
                # this is an empty listing
                continue
            lowest_fba_seller_found = False
            for i, listing in enumerate(lowest_offer_listing):
                try:
                    price = self._safe_dsearch(listing, 'LandedPrice')
                    if price:
                        current_listing['price'] = price[0]['Amount']['value']
                    else:
                        # This was an empty list and a listing with no information.
                        # TODO: Find out why we receive empty listings.
                        pass   
                except:
                    print("Unable to find price. {0}".format(self._safe_dsearch(listing, 'LandedPrice')))
                try:
                    shipping = self._safe_dsearch(listing, 'Shipping')
                    if shipping:
                        current_listing['shipping'] = shipping[0]['Amount']['value']
                    else:
                        # This was an empty list and a listing with no information.
                        # TODO: Find out why we receive empty listings.
                        pass   
                except:
                    print("Unable to find shipping. {0}".format(self._safe_dsearch(listing, 'Shipping')))
                try:
                    seller = self._safe_dsearch(listing, 'FulfillmentChannel')
                    if seller:
                        current_listing['seller'] = seller[0]['value']
                    else:
                        # This was an empty list and a listing with no information.
                        # TODO: Find out why we receive empty listings.
                        pass   
                except:
                    print("Unable to find price. {0}".format(self._safe_dsearch(listing, 'FulFillmentChannel')))
                # First listing will be the lowest.
                if i == 0:
                    current_listing['lowest_price'] = True
                    current_product['lowest_price'] = current_listing['price']
                if not lowest_fba_seller_found and current_listing['seller'] == 'Amazon':
                    current_product['lowest_fba_price'] = current_listing['price']
                    lowest_fba_seller_found = True

        return dlistings, dproducts

    
    def _safe_dsearch(self, obj, key):
        """Recursively searches through a *obj* for *key*
        dictHelper() is a custom utility class that helps target keys
        in dicts much easier.

        return object: values associated with *key* in *obj*.
        """
        dh = dictHelper()
        return dh.dsearch(obj, key)







class Product(object):
    """Product from the Amazon MWS Products API

    :attribute string asin: Amazon unique identifier for a product
    :attribute list _listings: Listings associated with Product
    :attribute string _lowest_price: Lowest price of Product
    :attribute string _shipping: Shipping price of Product for *_lowest_price*
    :attribute string _lowest_fba_price: Lowest FBA price of Product if available
    """

    def __init__(self, asin, listings=None, lowest_price=None, 
                 shipping=None, lowest_fba_price=None):
        self._asin = asin
        self._listings = listings
        self._lowest_price = lowest_price
        self._shipping = shipping
        self._lowest_fba_price = lowest_fba_price



    @property
    def asin(self):
        """ASIN (Amazon ID)

        :return string asin:
        """
        return self._asin

    @property
    def listings(self):
        """Listings associated with Product

        :return list _listings
        """
        return self._listings

    @property
    def lowest_price(self):
        """Lowest price of Product
        
        :return string _lowest_price
        """
        return self._lowest_price

    @property
    def lowest_fba_price(self):
        """Lowest FBA price of Product
        
        :return list _lowest_fba_price
        """
        return self._lowest_fba_price

    @property
    def shipping(self):
        """Shipping price of Product
        
        :return list _shipping
        """
        return self._shipping
    

    


class Listing(object):
    """A listing of a product from the Amazon MWS Products API

    :attribute string asin: Amazon unique identifier for a product
    :attribute string _price: price of product for this Listing
    :attribute string _shipping: Shipping price of Product for *_lowest_price*
    :attribute string _seller: Seller for this listing (merchant or amazon)
    :attribute bool _lowest_price: Is this the lowest price for this asin?
    :attribute string _seller_rating: the seller's feedback rating
    """


    def __init__(self, asin, price=None, shipping=None, seller=None, 
                lowest_price=None, seller_rating=None):
        self._asin = asin
        self._price = price
        self._shipping = shipping
        self._seller = seller
        self._lowest_price = lowest_price
        self._seller_rating = seller_rating

    @property
    def asin(self):
        """ASIN (Amazon ID)

        :return string asin:
        """
        return self._asin

    @property
    def price(self):
        """
        """
        return self._price

    @property
    def shipping(self):
        return self._shipping

    @property
    def lowest_price(self):
        return self._lowest_price

    @property
    def seller(self):
        return self._seller









