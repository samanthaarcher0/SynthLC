import networkx as nx
from itertools import chain, combinations
from networkx.algorithms.community.label_propagation import asyn_lpa_communities
import pandas as pd
import numpy as np
from pathlib import Path
import os
import pandas as pd
import sys
import re
sys.path.append("../../src")
from util import *
from HB_template import *



HEADERFILE="../header.sv"
with open(HEADERFILE, "r") as f:
    lines = f.readlines()
h_ = "".join(lines[:-5])
e_ = "".join(lines[-5:])


HEADERTCL='../header.tcl'
htcl_ = ""
with open(HEADERTCL, "r") as f:
    for line in f:
        htcl_ += line


JOB="rtl2mupath_perfloc_subset"


cv_perflocs = get_array("../xCoverAPerflocDiv/cover_individual.txt")
always_ = get_array("../xCoverAPerflocDiv/always_reach.txt")

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
for comb_pl, pl_list in combined_pl_dict.items():
    iid_map[comb_pl] =  iid_map[pl_list[0]]

for itm in cv_perflocs:
    h_ += hpn_reg_t2.format(s1=itm)


exclu_pairs = get_array("../xPairwiseDepDiv/exclusive.txt")
impli_pairs = get_array("../xPairwiseDepDiv/implication.txt")
# 
bound = 20
print(f"we treat undetermined as unreachable if bound is greater than or equal {bound}")
exclu_pairs_incomp = get_array("../xPairwiseDepDiv/undetermined_excl_over_bound.txt")
impli_pairs_incomp = get_array("../xPairwiseDepDiv/undetermined_impl_over_bound.txt")

implication_set_iids = get_array("../../xCommon/implication_iid.txt", exit_on_fail=False)
cnt_reachable_pls_iid = {}
for itm in cv_perflocs:
    iid = iid_map[itm]
    if not iid in cnt_reachable_pls_iid:
        cnt_reachable_pls_iid[iid] = 0
    cnt_reachable_pls_iid[iid] += 1 


#print(cnt_reachable_pls_iid)
indexmap = {}
for idx, itm in enumerate(cv_perflocs):
    indexmap[itm] = idx
class GenComb:

    def __init__(self, tarr):
        self.arr = [2] * len(tarr)
        self.elearr = tarr
        self.res = []
        self.acc = []
    def gen(self):
        self.get_all_combination(0)
    def get_all_combination(self, idx):
        global exclu_pairs
        global exclu_pairs_incomp
        global always_
        global impli_pairs
        global impli_pairs_incomp
        global indexmap
        # if idx == len(self.arr):
        # print(idx, len(self.arr))
        if idx == len(self.arr):
            self.res.append(self.acc[::])
            return
        # e weight 
        for t in range(0, 2): #self.arr[idx]):
            if t == 1:
                fail = False
                for itm in exclu_pairs:
                    u, v = itm
                    if (u in self.acc and v == self.elearr[idx]) or \
                            (v in self.acc and u == self.elearr[idx]):
                        fail = True
                        break
                if not fail: 
                    for itm in exclu_pairs_incomp:
                        u, v, bnd = itm
                        if (u in self.acc and v == self.elearr[idx]) or \
                                (v in self.acc and u == self.elearr[idx]):
                            fail = True
                            break
                if not fail:
                    for itm in impli_pairs:
                        # v implies u
                        u, v = itm
                        if v == self.elearr[idx] and (not u in self.acc and indexmap[u] < idx):
                            fail = True
                            break
                if not fail:
                    for itm in impli_pairs_incomp:
                        # v implies u
                        u, v, bnd = itm 
                        if v == self.elearr[idx] and (not u in self.acc and indexmap[u] < idx):
                            fail = True
                            break

                if not fail:
                    self.acc.append(self.elearr[idx])
                    self.get_all_combination(idx+1)
                    self.acc.pop()
            else:
                fail = False
                if self.elearr[idx] in always_: 
                    fail = True
                if not fail:
                    for itm in impli_pairs:
                        # v implies u
                        u, v = itm
                        if v in self.acc and u == self.elearr[idx]:
                            fail = True
                            break
                if not fail:
                    for itm in impli_pairs_incomp:
                        # v implies u
                        u, v, bnd = itm
                        if v in self.acc and u == self.elearr[idx]:
                            fail = True
                            break
                if not fail:
                    self.get_all_combination(idx+1)



