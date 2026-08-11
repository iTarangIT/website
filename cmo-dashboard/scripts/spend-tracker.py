#!/usr/bin/env python3
"""Profile API spend ledger and threshold/report helpers."""
from __future__ import annotations
import argparse, datetime as dt, fcntl, json, os
from pathlib import Path
from zoneinfo import ZoneInfo

PROFILE = Path('/opt/data/profiles/itarang_cmo')
LOG = PROFILE / 'logs/spend.log'
ALERT_STATE = PROFILE / 'state/spend-alert-state'
RESUME_STATE = PROFILE / 'state/morning-crawl-resume'
DELIVERY_LOG = PROFILE / 'logs/spend-alerts.log'
BUDGET = 50.0
WARNING = 40.0

def entries():
    if not LOG.exists(): return []
    out=[]
    for line in LOG.read_text(encoding='utf-8').splitlines():
        try:
            item=json.loads(line)
            if item.get('record_type','call') == 'call': out.append(item)
        except (ValueError, TypeError): pass
    return out

def mtd():
    month=dt.datetime.now(dt.timezone.utc).strftime('%Y-%m')
    return sum(float(x.get('estimated_cost_usd') or 0) for x in entries() if str(x.get('date','')).startswith(month))

def daily_firecrawl_credits(day=None):
    day = day or dt.datetime.now(ZoneInfo('Asia/Kolkata')).date().isoformat()
    firecrawl = [
        x for x in entries()
        if x.get('provider') == 'firecrawl' and x.get('credit_day', str(x.get('date', ''))[:10]) == day
    ]
    return {
        'day': day,
        'calls': len(firecrawl),
        'pages_fetched': sum(int(x.get('pages_fetched') or 0) for x in firecrawl),
        'estimated_credits': sum(int(x.get('estimated_credits') or 0) for x in firecrawl),
        'failed_calls': sum(1 for x in firecrawl if x.get('status') in {'failed','cancelled','canceled'}),
        'unaccounted_calls': sum(1 for x in firecrawl if x.get('estimated_credits') is None),
    }

def firecrawl_credit_line(day=None):
    usage = daily_firecrawl_credits(day)
    return (f"Firecrawl {usage['day']}: {usage['estimated_credits']} estimated credit(s), "
            f"{usage['pages_fetched']} page(s) fetched, {usage['calls']} call(s), "
            f"{usage['failed_calls']} failed call(s), {usage['unaccounted_calls']} unaccounted legacy call(s)")

def send(message):
    DELIVERY_LOG.parent.mkdir(parents=True, exist_ok=True)
    with DELIVERY_LOG.open('a', encoding='utf-8') as out:
        out.write(f"{dt.datetime.now(dt.timezone.utc).isoformat()} LOG_ONLY {message}\n")
    return True

def record(args):
    LOG.parent.mkdir(parents=True, exist_ok=True); ALERT_STATE.parent.mkdir(parents=True, exist_ok=True)
    lock=LOG.with_suffix('.log.lock'); lock.touch(exist_ok=True)
    with lock.open('r+', encoding='utf-8') as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        cost=None if args.cost in ('','none','null') else float(args.cost)
        item={'record_type':'call','date':dt.datetime.now(dt.timezone.utc).isoformat(),'provider':args.provider,'model':args.model,'task_id':args.task_id,'estimated_cost_usd':cost,'status':args.status}
        if args.pages_fetched is not None: item['pages_fetched']=args.pages_fetched
        if args.estimated_credits is not None: item['estimated_credits']=args.estimated_credits
        if args.credit_day is not None: item['credit_day']=args.credit_day
        with LOG.open('a', encoding='utf-8') as out:
            out.write(json.dumps(item, separators=(',',':'))+'\n')
        total=mtd(); month=dt.datetime.now(dt.timezone.utc).strftime('%Y-%m')
        prior=ALERT_STATE.read_text(encoding='utf-8').strip() if ALERT_STATE.exists() else ''
        if total >= BUDGET and prior != month+':budget':
            sent=send(f'🚨 API spend budget reached: Spend MTD: ${total:.2f} of $50. Morning crawl paused until owner says resume.')
            ALERT_STATE.write_text(month+':budget\n', encoding='utf-8')
        elif total >= WARNING and not prior.startswith(month+':'):
            sent=send(f'⚠️ API spend alert: Spend MTD: ${total:.2f} of $50 (crossed $40).')
            ALERT_STATE.write_text(month+':warning\n', encoding='utf-8')
        else: sent=False
    print(json.dumps({'mtd':round(total,6),'alert_sent':sent}))

def paused():
    return mtd() >= BUDGET and not RESUME_STATE.exists() and os.environ.get('HERMES_SPEND_RESUME','').lower() not in {'1','true','yes','resume'}

def resume():
    RESUME_STATE.parent.mkdir(parents=True, exist_ok=True)
    RESUME_STATE.write_text(dt.datetime.now(dt.timezone.utc).isoformat()+'\n', encoding='utf-8')
    print('morning crawl resume override enabled')


def weekly():
    now=dt.datetime.now(dt.timezone.utc); start=(now-date_delta(now.weekday())).date()
    week=[x for x in entries() if start <= dt.datetime.fromisoformat(x['date']).date() <= now.date()]
    providers={}; tasks={}
    for x in week:
        c=float(x.get('estimated_cost_usd') or 0); p=x.get('provider','unknown'); t=x.get('task_id','unknown')
        providers[p]=providers.get(p,0)+c; tasks[t]=tasks.get(t,0)+c
    ps=', '.join(f'{k}: ${v:.2f}' for k,v in sorted(providers.items(),key=lambda z:-z[1])) or 'none'
    ts='; '.join(f'{k}: ${v:.2f}' for k,v in sorted(tasks.items(),key=lambda z:-z[1])[:5]) or 'none'
    msg=f'Weekly API expense summary (week of {start.isoformat()}) — Total: ${sum(float(x.get("estimated_cost_usd") or 0) for x in week):.2f}; Providers: {ps}; Top 5 tasks: {ts}. MTD: ${mtd():.2f} of $50.'
    if send(msg): print(msg)

def date_delta(days): return dt.timedelta(days=days)

def main():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest='cmd',required=True)
    r=sub.add_parser('record'); r.add_argument('--provider',required=True); r.add_argument('--model',required=True); r.add_argument('--task-id',required=True); r.add_argument('--cost',required=True); r.add_argument('--status',default='estimated'); r.add_argument('--pages-fetched',type=int); r.add_argument('--estimated-credits',type=int); r.add_argument('--credit-day')
    c=sub.add_parser('credits'); c.add_argument('--day')
    sub.add_parser('morning'); sub.add_parser('weekly'); sub.add_parser('paused'); sub.add_parser('resume')
    a=ap.parse_args()
    if a.cmd=='record': record(a)
    elif a.cmd=='morning': print(f'Spend MTD: ${mtd():.2f} of $50\n{firecrawl_credit_line()}')
    elif a.cmd=='credits': print(firecrawl_credit_line(a.day))
    elif a.cmd=='weekly': weekly()
    elif a.cmd=='resume': resume()
    elif a.cmd=='paused': raise SystemExit(0 if paused() else 1)
if __name__=='__main__': main()
