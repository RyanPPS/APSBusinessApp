(function(){
    var injectParams = [];

    var csvFactory = function() {

        var factory = {};

        factory.headers = [
              'asin', 'manufacturer', 'title', 
              'part_number', 'upc', 'sales_rank', 
              'seller', 'lowest_price', 'lowest_fba_price', 
              'cost'
            ];

            factory.getTable = function(listings) {
            var temp = [];
            for(var i in listings){
              var tempd = {};
              var listing = listings[i]
              for(var h in factory.headers) {
                var heading = factory.headers[h];
                heading = heading;
                tempd[heading] = listing[heading];
              }
              temp.push(tempd);
            }
            return temp;
          };

          factory.getHeaders = function() {
            return factory.headers;
          };

          return factory;
    };

    csvFactory.$inject = injectParams;

    angular.module('FitsFbaApp').factory('csvFactory', csvFactory);
}());