#!/usr/bin/env python3

import sys, os
import amr
import smatch

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

def get_amr_line(input_f):
    """
    Read the file containing AMRs. AMRs are separated by a blank line.
    Each call of get_amr_line() returns the next available AMR (in one-line form).
    Note: this function does not verify if the AMR is valid

    """
    cur_amr = []
    has_content = False
    text = ""
    tokens = ""
    for line in input_f:
        orig_line, line = line.rstrip(), line.strip()
        if line == "":
            if not has_content:
                # empty lines before current AMR
                continue
            else:
                # end of current AMR
                break
        if line.startswith("#"):
            if line.startswith("# ::src-snt"):
                text = line[12:]
            elif line.startswith("# ::snt"):
                text = line[8:]
            elif line.startswith("# ::tok"):
                tokens = line[8:]
            # ignore the comment line (starting with "#") in the AMR file
            continue
        else:
            has_content = True
            cur_amr.append((line, orig_line))
    return " ".join(line for line, orig_line in cur_amr), "\n".join(orig_line for line, orig_line in cur_amr), text or tokens

class Dummy:
    pass

def parse_amr(lines):
    amr_line, amr_string, text = get_amr_line(lines)
    if not amr_line:
        return
    try:
        parsed_amr = amr.AMR.parse_AMR_line(amr_line)
        if parsed_amr:
            parsed_amr.valid = True
        else:
            # raise Exception("Error parsing AMR")
            parsed_amr = Dummy()
            parsed_amr.valid = False
    except:
        parsed_amr = Dummy()
        parsed_amr.valid = False
    parsed_amr.amr_line = amr_line      # original AMR string collapsed to single line
    parsed_amr.amr_string = amr_string  # original AMR string
    parsed_amr.text = text              # sentence text
    return parsed_amr

def parse_amr_iter(lines):
    if type(lines) is tuple or type(lines) is list:
        lines = iter(lines)
    while True:
        parsed_amr = parse_amr(lines)
        if not parsed_amr:
            break
        yield parsed_amr

