
class dictHelper(dict):
    """Various methods to help traverse the dict representation of
    an mws product api response.

    :method dsearch: returns list of values for the given key
    """

    def dsearch(self, obj, field):
        """Searches through a nested dict with nested lists as well.

        :param object obj: we care if it's a list or dict
        :param str field: key to search for
        """
        def recursion(value, field):
            if isinstance(value, list):
                    more_results = self.dsearch(value, field)
                    for result in more_results:
                        fields_found.append(result)

            elif isinstance(value, dict):
                results = self.dsearch(value, field)
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
















