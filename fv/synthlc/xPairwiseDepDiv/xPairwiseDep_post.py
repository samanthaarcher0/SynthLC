##################
# * perfloc implication for DIV
##################
import pandas as pd
from itertools import combinations
import numpy as np
import os
import pandas as pd
import sys
sys.path.append("../../src")
from util import *
from HB_template import *
if len(sys.argv) != 2:
    print("gen/pp")
    exit(0)


HEADERFILE='../header.sv'
with open(HEADERFILE, "r") as f:
    lines = f.readlines()
h_ = "".join(lines[:-5])
e_ = "".join(lines[-5:])


HEADERTCL='../header.tcl'
htcl_ = ""
with open(HEADERTCL, "r") as f:
    for line in f:
        htcl_ += line


cv_perflocs = get_array("../xCoverAPerflocDiv/cover_individual.txt")
always_ = get_array("../xCoverAPerflocDiv/always_reach.txt")
perflocs = []
for itm in cv_perflocs:
    if not itm in always_:
        perflocs.append(itm)
print("power set of ", perflocs)

with open("../../../../user_provided_files/combined_pls.txt", "r") as f:
    combined_pls = f.readlines()
combined_pl_dict = get_combined_pls_dict(combined_pls)
pl_to_comb = dict()
for comb, pl_list in combined_pl_dict.items():
    for pl in pl_list:
        if pl_to_comb.get(pl) is not None:
            assert(0)
        else: 
            pl_to_comb[pl] = comb
print(f"combined PLs dict: {pl_to_comb}")

## Get iid map
iid_map = {}        
pl_signals = {}
with open("../../../xDUVPLs/perfloc_signals.txt", "r") as f:
    for line in f:
        pl, sigs = line[:-1].split(" : ")
        pl_signals[pl] = sigs.split(",")
for k, v in pl_signals.items():
    iid_map[k] = v[0]
# iid_map[pl_name] -> iid
for comb_pl, pl_list in combined_pl_dict.items():
    iid_map[comb_pl] =  iid_map[pl_list[0]]


# xCommon proven cases
# PLs for IID_1 are exclusive of PLs for IID_2
exclusive_set_iids = get_array("../../xCommon/exclusive_set_iids.txt", exit_on_fail=False)
# At least one of PLs for IID1 should be in the set if there is at least oen PL
# for IID_2
implication_set_iids = get_array("../../xCommon/implication_iid.txt", exit_on_fail=False)
implication_set_pls = get_array("../../xCommon/implication_pl.txt", exit_on_fail=False)
#edge = get_array("../../xGenPerfLocDfgDiv/dfg_e.txt")

#print(exclusive_set_iids)
cnt_reachable_pls_iid = {}
for itm in cv_perflocs:
    if iid_map.get(itm) is not None: 
        iid = iid_map[itm]
        if not iid in cnt_reachable_pls_iid:
            cnt_reachable_pls_iid[iid] = 0 
        cnt_reachable_pls_iid[iid] += 1 
    elif combined_pl_dict.get(itm) is not None:
        print("HERE!!!")
        for pl in combined_pl_dict.get(itm):
            iid = iid_map[pl]
            if not iid in cnt_reachable_pls_iid:
                cnt_reachable_pls_iid[iid] = 0
            cnt_reachable_pls_iid[iid] += 1 
print(cnt_reachable_pls_iid)
def dom(pc1, pc2):
    cnt1 = cnt_reachable_pls_iid[pc1]
    if cnt1 == 1:
        return ([pc1, pc2] in implication_set_iids)
    else:
        return False

JOB="rtl2mupath_pairwise_dep"

