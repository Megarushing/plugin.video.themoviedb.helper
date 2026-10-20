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
