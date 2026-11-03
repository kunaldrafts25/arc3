"""Bounded GF(2) planning for empirically observed XOR action effects."""


def xor_plan(actions, difference, bits, free_search_limit=10):
    """Return actions whose XOR effects realize difference, or None.

    Enumerate at most 2**free_search_limit equivalent solutions to reduce moves.
    This is exact for full-rank systems; large null spaces are only approximated.
    """
    items = list(actions.items())
    columns = len(items)
    if not difference:
        return []
    if not columns:
        return None
    rows = [sum(((delta >> bit) & 1) << column for column, (_, delta) in enumerate(items))
            | (((difference >> bit) & 1) << columns) for bit in range(bits)]
    pivots = []
    rank = 0
    for column in range(columns):
        pivot = next((i for i in range(rank, len(rows)) if rows[i] & (1 << column)), None)
        if pivot is None:
            continue
        rows[rank], rows[pivot] = rows[pivot], rows[rank]
        for i in range(len(rows)):
            if i != rank and rows[i] & (1 << column):
                rows[i] ^= rows[rank]
        pivots.append(column)
        rank += 1
    coefficient_mask = (1 << columns)-1
    if any(not (row & coefficient_mask) and row & (1 << columns) for row in rows):
        return None
    solution = sum(((rows[i] >> columns) & 1) << column for i, column in enumerate(pivots))
    free = [j for j in range(columns) if j not in pivots]
    null = []
    for column in free[:free_search_limit]:
        vector = 1 << column
        for i, pivot in enumerate(pivots):
            vector |= ((rows[i] >> column) & 1) << pivot
        null.append(vector)
    best = solution
    for choice in range(1 << len(null)):
        candidate = solution
        for i, vector in enumerate(null):
            if choice & (1 << i):
                candidate ^= vector
        if candidate.bit_count() < best.bit_count():
            best = candidate
    return [action for i, (action, _) in enumerate(items) if best & (1 << i)]