def gen():
    global htcl_
    print("========== gen ====================")
    if not os.path.isdir("out"):
        os.mkdir("out")
    print(len(perflocs))        
    log_skip = open("pairwise_common.txt", "w") 
    cnt = 0
    todolog = open("todo.log", "w")
    ff_ = f"{JOB}.sv"
    with open (ff_, "w") as f:
        f.write(h_)
    for idx in range(len(perflocs)):
        with open (ff_, "a") as f:
            f.write(hpn_reg_t2.format(s1 = perflocs[idx]))
    for idx in range(len(perflocs)):
        for idx2 in range(len(perflocs)):
            if idx != idx2:
                pc_1 = iid_map[perflocs[idx]]
                pc_2 = iid_map[perflocs[idx2]]
                #print(perflocs[idx], perflocs[idx2])
                exclusive_already = False
                if  [pc_1, pc_2] in exclusive_set_iids or \
                    [pc_2, pc_1] in exclusive_set_iids:
                    print("exclusive,%s,%s" % (perflocs[idx], perflocs[idx2]),
                            file=log_skip)
                    exclusive_already = True

                if dom(pc_1, pc_2):
                    print("impl,%s,%s" % (perflocs[idx], perflocs[idx2]),
                            file=log_skip)
                    assert (not exclusive_already)
                elif [perflocs[idx], perflocs[idx2]] in implication_set_pls: 
                    print("impl_pl,%s,%s" % (perflocs[idx], perflocs[idx2]),
                            file=log_skip)
                    assert (not exclusive_already)
                elif not exclusive_already: #if [perflocs[idx], perflocs[idx2]] in edge: 

                    print("imp,%s,%s,%d" % (perflocs[idx], perflocs[idx2],cnt), file=todolog)
                    with open (ff_, "a") as f:
                        s1 = perflocs[idx]
                        s2 = perflocs[idx2]
                        htcl_ += pair_dep_t2_tcl.format(s1=s1, s2=s2, cnt=cnt, prefix=prefix)

                imp_already = dom(pc_1, pc_2) or \
                    dom(pc_2, pc_1) or \
                    ([perflocs[idx2], perflocs[idx]] in implication_set_pls) or \
                    ([perflocs[idx], perflocs[idx2]] in implication_set_pls)
                if idx < idx2 and (not exclusive_already) and (not imp_already):
                    print("excl,%s,%s,%d" % (perflocs[idx], perflocs[idx2],cnt), file=todolog)
                    s1 = perflocs[idx]
                    s2 = perflocs[idx2]
                    htcl_ += c_two_pl_t_tcl.format(s1=s1, s2=s2, cnt=cnt, prefix=prefix)

                cnt += 1
    with open (ff_, "a") as f:
        f.write(e_)
    log_skip.close()
    todolog.close()

    ff_ = f"{JOB}.tcl"
    with open (ff_, "w") as f:
        f.write(htcl_)
        f.write(f"set props [get_property_list -include {{name cvr_rtl2mupath_*}}]\n")
        f.write("prove -property $props\n")
        f.write("report -property $props -csv -results -file %s.csv -force\n" % JOB)
        f.write("save %s.db -force\n" % JOB)
        f.write("file copy %s.csv %s/.\n" % (JOB, os.getcwd()))
        #f.write("exit\n")

