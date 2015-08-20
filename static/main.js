(function () {


  'use strict';

  angular.module('APSBusinessApp', [])

    .controller('APSBusinessController', ['$scope', '$log', '$http', '$timeout', function($scope, $log, $http, $timeout) {
    $scope.submitManufacturerButtonText = "Search";
    $scope.submitUPCButtonText = "Search";
    $scope.loading = false;
    $scope.manufacturerError = false;
    $scope.UPCError = false;
    $scope.CriteriaError = false;
    $scope.searchby = 'UPC';
    $('.manufacturer-input').hide();

    $scope.startSearchResults = function() {

    $log.log("test");

    // get the upc from the input
    var user_input = $scope.input_search;
    var search_by = $scope.searchby;
    var request = {"user_input": user_input, "search_by":search_by}
    if($scope.manufacturer !== "") {
      request['manufacturer'] = $scope.manufacturer;
    }
    // fire the API request
    $http.post('/start', request).
          success(function(results) {
            $log.log(results);
            getSearchResults(results);
            $scope.listings = null;
            $scope.loading = true;
            $scope.submitInfoButtonText = "Loading...";
          }).
          error(function(error) {
            $log.log(error);
          });
    };

    function getSearchResults(search) {

        var timeout = "";

        
          // fire another request
          if (search['search_by'] === 'Manufacturer') {
            var poller = function() {
              // fire another request
              var manufacturer = search['user_input'];
              $log.log(manufacturer);
              $http.get('/itemsearch/'+search['user_input']).
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
          } else if (search['search_by'] === 'UPC' || search['search_by'] === 'ASIN') {
            var poller = function() {
            $http.get('/itemlookup', {params: search}).
              success(function(data, status, headers, config) {
                if(status === 202) {
                  $log.log(data, status);
                } else if (status === 200){
                  $log.log(data);
                  $scope.loading = false;
                  $scope.listingCount = data.count;
                  $scope.listings = data.products;
                  $scope.CriteriaError = false;
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
                $scope.CriteriaError = true;
              });
            };
            poller();
          } else if (search['search_by'] === 'Price') {
            var poller = function() {
              $http.get('/price_range_search', {params: search}).
              success(function(data, status, headers, config) {
                if(status === 202) {
                  $log.log(data, status);
                } else if (status === 200){
                  $log.log(data);
                  $scope.loading = false;
                  $scope.listingCount = data.count;
                  $scope.listings = data.products;
                  $scope.CriteriaError = false;
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
                $scope.CriteriaError = true;
              });
            };
            poller();
          }

        
    }
    $log.log($scope.searchby)
    $scope.searchBy = function() {
      switch($scope.searchby) {
        case 'UPC': 
          $('.manufacturer-input').hide();
          $('input.search-criteria[type=text]').attr('placeholder','upc1 [, upc2, ..., upc20]');
          break;
        case 'Price': 
          $('input.search-criteria[type=text]').attr('placeholder','low price, high price: ex. 5.00,6.00');
          $('.manufacturer-input').show();
          break;
        case 'OEM': 
          $('.manufacturer-input').hide();
          $('input.search-criteria[type=text]').attr('placeholder','oem1 [, oem2, ..., oem20]');
          break;
        case 'ASIN': 
          $('.manufacturer-input').hide();
          $('input.search-criteria[type=text]').attr('placeholder','asin1 [, asin2, ..., asin20]');
          break;
        case 'Manufacturer': 
          $('.manufacturer-input').hide();
          $('input.search-criteria[type=text]').attr('placeholder','Enter a manufacturer. ex. Pentair');
          break;
        default:
          $('.manufacturer-input').hide();
          $('input.search-criteria[type=text]').attr('placeholder','Enter search by criteria...');
      }
      $log.log($scope.searchby);
    };



    }

    ]);

}());