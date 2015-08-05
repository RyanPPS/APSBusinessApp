(function () {


  'use strict';

  angular.module('APSBusinessApp', [])

    .controller('APSBusinessController', ['$scope', '$log', '$http', '$timeout', function($scope, $log, $http, $timeout) {
    $scope.submitManufacturerButtonText = "Search";
    $scope.submitUPCButtonText = "Search";
    $scope.loading = false;
    $scope.manufacturerError = false;
    $scope.UPCError = false;
    $scope.getManufacturerResults = function() {

        $log.log("test");

        // get the manufacturer from the input
        var user_input = $scope.input_manufacturer;
        // fire the API request
        $http.post('/start', {"user_input": user_input}).
              success(function(results) {
                $log.log(results);
                getManufacturer(results);
                $scope.listings = null;
                $scope.loading = true;
                $scope.submitManufacturerButtonText = "Loading...";
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
                $scope.submitManufacturerButtonText = "Search";
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
              $scope.submitManufacturerButtonText = "Search";
              $scope.manufacturerError = true;
            });
        };
        poller();


    }
    $scope.getUPCResults = function() {

    $log.log("test");

    // get the upc from the input
    var user_input = $scope.input_upc;
    // fire the API request
    $http.post('/start', {"user_input": user_input}).
          success(function(results) {
            $log.log(results);
            getUPC(results);
            $scope.listings = null;
            $scope.loading = true;
            $scope.submitUPCButtonText = "Loading...";
          }).
          error(function(error) {
            $log.log(error);
          });
    };

    function getUPC(upc) {

        var timeout = "";

        var poller = function() {
          // fire another request
          $http.get('/itemlookup/'+upc).
            success(function(data, status, headers, config) {
              if(status === 202) {
                $log.log(data, status);
              } else if (status === 200){
                $log.log(data);
                $scope.loading = false;
                $scope.submitUPCButtonText = "Search";
                $scope.listingCount = data.count
                $scope.listings = data.products;
                $scope.UPCError = false;
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
              $scope.submitUPCButtonText = "Search";
              $scope.UPCError = true;
            });
        };
        poller();

        
    }
    }

    ]);

}());