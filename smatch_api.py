#!/usr/bin/env python3

import sys, os
import random

import asyncio
from concurrent.futures import ProcessPoolExecutor

import amr, smatch

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

class AMR:

    def __init__(self, line, string, text):
        self.line = line
        self.string = string
        self.text = text
        self.parsed = None
        self.instances = None
        self.attributes = None
        self.relations = None
        self.matches = None
        self.top = None

    @classmethod
    def read(cls, input_f):
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
        if not has_content:
            return
        return cls(line=" ".join(line for line,_ in cur_amr), string="\n".join(orig_line for _,orig_line in cur_amr), text=text or tokens)

    @classmethod
    def read_iter(cls, input_f):
        while True:
            amr = cls.read(input_f)
            if amr is None:
                break
            yield amr

    def parse(self):
        if not self.line:
            self.parsed = None
            return
        try:
            self.parsed = amr.AMR.parse_AMR_line(self.line)
        except:
            self.parsed = None
            return
        return self

    def output(self):
        return dict(top=self.top, instances=self.instances, attributes=self.attributes, relations=self.relations, text=self.text,
                src_compact=self.line, src=self.string,   # only for backwards compatability (for now)
                amr_line=self.line, amr_string=self.string)


class AMRPair:

    seed = None

    def __init__(self, gold_amr, test_amr):
        self.gold_amr = gold_amr
        self.test_amr = test_amr
        self.best_match_num = None

    @staticmethod
    def _matches(matches12_indexes, inst1, inst2):
        matches12 = {}
        matches21 = {}
        for i,m in enumerate(matches12_indexes):
            if m != -1:
                matches12[inst1[i][1]] = inst2[m][1]
                matches21[inst2[m][1]] = inst1[i][1]
        return matches12, matches21

    @staticmethod
    def _rename(inst, attr, rel, m):
        inst = [(i[0],m[i[1]],i[2]) for i in inst]
        attr = [(i[0],m[i[1]],i[2]) for i in attr]
        rel = [(i[0],m[i[1]],m[i[2]]) for i in rel]
        return inst, attr, rel

    @staticmethod
    def _convert(inst, attrs):
        top = None
        instances = { var:tag for _,var,tag in inst }
        attributes = []
        for attr in attrs:
            if attr[0] == "TOP":
                top = attr[1]
            else:
                attributes.append(attr)
        return instances, attributes, top

    @staticmethod
    def _match_attr(a, b, amr_a):
        if a[0] != b[0]:
            return
        if a[2] != b[2]:
            return
        if a[1] not in amr_a.matches:
            return
        if amr_a.matches[a[1]] != b[1]:
            return
        return True

    @staticmethod
    def _match_rel(a, b, amr_a):
        if a[0] != b[0]:
            return
        if a[1] not in amr_a.matches or a[2] not in amr_a.matches:
            return
        if amr_a.matches[a[1]] != b[1]:
            return
        if amr_a.matches[a[2]] != b[2]:
            return
        return True

    def match(self, verbose=False):
        smatch.match_triple_dict.clear()
        smatch.seed = self.seed

        if self.seed is not None:
            random.seed(seed)


        gold_label = 'g'
        test_label = 't'

        gold_inst_orig,_,_ = self.gold_amr.parsed.get_triples()
        test_inst_orig,_,_ = self.test_amr.parsed.get_triples()

        self.gold_amr.parsed.rename_node(gold_label)
        self.test_amr.parsed.rename_node(test_label)

        gold_inst, gold_attr, gold_rel = self.gold_amr.parsed.get_triples()
        test_inst, test_attr, test_rel = self.test_amr.parsed.get_triples()

        gold_map = {a[1]:b[1] for a,b in zip(gold_inst, gold_inst_orig)}
        test_map = {a[1]:b[1] for a,b in zip(test_inst, test_inst_orig)}

        # best_mapping, self.best_match_num = smatch.get_best_match(gold_inst, gold_attr, gold_rel, test_inst, test_attr, test_rel, gold_label, test_label)
        best_mapping, self.best_match_num = smatch.get_best_match(test_inst, test_attr, test_rel, gold_inst, gold_attr, gold_rel, test_label, gold_label)

        gold_inst, gold_attr, gold_rel = self._rename(gold_inst, gold_attr, gold_rel, gold_map)
        test_inst, test_attr, test_rel = self._rename(test_inst, test_attr, test_rel, test_map)

        if verbose:
            print('Gold instances:')
            for instance in gold_inst:
                print('   ', instance)
            print('Test instances:')
            for instance in test_inst:
                print('   ', instance)
            print("Best Match:", smatch.print_alignment(best_mapping, gold_inst, test_inst), file=sys.stderr)
            # print("Matches:", self._matches(best_mapping, gold_inst, test_inst))
            print("Matches:", self._matches(best_mapping, test_inst, gold_inst))

        gold_amr = self.gold_amr
        test_amr = self.test_amr

        gold_amr.instances, gold_amr.attributes, gold_amr.top = self._convert(gold_inst, gold_attr)
        gold_amr.relations = gold_rel
        test_amr.instances, test_amr.attributes, test_amr.top = self._convert(test_inst, test_attr)
        test_amr.relations = test_rel

        # gold_amr.matches, test_amr.matches = self._matches(best_mapping, gold_inst, test_inst)
        test_amr.matches, gold_amr.matches = self._matches(best_mapping, test_inst, gold_inst)

    def output(self):
        amr_gold = self.gold_amr
        amr_test = self.test_amr

        r = Dict(gold=amr_gold.output(), test=amr_test.output(), best_match_num=self.best_match_num)

        matched_instances = [ ((gvar, amr_gold.instances[gvar]), (svar, amr_test.instances[svar])) for gvar,svar in amr_gold.matches.items() ]
        gold_only_instances = [ (var, amr_gold.instances[var]) for var in amr_gold.instances if var not in amr_gold.matches ]
        test_only_instances = [ (var, amr_test.instances[var]) for var in amr_test.instances if var not in amr_test.matches ]

        # matched_attributes = [(g,s) for g in amr_gold.attributes for s in amr_test.attributes if self._match_rel1(g,s,amr_gold,amr_test)]

        matched_attributes = []
        gold_only_attributes = []
        test_only_attributes = []
        for g in amr_gold.attributes:
            for s in amr_test.attributes:
                if self._match_attr(g,s,amr_gold):
                    matched_attributes.append([g,s])
                    break
        for g in amr_gold.attributes:
            found = False
            for s in amr_test.attributes:
                if self._match_attr(g,s,amr_gold):
                    found = True
                    break
            if not found:
                gold_only_attributes.append(list(g))
        for s in amr_test.attributes:
            found = False
            for g in amr_gold.attributes:
                if self._match_attr(g,s,amr_gold):
                    found = True
                    break
            if not found:
                test_only_attributes.append(list(s))

        matched_relations = []
        gold_only_relations = []
        test_only_relations = []
        for g in amr_gold.relations:
            for s in amr_test.relations:
                if self._match_rel(g,s,amr_gold):
                    matched_relations.append([g,s])
                    break
        for g in amr_gold.relations:
            found = False
            for s in amr_test.relations:
                if self._match_rel(g,s,amr_gold):
                    found = True
                    break
            if not found:
                gold_only_relations.append(list(g))
        for s in amr_test.relations:
            found = False
            for g in amr_gold.relations:
                if self._match_rel(g,s,amr_gold):
                    found = True
                    break
            if not found:
                test_only_relations.append(list(s))

        return dict(
                gold=amr_gold.output(), silver=amr_test.output(), best_match_num=self.best_match_num,
                matched_instances=matched_instances,
                gold_only_instances=gold_only_instances,
                silver_only_instances=test_only_instances,
                matched_attributes=matched_attributes,
                gold_only_attributes=gold_only_attributes,
                silver_only_attributes=test_only_attributes,
                matched_relations=matched_relations,
                gold_only_relations=gold_only_relations,
                silver_only_relations=test_only_relations
            )

    @classmethod
    def make(cls, amr_pair):
        gold_amr, silver_amr = amr_pair
        if not gold_amr.parse() or not silver_amr.parse():
            return
        pair = cls(gold_amr, silver_amr)
        pair.match()
        return dict(pair.output())


