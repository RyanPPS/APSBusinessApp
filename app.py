import json
from flask import Flask, Response, render_template, request, jsonify
from copy import deepcopy
#this is another:  from amazonproduct import API
from amazon.api import AmazonAPI, AmazonProduct
from config import AMAZON_ACCESS_KEY, AMAZON_SECRET_KEY, AMAZON_ASSOC_TAG
from variables import LISTINGS_SCHEME


app = Flask(__name__)
amazon = AmazonAPI(AMAZON_ACCESS_KEY, AMAZON_SECRET_KEY, AMAZON_ASSOC_TAG)


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/itemsearch/<manufacturer>', methods=['GET'])
def itemsearch(manufacturer):
    listings = {}
    products = amazon.search(SearchIndex='LawnAndGarden', Manufacturer=manufacturer)
    listings = {'count':'',
                'products':{}}
    count = 0
    for i,product in enumerate(products):
        count += 1
        asin = product.asin
        listings['products'][asin] = deepcopy(LISTINGS_SCHEME)
        listing = listings['products'][asin]
        for keyi in listing.keys():
            #TODO: Extend AmazonProduct class to include LowestNewPrice
            # .. :temporary: extend AmazonProduct class
            if keyi == 'LowestNewPrice':
                price = product._safe_get_element_text(
                    'OfferSummary.LowestNewPrice.Amount')
                fprice = float(price) / 100 if 'JP' not in product.region else price
                listing[keyi] = fprice
                continue

            # images go in imagelist    
            if isinstance(listing[keyi], dict):
                for keyj in listing[keyi].keys():
                    try:
                        listing[keyi][keyj] = product.__getattribute__(keyj)
                    except:
                        print("Attribute {0} not found".format(keyj))
                continue

            try:
                listing[keyi] = product.__getattribute__(keyi)
            except:
                print("Attribute {0} not found".format(keyi))
    listings['count'] = count
    return jsonify(listings)

def get_jobid():
    job = q.enqueue_call(
        func=itemsearch, args=(manufacturer,), result_ttl=5000
    )
    # return created job id
    return job.get_id()

@app.route('/start', methods=['POST'])
def start():
    # TODO: Add jobid when database is set up.
    data = json.loads(request.data.decode())
    manufacturer = data["manufacturer"]
    """
    # start job
    job = q.enqueue_call(
        func=count_and_save_words, args=(manufacturer,), result_ttl=5000
    )
    # return created job id
    return job.get_id()
    """
    return manufacturer




if __name__ == '__main__': 
    app.debug = True
    app.run()