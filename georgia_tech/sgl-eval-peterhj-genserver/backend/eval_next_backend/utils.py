from collections import defaultdict
from typing import Callable, Iterable, TypeVar, Dict, List

T = TypeVar('T')
K = TypeVar('K')

def group_by(items: Iterable[T], key_func: Callable[[T], K]) -> Dict[K, List[T]]:
    grouped = defaultdict(list)
    for item in items:
        grouped[key_func(item)].append(item)
    return grouped
