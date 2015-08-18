import os
import uuid
import json
from sqlalchemy import func
from app import app
from models import Product, db



with app.app_context():
    session = db.session()
    db.metadata.create_all(db.engine)
    file_list = ['usseal', 'unicel', 'waterway', 'raypak', 'aladdin', 'hayward', 'zodiac']
    for f in file_list:
        with open('scripts/db_files/'+ f + '.json', 'Ur') as ifile:
            products = json.load(ifile)
            counter = 0
            for product in products:
                item = products[product]

                if not 'price' in item:
                    fprice = None
                elif not isinstance(item['price'], float):
                    price = item['price'].replace(',', '').replace('$', '')
                    fprice = float(price)
                else:
                    fprice = item['price']

                if 'dimensions' in item and item['dimensions']:
                    h, l, w = item['dimensions'].split('x')
                elif 'dimensions' in item and not item['dimensions']:
                    h,l,w = None, None, None
                else:
                    if 'height' in item:
                        h = item['height']
                    else:
                        h = None
                    if 'length' in item:
                        l = item['length']
                    else:
                        l = None
                    if 'width' in item:
                        w = item['width']
                    else:
                        w = None
                if 'ship_weight' in item:
                    weight = item['ship_weight']
                elif 'weight' in item:
                    weight = item['weight']
                else:
                    weight = None

                p = Product(part_number=item['oem'],
                            upc = item['upc'],
                            manufacturer = item['manufacturer'],
                            title = item['title'],
                            primary_cost = fprice,
                            available = True,
                            weight = weight,
                            height = h,
                            width = w,
                            length = l)
                session.add(p)
                session.commit()
                counter += 1
            print('{0} products added to database out of {1}.'.format(counter, len(products)))
            
