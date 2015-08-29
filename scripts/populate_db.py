import os
import uuid
import json
import csv
from sqlalchemy import func
from app import app
from models import Product, db



with app.app_context():
    session = db.session()
    db.metadata.create_all(db.engine)
    file_list_json = [
        'usseal.json', 'unicel.json', 'waterway.json', 
        'raypak.json', 'aladdin.json', 'hayward.json', 
        'zodiac.json'
    ]
    file_list_csv = [
        'valpak_manufacturer.csv',
        'srsmith.csv'
    ]
    for f in file_list_csv:
        if f.endswith('.json'):
            with open('scripts/db_files/'+ f, 'Ur') as ifile:
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

                    p = Product(
                        part_number=item['oem'],
                        upc = item['upc'],
                        manufacturer = item['manufacturer'],
                        title = item['title'],
                        primary_cost = fprice,
                        available = True,
                        weight = weight,
                        height = h,
                        width = w,
                        length = l
                    )
                    session.add(p)
                    session.commit()
                    counter += 1
                print('{0} products added to database out of {1}.'.format(counter, len(products)))
        if f.endswith('.csv'):
            with open('scripts/db_files/'+ f, 'Ur') as ifile:
                reader = csv.DictReader(ifile)
                for product in reader:
                    if 'weight' in product:
                        weight = product['weight']
                    if 'length' in product:
                        length = product['length']
                    if 'height' in product:
                        height = product['height']
                    if 'width' in product:
                        width = product['width']
                    if 'title' in product:
                        title  = product['title']
                    if 'manufacturer' in product:
                        manufacturer = product['manufacturer']
                    if 'price' in product:
                        price = product['price']
                    upc = product['upc']
                    part_number = product['part_number']
                    p = Product(
                        part_number=part_number,
                        upc = upc,
                        manufacturer = manufacturer,
                        title = title,
                        primary_cost = price,
                        available = True,
                        weight = weight,
                        height = height,
                        width = width,
                        length = length
                    )
                    session.add(p)
                    session.commit()
                    counter += 1
                print('{0} products added to database out of {1}.'.format(counter, len(products)))


            
