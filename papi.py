# papi is an acronym for MWS's Product API. 
# Receives a dictWrapper of the MWS response.
# For each response take the listings and products.
from utils import dsearch
from pprint import pprint

class PAPI(object):
    """A papi takes in a response from Amazon's mws product api.

    :attribute DictWrapper response: a parsed response 
    :attribute dict _products: Product objects associated with this response
    """

    def __init__(self, response):
        self.response = response
        self._products = {}

    def _make_listings(self, asin, product):
        return [
            Listing(
                asin=asin, 
                price=self.get_price_from_listing(offering), 
                seller=self.get_seller_from_listing(offering)
            ) for offering in self.get_offerings_from_product(product)
        ]

    def make_products(self):
        for product in self.get_products_from_response():
            try:
                asin = self.get_asin_from_product(product)
                listings = self._make_listings(asin, product)
            except KeyError:
                # ASINs are required to create Products and Listings
                # Listings although not required to create Products,
                # without them Products are just asins if they exists
                print('Unable to find offerings or asin')
                continue
            lowest_price, lowest_fba_price = self.lowest_prices(listings)
            self._products[asin] = Product(
                asin=asin, 
                lowest_price=lowest_price, 
                lowest_fba_price=lowest_fba_price,
                listings=listings
            )

    def lowest_prices(self, listings):
        lowp = None
        lowfbap = None      
        for listing in listings:
            lp = listing.price
            if lp < lowp or lowp is None:
                lowp = lp
            if listing.seller == "Amazon" and (lp < lowfbap or lowfbap is None):
                lowfbap = lp
        self._set_cheapest_listing(listings, lowp)
        return lowp, lowfbap

    def _set_cheapest_listing(self, listings, lowestprice):
        for listing in listings:
            if listing.price == lowestprice:
                listing.cheapest = True

    def get_products_from_response(self):
        if isinstance(self.response, dict):
            return [dsearch(self.response, 'Product')]
        else:
            return [dsearch(item, 'Product') for item in self.response]

    def get_asin_from_product(self, product):
        try:
            return dsearch(product, 'ASIN')[0]['value']
        except IndexError as e:
            raise KeyError("ASIN doesn't exist")
        
    def get_price_from_listing(self, listing):
        try:
            return float(dsearch(listing, 'LandedPrice')[0]['Amount']['value'])
        except ValueError:
            return dsearch(listing, 'LandedPrice')[0]['Amount']['value']
        except (KeyError, IndexError):
            return None

    def get_seller_from_listing(self, listing):
        try:
            return dsearch(listing, 'FulfillmentChannel')[0]['value']
        except (KeyError, IndexError):
            return None
        
    def get_offerings_from_product(self, product):
        offerings = dsearch(product, 'LowestOfferListing')
        try:
            if isinstance(offerings[0], list):
                return offerings[0]
            else:
                return offerings
        except IndexError as e:
            raise KeyError('Offerrings not found.')

    @property
    def products(self):
        return self._products
    

class Product(object):
    """Product from the Amazon MWS Products API

    :attribute string asin: Amazon unique identifier for a product
    :attribute list _listings: Listings associated with Product
    :attribute string _lowest_price: Lowest price of Product
    :attribute string _shipping: Shipping price of Product for *_lowest_price*
    :attribute string _lowest_fba_price: Lowest FBA price of Product if available
    """

    def __init__(self, asin, listings=None, 
                lowest_price=None, lowest_fba_price=None):
        self._asin = asin
        self._listings = listings
        self._lowest_price = lowest_price
        self._lowest_fba_price = lowest_fba_price

    def get_cheapest_seller(self):
        return [
            listing.seller if listing.seller else None 
            for listing in self.listings
        ][0]

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


class Listing(object):
    """A listing of a product from the Amazon MWS Products API

    :attribute string asin: Amazon unique identifier for a product
    :attribute string _price: price of product for this Listing
    :attribute string _seller: Seller for this listing (merchant or amazon)
    :attribute bool _lowest_price: Is this the lowest price for this asin?
    :attribute string _seller_rating: the seller's feedback rating
    """

    def __init__(self, asin, price=None, seller=None, cheapest=None):
        self._asin = asin
        self._price = price
        self._seller = seller
        self._cheapest = cheapest

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
    def cheapest(self):
        return self._cheapest
    
    @cheapest.setter
    def cheapest(self, value):
        self._cheapest = value

    @property
    def foo(self):
        return self._foo
    

    @property
    def seller(self):
        return self._seller









