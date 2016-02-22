#!/usr/bin/env python3

import re
from smatch_api import parse_amr_iter, make_matched_sentence, Dict, parse_amr
import smatch

def getAMRs(lines):

    comment_lines = []
    amr_lines = []
    amr_lines_collapsed = []

    def prep_amr():
        nonlocal amr_lines, amr_lines_collapsed, comment_lines
        amr = Dict(amr_string='\n'.join(amr_lines), amr_string_collapsed=' '.join(amr_lines_collapsed), comments_string='\n'.join(comment_lines))
        comments = { n:v and v[0] or True for n,*v in (comment.strip().split(' ',1) for cline in comment_lines for comment in cline.split('::')[1:]) }
        amr.comments = comments
        amr.text = comments.get('src-snt', comments.get('snt', comments.get('tok', '')))
        # reset
        comment_lines = []
        amr_lines = []
        amr_lines_collapsed = []
        return amr

    for line in lines:
        line = line.rstrip()
        sline = line.lstrip()
        if not line:
            if amr_lines:
                yield prep_amr()
            else:
                comment_lines.append(sline) # keep space between comment lines
        elif sline[0] == '#':
            comment_lines.append(sline)
            continue
        else:
            amr_lines.append(line)
            amr_lines_collapsed.append(sline)
    if amr_lines:
        yield prep_amr()



def choose_best(input_sentences, score_on_sentences=None, **options):
    if not score_on_sentences:
        score_on_sentences = input_sentences
    results = []

    unparsed_date_re = re.compile(r'\d\d\d\d-\d\d-\d\d')

    options = Dict(options)

    # skip silver AMRs with unparsed date
    if options.require_parsed_dates:
        without_unparsed_date_sentences = [sentence for sentence in input_sentences if not unparsed_date_re.search(sentence.amr_string_collapsed)]
        if without_unparsed_date_sentences:
            input_sentences = without_unparsed_date_sentences

    for silver in input_sentences:

        # if unparsed_date_re.search(silver.amr_string_collapsed):    # skip silver AMRs with unparsed date
        #     continue

        score = 0
        for gold in score_on_sentences:
            if silver is gold:
                continue
            if not silver.amr.valid or not gold.amr.valid:
                continue

            sentence = make_matched_sentence(gold.amr, silver.amr)
            sentence.text = gold.text or silver.text
            gold_triple_num = len(sentence.gold.instances) + len(sentence.gold.attributes) + len(sentence.gold.relations)
            test_triple_num = len(sentence.silver.instances) + len(sentence.silver.attributes) + len(sentence.silver.relations)
            gold_triple_num += 1 if sentence.gold.top else 0
            test_triple_num += 1 if sentence.silver.top else 0
            sentence.precision, sentence.recall, sentence.best_f_score = smatch.compute_f(sentence.best_match_num, test_triple_num, gold_triple_num)

            score += sentence.best_f_score

        results.append(Dict(amr=silver, gold=gold, score=score))

        # let's fallback on using silver sentences for scoring if not done that before
        if score == 0 and input_sentences is not score_on_sentences:
            for gold in input_sentences:
                if silver is gold:
                    continue
                if not silver.amr.valid or not gold.amr.valid:
                    continue

                sentence = make_matched_sentence(gold.amr, silver.amr)
                sentence.text = gold.text or silver.text
                gold_triple_num = len(sentence.gold.instances) + len(sentence.gold.attributes) + len(sentence.gold.relations)
                test_triple_num = len(sentence.silver.instances) + len(sentence.silver.attributes) + len(sentence.silver.relations)
                gold_triple_num += 1 if sentence.gold.top else 0
                test_triple_num += 1 if sentence.silver.top else 0
                sentence.precision, sentence.recall, sentence.best_f_score = smatch.compute_f(sentence.best_match_num, test_triple_num, gold_triple_num)

                score += sentence.best_f_score

            results[-1] = Dict(amr=silver, gold=gold, score=score) # replace last item
            # results.append(Dict(amr=silver, gold=gold, score=score))

    best = None
    second_best = None
    for result in results:
        if not best or best.score < result.score:
            second_best = best
            best = result
        elif not second_best or second_best.score < result.score:
            second_best = result

    best.min_dist = best.score - (second_best.score if second_best else best.score)
    return best, results


