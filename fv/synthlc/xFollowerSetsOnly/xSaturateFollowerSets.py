import ast
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
h_ = "".join(lines[:-5])
e_ = "".join(lines[-5:])


HEADERTCL='../header.tcl'
htcl_ = ""
with open(HEADERTCL, "r") as f:
    for line in f:
        htcl_ += line

cv_perflocs = get_array("../xCoverAPerflocDiv/cover_individual.txt")
edge = get_array("../xCoverCandidateHBEdges/hb_covered.txt")

with open("../../../../user_provided_files/combined_pls.txt", "r") as f:
    combined_pls = f.readlines()
combined_pl_dict = get_combined_pls_dict(combined_pls)


pl_signals = {}
with open("../../../xDUVPLs/perfloc_signals.txt", "r") as f:
    for line in f:
        pl, sigs = line[:-1].split(" : ")
        pl_signals[pl] = sigs.split(",")
iid_map = {}
for k, v in pl_signals.items():
    iid_map[k] = v[0]
for comb_pl, pl_list in combined_pl_dict.items():
    iid_map[comb_pl] =  iid_map[pl_list[0]]


decisions = dict()
with open("../xFollowerSetsOnly/decisions.txt", 'r') as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        try:
            key_part, list_part = line.split(",", 1)
        except ValueError:
            print(f"Skipping malformed line: {line}")
            continue

        key = key_part.strip()
        list_str = list_part.strip()
        try:
            parsed = ast.literal_eval(list_str)
        except Exception as e:
            print(f"Failed to parse line for key {key}: {e}")
            continue

        val_set = set()
        for subset in parsed:
            val_set.add(frozenset(subset))
        decisions[key] = val_set


print(decisions)
decisions_print = dict()
multiple_pls = 0
for k, v in decisions.items():
    l = list()
    for d in v:
        if len(d) > 1:
            multiple_pls += 1
        l.append(list(d))
    decisions_print[k] = l

print(f"multiple_pls: {multiple_pls}")
print(f"\nDECISIONS:\n{decisions_print}")
max_dest_set_len = 0
max_dest_set = []
for k, v in decisions.items():
    print(f"{k}: {len(v)}")
    for v_ in v:
        if len(v_) > max_dest_set_len:
            max_dest_set_len = len(v_)
            max_dest_set = v_
print(f"max dest set len: {max_dest_set_len} for {max_dest_set}")

with open("result.json", "w") as f:
    json.dump(decisions_print, f, indent=4)


for itm in cv_perflocs:
    h_ += hpn_reg_t2.format(s1=itm)

max_cyc_per_pl_raw = get_array("../xPerfLocCycleCount/max_cycle_per_pl.txt")

repeated_pls = list()
for itm in max_cyc_per_pl_raw:
    if int(itm[1]) > 1:
        repeated_pls.append(itm[0])

