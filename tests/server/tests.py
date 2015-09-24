import os
from copy import deepcopy
import unittest
import tempfile
from app import app
from forms import LoginForm
from models import Result, Listing, Product, Image, User, Catalog
from papi import PAPI, Product, Listing
from utils import dsearch
from test_variables import TEST_RESPONSE, TEST_RESPONSE_SM


class TestConfig(unittest.TestCase):


    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.app = app.test_client()

    def tearDown(self):
        pass


class TestLogin(TestConfig):


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
    """
    def test_start(self):
        self.logout()
        self.login('ryan@allpoolspa.com', os.environ['PASSWORD'])
        # test search by Manufacturer
        r1 = self.start('Hayward', 'Manufacturer')
        #print(r1.status)
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


class TestPAPI(TestConfig):


    def test_get_products_from_response(self):
        papi = PAPI(deepcopy(TEST_RESPONSE))
        products = papi.get_products_from_response()
        self.assertTrue(len(products) == 3)
        papi2 = PAPI(deepcopy(TEST_RESPONSE_SM))
        p2 = papi2.get_products_from_response()
        self.assertTrue(len(p2) == 1)

    def test_make_products(self):
        papi = PAPI(deepcopy(TEST_RESPONSE))
        papi.make_products()
        self.assertTrue(papi.products['B00KUP84L2'])
        self.assertTrue(papi.products['B00HEATHXK'])
        self.assertTrue(papi.products['B00KURKYTK'])
        self.assertTrue(len(papi.products) == 3)
        self.assertFalse(len(papi.products) == 4)

    def test_get_asin_from_product(self):
        # Test response as a list
        papi = PAPI(deepcopy(TEST_RESPONSE))
        products = papi.get_products_from_response()
        asin0 = papi.get_asin_from_product(products[0])
        asin1 = papi.get_asin_from_product(products[1])
        asin2 = papi.get_asin_from_product(products[2])
        self.assertEqual(asin0, 'B00KUP84L2')
        self.assertEqual(asin1, 'B00HEATHXK')
        self.assertEqual(asin2, 'B00KURKYTK')
        # IndexError and KeyError should raise KeyError
        self.assertRaises(KeyError, papi.get_asin_from_product, {})
        # Test response as a dict
        papi2 = PAPI(deepcopy(TEST_RESPONSE_SM))
        products = papi2.get_products_from_response()
        asin = papi2.get_asin_from_product(products[0])
        self.assertEqual(asin, 'B00M2ALI02')

    def test_get_price_from_listing(self):
        papi = PAPI(deepcopy(TEST_RESPONSE))
        products = papi.get_products_from_response()
        offerings0 = papi.get_offerings_from_product(products[0])
        offerings1 = papi.get_offerings_from_product(products[1])
        offerings2 = papi.get_offerings_from_product(products[2])
        self.assertEqual(papi.get_price_from_listing(offerings0[0]), 17.99)
        self.assertEqual(papi.get_price_from_listing(offerings0[1]), 21.39)
        offerings0[0]['Price']['LandedPrice']['Amount']['value'] = '$17.99'
        # catch ValueError
        self.assertEqual(papi.get_price_from_listing(offerings0[0]), '$17.99')
        # catch KeyError
        offerings0[0]['Price'] = {}
        self.assertEqual(papi.get_price_from_listing(offerings0[0]), None)
        # Test response as a dict
        papi2 = PAPI(deepcopy(TEST_RESPONSE_SM))
        products = papi2.get_products_from_response()
        offerings0 = papi.get_offerings_from_product(products[0])
        price = papi2.get_price_from_listing(offerings0[0])
        self.assertEqual(price, 15.99)


    def test_get_seller_from_listing(self):
        papi = PAPI(deepcopy(TEST_RESPONSE))
        products = papi.get_products_from_response()
        offerings0 = papi.get_offerings_from_product(products[0])
        offerings1 = papi.get_offerings_from_product(products[1])
        offerings2 = papi.get_offerings_from_product(products[2])
        self.assertEqual(papi.get_seller_from_listing(offerings0[0]), 'Amazon')
        self.assertEqual(papi.get_seller_from_listing(offerings0[1]), 'Merchant')
        offerings0[0]['Qualifiers']['FulfillmentChannel'] = {}
        # catch KeyError
        self.assertEqual(papi.get_seller_from_listing(offerings0[0]), None)
        # Test response as a dict
        papi2 = PAPI(deepcopy(TEST_RESPONSE_SM))
        products = papi2.get_products_from_response()
        offerings0 = papi.get_offerings_from_product(products[0])
        seller = papi2.get_seller_from_listing(offerings0[0])
        self.assertEqual(seller, 'Amazon')

    def test_get_offerings_from_product(self):
        papi = PAPI(deepcopy(TEST_RESPONSE))
        products = papi.get_products_from_response()
        offerings0 = papi.get_offerings_from_product(products[0])
        offerings1 = papi.get_offerings_from_product(products[1])
        offerings2 = papi.get_offerings_from_product(products[2])
        self.assertEqual(len(offerings0), 3)
        self.assertEqual(len(offerings1), 4)
        self.assertEqual(len(offerings2), 1)
        self.assertEqual(offerings0[0]['Price']['LandedPrice']['Amount']['value'], '17.99')
        # test raise KeyError
        self.assertRaises(KeyError, papi.get_offerings_from_product, {})

    def test_products(self):
        papi = PAPI(deepcopy(TEST_RESPONSE))
        papi.make_products()
        ps = papi.get_products_from_response()
        offerings0 = papi.get_offerings_from_product(ps[0])
        products = papi.products
        lp = products['B00KUP84L2'].lowest_price
        self.assertEqual(lp, 17.99)

    def set_cheapest_seller(self):pass

    def test_lowest_prices(self):
        papi = PAPI(deepcopy(TEST_RESPONSE_SM))
        papi.make_products()
        products = papi.products
        listings = products['B00M2ALI02'].listings
        lp, lfbap = papi.lowest_prices(listings)
        self.assertEqual(lp, 15.99)
        self.assertEqual(lfbap, 15.99)


if __name__ == "__main__":
    unittest.main()
