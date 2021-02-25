def solve_cp(dataset, max_time = None):
    model = cp_model.CpModel()
    open_interv = {}
    interval_starts = {}
    interval_ends = {}
    for (_,_,_,s) in dataset.streets:
        interval_starts[s] = model.NewIntVar(0, dataset.D, name='street_start'+s)
        interval_ends[s] = model.NewIntVar(0,dataset.D, name = 'street_end'+s)
        duration = model.NewIntVar(0,dataset.D, name='street_duration'+s)
        open_interv[s] = model.NewIntervalVar(interval_starts[s], duration, interval_ends[s], name='interval'+s)

    cycle_duration = {}
    for n in dataset.graph:
        all_incoming_streets_tw = []
        all_ends = []
        cycle_duration[n] = model.NewIntVar(1, dataset.D, name='cycle'+str(n))
        for p in dataset.graph.predecessors(n):
            street = dataset.graph[p][n]['street']
            all_incoming_streets_tw.append(open_interv[street])
            all_ends.append(interval_ends[street])
        model.AddMaxEquality(cycle_duration[n], all_ends)
        model.AddNoOverlap(all_incoming_streets_tw)

    F = model.NewIntVar(0,1000**3, name='F')
    model.Add(F ==  dataset.bonus_unit)
    scores = []
    xs = []
    for i,car in enumerate(dataset.cars):
        cur_xs = []
        x = model.NewIntVar(0, 1, name='start'+str(i))
        cur_xs.append(x)
        for s in car:
            y = model.NewIntVar(0,100*dataset.D, name='stop'+str(i)+' '+s)
            model.Add(y >= cur_xs[-1] + dataset.street_to_intersections[s][2])
            street_end = dataset.street_to_intersections[s][1]
            depart_mod = model.NewIntVar(0,dataset.D, name='depart-mod'+str(i)+' '+s)
            model.AddModuloEquality(depart_mod,y, cycle_duration[street_end])
            model.Add( interval_starts[s] <= depart_mod < intervals_starts[s])
            cur_xs.append(y)
        arrived_in_time = model.NewBoolVar(name='arrived '+str(i))
        model.Add(cur_xs[-1] <= dataset.D-1).OnlyEnforceIf(arrived_in_time)
        model.Add(cur_xs[-1] > dataset.D-1).OnlyEnforceIf(arrived_in_time.Not())
        score = model.NewIntVar(0, 1000**3, name='score '+str(i))
        add_to_score = model.NewBoolVar(name="add_to_score"+str(i))
        model.Add(score ==  F + dataset.D - 1 - cur_xs[-1]).OnlyEnforceIf(arrived_in_time)
        model.Add(score == 0).OnlyEnforceIf(arrived_in_time.Not())
        scores.append(score)
        xs.append(cur_xs)
    model.Maximize(sum(scores))
    solver = cp_model.CpSolver()
    if max_time is not None:
        solver.parameters.max_time_in_seconds = 10.0
    status = solver.Solve(model)
    print('Status = %s' % solver.StatusName(status))

    res = {}
    for n in dataset.graph:
        s = []
        intervals= []
        for p in dataset.graph.predecessors(n):
            street = dataset.graph[p][n]['street']
            inter = (solver.Value(interval_starts[street]), solver.Value(interval_ends[street]), street)
            if inter[1] > inter[0]:
                intervals.append(inter)
        sorted_intervals = sorted(intervals)
        print(n,sorted_intervals)
        deb = 0
        for i in range(len(intervals)):
            if i == len(intervals)-1:
                end = intervals[i][1]
            else:
                end = intervals[i+1][0]
            if n == 1:
                print(intervals[i])
            for j in range(deb, end):
                s.append(intervals[i][2])
            deb = end
        res[n] = s
    print(res)
    return res