class AMRProcessor:

    def __init__(self, max_workers=None, verbose=False):
        self.verbose = verbose
        self.pool = ProcessPoolExecutor(max_workers=max_workers) if max_workers is None or max_workers > 1 else None

    def shutdown(self, wait=True):
        if self.pool:
            self.pool.shutdown(wait=wait)

    def sentences(self, gold_lines, silver_lines, verbose=False, seed=None, loop=None):

        def extract_amr_pairs(gold_lines, silver_lines):
            while True:
                gold_amr = AMR.read(gold_lines)
                silver_amr = AMR.read(silver_lines)
                if gold_amr is None and silver_amr is None:
                    break
                elif gold_amr is None or silver_amr is None:
                    raise Exception('mismatched AMR count')
                yield gold_amr, silver_amr

        AMRPair.seed = seed

        self.total_match_num = 0
        self.total_test_num = 0
        self.total_gold_num = 0

        self.skipped = 0
        self.good = 0

        nr = 0

        def process_sentence(sentence):
            nonlocal nr

            sentence = Dict(sentence)
            sentence.gold = Dict(sentence.gold)
            sentence.silver = Dict(sentence.silver)

            nr += 1

            if not sentence:
                if verbose:
                    print('Skipping sentence:', gold_amr.text)
                self.skipped += 1
                return

            if verbose:
                print(sentence.gold.text)

            gold_triple_num = len(sentence.gold.instances) + len(sentence.gold.attributes) + len(sentence.gold.relations)
            test_triple_num = len(sentence.silver.instances) + len(sentence.silver.attributes) + len(sentence.silver.relations)
            gold_triple_num += 1 if sentence.gold.top else 0
            test_triple_num += 1 if sentence.silver.top else 0

            # if each AMR pair should have a score, compute and output it here
            sentence.precision, sentence.recall, sentence.best_f_score = smatch.compute_f(sentence.best_match_num, test_triple_num, gold_triple_num)

            # sentence.precision = precision
            # sentence.recall = recall
            # sentence.best_f_score = best_f_score
            
            self.total_match_num += sentence.best_match_num
            self.total_test_num += test_triple_num
            self.total_gold_num += gold_triple_num

            if verbose:
                print()
                print("Precision: %.4f" % sentence.precision)
                print("Recall: %.4f" % sentence.recall)
                print("Smatch score: %.4f" % sentence.best_f_score)
                print()
            else:
                print('.', end='', flush=True)

            self.good += 1

            sentence.nr = nr

            return sentence

        if loop is None:
            loop = asyncio.get_event_loop()

        class AMap:
            def __init__(self, func, futures):
                self.func = func
                self.futures = iter(futures)
            async def __aiter__(self):
                return self
            async def __anext__(self):
                try:
                    future = next(self.futures)
                except StopIteration:
                    raise StopAsyncIteration
                return self.func(await future)

        results = list(loop.run_in_executor(self.pool, AMRPair.make, amr_pair) for amr_pair in extract_amr_pairs(gold_lines, silver_lines))

        return AMap(process_sentence, results)

        # for result in results:
        #     sentence = await result
        #     sentence = process_sentence(sentence)
    
        # for sentence in (self.pool.map if self.pool else map)(AMRPair.make, extract_amr_pairs(gold_lines, silver_lines)):
        #     sentence = process_sentence(sentence)
        #     yield sentence

    async def __call__(self, gold_lines, silver_lines, verbose=False, seed=None):

        sentences = []
        async for sentence in self.sentences(gold_lines, silver_lines, verbose=verbose, seed=seed):
            sentences.append(sentence)

        # sentences = list(self.sentences(gold_lines, silver_lines, verbose=verbose, seed=seed))

        precision, recall, best_f_score = smatch.compute_f(self.total_match_num, self.total_test_num, self.total_gold_num)

        if verbose:
            print("Total:")
            print()
            print("Precision: %.4f" % precision)
            print("Recall: %.4f" % recall)
            print("Smatch score: %.4f" % best_f_score)

        return Dict(sentences=sentences, precision=precision, recall=recall, best_f_score=best_f_score, skipped=self.skipped, good=self.good)


