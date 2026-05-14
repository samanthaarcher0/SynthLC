import ast
import json
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

#HEADERFILE='../header_spv.sv'
HEADERFILE='../header.sv'
with open(HEADERFILE, "r") as f:
    lines = f.readlines()
h_ = "".join(lines)
e_ = ""


#HEADERTCL="../header_spv.tcl"
HEADERTCL="../header.tcl"
htcl_ = ""
#htcl_ = "check_spv -init\n"
with open(HEADERTCL, "r") as f:
    for line in f:
        htcl_ += line


cv_perflocs = get_array("../xCoverAPerflocDiv/cover_individual.txt")


try:
    with open("../../../../user_provided_files/combined_pls.txt", "r") as f:
        combined_pls = f.readlines()
    combined_pl_dict = get_combined_pls_dict(combined_pls)
except FileNotFoundError:
    combined_pl_dict = {}
pl_to_comb = dict()
for comb, pl_list in combined_pl_dict.items():
    for pl in pl_list:
        if pl_to_comb.get(pl) is not None:
            assert(0)
        else:
            pl_to_comb[pl] = comb


#for itm in cv_perflocs:
#    h_ += hpn_reg_t2.format(s1=itm)

decisions = dict()
with open("../xFollowerSetsOnly/decisions.txt", 'r') as file:
    for line_num, line in enumerate(file, 1):
        line = line.strip()
        if not line:
            continue
        if ', [' in line:
            key_part, value_part = line.split(', [', 1)
            key = key_part.strip()
            list_str = '[' + value_part
            decisions[key] = ast.literal_eval(list_str)

print(decisions)


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
    pl_signals[comb_pl] = pl_signals[pl_list[0]]


taint = "taint_rs1"
with open(f"../../../../user_provided_files/{taint}.json", "r") as f:
    tainted_signals = json.load(f)
print(tainted_signals)

JOB="spv_rtl2mupath_" + taint

not_throughs = "-not_through {amo_resp.ack amo_resp.result fetch_entry_if_id.address fetch_entry_if_id.branch_predict.cf fetch_entry_if_id.branch_predict.predict_address fetch_entry_if_id.ex.cause fetch_entry_if_id.ex.tval fetch_entry_if_id.ex.valid tmp_icache_dreq_cache_if.data tmp_icache_dreq_cache_if.ex.cause tmp_icache_dreq_cache_if.ex.tval tmp_icache_dreq_cache_if.ex.valid tmp_icache_dreq_cache_if.ready tmp_icache_dreq_cache_if.vaddr tmp_icache_dreq_cache_if.valid tmp_icache_dreq_if_cache.kill_s1 tmp_icache_dreq_if_cache.kill_s2 tmp_icache_dreq_if_cache.req tmp_icache_dreq_if_cache.spec tmp_icache_dreq_if_cache.vaddr issue_stage_i.i_scoreboard.rs2_fwd_req issue_stage_i.i_scoreboard.rs1_fwd_req}"
 
def gen():
    global htcl_

#     TMPLT = '''
# check_spv -create -name {tnm}_src_{s}_dest_{d} -from {{{tsigs}}} -from_precond {{{tval}}} -to {{{dest_sig}}} -to_precond {{$past({src}) & {dest} }}
# '''

#    TMPLT = '''
#check_spv -create -name {tnm}_src_{s}_dest_{d} -from {{{tsigs}}} -from_precond {{{tval}}} -to {{{dest_sig}}} -to_precond {{$past({src})}} {options}
#'''

    TMPLT = '''
check_spv -create -name {tnm}_src_{s}_dest_{d} -from {{{tsigs}}} -from_precond {{{tval}}} -to {{{dest_sig}}} -to_precond {{$past({src})}} {options}
'''

    #htcl_ += remove_stopats

    all_tainted_signals = list()
    for op, defs in tainted_signals.items():
        sig = defs.get("sigs")
        val = defs.get("valid")
        tnm = taint + "_" + op
        all_tainted_signals.append(sig)

    for s, dest_set_list in decisions.items():
        added_sigs = list()
        cnt = 0
        for dest_set in dest_set_list:
            if len(dest_set) > 0:
                for dest in dest_set:
                    for pl_sig in pl_signals[dest]:
                        if pl_sig not in added_sigs:
                            added_sigs.append(pl_sig)
        htcl_ += TMPLT.format(tnm=tnm, s=s, d=cnt, tsigs=" ".join(all_tainted_signals), tval=val, dest_sig=" ".join(added_sigs), src=prefix+s, options=not_throughs)
        cnt += 1



    with open (f"{JOB}.tcl", "w") as f:
        f.write(htcl_)
        f.write("\n#set_message -warning ESPV338\n")
        f.write("#check_spv -prove -strategy proof\n")
        f.write("#report -property $props -csv -results -file %s.csv -force\n" % JOB)
        f.write("#save %s.db -force\n" % JOB)
        f.write("#file copy %s.csv %s/.\n" % (JOB, os.getcwd()))
    with open (f"{JOB}.sv", "w") as f:
        f.write(h_)
        f.write(e_)

    return


def pp():


    return


if len(sys.argv) != 2:
    print("gen/pp")
    exit(0)

opt = sys.argv[1]
if opt == "gen":
    gen()
elif opt == "pp":
    pp()

