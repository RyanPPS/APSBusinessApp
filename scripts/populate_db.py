import os
import uuid
import json
from sqlalchemy import func
from app import app
from models import Product, db



with app.app_context():
    session = db.session()
    db.metadata.create_all(db.engine)
    with open('scripts/database_files/scp_cc_files/unicel_combined.json', 'Ur') as ifile:
        products = json.load(ifile)
        counter = 0
        for product in products:
            item = products[product]
            try:
                price = item['price'].replace(',', '').replace('$', '')
                fprice = float(price)
            except AttributeError:
                fprice = float(item['price'])
            else:
                fprice = item['price']
            try:
                h, l, w = item['dimensions'].split('x')
            except:
                h, l, w = None, None, None
                #print('No dimensions available.')
            try:
                weight = item['ship_weight']
            except:
                weight = None
                #print('No weight available.')

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
            
