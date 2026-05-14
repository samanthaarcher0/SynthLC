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
h_ = "".join(lines)
e_ = ""


HEADERTCL='../header.tcl'
htcl_ = ""
with open(HEADERTCL, "r") as f:
    for line in f:
        htcl_ += line


cv_perflocs = get_array("../xCoverAPerflocDiv/cover_individual.txt")

edge = get_array("../../xGenPerfLocDfgDiv/dfg_e.txt")
reachable_sets = get_array("../xPerfLocSubsetDiv/reachable_set.txt", arr_as_ele = True, exit_on_fail=False)

print("edges: ", len(edge))
print("reachable_sets: ", len(reachable_sets))
print("cv_perflocs: ", len(cv_perflocs))


for itm in cv_perflocs:
    h_ += hpn_reg_t2.format(s1=itm)

JOB="rtl2mupath_candidate_HB"

A_HB_1_CYCLE_B_t_tcl = '''cover -name cvr_rtl2mupath_{s1}_HB_1_cyc_{s2} {{ {prefix}{s1} ##1 {prefix}{s2} }}\n'''
A_CONCUR_B_t_tcl = '''cover -name cvr_rtl2mupath_{s1}_CONCUR_1_cyc_{s2} {{ {prefix}{s1} && {prefix}{s2} }}\n'''

def gen():
    global htcl_
    tcl_out = f"{JOB}.tcl"

    for idx, e in enumerate(edge):
        in_aset = False
        e0 = e[0]
        e1 = e[1]
 
        #for aSet in reachable_sets:
            #if e0 in aSet and e1 in aSet and e0 != e1:
        if e0 in cv_perflocs and e1 in cv_perflocs and e0 != e1:
           in_aset = True
        
        if in_aset: 
            htcl_ += A_HB_1_CYCLE_B_t_tcl.format(s1 = e0, s2 = e1, prefix=prefix)
            htcl_ += A_CONCUR_B_t_tcl.format(s1 = e0, s2 = e1, prefix=prefix)
        else:
            print("not in reachable_sets: ", e)
    
    with open (tcl_out, "w") as f:
        f.write(htcl_)
        f.write("set props [get_property_list -include {name cvr_rtl2mupath_*}]\n")
        f.write("prove -property $props\n")
        f.write("report -property $props -csv -results -file %s.csv -force\n" % JOB)
        #f.write("save %s.db -force\n" % JOB)
        f.write("file copy -force %s.csv %s/.\n" % (JOB, os.getcwd()))
        #f.write("exit\n")
    with open (f"{JOB}.sv", "w") as f:
        f.write(h_)
        f.write(e_)

    return

def pp():
    reachable_nodes = get_array("../xCoverAPerflocDiv/cover_individual.txt")
    covered_hb = []
    unreachable_hb = []
    undetermined_hb = []

    covered_concur = []
    unreachable_concur = []
    undetermined_concur = []

    covered_all = []

    for idx, e in enumerate(edge):
        in_aset = False
        e0 = e[0]
        e1 = e[1]

        #for aSet in reachable_sets:
            #if e0 in aSet and e1 in aSet and e0 != e1:
        if e0 in cv_perflocs and e1 in cv_perflocs and e0 != e1:
           in_aset = True
        
        if not in_aset:
            continue
        
        TMPLT="cvr_rtl2mupath_{s1}_HB_1_cyc_{s2}"
        TMPLT2="cvr_rtl2mupath_{s1}_CONCUR_1_cyc_{s2}"
        r_, t_, b_ = get_result(f"{JOB}.csv", TMPLT.format(s1=e0, s2=e1)) #"ariane.HB_%d" % idx)
        r2_, t2_, b2_ = get_result(f"{JOB}.csv", TMPLT2.format(s1=e0, s2=e1)) 
        if r_ == "ERR":
            print("FAIL HB %s" % e)
        if r_ == "covered":
            covered_hb.append(e)
        elif r_ == "unreachable" or r_=="bounded_unreachable_user":
            unreachable_hb.append(e)
        elif r_ == "undetermined":
            undetermined_hb.append(e)
            print("undetermined HB: ", e)

        if r2_ == "ERR":
            print("FAIL CONCUR %s" % e)
        if r2_ == "covered":
            covered_concur.append(e)
        elif r2_ == "unreachable" or r2_=="bounded_unreachable_user":
            unreachable_concur.append(e)
        elif r2_ == "undetermined":
            undetermined_concur.append(e)
            print("undetermined CONCUR: ",e)

        if r_ == "covered" or r2_ == "covered":
            covered_all.append(e)

    with open("hb_covered.txt", "w") as f:
        for e in covered_hb:
            f.write(",".join(e) + "\n")
    
    with open("hb_unreachable.txt", "w") as f:
        for e in unreachable_hb:
            f.write(",".join(e) + "\n")

    with open("hb_undetermined.txt", "w") as f:
        for e in undetermined_hb:
            f.write(",".join(e) + "\n")


    with open("concur_covered.txt", "w") as f:
        for e in covered_concur:
            f.write(",".join(e) + "\n")
    
    with open("concur_unreachable.txt", "w") as f:
        for e in unreachable_concur:
            f.write(",".join(e) + "\n")

    with open("concur_undetermined.txt", "w") as f:
        for e in undetermined_concur:
            f.write(",".join(e) + "\n")

    with open("covered_edges.txt", "w") as f:
        for e in covered_all:
            f.write(",".join(e) + "\n")


    return


if len(sys.argv) != 2:
    print("gen/pp")
    exit(0)

opt = sys.argv[1]
if opt == "gen":
    gen()
elif opt == "pp":
    pp()

