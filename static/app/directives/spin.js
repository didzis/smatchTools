"use strict";

var spin = angular.module('spin', []);

spin.directive('spin', function () {
	return {
		restrict: 'E',
		replace: true,
		require: '?ngModel',
		transclude: true,
		template: '<div class="spin"></div>',
		link: function (scope, element, attrs, ngModel) {

			var opts = {
				lines: 13, // The number of lines to draw
				length: 5, // The length of each line
				width: 2, // The line thickness
				radius: 3, // The radius of the inner circle
				corners: 1, // Corner roundness (0..1)
				rotate: 0, // The rotation offset
				direction: 1, // 1: clockwise, -1: counterclockwise
				color: '#000', // #rgb or #rrggbb
				speed: 1, // Rounds per second
				trail: 60, // Afterglow percentage
				shadow: false, // Whether to render a shadow
				hwaccel: false, // Whether to use hardware acceleration
				className: 'spinner', // The CSS class to assign to the spinner
				zIndex: 2e9, // The z-index (defaults to 2000000000)
				top: 'auto', // Top position relative to parent in px
				left: 'auto' // Left position relative to parent in px
			};

			// override options
			angular.extend(opts, scope.$eval(attrs.options));

			var spinner = new Spinner(opts);
			if(!ngModel)
			{
				spinner.spin(element[0]);
				return;
			}

			scope.$watch(attrs.ngModel, function (value) {
				if(value)
					spinner.spin(element[0]);
				else
					spinner.stop();
			});
		}
	};
});

