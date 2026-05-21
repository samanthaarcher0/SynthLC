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
sys.path.append("../../src_ift_utils")
from IFT_template import *


HEADERFILE='../header.sv'
with open(HEADERFILE, "r") as f:
    lines = f.readlines()
# Replace the SPV transmitter define with the IFT T_FROM_IUV define + RS1 taint operand
#h_ = "".join(lines).replace("`define INTRA_TRANSMITTER", "`define T_FROM_IUV\n`define RS1")
h_ = ""
e_ = ""


HEADERTCL="../../../src_ift/jg2.tcl"
htcl_ = ""
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

# Parse common_header.sv to get the individual _t0 component signals for each PL.
# Each PL-level wire (e.g. scb_0_s8_t0) is an OR of the underlying CellIFT shadow
# signals; use those directly so we don't depend on the wire declaration being in scope.
COMMON_HEADER = "../../../src_ift/common_header.sv"
pl_t0_sigs = {}
with open(COMMON_HEADER, "r") as f:
    for line in f:
        line = line.strip()
        m = re.match(r'wire\s+(\w+)_t0\s*=\s*\|\{(.+)\}\s*;', line)
        if m:
            pl_name = m.group(1)
            sigs_str = m.group(2)
            sigs = [s.strip() for s in sigs_str.split(',') if s.strip()]
            pl_t0_sigs[pl_name] = sigs


taint = "taint_rs1"
with open(f"../../../../user_provided_files/{taint}.json", "r") as f:
    tainted_signals = json.load(f)
print(tainted_signals)

JOB="ift_rtl2mupath_" + taint

PROP_TMPLT = '''\
cover -name {{{tnm}_src_{s}_dest_{d}}} {{@(posedge clk_i) {src} ##1 (|{{{t0_sigs}, 1\'b0}})}}
'''

PROP_TMPLT2 = '''\
cover -name {{{tnm}_src_{s}_dest_{d}}} {{@(posedge clk_i) {src} ##1 ( {in_dest} && (|{{{t0_sigs}, 1\'b0}}))}}
'''

def gen():
    global htcl_

    for op, defs in tainted_signals.items():
        #tnm = taint + "_" + op
        tnm = taint

    all_dest_pls = set()
    for s, dest_set_list in decisions.items():
        all_dest_pls = set()
        for dest_set in dest_set_list:
            for dest in dest_set:
                all_dest_pls.add(dest)

        cnt = 0
        for dest_set in dest_set_list:
            added_t0_sigs = list()
            in_dest = ""
            if len(dest_set) == 0:
                for dest in all_dest_pls:
                    # Use the individual CellIFT shadow signals that compose this
                    # PL's taint wire, so we don't need the wire to be in scope.
                    #for t0_sig in pl_t0_sigs.get(dest, [dest + "_t0"]):
                    t0_sig = prefix + dest + "_t0"
                    if t0_sig not in added_t0_sigs:
                        added_t0_sigs.append(t0_sig)
                    in_dest += f"!{prefix+dest} && "
            else:
                for dest in all_dest_pls:
                    if dest in dest_set:
                        in_dest += f"{prefix+dest} && "
                        # Use the individual CellIFT shadow signals that compose this
                        # PL's taint wire, so we don't need the wire to be in scope.
                        #for t0_sig in pl_t0_sigs.get(dest, [dest + "_t0"]):
                        t0_sig = prefix + dest + "_t0"    
                        if t0_sig not in added_t0_sigs:
                            added_t0_sigs.append(t0_sig)
                    else:
                        in_dest += f"!{prefix+dest} && "
            
            in_dest += "1'b1"
            if added_t0_sigs:
                htcl_ += PROP_TMPLT2.format(
                    tnm=tnm,
                    s=s,
                    d=cnt,
                    src=prefix + s,
                    in_dest=in_dest,
                    t0_sigs=", ".join(added_t0_sigs)
                )
            cnt += 1
    
    iii = ""
    with open("../idef.sv", "r") as idef:
        for line in idef:
            iii += line
   
    DEFINEOPTAINT="`define BORTHRS"
    outstring = itself_assume_only_template
    rep_pairs = [
        ("OP_TAINT", DEFINEOPTAINT),
        ("INSTN_CONSTRAINT", iii),
        ]
    for tt in rep_pairs:
        outstring = outstring.replace(tt[0], tt[1])

    with open (f"{JOB}.sv", "w") as f:
        f.write(h_)
        f.write(outstring) 
        f.write(e_)
    with open (f"{JOB}.tcl", "w") as f:
        f.write(htcl_)
        f.write("\nprove -all\n")
        f.write("report -property $props -csv -results -file %s.csv -force\n" % JOB)
        f.write("#save %s.db -force\n" % JOB)
        f.write("file copy %s.csv %s/.\n" % (JOB, os.getcwd()))

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
