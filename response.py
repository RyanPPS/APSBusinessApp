from copy import deepcopy


class Response(object):
    
    __response_scheme = { 'sku': '',
                        'asin': '',
                        'part_number': '',
                        'title': '',
                        'features': '',
                        'sales_rank': '',
                        'price_and_currency': '',
                        'LowestNewPrice': '',
                        'list_price': '',
                        'offer_url': '',
                        'manufacturer': '',
                        'imagelist': {
                            'large_image_url': '',
                            'medium_image_url': '',
                            'small_image_url': '',
                            'tiny_image_url': '',
                        },
                        'brand': '',
                        'ean': '',
                        'upc': '',
                        'color': '',}


    def __init__(self):
        self._listings = {'products': {}}

    def populate_response(self, product):
        """Populate a listing with product attributes.

        param obj product: a product from amazon paapi
        param dict listing: dict representation of amazon listing
        """
        # configure the listings
        if product.asin:
            asin = product.asin
            self.push_product(asin)
            self.set_product_attributes(product)

    def push_product(self, asin):
        self.listings['products'][asin] = deepcopy(self.__response_scheme)

    def set_cost(self, asin, cost):
        self.listings['products'][asin]['cost'] = cost

    def set_seller(self, asin, seller):
        """Sellers are either Merchants or Amazon. 
        This identifies the fulfillment method. FBA or FBM

        :param obj asin: product sold on Amazon
        :param obj seller: seller associated with product
        """
        self.listings['products'][asin]['seller'] = seller
        
    def set_lowest_price_mws(self, asin, lowest_price):
        self.listings['products'][asin]['lowest_price'] = lowest_price
    
    def set_lowest_fba_price_mws(self, asin, lowest_fba_price):
        self.listings['products'][asin]['lowest_fba_price'] = lowest_fba_price

    def set_product_attributes(self, product):
        """Add product attributes to the listing.

        param obj product: a product from amazon paapi
        """
        listing = self.listings['products'][product.asin]
        for keyi in self.__response_scheme.keys():
            #TODO: Extend AmazonProduct class to include LowestNewPrice
            if keyi == 'LowestNewPrice':
                listing[keyi] = self.get_lowest_price_pa(product)
            elif isinstance(listing[keyi], dict):
                # images go in imagelist 
                for keyj in listing[keyi].keys():
                    try:
                        listing[keyi][keyj] = product.__getattribute__(keyj)
                    except:
                        print("Attribute {0} not found".format(keyj))
            else:
                try:
                    listing[keyi] = product.__getattribute__(keyi)
                except:
                    print("Attribute {0} not found".format(keyi))

    def get_lowest_price_pa(self, product):
        lowest_price = product._safe_get_element_text(
                    'OfferSummary.LowestNewlowest_price.Amount')
        if lowest_price:
            try:
                flowest_price = float(lowest_price) / 100 if 'JP' not in product.region else lowest_price
            except:
                flowest_price = lowest_price
        else:
            flowest_price = lowest_price
        return flowest_price

    
    @property
    def listings(self):
        return self._listings

    @property
    def products(self):
        return self.listings['products']




    