def __match_amr():

    def matches(matches12_indexes, inst1, inst2):
        matches12 = {}
        matches21 = {}
        for i,m in enumerate(matches12_indexes):
            if m != -1:
                matches12[inst1[i][1]] = inst2[m][1]
                matches21[inst2[m][1]] = inst1[i][1]
        return matches12, matches21

    def rename(inst, attr, rel, m):
        inst = [(i[0],m[i[1]],i[2]) for i in inst]
        attr = [(i[0],m[i[1]],i[2]) for i in attr]
        rel = [(i[0],m[i[1]],m[i[2]]) for i in rel]
        return inst, attr, rel

    def convert(amr, inst, attrs, relations):
        top = None
        instances = { var:tag for _,var,tag in inst }
        attributes = []
        for attr in attrs:
            if attr[0] == "TOP":
                top = attr[1]
            else:
                attributes.append(attr)
        return Dict(top=top, instances=instances, attributes=attributes, relations=relations, text=amr.text,
                src_compact=amr.amr_line, src=amr.amr_string,   # only for backwards compatability (for now)
                amr_line=amr.amr_line, amr_string=amr.amr_string)

    def match_amr(gold_amr, test_amr, verbose=False):
        smatch.match_triple_dict.clear()

        gold_label = 'g'
        test_label = 't'

        gold_inst_orig,_,_ = gold_amr.get_triples()
        test_inst_orig,_,_ = test_amr.get_triples()

        gold_amr.rename_node(gold_label)
        test_amr.rename_node(test_label)

        gold_inst, gold_attr, gold_rel = gold_amr.get_triples()
        test_inst, test_attr, test_rel = test_amr.get_triples()

        gold_map = {a[1]:b[1] for a,b in zip(gold_inst, gold_inst_orig)}
        test_map = {a[1]:b[1] for a,b in zip(test_inst, test_inst_orig)}

        # best_mapping, best_match_num = smatch.get_best_match(gold_inst, gold_attr, gold_rel, test_inst, test_attr, test_rel, gold_label, test_label)
        best_mapping, best_match_num = smatch.get_best_match(test_inst, test_attr, test_rel, gold_inst, gold_attr, gold_rel, test_label, gold_label)

        gold_inst, gold_attr, gold_rel = rename(gold_inst, gold_attr, gold_rel, gold_map)
        test_inst, test_attr, test_rel = rename(test_inst, test_attr, test_rel, test_map)

        if verbose:
            print('Gold instances:')
            for instance in gold_inst:
                print('   ', instance)
            print('Test instances:')
            for instance in test_inst:
                print('   ', instance)
            print("Best Match:", smatch.print_alignment(best_mapping, gold_inst, test_inst), file=sys.stderr)
            # print("Matches:", matches(best_mapping, gold_inst, test_inst))
            print("Matches:", matches(best_mapping, test_inst, gold_inst))

        amr1 = convert(gold_amr, gold_inst, gold_attr, gold_rel)
        amr2 = convert(test_amr, test_inst, test_attr, test_rel)
        # amr1.matches, amr2.matches = matches(best_mapping, gold_inst, test_inst)
        amr2.matches, amr1.matches = matches(best_mapping, test_inst, gold_inst)

        return amr1, amr2, best_match_num

    def match_attr(a, b, amr_a):
        if a[0] != b[0]:
            return
        if a[2] != b[2]:
            return
        if a[1] not in amr_a.matches:
            return
        if amr_a.matches[a[1]] != b[1]:
            return
        return True

    def match_rel(a, b, amr_a):
        if a[0] != b[0]:
            return
        if a[1] not in amr_a.matches or a[2] not in amr_a.matches:
            return
        if amr_a.matches[a[1]] != b[1]:
            return
        if amr_a.matches[a[2]] != b[2]:
            return
        return True

    def make_sentence(amr_gold, amr_silver):

        best_match_num = None

        if not hasattr(amr_gold, 'matches') or not hasattr(amr_silver, 'matches'):
            amr_gold, amr_silver, best_match_num = match_amr(amr_gold, amr_silver)

        r = Dict(gold=amr_gold, silver=amr_silver, best_match_num=best_match_num)

        r.matched_instances = [ ((gvar, amr_gold.instances[gvar]), (svar, amr_silver.instances[svar])) for gvar,svar in amr_gold.matches.items() ]
        r.gold_only_instances = [ (var, amr_gold.instances[var]) for var in amr_gold.instances if var not in amr_gold.matches ]
        r.silver_only_instances = [ (var, amr_silver.instances[var]) for var in amr_silver.instances if var not in amr_silver.matches ]

        # r.matched_attributes = [(g,s) for g in amr_gold.attributes for s in amr_silver.attributes if match_rel1(g,s,amr_gold,amr_silver)]

        r.matched_attributes = []
        r.gold_only_attributes = []
        r.silver_only_attributes = []
        for g in amr_gold.attributes:
            for s in amr_silver.attributes:
                if match_attr(g,s,amr_gold):
                    r.matched_attributes.append([g,s])
                    break
        for g in amr_gold.attributes:
            found = False
            for s in amr_silver.attributes:
                if match_attr(g,s,amr_gold):
                    found = True
                    break
            if not found:
                r.gold_only_attributes.append(list(g))
        for s in amr_silver.attributes:
            found = False
            for g in amr_gold.attributes:
                if match_attr(g,s,amr_gold):
                    found = True
                    break
            if not found:
                r.silver_only_attributes.append(list(s))

        r.matched_relations = []
        r.gold_only_relations = []
        r.silver_only_relations = []
        for g in amr_gold.relations:
            for s in amr_silver.relations:
                if match_rel(g,s,amr_gold):
                    r.matched_relations.append([g,s])
                    break
        for g in amr_gold.relations:
            found = False
            for s in amr_silver.relations:
                if match_rel(g,s,amr_gold):
                    found = True
                    break
            if not found:
                r.gold_only_relations.append(list(g))
        for s in amr_silver.relations:
            found = False
            for g in amr_gold.relations:
                if match_rel(g,s,amr_gold):
                    found = True
                    break
            if not found:
                r.silver_only_relations.append(list(s))

        return r

    return match_amr, make_sentence