if __name__ == "__main__":

    import sys

    # for debug AMR parsing
    # for amr in getAMRs(open(sys.argv[1])):
    #     print(amr.comments)
    #     print(amr.amr_string_collapsed)
    #     print(amr.comments_string)
    #     print(amr.amr_string)
    #     print()

    def log(*args, **kwargs):
        print(*args, file=sys.stderr, **kwargs)

    def usage():
        log('Sentence by sentence voting from an ensemble of AMRs (based on SMATCH)')
        log()
        log(sys.argv[0], 'filenames... [-g gold_file] [-g gold_file] ...')
        log()
        log('options:')
        log('-g, --gold=<filename>    specify gold file, can be used multiple times,')
        log('                         if no gold specified will use input files as golds')
        log('-d, --req-dates          request that dates must be parsed (requests that no "YYYY-MM-DD" patterns are present in AMR graphs)')
        log('-s, --seed=<seed>        set seed (for deterministic results between runs)')
        log('-v, --verbose            output verbose results to stderr')
        log()
        log('Will measure SMATCH score against all gold AMRs (if not specified will measure each input sentence pairs) and output AMR with highes score.')
        log()
        log('Resulting AMR will be written to standard output.')
        log()

    gold_filenames = []
    verbose = False
    require_parsed_dates = False
    
    args = iter(sys.argv)
    unused_args = []
    next(args)
    for arg in args:
        if arg == '--':
            unused_args.extend(args)
            break
        if arg[0] == '-':
            option,*value = arg.split('=',1)
            if option == '-h' or option == '--help':
                usage()
                sys.exit(1)
            elif option == '-g' or option == '--gold':
                value = value[0] if value else next(args)
                gold_filenames.append(value)
            elif option == '-s' or option == '--seed':
                value = value[0] if value else next(args)
                smatch.seed = int(value)
            elif option == '-v' or option == '--verbose':
                verbose = True
            elif option == '-d' or option == '--req-dates':
                require_parsed_dates = True
        else:
            unused_args.append(arg)

    silver_filenames = unused_args

    if not silver_filenames:
        log('Error: no files specified!')
        sys.exit(1)

    log('Files for voting:')
    for fn in silver_filenames:
        log(fn)
    log()
    log('Files to score on:')
    for fn in gold_filenames or silver_filenames:
        log(fn)
    log()

    def load(fn):
        with open(fn) as f:
            log(fn, end=': ', flush=True)
            amrs = list(getAMRs(f))
            for amr in amrs:
                amr.amr = parse_amr(amr.comments_string.split('\n')+amr.amr_string.split('\n'))
            log(len(amrs), 'sentences')
            return amrs

    log('Loading files:')
    silver_amrs = [load(fn) for fn in silver_filenames]
    if gold_filenames:
        gold_amrs = [load(fn) for fn in gold_filenames]
    else:
        gold_amrs = silver_amrs
    log()

    from itertools import chain

    max_amrs = max(chain(gold_amrs, silver_amrs), key=lambda amr: len(amr))
    min_amrs = min(chain(gold_amrs, silver_amrs), key=lambda amr: len(amr))

    if max_amrs != min_amrs:
        log('WARNING: no matching sentence counts:')
        log('Will compare first', len(min_amrs), 'sentences')

    log()
    log('Vote sentences:')

    total = len(min_amrs)
    digits = str(len(str(total)))
    n = 0
    for silvers, golds in zip(zip(*silver_amrs), zip(*gold_amrs)):
        n += 1
        if verbose:
            log(('Sentence #% '+digits+'i (%5.1f %%)') % (n, n*100.0/total), end=': ', flush=True)
        best, results = choose_best(silvers, golds, require_parsed_dates=require_parsed_dates)

        print(best.amr.comments_string)
        print(best.amr.amr_string)
        print()

        if verbose:
            log('best score: %.4f' % best.score, '   other scores:', \
                    ', '.join('%.4f' % result.score for result in results if result.amr is not best.amr), '  ', \
                    'min gain:', ('%.4f' % best.min_dist) if best.min_dist > 0 else '0')
        else:
            log(end='.', flush=True)

    log()
