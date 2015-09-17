(function () {


  'use strict';

  var fitsfba = angular.module('FitsFbaApp');

  //Controllers
  fitsfba.controller('listingsController', 
    ['$scope', '$log', '$http', 
    '$timeout', 'dataFactory', 
    'csvFactory', 'placeholderFactory',
    function($scope, $log, $http, $timeout, dataFactory, csvFactory, placeholderFactory) {

      $scope.startSearchResults = function() {
        /* Start the search request. We first submit the request.
        * the server responds with a jobid that was designated to
        * handle the request. Then we call getSearchResults to
        * get the results when the job is finished.
        */
        // Make request data.
        var request = {};
        request.user_input = $scope.input_search;
        request.search_by = $scope.searchby;
        if($scope.low_price && $scope.high_price) {
          request.low_price = $scope.low_price;
          request.high_price = $scope.high_price;
        }
        // start the request
        var start = dataFactory.start();
        start.save(request, 
          function(response) {
            $scope.listingCount = null;
            $scope.listings = null;
            $scope.loading = true;
            $scope.submitInfoButtonText = "Loading...";
            getSearchResults(response.jobid);
          },
          function(error) {
            $log.log(error);
        });
      };

      function getSearchResults(jobid) {
          /* Some of these requests can take awhile,
          * so we have to pull the server to see when it is done.
          * We also pull the server so Heroku doesn't terminate
          * the request. There is still a 180sec limit that 
          * the server implements.
          */

          var timeout = "";

          var poller = function() {
            var Job = dataFactory.results(jobid);
              Job.then(
                function(response) {
                  if(response.status === 202 || response.status === 201) {
                    $log.log(response.statusText);
                  } else if (response.status === 200){
                    var products = response.data.products;
                    $scope.loading = false;
                    $scope.listingCount = Object.keys(products).length;
                    $scope.listings = products;
                    $scope.CriteriaError = false;
                    $timeout.cancel(timeout);
                    return false;
                  }
                  // continue to call the poller() function every second
                  // until the timeout is cancelled
                  timeout = $timeout(poller, 1000);
                },
                function(error) {
                  $log.log(error);
                  $scope.loading = false;
                  $scope.CriteriaError = true;
                }
              );
          };
          poller();
      } //end getSearcResults()


      $scope.searchBy = function(searchby) {
        // TODO: each option in the select is calling this everytime.
        $scope.searchByPlaceholder = placeholderFactory.changePlaceholder(searchby);
      };

      // Csv factory.
      $scope.getTable = function(listings) {
        return csvFactory.getTable(listings);
      };

      $scope.getHeader = function() {
        return csvFactory.getHeaders();
      };


      var init = function(){
        $scope.customMarginTop = '-3px';
        $scope.imageSource = "/static/logos/fits_logo_sm.png";
        $scope.loading = false;
        $scope.CriteriaError = false;
        $scope.searchby = 'UPC';
        $scope.headings = [
            '', 'ASIN', 'Manufacturer', 'Title', 'Part Number', 'UPC', 
            'Sales Rank', 'Seller', 'Price', 'FBA Price', 'Our Cost'
        ];
        $scope.searchBy($scope.searchby);
        $scope.listings = null;
        $scope.listingCount = null;
      };
      init();
    }

    ]);

}());