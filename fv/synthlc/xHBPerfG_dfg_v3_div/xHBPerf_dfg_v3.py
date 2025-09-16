import re
import networkx as nx
from itertools import chain, combinations
import pandas as pd
import numpy as np
import os
import pandas as pd
import sys
sys.path.append("../../src")
from util import *
from HB_template import *


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

edge = get_array("../../xGenPerfLocDfgDiv/dfg_e.txt")
reachable_sets = get_array("../xPerfLocSubsetDiv/reachable_set.txt", arr_as_ele = True)

print("edges: ", len(edge))
print("reachable_sets: ", len(reachable_sets))
print("cv_perflocs: ", len(cv_perflocs))


for itm in cv_perflocs:
    h_ += hpn_reg_t2.format(s1=itm)

JOB1="rtl2mupath_HB_1"
JOB2="rtl2mupath_HB_2"


def gen():
    reachable_nodes = get_array("../xCoverAPerflocDiv/cover_individual.txt")
    tcl_out = f"{JOB1}.tcl"
    with open (tcl_out, "w") as f:
        f.write(htcl_)


    add_wait_comb = []
    for idx, e in enumerate(edge):
        in_aset = False
        e0 = e[0]
        e1 = e[1]
 
        for aSet in reachable_sets:
            if e0 in aSet and e1 in aSet and e0 != e1:
                in_aset = True
        #if in_aset:
        # unfortunately previous bug and to avoid re-evaluate stuffs
        if in_aset: #and e in yosys_edge: 
            with open (tcl_out, "a") as f:
                f.write(ENTER_A_HP_ENTER_B_t1_tcl.format(s1 = e0, s2 = e1, cnt = idx, prefix=prefix))
        else:
            print("not in reachable_sets: ", e)
    with open (tcl_out, "a") as f:
        f.write("set props [get_property_list -include {name asrt_rtl2mupath_*}]\n")
        f.write("prove -property $props\n")
        f.write("report -property $props -csv -results -file %s.csv -force\n" % JOB1)
        f.write("save %s.db -force\n" % JOB1)
        f.write("file copy %s.csv %s/.\n" % (JOB1, os.getcwd()))
        #f.write("exit\n")
    with open (f"{JOB1}.sv", "w") as f:
        f.write(h_)
        f.write(e_)

def gen_s2():
    reachable_nodes = get_array("../xCoverAPerflocDiv/cover_individual.txt")
    print(reachable_nodes )

    whb = []
    shb = []    
    undetermined = []
    tcl_out = f"{JOB2}.tcl"
    with open (tcl_out, "w") as f:
        f.write(htcl_)

    add_wait_comb = []
    for idx, e in enumerate(edge):
        in_aset = False
        e0 = e[0]
        e1 = e[1]

        for aSet in reachable_sets:
            if e0 in aSet and e1 in aSet and e0 != e1:
                in_aset = True
        if not in_aset:
            continue

        TMPLT="asrt_rtl2mupath_HB_%d"
        r_, tpt_, bnd_ = get_result(f"{JOB1}.csv", TMPLT % idx) #"ariane.HB_%d" % idx)
        print(idx, r_)
        if r_ == "cex":
            print("CHECK FOR WHB for ", e)
            with open (tcl_out, "a") as f:
                f.write(ENTER_A_HP_ENTER_B_t2_tcl.format(s1 = e0, s2 = e1, cnt = idx, prefix=prefix))
            whb.append(e)
        elif r_ == "undetermined":
            print("undetermined?", e[0], e[1])
    with open (tcl_out, "a") as f:
        f.write("set props [get_property_list -include {name asrt_rtl2mupath_*}]\n")
        f.write("prove -property $props\n")
        f.write("report -property $props -csv -results -file %s.csv -force\n" % JOB2)
        f.write("save %s.db -force\n" % JOB2)
        f.write("file copy %s.csv %s/.\n" % (JOB2, os.getcwd()))
        #f.write("exit\n")
    with open(f"whb_todo.txt", "w") as f:
        for e in whb:
            f.write(",".join(e) + "\n")

