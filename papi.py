# papi is an acronym for MWS's Product API. 
# Receives a dictWrapper of the MWS response.
# For each response take the listings and products.
from utils import dictHelper

class Papi(object):
    """A papi takes in a response from Amazon's mws product api.

    :attribute dict response: _mydict (dictWrapper) of response
    :attribute dict _products: Product objects associated with this response
    :attribute list _listings: Listing objects associated with this response
    """

    def __init__(self, response):
        self.response = response
        self._products = {}
        self._listings = []
        # Auto populates _products and _listings
        self.make_products_and_listings()


    def make_products_and_listings(self):
        """Makes Listing and Product objects.
        Auto populate _listings and _products.
        Calls _listings_and_products()
        """
        dlistings, dproducts = self._listings_and_products()
        self._make_listings(dlistings, dproducts)
        self._make_products(dproducts)

    def _make_products(self, dproducts):
        for asin, vals in dproducts.items():
            self._products[asin] = Product(
                asin, vals['listings'], 
                vals['lowest_price'], 
                vals['shipping'],
                vals['lowest_fba_price']
            )

    def _make_listings(self, dlistings, dproducts):
        for asin, vals in dlistings.items():
            listing = Listing(
                asin, 
                vals['price'], 
                vals['shipping'], 
                vals['seller'], 
                vals['lowest_price']
            )
            self._listings.append(listing)
            dproducts[asin]['listings'].append(listing)


    @property 
    def products(self):
        """:return list self._products:"""
        return self._products

    @property
    def listings(self):
        """:return list self._listings:"""
        return self._listings
    
    def _listings_and_products(self):
        dlistings = {}
        dproducts = {}
        self.populate_listings_and_products(dlistings, dproducts)
        return dlistings, dproducts

    def init_listing_and_product(self, asin, listings, products):
        listings[asin] = { 
            'price':'',
            'shipping': '',
            'seller': '',
            'lowest_price': False
        }
        products[asin] = { 
            'listings': [],
            'lowest_price': '',
            'shipping': '',
            'lowest_fba_price': ''
        }

    def populate_listing_and_product(self, current_listing, current_product, lowest_offer_listing):
        lowest_fba_seller_found = False
        for i, listing in enumerate(lowest_offer_listing):
            current_listing['price'] = self.retrieve_price(listing)
            current_listing['shipping'] = self.retrieve_shipping_price(listing)
            current_listing['seller'] = self.retrieve_seller(listing)
            # First listing will be the lowest.
            if i == 0:
                self.set_lowest_price(current_listing, current_product)
            if not lowest_fba_seller_found and current_listing['seller'] == 'Amazon':
                self.set_lowest_fba_price(current_listing, current_product)
                lowest_fba_seller_found = True

    def populate_listings_and_products(self, listings, products):
        """Make a dictionaries out of the listings/products in the response

        :return dict dlistings: dictionary of Listing objects.
        :return dict dproducts: dictionary of Product objects.
        """
        for product in self._retrieve_products_from_response():
            lowest_offer_listing = self.actual_listing(product)
            if lowest_offer_listing is False or not product:
                # this is an empty listing
                continue
            asin = product['Identifiers']['MarketplaceASIN']['ASIN']['value']
            self.init_listing_and_product(asin, listings, products)
            self.populate_listing_and_product(listings[asin], products[asin], lowest_offer_listing)

    def set_lowest_price(self, current_listing, current_product):
        current_listing['lowest_price'] = True
        current_product['lowest_price'] = current_listing['price']

    def set_lowest_fba_price(self, current_listing, current_product):
        current_product['lowest_fba_price'] = current_listing['price']

    def _retrieve_products_from_response(self):
        """Search for all values of Product dict in self.response.

        :return obj: values associated with Product key in self.response
        """
        product = self.dictsearch(self.response, 'Product')
        return product


    def actual_listing(self, listing):
        try:
            return self.dictsearch(listing, 'LowestOfferListing')[0]
        except:
            return False
        
    def retrieve_price(self, listing):
        try:
            price = self.dictsearch(listing, 'LandedPrice')
            if price:
                return price[0]['Amount']['value']  
        except:
            print("Unable to find price. {0}")
            return 0.0

    def retrieve_shipping_price(self, listing):
        try:
            shipping = self.dictsearch(listing, 'Shipping')
            if shipping:
                return shipping[0]['Amount']['value']
        except:
            print("Unable to find shipping price.")
            return 0.0

    def retrieve_seller(self, listing):
        try:
            seller = self.dictsearch(listing, 'FulfillmentChannel')
            if seller:
                return seller[0]['value'] 
        except:
            print("Unable to find price.")
        return None

    def dictsearch(self, obj, key):
        """Recursively searches through a *obj* for *key*
        dictHelper() is a custom utility class that helps target keys
        in nested dicts much easier.

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


    def get_cheapest_seller(self):
        seller = None
        # TODO: find a more efficient way for the below code.
        for listing in self.listings:
            if listing.lowest_price:
                seller = listing.seller
        return seller 

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









