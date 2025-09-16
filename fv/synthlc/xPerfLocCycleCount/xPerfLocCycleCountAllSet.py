# 1. for all reachable nodes run max cycle **in no specific sets**
# 2. for nodes with greater than 1 max cycle specialize? 

import networkx as nx
import re
from itertools import chain, combinations
import pandas as pd
import numpy as np
import os
import pandas as pd
import sys
sys.path.append("../../src")
from util import *
from HB_template import *

cv_perflocs = get_array("../xCoverAPerflocDiv/cover_individual.txt")
reachable_sets = get_array("../xPerfLocSubsetDiv/reachable_set.txt", arr_as_ele = True)

interference = True
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

for itm in cv_perflocs:
    h_ += hpn_reg_t2.format(s1=itm)

JOB1="rtl2mupath_pl_revisit_possible"
JOB2="rtl2mupath_pl_subset_revisit_possible"

def gen():

    template = '''cover -name cvr_rtl2mupath_{s}_revisit {{(@(posedge {prefix}fv_clk) ({prefix}{s} [*2] ##1 !{prefix}{s}))}}\n'''
    tcl = ''
    for itm in cv_perflocs:
        tcl += (template.format(s=itm, prefix=prefix))

    with open(f"{JOB1}.sv", "w") as f:
        f.write(h_)
        f.write(e_)

    with open(f"{JOB1}.tcl", "w") as f:
        f.write(htcl_)
        f.write(tcl)
        f.write("\n")
        f.write("set props [get_property_list -include {name cvr_rtl2mupath_*_revisit}] \n")
        f.write("prove -property $props \n")
        f.write("report -property $props -csv -results -file %s.csv -force\n" % JOB1)
        f.write("save %s.db -force\n" % JOB1)
        f.write("file copy %s.csv %s/.\n" % (JOB1, os.getcwd()))
        #f.write("exit\n")
    return



def proc(fnm, itm):
    if not os.path.exists(fnm):
        return None
    csv_ = pd.read_csv(fnm)

    nm_raw = csv_[csv_['Name'].str.contains('consec_%s' % itm)]['Name'].values
    nm_raw = [int(re.search(r"consec_%s_([0-9]+)" % itm, nm).group(1)) for nm in nm_raw]

    res_raw = csv_[csv_['Name'].str.contains('consec_%s' % itm)]['Result'].values
    res_raw = list(zip(nm_raw, res_raw))

    res = sorted(res_raw, key = lambda i: i[0], reverse=True)
    res_inc = sorted(res_raw, key = lambda i: i[0], reverse=False)

    cyc = None
    cyc_res = None

    for rr in res:
        if rr[1] == 'covered' or rr[1] == 'undetermined':
            cyc = rr[0]
            cyc_res = rr[1]
            break

    max_cyc_covered = None
    for rr in res:
        if rr[1] == 'covered':
            max_cyc_covered = rr[0]
            break
    assert(max_cyc_covered is not None)

    # prerequisite for cyc to be max cycle is other smaller number
    # should not be unreachable
    min_unreach_cyc = None
    min_covered_cyc_under_unreach = None
    
    for rr in res_inc:
        if rr[1] == 'unreachable' and rr[0] < cyc:
            min_unreach_cyc = rr[0]
            break
        if rr[1] == 'covered':
            min_covered_cyc_under_unreach = rr[0]
    if min_unreach_cyc is not None:
        print(itm, cyc, "cyc change to ", min_covered_cyc_under_unreach,
                "from original result", cyc, cyc_res)
        cyc = min_covered_cyc_under_unreach

    return (cyc, max_cyc_covered)