def pp():
    print("========== pp ====================")
    log_skip = get_array("pairwise_common.txt") 
    dep_in_log = []
    excl_in_log = []
    for itm in log_skip:
        t, u, v = itm
        if "impl" in t:
            dep_in_log.append((u, v))
        else:
            excl_in_log.append((u, v))

    exclu = []
    dep = []

    undetermined_exclu = []
    undetermined_exclu_over_bound = []
    undetermined_exclu_under_bound = []
    undetermined_dep = []
    undetermined_dep_over_bound = []
    undetermined_dep_under_bound = []
    comps = []
    incomps = []

    counter_excl = 0
    counter_dep = 0
    bound = 20

    counter_undetermined_excl_over_bound = 0
    counter_undetermined_dep_over_bound = 0
    counter_undetermined_excl = 0
    counter_undetermined_dep = 0
    counter_covered = 0
    todo_items = get_array("todo.log")
    for itm in todo_items:
        ff = f"{JOB}.csv"  
        assert(os.path.exists(ff))
        df = pd.read_csv(ff, dtype=mydtypes)

        #ff2 = "cover_individual_2.csv"  
        #assert(os.path.exists(ff2))
        #df2 = pd.read_csv(ff, dtype=mydtypes)
        
        prop, pl1, pl2, cnt = itm
        if prop == "excl":
            prop = 'cvr_rtl2mupath_C_%s' % cnt

            res, bnd, time = df_query(df, prop, exact_name=True)
            #res2, bnd2, time2 = df_query(df2, prop)

            if res == "unreachable" or res == "bounded_unreachable_user":
                # idx2 implies idx
                exclu.append((pl1, pl2)) #perflocs[idx], perflocs[idx2]))
                counter_excl += 1
            elif res == 'undetermined' or res=="processing":
                #max_bnd = max(bnd, bnd2)
                max_bnd = bnd
                undetermined_exclu.append((pl1, pl2, int(max_bnd))) #perflocs[idx], perflocs[idx2]))
                if int(max_bnd) >= bound:
                    undetermined_exclu_over_bound.append((pl1, pl2, int(max_bnd)))
                    counter_undetermined_excl_over_bound += 1
                else:
                    undetermined_exclu_under_bound.append((pl1, pl2, int(max_bnd)))
                    counter_undetermined_excl += 1
            else:
                counter_covered += 1

            if res in ["covered", "unreachable", "cex", "proven", "bounded_unreachable_user"]:
                comps.append(time)
            else:
                incomps.append((time, bnd))

        else:
            prop = 'cvr_rtl2mupath_DEP_%s_b' % cnt
            res, bnd, time = df_query(df, prop, exact_name=True)
            #res2, bnd2, time2 = df_query(df2, prop)

            if res == "unreachable" or res == "bounded_unreachable_user":
                # idx2 implies idx
                dep.append((pl1, pl2)) #perflocs[idx], perflocs[idx2]))
                counter_dep += 1

            elif res == 'undetermined' or res=="processing":
                #max_bnd = max(bnd, bnd2)
                max_bnd = bnd
                undetermined_dep.append((pl1, pl2, int(max_bnd))) #(perflocs[idx], perflocs[idx2]))
                if int(max_bnd) >= bound:
                    undetermined_dep_over_bound.append((pl1, pl2, int(max_bnd)))
                    counter_undetermined_dep_over_bound += 1
                else:
                    undetermined_dep_under_bound.append((pl1, pl2, int(max_bnd)))
                    counter_undetermined_dep += 1
            else:
                counter_covered += 1

            if res in ["covered", "unreachable", "cex", "proven", "bounded_unreachable_user"]:
                comps.append(time)
            else:
                incomps.append((time, bnd))

    with open("implication.txt", "w") as f:
        for itm in dep + dep_in_log:
            f.write(",".join(itm) + "\n")

    with open("undetermined_impl.txt", "w") as f:
        for itm in undetermined_dep:
            f.write("%s,%s,%s\n" % (itm[0], itm[1], itm[2]))

    with open("undetermined_impl_over_bound.txt", "w") as f:
        for itm in undetermined_dep_over_bound:
            f.write("%s,%s,%s\n" % (itm[0], itm[1], itm[2]))

    with open("undetermined_impl_under_bound.txt", "w") as f:
        for itm in undetermined_dep_under_bound:
            f.write("%s,%s,%s\n" % (itm[0], itm[1], itm[2]))

    with open("exclusive.txt", "w") as f:
        for itm in exclu + excl_in_log:
            f.write(",".join(itm) + "\n")

    with open("undetermined_excl.txt", "w") as f:
        for itm in undetermined_exclu:
            f.write("%s,%s,%s\n" % (itm[0], itm[1], itm[2]))

    with open("undetermined_excl_over_bound.txt", "w") as f:
        for itm in undetermined_exclu_over_bound:
            f.write("%s,%s,%s\n" % (itm[0], itm[1], itm[2]))

    with open("undetermined_excl_under_bound.txt", "w") as f:
        for itm in undetermined_exclu_under_bound:
            f.write("%s,%s,%s\n" % (itm[0], itm[1], itm[2]))

    with open("stats.txt", "w") as f:
        f.write("%d,%f\n" % (len(comps), sum(comps)))
        for itm in comps:
            f.write("%f," % itm)
        f.write("\n")
        t = sum([r[0] for r in incomps])
        f.write("%d,%f\n" % (len(incomps), t))
        for itm in incomps:
            f.write("%f," % itm[0])
        f.write("\n")
        for itm in incomps:
            f.write("%d," % itm[1])
        f.write("\n")

    print("counter_excl: ", counter_excl)
    print("counter_dep: ", counter_dep)
    print("counter_undetermined_excl: ", counter_undetermined_excl)
    print("counter_undetermined_excl_over_bound: ", counter_undetermined_excl_over_bound)
    print("counter_undetermined_dep: ", counter_undetermined_dep)
    print("counter_undetermined_dep_over_bound: ", counter_undetermined_dep_over_bound)
    print("counter_covered: ", counter_covered)
    print("total: ", counter_excl + counter_dep + counter_undetermined_excl + counter_undetermined_excl_over_bound + counter_undetermined_dep + counter_undetermined_dep_over_bound + counter_covered)


