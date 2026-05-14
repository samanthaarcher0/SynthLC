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


class GenComb:
    def __init__(self, arr):
        self.arr = arr
        self.res = []
        self.acc = []
    
    def gen(self):
        self.get_all_combination(0)
 
    def get_all_combination(self, idx):
        if idx == len(self.arr):
            self.res.append(self.acc[:])
            return
        self.get_all_combination(idx + 1)
        self.acc.append(self.arr[idx])
        self.get_all_combination(idx + 1)
        self.acc.pop()



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

#edge = get_array("../../xGenPerfLocDfgDiv/dfg_e.txt")
edge = get_array("../xCoverCandidateHBEdges/hb_covered.txt")
reachable_sets = get_array("../xPerfLocSubsetDiv/reachable_set.txt", arr_as_ele = True, exit_on_fail=False)

print("edges: ", len(edge))
print("cv_perflocs: ", len(cv_perflocs))


for itm in cv_perflocs:
    h_ += hpn_reg_t2.format(s1=itm)

JOB1="rtl2mupath_followers"
JOB2="rtl2mupath_first_pls"
JOB3="rtl2mupath_first_pl_sets"

max_cyc_per_pl_raw = get_array("../xPerfLocCycleCount/max_cycle_per_pl.txt")

repeated_pls = list()
for itm in max_cyc_per_pl_raw:
    if int(itm[1]) > 1:
        repeated_pls.append(itm[0])


def gen():
    global htcl_
    TMPLT = '''cover -name cvr_rtl2mupath_src_{src_nm}_dest_set_{dst} {{{src} ##1 (({conj_dest}) & ! ({disj})) }}\n'''

    followers = dict()
    for idx, e in enumerate(edge):
        in_aset = False
        e0 = e[0]
        e1 = e[1]
        pl_followers = followers.get(e0)
        if pl_followers is None:
            followers[e0] = [e1]
        else:
            followers[e0].append(e1)

    for pl in cv_perflocs:
        if pl in repeated_pls:
            followers[pl].append(pl)
     
    for src, dest_set in followers.items():
        print(f"SRC: {src}")
        print(f"DEST SET: {dest_set}") 
        comb_obj = GenComb(dest_set)
        comb_obj.gen()
        print(f"comb: {comb_obj.res}")
        fs = ""
        fs_conj = ""
        for a_comb in comb_obj.res:
            print(a_comb)
            fs = ""
            fs_conj = ""
            nfs_disj = ""
            for a in dest_set:
                if a in a_comb:
                    fs += ("_" + a)
                    fs_conj += prefix + a + " & "
                else:
                    nfs_disj += prefix + a + " | " 
            fs_conj += " 1'b1 "
            nfs_disj += " 1'b0 "

            htcl_ += TMPLT.format(src_nm=src, src=prefix+src, dst=fs, conj_dest=fs_conj, disj=nfs_disj) 

    with open (f"{JOB1}.tcl", "w") as f:
        f.write(htcl_)
        f.write("set props [get_property_list -include {name cvr_rtl2mupath_*}]\n")
        f.write("prove -property $props\n")
        f.write("report -property $props -csv -results -file %s.csv -force\n" % JOB1)
        #f.write("save %s.db -force\n" % JOB1)
        f.write("file copy -force %s.csv %s/.\n" % (JOB1, os.getcwd()))
        #f.write("exit\n")
    with open (f"{JOB1}.sv", "w") as f:
        f.write(h_)
        f.write(e_)

    return


def gen_s2():
        
    global htcl_

    TMPLT = '''cover -name cvr_rtl2mupath_src_first_{pl_nm} {{{pl} & ! ({others_hpn}) }}\n'''

    others_hpn = ""
    for pl2 in cv_perflocs:
        others_hpn += prefix + pl2 + "_hpn | "
    others_hpn += " 1'b0"

    for pl in cv_perflocs:
        htcl_ += TMPLT.format(pl_nm=pl, pl=prefix+pl, others_hpn=others_hpn)

    with open (f"{JOB2}.tcl", "w") as f:
        f.write(htcl_)
        f.write("set props [get_property_list -include {name cvr_rtl2mupath_*}]\n")
        f.write("prove -property $props\n")
        f.write("report -property $props -csv -results -file %s.csv -force\n" % JOB2)
        #f.write("save %s.db -force\n" % JOB2)
        f.write("file copy -force %s.csv %s/.\n" % (JOB2, os.getcwd()))
        #f.write("exit\n")
    with open (f"{JOB2}.sv", "w") as f:
        f.write(h_)
        f.write(e_)
    return


