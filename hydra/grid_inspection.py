"""Exact, bounded inspection of already-observed letter-coded frames.

Coordinates are always raw zero-based (row, col). Rectangle/run stops are
exclusive. Sampling reports pixels, not inferred objects or logical cells.
"""


def install(namespace):
    events=[]

    def integer(value,label):
        if type(value) is not int:raise ValueError(label+' must be an integer')
        return value

    def select(frame,step):
        if frame is not None and step is not None:raise ValueError('Choose frame OR observed step')
        known=[getattr(entry,'frame',None) for entry in namespace.get('history',[])]
        known.append(namespace.get('current_frame'))
        if frame is not None and not any(frame is observed for observed in known):
            raise ValueError('Frame is not in supplied observation history')
        if step is not None:
            integer(step,'step')
            matches=[f for f in known if f is not None and f.step==step]
            if not matches:raise ValueError('Step is not in supplied observation history')
            if len({(f.level,f.ascii) for f in matches})!=1:
                raise ValueError('Step is ambiguous; pass an observed frame explicitly')
            frame=matches[-1]
        elif frame is None:frame=namespace.get('current_frame')
        if frame is None:raise ValueError('No observed frame selected')
        rows=frame.ascii.splitlines()
        if not rows or not rows[0] or len(rows)>128 or len(rows[0])>128:
            raise ValueError('Expected a nonempty letter grid at most 128 x 128')
        if any(len(row)!=len(rows[0]) for row in rows):raise ValueError('Grid must be rectangular')
        if hasattr(frame,'shape') and tuple(frame.shape)!=(len(rows),len(rows[0])):
            raise ValueError('ASCII dimensions disagree with frame shape')
        return frame,rows

    def base(frame):
        return dict(step=frame.step,level=frame.level,coordinate_order='row,col',zero_based=True)

    def log(tool,frame,**details):
        if len(events)<64:events.append(dict(tool=tool,step=frame.step,level=frame.level,**details))
        else:events[-1]['additional_calls_not_logged']=events[-1].get('additional_calls_not_logged',0)+1

    def read_cells(points,*,frame=None,step=None):
        frame,rows=select(frame,step)
        if not isinstance(points,(list,tuple)) or not 1<=len(points)<=64:
            raise ValueError('Read 1..64 explicit (row,col) points')
        cells=[]
        for point in points:
            if not isinstance(point,(list,tuple)) or len(point)!=2:raise ValueError('Use (row,col) points')
            row,col=point;integer(row,'row');integer(col,'col')
            if not 0<=row<len(rows) or not 0<=col<len(rows[0]):raise ValueError('Point outside observed grid')
            cells.append(dict(row=row,col=col,color=rows[row][col]))
        log('read_cells',frame,returned_cells=len(cells))
        return dict(**base(frame),cells=cells)

    def read_region(bounds,*,stride=(1,1),frame=None,step=None):
        frame,rows=select(frame,step)
        if not isinstance(bounds,(list,tuple)) or len(bounds)!=4:raise ValueError('Use (row_start,row_stop,col_start,col_stop)')
        if not isinstance(stride,(list,tuple)) or len(stride)!=2:raise ValueError('Use positive (row_stride,col_stride)')
        r0,r1,c0,c1=bounds;dr,dc=stride
        for value in (*bounds,*stride):integer(value,'coordinate/stride')
        if not 0<=r0<r1<=len(rows) or not 0<=c0<c1<=len(rows[0]) or dr<1 or dc<1:
            raise ValueError('Bounds/stride outside observed grid')
        rr=list(range(r0,r1,dr));cc=list(range(c0,c1,dc))
        if len(rr)*len(cc)>256:raise ValueError('At most 256 sampled pixels; crop or increase stride')
        colors=[''.join(rows[r][c] for c in cc) for r in rr]
        log('read_region',frame,bounds=list(bounds),stride=list(stride),returned_cells=len(rr)*len(cc))
        return dict(**base(frame),bounds=list(bounds),stop_exclusive=True,
            row_coordinates=rr,col_coordinates=cc,colors=colors,sampling='exact pixels, not cell aggregation')

    def row_runs(row,*,cols=None,frame=None,step=None):
        frame,rows=select(frame,step);integer(row,'row')
        if not 0<=row<len(rows):raise ValueError('Row outside observed grid')
        if cols is None:cols=(0,len(rows[0]))
        if not isinstance(cols,(list,tuple)) or len(cols)!=2:raise ValueError('Use (col_start,col_stop)')
        start,stop=cols;integer(start,'col_start');integer(stop,'col_stop')
        if not 0<=start<stop<=len(rows[0]):raise ValueError('Columns outside observed grid')
        runs=[];i=start
        while i<stop:
            end=i+1
            while end<stop and rows[row][end]==rows[row][i]:end+=1
            runs.append(dict(col_start=i,col_stop=end,color=rows[row][i]));i=end
        log('row_runs',frame,row=row,cols=list(cols),returned_runs=len(runs))
        return dict(**base(frame),row=row,stop_exclusive=True,runs=runs)

    namespace.update(read_cells=read_cells,read_region=read_region,row_runs=row_runs)
    return events
