(function(){
    var injectParams = ['$resource', '$http'];

    var dataFactory = function($resource, $http) {
        var factory = {};

        factory.start = function() {
            return $resource('/start');
        };

        factory.results = function(jobid) {
          return $http.get('/results/' + jobid);
        };

        return factory;
    };

    dataFactory.$inject = injectParams;
    angular.module('FitsFbaApp').factory('dataFactory', dataFactory);
}());