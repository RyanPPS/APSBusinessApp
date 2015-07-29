(function () {


  'use strict';

  angular.module('APSBusinessApp', [])

    .controller('APSBusinessController', ['$scope', '$log', '$http', '$timeout', function($scope, $log, $http, $timeout) {
    $scope.submitButtonText = "Search";
    $scope.loading = false;
    $scope.urlError = false;
    $scope.getResults = function() {

        $log.log("test");

        // get the manufacturer from the input
        var userInput = $scope.input_manufacturer;
        // fire the API request
        $http.post('/start', {"manufacturer": userInput}).
              success(function(results) {
                $log.log(results);
                getManufacturer(results);
                $scope.listings = null;
                $scope.loading = true;
                $scope.submitButtonText = "Loading...";
              }).
              error(function(error) {
                $log.log(error);
              });
    };

    function getManufacturer(manufacturer) {

        var timeout = "";

        var poller = function() {
          // fire another request
          $http.get('/itemsearch/'+manufacturer).
            success(function(data, status, headers, config) {
              if(status === 202) {
                $log.log(data, status);
              } else if (status === 200){
                $log.log(data);
                $scope.loading = false;
                $scope.submitButtonText = "Search";
                $scope.listingCount = data.count
                $scope.listings = data.products;
                $scope.manufacturerError = false;
                $timeout.cancel(timeout);
                return false;
              }
              // continue to call the poller() function every 2 seconds
              // until the timeout is cancelled
              timeout = $timeout(poller, 2000);
            }).
            error(function(error) {
              $log.log(error);
              $scope.loading = false;
              $scope.submitButtonText = "Search";
              $scope.manufacturerError = true;
            });
        };
        poller();
}
    }

    ]);

}());