print('Starting benchmark...')

# Build the live competition game list from the gateway's available environments.
def _competition_games():
    import arc_agi

    import taaf.game_api

    spec = taaf.game_api.ArcadeSpec(
        operation_mode=arc_agi.OperationMode.COMPETITION,
        arc_base_url=os.environ["ARC_BASE_URL"],
        environments_dir="",
    )
    arcade = arc_agi.Arcade(
        operation_mode=arc_agi.OperationMode.COMPETITION,
        arc_base_url=spec.arc_base_url,
        environments_dir="",
    )
    game_ids = [env_info.game_id for env_info in arcade.available_environments]
    if not game_ids:
        raise RuntimeError("Competition Arcade exposed zero environments.")
    return [taaf.game_api.GameAPI(env_name=game_id, arcade_spec=spec) for game_id in game_ids]


# Build the offline game list from the competition's bundled environment files.
def _offline_games(env_dir: str):
    import arc_agi

    import taaf.game_api

    spec = taaf.game_api.ArcadeSpec(operation_mode=arc_agi.OperationMode.OFFLINE, environments_dir=env_dir)
    arcade = arc_agi.Arcade(operation_mode=arc_agi.OperationMode.OFFLINE, environments_dir=env_dir)
    game_ids = [env_info.game_id for env_info in arcade.available_environments]
    if not game_ids:
        raise RuntimeError(f"No offline environments found under {env_dir}.")
    game_ids = [game_id for game_id in game_ids if not any(game_id.startswith(g) for g in demo_excluded_games)]
    return [taaf.game_api.GameAPI(env_name=game_id, arcade_spec=spec) for game_id in game_ids]


# The gateway can take a while to come up; poll until it answers.
def _wait_for_gateway(base_url: str, timeout_s: float = 600.0) -> None:
    deadline = time.monotonic() + timeout_s
    last_error = ""
    while time.monotonic() < deadline:
        try:
            with urlopen(f"{base_url}api/games", timeout=10) as response:
                if response.status < 500:
                    return
        except Exception as exc:
            last_error = repr(exc)
        time.sleep(5)
    raise RuntimeError(f"Kaggle gateway did not become ready: {last_error}")


# Print the run preamble and persist the launcher's git status for diagnostics.
#print((BUNDLE_DIR / "preamble.txt").read_text())
(WORKING_DIR / "git_status.txt").write_text((BUNDLE_DIR / "git_status.txt").read_text())

# arc_agi reads RECORDINGS_DIR and ARC_API_KEY from env (ArcadeSpec carries neither); operation
# mode, environments dir, and base url are all passed explicitly via the spec, so no env is needed.
os.environ.setdefault("RECORDINGS_DIR", str(WORKING_DIR / "server_recording"))

if TRUE_SUBMISSION:
    # Real submission: play the live competition Arcade served by the Kaggle gateway.
    os.environ.setdefault("ARC_API_KEY", "test-key-123")
    os.environ.setdefault("ARC_BASE_URL", "http://gateway:8001/")
    # The gateway boots asynchronously; wait before swapping in its game list.
    _wait_for_gateway(os.environ["ARC_BASE_URL"])
    bm.games = _competition_games()
else:
    # Interactive run: play the bundled competition environments offline (no gateway).
    # The competition's environment files ship alongside the wheelhouse in the competition dataset.
    competition_env_files = str(Path("/kaggle/input/competitions/arc-prize-2026-arc-agi-3/arc_agi_3_wheels").parent / "environment_files")
    bm.games = _offline_games(competition_env_files)