if __name__ == "__main__":

    args = sys.argv[1:]

    if not args:
        print('usage:', sys.argv[0], '[-p] [-j | --json] [-f GOLD TEST]')
        print('      ', sys.argv[0], '[AMR file]')
        sys.exit(0)

    max_workers = None

    if '-p' in args:
        i = args.index('-p')
        args.pop(i)
        max_workers = int(args.pop(i))

    if '-f' in args:
        i = args.index('-f')
        args.pop(i)
        gold_filename = args.pop(i)
        silver_filename = args.pop(i)

        processor = AMRProcessor(max_workers)

        if '-j' in args or '--json' in args:
            args.pop(i)
            json_filename = args.pop(i)
            with open(gold_filename) as gf, open(silver_filename) as sf:
                loop = asyncio.get_event_loop()
                document = loop.run_until_complete(processor(gf, sf, True))
                # document = processor(gf, sf, True)
                import json
                with open(json_filename, 'w') as f:
                    json.dump(document, f, indent=4)
        else:
            with open(gold_filename) as gf, open(silver_filename) as sf:
                loop = asyncio.get_event_loop()
                async def list_sentences(sentences):
                    async for sentence in sentences:
                        print(sentence)
                loop.run_until_complete(list_sentences(processor.sentences(gf, sf, True)))
                # for sentence in processor.sentences(gf, sf, True):
                #     print(sentence)
        sys.exit(0)

    filename = args[0]

    with open(filename) as f:
        
        for cur_amr in AMR.read_iter(f):
            print('AMR:')
            print(cur_amr.string)
            cur_amr.parse()
            # cur_amr.rename_node('a')
            instances, attributes, relations = cur_amr.parsed.get_triples()
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
