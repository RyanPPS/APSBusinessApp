import os
import uuid
import json
import csv
from sqlalchemy import func, update
from app import app
from models import Product, Image, Listing, Catalog, Company, db


with app.app_context():
    session = db.session()
    db.metadata.create_all(db.engine)
    with open('scripts/db_files/companies.csv', 'Ur') as cfile:
        companyrdr = csv.DictReader(cfile)
        for product in companyrdr:
            name = product['company']
            abbr = product['abbreviation']
            website = product['website']
            phone = product['phone']
            company_type = product['class']
            item = Company(
                name = name,
                abbreviation = abbr,
                website = website,
                phone = phone,
                company_type = company_type
            )
            db.session.add(item)
            db.session.commit()