def stats():
    print("========== stats ====================")
    pp()
    #comps = []
    #incomps = []

    ## nunv_anytwo
    #cnt = 0
    #for idx in range(len(perflocs)):
    #    for idx2 in range(len(perflocs)):
    #        if idx != idx2:
    #            pc_1 = iid_map[perflocs[idx]]
    #            pc_2 = iid_map[perflocs[idx2]]
    #            #print(perflocs[idx], perflocs[idx2])
    #            exclusive_already = False
    #            if  [pc_1, pc_2] in exclusive_set_iids or \
    #                [pc_2, pc_1] in exclusive_set_iids:
    #                exclusive_already = True

    #            if [pc_1, pc_2] in implication_set_iids:
    #                pass
    #            elif [perflocs[idx], perflocs[idx2]] in implication_set_pls: 
    #                pass
    #            elif not exclusive_already: #if [perflocs[idx], perflocs[idx2]] in edge: 
    #                df = pd.read_csv("./nunv_anytwo_%d.csv" % cnt, dtype=mydtypes)
    #                res, bnd, time = df_query(df, 'DEP_%d_b' % cnt)
    #                if res in ["covered", "unreachable", "cex", "proven"]:
    #                    comps.append(time)
    #                else:
    #                    incomps.append((time, bnd))
    #            cnt += 1
    #cnt = 0
    #for idx in range(len(perflocs)):
    #    for idx2 in range(len(perflocs)):
    #        if idx != idx2 :
    #            pc_1 = iid_map[perflocs[idx]]
    #            pc_2 = iid_map[perflocs[idx2]]
    #            exclusive_already = False
    #            if  [pc_1, pc_2] in exclusive_set_iids or \
    #                [pc_2, pc_1] in exclusive_set_iids:
    #                #print("skip %s %s check" % (perflocs[idx], perflocs[idx2]))
    #                exclusive_already = True
    #            imp_already = ([pc_1, pc_2] in implication_set_iids) or \
    #                ([pc_2, pc_1] in implication_set_iids) or \
    #                ([perflocs[idx2], perflocs[idx]] in implication_set_pls) or \
    #                ([perflocs[idx], perflocs[idx2]] in implication_set_pls)
    #            if idx < idx2 and (not exclusive_already) and (not imp_already):
    #            #if idx < idx2:
    #                df = pd.read_csv("./exclusive_%d.csv" % cnt, dtype=mydtypes)
    #                res, bnd, time = df_query(df, 'C_%d' % cnt)
    #                if res in ["covered", "unreachable", "cex", "proven"]:
    #                    comps.append(time)
    #                else:
    #                    incomps.append((time, bnd))
    #            cnt += 1

    #with open("stats.txt", "w") as f:
    #    f.write("%d,%f\n" % (len(comps), sum(comps)))
    #    for itm in comps:
    #        f.write("%f," % itm)
    #    f.write("\n")
    #    t = sum([r[0] for r in incomps])
    #    f.write("%d,%f\n" % (len(incomps), t))
    #    for itm in incomps:
    #        f.write("%f," % itm[0])
    #    f.write("\n")
    #    for itm in incomps:
    #        f.write("%d," % itm[1])
    #    f.write("\n")

if len(sys.argv) != 2:
    print("gen/pp")
    exit(0)

opt = sys.argv[1]
if opt == "gen":
    gen()
elif opt == "pp":
    pp()
elif opt == "stats":
    stats()