perflocs_map = {}
for idx, v in enumerate(cv_perflocs):
    perflocs_map[idx] = v


def gen():
    if not os.path.isdir("covertest"):
        print("creating dir out")
        os.mkdir("covertest")

    print("========== gen ====================")
    combgen = GenComb(cv_perflocs)
    combgen.get_all_combination(0)
    print(len(combgen.res))
    outf = open("potential_subset.txt","w") 
    tcl_out = f"{JOB}.tcl"
    cnt = 0
    num_filtered = 0
    num_pruned = 0
    sv_out = f"{JOB}.sv"
    with open (sv_out, "w") as f:
        f.write(h_)
        f.write(e_)

    seen_sets = set()
    seen_sets_list = list()
    t_ = ""
    for idx, aSet in enumerate(combgen.res):
        len_set = len(aSet)
        if len_set == 0:
            continue
        outf.write(",".join(aSet) + "\n")
        cnt += 1

        s_ = ""
        ors_ = ""
        ors_hpn = ""
        added_comb_lrq_loc = False
        for loc in cv_perflocs:
            ors_ += "{prefix}{s1} | ".format(s1=loc, prefix=prefix)
            if loc in aSet:
                s_ += "{prefix}{s1}_hpn & ".format(s1=loc, prefix=prefix)
            else:
                ors_hpn += "{prefix}{s1}_hpn | ".format(s1=loc, prefix=prefix)


        s_ += "1'b1"
        ors_ += "1'b0"
        ors_hpn += "1'b0"
        t_ += "cover -name cvr_rtl2mupath_C_%d_N {(@(posedge %sfv_clk) %s & !(%s) & !(%s))} \n" % (idx, prefix, s_, ors_hpn, ors_)
    outf.close()
 
    with open(tcl_out, "w") as f:
        f.write(htcl_)
        f.write("\n")
        f.write(t_)
        f.write("\n")
        f.write("set props [get_property_list -include {name cvr_rtl2mupath_C_*}] \n")
        f.write("prove -property $props \n")
        f.write("report -property $props -csv -results -file %s.csv -force\n" % JOB)
        f.write("save %s.db -force\n" % JOB)
        f.write("file copy %s.csv %s/.\n" % (JOB, os.getcwd()))
        #f.write("exit\n")
  
    print("num_pruned", num_pruned)
    print("num_filtered", num_filtered)
    print("total cnt", cnt)


