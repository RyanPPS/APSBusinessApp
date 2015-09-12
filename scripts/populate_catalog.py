import os
import uuid
import json
import csv
from sqlalchemy import func, update
from app import app
from models import Product, Image, Listing, Catalog, db


def populate_db():
    with app.app_context():
        session = db.session()
        db.metadata.create_all(db.engine)
        products = Product.query.filter(Product.manufacturer.ilike('%Waterway%')).all()
        for product in products:
            part_number = product.part_number
            manufacturer = product.manufacturer
            sku = make_sku(part_number, manufacturer)
            cost = product.primary_cost
            res_price = make_res_price(cost)
            com_price = make_com_price(cost)
            shipping = get_shipping(product.weight)
            leadtime = get_leadtime(manufacturer)
            quantity = get_quantity()
            fba = get_fba()
            instock = get_instock()
            if get_item(sku) is not None:
                continue
            try:
                item = Catalog(
                    sku = sku,
                    part_number = product.part_number,
                    cost = cost,
                    res_price = res_price,
                    com_price = com_price,
                    shipping = shipping,
                    leadtime = leadtime,
                    quantity = quantity,
                    manufacturer = product.manufacturer,
                    #asin = asin,
                    upc = product.upc,
                    fba = fba,
                    instock = instock,
                    #listing_asin = asin,
                    product_id = product.id
                )
                db.session.add(item)
                db.session.commit()
            except:
                print('Unable to add to db')
            print(sku, res_price, cost, shipping)

def get_item(sku):
    try:
        item = Catalog.query.filter_by(sku=sku).first()
    except:
        item = None
    return item

def get_shipping(weight):
    if weight > 40:
        return 59.99
    elif weight < 40 and weight >= 20:
        return 29.99
    elif weight < 20 and weight >= 10:
        return 19.99
    elif weight < 10 and weight >= 4:
        return 9.99
    else:
        return 4.99

def get_leadtime(manufacturer):
    if manufacturer in 'Val-Pak':
        return 2
    else:
        return 14

def get_quantity():
    return 10

def get_fba():
    return False

def get_instock():
    return False

def make_sku(part_number, manufacturer):
    if 'smith' in manufacturer.lower():
        sku = 'SRS_' + part_number
    else:
        sku = manufacturer[:3].replace(' ', '').upper() + '_' + part_number
    return sku

def make_res_price(price):
    try:
        res_price = make_price(price, .30)
    except:
        res_price = None
    return res_price

def make_com_price(price):
    try:
        com_price = make_price(price, .27)
    except:
        com_price = None
    return com_price


def make_price(price, multiplier):
    referral_fee = max(1.00, price*.15)
    handling = 1.00
    packaging = 1.00
    min_profit = 1.00
    total_fees = referral_fee + handling + packaging + min_profit
    sale_price = price + (price * multiplier) + total_fees
    return round(sale_price, 2)

populate_db()
