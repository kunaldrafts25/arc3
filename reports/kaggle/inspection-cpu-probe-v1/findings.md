# Exact inspection CPU gate

Exact version `kunalsinghh25/arc-hydra-inspection-cpu-probe/1` is COMPLETE.
`inspection-probe.json` records seven passing cases: historical pixel reading
and telemetry, correct absolute/exclusive run endpoints, coordinate-labelled
sampling, unknown steps, negative indices, actual host results/event persistence
and game isolation. The original eight mechanical and 16 prompt cases also pass.

The local full suite passed 124 tests, including nine inspection tests. No model
inference or competition gameplay was performed in this CPU gate. The generated
notebook/source manifest hashes were recorded before completion. The gameplay
packager verifies those hashes and current source hashes, and checks actual
installed reports against the completed gate at runtime.

The new helper interface is based on the preserved flexible optional-planning
agent, without study memory or recovery additions. Original models, serving,
scheduler, ordinary actions and existing guards remain unchanged. A concrete
model-written coordinate arithmetic bug motivated the experiment; offering a
correct helper does not establish that the model will adopt it or solve more
games. Adoption events are bounded with explicit overflow counts.

`notebooks/inspection_candidate` uses all 25 games and a 32,400-second whole
notebook budget including startup and a 600-second finalization reserve.
It has not been launched. Score improvement remains unverified.