def pp():
    potential_subsets = get_array("potential_subset.txt", arr_as_ele = True)
    combgen = GenComb(cv_perflocs)
    combgen.get_all_combination(0)
 
    print("========== gen ====================")
    print(len(potential_subsets))
    possible = []
    unreachable = []
    undetermined = []
    undetermined_under_bound = []
    undetermined_over_bound = []
    undetermined_no_file = []
    
    csv_files = [f"{JOB}.csv"]
    print(f"Found {len(csv_files)} CSV files in results directory")
    
    # Process all CSV files and collect all unique property names
    all_results = {}  # property_name -> (result, time, bound, source_file)
    
    for csv_file in csv_files:
        print(f"Processing {csv_file}")
        if not check_file(str(csv_file), exit_on_fail=False):
            continue
            
        try:
            df = pd.read_csv(csv_file, dtype=mydtypes)
            
            # Process each row in the CSV to extract all properties
            for _, row in df.iterrows():
                prop_name = row['Name']
                result = row['Result']
                
                # Parse bound
                bound_str = str(row['Bound'])
                bound_match = re.search(r'(\d+)', bound_str)
                bound_val = int(bound_match.group(1)) if bound_match else float('inf')
                
                # Ensure unique property names across all files
                if prop_name in all_results:
                    print(f"Warning: Property '{prop_name}' found in multiple files!")
                    print(f"  Previous: {all_results[prop_name][3]}")
                    print(f"  Current: {csv_file}")
                
                all_results[prop_name] = (result, bound_val, str(csv_file))
                
        except Exception as e:
            print(f"Error processing {csv_file}: {e}")
            continue
    
    print(f"Total unique properties found: {len(all_results)}")
    
    # Process potential subsets using the collected results
    for idx, itm in enumerate(combgen.res):

        if len(itm) == 0:
            continue

        TMPLT="cvr_rtl2mupath_C_%d_N"

        result = all_results.get(TMPLT % idx)
        if result is None:
            undetermined_no_file.append(itm)
            continue
        r_, b_, source_file = result

        print(f"Found result for subset {idx}: {result}")

        # Categorize results
        if r_ == "covered":
            possible.append(itm)
        elif r_ == "unreachable":
            unreachable.append(itm)
        else:
            undetermined.append((itm, b_))
            if b_ < bound:
                undetermined_under_bound.append((itm, b_))    
            else:
                undetermined_over_bound.append((itm, b_))

    with open("reachable_set.txt", "w") as f:
        for itm in possible:
            f.write(",".join(itm) + "\n")
    with open("unreachable_set.txt", "w") as f:
        for itm in unreachable:
            f.write(",".join(itm) + "\n")

    with open("undetermined_set.txt", "w") as f:
        for itm in undetermined:
            f.write(",".join(itm[0]) + " " + str(itm[1]) + "\n")

    with open("undetermined_under_bound.txt", "w") as f:
        for itm in undetermined_under_bound:
            f.write(",".join(itm[0]) + " " + str(itm[1]) + "\n")
    
    with open("undetermined_over_bound.txt", "w") as f:
        for itm in undetermined_over_bound:
            f.write(",".join(itm[0]) + " " + str(itm[1]) + "\n")
    
    with open("undetermined_no_file.txt", "w") as f:
        for itm in undetermined_no_file:
            f.write(",".join(itm) + "\n")

    print("potential subsets %d" % len(potential_subsets))
    print("covered subsets %d" % len(possible))
    print("unreachable subsets %d" % len(unreachable))
    print("undetermined subsets %d" % len(undetermined))
    print("undetermined subsets under bound %d" % len(undetermined_under_bound))
    print("undetermined subsets over bound %d" % len(undetermined_over_bound))
    print("undetermined subsets no file %d" % len(undetermined_no_file))