def pp():
    reachable_nodes = get_array("../xCoverAPerflocDiv/cover_individual.txt")
    whb = get_array(f"whb_todo.txt")
    bound = 20
    hb_ = []
    whb_ = []
    aws_same = []
    undetermined_hb_under_bound = []
    undetermined_hb_over_bound = []
    undetermined_whb_under_bound = []
    undetermined_whb_over_bound = []
    undetermined_concur_under_bound = []
    undetermined_concur_over_bound = []
    per_pl_set = []
    for idx, itm in enumerate(edge):
        if not (itm[0] in reachable_nodes and itm[1] in reachable_nodes):
            continue
        in_aset = False
        for aSet in reachable_sets:
            if itm[0] in aSet and itm[1] in aSet:
                in_aset = True
        if not in_aset:
            continue
        #if not itm in yosys_edge:
        #    continue
        TMPLT="asrt_rtl2mupath_HB_%d"
        r_, t_, b_ = get_result(f"{JOB1}.csv", TMPLT % idx) #"ariane.HB_%d" % idx)
        if r_ == "ERR":
            print("FAIL HB_%d" % idx)
        if r_ == "cex":
            TMPLT="asrt_rtl2mupath_WHB_%d"
            r2, t2, b2 = get_result(f"{JOB2}.csv", TMPLT % idx) #"ariane.WHB_%d" % idx)
            TMPLT="asrt_rtl2mupath_WHB_CONCUR_%d"
            r2_samecyc, t2_samecyc, b2_samecyc = get_result(
                    f"{JOB2}.csv", TMPLT % idx) #"ariane.WHB_CONCUR_%d" % idx)
            if r2 == "ERR":
                print("FAIL WHB_%d" % idx)
                os.system('grep "WHB_.*proven" %s ' % (f"{JOB2}.csv"))
            if r2_samecyc == "ERR":
                print("FAIL WHB_%d" % idx)
                os.system('grep "WHB_.*proven" %s ' % (f"{JOB2}.csv"))

            if r2 == "proven" or r2 == "bounded_proven_user":
                whb_.append(itm)
            elif r2 == "undetermined":
                print("WHB_%d %s %s undetermined" % (idx, itm[0], itm[1]))
                if b2 < bound:
                    undetermined_whb_under_bound.append(itm)
                else:
                    undetermined_whb_over_bound.append(itm)
            if r2 != 'proven' and r2 != "bounded_proven_user":
                per_pl_set.append(itm)

            if r2_samecyc == "proven" or r2_samecyc == "bounded_proven_user":
                aws_same.append(itm)
            elif r2_samecyc == "undetermined":
                print("WHB_CONCUR_%d %s %s undetermined" % (idx, itm[0], itm[1]))
                if b2_samecyc < bound:
                    undetermined_concur_under_bound.append(itm)
                else:
                    undetermined_concur_over_bound.append(itm)

        elif r_ == "proven" or r_=="bounded_proven_user":
            hb_.append(itm)
        elif r_ == "undetermined":
            if b_ < bound:
                undetermined_hb_under_bound.append(itm)
            else:
                undetermined_hb_over_bound.append(itm)
            print("undetermined HB: ", itm)


    with open("hb_proven.txt", "w") as f:
        for e in hb_:
            f.write(",".join(e) + "\n")
    at_the_same_time = []
    for e in whb_:
        if [e[1], e[0]] in whb_:
            at_the_same_time.append(e)
    for e in aws_same:
        if not e in at_the_same_time:
            at_the_same_time.append(e)
    with open("aws_concurrent.txt", "w") as f:
        for itm in at_the_same_time:
            f.write(",".join(itm) + "\n")
        
    with open("whb_proven.txt", "w") as f:
        for e in whb_:
            if not e in at_the_same_time:
                f.write(",".join(e) + "\n")
    with open("hb_undetermined_over_bound.txt", "w") as f:
        for itm in undetermined_hb_over_bound:
            f.write(",".join(itm) + "\n")
    with open("wbh_undetermined_over_bound.txt", "w") as f:
        for itm in undetermined_whb_over_bound:
            f.write(",".join(itm) + "\n")
    with open("concurrent_undetermined_over_bound.txt", "w") as f:
        for itm in undetermined_concur_over_bound:
            f.write(",".join(itm) + "\n")
    with open("undetermined_under_bound.txt", "w") as f:
        f.write("* undetermined hb\n")
        for itm in undetermined_hb_under_bound:
            f.write(",".join(itm) + "\n")
        f.write("* undetermined whb\n")
        for itm in undetermined_whb_under_bound:
            f.write(",".join(itm) + "\n")
        f.write("* undetermined concur\n")
        for itm in undetermined_concur_under_bound:
            f.write(",".join(itm) + "\n")
    for itm in per_pl_set:
        rev = [itm[1], itm[0]]
        if rev in at_the_same_time or itm in at_the_same_time:
            continue
        if rev in hb_:
            continue
        if rev in whb_:
            print("? ", itm)
            continue
        # a -- dfg --> b but it doesn't constitue any happens-before relation
        # from a to b 
        #print("No particular relation", itm) 

