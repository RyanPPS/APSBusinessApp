import os
from app import app
import unittest
import tempfile
from forms import LoginForm
from models import Result, Listing, Product, Image, User, Catalog


class testLogin():#unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.app = app.test_client()

    def tearDown(self):
        pass


    def test_login_logout(self):
        # test valid login.
        response = self.login('ryan@allpoolspa.com', os.environ['PASSWORD'])
        self.assertTrue('Home' in response.data)
        response = self.logout()
        self.assertTrue('logged out' in response.data)
        # test invalid username
        response = self.login('r@allpoolspa.com', os.environ['PASSWORD'])
        self.assertTrue('email' in response.data)
        # test invalid password
        response = self.login('ryan@allpoolspa.com', 'default')
        self.assertTrue('email' in response.data)


    def login(self, username, password):
        form = LoginForm(email=username, password=password)
        self.assertTrue(form.validate())
        return self.app.post(
            '/login', 
            data=dict(
                email=form.email.data,
                password=form.password.data
            ), 
            follow_redirects=True
        )

    def test_start(self):
        self.login('ryan@allpoolspa.com', os.environ['PASSWORD'])
        # test search by Manufacturer
        r1 = self.start('Hayward', 'Manufacturer')
        print(r1.status)
        """
        self.assertTrue(r1.status_code == 302)
        # test search by UPC
        upc_request = {uinput: '811636026407', searchby: 'UPC'}
        r2 = self.app.post(url, upc_request)
        self.assertTrue(r2.status_code == 302)
        # test search by ASIN
        asin_request = {uinput: 'B00BY5RWRY', searchby: 'ASIN'}
        r3 = self.app.post(url, asin_request)
        self.assertTrue(r3.status_code == 302)
        # test search by Price
        price_request = {
            uinput: 'B00BY5RWRY', searchby: 'ASIN',
            'low_price': 0.00, 'high_price':1.00
        }
        r4 = self.app.post(url, price_request)
        self.assertTrue(r4.status_code == 302)
        # test bad search
        bad_request = {uinput: '', searchby: 'ASIN'}
        r5 = self.app.post(url, bad_request)
        print(r5.status_code)
        #self.assertTrue(r5.status_code == 500)
        """

    def logout(self):
        return self.app.get('/logout', follow_redirects=True)

    def start(self, uinput, search_by, low_price=None, high_price=None):
        if low_price is None or high_price is None:
            return self.app.post(
                '/start',
                data=dict(
                    user_input=uinput,
                    search_by=search_by
                ),
                follow_redirects=True
            )
        else:
            return self.app.post(
                '/start',
                data=dict(
                    user_input=uinput,
                    search_by=search_by,
                    low_price=low_price,
                    high_price=high_price
                ),
                follow_redirects=True
            )



class testStart(unittest.TestCase):
    

    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.app = app.test_client()

    def tearDown(self):
        pass

    def login(self, username, password):
        form = LoginForm(email=username, password=password)
        self.assertTrue(form.validate())
        return self.app.post(
            '/login', 
            data=dict(
                email=form.email.data,
                password=form.password.data
            ), 
            follow_redirects=True
        )

    





upcs = [
    '811636026407', '811636024281', 
    '011670112474', '811636024274',
    '811636024281', '811636024304', 
    '811636020528', '811636022799'
]

asins = [
    'B00BY5RWRY', 'B00HEATXLG', 
    'B00HEAUAE0', 'B00KHUJUA4',
    'B00KUP84L2', 'B00LAGMOGG',
    'B00M2AH2LG', 'B00M2AL91U'
]

