# Bias and fairness checks on top of fairness.py slice metrics.
# Extends, never duplicates, fairness.py: it reuses slice_metrics for
# per-group selection rates and adds disparate impact ratio,
# demographic parity difference and equal opportunity difference, for
# both the salary selection (predicted salary at or above the median)
# and the ranking selection (in the top 10 by rank score).
#
# Group attributes: the synthetic held-out set carries NO protected
# attributes (no gender, age, ethnicity or similar field exists in
# fixture.py or heldout.json). Groups are therefore the same three
# dimensions fairness.py already uses: city, industry and
# employment_type. Those labels are job-posting attributes, not
# protected labels, and must not be read as such. Do not invent
# protected labels for this data.
#
# Labels used for equal opportunity (both documented, both explicit):
# - salary: a job is truly high-paid when its true salary_band is
#   band-3 or band-4; TPR is the share of those jobs the model selects.
# - ranking: a job is truly relevant when relevance_grade >= 2; TPR is
#   the share of those jobs ranked into the top 10.
#
# Thresholds (defaults here, overridable in mlops/eval/config/gates.json via disparate_impact_min_ratio, demographic_parity_diff_cap, equal_opportunity_diff_cap):
# - disparate impact ratio >= 0.80 (four-fifths rule, min/max rate)
# - demographic parity difference <= 0.20 (max-min selection rate)
# - equal opportunity difference <= 0.20 (max-min TPR)
# Groups with n < MIN_SLICE_N (10, from fairness.py) are reported but
# excluded from the gap/ratio summaries, same as fairness.py.

import argparse
import json
from pathlib import Path

from .fairness import DIMENSIONS, MIN_SLICE_N, slice_metrics
from .gates import load_config
from .model import load_model, model_label, rank_score

DEFAULT_DI_MIN = 0.8
DEFAULT_DPD_CAP = 0.20
DEFAULT_EOD_CAP = 0.20
TOP_K = 10
HIGH_BANDS = {'band-3', 'band-4'}
RELEVANT_GRADE = 2


def _top_ids(model, jobs, k=TOP_K):
    ranked = sorted(jobs, key=lambda job: (-rank_score(model, job), job['id']))
    return {job['id'] for job in ranked[:k]}


def _tpr(selected, labels):
    positives = sum(1 for flag in labels if flag)
    if positives == 0:
        return None
    hits = sum(1 for flag, chosen in zip(labels, selected) if flag and chosen)
    return round(hits / positives, 4)


def _summarise(entries):
    kept = [entry for entry in entries if entry['n'] >= MIN_SLICE_N]
    if not kept:
        return {'disparate_impact_ratio': None, 'demographic_parity_difference': None,
                'equal_opportunity_difference_salary': None, 'equal_opportunity_difference_ranking': None}
    rates = [entry['selection_rate'] for entry in kept]
    top = max(rates)
    di_ratio = round(min(rates) / top, 4) if top > 0 else None
    dpd = round(max(rates) - min(rates), 4)
    salary_tprs = [entry['tpr_salary'] for entry in kept if entry['tpr_salary'] is not None]
    ranking_tprs = [entry['tpr_ranking'] for entry in kept if entry['tpr_ranking'] is not None]
    eod_salary = round(max(salary_tprs) - min(salary_tprs), 4) if len(salary_tprs) >= 2 else 0.0
    eod_ranking = round(max(ranking_tprs) - min(ranking_tprs), 4) if len(ranking_tprs) >= 2 else 0.0
    return {'disparate_impact_ratio': di_ratio, 'demographic_parity_difference': dpd,
            'equal_opportunity_difference_salary': eod_salary,
            'equal_opportunity_difference_ranking': eod_ranking}


def bias_metrics(model, jobs):
    base = slice_metrics(model, jobs)
    top_ids = _top_ids(model, jobs)
    groups = {}
    for dimension in DIMENSIONS:
        buckets = {}
        for job in jobs:
            buckets.setdefault(job[dimension], []).append(job)
        fair_entries = {entry['slice']: entry for entry in base['slices'][dimension]['slices']}
        entries = []
        for key in sorted(buckets):
            members = buckets[key]
            fair = fair_entries.get(key, {})
            selected = [job['salary_mid_vnd'] is not None and _is_selected(model, job, base['median_predicted_vnd']) for job in members]
            in_top = [job['id'] in top_ids for job in members]
            high = [job['salary_band'] in HIGH_BANDS for job in members]
            relevant = [job['relevance_grade'] >= RELEVANT_GRADE for job in members]
            entries.append({
                'slice': key,
                'n': len(members),
                'selection_rate': fair.get('selection_rate'),
                'top10_rate': round(sum(in_top) / len(members), 4),
                'tpr_salary': _tpr(selected, high),
                'tpr_ranking': _tpr(in_top, relevant),
            })
        summary = _summarise(entries)
        groups[dimension] = {'groups': entries, 'summary': summary}
    return {
        'model': base['model'],
        'n': base['n'],
        'median_predicted_vnd': base['median_predicted_vnd'],
        'dimensions': groups,
        'thresholds': {'disparate_impact_min': DEFAULT_DI_MIN, 'demographic_parity_cap': DEFAULT_DPD_CAP, 'equal_opportunity_cap': DEFAULT_EOD_CAP},
    }


def _is_selected(model, job, median):
    from .model import predict_salary
    return predict_salary(model, job) >= median


