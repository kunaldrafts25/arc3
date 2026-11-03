---
license: cc-by-4.0
pretty_name: "How Humans Learn Unfamiliar Worlds: A Think-Aloud Dataset on ARC-AGI-3"
language:
- en
- zh
tags:
- arc-agi-3
- think-aloud
- interactive-learning
- world-models
- human-ai-comparison
- audio
- text
size_categories:
- n<1K
configs:
- config_name: default
  data_files:
  - split: corpus
    path: metadata.jsonl
---

# ARC3 Human Think-Aloud

ARC3 Human Think-Aloud records human learning and problem solving in 25 public ARC-AGI-3 games. It pairs gameplay actions and visual observations with concurrent think-aloud recordings and time-stamped transcripts, making it possible to study how understanding develops over the course of an interaction. The dataset also includes LLM agent trajectories on the same games for comparative analysis.

The dataset accompanies [*How Humans Learn Unfamiliar Worlds: A Think-Aloud Dataset on ARC-AGI-3*](https://arxiv.org/abs/2610.34523), by Shuzhi Liu, Archana Warrier, Dat Nguyen, Chengqi Zheng, Kevin Ellis, and Yewen Pu.

[Paper (arXiv:2610.34523)](https://arxiv.org/abs/2610.34523) · [Project website and interactive explorer](https://arc3-human-think-aloud.github.io/)

## Dataset Overview

| | Human participants | LLM agents |
| --- | --- | --- |
| Games | 25 | The same 25 games |
| Participants / configurations | 64 participants | 10 model–harness configurations |
| Trajectories | 144 successful trajectories | 250 trajectories, including successful and unsuccessful runs |
| Actions | 136,876 | 99,930 |
| Verbal records | Think-aloud audio and transcripts | Available public reasoning records |

Human recordings are provided as **147 game/session audio clips**. The shared annotation framework covers **354 game mechanisms** and three aspects of interaction: mechanism triggering and recognition, action purposes, and errors and recovery.

The data support research on world-model learning, exploration, hypothesis testing, planning, and error recovery, as well as comparisons between human and LLM approaches to interactive problem solving.

## Data Collection

Human participants were recruited through Prolific. After study instructions, consent, a microphone check, interface training, and a think-aloud attention check, participants explored unfamiliar games while verbalizing their thoughts. Gameplay actions and speech were recorded concurrently. Audio is accompanied by automatically generated transcripts.

The agent collection contains 100 trajectories from direct LLM configurations and 150 from configurations using VISTA, Schema, OPINE-World, or the Provider Adapter. Each configuration contributes one trajectory for each of the 25 games, with its actions, outcome, and available public reasoning.

## Annotation Framework

Annotations connect behavior and verbal evidence to three questions:

| Annotation | What it captures |
| --- | --- |
| **Mechanism triggering and recognition** | When a game mechanism is encountered and when the learner shows evidence of understanding it. |
| **Action purposes** | Whether actions pursue a goal, gather information, or serve both purposes, including exploration and hypothesis testing. |
| **Errors and recovery** | Mistaken mechanism beliefs, planning failures, execution errors, and subsequent corrections. |

Game mechanisms were defined by the authors. Trajectory annotation combines programmatic trigger detection with AI-assisted analysis of actions and verbal evidence, with author spot checks. Each game's `mechanisms.json` defines its mechanisms; each trajectory's `annotations.json` contains the associated labels, action ranges, and supporting evidence.

## Data Organization

Human data are organized by **game / participant**, and agent data by **game / harness / configuration**:

```text
games/
└── ar25/
    ├── mechanisms.json
    ├── P02/
    │   ├── metadata.json
    │   ├── audio.mp3
    │   ├── actions.json
    │   ├── observed_actions.json
    │   ├── transcript.json
    │   ├── transcript.txt
    │   ├── annotations.json
    │   ├── timeline.json
    │   └── timeline.json.gz
    ├── P03/
    │   └── ...
    └── llm/
        └── direct/
            └── anthropic-claude-opus-5-high/
                ├── metadata.json
                ├── actions.json
                ├── reasoning.json
                ├── annotations.json
                ├── timeline.json
                └── timeline.json.gz
```

Participants are identified by pseudonyms `P01`–`P64`, which are consistent across games. Human trajectory IDs combine the pseudonym and game, for example `P28__ls20`. Original recruitment identifiers are not included. A trajectory with multiple sessions has numbered audio, transcript, and timeline files, such as `audio_01.mp3` and `audio_02.mp3`, in the same participant folder.

| File | Contents |
| --- | --- |
| `metadata.json` | Trajectory information, session descriptions, and paths to the associated files. |
| `audio.mp3` | Think-aloud recording for the game/session. |
| `actions.json` | Canonical action sequence and trajectory information. |
| `observed_actions.json` | Logged human inputs, including undo operations and available timing information. |
| `transcript.json` / `transcript.txt` | Time-stamped utterances and a readable text version. |
| `annotations.json` | Mechanism, action-purpose, and error/recovery annotations. |
| `timeline.json` / `timeline.json.gz` | Game frames linked to human timestamps or agent action steps; both files contain the same data. |
| `reasoning.json` | Public agent reasoning linked to action steps. |

At the repository root, `index.json` lists games and trajectories, and `metadata.jsonl` provides a tabular index for the Hugging Face Dataset Viewer. The `corpus` split contains one index row per trajectory; audio and detailed records are available through the listed paths.

Agent timelines provide the resulting game frame after each action. In `action_frames`, entry `n - 1` gives the index in `frames` for action `n`. Each frame stores its width (`w`), height (`h`), and row-major run-length encoding (`runs`); for each integer `r`, `r >> 4` is the run length and `r & 15` is the color index in the root index's `palette`.

Transcripts use seconds relative to each session segment; timeline timestamps use milliseconds. Session metadata supplies the audio offset. Annotation action ranges are one-based and inclusive, referring to the canonical action sequence rather than positions in the observed-input log.

## Getting Started

Install the Hugging Face client:

```bash
pip install -U huggingface_hub
```

Download and read one participant's data for a game:

```python
import json
from pathlib import Path
from huggingface_hub import snapshot_download

root = Path(snapshot_download(
    repo_id="hellohawaii/ARC3-human-think-aloud",
    repo_type="dataset",
    allow_patterns=["games/ar25/P02/*"],
))
participant = root / "games/ar25/P02"

metadata = json.loads((participant / "metadata.json").read_text())
actions = json.loads((participant / metadata["actions"]).read_text())["actions"]
annotations = json.loads((participant / metadata["annotations"]).read_text())

segment = metadata["segments"][0]
audio_path = participant / segment["audio"]["path"]
transcript = json.loads((participant / segment["transcript"]).read_text())

print(f"Actions: {len(actions)}")
print(f"Audio: {audio_path}")
print(transcript["utterances"][0]["text"])
```

Remove `allow_patterns` to download the full dataset. To browse a particular game, use a pattern such as `games/ar25/**`.

## Citation

If you use this dataset, please cite:

```bibtex
@misc{liu2026humanslearnunfamiliarworlds,
      title={How Humans Learn Unfamiliar Worlds: A Think-Aloud Dataset on ARC-AGI-3}, 
      author={Shuzhi Liu and Archana Warrier and Dat Nguyen and Chengqi Zheng and Kevin Ellis and Yewen Pu},
      year={2026},
      eprint={2610.34523},
      archivePrefix={arXiv},
      primaryClass={cs.AI},
      url={https://arxiv.org/abs/2610.34523}, 
}
```

## License

The dataset is released under [CC BY 4.0](LICENSE). Third-party game assets and agent source materials remain subject to their respective licenses.
