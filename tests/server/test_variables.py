"""
Product ->
  ASIN: string
  lowest_price: float
  lowest_fba_price: float
  listings: list

Listing ->
  ASIN: string
  landed_price: float
  merchant: string
  lowest_price: bool

PAPI ->
Takes in a response.parsed
  this gives us a list of dicts. We retrieve the Product dict from each.
  So we have a list of product dicts. Now we must convert each product dict
  into product objects and listing objects. 
  There will be one product for each product dict and multiple listings
  Also PAPI has Products. Products have Listings. PAPIs have listings indirectly through
  Products.

  methods:
  _make_listings(asin, product): 
    return [
      Listing(asin, get_landed_price(offering), get_merchant(offering))
      for offering in get_offerings(product)
    ]

  make_products():
    for product in get_products():
      asin = get_asin(product)
      listings = _make_listings(asin, product)
      lowest_price = 999999999.99
      lowest_fba_price = 99999999.99
      for listing in listings:
        if listing.price < lowest_price:
          lowest_price = listing.price
        if listing.fba_price < lowest_fba_price:
          lowest_fba_price = listing.fba_price
      self.products.append(Product(asin, lowest_price, lowest_fba_price, listings))



  get_products(): return [dsearch(item, 'Product') for item in self.response]
  get_asin_from_product(product): return dsearch(product, 'asin')
  get_price_from_listing(listing): return dsearch(listing, 'landed_price')
  get_merchant_from_listing(listing): return dsearch(listing, 'FulfillmentChannel')
  get_offerings_from_product(product): return dsearch(product, 'MultipleOffersAtLowestPrice')

"""

UPCS = [
    '811636026407', '811636024281', 
    '011670112474', '811636024274',
    '811636024281', '811636024304', 
    '811636020528', '811636022799'
]

ASINS = [
    'B00BY5RWRY', 'B00HEATXLG', 
    'B00HEAUAE0', 'B00KHUJUA4',
    'B00KUP84L2', 'B00LAGMOGG',
    'B00M2AH2LG', 'B00M2AL91U'
]
PROBLEM_ASINS = ['B00M29ZO2G']
TEST_PRODUCT_EMPTY = {'Identifiers': {'MarketplaceASIN': {'ASIN': {'value': 'B00HU5L3OK'}, 'MarketplaceId': {'value': 'ATVPDKIKX0DER'}}}, 'LowestOfferListings': {}}
TEST_RESPONSE_SM = {'status': {'value': 'Success'}, 'ASIN': {'value': 'B00M2ALI02'}, 'AllOfferListingsConsidered': {'value': 'true'}, 'Product': {'Identifiers': {'MarketplaceASIN': {'ASIN': {'value': 'B00M2ALI02'}, 'MarketplaceId': {'value': 'ATVPDKIKX0DER'}}}, 'LowestOfferListings': {'LowestOfferListing': {'MultipleOffersAtLowestPrice': {'value': 'False'}, 'Price': {'LandedPrice': {'CurrencyCode': {'value': 'USD'}, 'Amount': {'value': '15.99'}}, 'ListingPrice': {'CurrencyCode': {'value': 'USD'}, 'Amount': {'value': '15.99'}}, 'Shipping': {'CurrencyCode': {'value': 'USD'}, 'Amount': {'value': '0.00'}}}, 'NumberOfOfferListingsConsidered': {'value': '1'}, 'Qualifiers': {'SellerPositiveFeedbackRating': {'value': '98-100%'}, 'ItemSubcondition': {'value': 'New'}, 'FulfillmentChannel': {'value': 'Amazon'}, 'ShipsDomestically': {'value': 'True'}, 'ItemCondition': {'value': 'New'}, 'ShippingTime': {'Max': {'value': '0-2 days'}}}, 'SellerFeedbackCount': {'value': '187'}}}}}

