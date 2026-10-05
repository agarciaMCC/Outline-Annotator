"""Columns from PDF - test library runner.

    python run_library.py            run every case, compare with baseline/, print a report
    python run_library.py --update   run and save the results as the new baseline
    python run_library.py --checks   also write schedule_check / plan_check PDFs per job

Needs Python 3 + PyMuPDF (the same Python the MCC buttons use). The engine is
taken from ../MCC.extension (next to this folder), so run this after every
change to the Columns from PDF / Grids from PDF code: any case whose result
changed is listed, so a fix for one engineer's drawings can't quietly break
another's.

cases.json: one entry per sheet pair. 'verified': true means someone checked
the baseline against the drawings by hand; unverified baselines only guard
against changes, they are not known to be right.
"""
import argparse, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
EXT = os.path.normpath(os.path.join(HERE, '..', 'MCC.extension', 'MCC.tab', 'Setup.panel'))
COLS = os.path.join(EXT, 'Columns from PDF.pushbutton', 'pdfcols')
sys.path.insert(0, COLS)
import schedule as S          # noqa: E402

BASE = os.path.join(HERE, 'baseline')


def case_id(c):
    return '%s_%s' % (c['job'], os.path.splitext(os.path.basename(c.get('plan') or c['schedule']))[0])


def schedule_result(path):
    s = S.parse_schedule(path)
    out = {}
    for mk in sorted(s['marks']):
        row = {}
        for L in s['levels'] or ['*']:
            e = S.lookup(s, mk, L if L != '*' else '1')
            if isinstance(e, dict):
                row[L] = e.get('steel') or ('x'.join(map(str, e['size'])) if e['size'] else '%dDIA' % e['dia'])
            elif e == 'none':
                row[L] = '-'
        out[mk] = row
    return dict(tables=S.summary(s), levels=s['levels'], marks=out)


def plan_result(c, tmp, checks):
    args = [sys.executable, os.path.join(COLS, 'columns.py'), '--out', tmp,
            '--plan', os.path.join(HERE, c['plan']) + ':1', '--schedule', os.path.join(HERE, c['schedule']),
            '--level', c['level']]
    if checks:
        args += ['--check-dir', os.path.join(HERE, c['job'])]
    p = subprocess.run(args, capture_output=True, text=True)
    if p.returncode != 0:
        return dict(error=(p.stderr or p.stdout).strip().splitlines()[-1:])
    r = json.load(open(tmp))
    cols = sorted((x['mark'], x.get('size') and 'x'.join(map(str, x['size'])), [round(v, 1) for v in x['center']],
                   sorted(f.split(' - ')[0][:60] for f in x['flags'])) for x in r['columns'])
    return dict(scale=r['scale'], grids=len(r['grids']), columns=len(r['columns']),
                unmarked=r['unmarked_shapes'], flagged=sum(1 for x in r['columns'] if x['flags']),
                warnings=r['warnings'], detail=cols)


def diff(a, b, path=''):
    out = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            out += diff(a.get(k), b.get(k), path + '/' + str(k))
    elif a != b:
        out.append('%s: %s -> %s' % (path, json.dumps(a)[:80], json.dumps(b)[:80]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--update', action='store_true')
    ap.add_argument('--checks', action='store_true')
    ap.add_argument('--only', help='job number')
    a = ap.parse_args()
    cases = json.load(open(os.path.join(HERE, 'cases.json')))
    os.makedirs(BASE, exist_ok=True)
    tmp = os.path.join(BASE, '_tmp.json')
    changed = 0
    for c in cases:
        if a.only and c['job'] != a.only:
            continue
        cid = case_id(c)
        res = dict(schedule=schedule_result(os.path.join(HERE, c['schedule'])))
        if c.get('plan'):
            res['plan'] = plan_result(c, tmp, a.checks)
        bpath = os.path.join(BASE, cid + '.json')
        tag = 'verified' if c.get('verified') else 'unverified'
        line = '%-22s %-10s sched: %s' % (cid, tag, '; '.join(res['schedule']['tables']) or 'NO TABLE FOUND')
        if 'plan' in res:
            p = res['plan']
            line += ' | plan: ' + (p['error'][0] if 'error' in p else '%d columns, %d flagged, %d unmarked shapes, %d grids, %s'
                                   % (p['columns'], p['flagged'], p['unmarked'], p['grids'], p['scale']))
        print(line)
        if a.update or not os.path.exists(bpath):
            json.dump(res, open(bpath, 'w'), indent=1)
        else:
            d = diff(json.load(open(bpath)), res)
            if d:
                changed += 1
                print('    CHANGED vs baseline (%d differences):' % len(d))
                for x in d[:15]:
                    print('     ', x)
    if os.path.exists(tmp):
        os.remove(tmp)
    print('\n%d case(s) changed' % changed if not a.update else '\nbaseline saved')


if __name__ == '__main__':
    main()
