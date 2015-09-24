from itertools import izip_longest




def dsearch(obj, field):
    """Searches through a nested dict with nested lists as well.

    :param object obj: we care if it's a list or dict
    :param str field: key to search for
    :return list fields_found: a list of values, one for every *field* in obj
    """
    def recursion(value, field):
        if isinstance(value, list):
                more_results = dsearch(value, field)
                for result in more_results:
                    fields_found.append(result)

        elif isinstance(value, dict):
            results = dsearch(value, field)
            for result in results:
                fields_found.append(result)
        else:
            pass

    fields_found = []
    if isinstance(obj, dict):

        for key, value in obj.items():

            if field == key:
                fields_found.append(value)

            recursion(value, field)

    elif isinstance(obj, list):

        for value in obj:
            recursion(value, field)

    return fields_found




def sectionize_upcs(products):
    upcs = [product.upc for product in products if product.upc]
    return sectionize_into_strings(upcs)

def sectionize_into_lists(alist):
    return [
        [item for item in section if item is not None] 
        for section in izip_longest(*(iter(alist),) * 10)
    ]

def sectionize_into_strings(alist):
    """ Amazon only allows 10 asins or upcs at a time. 
    So we make sections of 10.

    :param list products: a list of Products .
    :return list sections: each item is a comma separated string 
        of at most 10 items from alist.
    """
    filtered_sectioned_list = sectionize_into_lists(alist)
    sections = [
        ', '.join(filtered_section) for filtered_section in 
        filtered_sectioned_list
    ]
    return sections
