TEST_RESPONSE = [{'ASIN': {'value': 'B00KUP84L2'},
  'AllOfferListingsConsidered': {'value': 'true'},
  'Product': {'Identifiers': {'MarketplaceASIN': {'ASIN': {'value': 'B00KUP84L2'},
                                                  'MarketplaceId': {'value': 'ATVPDKIKX0DER'}}},
              'LowestOfferListings': {'LowestOfferListing': [{'MultipleOffersAtLowestPrice': {'value': 'False'},
                                                              'NumberOfOfferListingsConsidered': {'value': '2'},
                                                              'Price': {'LandedPrice': {'Amount': {'value': '17.99'},
                                                                                        'CurrencyCode': {'value': 'USD'}},
                                                                        'ListingPrice': {'Amount': {'value': '17.99'},
                                                                                         'CurrencyCode': {'value': 'USD'}},
                                                                        'Shipping': {'Amount': {'value': '0.00'},
                                                                                     'CurrencyCode': {'value': 'USD'}}},
                                                              'Qualifiers': {'FulfillmentChannel': {'value': 'Amazon'},
                                                                             'ItemCondition': {'value': 'New'},
                                                                             'ItemSubcondition': {'value': 'New'},
                                                                             'SellerPositiveFeedbackRating': {'value': '98-100%'},
                                                                             'ShippingTime': {'Max': {'value': '0-2 days'}},
                                                                             'ShipsDomestically': {'value': 'True'}},
                                                              'SellerFeedbackCount': {'value': '187'}},
                                                             {'MultipleOffersAtLowestPrice': {'value': 'False'},
                                                              'NumberOfOfferListingsConsidered': {'value': '1'},
                                                              'Price': {'LandedPrice': {'Amount': {'value': '21.39'},
                                                                                        'CurrencyCode': {'value': 'USD'}},
                                                                        'ListingPrice': {'Amount': {'value': '16.40'},
                                                                                         'CurrencyCode': {'value': 'USD'}},
                                                                        'Shipping': {'Amount': {'value': '4.99'},
                                                                                     'CurrencyCode': {'value': 'USD'}}},
                                                              'Qualifiers': {'FulfillmentChannel': {'value': 'Merchant'},
                                                                             'ItemCondition': {'value': 'New'},
                                                                             'ItemSubcondition': {'value': 'New'},
                                                                             'SellerPositiveFeedbackRating': {'value': '98-100%'},
                                                                             'ShippingTime': {'Max': {'value': '0-2 days'}},
                                                                             'ShipsDomestically': {'value': 'True'}},
                                                              'SellerFeedbackCount': {'value': '3'}},
                                                             {'MultipleOffersAtLowestPrice': {'value': 'False'},
                                                              'NumberOfOfferListingsConsidered': {'value': '1'},
                                                              'Price': {'LandedPrice': {'Amount': {'value': '22.98'},
                                                                                        'CurrencyCode': {'value': 'USD'}},
                                                                        'ListingPrice': {'Amount': {'value': '22.98'},
                                                                                         'CurrencyCode': {'value': 'USD'}},
                                                                        'Shipping': {'Amount': {'value': '0.00'},
                                                                                     'CurrencyCode': {'value': 'USD'}}},
                                                              'Qualifiers': {'FulfillmentChannel': {'value': 'Merchant'},
                                                                             'ItemCondition': {'value': 'New'},
                                                                             'ItemSubcondition': {'value': 'New'},
                                                                             'SellerPositiveFeedbackRating': {'value': '95-97%'},
                                                                             'ShippingTime': {'Max': {'value': '0-2 days'}},
                                                                             'ShipsDomestically': {'value': 'True'}},
                                                              'SellerFeedbackCount': {'value': '9077'}}]}},
  'status': {'value': 'Success'}},
 {'ASIN': {'value': 'B00HEATHXK'},
  'AllOfferListingsConsidered': {'value': 'true'},
  'Product': {'Identifiers': {'MarketplaceASIN': {'ASIN': {'value': 'B00HEATHXK'},
                                                  'MarketplaceId': {'value': 'ATVPDKIKX0DER'}}},
              'LowestOfferListings': {'LowestOfferListing': [{'MultipleOffersAtLowestPrice': {'value': 'False'},
                                                              'NumberOfOfferListingsConsidered': {'value': '1'},
                                                              'Price': {'LandedPrice': {'Amount': {'value': '15.99'},
                                                                                        'CurrencyCode': {'value': 'USD'}},
                                                                        'ListingPrice': {'Amount': {'value': '15.99'},
                                                                                         'CurrencyCode': {'value': 'USD'}},
                                                                        'Shipping': {'Amount': {'value': '0.00'},
                                                                                     'CurrencyCode': {'value': 'USD'}}},
                                                              'Qualifiers': {'FulfillmentChannel': {'value': 'Merchant'},
                                                                             'ItemCondition': {'value': 'New'},
                                                                             'ItemSubcondition': {'value': 'New'},
                                                                             'SellerPositiveFeedbackRating': {'value': '95-97%'},
                                                                             'ShippingTime': {'Max': {'value': '0-2 days'}},
                                                                             'ShipsDomestically': {'value': 'True'}},
                                                              'SellerFeedbackCount': {'value': '9077'}},
                                                             {'MultipleOffersAtLowestPrice': {'value': 'False'},
                                                              'NumberOfOfferListingsConsidered': {'value': '2'},
                                                              'Price': {'LandedPrice': {'Amount': {'value': '16.00'},
                                                                                        'CurrencyCode': {'value': 'USD'}},
                                                                        'ListingPrice': {'Amount': {'value': '16.00'},
                                                                                         'CurrencyCode': {'value': 'USD'}},
                                                                        'Shipping': {'Amount': {'value': '0.00'},
                                                                                     'CurrencyCode': {'value': 'USD'}}},
                                                              'Qualifiers': {'FulfillmentChannel': {'value': 'Merchant'},
                                                                             'ItemCondition': {'value': 'New'},
                                                                             'ItemSubcondition': {'value': 'New'},
                                                                             'SellerPositiveFeedbackRating': {'value': '90-94%'},
                                                                             'ShippingTime': {'Max': {'value': '0-2 days'}},
                                                                             'ShipsDomestically': {'value': 'True'}},
                                                              'SellerFeedbackCount': {'value': '2209'}},
                                                             {'MultipleOffersAtLowestPrice': {'value': 'False'},
                                                              'NumberOfOfferListingsConsidered': {'value': '2'},
                                                              'Price': {'LandedPrice': {'Amount': {'value': '16.99'},
                                                                                        'CurrencyCode': {'value': 'USD'}},
                                                                        'ListingPrice': {'Amount': {'value': '16.99'},
                                                                                         'CurrencyCode': {'value': 'USD'}},
                                                                        'Shipping': {'Amount': {'value': '0.00'},
                                                                                     'CurrencyCode': {'value': 'USD'}}},
                                                              'Qualifiers': {'FulfillmentChannel': {'value': 'Amazon'},
                                                                             'ItemCondition': {'value': 'New'},
                                                                             'ItemSubcondition': {'value': 'New'},
                                                                             'SellerPositiveFeedbackRating': {'value': '98-100%'},
                                                                             'ShippingTime': {'Max': {'value': '0-2 days'}},
                                                                             'ShipsDomestically': {'value': 'True'}},
                                                              'SellerFeedbackCount': {'value': '187'}},
                                                             {'MultipleOffersAtLowestPrice': {'value': 'False'},
                                                              'NumberOfOfferListingsConsidered': {'value': '1'},
                                                              'Price': {'LandedPrice': {'Amount': {'value': '27.87'},
                                                                                        'CurrencyCode': {'value': 'USD'}},
                                                                        'ListingPrice': {'Amount': {'value': '21.32'},
                                                                                         'CurrencyCode': {'value': 'USD'}},
                                                                        'Shipping': {'Amount': {'value': '6.55'},
                                                                                     'CurrencyCode': {'value': 'USD'}}},
                                                              'Qualifiers': {'FulfillmentChannel': {'value': 'Merchant'},
                                                                             'ItemCondition': {'value': 'New'},
                                                                             'ItemSubcondition': {'value': 'New'},
                                                                             'SellerPositiveFeedbackRating': {'value': '98-100%'},
                                                                             'ShippingTime': {'Max': {'value': '0-2 days'}},
                                                                             'ShipsDomestically': {'value': 'True'}},
                                                              'SellerFeedbackCount': {'value': '556'}}]}},
  'status': {'value': 'Success'}},
 {'ASIN': {'value': 'B00KURKYTK'},
  'AllOfferListingsConsidered': {'value': 'true'},
  'Product': {'Identifiers': {'MarketplaceASIN': {'ASIN': {'value': 'B00KURKYTK'},
                                                  'MarketplaceId': {'value': 'ATVPDKIKX0DER'}}},
              'LowestOfferListings': {'LowestOfferListing': {'MultipleOffersAtLowestPrice': {'value': 'False'},
                                                             'NumberOfOfferListingsConsidered': {'value': '1'},
                                                             'Price': {'LandedPrice': {'Amount': {'value': '26.79'},
                                                                                       'CurrencyCode': {'value': 'USD'}},
                                                                       'ListingPrice': {'Amount': {'value': '21.80'},
                                                                                        'CurrencyCode': {'value': 'USD'}},
                                                                       'Shipping': {'Amount': {'value': '4.99'},
                                                                                    'CurrencyCode': {'value': 'USD'}}},
                                                             'Qualifiers': {'FulfillmentChannel': {'value': 'Merchant'},
                                                                            'ItemCondition': {'value': 'New'},
                                                                            'ItemSubcondition': {'value': 'New'},
                                                                            'SellerPositiveFeedbackRating': {'value': '98-100%'},
                                                                            'ShippingTime': {'Max': {'value': '0-2 days'}},
                                                                            'ShipsDomestically': {'value': 'True'}},
                                                             'SellerFeedbackCount': {'value': '3'}}}},
  'status': {'value': 'Success'}}]
