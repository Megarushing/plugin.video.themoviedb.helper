import random
from datetime import date
from urllib.parse import parse_qsl


# Params that change between loads of the SAME widget: refresh counters, paging and labels
VOLATILE_PARAMS = ('page', 'reload', 'widget', 'cacheonly', 'nextpage', 'plugin_category', 'update_listing', 'length')


def stable_random(paramstring, day=None):
    """ Random generator that gives the same picks for the same list all day
    So a Trakt refresh or the next page keeps the list that was randomly chosen
    """
    params = sorted((k, v) for k, v in parse_qsl((paramstring or '').lstrip('?')) if k not in VOLATILE_PARAMS)
    return random.Random(f'{day or date.today().isoformat()}|{params}')


def stable_list_choice(paramstring, items, day=None):
    """Give numbered sibling widgets distinct daily picks from a shared pool.

    Without a slot, retain the existing selection. With slots, canonicalise and
    deduplicate list identities before drawing a shared daily permutation.
    Pools smaller than the slot count necessarily repeat, rather than failing.
    """
    from urllib.parse import urlencode

    params = parse_qsl((paramstring or '').lstrip('?'))
    slot_value = next((v for k, v in params if k == 'random_slot'), '')
    shared_params = urlencode([(k, v) for k, v in params if k != 'random_slot'])
    rng = stable_random(shared_params, day=day)
    try:
        slot = int(slot_value)
    except (TypeError, ValueError):
        slot = 0
    if slot <= 0:
        return rng.choice(items)
    by_identity = {}
    for item in items:
        p = item['params']
        identity = (str(p.get('user_slug', '')), str(p.get('list_slug', '')))
        by_identity.setdefault(identity, item)
    pool = [by_identity[key] for key in sorted(by_identity)]
    rng.shuffle(pool)
    return pool[(slot - 1) % len(pool)]