# Preserve official gateway and submission budget path.
soft_end = None
if TRUE_SUBMISSION:
    # A single absolute notebook budget; startup is part of the nine hours.
    official_end_epoch = NOTEBOOK_START_TIME + 9*60*60 - 600
    remaining = official_end_epoch - time.time()
    if remaining <= 0:
        raise TimeoutError('Official notebook budget exhausted before gameplay')
    soft_end = datetime.fromtimestamp(official_end_epoch)
    bm.solver.max_runtime_s_per_game = min(bm.solver.max_runtime_s_per_game, remaining)
    if hasattr(bm, 'periodic_save_interval_s'):
        bm.periodic_save_interval_s = min(float(bm.periodic_save_interval_s or 60), 60)
    (WORKING_DIR/'V31_OFFICIAL_PREFLIGHT.json').write_text(json.dumps({
        'official':True,'game_count':len(bm.games),'notebook_start':NOTEBOOK_START_TIME,
        'soft_end_epoch':official_end_epoch,'remaining_seconds':remaining,
        'gateway':os.environ.get('ARC_BASE_URL'),
        'model_ready_policy':'original warmup RESET and bounded analyzer retries retained'},indent=2))
if 'proc' in globals() and proc.poll() is not None:
    raise RuntimeError(f'SGLang exited ({proc.returncode}); benchmark cancelled')
if not TRUE_SUBMISSION:
    from budget import preflight, gameplay_deadline
    hard_budget = float(target.max_runtime_s)
    hard_start = NOTEBOOK_START_TIME
    remaining = hard_start + hard_budget - min(600.0,hard_budget/2) - time.time()
    if remaining <= 0:
        raise TimeoutError('Notebook budget exhausted before readiness')
    print('V31 LOCAL PREFLIGHT: completion required before gameplay clock',flush=True)
    preflight(f'http://127.0.0.1:{SERVED_MODEL_PORT}',SERVED_MODEL_NAME,
              timeout=min(2100.0,remaining),process=globals().get('proc'))
    ready_epoch=time.time()
    end_epoch=gameplay_deadline(hard_start,ready_epoch,hard_budget,
                              play_budget=float(bm.solver.max_runtime_s_per_game))
    soft_end=datetime.fromtimestamp(end_epoch)
    (WORKING_DIR/'V31_timing.json').write_text(json.dumps({
        'notebook_start_epoch':hard_start,'ready_epoch':ready_epoch,
        'startup_seconds':ready_epoch-hard_start,'soft_end_epoch':end_epoch,
        'play_budget_seconds':end_epoch-ready_epoch,'hard_budget_seconds':hard_budget},indent=2))
    if len(bm.games)!=10:
        raise RuntimeError(f'V31 expects 10 local games, got {len(bm.games)}')

# Play the benchmark; teardown commands run even if the run raises.
try:
    await bm.run(soft_end_time=soft_end, runtime_environment=target, minimal_diagnostics=TRUE_SUBMISSION)
finally:
    if not TRUE_SUBMISSION:
        from summarize_verification import summarize
        _v31_metrics=summarize(WORKING_DIR)
        (WORKING_DIR/'V31_verification_summary.json').write_text(json.dumps(_v31_metrics,indent=2))
        print('V31_VERIFICATION_SUMMARY',json.dumps(_v31_metrics))

if not TRUE_SUBMISSION:
    # An offline run isn't scored, but Kaggle still expects a submission.parquet output.
    import pandas as pd

    pd.DataFrame(
        [["1_0", "1", True, 1]],
        columns=["row_id", "game_id", "end_of_game", "score"],
    ).to_parquet(WORKING_DIR / "submission.parquet", index=False)
if TRUE_SUBMISSION:
    _submission = WORKING_DIR/'submission.parquet'
    if not _submission.is_file() or _submission.stat().st_size == 0:
        raise RuntimeError('Official benchmark returned without submission.parquet; refusing a dummy result')
    import pandas as pd
    _submitted = pd.read_parquet(_submission)
    if _submitted.empty:
        raise RuntimeError('Official submission.parquet has no rows')
    (WORKING_DIR/'V31_OFFICIAL_RESULT.json').write_text(json.dumps({
        'rows':len(_submitted),'columns':list(_submitted.columns),
        'bytes':_submission.stat().st_size,'finished_epoch':time.time()},indent=2))