def plset_cnt_iso():
    ######### isomorphic ###
    # isomorphic_sets = [
    # set(["lsq_enq_0_s1", "lsq_enq_1_s1"]), 
    # set(["scb_0_s12", "scb_1_s12", "scb_2_s12", "scb_3_s12"]), 
    # set(["scb_0_s13", "scb_1_s13", "scb_2_s13", "scb_3_s13"]),
    # set(["scb_0_s14", "scb_1_s14", "scb_2_s14", "scb_3_s14"]), 
    # set(["scb_0_s8", "scb_1_s8", "scb_2_s8", "scb_3_s8"]),
    # set(["stb_com_0_s1", "stb_com_1_s1"]),
    # set(["stb_spec_0_s1", "stb_spec_1_s1"]),
    # ]
    #super_isomorphic_sets = [
    #set(["scb_0_s12", "scb_1_s12", "scb_2_s12", "scb_3_s12",
    #"scb_0_s13", "scb_1_s13", "scb_2_s13", "scb_3_s13",
    #"scb_0_s14", "scb_1_s14", "scb_2_s14", "scb_3_s14",
    #"scb_0_s8", "scb_1_s8", "scb_2_s8", "scb_3_s8"]),
    #set(["stb_com_0_s1", "stb_com_1_s1"]),
    #set(["stb_spec_0_s1", "stb_spec_1_s1"]),
    #]
    isomorphic_sets = [
        set(["lrq0_entry0_s0", "lrq0_entry1_s0", "lrq0_entry2_s0", "lrq0_entry3_s0"]),
        set(["lrq0_entry0_s1", "lrq0_entry1_s1", "lrq0_entry2_s1", "lrq0_entry3_s1"]),
        set(["lrq0_entry0_s2", "lrq0_entry1_s2", "lrq0_entry2_s2", "lrq0_entry3_s2"]),
        set(["lrq0_entry0_s3", "lrq0_entry1_s3", "lrq0_entry2_s3", "lrq0_entry3_s3"]),
        set(["lrq0_entry0_s4", "lrq0_entry1_s4", "lrq0_entry2_s4", "lrq0_entry3_s4"]),
        set(["lrq0_entry0_s5", "lrq0_entry1_s5", "lrq0_entry2_s5", "lrq0_entry3_s5"]),
        set(["lrq0_entry0_s6", "lrq0_entry1_s6", "lrq0_entry2_s6", "lrq0_entry3_s6"]),
        set(["lrq0_entry0_s8", "lrq0_entry1_s8", "lrq0_entry2_s8", "lrq0_entry3_s8"]),
        set(["lrq0_entry0_s9", "lrq0_entry1_s9", "lrq0_entry2_s9", "lrq0_entry3_s9"]),
        set(["ls0_d6_s1", "ls0_d6_s2", "ls0_d6_s4", "ls0_d6_s8"]),
    ]

    def larger_isomorhpic(a, b):
        # different index then already 
        if 'scb' in a and 'scb' in b:
           return a[:5] != b[:5] 
        return False
        

        
        
    pl_to_iso_set = {}
    # check if one is in cv_perflocs then every other should be
    #iterables = []
    for idx, aset in enumerate(isomorphic_sets):
        sync = None 
        for itm in aset:
            pl_to_iso_set[itm] = idx
            if sync is None:
                sync = (itm in cv_perflocs)
            else:
                assert(sync == (itm in cv_perflocs))
        #if sync:
        #    iterables.append("iso_%d" % idx)
    #print(pl_to_iso_set)
    print("- pass iso check on cv_perflocs")
    iterables_iso_PL = []
    for itm in cv_perflocs:
        if itm in pl_to_iso_set:
            iso = "iso_%d" % pl_to_iso_set[itm]
            if not iso in iterables_iso_PL:
                iterables_iso_PL.append(iso)
        else:
            iterables_iso_PL.append(itm)
    all_candidate = powerset(iterables_iso_PL)

    def transform(aset):
        ret = []
        for itm in aset:
            if itm in pl_to_iso_set:
                iso = "iso_%d" % pl_to_iso_set[itm]
                if not iso in ret:
                    ret.append(iso)
            else:
                ret.append(itm)
        return ret
    def trans(itm):
        if itm in pl_to_iso_set:
            return "iso_%d" % pl_to_iso_set[itm]
        else:
            return itm
        

    check_and_reachable_sets = get_array("reachable_set.txt", arr_as_ele=True)
    check_and_reachable_sets = [transform(itm) for itm in check_and_reachable_sets]
    #print(check_and_reachable_sets)
    check_and_unreachable_sets = get_array("unreachable_set.txt", arr_as_ele=True)
    check_and_unreachable_sets = [transform(itm) for itm in check_and_unreachable_sets]

    for itm in check_and_unreachable_sets:
        assert(not itm in check_and_reachable_sets)
    for itm in check_and_reachable_sets:
        assert(not itm in check_and_unreachable_sets)

    check_and_undetermined_sets = get_array("undetermined_set.txt", arr_as_ele=True)
    check_and_undetermined_sets = [transform(itm) for itm in check_and_undetermined_sets]

    # doesn't even make it to the cover property
    # - one proven iso morphic  then applies to all others
    pruned_by_proven_pairwise_relation = [] 
    pruned_by_undetermined_pairwise_relation = []

    # make it to cover property
    potential_subset = []
    potential_subset_undet = []
    potential_subset_unreachable = []
    potential_subset_covered = []
    cnt = 0
    for candidate in all_candidate:
        cnt += 1
        candidate = list(candidate)

        pruned = False
        pruned_based_undet_pairwise = False

        for itm in always_:
            if not trans(itm) in candidate:
                pruned = True
                break
                
        if not pruned:
            for itm in exclu_pairs:
                u, v = itm
                u_trans, v_trans = trans(u), trans(v)
                if u_trans == v_trans or larger_isomorhpic(u, v):
                    continue
                # only same iid but different state is interesting 
                if u_trans in candidate and v_trans in candidate:
                    #print( itm, "prun by proven pairwise ", ",".join(candidate))
                    pruned = True
                    break

        if not pruned :
            for itm in impli_pairs:
                # v implies u
                u, v = itm
                if trans(v) in candidate and (not trans(u) in candidate):
                    #print('imp', itm, "prun by proven pairwise ", ",".join(candidate))
                    pruned = True 
                    break
        if pruned:
            pruned_by_proven_pairwise_relation.append(candidate)
            continue
        
        if not pruned_based_undet_pairwise:
            for itm in exclu_pairs_incomp:
                u, v = itm
                u_trans, v_trans = trans(u), trans(v)
                if u_trans == v_trans or larger_isomorhpic(u, v):
                    continue
                if u_trans in candidate and v_trans in candidate:
                    #print(itm, "prun by pairwise ", ",".join(candidate))
                    pruned_based_undet_pairwise = True
                    break

        if not pruned_based_undet_pairwise:
            for itm in impli_pairs_incomp:
                # v implies u
                u, v = itm
                if trans(v) in candidate and (not trans(u) in candidate):
                    #print('imp', itm, "prun by pairwise ", ",".join(candidate))
                    pruned_based_undet_pairwise = True 
                    break
        if pruned_based_undet_pairwise:
            pruned_by_undetermined_pairwise_relation.append(candidate)
        else:
            potential_subset.append(candidate)
    for candidate in potential_subset:
        candidate = list(candidate)
        if candidate in check_and_unreachable_sets:
            potential_subset_unreachable.append(candidate)
        elif candidate in check_and_reachable_sets:
            potential_subset_covered.append(candidate)
        elif candidate in check_and_undetermined_sets:
            potential_subset_undet.append(candidate) 
            #if (candidate in check_and_unreachable_sets or  \
            #    candidate in check_and_reachable_sets):
            #    print(" ??? ", candidate, type(candidate), type(check_and_unreachable_sets[0]))
        else:
            print(" ??? ", candidate)
            assert(0)
    #print('total cnt', cnt) 
    #print('pruned_by_proven_pairwise_relation', len(pruned_by_proven_pairwise_relation))
    #print('potential_subset_covered', len(potential_subset_covered))
    #print('potential_subset_unreachable', len(potential_subset_unreachable))
    #print("potential_subset_undet: %d" % len(potential_subset_undet))
    #print("pruned_by_undetermined_pairwise_relation: %d" % len(pruned_by_undetermined_pairwise_relation))
    with open("cnt_iso.txt", "w") as f:
        f.write("%d\n" % cnt) 
        f.write("%d\n" % len(pruned_by_proven_pairwise_relation))
        f.write("%d\n" % len(potential_subset_covered))
        f.write("%d\n" % len(potential_subset_unreachable))
        f.write("%d\n" % len(potential_subset_undet))
        f.write("%d\n" % len(pruned_by_undetermined_pairwise_relation))
        
    print("pass") 

    with open("undetermined_total_iso.txt", "w") as f:
        f.write("potential_subset_undet\n")
        for itm in potential_subset_undet:
            f.write(",".join(itm) + "\n")
        f.write("pruned_by_undetermined_pairwise_relation\n")
        for itm in pruned_by_undetermined_pairwise_relation:
            f.write(",".join(itm) + "\n")

