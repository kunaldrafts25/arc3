"""Advisory recovery evidence from public observations; never gates actions."""
from collections import Counter
from hashlib import blake2s


def fingerprint(frame):
    return blake2s(repr(frame.grid).encode(),digest_size=12).hexdigest()


class RecoveryMonitor:
    def __init__(self):
        self.level=None
        self.last_notice_step=None

    def observe(self,current,history):
        if current is None:return None
        if self.level!=current.level or (self.last_notice_step is not None and current.step<self.last_notice_step):
            self.level=current.level;self.last_notice_step=None
        if self.last_notice_step is not None and current.step-self.last_notice_step<32:return None
        # Contiguous suffix only: resets or earlier levels cannot create a
        # fictitious uninterrupted streak. Never scan an unbounded grid history.
        recent=[]
        for entry in reversed(history):
            frame=getattr(entry,'frame',None)
            if frame is None or frame.level!=current.level:break
            recent.append(entry)
            if len(recent)>=257:break
        recent.reverse()
        if len(recent)<65:return None
        if recent[-1].frame.step!=current.step:return None
        window=recent[-65:]
        hashes=[fingerprint(e.frame) for e in window]
        transitions=[]
        for i in range(1,len(window)):
            if window[i].frame.step<=window[i-1].frame.step:continue
            transitions.append((hashes[i-1],str(window[i].action),hashes[i],window[i].frame.step))
        counts=Counter(t[:3] for t in transitions)
        repeats=[]
        for key,count in counts.most_common(3):
            if count<3:continue
            refs=[t[3] for t in transitions if t[:3]==key]
            repeats.append(dict(action=key[1][:90],count=count,first_step=refs[0],last_step=refs[-1],
                                unchanged_visible_grid=key[0]==key[2]))
        self.last_notice_step=current.step
        return dict(level=current.level,step=current.step,recorded_transitions_at_level=len(recent)-1,
                    count_is_lower_bound=len(recent)==257,window_transitions=len(transitions),
                    repeated_visible_transitions=repeats,
                    unchanged_visible_transitions=sum(t[0]==t[2] for t in transitions))


def render_notice(evidence):
    if not evidence:return ''
    n=evidence['recorded_transitions_at_level']
    lower='at least ' if evidence['count_is_lower_bound'] else ''
    lines=[f'\nRecovery check: {lower}{n} recorded transitions at this level without a level boundary.']
    for repeat in evidence['repeated_visible_transitions'][:2]:
        lines.append(f"Same visible before/action/after repeated {repeat['count']} times: {repeat['action']} (steps {repeat['first_step']}..{repeat['last_step']}).")
    lines.append('A long level or identical pixels do not prove failure: waiting, timing and hidden state may matter. '
                 'Before another costly attempt, check recall() for counterexamples. State the uncertain goal or rule '
                 'and one test that separates alternatives; reuse a failed test only with a changed condition or timing reason. '
                 'If dynamics are supported, compute a shorter route before acting. Ordinary actions remain available.')
    return '\n'.join(lines)[:1000]