JOB1 = "rtl2mupath_follower_of_comb"
JOB2 = "rtl2mupath_follower_of_comb_round2"
JOB3 = "rtl2mupath_follower_of_comb_round3"


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

    to_check = set()
    str_to_dests = dict()
    total_to_check = 0
    props  = list()
    dest_sets_explored = list()
    for src, set_of_dests in decisions_print.items():
        for dests in set_of_dests:
            print(f"src: {src}, dests: {dests}, len: {len(dests)}")
            d_str = "__".join(sorted(dests))
            str_to_dests[d_str] = dests
            added = list()
            if d_str in dest_sets_explored:
                continue
            else:
                dest_sets_explored.append(d_str)
            if len(dests) == 2:
                dest0 = dests[0]
                dest1 = dests[1]
                dest0_followers = decisions_print.get(dest0, [[]])
                dest1_followers = decisions_print.get(dest1, [[]])
                all_follower_pls = followers.get(dest0, []) + followers.get(dest1, [])
                print(all_follower_pls) 
                for d0 in dest0_followers:
                    for d1 in dest1_followers:
                        new_dest = set(d0 + d1)
                        # Check if two PLs in the combined destination set are different PLs of the same uFSM
                        # if so, then it is unreachable and don't need to check
                        same_iid = False
                        iid_list = list()
                        for i in new_dest:
                            for j in new_dest:
                                if i==j:
                                    continue
                                elif iid_map[i] == iid_map[j]:
                                    same_iid = True 
                        if same_iid:
                            continue 
                        new_dest_str = "__".join(sorted(new_dest))
                        if new_dest_str not in added:
                            added.append(new_dest_str)
                            total_to_check += 1  
                            conj_dest = ""
                            disj = ""
                            for f in all_follower_pls:
                                if f in new_dest:
                                    conj_dest += (prefix + f + " & ")
                                else:
                                    disj += (prefix + f + " | ")
                            conj_dest += " 1'b1"
                            disj += " 1'b0"
                            src = prefix + dest0 + " & " + prefix + dest1
                            htcl_ += TMPLT.format(src_nm=d_str, dst=new_dest_str, src=src, conj_dest=conj_dest, disj=disj)
                            prop = f"cvr_rtl2mupath_src_{d_str}_dest_set_{new_dest_str}" 
                            if prop in props:
                                print("already in props 2")
                                print(prop)
                                return
                            else:
                                props.append(prop)
 
                print("ADDED")                        
                print(added) 

            if len(dests) == 3:
                dest0 = dests[0]
                dest1 = dests[1]
                dest2 = dests[2]
                dest0_followers = decisions_print.get(dest0, [[]])
                dest1_followers = decisions_print.get(dest1, [[]])
                dest2_followers = decisions_print.get(dest2, [[]])
                all_follower_pls = followers.get(dest0, []) + followers.get(dest1, []) + followers.get(dest2, [])
                print(all_follower_pls)
                for d0 in dest0_followers:
                    for d1 in dest1_followers:
                        for d2 in dest2_followers:
                            new_dest = set(d0 + d1 + d2)
                            # Check if two PLs in the combined destination set are different PLs of the same uFSM
                            # if so, then it is unreachable and don't need to check
                            same_iid = False
                            iid_list = list()
                            for i in new_dest:
                                for j in new_dest:
                                    if i==j:
                                        continue
                                    elif iid_map[i] == iid_map[j]:
                                        same_iid = True 
                            if same_iid:
                                continue 
                            new_dest_str = "__".join(sorted(new_dest))
                            if new_dest_str not in added:
                                added.append(new_dest_str)
                                total_to_check += 1
                                conj_dest = ""
                                disj = ""
                                for f in all_follower_pls:
                                    if f in new_dest:
                                        conj_dest += (prefix + f + " & ")
                                    else:
                                        disj += (prefix + f + " | ")
                                conj_dest += " 1'b1"
                                disj += " 1'b0"
                                src = prefix + dest0 + " & " + prefix + dest1 + " & " + prefix + dest2
                                htcl_ += TMPLT.format(src_nm=d_str, dst=new_dest_str, src=src, conj_dest=conj_dest, disj=disj)
                                prop = f"cvr_rtl2mupath_src_{d_str}_dest_set_{new_dest_str}"  
                                if prop in props:
                                    print("already in props 2 ")
                                    print(prop)
                                    return
                                else:
                                    props.append(prop)

                    print("ADDED")
                    print(added)


            if len(dests) == 4:
                dest0 = dests[0]
                dest1 = dests[1]
                dest2 = dests[2]
                dest3 = dests[3]
                dest0_followers = decisions_print.get(dest0, [[]])
                dest1_followers = decisions_print.get(dest1, [[]])
                dest2_followers = decisions_print.get(dest2, [[]])
                dest3_followers = decisions_print.get(dest3, [[]])
                all_follower_pls = followers.get(dest0, []) + followers.get(dest1, []) + followers.get(dest2, []) + followers.get(dest3, [])
                print(all_follower_pls)
                for d0 in dest0_followers:
                    for d1 in dest1_followers:
                        for d2 in dest2_followers:
                            for d3 in dest3_followers:
                                new_dest = set(d0 + d1 + d2 + d3)
                                # Check if two PLs in the combined destination set are different PLs of the same uFSM
                                # if so, then it is unreachable and don't need to check
                                same_iid = False
                                iid_list = list()
                                for i in new_dest:
                                    for j in new_dest:
                                        if i==j:
                                            continue
                                        elif iid_map[i] == iid_map[j]:
                                            same_iid = True 
                                if same_iid:
                                    continue 
                                new_dest_str = "__".join(sorted(new_dest))
                                if new_dest_str not in added:
                                    added.append(new_dest_str)
                                    total_to_check += 1
                                    conj_dest = ""
                                    disj = ""
                                    for f in all_follower_pls:
                                        if f in new_dest:
                                            conj_dest += (prefix + f + " & ")
                                        else:
                                            disj += (prefix + f + " | ")
                                    conj_dest += " 1'b1"
                                    disj += " 1'b0"
                                    src = prefix + dest0 + " & " + prefix + dest1 + " & " + prefix + dest2 + " & " + prefix + dest3
                                    htcl_ += TMPLT.format(src_nm=d_str, dst=new_dest_str, src=src, conj_dest=conj_dest, disj=disj)
                                    prop = f"cvr_rtl2mupath_src_{d_str}_dest_set_{new_dest_str}"  
                                    if prop in props:
                                        print("already in props 4")
                                        print(prop)
                                        return
                                    else:
                                        props.append(prop)

                        print("ADDED")
                        print(added)

    with open("to_check.txt", "w") as f:
        for a in dest_sets_explored:
            f.write("%s\n" % a)


    with open("props.txt", "w") as f:
        for prop in props:
            f.write("%s\n" % prop)

    print(f"total_to_check: {total_to_check}")

    with open (f"{JOB1}.tcl", "w") as f:
        f.write(htcl_)
        f.write("set props [get_property_list -include {name cvr_rtl2mupath_*}]\n")
        f.write("prove -property $props\n")
        f.write("report -property $props -csv -results -file %s.csv -force\n" % JOB1)
        f.write("save %s.db -force\n" % JOB1)
        f.write("file copy %s.csv %s/.\n" % (JOB1, os.getcwd()))
        #f.write("exit\n")

    with open (f"{JOB1}.sv", "w") as f:
        f.write(h_)
        f.write(e_)


    return

 

