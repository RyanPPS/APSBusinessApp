# Makes a json file froma  csv.
# Also, we can merge a json and csv file into a new json file.
# This is not the prettiest script but it gets the job done.
# Be aware that this expects and accepts certain keys.
# You may have to change the title of the keys in your file
# before using this script.
# TODO: list except and accept keys.

import json
import csv


manufacturer = 'add the manufacturer here'
p = {}
unsure = {}
fjson = 'add a .json catalog file here'
fcsv = 'add a .csv catalog file here'
outf = 'add an output file here'


if fjson and endswith('.json'):
    with open('db_files/'+ fjson, 'Ur') as ifile:
        products = json.load(ifile, encoding="cp1252")
        counter = 0
        for product in products:
            if isinstance(products, list):
                item = product
            else:
                item = products[product]
                print 'in'
            fprice = item['primary_cost']
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

            if item['part_number'] not in p:
                if fprice:
                    available = True
                else:
                    available = False
                p[item['part_number']] = {
                    'part_number' : item['part_number'],
                    'upc' : item['upc'],
                    'manufacturer' : manufacturer,
                    'title' : item['title'],
                    'primary_cost' : fprice,
                    'available' : available,
                    'weight' : weight,
                    'height' : h,
                    'width' : w,
                    'length' : l
                }

if fcsv and endswith('.csv'):
    with open('db_files/'+ fcsv, 'Ur') as ifile:
        products = csv.DictReader(ifile)
        counter = 0
        for product in products:
            if 'weight' in product:
                weight = product['weight']
            else:
                weight = None
            if 'length' in product:
                length = product['length']
            else:
                length = None
            if 'height' in product:
                height = product['height']
            else:
                height = None
            if 'width' in product:
                width = product['width']
            else:
                width = None
            if 'title' in product:
                title  = product['title']
            else:
                title = None
            if 'manufacturer' in product:
                manufacturer = product['manufacturer']
            else:
                manufacturer = None
            try:
                if not isinstance(product['price'], float):
                    price = product['price'].replace(',', '').replace('$', '')
                    fprice = float(price)
                else:
                    fprice = product['price']
                    print 'Price unconverted'
            except:
                print 'Price Unavailable'
                fprice = None

            upc = product['upc']
            part_number = product['part_number']

            if part_number in p:
                ppn = p[part_number]
                if not ppn['length']:
                    ppn['length'] = length
                if not ppn['width']:
                    ppn['width'] = width
                if not ppn['weight']:
                    ppn['weight'] = weight
                if not ppn['height']:
                    ppn['height'] = height
                if not ppn['title']:
                    ppn['title'] = title

                if fprice:
                    ppn['primary_cost'] = fprice
                    ppn['available'] = True
                else:
                    fprice
                if not ppn['upc'] == upc:
                    unsure[upc] = {
                        'upc_scp' : upc,
                        'upc_man' : ppn['upc'],
                        'part_number': part_number,
                        'title': title
                    }
                ppn['upc'] = upc
                counter += 1
            else:
                if fprice:
                    available = True
                else:
                    print 'Price Unavailable', fprice
                    available = False
                p[part_number] = {
                    'part_number' : part_number,
                    'upc' : upc,
                    'manufacturer' : manufacturer,
                    'title' : title,
                    'primary_cost' : fprice,
                    'available' : available,
                    'weight' : weight,
                    'height' : height,
                    'width' : width,
                    'length' : length
                }
                counter += 1
        print counter


with open('db_files/'+outf, 'w') as merged:
    json.dump(
        p, merged, 
        sort_keys = True, indent = 4, ensure_ascii=True
    )