def stats():
    reachable_nodes = get_array("../xCoverAPerflocDiv/cover_individual.txt")
    whb = get_array("whb_todo.txt")
    det_time_point = []
    det_res = []
    hb_ = []
    whb_ = []
    undetermined = []
    #sum_ = 0

    comps = []
    incomps = []
    for idx, itm in enumerate(edge):
        if not itm in whb:
            continue
        if not (itm[0] in reachable_nodes and itm[1] in reachable_nodes):
            continue
        in_aset = False
        for aSet in reachable_sets:
            if itm[0] in aSet and itm[1] in aSet:
                in_aset = True
        if not in_aset:
            continue
        #if not itm in yosys_edge:
        #    continue
        df = pd.read_csv(f"{JOB1}.csv", dtype=mydtypes)
        res, bnd, time = df_query(df, "asrt_rtl2mupath_HB_%d" % idx)
        if res in ["covered", "unreachable", "cex", "proven", "bounded_proven_user"]:
            comps.append(time)
        else:
            incomps.append((time, bnd))

        if res == "cex":

            TMPLT="asrt_rtl2mupath_WHB_%d"
            r2, t2, b2 = get_result(f"{JOB2}.csv", TMPLT % idx) #"ariane.WHB_%d" % idx)
            TMPLT=TMPLT="asrt_rtl2mupath_WHB_CONCUR_%d"
            r2_samecyc, t2_samecyc = get_result(
                    f"{JOB2}.csv", TMPLT % idx) #"ariane.WHB_CONCUR_%d" % idx)

            df = pd.read_csv(f"{JOB2}.csv", dtype=mydtypes)
            if r2 == "ERR":
                r=df[df['Name'].str.contains("WHB_") & ~(df['Name'].str.contains("precondition"))]
                r=r[~r['Name'].str.contains("CONCUR")]
                print("FAIL WHB_%d.csv" % idx, r['Name'].values[0])
                if len(r) == 1:
                    res=r['Result'].values[0]
                    t = float(r['Time'].values[0][:-2])
                    if res in ["covered", "unreachable", "cex", "proven", "bounded_proven_user"]:
                        comps.append(t)
                    else:
                        incomps.append((t, -1))
                else:
                    assert(0)
            else:
                if r2 in ["covered", "unreachable", "cex", "proven", "bounded_proven_user"]:
                    comps.append(t2) 
                else:
                    incomps.append((time,-1))
            if r2_samecyc == "ERR":
                r=df[df['Name'].str.contains("WHB_") & ~(df['Name'].str.contains("precondition"))]
                r=r[r['Name'].str.contains("CONCUR")]
                print("FAIL WHB_CONCUR_%d.csv" % idx, r['Name'].values[0])
                if len(r) == 1:
                    res=r['Result'].values[0]
                    t = float(r['Time'].values[0][:-2])
                    if res in ["covered", "unreachable", "cex", "proven", "bounded_proven_user"]:
                        comps.append(t)
                    else:
                        incomps.append((t, -1))
                else:
                    assert(0)
            else:
                if r2_samecyc in ["covered", "unreachable", "cex", "proven", "bounded_proven_user"]:
                    comps.append(t2_samecyc) 
                else:
                    incomps.append((t2_samecyc,-1))

        #if os.path.exists("WHB_%d.csv" % idx):
        #    #sum_ += get_time_total("WHB_%d.csv" % idx) # "ariane.WHB_%d" % idx)
        #    df = pd.read_csv("WHB_%d.csv" % idx, dtype=mydtypes)
        #    res, bnd, time = df_query(df, "WHB_%d" % idx)
        #    if res in ["covered", "unreachable", "cex", "proven"]:
        #        comps.append(time)
        #    else:
        #        incomps.append((time, bnd))
        #    res, bnd, time = df_query(df, "WHB_CONCUR_%d" % idx)
        #    if res in ["covered", "unreachable", "cex", "proven"]:
        #        comps.append(time)
        #    else:
        #        incomps.append((time, bnd))

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


if len(sys.argv) != 2:
    print("gen/gen_s2/pp")
    exit(0)

opt = sys.argv[1]
if opt == "gen":
    gen()
elif opt == "gen_s2":
    gen_s2()
elif opt == "pp":
    pp()
elif opt == "stats":
    stats()
        