def gen_s2():
    global htcl_
    TMPLT = '''cover -name cvr_rtl2mupath_src_{src_nm}_dest_set_{dst} {{{src} ##1 (({conj_dest}) & ! ({disj})) }}\n'''
    df = pd.read_csv(f"{JOB1}.csv", dtype=mydtypes)
    props_step_1 = get_array("props.txt")

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


    followers_step2 = dict()
    total_covered = 0
    props  = list()
    dest_sets_explored = set()
    for p in props_step_1:
        p_pls = p.split("_src_")[1]
        src, d_str = p_pls.split("_dest_set_")
        dest_sets_explored.add(src)
        res, bnd, time = df_query(df, p, exact_name=True)
        if res == "covered":
            if followers_step2.get(src) is None:
                followers_step2[src] = list()
            followers_step2[src].append(d_str)
            total_covered += 1


    to_check = set()
    max_len = 0
    for k, vset in followers_step2.items():
        for v in vset:
            if followers_step2.get(v) is None:
                v_split = v.split("__")
                if v in dest_sets_explored:
                    print(f"already checked: {v}")
                elif len(v_split)==1:
                    print(f"single PL: {v}")
                else:
                    print(f"TO CHECK: {v}")
                    l = len(v_split)
                    if l >  max_len:
                        max_len = l
                    to_check.add(v)

    with open(f"to_check_s2.txt", "w") as f:
        for itm in sorted(to_check):
            f.write("%s\n" % itm)

    print(f"total covered: {total_covered}")
    print(f"to check: {len(to_check)}")
    print(f"max length: {max_len}")

    dest_sets_explored = list()
    total_to_check = 0
    props = list()
    for d_str in to_check:
        dests = d_str.split("__")
        print(f"dests: {dests}, len: {len(dests)}")
        added = list()
        if d_str in dest_sets_explored:
            continue
        else:
            dest_sets_explored.append(d_str)
        if len(dests) == 2:
            dest0 = dests[0]
            dest1 = dests[1]
            dest0_followers = decisions_print.get(dest0, [[]])
            dest1_followers = decisions_print.get(dest1, [[]])
            all_follower_pls = followers.get(dest0, []) + followers.get(dest1, [])
            print(all_follower_pls) 
            for d0 in dest0_followers:
                for d1 in dest1_followers:
                    new_dest = set(d0 + d1)
                    # Check if two PLs in the combined destination set are different PLs of the same uFSM
                    # if so, then it is unreachable and don't need to check
                    same_iid = False
                    iid_list = list()
                    for i in new_dest:
                        for j in new_dest:
                            if i==j:
                                continue
                            elif iid_map[i] == iid_map[j]:
                                same_iid = True 
                    if same_iid:
                        continue 
                    new_dest_str = "__".join(sorted(new_dest))
                    if new_dest_str not in added:
                        added.append(new_dest_str)
                        total_to_check += 1  
                        conj_dest = ""
                        disj = ""
                        for f in all_follower_pls:
                            if f in new_dest:
                                conj_dest += (prefix + f + " & ")
                            else:
                                disj += (prefix + f + " | ")
                        conj_dest += " 1'b1"
                        disj += " 1'b0"
                        src = prefix + dest0 + " & " + prefix + dest1
                        htcl_ += TMPLT.format(src_nm=d_str, dst=new_dest_str, src=src, conj_dest=conj_dest, disj=disj)
                        prop = f"cvr_rtl2mupath_src_{d_str}_dest_set_{new_dest_str}" 
                        if prop in props:
                            print("already in props 2")
                            print(prop)
                            return
                        else:
                            props.append(prop)


        if len(dests) == 3:
            dest0 = dests[0]
            dest1 = dests[1]
            dest2 = dests[2]
            dest0_followers = decisions_print.get(dest0, [[]])
            dest1_followers = decisions_print.get(dest1, [[]])
            dest2_followers = decisions_print.get(dest2, [[]])
            all_follower_pls = followers.get(dest0, []) + followers.get(dest1, []) + followers.get(dest2, [])
            print(all_follower_pls)
            for d0 in dest0_followers:
                for d1 in dest1_followers:
                    for d2 in dest2_followers:
                        new_dest = set(d0 + d1 + d2)
                        # Check if two PLs in the combined destination set are different PLs of the same uFSM
                        # if so, then it is unreachable and don't need to check
                        same_iid = False
                        iid_list = list()
                        for i in new_dest:
                            for j in new_dest:
                                if i==j:
                                    continue
                                elif iid_map[i] == iid_map[j]:
                                    same_iid = True 
                        if same_iid:
                            continue 
                        new_dest_str = "__".join(sorted(new_dest))
                        if new_dest_str not in added:
                            added.append(new_dest_str)
                            total_to_check += 1
                            conj_dest = ""
                            disj = ""
                            for f in all_follower_pls:
                                if f in new_dest:
                                    conj_dest += (prefix + f + " & ")
                                else:
                                    disj += (prefix + f + " | ")
                            conj_dest += " 1'b1"
                            disj += " 1'b0"
                            src = prefix + dest0 + " & " + prefix + dest1 + " & " + prefix + dest2
                            htcl_ += TMPLT.format(src_nm=d_str, dst=new_dest_str, src=src, conj_dest=conj_dest, disj=disj)
                            prop = f"cvr_rtl2mupath_src_{d_str}_dest_set_{new_dest_str}"  
                            if prop in props:
                                print("already in props 2 ")
                                print(prop)
                                return
                            else:
                                props.append(prop)

        if len(dests) == 4:
            dest0 = dests[0]
            dest1 = dests[1]
            dest2 = dests[2]
            dest3 = dests[3]
            dest0_followers = decisions_print.get(dest0, [[]])
            dest1_followers = decisions_print.get(dest1, [[]])
            dest2_followers = decisions_print.get(dest2, [[]])
            dest3_followers = decisions_print.get(dest3, [[]])
            all_follower_pls = followers.get(dest0, []) + followers.get(dest1, []) + followers.get(dest2, []) + followers.get(dest3, [])
            print(all_follower_pls)
            for d0 in dest0_followers:
                for d1 in dest1_followers:
                    for d2 in dest2_followers:
                        for d3 in dest3_followers:
                            new_dest = set(d0 + d1 + d2 + d3)
                            # Check if two PLs in the combined destination set are different PLs of the same uFSM
                            # if so, then it is unreachable and don't need to check
                            same_iid = False
                            iid_list = list()
                            for i in new_dest:
                                for j in new_dest:
                                    if i==j:
                                        continue
                                    elif iid_map[i] == iid_map[j]:
                                        same_iid = True 
                            if same_iid:
                                continue 
                            new_dest_str = "__".join(sorted(new_dest))
                            if new_dest_str not in added:
                                added.append(new_dest_str)
                                total_to_check += 1
                                conj_dest = ""      
                                disj = ""
                                for f in all_follower_pls:
                                    if f in new_dest:
                                        conj_dest += (prefix + f + " & ")
                                    else:
                                        disj += (prefix + f + " | ")
                                conj_dest += " 1'b1"
                                disj += " 1'b0"
                                src = prefix + dest0 + " & " + prefix + dest1 + " & " + prefix + dest2 + " & " + prefix + dest3
                                htcl_ += TMPLT.format(src_nm=d_str, dst=new_dest_str, src=src, conj_dest=conj_dest, disj=disj)
                                prop = f"cvr_rtl2mupath_src_{d_str}_dest_set_{new_dest_str}"  
                                if prop in props:
                                    print("already in props 4")
                                    print(prop)
                                    return
                                else:
                                    props.append(prop)

    with open("props_s2.txt", "w") as f:
        for prop in props:
            f.write("%s\n" % prop)

    print(f"total_to_check: {total_to_check}")

    with open (f"{JOB2}.tcl", "w") as f:
        f.write(htcl_)
        f.write("set props [get_property_list -include {name cvr_rtl2mupath_*}]\n")
        f.write("prove -property $props\n")
        f.write("report -property $props -csv -results -file %s.csv -force\n" % JOB2)
        f.write("save %s.db -force\n" % JOB2)
        f.write("file copy %s.csv %s/.\n" % (JOB2, os.getcwd()))
        #f.write("exit\n")

    with open (f"{JOB2}.sv", "w") as f:
        f.write(h_)
        f.write(e_)

    return



