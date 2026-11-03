"""Observation/action-only public Arcade session for direct research play.

No game implementation or hidden environment state is inspected. The local
bridge preserves live sessions so the researcher can choose successive probes.
"""
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import logging
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image, ImageDraw
from arc_agi import Arcade, OperationMode
from arcengine import GameAction
from hydra.perception import components, grid_diff

OUTPUT=ROOT/'reference/manual-play/2026-10-28'
COLORS=['#FFFFFF','#CCCCCC','#999999','#666666','#333333','#000000',
        '#E53AA3','#F93C31','#F98016','#FFDC00','#8FCC48','#1E93FF',
        '#83D6F2','#4FBE9F','#A356D6','#C4A484']


class Session:
    def __init__(self):
        OUTPUT.mkdir(parents=True,exist_ok=True)
        self.arc=Arcade(operation_mode=OperationMode.OFFLINE)
        self.ids=sorted(e.game_id for e in self.arc.get_environments())
        self.games={}
        self.states={}
        self.counts=Counter()

    def observe(self,gid,observation,reason,prior=None,command=None):
        grid=np.asarray(observation.frame[-1],dtype=np.int16)
        count=self.counts[gid]
        short=gid.split('-')[0]
        image=Image.new('RGB',(grid.shape[1],grid.shape[0]))
        image.putdata([tuple(bytes.fromhex(COLORS[int(c)].lstrip('#'))) for c in grid.flat])
        image=image.resize((512,512),Image.Resampling.NEAREST)
        filename=OUTPUT/f'{short}-{count:04}.png'
        image.save(filename)
        record=dict(game=gid,index=count,command=command,reason=reason,
                    observed_at=datetime.now(timezone.utc).isoformat(),
                    state=observation.state.name,levels=observation.levels_completed,
                    total_levels=observation.win_levels,actions=list(observation.available_actions),
                    grid=grid.tolist(),image=str(filename),
                    diff=grid_diff(prior,grid) if prior is not None else None,
                    observation_sha256=sha256(grid.tobytes()).hexdigest())
        with (OUTPUT/'observations.jsonl').open('a',encoding='utf-8') as stream:
            stream.write(json.dumps(record)+'\n')
        self.states[gid]=record
        return self.summary(record)

    def summary(self,record):
        grid=np.asarray(record['grid'])
        return {**{k:v for k,v in record.items() if k!='grid'},
                'colors':dict(Counter(map(int,grid.flat))),
                'components':components(grid,limit=50,describe=True)}

    def start(self,gid):
        if gid not in self.ids:
            matches=[g for g in self.ids if g.split('-')[0]==gid]
            if len(matches)!=1:raise ValueError('Unknown public game')
            gid=matches[0]
        self.games[gid]=self.arc.make(gid,seed=0)
        self.counts[gid]=0
        return self.observe(gid,self.games[gid].reset(),'Initial public observation; no gameplay conclusion')

    def step(self,gid,commands,reason):
        matches=[g for g in self.games if g==gid or g.split('-')[0]==gid]
        if len(matches)!=1:raise ValueError('Start the public game first')
        gid=matches[0]
        if not reason or not 1<=len(commands)<=16:raise ValueError('Require rationale and 1..16 actions')
        results=[]
        for command in commands:
            prior=np.asarray(self.states[gid]['grid'])
            prior_levels=self.states[gid]['levels']
            action_id=int(command['action'])
            action=GameAction['RESET' if action_id==0 else f'ACTION{action_id}']
            obs=self.games[gid].step(action,data=command.get('data'))
            if obs is None:raise ValueError('No observation returned')
            self.counts[gid]+=1
            result=self.observe(gid,obs,reason,prior,command)
            results.append(result)
            if result['state'] in ('WIN','GAME_OVER') or result['levels']>prior_levels:
                break
        return results

    def survey(self):
        for gid in self.ids:self.start(gid)
        sheet=Image.new('RGB',(1280,1400),'#eeeeee')
        draw=ImageDraw.Draw(sheet)
        for index,gid in enumerate(self.ids):
            state=self.states[gid]
            x,y=(index%5)*256,(index//5)*280
            tile=Image.open(state['image']).resize((256,256),Image.Resampling.NEAREST)
            sheet.paste(tile,(x,y+24))
            draw.text((x+5,y+5),gid.split('-')[0]+' actions='+str(state['actions']),fill='black')
        sheet.save(OUTPUT/'initial-survey.png')
        (OUTPUT/'manifest.json').write_text(json.dumps([self.summary(r) for r in self.states.values()],indent=2),encoding='utf-8')
        print(json.dumps(dict(public_games=len(self.ids),survey=str(OUTPUT/'initial-survey.png'))),flush=True)


def main():
    logging.getLogger().setLevel(logging.ERROR)
    session=Session()
    session.survey()
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_POST(self):
            try:
                request=json.loads(self.rfile.read(int(self.headers.get('Content-Length','0'))))
                if self.path=='/step':
                    value=session.step(request['game'],request['commands'],request['reason'])
                elif self.path=='/start':value=session.start(request['game'])
                elif self.path=='/observe':
                    gid=next(g for g in session.states if g==request['game'] or g.split('-')[0]==request['game'])
                    value=session.summary(session.states[gid])
                else:raise ValueError('Unknown endpoint')
                payload=json.dumps(value).encode()
                self.send_response(200)
            except Exception as error:
                payload=json.dumps(dict(error=type(error).__name__+': '+str(error))).encode()
                self.send_response(400)
            self.send_header('Content-Type','application/json')
            self.end_headers()
            self.wfile.write(payload)
    print('Observation/action bridge at http://127.0.0.1:8788',flush=True)
    HTTPServer(('127.0.0.1',8788),Handler).serve_forever()


if __name__=='__main__':main()