test_response = [{'Identifiers': {'MarketplaceASIN': {'ASIN': {'value': 'B000A4TDPO'}, 'MarketplaceId': {'value': 'ATVPDKIKX0DER'}}}, 'LowestOfferListings': {'LowestOfferListing': [{'MultipleOffersAtLowestPrice': {'value': 'False'}, 'Price': {'LandedPrice': {'CurrencyCode': {'value': 'USD'}, 'Amount': {'value': '25.14'}}, 'ListingPrice': {'CurrencyCode': {'value': 'USD'}, 'Amount': {'value': '25.14'}}, 'Shipping': {'CurrencyCode': {'value': 'USD'}, 'Amount': {'value': '0.00'}}}, 'NumberOfOfferListingsConsidered': {'value': '2'}, 'Qualifiers': {'SellerPositiveFeedbackRating': {'value': '98-100%'}, 'ItemSubcondition': {'value': 'New'}, 'FulfillmentChannel': {'value': 'Amazon'}, 'ShipsDomestically': {'value': 'True'}, 'ItemCondition': {'value': 'New'}, 'ShippingTime': {'Max': {'value': '0-2 days'}}}, 'SellerFeedbackCount': {'value': '439193'}}, {'MultipleOffersAtLowestPrice': {'value': 'False'}, 'Price': {'LandedPrice': {'CurrencyCode': {'value': 'USD'}, 'Amount': {'value': '25.99'}}, 'ListingPrice': {'CurrencyCode': {'value': 'USD'}, 'Amount': {'value': '25.99'}}, 'Shipping': {'CurrencyCode': {'value': 'USD'}, 'Amount': {'value': '0.00'}}}, 'NumberOfOfferListingsConsidered': {'value': '2'}, 'Qualifiers': {'SellerPositiveFeedbackRating': {'value': '95-97%'}, 'ItemSubcondition': {'value': 'New'}, 'FulfillmentChannel': {'value': 'Merchant'}, 'ShipsDomestically': {'value': 'True'}, 'ItemCondition': {'value': 'New'}, 'ShippingTime': {'Max': {'value': '0-2 days'}}}, 'SellerFeedbackCount': {'value': '93518'}}, {'MultipleOffersAtLowestPrice': {'value': 'False'}, 'Price': {'LandedPrice': {'CurrencyCode': {'value': 'USD'}, 'Amount': {'value': '30.25'}}, 'ListingPrice': {'CurrencyCode': {'value': 'USD'}, 'Amount': {'value': '30.25'}}, 'Shipping': {'CurrencyCode': {'value': 'USD'}, 'Amount': {'value': '0.00'}}}, 'NumberOfOfferListingsConsidered': {'value': '1'}, 'Qualifiers': {'SellerPositiveFeedbackRating': {'value': '98-100%'}, 'ItemSubcondition': {'value': 'New'}, 'FulfillmentChannel': {'value': 'Merchant'}, 'ShipsDomestically': {'value': 'Unknown'}, 'ItemCondition': {'value': 'New'}, 'ShippingTime': {'Max': {'value': '0-2 days'}}}, 'SellerFeedbackCount': {'value': '66460'}}, {'MultipleOffersAtLowestPrice': {'value': 'False'}, 'Price': {'LandedPrice': {'CurrencyCode': {'value': 'USD'}, 'Amount': {'value': '32.92'}}, 'ListingPrice': {'CurrencyCode': {'value': 'USD'}, 'Amount': {'value': '24.58'}}, 'Shipping': {'CurrencyCode': {'value': 'USD'}, 'Amount': {'value': '8.34'}}}, 'NumberOfOfferListingsConsidered': {'value': '1'}, 'Qualifiers': {'SellerPositiveFeedbackRating': {'value': '95-97%'}, 'ItemSubcondition': {'value': 'New'}, 'FulfillmentChannel': {'value': 'Merchant'}, 'ShipsDomestically': {'value': 'Unknown'}, 'ItemCondition': {'value': 'New'}, 'ShippingTime': {'Max': {'value': '8-13 days'}}}, 'SellerFeedbackCount': {'value': '199306'}}, {'MultipleOffersAtLowestPrice': {'value': 'False'}, 'Price': {'LandedPrice': {'CurrencyCode': {'value': 'USD'}, 'Amount': {'value': '35.87'}}, 'ListingPrice': {'CurrencyCode': {'value': 'USD'}, 'Amount': {'value': '26.72'}}, 'Shipping': {'CurrencyCode': {'value': 'USD'}, 'Amount': {'value': '9.15'}}}, 'NumberOfOfferListingsConsidered': {'value': '2'}, 'Qualifiers': {'SellerPositiveFeedbackRating': {'value': '98-100%'}, 'ItemSubcondition': {'value': 'New'}, 'FulfillmentChannel': {'value': 'Merchant'}, 'ShipsDomestically': {'value': 'True'}, 'ItemCondition': {'value': 'New'}, 'ShippingTime': {'Max': {'value': '0-2 days'}}}, 'SellerFeedbackCount': {'value': '506'}}]}}, {'Identifiers': {'MarketplaceASIN': {'ASIN': {'value': 'B000BNM25W'}, 'MarketplaceId': {'value': 'ATVPDKIKX0DER'}}}, 'LowestOfferListings': {'LowestOfferListing': [{'MultipleOffersAtLowestPrice': {'value': 'False'}, 'Price': {'LandedPrice': {'CurrencyCode': {'value': 'USD'}, 'Amount': {'value': '15.51'}}, 'ListingPrice': {'CurrencyCode': {'value': 'USD'}, 'Amount': {'value': '15.51'}}, 'Shipping': {'CurrencyCode': {'value': 'USD'}, 'Amount': {'value': '0.00'}}}, 'NumberOfOfferListingsConsidered': {'value': '1'}, 'Qualifiers': {'SellerPositiveFeedbackRating': {'value': '98-100%'}, 'ItemSubcondition': {'value': 'New'}, 'FulfillmentChannel': {'value': 'Amazon'}, 'ShipsDomestically': {'value': 'True'}, 'ItemCondition': {'value': 'New'}, 'ShippingTime': {'Max': {'value': '0-2 days'}}}, 'SellerFeedbackCount': {'value': '136614'}}, {'MultipleOffersAtLowestPrice': {'value': 'False'}, 'Price': {'LandedPrice': {'CurrencyCode': {'value': 'USD'}, 'Amount': {'value': '18.84'}}, 'ListingPrice': {'CurrencyCode': {'value': 'USD'}, 'Amount': {'value': '18.84'}}, 'Shipping': {'CurrencyCode': {'value': 'USD'}, 'Amount': {'value': '0.00'}}}, 'NumberOfOfferListingsConsidered': {'value': '1'}, 'Qualifiers': {'SellerPositiveFeedbackRating': {'value': '98-100%'}, 'ItemSubcondition': {'value': 'New'}, 'FulfillmentChannel': {'value': 'Merchant'}, 'ShipsDomestically': {'value': 'Unknown'}, 'ItemCondition': {'value': 'New'}, 'ShippingTime': {'Max': {'value': '0-2 days'}}}, 'SellerFeedbackCount': {'value': '66438'}}, {'MultipleOffersAtLowestPrice': {'value': 'False'}, 'Price': {'LandedPrice': {'CurrencyCode': {'value': 'USD'}, 'Amount': {'value': '20.94'}}, 'ListingPrice': {'CurrencyCode': {'value': 'USD'}, 'Amount': {'value': '15.95'}}, 'Shipping': {'CurrencyCode': {'value': 'USD'}, 'Amount': {'value': '4.99'}}}, 'NumberOfOfferListingsConsidered': {'value': '1'}, 'Qualifiers': {'SellerPositiveFeedbackRating': {'value': '90-94%'}, 'ItemSubcondition': {'value': 'New'}, 'FulfillmentChannel': {'value': 'Merchant'}, 'ShipsDomestically': {'value': 'True'}, 'ItemCondition': {'value': 'New'}, 'ShippingTime': {'Max': {'value': '0-2 days'}}}, 'SellerFeedbackCount': {'value': '9720'}}, {'MultipleOffersAtLowestPrice': {'value': 'False'}, 'Price': {'LandedPrice': {'CurrencyCode': {'value': 'USD'}, 'Amount': {'value': '21.04'}}, 'ListingPrice': {'CurrencyCode': {'value': 'USD'}, 'Amount': {'value': '12.95'}}, 'Shipping': {'CurrencyCode': {'value': 'USD'}, 'Amount': {'value': '8.09'}}}, 'NumberOfOfferListingsConsidered': {'value': '1'}, 'Qualifiers': {'SellerPositiveFeedbackRating': {'value': '95-97%'}, 'ItemSubcondition': {'value': 'New'}, 'FulfillmentChannel': {'value': 'Merchant'}, 'ShipsDomestically': {'value': 'Unknown'}, 'ItemCondition': {'value': 'New'}, 'ShippingTime': {'Max': {'value': '8-13 days'}}}, 'SellerFeedbackCount': {'value': '199305'}}, {'MultipleOffersAtLowestPrice': {'value': 'True'}, 'Price': {'LandedPrice': {'CurrencyCode': {'value': 'USD'}, 'Amount': {'value': '21.06'}}, 'ListingPrice': {'CurrencyCode': {'value': 'USD'}, 'Amount': {'value': '10.07'}}, 'Shipping': {'CurrencyCode': {'value': 'USD'}, 'Amount': {'value': '10.99'}}}, 'NumberOfOfferListingsConsidered': {'value': '2'}, 'Qualifiers': {'SellerPositiveFeedbackRating': {'value': '98-100%'}, 'ItemSubcondition': {'value': 'New'}, 'FulfillmentChannel': {'value': 'Merchant'}, 'ShipsDomestically': {'value': 'True'}, 'ItemCondition': {'value': 'New'}, 'ShippingTime': {'Max': {'value': '0-2 days'}}}, 'SellerFeedbackCount': {'value': '493'}}, {'MultipleOffersAtLowestPrice': {'value': 'False'}, 'Price': {'LandedPrice': {'CurrencyCode': {'value': 'USD'}, 'Amount': {'value': '28.62'}}, 'ListingPrice': {'CurrencyCode': {'value': 'USD'}, 'Amount': {'value': '24.00'}}, 'Shipping': {'CurrencyCode': {'value': 'USD'}, 'Amount': {'value': '4.62'}}}, 'NumberOfOfferListingsConsidered': {'value': '1'}, 'Qualifiers': {'SellerPositiveFeedbackRating': {'value': '98-100%'}, 'ItemSubcondition': {'value': 'New'}, 'FulfillmentChannel': {'value': 'Merchant'}, 'ShipsDomestically': {'value': 'True'}, 'ItemCondition': {'value': 'New'}, 'ShippingTime': {'Max': {'value': '3-7 days'}}}, 'SellerFeedbackCount': {'value': '147'}}]}}, {'Identifiers': {'MarketplaceASIN': {'ASIN': {'value': 'B000BNM27U'}, 'MarketplaceId': {'value': 'ATVPDKIKX0DER'}}}, 'LowestOfferListings': {'LowestOfferListing': [{'MultipleOffersAtLowestPrice': {'value': 'False'}, 'Price': {'LandedPrice': {'CurrencyCode': {'value': 'USD'}, 'Amount': {'value': '24.99'}}, 'ListingPrice': {'CurrencyCode': {'value': 'USD'}, 'Amount': {'value': '24.99'}}, 'Shipping': {'CurrencyCode': {'value': 'USD'}, 'Amount': {'value': '0.00'}}}, 'NumberOfOfferListingsConsidered': {'value': '2'}, 'Qualifiers': {'SellerPositiveFeedbackRating': {'value': '95-97%'}, 'ItemSubcondition': {'value': 'New'}, 'FulfillmentChannel': {'value': 'Merchant'}, 'ShipsDomestically': {'value': 'True'}, 'ItemCondition': {'value': 'New'}, 'ShippingTime': {'Max': {'value': '0-2 days'}}}, 'SellerFeedbackCount': {'value': '93518'}}, {'MultipleOffersAtLowestPrice': {'value': 'False'}, 'Price': {'LandedPrice': {'CurrencyCode': {'value': 'USD'}, 'Amount': {'value': '26.96'}}, 'ListingPrice': {'CurrencyCode': {'value': 'USD'}, 'Amount': {'value': '26.96'}}, 'Shipping': {'CurrencyCode': {'value': 'USD'}, 'Amount': {'value': '0.00'}}}, 'NumberOfOfferListingsConsidered': {'value': '2'}, 'Qualifiers': {'SellerPositiveFeedbackRating': {'value': '98-100%'}, 'ItemSubcondition': {'value': 'New'}, 'FulfillmentChannel': {'value': 'Amazon'}, 'ShipsDomestically': {'value': 'True'}, 'ItemCondition': {'value': 'New'}, 'ShippingTime': {'Max': {'value': '0-2 days'}}}, 'SellerFeedbackCount': {'value': '167117'}}, {'MultipleOffersAtLowestPrice': {'value': 'False'}, 'Price': {'LandedPrice': {'CurrencyCode': {'value': 'USD'}, 'Amount': {'value': '30.36'}}, 'ListingPrice': {'CurrencyCode': {'value': 'USD'}, 'Amount': {'value': '22.27'}}, 'Shipping': {'CurrencyCode': {'value': 'USD'}, 'Amount': {'value': '8.09'}}}, 'NumberOfOfferListingsConsidered': {'value': '1'}, 'Qualifiers': {'SellerPositiveFeedbackRating': {'value': '95-97%'}, 'ItemSubcondition': {'value': 'New'}, 'FulfillmentChannel': {'value': 'Merchant'}, 'ShipsDomestically': {'value': 'Unknown'}, 'ItemCondition': {'value': 'New'}, 'ShippingTime': {'Max': {'value': '8-13 days'}}}, 'SellerFeedbackCount': {'value': '199305'}}, {'MultipleOffersAtLowestPrice': {'value': 'False'}, 'Price': {'LandedPrice': {'CurrencyCode': {'value': 'USD'}, 'Amount': {'value': '34.18'}}, 'ListingPrice': {'CurrencyCode': {'value': 'USD'}, 'Amount': {'value': '23.19'}}, 'Shipping': {'CurrencyCode': {'value': 'USD'}, 'Amount': {'value': '10.99'}}}, 'NumberOfOfferListingsConsidered': {'value': '1'}, 'Qualifiers': {'SellerPositiveFeedbackRating': {'value': '98-100%'}, 'ItemSubcondition': {'value': 'New'}, 'FulfillmentChannel': {'value': 'Merchant'}, 'ShipsDomestically': {'value': 'True'}, 'ItemCondition': {'value': 'New'}, 'ShippingTime': {'Max': {'value': '0-2 days'}}}, 'SellerFeedbackCount': {'value': '493'}}, {'MultipleOffersAtLowestPrice': {'value': 'False'}, 'Price': {'LandedPrice': {'CurrencyCode': {'value': 'USD'}, 'Amount': {'value': '44.57'}}, 'ListingPrice': {'CurrencyCode': {'value': 'USD'}, 'Amount': {'value': '39.00'}}, 'Shipping': {'CurrencyCode': {'value': 'USD'}, 'Amount': {'value': '5.57'}}}, 'NumberOfOfferListingsConsidered': {'value': '1'}, 'Qualifiers': {'SellerPositiveFeedbackRating': {'value': '98-100%'}, 'ItemSubcondition': {'value': 'New'}, 'FulfillmentChannel': {'value': 'Merchant'}, 'ShipsDomestically': {'value': 'True'}, 'ItemCondition': {'value': 'New'}, 'ShippingTime': {'Max': {'value': '3-7 days'}}}, 'SellerFeedbackCount': {'value': '147'}}]}}]

if __name__ == "__main__":
    unittest.main()
