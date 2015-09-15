var app = angular.module('FitsFbaApp');

app.factory('dataFactory', 
    ['$resource', '$log', '$http',
    function($resource, $log, $http) {
        
        var dataFactory = {};

        dataFactory.start = function() {
            return $resource('/start');
        };

        dataFactory.results = function(jobid) {
            return $http.get('/results/' + jobid);
        };

        return dataFactory;
    }


]);

app.factory('csvFactory',
    ['$log', 
    function($log) {

        var csvFactory = {};

        var headers = [
          'asin', 'manufacturer', 'title', 
          'part_number', 'upc', 'sales_rank', 
          'seller', 'lowest_price', 'lowest_fba_price', 
          'cost'
        ];

        csvFactory.getTable = function(listings) {
        var temp = [];
        for(var i in listings){
          var tempd = {};
          var listing = listings[i]
          for(var h in headers) {
            var heading = headers[h];
            heading = heading;
            tempd[heading] = listing[heading];
          }
          temp.push(tempd);
        }
        $log.log(temp);
        return temp;
      };

      csvFactory.getHeaders = function() {
        return headers;
      };

      return csvFactory;
    }
]);