def gen_s3():    
    global htcl_
    TMPLT = '''cover -name cvr_rtl2mupath_src_{src_nm}_dest_set_{dst} {{{src} ##1 (({conj_dest}) & ! ({disj})) }}\n'''
    df1 = pd.read_csv(f"{JOB1}.csv", dtype=mydtypes)
    df2 = pd.read_csv(f"{JOB2}.csv", dtype=mydtypes)

    props_step_1 = get_array("props.txt")
    props_step_2 = get_array("props_s2.txt")


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


    followers_step2 = dict()
    total_covered = 0
    props  = list()
    dest_sets_explored = set()

    print("GETTING RESULTS FROM STEP 1")
    for p in props_step_1:
        p_pls = p.split("_src_")[1]
        src, d_str = p_pls.split("_dest_set_")
        dest_sets_explored.add(src)
        res, bnd, time = df_query(df1, p, exact_name=True)
        if res == "covered":
            if followers_step2.get(src) is None:
                followers_step2[src] = list()
            followers_step2[src].append(d_str)
            total_covered += 1

    print("GETTING RESULTS FROM STEP 2")
    for p in props_step_2:
        p_pls = p.split("_src_")[1]
        src, d_str = p_pls.split("_dest_set_")
        dest_sets_explored.add(src)
        res, bnd, time = df_query(df2, p, exact_name=True)
        if res == "covered":
            if followers_step2.get(src) is None:
                followers_step2[src] = list()
            followers_step2[src].append(d_str)
            total_covered += 1

    to_check = set()
    max_len = 0
    for k, vset in followers_step2.items():
        for v in vset:
            if followers_step2.get(v) is None:
                v_split = v.split("__")
                if v in dest_sets_explored:
                    print(f"already checked: {v}")
                elif len(v_split)==1:
                    print(f"single PL: {v}")
                else:
                    print(f"TO CHECK: {v}")
                    l = len(v_split)
                    if l >  max_len:
                        max_len = l
                    to_check.add(v)

    with open(f"to_check_s3.txt", "w") as f:
        for itm in sorted(to_check):
            f.write("%s\n" % itm)

    print(f"total covered: {total_covered}")
    print(f"to check: {len(to_check)}")
    print(f"max length: {max_len}")

    dest_sets_explored = list()
    total_to_check = 0
    props = list()
    for d_str in to_check:
        dests = d_str.split("__")
        print(f"dests: {dests}, len: {len(dests)}")
        added = list()
        if d_str in dest_sets_explored:
            continue
        else:
            dest_sets_explored.append(d_str)
        if len(dests) == 2:
            dest0 = dests[0]
            dest1 = dests[1]
            dest0_followers = decisions_print.get(dest0, [[]])
            dest1_followers = decisions_print.get(dest1, [[]])
            all_follower_pls = followers.get(dest0, []) + followers.get(dest1, [])
            print(all_follower_pls) 
            for d0 in dest0_followers:
                for d1 in dest1_followers:
                    new_dest = set(d0 + d1)
                    # Check if two PLs in the combined destination set are different PLs of the same uFSM
                    # if so, then it is unreachable and don't need to check
                    same_iid = False
                    iid_list = list()
                    for i in new_dest:
                        for j in new_dest:
                            if i==j:
                                continue
                            elif iid_map[i] == iid_map[j]:
                                same_iid = True 
                    if same_iid:
                        continue 
                    new_dest_str = "__".join(sorted(new_dest))
                    if new_dest_str not in added:
                        added.append(new_dest_str)
                        total_to_check += 1  
                        conj_dest = ""
                        disj = ""
                        for f in all_follower_pls:
                            if f in new_dest:
                                conj_dest += (prefix + f + " & ")
                            else:
                                disj += (prefix + f + " | ")
                        conj_dest += " 1'b1"
                        disj += " 1'b0"
                        src = prefix + dest0 + " & " + prefix + dest1
                        htcl_ += TMPLT.format(src_nm=d_str, dst=new_dest_str, src=src, conj_dest=conj_dest, disj=disj)
                        prop = f"cvr_rtl2mupath_src_{d_str}_dest_set_{new_dest_str}" 
                        if prop in props:
                            print("already in props 2")
                            print(prop)
                            return
                        else:
                            props.append(prop)


        if len(dests) == 3:
            dest0 = dests[0]
            dest1 = dests[1]
            dest2 = dests[2]
            dest0_followers = decisions_print.get(dest0, [[]])
            dest1_followers = decisions_print.get(dest1, [[]])
            dest2_followers = decisions_print.get(dest2, [[]])
            all_follower_pls = followers.get(dest0, []) + followers.get(dest1, []) + followers.get(dest2, [])
            print(all_follower_pls)
            for d0 in dest0_followers:
                for d1 in dest1_followers:
                    for d2 in dest2_followers:
                        new_dest = set(d0 + d1 + d2)
                        # Check if two PLs in the combined destination set are different PLs of the same uFSM
                        # if so, then it is unreachable and don't need to check
                        same_iid = False
                        iid_list = list()
                        for i in new_dest:
                            for j in new_dest:
                                if i==j:
                                    continue
                                elif iid_map[i] == iid_map[j]:
                                    same_iid = True 
                        if same_iid:
                            continue 
                        new_dest_str = "__".join(sorted(new_dest))
                        if new_dest_str not in added:
                            added.append(new_dest_str)
                            total_to_check += 1
                            conj_dest = ""
                            disj = ""
                            for f in all_follower_pls:
                                if f in new_dest:
                                    conj_dest += (prefix + f + " & ")
                                else:
                                    disj += (prefix + f + " | ")
                            conj_dest += " 1'b1"
                            disj += " 1'b0"
                            src = prefix + dest0 + " & " + prefix + dest1 + " & " + prefix + dest2
                            htcl_ += TMPLT.format(src_nm=d_str, dst=new_dest_str, src=src, conj_dest=conj_dest, disj=disj)
                            prop = f"cvr_rtl2mupath_src_{d_str}_dest_set_{new_dest_str}"  
                            if prop in props:
                                print("already in props 2 ")
                                print(prop)
                                return
                            else:
                                props.append(prop)

        if len(dests) == 4:
            dest0 = dests[0]
            dest1 = dests[1]
            dest2 = dests[2]
            dest3 = dests[3]
            dest0_followers = decisions_print.get(dest0, [[]])
            dest1_followers = decisions_print.get(dest1, [[]])
            dest2_followers = decisions_print.get(dest2, [[]])
            dest3_followers = decisions_print.get(dest3, [[]])
            all_follower_pls = followers.get(dest0, []) + followers.get(dest1, []) + followers.get(dest2, []) + followers.get(dest3, [])
            print(all_follower_pls)
            for d0 in dest0_followers:
                for d1 in dest1_followers:
                    for d2 in dest2_followers:
                        for d3 in dest3_followers:
                            new_dest = set(d0 + d1 + d2 + d3)
                            # Check if two PLs in the combined destination set are different PLs of the same uFSM
                            # if so, then it is unreachable and don't need to check
                            same_iid = False
                            iid_list = list()
                            for i in new_dest:
                                for j in new_dest:
                                    if i==j:
                                        continue
                                    elif iid_map[i] == iid_map[j]:
                                        same_iid = True 
                            if same_iid:
                                continue 
                            new_dest_str = "__".join(sorted(new_dest))
                            if new_dest_str not in added:
                                added.append(new_dest_str)
                                total_to_check += 1
                                conj_dest = ""      
                                disj = ""
                                for f in all_follower_pls:
                                    if f in new_dest:
                                        conj_dest += (prefix + f + " & ")
                                    else:
                                        disj += (prefix + f + " | ")
                                conj_dest += " 1'b1"
                                disj += " 1'b0"
                                src = prefix + dest0 + " & " + prefix + dest1 + " & " + prefix + dest2 + " & " + prefix + dest3
                                htcl_ += TMPLT.format(src_nm=d_str, dst=new_dest_str, src=src, conj_dest=conj_dest, disj=disj)
                                prop = f"cvr_rtl2mupath_src_{d_str}_dest_set_{new_dest_str}"  
                                if prop in props:
                                    print("already in props 4")
                                    print(prop)
                                    return
                                else:
                                    props.append(prop)

    with open("props_s3.txt", "w") as f:
        for prop in props:
            f.write("%s\n" % prop)

    print(f"total_to_check: {total_to_check}")

    with open (f"{JOB3}.tcl", "w") as f:
        f.write(htcl_)
        f.write("set props [get_property_list -include {name cvr_rtl2mupath_*}]\n")
        f.write("prove -property $props\n")
        f.write("report -property $props -csv -results -file %s.csv -force\n" % JOB3)
        f.write("save %s.db -force\n" % JOB3)
        f.write("file copy %s.csv %s/.\n" % (JOB3, os.getcwd()))
        #f.write("exit\n")

    with open (f"{JOB3}.sv", "w") as f:
        f.write(h_)
        f.write(e_)
    return



def pp():
 
    return


if len(sys.argv) != 2:
    print("gen/gen_s2/gen_s3/pp")
    #exit(0)



opt = sys.argv[1]
if opt == "gen":
    gen()
elif opt == "gen_s2":
    gen_s2()
elif opt == "gen_s2_2":
    gen_s2_2()
elif opt == "gen_s3":
    gen_s3()
elif opt == "pp":
    pp()
        
