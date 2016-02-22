'use strict';

angular.module('resizer', []).directive('resizer', function($document, $timeout, $window) {

	return {
		restrict: 'A',
		priority: 1000,
		scope: {},
		controller: function ($scope, $element, $attrs, $transclude) {
				
			// http://stackoverflow.com/a/2548133
			function endsWith(str, suffix) {
				return str.indexOf(suffix, str.length - suffix.length) !== -1;
			}

			// alternative: https://github.com/heygrady/Units
			// or: http://heygrady.com/blog/2011/12/21/length-and-angle-unit-conversion-in-javascript/
			// number, number px, number % to number of px
			function x2px(x)
			{
				if(typeof x == "number")
					return x;
				if(endsWith(x, 'px'))
					return parseInt(x);
				if(endsWith(x, '%'))
					return parseFloat(x) * $scope.container.innerWidth() / 100.0;
				return parseInt(x);
			}
			function y2px(y)
			{
				if(typeof y == "number")
					return y;
				if(endsWith(y, 'px'))
					return parseInt(y);
				if(endsWith(y, '%'))
					return parseFloat(y) * $scope.container.innerHeight() / 100.0;
				return parseInt(y);
			}
			
			// lai var ērtāk nodefinēt property
			function property(name) {
				Object.defineProperty(controller, name, {
					get: function () {
						return $scope[name];
					},
					set: function (value) {
						$scope[name] = value;
						propertyChanged(name);
					},
					enumerable: true,
					configurable: true
				});
			}

			function propertyChanged(name) {
			}

			var lastReversePosition;	// no otra gala

			this.restoreLastReversePosition = function () {
				if(lastReversePosition === undefined)
					return;
				var size;
				if($scope.orientation == 'vertical')
					size = $scope.container.innerWidth();
				else if($scope.orientation == 'horizontal')
					size = $scope.container.innerHeight();
				if(size > 0)
					this.setPosition(size - lastReversePosition);
			};

			this.setPosition = function (position) {
				if($scope.orientation == 'vertical')
				{
					var width = $scope.container.innerWidth();
					if(width === 0)
						return false;

					var topLeftMin = x2px($scope.topLeftMin);
					var topLeftMax = x2px($scope.topLeftMax);
					var bottomRightMin = x2px($scope.bottomRightMin);
					var bottomRightMax = x2px($scope.bottomRightMax);
					var handleSize = $scope.handleThickness;
					// TODO: pareizi būtu, ja prioritāte būtu tam ierobežojumam (gadījumā, ja pārklājas), kurš ir izteikts precīzi pikseļos (nevis %)

					var x = position;

					if(x < topLeftMin)
						x = topLeftMin;
					else if(x > topLeftMax)
						x = topLeftMax;
					else if(x < 0)
						x = 0;
					if(x + handleSize > width - bottomRightMin)
						x = width - bottomRightMin - handleSize;
					else if(x + handleSize < width - bottomRightMax)
						x = width - bottomRightMax - handleSize;
					else if(x + handleSize > width)
						x = width - handleSize;

					// if (attrs.resizerMax && x > attrs.resizerMax) {
					// 	x = parseInt(attrs.resizerMax);
					// }
					
					$scope.handle.css({
						left: x + 'px'
					});
					$scope.leftPane.css({
						width: x + 'px'
					});
					$scope.rightPane.css({
						left: (x + parseInt(handleSize)) + 'px'
					});


					if(width > 0)
					{
						lastReversePosition = width - x;
						$scope.position = position;
					}
				}
				else if($scope.orientation == 'horizontal')
				{
					var height = $scope.container.innerHeight();
					if(height === 0)
						return false;

					var topLeftMin = y2px($scope.topLeftMin);
					var topLeftMax = y2px($scope.topLeftMax);
					var bottomRightMin = y2px($scope.bottomRightMin);
					var bottomRightMax = y2px($scope.bottomRightMax);
					var handleSize = $scope.handleThickness;

					var y = position;

					if(y < topLeftMin)
						y = topLeftMin;
					else if(y > topLeftMax)
						y = topLeftMax;
					else if(y < 0)
						y = 0;
					if(y + handleSize > height - bottomRightMin)
						y = height - bottomRightMin - handleSize;
					else if(y + handleSize < height - bottomRightMax)
						y = height - bottomRightMax - handleSize;
					else if(y + handleSize > height)
						y = height - handleSize;

					$scope.handle.css({
						top: y + 'px'
					});

					$scope.topPane.css({
						height: y + 'px'
					});
					$scope.bottomPane.css({
						top: (y + parseInt(handleSize)) + 'px'
					});


					if(height > 0)
					{
						lastReversePosition = height - y;
						$scope.position = position;
					}
				}

				return true;
			};

			this.init = function () {

				if($scope.orientation == 'vertical')
				{
					// TODO: ar procentiem šeit būs problēmas, jo nav zināms vai konteinera skats ir beidzis pastāvēt
					// varbūt konvertācija ir jāveic citur un savādāk
					// $scope.topLeftMin = x2px($scope.topLeftMin);
					// $scope.topLeftMax = x2px($scope.topLeftMax);
					// $scope.bottomRightMin = x2px($scope.bottomRightMin);
					// $scope.bottomRightMax = x2px($scope.bottomRightMax);

					if($scope.leftPane && $scope.rightPane && $scope.handle)
					{
						$scope.handle.css({
							position: 'absolute',
							cursor: 'ew-resize',
							top: '0px',
							bottom: '0px',
							// left: position+'px',
							// width: '6px'
							width: $scope.handleThickness+'px'
						});

						return this.setPosition(x2px($scope.position));
					}
				}
				else if($scope.orientation == 'horizontal')	// default ?
				{
					// $scope.topLeftMin = y2px($scope.topLeftMin);
					// $scope.topLeftMax = y2px($scope.topLeftMax);
					// $scope.bottomRightMin = y2px($scope.bottomRightMin);
					// $scope.bottomRightMax = y2px($scope.bottomRightMax);

					if($scope.topPane && $scope.bottomPane && $scope.handle)
					{
						$scope.handle.css({
							position: 'absolute',
							cursor: 'ns-resize',
							left: '0px',
							right: '0px',
							// top: position+'px',
							// height: '6px'
							height: $scope.handleThickness+'px'
						});

						return this.setPosition(y2px($scope.position));
					}
				}
			};

			var controller = this;

			property('container');
			property('rightPane');
			property('leftPane');
			property('topPane');
			property('bottomPane');
			property('handle');
			property('orientation');
			property('handleThickness');
			property('topLeftMin');
			property('topLeftMax');
			property('bottomRightMin');
			property('bottomRightMax');
		},
		link: function (scope, element, attrs, controller, linker) {

			function init()
			{
				// koriģē konteineri ?
				element.css({position: 'absolute'});	// TODO: vai relative
				// šis ir domāts - lai sākumā nostrādā vienreiz
				// if(element.innerWidth() == 0)
				// 	element.css({left: '0px', right: '0px'});
				// if(element.innerHeight() == 0)
				// 	element.css({top: '0px', bottom: '0px'});

				return controller.init();
			}

			scope.resizing = true;
			scope.orientation = attrs.resizer || 'vertical';		// TODO: exception on invalid value or default...
			scope.container = element;
			scope.position = attrs.position != undefined ? attrs.position : 100;

			var followLeftBottom = attrs.hasOwnProperty('followLeft') || attrs.hasOwnProperty('followBottom');


			// init();


			var onResize = function () {
				// NOTE: has follow-left or follow-bottom attributes
				if(!visible)
					return;
				if(followLeftBottom)
				{
					// jāzina pēdējais attālums no kreisās malas / apakšas
					controller.restoreLastReversePosition();
				}

				// TODO: alternatīvs variants: izsaukt scope.$apply(), kas savukārt atkārtoti izsauc šo funkciju dēļ resizeWatch, bet tas jāčeko
				// kaut kas līdzīgs šeit: http://microblog.anthonyestebe.com/2013-11-30/window-resize-event-with-angular/
			};

			// bind div resize on $digest
			var resizeWatch = scope.$watch(function () {
				return [element[0].clientWidth, element[0].clientHeight].join('x');
			}, onResize);

			// bind window resize
			var windowElement = angular.element($window);
			windowElement.bind('resize', onResize);

			var visible = true;

			if(attrs.visible)
			{
				visible = false;
				// izmantot $parent kā haks
				scope.$parent.$watch(attrs.visible, function (value) {
					if(value)
					{
						// TODO: labāks veids, kā noteikt, vai skats ir redzams ?
						if(!init())
							$timeout(function () {
								if(!init())
									$timeout(function () {
										init();
									}, 200);
							}, 10);
						// init();
						visible = value;
					}
				});
			}

			if(scope.orientation == 'vertical')
			{
			}
			else if(scope.orientation == 'horizontal')
			{
			}
			else
			{
				// TODO: error
			}

			scope.$on('$destroy', function () {
				resizeWatch();
				windowElement.unbind('resize', onResize);
				scope.rightPane = undefined;
				scope.leftPane = undefined;
				scope.topPane = undefined;
				scope.bottomPane = undefined;
				scope.handle = undefined;
				scope.container = undefined;
			});
		}
	};
}).directive('resizerHandle', function($document) {
	return {
		restrict: 'A',
		priority: 1000,
		require: '^resizer',
		scope: true,
		link: function (scope, element, attrs, controller, linker) {

			controller.handle = element;
			controller.handleThickness = parseInt(attrs.size) || 6;				// default

			var deltaX = 0;
			var deltaY = 0;
			var cursor;

			element.on('touchstart mousedown', function(event)
			{
				event.preventDefault();

				// TODO: te ir jānosaka delta
				
				var offset = element.offset();
				deltaX = event.originalEvent.pageX - offset.left;
				deltaY = event.originalEvent.pageY - offset.top;

				// http://stackoverflow.com/a/8469671
				if(controller.orientation == 'vertical')
					$('html').addClass('resizing-horizontal');
				else if(controller.orientation == 'horizontal')
					$('html').addClass('resizing-vertical');

				scope.$apply(function () {
					scope.resizing = true;
				});

				$document.on('touchmove mousemove', mousemove);
				$document.on('touchend mouseup touchcancel', mouseup);
			});

			function mousemove(event)
			{
				var position = 0;

				if(controller.orientation == 'vertical')
					position = event.originalEvent.pageX - controller.container.offset().left - deltaX;
				else if(controller.orientation == 'horizontal')
					position = event.originalEvent.pageY - controller.container.offset().top - deltaY;

				controller.setPosition(position);
			}

			function mouseup()
			{
				if(controller.orientation == 'vertical')
					$('html').removeClass('resizing-horizontal');
				else if(controller.orientation == 'horizontal')
					$('html').removeClass('resizing-vertical');
				scope.$apply(function () {
					scope.resizing = false;
				});
				$document.unbind('touchmove mousemove', mousemove);
				$document.unbind('touchend mouseup touchcancel', mouseup);
			}
		}
	};
})
.directive('resizerLeftPane', function($document) {
	return {
		restrict: 'A',
		priority: 1000,
		require: '^resizer',
		link: function (scope, element, attrs, controller, linker) {
			controller.leftPane = element;
			controller.topLeftMin = attrs.minSize || 0;
			controller.topLeftMax = attrs.maxSize || '100%';
			// TODO: var caur attrs.resizerLeftPane {} kā options ar default vērtībām
			element.css({
				position: 'absolute',
				left: '0px',
				top: '0px',
				bottom: '0px'
			});
		}
	};
})
.directive('resizerRightPane', function($document) {
	return {
		restrict: 'A',
		priority: 1000,
		require: '^resizer',
		link: function (scope, element, attrs, controller, linker) {
			controller.rightPane = element;
			controller.bottomRightMin = attrs.minSize || 0;
			controller.bottomRightMax = attrs.maxSize || '100%';
			element.css({
				position: 'absolute',
				right: '0px',
				top: '0px',
				bottom: '0px'
			});
		}
	};
})
.directive('resizerTopPane', function($document) {
	return {
		restrict: 'A',
		priority: 1000,
		require: '^resizer',
		link: function (scope, element, attrs, controller, linker) {
			controller.topPane = element;
			controller.topLeftMin = attrs.minSize || 0;
			controller.topLeftMax = attrs.maxSize || '100%';
			element.css({
				position: 'absolute',
				top: '0px',
				left: '0px',
				right: '0px'
			});
		}
	};
})
.directive('resizerBottomPane', function($document) {
	return {
		restrict: 'A',
		priority: 1000,
		require: '^resizer',
		link: function (scope, element, attrs, controller, linker) {
			controller.bottomPane = element;
			controller.bottomRightMin = attrs.minSize || 0;
			controller.bottomRightMax = attrs.maxSize || '100%';
			element.css({
				position: 'absolute',
				bottom: '0px',
				left: '0px',
				right: '0px'
			});
		}
	};
});
