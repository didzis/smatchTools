#!/usr/bin/env python3

# JavaScript like dictionary: d.key <=> d[key]
# http://stackoverflow.com/a/14620633
class Dict(dict):
    def __init__(self, *args, **kwargs):
        super(Dict, self).__init__(*args, **kwargs)
        self.__dict__ = self
    def __getattribute__(self, key):
        try:
            return super(Dict, self).__getattribute__(key)
        except:
            return
    def __delattr__(self, name):
        if name in self:
            del self[name]


import os, sys, json
import pyd21 as PyC60


def new_classifier():
    classifier = PyC60.Classifier()
    classifier.max_features = 3
    classifier.filter_rules = True
    return classifier

def generate_document_rules(document):

    classifier = new_classifier()

    for sentence in document.sentences:

        classname = "MATCHED_INSTANCE"
        for r in sentence.matched_instances:
            g, s = r
            features = {}
            features["GOLD_TYPE"] = g[1]
            features["SILVER_TYPE"] = s[1]
            classifier.add(classname, features)
            # print(classname, features)

        classname = "GOLD_INSTANCE"
        for g in sentence.gold_only_instances:
            features = {}
            features["GOLD_TYPE"] = g[1]
            classifier.add(classname, features)
            # print(classname, features)

        classname = "SILVER_INSTANCE"
        for s in sentence.silver_only_instances:
            features = {}
            features["SILVER_TYPE"] = s[1]
            classifier.add(classname, features)
            # print(classname, features)

    classifier.train()
    document.instance_rules = classifier.rules()

    classifier = new_classifier()

    for sentence in document.sentences:

        classname = "MATCHED_ATTRIBUTE"
        for r in sentence.matched_attributes:
            g, s = r
            features = {}
            features["GOLD_RELATION"] = g[0]
            features["GOLD_TYPE"] = sentence.gold.instances[g[1]]
            features["GOLD_CONST"] = g[2]
            features["SILVER_RELATION"] = s[0]
            features["SILVER_TYPE"] = sentence.silver.instances[s[1]]
            features["SILVER_CONST"] = s[2]
            r.append(features)
            classifier.add(classname, features)
            # print(classname, features)

        classname = "GOLD_ATTRIBUTE"
        for g in sentence.gold_only_attributes:
            features = {}
            features["GOLD_RELATION"] = g[0]
            features["GOLD_TYPE"] = sentence.gold.instances[g[1]]
            features["GOLD_CONST"] = g[2]
            g.append(features)
            classifier.add(classname, features)
            # print(classname, features)

        classname = "SILVER_ATTRIBUTE"
        for s in sentence.silver_only_attributes:
            features = {}
            features["SILVER_RELATION"] = s[0]
            features["SILVER_TYPE"] = sentence.silver.instances[s[1]]
            features["SILVER_CONST"] = s[2]
            s.append(features)
            classifier.add(classname, features)
            # print(classname, features)

    classifier.train()
    document.attribute_rules = classifier.rules()

    classifier = new_classifier()

    for sentence in document.sentences:

        classname = "MATCHED_RELATION"
        for r in sentence.matched_relations:
            g, s = r
            features = {}
            features["GOLD_RELATION"] = g[0]
            features["GOLD_TYPE1"] = sentence.gold.instances[g[1]]
            features["GOLD_TYPE2"] = sentence.gold.instances[g[2]]
            features["SILVER_RELATION"] = s[0]
            features["SILVER_TYPE1"] = sentence.silver.instances[s[1]]
            features["SILVER_TYPE2"] = sentence.silver.instances[s[2]]
            r.append(features)
            classifier.add(classname, features)
            # print(classname, features)

        classname = "GOLD_RELATION"
        for g in sentence.gold_only_relations:
            features = {}
            features["GOLD_RELATION"] = g[0]
            features["GOLD_TYPE1"] = sentence.gold.instances[g[1]]
            features["GOLD_TYPE2"] = sentence.gold.instances[g[2]]
            g.append(features)
            classifier.add(classname, features)
            # print(classname, features)

        classname = "SILVER_RELATION"
        for s in sentence.silver_only_relations:
            features = {}
            features["SILVER_RELATION"] = s[0]
            features["SILVER_TYPE1"] = sentence.silver.instances[s[1]]
            features["SILVER_TYPE2"] = sentence.silver.instances[s[2]]
            s.append(features)
            classifier.add(classname, features)
            # print(classname, features)

    classifier.train()
    document.relation_rules = classifier.rules()

    # import pprint
    # pprint.pprint(classifier.rules())
    # print(classifier.rules())


if __name__ == "__main__":

    args = sys.argv[1:]

    if not args:
        quit()

    if '-f' in args:
        i = args.index('-f')
        args.pop(i)
        gold_filename = args.pop(i)
        silver_filename = args.pop(i)
        with open(gold_filename) as gf, open(silver_filename) as sf:
            import smatch_api
            document = smatch_api.make_matched_document(gf, sf)
            generate_document_rules(document)
            print('Attribute rules:')
            for rule in document.attribute_rules:
                print("%s : w=%f yes=%i no=%i %s" % \
                        (rule['class'], rule['w'], rule['yes'], rule['no'], ', '.join('%s=%s' % kv for kv in rule['data'].items())))
            print('Relation rules:')
            for rule in document.attribute_rules:
                print("%s : w=%f yes=%i no=%i %s" % \
                        (rule['class'], rule['w'], rule['yes'], rule['no'], ', '.join('%s=%s' % kv for kv in rule['data'].items())))
