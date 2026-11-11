"""Behavioural analysis of WF-nets: soundness and bounded languages."""
from collections import Counter, deque


def _marking(counter):
    return tuple(sorted((p, k) for p, k in counter.items() if k > 0))


def _enabled(net, m):
    md = dict(m)
    return [t for t in net.transitions
            if all(md.get(p, 0) >= 1 for p in net.preset(t))]


def _fire(net, m, t):
    c = Counter(dict(m))
    for p in net.preset(t):
        c[p] -= 1
    for p in net.postset(t):
        c[p] += 1
    return _marking(c)


def reachability_graph(net, max_states=50_000, max_tokens=20):
    start = _marking(Counter({"i": 1}))
    edges, seen, queue = {}, {start}, deque([start])
    truncated = False
    while queue:
        m = queue.popleft()
        edges[m] = []
        for t in _enabled(net, m):
            m2 = _fire(net, m, t)
            if sum(k for _, k in m2) > max_tokens:
                truncated = True          # likely unbounded
                continue
            edges[m].append((t, m2))
            if m2 not in seen:
                if len(seen) >= max_states:
                    truncated = True
                    continue
                seen.add(m2); queue.append(m2)
    return start, edges, truncated


def check_soundness(net, **kw):
    """Classical WF-net soundness:
    (1) option to complete  - from every reachable marking, [o] is reachable
    (2) proper completion   - if o is marked, no other tokens remain
    (3) no dead transitions - every transition can fire in some reachable marking
    """
    report = {"structure_errors": net.wf_structure_errors()}
    if report["structure_errors"]:
        report["sound"] = False
        return report
    start, edges, truncated = reachability_graph(net, **kw)
    final = _marking(Counter({"o": 1}))
    # backward reachability to the final marking
    rev = {}
    for m, outs in edges.items():
        for _, m2 in outs:
            rev.setdefault(m2, []).append(m)
    can_finish, stack = {final} if final in edges else set(), [final] if final in edges else []
    while stack:
        for m in rev.get(stack.pop(), []):
            if m not in can_finish:
                can_finish.add(m); stack.append(m)
    no_completion = [m for m in edges if m not in can_finish]
    improper = [m for m in edges if dict(m).get("o", 0) >= 1 and m != final]
    fired = {t for outs in edges.values() for t, _ in outs}
    dead = [t for t in net.transitions if t not in fired]
    report.update({
        "states": len(edges),
        "truncated": truncated,
        "option_to_complete": not no_completion,
        "proper_completion": not improper,
        "no_dead_transitions": not dead,
        "dead_transitions": [(t, net.transitions[t]) for t in dead],
    })
    report["sound"] = (not truncated and report["option_to_complete"]
                       and report["proper_completion"] and report["no_dead_transitions"])
    return report


def bounded_language(net, max_len=8, max_silent=12, max_configs=300_000):
    """All complete visible traces (start [i] -> end [o]) with <= max_len activities.

    max_silent bounds consecutive silent steps (protects against tau-cycles).
    max_configs stops the search on state explosion (many parallel branches).
    """
    start = _marking(Counter({"i": 1}))
    final = _marking(Counter({"o": 1}))
    traces = set()
    queue = deque([(start, (), 0)])
    seen = set()
    while queue:
        m, tr, silent = queue.popleft()
        if (m, tr) in seen:
            continue
        seen.add((m, tr))
        if len(seen) > max_configs:
            raise RuntimeError("bounded_language: too many configurations; lower max_len")
        if m == final:
            traces.add(tr)
            continue
        for t in _enabled(net, m):
            lab = net.transitions[t]
            m2 = _fire(net, m, t)
            if lab is None:
                if silent < max_silent:
                    queue.append((m2, tr, silent + 1))
            elif len(tr) < max_len:
                queue.append((m2, tr + (lab,), 0))
    return traces


def language_similarity(net_a, net_b, max_len=8):
    """Jaccard similarity, precision and recall of bounded languages (b = reference)."""
    A, B = bounded_language(net_a, max_len), bounded_language(net_b, max_len)
    inter = A & B
    return {
        "max_len": max_len,
        "traces_generated": len(A),
        "traces_reference": len(B),
        "jaccard": len(inter) / len(A | B) if A | B else 1.0,
        "precision": len(inter) / len(A) if A else 0.0,   # generated traces allowed by reference
        "recall": len(inter) / len(B) if B else 0.0,      # reference traces reproduced
    }


# ---------------------------------------------------------------------------
# Footprints (van der Aalst, Process Mining, 2nd ed., Sect. 6.2 / 8.3)
# ---------------------------------------------------------------------------
def footprint(traces, alphabet=None):
    """Footprint matrix from a set of traces.

    For activities a, b with directly-follows relation >:
      a -> b  causality   (a > b and not b > a)
      a <- b             (b > a and not a > b)
      a || b  parallel    (a > b and b > a)
      a #  b  no relation (neither)
    Returns {(a, b): rel} over the alphabet.
    """
    df = {(t[k], t[k + 1]) for t in traces for k in range(len(t) - 1)}
    alpha = sorted(alphabet if alphabet is not None else {a for t in traces for a in t})
    fp = {}
    for a in alpha:
        for b in alpha:
            ab, ba = (a, b) in df, (b, a) in df
            fp[(a, b)] = "||" if ab and ba else "->" if ab else "<-" if ba else "#"
    return fp


def footprint_similarity(traces_gen, traces_ref):
    """Share of footprint cells that agree, over the union of both alphabets."""
    alpha = {a for t in traces_gen for a in t} | {a for t in traces_ref for a in t}
    if not alpha:
        return 1.0
    fa, fb = footprint(traces_gen, alpha), footprint(traces_ref, alpha)
    return sum(fa[k] == fb[k] for k in fa) / len(fa)
