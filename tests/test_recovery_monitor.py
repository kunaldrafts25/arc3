from types import SimpleNamespace as NS

from hydra.recovery_monitor import RecoveryMonitor,render_notice


def observations(n,level=1,cycle=None,action='WAIT'):
    return [NS(action=action,frame=NS(step=i,level=level,grid=((i%cycle if cycle else 0,),))) for i in range(n+1)]


def test_same_screen_waiting_is_advisory_and_can_reach_delayed_reward():
    monitor=RecoveryMonitor();notices=[];state=0
    # Hidden timer advances despite identical public pixels. An advisory monitor
    # has no authority to reject the valid waiting strategy.
    for i in range(97):
        history=observations(i)
        report=monitor.observe(history[-1].frame,history)
        if report:notices.append(report)
        state+=1
    assert state==97 and len(notices)==2
    assert notices[0]['unchanged_visible_transitions']==64
    assert 'do not prove failure' in render_notice(notices[0])
    assert 'Ordinary actions remain available' in render_notice(notices[0])


def test_changed_prerequisite_is_not_reported_as_same_transition():
    history=observations(70,cycle=2,action='RIGHT')
    # A new visible mode/selection changes the transition even if input repeats.
    history[-1].frame.grid=((9,),)
    report=RecoveryMonitor().observe(history[-1].frame,history)
    assert report and all(r['last_step']<70 for r in report['repeated_visible_transitions'])


def test_level_boundary_and_game_restart_clear_old_evidence():
    monitor=RecoveryMonitor();history=observations(100)
    assert monitor.observe(history[-1].frame,history)
    new=observations(4,level=2)
    assert monitor.observe(new[-1].frame,history+new) is None
    restarted=observations(70)
    assert monitor.observe(restarted[-1].frame,restarted)


def test_new_boards_do_not_create_a_fictitious_repeat():
    history=observations(75,cycle=100)
    report=RecoveryMonitor().observe(history[-1].frame,history)
    assert report['repeated_visible_transitions']==[]
    assert report['unchanged_visible_transitions']==0


def test_cooldown_avoids_repeated_notices_without_new_actions():
    monitor=RecoveryMonitor();history=observations(70,cycle=3)
    report=monitor.observe(history[-1].frame,history)
    assert report
    for _ in range(20):assert monitor.observe(history[-1].frame,history) is None
    assert len(render_notice(report))<=1000


def test_truncated_history_is_explicit_and_stale_current_is_ignored():
    history=observations(600)
    report=RecoveryMonitor().observe(history[-1].frame,history)
    assert report['count_is_lower_bound'] and report['recorded_transitions_at_level']==256
    assert 'at least' in render_notice(report)
    assert RecoveryMonitor().observe(history[-2].frame,history) is None
