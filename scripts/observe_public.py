"""Capture public observations and action effects, without game internals."""
import json
from pathlib import Path
import sys
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT/"vendor/ARC-AGI-3-Agents"))
from arc_agi import Arcade, OperationMode
from arc_agi.rendering import COLOR_MAP, hex_to_rgb
from arcengine import GameAction, GameState
from agent.my_agent import MyAgent
from hydra.perception import grid_diff

destination = ROOT/"reports/v02/observations"
destination.mkdir(parents=True, exist_ok=True)
arcade = Arcade(operation_mode=OperationMode.OFFLINE)
palette = np.array([hex_to_rgb(COLOR_MAP[i]) for i in range(16)], dtype=np.uint8)
games = ["ls20", "ft09", "vc33", "r11l"]
indices = [0, 1, 2, 3, 4, 8, 16, 32]
sheet = Image.new("RGB", (8*256, len(games)*282), "#202025")
draw = ImageDraw.Draw(sheet)
for row, game in enumerate(games):
    env = arcade.make(game, seed=0)
    if env is None:
        raise RuntimeError(game)
    agent = MyAgent(card_id="diagnostic", game_id=game, agent_name="diagnostic",
                    ROOT_URL="http://localhost", record=False, arc_env=env)
    frame = agent._convert_raw_frame_data(env.observation_space)
    grids = [np.asarray(frame.frame[-1], dtype=np.int16)]
    records = [{"step": 0, "state": frame.state.name, "level": frame.levels_completed}]
    for step in range(1, 33):
        simple = [a for a in frame.available_actions if 1 <= a <= 5]
        if simple and frame.state == GameState.NOT_FINISHED:
            # Isolated action probes, then longer repeated runs.
            action = GameAction.from_id(simple[(step-1) % len(simple)] if step <= 8 else simple[((step-9)//4) % len(simple)])
            action.set_data({"game_id": game})
            agent._payload = {"game_id": game}
        else:
            action = agent.choose_action(agent.frames, frame)
        previous = grids[-1]
        frame = agent.take_action(action)
        if frame is None or not frame.frame:
            raise RuntimeError("Missing diagnostic frame")
        agent.append_frame(frame)
        agent.action_counter += 1
        grid = np.asarray(frame.frame[-1], dtype=np.int16)
        grids.append(grid)
        records.append(dict(step=step, action=action.value, data=agent._payload.copy(),
                            state=frame.state.name, level=frame.levels_completed,
                            difference=grid_diff(previous, grid)))
    np.savez_compressed(destination/(game+".npz"), frames=np.stack(grids))
    (destination/(game+".json")).write_text(json.dumps(records, indent=2), encoding="utf-8")
    for column, index in enumerate(indices):
        image = Image.fromarray(palette[grids[index]]).resize((256, 256), Image.Resampling.NEAREST)
        sheet.paste(image, (column*256, row*282+26))
        record = records[index]
        draw.text((column*256+4, row*282+6), f"{game} step {index} action {record.get('action', '-')} level {record['level']}", fill="white")
    print(json.dumps({"game":game, "actions":frame.available_actions, "levels":frame.levels_completed,
                      "differences":[r.get("difference") for r in records[1:9]]}))
sheet.save(destination/"contact-sheet.png")
