"use strict";

// Other implementations: http://www.dropzonejs.com/

angular.module('dropzone', []).directive('dropzone', function ($parse, $timeout) {
	return {
		restrict: 'A',
		// scope: true,
		link: function (scope, element, attrs) {

			function dragEnterLeave(event) {
				if(event.type == "dragenter" && attrs.dropzoneValid)
				{
					if(!scope.$eval(attrs.dropzoneValid)(event))
					{
						// console.log('cancel')
						return;
					}
				}
				event.stopPropagation();
				event.preventDefault();
				scope.$apply(function() {
					scope.dragState = '';
					if(dragOverClass)
						element.removeClass(dragOverClass);
				});
			}

			var dragOverClass = attrs.dragOverClass;

			element.addClass('dropzone');

			// TODO: portablāku veidu, kā pievienot eventus
			element[0].addEventListener('dragenter', dragEnterLeave, false);
			element[0].addEventListener('dragleave', dragEnterLeave, false);
			element[0].addEventListener('dragover', function (event) {
				if(attrs.dropzoneValid)
				{
					if(!scope.$eval(attrs.dropzoneValid)(event))
						return;
				}
				event.stopPropagation();
				event.preventDefault();
				// TODO: šito būtu kaut kā jākonfigurē
				// NOTE: firefox ir .contains funkcija, bet webkit implementācijā .types ir vienkārši array
				var types = event.dataTransfer && event.dataTransfer.types;
				var ok = types && ((types.contains && types.contains('Files')) || (!types.contains && types.indexOf('Files') >= 0));
				if(dragOverClass)
					element.addClass(dragOverClass);
				scope.$apply(function () {
					scope.dragState = ok ? 'over' : 'not-available';
				});
			}, false);
			element[0].addEventListener('drop', function (event) {
				if(attrs.dropzoneValid)
				{
					if(!scope.$eval(attrs.dropzoneValid)(event))
					{
						// console.log('cancel')
						return;
					}
				}
				event.stopPropagation();
				event.preventDefault();
				scope.$apply(function () {
					scope.dragState = '';
					if(dragOverClass)
						element.removeClass(dragOverClass);
				});
				// callback
				if(attrs.dropzone) {
					scope.$eval(attrs.dropzone)(event);
				}
				else
					console.log('invalid dropzone function');
				/*
				var files = event.dataTransfer.files;
				if(files.length > 0)
				{
					for (var i = 0, f; f = files[i]; i++)
					{
						var reader = new FileReader();
						reader.onload = function (event) {
							$scope.load(this.result);
						};

						reader.readAsText(f);
					}
				}
				*/
			}, false);
		}
	};
});
