
'use strict';

// console.log = function () {};
var debug = console.log.bind(console);
// var debug = function () {};

angular.module('app', [
	'ui.bootstrap',
	'spin',
	'dropzone',
	'FileSelector',
	'resizer',
	'ui.event',
])
.filter('tuple', function () {
    return function (val, sortBy, reverse) {
		if(!val)
			return '[none]';
		return val.join(', ');
        // var result = [];
        // angular.forEach(items, function (item, key) {
        //     item.$key = key;
        //     result.push(item);
        // });
        // result.sort(function (a, b) {
        //     return a[sortBy].localeCompare(b[sortBy]);
        //     // return a[sortBy] < b[sortBy] ? -1 : (a[sortBy] > b[sortBy] ? 1 : 0);
        // });
        // return result;
    };
})
.controller('AppController', function ($scope, $timeout, $rootScope, $location, $http, $window, $q, $parse) {

	function parseAMR(amr_lines, target) {
		$http.post('/api/parse_amr', amr_lines).success(function (data) {
			console.log(data);
			if(target)
				target(data);
			$scope.loadingSentences = false;
		}).error(function (err) {
			console.error('Error document:', err);
			$scope.loadingSentences = false;
		});
	}

	function readFiles(files, callback) {
		var reader;
		var loading = 0;
        var i, file;
		for(i=0; i<files.length; ++i) {
            file = files[i];
			reader = new FileReader();

			reader.onload = function (file) {
				callback(file, this.result);
			}.bind(reader, file);

			reader.onloadend = function () {
				--loading;
				if(loading == 0)
					callback();
			};

			++loading;
			reader.readAsText(file);
        }
	}

	function loadFiles(files, target) {

		var reader;
		var loading = 0;
        var i, file;
		for(i=0; i<files.length; ++i)
        {
            file = files[i];
            // TODO: global files list
			// files.push({ name: file.name, size: file.size });
			// console.log('dropped file:', file.name);
			
			var reader = new FileReader();

			reader.onload = function (file) {
				var data = this.result;
				parseAMR(data, target);
			}.bind(reader, file);

			reader.onloadend = function () {
				--loading;
				if(loading == 0)
					$scope.loadingSentences = false;
				$scope.$digest();
			};

			++loading;
			$scope.loadingSentences = true;
			$scope.$digest();

			reader.readAsText(file);
        }
	}

	function assign_data(data) {
		var i, amr, sentence, j, sz, instance, relation;
		if($scope.sentences.length == 0) {
			for(i in data) {
				amr = data[i];

				$scope.sentences.push({
					left: amr,
				});
			}
		} else {
			for(i in data) {
				amr = data[i];
				if(i < $scope.sentences.length)
				{
					sentence = $scope.sentences[i];
					sentence.right = amr;
				}
				else 
				{
					$scope.sentences.push({
						right: amr
					});
				}
			}

			for(i in $scope.sentences) {
				sentence = $scope.sentences[i];
				sentence.amr = sentence.left && sentence.left.amr || sentence.right.amr;
				sentence.instances = [];
				if(sentence.left && sentence.right)
					sz = Math.max(sentence.left.instances.length, sentence.right.instances.length);
				else if(sentence.left)
					sz = sentence.left.instances.length;
				else if(sentence.right)
					sz = sentence.right.instances.length;
				for(j=0; j<sz; ++j)
				{
					instance = {
					};
					if(sentence.left && j < sentence.left.instances.length)
						instance.left = sentence.left.instances[j];
					if(sentence.right && j < sentence.right.instances.length)
						instance.right = sentence.right.instances[j];
					sentence.instances.push(instance);
				}
				sentence.relations = [];
				if(sentence.left && sentence.right)
					sz = Math.max(sentence.left.relations.length, sentence.right.relations.length);
				else if(sentence.left)
					sz = sentence.left.relations.length;
				else if(sentence.right)
					sz = sentence.right.relations.length;
				for(j=0; j<sz; ++j)
				{
					relation = {
					};
					if(sentence.left && j < sentence.left.relations.length)
						relation.left = sentence.left.relations[j];
					if(sentence.right && j < sentence.right.relations.length)
						relation.right = sentence.right.relations[j];
					sentence.relations.push(relation);
				}
				console.log(sentence);
			}
		}
	}

	$scope.selectSentence = function (sentence, index) {
		$scope.selectedSentence = sentence;
		$scope.selectedSentenceIndex = index;
	};

	$scope.sentences = undefined;
	$scope.selectedSentence = undefined;
	$scope.selectedSentenceIndex = undefined;

	$scope.fileDrop = function (event) {
		loadFiles(event.dataTransfer.files, assign_data);
	};

	$scope.fileDropLeft = function (event) {
		$scope.leftFileName = event.dataTransfer.files[0].name;
		$scope.loadingLeft = true;
		readFiles([event.dataTransfer.files[0]], function (file, data) {
			if(!file) {
				$scope.loadingLeft = false;
				$scope.$digest();
				return;
			}
			$scope.leftFileContent = data;
			$scope.loadingLeft = false;
			$scope.$digest();

			if($scope.leftFileContent && $scope.rightFileContent) {
				$scope.parseMatchData();
			}
		});
	};

	$scope.fileDropRight = function (event) {
		$scope.rightFileName = event.dataTransfer.files[0].name;
		$scope.loadingRight = true;
		readFiles([event.dataTransfer.files[0]], function (file, data) {
			if(!file) {
				$scope.loadingRight = false;
				$scope.$digest();
				return;
			}
			$scope.rightFileContent = data;
			$scope.loadingRight = false;
			$scope.$digest();

			if($scope.leftFileContent && $scope.rightFileContent) {
				$scope.parseMatchData();
			}
		});
	};

	$scope.fileDropValid = function (event) {
		var types = event.dataTransfer.types;
        if(types.contains)
        {
            if(!types.contains("Files"))
                return false;
        }
        else if(types.indexOf("Files") == -1)
            return false;
		return true;
	};

	function convertData(data) {
		$scope.document = data;
		$scope.sentences = data.sentences;
		var sentence;
		for(var i in data.sentences) {
			sentence = data.sentences[i];
			sentence.n = parseInt(i)+1;
			sentence.gold.single_line_amr = sentence.gold.amr_string.split('\n').length == 1;
			sentence.silver.single_line_amr = sentence.silver.amr_string.split('\n').length == 1;
			if(sentence.gold.single_line_amr) {
				sentence.gold.amr_string = sentence.gold.amr_string.replace(/([()]+)/g, '    \n$1');
			}
			if(sentence.silver.single_line_amr) {
				sentence.silver.amr_string = sentence.silver.amr_string.replace(/([)])(?!\s*[)])/g, '$1\n').replace(/([(])(?!\s*[(])/g, '    \n$1');
			}
		}
		$scope.filter();
		return;
		$scope.sentences = data;
		var sentence, i, j, k, instances, matches, relations, name, relation, other_relations, other_relation, found;
		for(i in data) {
			sentence = data[i];
			sentence.matchedInstances = [];
			sentence.leftOnlyInstances = [];
			sentence.rightOnlyInstances = [];
			instances = sentence.left.instances;
			matches = sentence.left.matches;
			for(name in instances) {
				if(name in matches) {
					sentence.matchedInstances.push({
						left: { name: name, tag: sentence.left.instances[name] },
						right: { name: matches[name], tag: sentence.right.instances[matches[name]] }
					});
				} else {
					sentence.leftOnlyInstances.push({
						name: name, tag: sentence.left.instances[name]
					});
				}
			}
			instances = sentence.right.instances;
			matches = sentence.right.matches;
			for(name in instances) {
				if(!(name in matches)) {
					sentence.rightOnlyInstances.push({
						name: name, tag: instances[name]
					});
				}
			}
			sentence.matchedRelations1 = [];
			sentence.leftOnlyRelations1 = [];
			sentence.rightOnlyRelations1 = [];
			relations = sentence.left.relations1;
			other_relations = sentence.right.relations1;
			matches = sentence.left.matches;
			for(j in relations) {
				relation = relations[j];
				// console.log('first:', relation);
				found = false;
				if(relation[1] in matches) {
					for(k in other_relations) {
						other_relation = other_relations[k];
						// console.log('other:', other_relation);
						if(relation[0] == other_relation[0] && other_relation[1] == matches[relation[1]] && relation[2] == other_relation[2]) {
							// console.log('match:', relation, other_relation);
							sentence.matchedRelations1.push({
								left: relation,
								right: other_relation
							});
							found = true;
							break;
						}
					}
				}
				if(!found) {
					sentence.leftOnlyRelations1.push(relation);
				}
			}
			relations = sentence.right.relations1;
			other_relations = sentence.left.relations1;
			matches = sentence.right.matches;
			for(j in relations) {
				relation = relations[j];
				found = false;
				if(relation[1] in matches) {
					for(k in other_relations) {
						other_relation = other_relations[k];
						if(relation[0] == other_relation[0] && other_relation[1] == matches[relation[1]] && relation[2] == other_relation[2]) {
							found = true;
							break;
						}
					}
				}
				if(!found) {
					sentence.rightOnlyRelations1.push(relation);
				}
			}
			sentence.matchedRelations2 = [];
			sentence.leftOnlyRelations2 = [];
			sentence.rightOnlyRelations2 = [];
			relations = sentence.left.relations2;
			other_relations = sentence.right.relations2;
			matches = sentence.left.matches;
			for(j in relations) {
				relation = relations[j];
				// console.log('first:', relation);
				found = false;
				if(relation[1] in matches) {
					for(k in other_relations) {
						other_relation = other_relations[k];
						// console.log('other:', other_relation);
						if(relation[0] == other_relation[0]
							&& other_relation[1] == matches[relation[1]]
							&& other_relation[2] == matches[relation[2]]) {
							// console.log('match:', relation, other_relation);
							sentence.matchedRelations2.push({
								left: relation,
								right: other_relation
							});
							found = true;
							break;
						}
					}
				}
				if(!found) {
					sentence.leftOnlyRelations2.push(relation);
				}
			}
			relations = sentence.right.relations2;
			other_relations = sentence.left.relations2;
			matches = sentence.right.matches;
			for(j in relations) {
				relation = relations[j];
				// console.log('first:', relation);
				found = false;
				if(relation[1] in matches) {
					for(k in other_relations) {
						other_relation = other_relations[k];
						// console.log('other:', other_relation);
						if(relation[0] == other_relation[0]
							&& other_relation[1] == matches[relation[1]]
							&& other_relation[2] == matches[relation[2]]) {
							// console.log('match:', relation, other_relation);
							found = true;
							break;
						}
					}
				}
				if(!found) {
					sentence.rightOnlyRelations2.push(relation);
				}
			}
		}
	}

	$scope.parseMatchData = function () {
		$scope.parsingLeftRight = true;
		$scope.error = undefined;
		$http.post('/api/parse_match_amr', {left: $scope.leftFileContent, right: $scope.rightFileContent, seed: $scope.settings.deterministic?1:null})
		// .success(function (data) {
		.then(function (response) {
			var data = response.data;
			console.log(data);
			convertData(data);
			$scope.parsingLeftRight = false;
			// if(target)
			// 	target(data);
			// $scope.loadingSentences = false;
		// }).error(function (err) {
		}, function (response) {
			console.error('Error document:', response.status, response.statusText);
			// console.error('Error document:', err);
			$scope.parsingLeftRight = false;
			$scope.error = 'Error: '+response.status+' ('+response.statusText+')';
			// $scope.loadingSentences = false;
		});
	};

	function loadTestData() {
		$scope.parsingLeftRight = true;
		$http.get('/api/test_data', { params: { seed: $scope.settings.deterministic ? '1' : '' } }).success(function (data) {
			console.log(data);
			convertData(data);
			data.goldFilename = 'testdata.gold';
			data.silverFilename = 'testdata';
			// if(target)
			// 	target(data);
			// $scope.loadingSentences = false;
			$scope.parsingLeftRight = false;
		}).error(function (err) {
			console.error('Error document:', err);
			// $scope.loadingSentences = false;
			$scope.parsingLeftRight = false;
		});
	};

	$scope.reset = function () {
		$scope.loadingLeft = false;
		$scope.loadingRight = false;
		$scope.leftFileName = undefined;
		$scope.leftFileContent = undefined;
		$scope.rightFileName = undefined;
		$scope.rightFileContent = undefined;
		$scope.sentences = undefined;
		$scope.selectedSentence = undefined;
		$scope.parsingLeftRight = false;
		$scope.error = false;
		// window.location.reload(true);
	};

	$scope.match_attribute_rules = function (features) {
		var rules, rule, i, key, matched;
		var result = [];
		rules = $scope.document.attribute_rules;
		for(i in rules) {
			rule = rules[i];
			matched = true;
			for(key in rule.data) {
				if(features[key] != rule.data[key]) {
					matched = false;
					break;
				}
			}
			if(matched) {
				result.push(rule);
			}
		}
		return result;
	};

	$scope.match_relation_rules = function (features) {
		var rules, rule, i, key, matched;
		var result = [];
		rules = $scope.document.relation_rules;
		for(i in rules) {
			rule = rules[i];
			matched = true;
			for(key in rule.data) {
				if(features[key] != rule.data[key]) {
					matched = false;
					break;
				}
			}
			if(matched) {
				result.push(rule);
			}
		}
		return result;
	};

	$scope.empty = function (obj) {
		if(!obj)
			return true;
		return Object.keys(obj).length == 0;
	};

	$scope.filterKeypress = function (scope, event) {
		if(event.$event.keyCode == 13) {
			$scope.filter();
		}
	};

	function sortFnByNumber(a, b) {
		if(a.n < b.n) return -1;
		if(a.n > b.n) return 1;
		return 0;
	}

	function sortFnByLengthAsc(a, b) {
		if(!a.text) a.text = a.gold.text || b.gold.text;
		if(!b.text) b.text = b.gold.text || b.gold.text;
		if(a.text.length < b.text.length) return -1;
		if(a.text.length > b.text.length) return 1;
		return 0;
	}

	function sortFnByLengthDesc(a, b) {
		if(!a.text) a.text = a.gold.text || b.gold.text;
		if(!b.text) b.text = b.gold.text || b.gold.text;
		if(a.text.length > b.text.length) return -1;
		if(a.text.length < b.text.length) return 1;
		return 0;
	}

	function sortFnByWordsAsc(a, b) {
		if(!a.words) {
			a.text = a.gold.text || b.gold.text;
			a.words = a.text.split(' ');
		}
		if(!b.words) {
			b.text = b.gold.text || b.gold.text;
			b.words = b.text.split(' ');
		}
		if(a.words.length < b.words.length) return -1;
		if(a.words.length > b.words.length) return 1;
		return 0;
	}

	function sortFnByWordsDesc(a, b) {
		if(!a.words) {
			a.text = a.gold.text || b.gold.text;
			a.words = a.text.split(' ');
		}
		if(!b.words) {
			b.text = b.gold.text || b.gold.text;
			b.words = b.text.split(' ');
		}
		if(a.words.length > b.words.length) return -1;
		if(a.words.length < b.words.length) return 1;
		return 0;
	}

	function sortFnByScoreAsc(a, b) {
		if(a.best_f_score < b.best_f_score) return -1;
		if(a.best_f_score > b.best_f_score) return 1;
		return 0;
	}

	function sortFnByScoreDesc(a, b) {
		if(a.best_f_score > b.best_f_score) return -1;
		if(a.best_f_score < b.best_f_score) return 1;
		return 0;
	}

	function chooseSortFn(sortBy) {
		if(sortBy == 'n') {
			return sortFnByNumber;

		} else if(sortBy == 'wasc') {
			return sortFnByWordsAsc;
		} else if(sortBy == 'wdesc') {
			return sortFnByWordsDesc;

		} else if(sortBy == 'lasc') {
			return sortFnByLengthAsc;
		} else if(sortBy == 'ldesc') {
			return sortFnByLengthDesc;

		} else if(sortBy == 'fasc') {
			return sortFnByScoreAsc;
		} else if(sortBy == 'fdesc') {
			return sortFnByScoreDesc;
		}
	}

	$scope.sort = function (sortBy, sortBy2) {
		if(sortBy == undefined) {
			sortBy = $scope.state.sortBy;
			sortBy2 = $scope.state.sortBy2;
		}
		var sortFn, sortFn2;
		sortFn = chooseSortFn(sortBy);
		sortFn2 = chooseSortFn(sortBy2);
		if($scope.sentences)
			$scope.sentences.sort(function (a, b) {
				var r = sortFn(a, b);
				if(r == 0 && sortFn2)
					return sortFn2(a, b);
				return r;
			});
			// $scope.sentences.sort(sortFn);
	};

	$scope.filter = function () {
		if(!$scope.document)
			return;
		if(!$scope.state.filterText || $scope.state.filterText.length == 0) {
			$scope.sentences = $scope.document.sentences;
		} else {
			console.log('filter')
			var text = $scope.state.filterText.toLowerCase();
			$scope.loadingSentences = true;
			$scope.sentences = $scope.document.sentences.filter(function (s) {
				if(!s.gold.text_)
					s.gold.text_ = s.gold.text.toLowerCase();
				if(!s.silver.text_)
					s.silver.text_ = s.silver.text.toLowerCase();
				if(!s.gold.amr_string_)
					s.gold.amr_string_ = s.gold.amr_string.toLowerCase();
				if(!s.silver.amr_string_)
					s.silver.amr_string_ = s.silver.amr_string.toLowerCase();
				if(s.gold.text_.indexOf(text) != -1)
					return true;
				if(s.silver.text_.indexOf(text) != -1)
					return true;
				if(s.gold.amr_string_.indexOf(text) != -1)
					return true
				if(s.silver.amr_string_.indexOf(text) != -1)
					return true
				return false;
			});
			$scope.loadingSentences = false;
		}
		$scope.sort();
	};

	$scope.sortByOptions = [
		{
			id: 'n',
			title: 'Sentence #'
		},
		{
			id: 'fasc',
			title: 'F-Score asc.'
		},
		{
			id: 'fdesc',
			title: 'F-Score desc.'
		},
		{
			id: 'lasc',
			title: 'Symbol cnt asc.'
		},
		{
			id: 'ldesc',
			title: 'Symbol cnt desc.'
		},
		{
			id: 'wasc',
			title: 'Word cnt asc.'
		},
		{
			id: 'wdesc',
			title: 'Word cnt desc.'
		},
	];

	$scope.sortByOptions2 = $scope.sortByOptions.slice();
	$scope.sortByOptions2.push({
		id: '',
		title: 'no sorting'
	});

	// $scope.sortBy = $scope.sortByOptions[0];

	// $scope.loadingDocuments = true;
	$scope.parsingLeftRight = false;
	$scope.leftFileName;
	$scope.rightFileName;
	// $scope.data;
	$scope.settings = { deterministic: false, inline_rules: false };
	$scope.state = { filterText: '', sortBy: 'n', sortBy2: '' };

	$scope.loadTestData = function () {
		$scope.state.sentencesTab = true;
		loadTestData();
	};
	// loadTestData();
});
