  var fitsfba = angular.module('FitsFbaApp');

  //Filters
  fitsfba.filter('object2Array', function() {
      return function(input) {
          var out = []; 
          for(var key in input){
              if(input.hasOwnProperty(key)) {
                  out.push(input[key]);
              }
          }
          return out;
      }
  });