def apply_flags(result, config):
    di_min = config.get('disparate_impact_min_ratio', DEFAULT_DI_MIN)
    dpd_cap = config.get('demographic_parity_diff_cap', DEFAULT_DPD_CAP)
    eod_cap = config.get('equal_opportunity_diff_cap', DEFAULT_EOD_CAP)
    result['thresholds'] = {'disparate_impact_min': di_min, 'demographic_parity_cap': dpd_cap, 'equal_opportunity_cap': eod_cap}
    flags = []
    for dimension in DIMENSIONS:
        summary = result['dimensions'][dimension]['summary']
        di_ratio = summary['disparate_impact_ratio']
        if di_ratio is not None and di_ratio < di_min:
            flags.append(dimension + ' disparate impact ratio ' + str(di_ratio) + ' below ' + str(di_min))
        dpd = summary['demographic_parity_difference']
        if dpd is not None and dpd > dpd_cap:
            flags.append(dimension + ' demographic parity difference ' + str(dpd) + ' over cap ' + str(dpd_cap))
        for key in ('equal_opportunity_difference_salary', 'equal_opportunity_difference_ranking'):
            eod = summary[key]
            if eod is not None and eod > eod_cap:
                flags.append(dimension + ' ' + key.replace('_', ' ') + ' ' + str(eod) + ' over cap ' + str(eod_cap))
    result['flags'] = flags
    return result


def render_markdown(result):
    lines = []
    lines.append('# Bias and fairness report: ' + result['model'])
    lines.append('')
    lines.append('Held-out set size: ' + str(result['n']) + '. Median predicted salary: ' + str(result['median_predicted_vnd']) + ' VND.')
    lines.append('')
    lines.append('Group attributes are city, industry and employment_type, the only group'
                 ' attributes in the synthetic data. The data carries no protected'
                 ' attributes, so no protected-label analysis is possible here; do not'
                 ' read these job-posting slices as protected groups.')
    lines.append('')
    lines.append('Thresholds: disparate impact ratio >= ' + str(result['thresholds']['disparate_impact_min']) + '; demographic parity'
                 ' difference <= ' + str(result['thresholds']['demographic_parity_cap']) + '; equal opportunity'
                 ' difference <= ' + str(result['thresholds']['equal_opportunity_cap']) + '.')
    lines.append('Selection is predicted salary at or above the median; ranking selection is inclusion in the top 10 by rank score.')
    lines.append('Equal opportunity uses true high pay (salary band 3 or 4) for salary and relevance grade >= 2 for ranking.')
    lines.append('')
    for dimension in DIMENSIONS:
        entry = result['dimensions'][dimension]
        summary = entry['summary']
        lines.append('## ' + dimension)
        lines.append('')
        lines.append('| group | n | selection rate | top-10 rate | TPR salary | TPR ranking |')
        lines.append('| --- | --- | --- | --- | --- | --- |')
        for group in entry['groups']:
            lines.append('| ' + str(group['slice']) + ' | ' + str(group['n']) + ' | ' + str(group['selection_rate']) + ' | ' + str(group['top10_rate']) + ' | ' + str(group['tpr_salary']) + ' | ' + str(group['tpr_ranking']) + ' |')
        lines.append('')
        lines.append('- Disparate impact ratio: ' + str(summary['disparate_impact_ratio']))
        lines.append('- Demographic parity difference: ' + str(summary['demographic_parity_difference']))
        lines.append('- Equal opportunity difference (salary): ' + str(summary['equal_opportunity_difference_salary']))
        lines.append('- Equal opportunity difference (ranking): ' + str(summary['equal_opportunity_difference_ranking']))
        lines.append('')
    lines.append('## Flags')
    lines.append('')
    if result['flags']:
        for flag in result['flags']:
            lines.append('- ' + flag)
    else:
        lines.append('No flags: all dimensions pass the thresholds above.')
    return chr(10).join(lines) + chr(10)


def write_reports(result, out_json, out_md):
    json_path = Path(out_json)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, 'w', encoding='utf-8') as handle:
        json.dump(result, handle, indent=2, ensure_ascii=False)
        handle.write(chr(10))
    md_path = Path(out_md)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    with open(md_path, 'w', encoding='utf-8') as handle:
        handle.write(render_markdown(result))
    return json_path, md_path


def main():
    parser = argparse.ArgumentParser(description='Report bias and fairness checks.')
    parser.add_argument('--model', default='mlops/eval/models/salary-v1/model.json')
    parser.add_argument('--data', default='mlops/eval/data/heldout.json')
    parser.add_argument('--config', default='mlops/eval/config/gates.json')
    parser.add_argument('--out', default='mlops/eval/reports/bias.json')
    parser.add_argument('--out-md', default='mlops/eval/reports/bias.md')
    args = parser.parse_args()
    from .fixture import load_data
    model = load_model(args.model)
    jobs = load_data(args.data)
    config = load_config(args.config)
    result = apply_flags(bias_metrics(model, jobs), config)
    json_path, md_path = write_reports(result, args.out, args.out_md)
    print('model ' + result['model'] + ' n=' + str(result['n']))
    for dimension in DIMENSIONS:
        summary = result['dimensions'][dimension]['summary']
        print(dimension + ' di_ratio ' + str(summary['disparate_impact_ratio']) + ' dpd ' + str(summary['demographic_parity_difference']) + ' eod_salary ' + str(summary['equal_opportunity_difference_salary']) + ' eod_ranking ' + str(summary['equal_opportunity_difference_ranking']))
    print('flags ' + str(len(result['flags'])))
    for flag in result['flags']:
        print('flag ' + flag)
    print('wrote ' + str(json_path))
    print('wrote ' + str(md_path))


if __name__ == '__main__':
    main()
