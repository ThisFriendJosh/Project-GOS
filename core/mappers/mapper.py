from typing import Dict, List, Tuple
from api.schemas import EventIn  # root-mode import

def map_event_to_ttps(evt: EventIn) -> Tuple[List[str], Dict[str,float]]:
    # TODO: implement heuristics/ML mapping
    return [], {}