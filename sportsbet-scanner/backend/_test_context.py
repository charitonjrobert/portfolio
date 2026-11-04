import sys, json
sys.path.insert(0, 'backend')
from context import ContextEngine
from value import find_value_bets

c = json.load(open('backend/config.json', encoding='utf-8'))
ce = ContextEngine(c['context'], cache_file='backend/context_test_cache.json')
ce.begin_scan()
cache = json.load(open('backend/odds_cache.json', encoding='utf-8'))

for g, evs in cache.items():
    vbs = find_value_bets(evs, g, c['value_threshold_pct'], context_engine=ce,
                          borderline_window_pct=c['context']['borderline_window_pct'])
    print('==' + g, 'value bets:', len(vbs))
    for v in vbs[:5]:
        ctx = v.get('context') or {}
        h = ctx.get('home') or {}
        a = ctx.get('away') or {}
        print('  {} vs {} -> {} @{} edge {}% conf {} ctx(h={},a={})'.format(
            v['home_team'], v['away_team'], v['side'], v['odds'], v['edge_pct'],
            v['confidence'], h.get('score'), a.get('score')))
        if h.get('negative_headline'):
            print('    H neg:', h['negative_headline'][:100])