// 
// © 2015 Didzis Goško, Institute of Mathematics and Computer Science, University of Latvia
// (LU aģentūra "Latvijas Universitātes Matemātikas un informātikas institūts")
//
// All rights reserved.
//

'use strict';

angular.module('FrameEditor', [])
.directive('frameEditor', function ($timeout) {
	return {
		restrict: 'E',
		transclude: true,
		replace: true,
		require: '?ngModel',
		// scope: true,
		// template: '<svg xmlns="http://www.w3.org/2000/svg" style="position: absolute; width: 100%; height: 100%; outline: 0; top: 0; bottom: 0px"></svg>',	// bez xmlns ar jaunākām angularjs versijām nedarbojas
		template: '<svg xmlns="http://www.w3.org/2000/svg"></svg>',	// bez xmlns ar jaunākām angularjs versijām nedarbojas
		link: function (scope, element, attrs, ngModel) {

			var editor = FrameEditor(d3.select(element[0]));

			scope.$watch(attrs.ngModel, function (value) {
				if(editor.sentence !== value)	// citādi būs efekts, ka labojot tiek mainīts value saturs (ja true)
				editor.generate(value);

				editor.hideSDP(scope.$eval(attrs.hideSdp));
				editor.hideFrames2(scope.$eval(attrs.hideFrames2));
				editor.hideRawElements(scope.$eval(attrs.hideRawElements));
			}, false);

			scope.$watch(attrs.hideSdp, function (value) {
				editor.hideSDP(value);
			});

			scope.$watch(attrs.hideFrames2, function (value) {
				editor.hideFrames2(value);
			});

			scope.$watch(attrs.hideRawElements, function (value) {
				editor.hideRawElements(value);
			});

			scope.$watch(attrs.frameNet, function (value) {
				if(value)
					editor.setFrameNet(value);
			});

			scope.$watch(attrs.disableKeyboard, function (value) {
				if(value !== undefined)
					editor.keyboardDisabled = value;
			});

			scope.$watch(attrs.disableEditing, function (value) {
				if(value !== undefined)
					editor.disableEditing(value);
			});

			// if(attrs.visible)
			// 	scope.$watch(attrs.visible, function (value) {
			// 		if(value)
			// 		{
			// 			$timeout(function () {					// citādi nepārzīmējas kā nākas
			// 				sdp.generate(ngModel.$modelValue);
			// 			}, 0);
			// 		}
			// 	});
		}
	};
});
