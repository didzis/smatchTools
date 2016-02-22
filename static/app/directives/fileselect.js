'use strict';

angular.module('FileSelector', [])
.directive('onSelectFiles', function () {
	return {
		restrict: 'A',
		link: function (scope, element, attrs) {

			// http://www.html5rocks.com/en/tutorials/file/dndfiles/#toc-selecting-files
			// http://codepen.io/wallaceerick/pen/fEdrz

			// NOTE: using appendTo leads to infinite click loop (when calling .focus().click())
			var fileSelector = $('<input type="file" style="display: none" />').insertAfter(element);

			fileSelector.change(function () {
				scope.$eval(attrs.onSelectFiles, {files: this.files});
			});

			element.on('click', function () {
				fileSelector.focus().click();
			});

			scope.$on('$destroy', function () {
				element.unbind();
				fileSelector.unbind();
				fileSelector.remove();
			});
		}
	};
});