def make_matched_document(gold_lines, silver_lines, verbose=False):

    gold_amrs = parse_amr_iter(gold_lines)
    silver_amrs = parse_amr_iter(silver_lines)

    sentences = []
    total_match_num = 0
    total_test_num = 0
    total_gold_num = 0

    skipped = 0
    good = 0

    nr = 0

    for gold_amr, silver_amr in zip(gold_amrs, silver_amrs):

        nr += 1

        if not gold_amr.valid or not silver_amr.valid:
            if verbose:
                print('Skipping sentence:', gold_amr.text)
            skipped += 1
            continue

        if verbose:
            print(gold_amr.text)

        sentence = make_matched_sentence(gold_amr, silver_amr)

        gold_triple_num = len(sentence.gold.instances) + len(sentence.gold.attributes) + len(sentence.gold.relations)
        test_triple_num = len(sentence.silver.instances) + len(sentence.silver.attributes) + len(sentence.silver.relations)
        gold_triple_num += 1 if sentence.gold.top else 0
        test_triple_num += 1 if sentence.silver.top else 0

        # if each AMR pair should have a score, compute and output it here
        sentence.precision, sentence.recall, sentence.best_f_score = smatch.compute_f(sentence.best_match_num, test_triple_num, gold_triple_num)

        # sentence.precision = precision
        # sentence.recall = recall
        # sentence.best_f_score = best_f_score
        
        total_match_num += sentence.best_match_num
        total_test_num += test_triple_num
        total_gold_num += gold_triple_num

        if verbose:
            print()
            print("Precision: %.4f" % sentence.precision)
            print("Recall: %.4f" % sentence.recall)
            print("Smatch score: %.4f" % sentence.best_f_score)
            print()
        else:
            print('.', end='', flush=True)

        good += 1

        sentence.nr = nr

        sentences.append(sentence)

    precision, recall, best_f_score = smatch.compute_f(total_match_num, total_test_num, total_gold_num)

    if verbose:
        print("Total:")
        print()
        print("Precision: %.4f" % precision)
        print("Recall: %.4f" % recall)
        print("Smatch score: %.4f" % best_f_score)

    if next(gold_amrs, None):
        pass
    if next(silver_amrs, None):
        pass

    return Dict(sentences=sentences, precision=precision, recall=recall, best_f_score=best_f_score, skipped=skipped, good=good)



match_amr, make_matched_sentence = __match_amr()



if __name__ == "__main__":

    args = sys.argv[1:]

    if not args:
        quit()

    if '-f' in args:
        i = args.index('-f')
        args.pop(i)
        gold_filename = args.pop(i)
        silver_filename = args.pop(i)
        if '-j' in args or '--json' in args:
            args.pop(i)
            json_filename = args.pop(i)
            with open(gold_filename) as gf, open(silver_filename) as sf:
                document = make_matched_document(gf, sf, True)
                import json
                with open(json_filename, 'w') as f:
                    json.dump(document, f, indent=4)
        else:
            with open(gold_filename) as gf, open(silver_filename) as sf:
                gold_amrs = list(parse_amr_iter(gf))
                silver_amrs = list(parse_amr_iter(sf))
                for gold_amr, silver_amr in zip(gold_amrs, silver_amrs):
                    # match_amr(gold_amr, silver_amr, True)
                    # break
                    sentence = make_matched_sentence(gold_amr, silver_amr)
                    print(sentence)
        quit()

    filename = args[0]

    with open(filename) as f:
        
        for cur_amr in parse_amr_iter(f):
            print('AMR:')
            print(cur_amr.amr_string)
            # cur_amr.rename_node('a')
            instances, attributes, relations = cur_amr.get_triples()
            TOP = ''
            for attribute in attributes:
                if attribute[0] == 'TOP':
                    TOP = attribute[1]
                    break
            print('Instances:')
            for instance in instances:
                print('   %s / %s' % instance[1:], '(TOP)' if TOP == instance[1] else '')
            print('Attributes:')
            for attribute in attributes:
                if attribute[0] == 'TOP':
                    continue
                print('   (%s, %s, %s)' % attribute)
            print('Relations:')
            for relation in relations:
                print('   (%s, %s, %s)' % relation)
            print()
            print('-------------------------------')