def gen_s2():
 
    seen_wait_comb = False
    t_ = ""
    CVR_TMPLT = '''cover -name cvr_rtl2mupath_over1cyc_{idx}_{itm_nm} {{(@(posedge {prefix}fv_clk) ({itm}) [*2] ##[0:$] ({path})) }}\n'''
    max_cyc_perloc = list()
    for itm in cv_perflocs:
        print(itm)
        TMPLT="cvr_rtl2mupath_%s_revisit"
        r_, tpt_, bnd_ = get_result(f"{JOB1}.csv", TMPLT % itm)
        if r_ != "covered":
            max_cyc_perloc.append((itm, 1))
            continue
        max_cyc_perloc.append((itm, 2))
        set_itm = itm

        # for each reachable set try see if the performing location can be
        # longer than one cycle 
        for set_idx, aSet in enumerate(reachable_sets):
            if not set_itm in aSet:
                continue
        
            s_ = ""
            ors_ = ""
            ors_hpn = ""
            added_comb_lrq_loc = False
            for loc in cv_perflocs:
                ors_ += "{prefix}{s1} | ".format(s1=loc, prefix=prefix)
                loc_in_set = (loc in aSet)
 
                if loc_in_set:
                    s_ += "{prefix}{s1}_hpn & ".format(s1=loc, prefix=prefix)
                else:
                    ors_hpn += "{prefix}{s1}_hpn | ".format(s1=loc, prefix=prefix)

            s_ += "1'b1"
            ors_ += "1'b0"
            ors_hpn += "1'b0"
            path = s_ + " & !(%s) & !(%s)" % (ors_hpn, ors_)
            #if itm == "lrq0_entry0_wait_comb":
            #    t_ += CVR_TMPLT.format(idx=set_idx, itm_nm="lrq0_entry0_wait_comb", itm=lrq0_entry0_wait_comb_hpn, path=path)
            #else: 
            t_ += CVR_TMPLT.format(idx=set_idx, itm_nm=itm, itm=("%s%s" % (prefix, itm)), path=path, prefix=prefix)
            t_ += "\n"

    with open(f"{JOB2}.sv", "w") as f:
        f.write(h_)
        f.write(e_)

    with open(f"{JOB2}.tcl", "w") as f:
        f.write(htcl_)
        f.write(t_)
        f.write("\n")
        f.write("set props [get_property_list -include {name cvr_rtl2mupath_over1cyc_*}] \n")
        f.write("prove -property $props \n")
        f.write("report -property $props -csv -results -file %s.csv -force\n" % JOB2)
        f.write("save %s.db -force\n" % JOB2)
        f.write("file copy %s.csv %s/.\n" % (JOB2, os.getcwd()))
        #f.write("exit\n")

    with open("max_cycle_per_pl.txt", "w") as f:
        for itm in max_cyc_perloc:
            f.write("%s,%d\n" % (itm[0], itm[1]))
    return

def pp():
    max_cyc_perloc = get_array("max_cycle_per_pl.txt")
    pl_cyc = {}
    for itm in max_cyc_perloc:
        pl_cyc[itm[0]] = int(itm[1])
    
    result = [] # (itm,cyc_that_covered,...)
    undetermined_result = []
    # itm, cyc, res
    fnm = os.getcwd() + "/%s.csv" % JOB2
    check_file(fnm)
    seen_wait_comb = False
    df = pd.read_csv(fnm, dtype=mydtypes)
    for itm in cv_perflocs:
        TMPLT="cvr_rtl2mupath_%s_revisit"
        if pl_cyc.get(itm) == 1:
            continue

        #if itm in lrq0_entry0_wait_comb_list:
        #    if seen_wait_comb:
        #        continue
        #    itm_nm = "lrq0_entry0_wait_comb"
        #    seen_wait_comb = True
        #else:
        itm_nm = itm

        for set_idx, aSet in enumerate(reachable_sets):
            if not itm in aSet:
                continue

            
            res, bnd, time = df_query(df, "cvr_rtl2mupath_over1cyc_%d_%s" % (set_idx, itm_nm), exact_name=True)
            #print(res)
            if res == "unreachable" or (res == "undetermined" and bnd >= 20) or res == "bounded_unreachable_user":
                # can reach only 1 cycle even though other set has this nodes
                # over 1 cycle
                result.append((set_idx, itm, 0))
            else:
                result.append((set_idx, itm, 1))

    with open("cycle_count_gt1_perset.txt", "w") as f:
        for itm in result:
            f.write("%d,%s,%d\n" % itm)

def stats():
    max_cyc_perloc = get_array("max_cycle_per_pl.txt")
    pl_cyc = {}
    for itm in max_cyc_perloc:
        pl_cyc[itm[0]] = int(itm[1])

    comps = []
    incomps = []
    for itm in cv_perflocs:
        fnm = os.getcwd() + "/max_cycle_count_%s.csv" % (itm)
        df = pd.read_csv(fnm, dtype=mydtypes)
        df = df[df['Name'].str.contains('consec_%s' % itm)]
        for r_, time in zip(list(df['Result'].values), list(df['Time'].values)):
            t_ = float(time[:-2])
            if r_ in ["covered", "unreachable", "cex", "proven"]:
                comps.append(t_)
            else:
                incomps.append((t_, -1))

        #if pl_cyc[itm] != 1:
        #    for set_idx, aSet in enumerate(reachable_sets):
        #        if not itm in aSet:
        #            continue
        #        #fnm = os.getcwd() + "/over1cyc_%d_%s.csv" % (set_idx, itm)
        #        #df = pd.read_csv(fnm, dtype=mydtypes)
        #        #res, bnd, time = df_query(df, "CS_gt_%s_%d" % (itm, 2))
        #        #if res in ["covered", "unreachable", "cex", "proven"]:
        #        #    comps.append(time)
        #        #else:
        #        #    incomps.append((time, bnd))


        #fnm = os.getcwd() + "/max_cycle_count_%s.csv" % (itm)
        #df = pd.read_csv(fnm, dtype=mydtypes)

        #for idx, tar_row in df[df['Name'].str.contains("consec_%s" % itm)].iterrows():
        #    res = tar_row['Result']
        #    bnd = tar_row['Bound']
        #    sr = re.search("([0-9]+)", bnd)
        #    if sr is not None:
        #        bnd = int(sr.group(1))
        #    else:
        #        bnd = None
        #    time = float(tar_row['Time'][:-2])
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
