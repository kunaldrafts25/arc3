"""Game-independent research protocol; no public-game solutions or IDs."""
GUIDANCE='''

Learn the unfamiliar game through evidence and mathematics:
- Keep controls, relevant state/mode, mechanics, goals and resource costs separate.
  A legal input or a changed counter does not prove useful gameplay progress.
- Choose small experiments that distinguish competing explanations. State the
  expected difference briefly, then compare with the actual observation. Repeated
  inert inputs need a new reason: changed mode, selection, timing or prerequisite.
- When predictions fail, inspect actor identity, selection, mode, camera, timing,
  collision and missing prerequisites before discarding supported physics. Keep
  goal uncertainty separate: correct movement does not establish the win condition.
- Use the smallest predictive representation. Navigation needs actor footprint,
  stride and collision/door rules. Rigid geometry needs measured rotation anchoring,
  relative contact points and free approach paths. Fixed-slot rearrangements suggest
  permutation/cycle algebra: test inverses and composition, including overlapping
  controls. Track only goal-relevant token positions when other colors cannot affect
  dynamics, but compare fuller observations to detect a bad abstraction.
- Binary toggle algebra over GF(2) needs tested state-independent effects and
  appropriate repeat/commutation checks. Symbolic ordering/resource puzzles can use
  constraint solving. Hidden state needs conditional hypotheses. Use game-theoretic
  adversarial reasoning only if an actual opponent or justified adversarial model
  exists. Search cannot fix an incorrect simulator, representation or goal.
- Ordinary action batches/repeated calls remain available. Use short plans under
  uncertainty and efficient longer plans when evidence supports them; stop/replan
  at contradictions or actual boundaries. Complete simulation is optional. Do not
  spend the run repairing a simulator when a simpler representation or probe helps.
- Preserve concise working hypotheses with remember(key, claim, kind='mechanics',
  status='hypothesis', evidence_steps=[], scope='level', condition=''). Kinds are
  control/state/mechanics/goal/resource; statuses hypothesis/supported/contradicted.
  Supported or contradicted notes need real observed frame.step references, at most
  six. These references do not certify causality or goals. Use scope='game' for
  transferable mechanics; prior-level notes must be rechecked. Update a short key
  instead of accumulating a story. remember(key,None) removes a stale note.
  recall() returns the bounded notebook (10 notes, claims <=240 characters).
- Notes survive Python-call resets and context drains. A compact panel reappears
  on later turns. Do not repeat lengthy explanations or force a note on every
  action; record discoveries, contradictions, goal revisions and the next useful
  test. Use literal defaults/arguments for retained-function dependencies.
- Actual level/game completion is the outcome evidence. Transfer rules as
  hypotheses at a new level, rechecking mode, goals and new objects. Spend moves,
  time and reasoning on information that changes the next decision.
'''