def gen_s3():

    global htcl_     
    TMPLT = '''cover -name cvr_rtl2mupath_src_first_{pl_nms} {{{pls} & ! ({others_hpn}) }}\n'''
 
    prop="cvr_rtl2mupath_src_first_%s"
    first_pls = list()
    for pl in cv_perflocs:
        r_, t_, b_ = get_result(f"{JOB2}.csv", prop % pl)
        if r_ == "covered":
            first_pls.append(pl)

    with open("first_covered.txt", "w") as f:
        for itm in first_pls:
            f.write(itm + "\n")


    comb_obj = GenComb(first_pls)
    comb_obj.gen()
    print(f"comb: {comb_obj.res}")

    others_hpn = ""
    for pl2 in cv_perflocs:
        others_hpn += prefix + pl2 + "_hpn | "
    others_hpn += " 1'b0"

    for a_comb in comb_obj.res:
        if len(a_comb) == 0:
            continue
        pl_nms = ""
        pls = ""
        for pl in cv_perflocs:
            if pl in a_comb:
                pls += prefix + pl + " & "
                pl_nms += "_"+pl
            else:
                pls += "!" + prefix + pl + " & "
        pls += "1'b1"

        htcl_ += TMPLT.format(pl_nms=pl_nms, pls=pls, others_hpn=others_hpn)


    with open (f"{JOB3}.tcl", "w") as f:
        f.write(htcl_)
        f.write("set props [get_property_list -include {name cvr_rtl2mupath_*}]\n")
        f.write("prove -property $props\n")
        f.write("report -property $props -csv -results -file %s.csv -force\n" % JOB3)
        #f.write("save %s.db -force\n" % JOB3)
        f.write("file copy -force %s.csv %s/.\n" % (JOB3, os.getcwd()))
        #f.write("exit\n")
    with open (f"{JOB3}.sv", "w") as f:
        f.write(h_)
        f.write(e_)

    return

def pp():
    TMPLT = '''cvr_rtl2mupath_src_{src}_dest_set_{dst}'''

    followers = dict()
    for idx, e in enumerate(edge):
        in_aset = False
        e0 = e[0]
        e1 = e[1]
        pl_followers = followers.get(e0)
        if pl_followers is None:
            followers[e0] = [e1]
        else:
            followers[e0].append(e1)

    for pl in cv_perflocs:
        if pl in repeated_pls:
            followers[pl].append(pl)

    undetermined = list()
    decisions = dict()
    for src, dest_set in followers.items():
        comb_obj = GenComb(dest_set)
        comb_obj.gen()
        fs = ""
        for a_comb in comb_obj.res:
            fs = ""
            for a in dest_set:
                if a in a_comb:
                    fs += ("_" + a)
            prop = TMPLT.format(src=src, dst=fs)
            print(prop)
            r_, t_, b_ = get_result(f"{JOB1}.csv", prop) 
            if r_ == "covered":
                
                if decisions.get(src) == None:
                    decisions[src] = [a_comb]
                else:
                    decisions[src].append(a_comb)

            elif r_ == "undetermined":
                undetermined.append((src, a_comb)) 

    TMPLT = '''cvr_rtl2mupath_src_first_{pl_nms}'''
    first_pls = get_array("first_covered.txt")
    comb_obj = GenComb(first_pls)
    comb_obj.gen()
    src = "instn_begin"
    for dest_set in comb_obj.res:
        if len(dest_set) == 0:
            continue
        pl_nms = ""
        for pl in cv_perflocs:
            if pl in dest_set:
                pl_nms += "_"+pl
        
        prop = TMPLT.format(pl_nms=pl_nms)
        r_, t_, b_ = get_result(f"{JOB3}.csv", prop)
        if r_ == "covered":
            if decisions.get(src) == None:
                decisions[src] = [dest_set]
            else:
                decisions[src].append(dest_set)

        elif r_ == "undetermined":
            undetermined.append(src, dest_set)


    with open("decisions.txt", "w") as f:
        for src, dest in decisions.items():
            f.write(f"{src}, {dest}\n")

 
    return

if len(sys.argv) != 2:
    print("gen/gen_s2/gen_s3/pp")
    exit(0)

opt = sys.argv[1]
if opt == "gen":
    gen()
elif opt == "gen_s2":
    gen_s2()
elif opt == "gen_s3":
    gen_s3()
elif opt == "pp":
    pp()
        
