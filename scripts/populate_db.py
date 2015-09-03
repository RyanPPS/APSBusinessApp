# populate_db.py adds products from a set of files *files*
# to the database. 
# It expects the following keys:
#   1. part_number
#   2. manufacturer
# It accepts the following keys:
#   1. those it expects
#   2. title
#   3. upc
#   4. weight
#   5. height 
#   6. length 
#   7. width 
#       * can take a set of dimensions as a string separated by 'x'.
#           (ex. '1.0x2.0x3.0').
#   8. price 
#       * wants a float but can handle a string with ',' or '.' or '$'.
# It checks if a product exists with that part_number and manufacturer beforing adding.
# If item is found, price, upc, and title are updated if they don't exist.
# It only handles json files.
# If you have a csv file, please see the make_json_file.py.


import os
import uuid
import json
import csv
from sqlalchemy import func, update
from app import app
from models import Product, db



def populate_db(files):
    with app.app_context():
        session = db.session()
        db.metadata.create_all(db.engine)
        main_added_counter = 0
        main_updated_counter = 0
        for f in files:
            if f.endswith('.json'):
                openf = 'scripts/db_files/'+ f
                with open(openf, 'Ur') as ifile:
                    print ifile
                    products = json.load(ifile, encoding="cp1252")
                    added_counter = 0
                    updated_counter = 0
                    for product in products:
                        item = products[product]
                        # Set variables
                        part_number = item['part_number']
                        manufacturer = item['manufacturer']
                        fprice = get_price(item)
                        h, l, w = get_dimensions(item)
                        weight = get_value('weight', item)
                        upc = get_value('upc', item)
                        title = get_value('title', item)
                        # Check if item exist in database.
                        dbproduct = get_product(part_number, manufacturer)
                        if dbproduct is not None:
                            update_product(dbproduct, item, session)
                            updated_counter += 1
                        else:
                            product_for_db = Product(
                                part_number=part_number, upc = upc,
                                manufacturer = manufacturer, title = title,
                                primary_cost = fprice, available = True,
                                weight = weight, height = h,
                                width = w, length = l
                            )
                            add_product(product_for_db, session)
                            added_counter += 1
                    print('{0} products from {1} added to database.'.format(added_counter, manufacturer))
                    print('{0} products from {1} updated in the database.'.format(updated_counter, manufacturer))
                main_added_counter += added_counter
                main_updated_counter += updated_counter
        print('{0} total products added to database.'.format(main_added_counter))
        print('{0} total products updated in the database.'.format(main_updated_counter))

def update_product(product, item, session):
    try:
        if not product.upc:
            product.upc = get_value('upc', item)
        if not product.primary_cost:
            product.primary_cost = get_price(item)
        if not product.title:
            product.title = get_value('title', item)
        session.commit()
    except:
        print("Experienced error")

def get_value(key, item):
    if key in item:
        value = item[key]
    else:
        value = None
    return value

def get_price(item):
    if not 'price' in item:
        return None
    if isinstance(item['price'], float):
        fprice = item['price']
    else:
        try:
            price = item['price'].replace(',', '').replace('$', '')
            fprice = float(price)
        except:
            print('Price Unavailable for {0}'.format(item['part_number']))
            fprice = None
            pass
    return fprice

def get_dimensions(item):
    if 'dimensions' in item and item['dimensions']:
        h, l, w = item['dimensions'].split('x')
    elif 'dimensions' in item and not item['dimensions']:
        h,l,w = None, None, None
    else:
        h = get_value('height', item)
        l = get_value('length', item)
        w = get_value('width', item)
    return h, l, w

def get_product(part_number, manufacturer):
    try:
        product = Product.query.filter_by(part_number=part_number, manufacturer=manufacturer).first()
    except:
        product = None
    return product

def add_product(product, session):
    try:
        session.add(product)
        session.commit()
    except:
        print('Unable to add items to database.')


if __name__ == '__main__':
    files = [
            'pentair.json',
            'srsmith.json',
            'valpak.json'
    ]
    populate_db(files)

    
        

            
