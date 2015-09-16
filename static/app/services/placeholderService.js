(function(){
    var injectParams = ['$log'];

    var placeholderFactory = function($log) {

        var factory = {};

        factory.placeholders = {
            'UPC': 'upc1 [, upc2, ..., upc20]',
            'Price': 'low price, high price: ex. 5.00,6.00',
            'OEM': 'oem1 [, oem2, ..., oem20]',
            'ASIN': 'asin1 [, asin2, ..., asin20]',
            'Manufacturer': 'Enter a manufacturer. ex. Pentair'
        };

        factory.changePlaceholder = function(searchby) {
          return factory.placeholders[searchby];
        };

          factory.getPlaceholders = function() {
            return factory.placeholders;
          };

          return factory;
    };

    placeholderFactory.$inject = injectParams;

    angular.module('FitsFbaApp').factory('placeholderFactory', placeholderFactory);
}());