def plset_cnt():
    check_and_reachable_sets = get_array("reachable_set.txt", arr_as_ele=True)
    check_and_unreachable_sets = get_array("unreachable_set.txt", arr_as_ele=True)
    check_and_undetermined_sets = get_array("undetermined_set.txt", arr_as_ele=True)

    
    all_candidate = powerset(cv_perflocs)

    # doesn't even make it to the cover property
    pruned_by_proven_pairwise_relation = []
    pruned_by_undetermined_pairwise_relation = []

    # make it to cover property
    potential_subset = []
    potential_subset_undet = []
    potential_subset_unreachable = []
    potential_subset_covered = []

    cnt = 0

    for candidate in all_candidate:
        cnt += 1
        candidate = list(candidate)
        pruned = False
        pruned_based_undet_pairwise = False

        for itm in always_:
            if not itm in candidate:
                pruned = True
                break
                
        if not pruned:
            for itm in exclu_pairs:
                u, v = itm
                if u in candidate and v in candidate:
                    pruned = True
                    break

        if not pruned :
            for itm in impli_pairs:
                # v implies u
                u, v = itm
                if v in candidate and (not u in candidate):
                    pruned = True 
                    break
        if pruned:
            pruned_by_proven_pairwise_relation.append(candidate)
            continue

        if not pruned_based_undet_pairwise:
            for itm in exclu_pairs_incomp:
                u, v = itm
                if u in candidate and v in candidate:
                    pruned_based_undet_pairwise = True
                    break

        if not pruned_based_undet_pairwise:
            for itm in impli_pairs_incomp:
                # v implies u
                u, v = itm
                if v in candidate and (not u in candidate):
                    pruned_based_undet_pairwise = True 
                    break
        if pruned_based_undet_pairwise:
            pruned_by_undetermined_pairwise_relation.append(candidate)
        else:
            potential_subset.append(candidate)

    for candidate in potential_subset:
        candidate = list(candidate)
        if candidate in check_and_undetermined_sets:
            potential_subset_undet.append(candidate) 
            if (candidate in check_and_unreachable_sets or  \
                candidate in check_and_reachable_sets):
                print(" ??? ", candidate, type(candidate), type(check_and_unreachable_sets[0]))
        elif candidate in check_and_unreachable_sets:
            potential_subset_unreachable.append(candidate)
        elif candidate in check_and_reachable_sets:
            potential_subset_covered.append(candidate)
        else:
            assert(0)
    print("total cnt", cnt)
    print('pruned_by_proven_pairwise_relation', len(pruned_by_proven_pairwise_relation))
    print('potential_subset_covered', len(potential_subset_covered))
    print('potential_subset_unreachable', len(potential_subset_unreachable))
    print("potential_subset_undet: %d" % len(potential_subset_undet))
    print("pruned_by_undetermined_pairwise_relation: %d" % len(pruned_by_undetermined_pairwise_relation))

    with open("undetermined_total.txt", "w") as f:
        f.write("potential_subset_undet\n")
        for itm in potential_subset_undet:
            f.write(",".join(itm) + "\n")
        f.write("pruned_by_undetermined_pairwise_relation\n")
        for itm in pruned_by_undetermined_pairwise_relation:
            f.write(",".join(itm) + "\n")
    
    total_undet = potential_subset_undet + pruned_by_undetermined_pairwise_relation
    total_undet_nonsquahs = []
    total_undet_squash = []
    for itm in total_undet:
        #if itm in potential_subset_undet and itm in pruned_by_undetermined_pairwise_relation:
        if not ('scb_0_s13' in itm or \
                'scb_1_s13' in itm or \
                'scb_2_s13' in itm or \
                'scb_3_s13' in itm):
           total_undet_squash.append(itm)
        else:
           total_undet_nonsquahs.append(itm)
    for itm in total_undet_squash:
        ssubset = set(itm) 
        is_subset = False 
        for itm2 in total_undet_nonsquahs:
            aset = set(itm2)
            if ssubset.issubset(aset):
                is_subset = True
                break
            
        if not is_subset:
            is_subset_ofreachable = False
            for itm2 in check_and_reachable_sets:
                aset = set(itm2)
                if ssubset.issubset(aset):
                    is_subset_ofreachable = True
                    break
            print(is_subset_ofreachable, "not a subset", ",".join(itm))




def stats():
    potential_subsets = get_array("potential_subset.txt", arr_as_ele = True)
    print("========== stats ====================")

    cnt = 0
    sum_ = 0

    comps = []
    incomps = []
    idx = 0
    for _, itm in enumerate(potential_subsets):
        df = pd.read_csv("./coverset_%d.csv" % idx, dtype=mydtypes)
        TMPLT=GLBTOPMOD + ".C_%d_N"
        res, bnd, time = df_query(df,TMPLT % idx, exact_name=True)
        if res in ["covered", "unreachable", "cex", "proven"]:
            comps.append(time)
        else:
            incomps.append((time, bnd))
        idx += 1

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
    print("gen/pp")
    exit(0)

opt = sys.argv[1]
if opt == "gen":
    gen()
elif opt == "pp":
    pp()
elif opt == "stats":
    stats()
elif opt == "plset_cnt":
    plset_cnt()
elif opt == "plset_cnt_iso":
    plset_cnt_iso()
