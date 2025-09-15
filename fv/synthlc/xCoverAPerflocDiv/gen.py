import os 
import pandas as pd
import sys
sys.path.append("../../src")
from util import *
if len(sys.argv) != 2:
    print("gen/pp")
    exit(0)


HEADERFILE="../header.sv"
OUTDIR="out"
perflocs = get_perflocs(HEADERFILE)

with open("../../../../user_provided_files/combined_pls.txt", "r") as f:
    combined_pls = f.readlines()
combined_pl_dict = get_combined_pls_dict(combined_pls)

print("perflocs: ", perflocs)

with open(HEADERFILE, "r") as f:
    lines = f.readlines()
h_ = "".join(lines[:-5])
t_ = "".join(lines[-5:])


HEADERTCL='../header.tcl'
htcl_ = ""
with open(HEADERTCL, "r") as f:
    for line in f:
        htcl_ += line

JOB="rtl2mupath_instn_reachable_perf_loc"

def gen():

    with open(f"{JOB}.tcl", "w") as f:
        f.write(htcl_)
        for idx, itm in enumerate(perflocs):
            f.write("cover -name cvr_rtl2mupath_C_%s {(@(posedge %s%s) %s%s)}\n" % (idx, prefix, GLBCLK, prefix, itm))

        f.write("set props [get_property_list -include {name cvr_rtl2mupath_C*}]\n")
        f.write("prove -property $props\n")
        f.write("report -property $props -csv -results -file %s.csv -force\n" % JOB)
        f.write("save %s.db -force\n" % JOB)
        f.write("file copy -force %s.csv %s\n" % (JOB, os.getcwd()))
    #    f.write("exit\n")

    with open(f"{JOB}.sv", "w") as f:
        f.write(h_)
        f.write(t_)


def stats():
    print("====== stats ==============")

    FILE = f"{JOB}.csv"
    plist = ["C_%d" % i for i in range(len(perflocs))]

    comps = []
    incomps = []
    if os.path.exists(FILE):
        df = pd.read_csv(FILE, dtype=mydtypes)
        for itm in plist:
            res, bnd, time = df_query(df, itm, exact_name=True)
            if res in ["covered", "unreachable", "cex", "proven", "bounded_proven_user"]:
                comps.append(time)
            else:
                incomps.append((time, bnd))
            
    for idx, itm in enumerate(perflocs):
        FILE = "%d.csv" % idx
        if os.path.exists(FILE):
            df = pd.read_csv(FILE, dtype=mydtypes)
        else:
            continue
        #print(FILE)
        res, bnd, time = df_query(df,":noConflict")

        if res in ["covered", "unreachable", "cex", "proven", "bounded_proven_user"]:
            comps.append(time)
        else:
            incomps.append((time, bnd))

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


def pp():
    print("====== pp ==============")
    FILE = f"{JOB}.csv"
    cover_set = []
    undetermined = []
    if os.path.exists(FILE):
        TMPLT="cvr_rtl2mupath_C_%d"
        plist = [TMPLT % i for i in range(len(perflocs))]
        ret = get_results(FILE, plist)
        for itm, r in zip(perflocs, ret):
            if r[0] == "covered":
                cover_set.append(itm)
            if r[0] == "undetermined":
                undetermined.append(itm)

        with open("cover_individual_all.txt", "w") as f:
            for itm in cover_set:
                f.write(itm + "\n")
    
        with open("cover_individual.txt", "w") as f:
            # write only PLs that are covered that are not in combined PLs
            # if the combined_pl is covered, then it will be included itself
            for itm in cover_set:
                in_comb_pl = False
                for comb_pl_name, pl_set in combined_pl_dict.items():
                    if itm in pl_set:
                        in_comb_pl = True
                if not in_comb_pl:                
                    f.write(itm + "\n")

        with open("undetermined.txt", "w") as f:
            for itm in undetermined:
                f.write(itm + "\n")

    #print("====================")
    always_set = []
    for idx, itm in enumerate(perflocs):
        FILE="%d.csv" % idx
        r_, t_, b_ = get_result(FILE, ":noConflict")
        if (r_ == "cex"):
            always_set.append(itm)
    with open("always_reach.txt", "w") as f:
        for itm in always_set:
            f.write(itm + "\n")
    #print(always_set)
    #print("====================")

opt = sys.argv[1]
if opt == "gen":
    gen()
elif opt == "pp":
    pp()
elif opt == "stats":
    stats()
elif opt == "gen_s2":
    gen_s2()
        
