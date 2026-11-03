"""Render observed frames around a public level transition for diagnosis."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/"vendor/ARC-AGI-3-Agents")]
from arc_agi import Arcade, OperationMode
from arc_agi.rendering import COLOR_MAP, hex_to_rgb
from agent.my_agent import MyAgent
from hydra.clicks import tile_groups
from hydra.perception import components

parser = argparse.ArgumentParser()
parser.add_argument("game")
parser.add_argument("--steps", type=int, default=200)
parser.add_argument("--policy", default="reasoning")
parser.add_argument("--level", type=int, default=1)
args = parser.parse_args()
arcade = Arcade(operation_mode=OperationMode.OFFLINE)
game_id = next(g.game_id for g in arcade.get_environments() if g.game_id.split('-')[0] == args.game)
env = arcade.make(game_id, seed=0)
agent = MyAgent(card_id="diagnostic", game_id=game_id, agent_name="diagnostic", ROOT_URL="http://localhost",
                record=False, arc_env=env, hydra_policy=args.policy, hydra_seed=0)
agent.MAX_ACTIONS = args.steps
initial = agent._convert_raw_frame_data(env.observation_space)
agent.main()
frames = [initial]+agent.frames[1:]
transition = next((i for i, f in enumerate(frames) if f.levels_completed >= args.level), 1)
indices = sorted(set(min(len(frames)-1, max(0, transition+offset)) for offset in (-1, 0, 1, 8, 32, 64, 128, args.steps)))
palette = np.array([hex_to_rgb(COLOR_MAP[i]) for i in range(16)], dtype=np.uint8)
sheet = Image.new("RGB", (len(indices)*256, 280), "#222228")
draw = ImageDraw.Draw(sheet)
destination = ROOT/"reports/v02/observations"
for column, index in enumerate(indices):
    f = frames[index]
    grid = np.asarray(f.frame[-1], dtype=np.int16)
    image = Image.fromarray(palette[grid]).resize((256,256), Image.Resampling.NEAREST)
    sheet.paste(image, (column*256, 24))
    draw.text((column*256+4, 6), f"step {index} level {f.levels_completed} {f.state.name}", fill="white")
    if index == transition:
        groups = tile_groups(components(grid, describe=True))
        print("NEXT_LEVEL_GROUPS", json.dumps([[c["bbox"] for c in g] for g in groups]))
sheet.save(destination/(args.game+"-transition.png"))
np.savez_compressed(destination/(args.game+"-reasoning-run.npz"), frames=np.stack([f.frame[-1] for f in frames]),
                    levels=np.array([f.levels_completed for f in frames]))
print("STATS", json.dumps(dict(agent.controller.stats)))
print("CLICK_ACTIVE", bool(agent.clicks.active), "CLICK_STEPS", agent.clicks.steps)
print("LEARNED_GOAL_PROGRAMS", json.dumps(dict(agent.clicks.success_labels)))
print("LEARNED_GLYPH_COLORS", sorted(agent.clicks.glyph_colors))
