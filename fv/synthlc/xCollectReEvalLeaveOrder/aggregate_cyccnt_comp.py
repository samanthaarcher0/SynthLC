import re
import networkx as nx
from itertools import chain, combinations
import textwrap
import pandas as pd
import numpy as np
import os
import itertools
import pandas as pd
import sys
sys.path.append("../../src")
from util import *
from HB_template import *
from DOT_template import *
from solver import *


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

JOB_enter_order = "rtl2mupath_enter_order"
JOB = "rtl2mupath_leave_order"
JOB2 = "rtl2mupath_leave_order2"

class GenComb:
    def __init__(self, arr):
        self.arr = arr
        self.res = []
        self.acc = []
    def gen(self):
        self.get_all_combination(0)
    def get_all_combination(self, idx):
        if idx == len(self.arr):
            self.res.append(self.acc[::])
            return
        # e weight 
        results = []
        for t in range(0, self.arr[idx]):
            self.acc.append(t)
            self.get_all_combination(idx+1)
            self.acc.pop()
# For cycle count per IUV or per PL set
is_interference_case = "III" in os.getcwd()

cv_perflocs = get_array("../xCoverAPerflocDiv/cover_individual.txt")
#edge = get_array("../../xGenPerfLocDfgDiv/dfg_e.txt")
edge = get_array("../xCoverCandidateHBEdges/covered_edges.txt")



try:
    with open("../../../../user_provided_files/combined_pls.txt", "r") as f:
        combined_pls = f.readlines()
    combined_pl_dict = get_combined_pls_dict(combined_pls)
except FileNotFoundError:
    combined_pl_dict = {}


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
    
#print("TODO: for pair of nodes after transitive reduction we shoudl check if \
#its possible to have two happen concurrently if not we should see if per PL set \
#is always one way or the other")

enter_concurrent_pairs = get_array("../xHBPerfG_dfg_v3_div/aws_concurrent.txt", exit_on_fail=False)
# print(type(enter_concurrent_pairs[0]))
whb_edge = get_array("../xHBPerfG_dfg_v3_div/whb_proven.txt", exit_on_fail=False)
hb_edge = get_array("../xHBPerfG_dfg_v3_div/hb_proven.txt", exit_on_fail=False)
print("HB edge:", hb_edge)
reachable_sets = get_array("../xPerfLocCycleCount/new_reachable_sets.txt", arr_as_ele = True)

#if os.path.exists("../xPerfLocCycleCount_v2/max_cycle_per_pl.txt"):
#    max_cyc_per_pl_raw = get_array("../xPerfLocCycleCount_v2/max_cycle_per_pl.txt")
#    print("perfloc cycle v2")
#else:
max_cyc_per_pl_raw = get_array("../xPerfLocCycleCount/max_cycle_per_pl.txt")
#print("TBD")
    #if os.path.exists("../xPerfLocCycleCount/max_cycle_per_pl_covered.txt"):
    #    max_cyc_per_pl_raw = get_array("../xPerfLocCycleCount/max_cycle_per_pl_covered.txt")
    #    print("pl_covered.txt")
    #else:
    #    max_cyc_per_pl_raw = get_array("../xPerfLocCycleCount/max_cycle_per_pl.txt")
    #    print("pl.txt")

max_cyc_per_pl = {}
for itm in max_cyc_per_pl_raw:
    max_cyc_per_pl[itm[0]] = int(itm[1])
#if os.path.exists("../xPerfLocCycleCount_v2/max_cycle_per_pl.txt"):
#    cyc_cnt_gt1_per_set_raw = get_array("../xPerfLocCycleCount_v2/cycle_count_gt1_perset.txt")
#else:
cyc_cnt_gt1_per_set_raw = get_array("../xPerfLocCycleCount/cycle_count_gt1_perset.txt")

cyc_cnt_gt1_per_set = {}
for itm in cyc_cnt_gt1_per_set_raw:
    set_idx, pl, gt1 = itm
    set_idx = int(set_idx)
    if gt1 == "1":
        if cyc_cnt_gt1_per_set.get(set_idx) is None:
            cyc_cnt_gt1_per_set[set_idx] = []
        cyc_cnt_gt1_per_set[set_idx].append(pl)
#print(cyc_cnt_gt1_per_set)


leaving_hb_proven_res = get_array("../xHBPerfG_leaving/leaving_hb_proven.txt", exit_on_fail=False)
leaving_hb_proven_res_pairs = []
for itm in leaving_hb_proven_res:
    u = itm[1]
    if itm[0] == "1":
        u += "__final"
    v = itm[3]
    if itm[2] == "1":
        v += "__final"
    leaving_hb_proven_res_pairs.append((u, v))
#print("leaving_hb_proven_res_pairs:", leaving_hb_proven_res_pairs)
aws_concur_leaving = get_array("../xHBPerfG_leaving/leaving_concur_proven.txt", exit_on_fail=False)
aws_concur_leaving_pairs = []
for itm in aws_concur_leaving:
    u = itm[1]
    if itm[0] == "1":
        u += "__final"
    v = itm[3]
    if itm[2] == "1":
        v += "__final"
    aws_concur_leaving_pairs.append((u, v))
whb_leaving_res = get_array("../xHBPerfG_leaving/leaving_whb_proven.txt", exit_on_fail=False)

undetermined_dfe = get_array("../xHBPerfG_dfg_v3_div/undetermined_under_bound.txt") 
undetermined_whb = []
undetermined_hb = []
undetermined_concur = []
cnt = 0
for itm in undetermined_dfe:
    if "*" in itm:
        cnt += 1
        continue
    if cnt == 1:
        undetermined_hb.append((itm[0], itm[1]))
    if cnt == 2:
        undetermined_whb.append((itm[0], itm[1]))
    if cnt == 3:
        undetermined_concur.append((itm[0], itm[1]))
hb_cex_e = get_array("../xHBPerfG_dfg_v3_div/whb_todo.txt") 


# node_rows = {}
# label_s = ""
# row = 0
# for _, v in enumerate(list_rows):
#     node_rows[v] = row
#     label_s += label.format(nm=v,loc=row)
#     row += 1
#     if v in max_cyc_per_pl and max_cyc_per_pl[v] > 1:
#     #if v in over1cyc_pl:
#         label_s += label.format(nm = v + "__final", loc=row)
#         node_rows[v + "__final"] = row
#         row += 1

path_cnt = 0

cv_perflocs_with_final = list()
for itm in cv_perflocs:
    h_ += hpn_reg_t2.format(s1=itm)
    cv_perflocs_with_final.append(itm)

for PL, cnt in max_cyc_per_pl.items():
    if cnt > 1:
        h_ += pl_repeated_hpn_reg_nm_t.format(s1=PL, nm=PL+"__final")
        cv_perflocs_with_final.append(PL+"__final")


def gen():

    global h_
    global htcl_
    # if not os.path.isdir("out_complete_2"):
    #     os.mkdir("out_complete_2")

    # if not os.path.isdir("out_complete_2_setcover"):
        # os.mkdir("out_complete_2_setcover")

    cnt_todo_cover_final = 0

    df = pd.read_csv(f"../xCollectReEval/{JOB_enter_order}.csv", dtype=mydtypes)
    covered = 0
    total_sets = 0
    total_combs = 0
    skipped_no_final = 0
    num_sat = 0

    assumption_names = list()
    for set_idx, aSet in enumerate(reachable_sets):
        total_sets += 1
        cover_hb = []
        cover_concur = []

        undet_hb = []
        undet_concur = []

        print("===== SET idx: %d ====" % set_idx)
        print(aSet)

        result_edges = {}
        print("  Getting entering edge results")
        with open("../xCollectReEval/%d_edge_todo_per_set.txt" % set_idx, "r") as f:
            for line in f:
                pair = (line.split(":")[0]).split(",")
                seqs = (line[:-1].split(":")[1]).split(",")
                assert(df is not None)

                for hbtype in seqs:
                    prop = None
                    if hbtype == ">":
                        prop = "cvr_rtl2mupath_CS_{idx}_{e0}_hb_{e1}".format(idx=set_idx, e0=pair[0], e1=pair[1])
                        res, bnd, time = df_query(df, prop, exact_name=True)
                        if res == "covered":
                            covered += 1 
                            cover_hb.append([pair[0], pair[1]])
                            if ((pair[0], pair[1]) in result_edges):
                                result_edges[(pair[0], pair[1])].append(">")
                            else:
                                result_edges[(pair[0], pair[1])] = [">"]
                        elif res == "undetermined":
                            undet_hb.append([pair[0], pair[1]])
                    if hbtype == "<":
                        prop = "cvr_rtl2mupath_CS_{idx}_{e0}_hb_{e1}".format(idx=set_idx, e0=pair[1], e1=pair[0])
                        res, bnd, time = df_query(df, prop, exact_name=True)
                        if res == "covered":
                            covered += 1
                            cover_hb.append([pair[1], pair[0]])
                            if ((pair[0], pair[1]) in result_edges):
                                result_edges[(pair[0], pair[1])].append("<")
                            else:
                                result_edges[(pair[0], pair[1])] = ["<"]
                        elif res == "undetermined":
                            undet_hb.append([pair[0], pair[1]])
                    if hbtype == "=":
                        prop = "cvr_rtl2mupath_CS_{idx}_{e0}_concur_{e1}".format(idx=set_idx, e0=pair[1], e1=pair[0])
                        res, bnd, time = df_query(df, prop, exact_name=True)
                        if res == "covered":
                            covered += 1
                            cover_concur.append([pair[0], pair[1]])
                            if ((pair[0], pair[1]) in result_edges):
                                result_edges[(pair[0], pair[1])].append("=")
                            else:
                                result_edges[(pair[0], pair[1])] = ["="]
                        elif res == "undetermined":
                            undet_concur.append([pair[0], pair[1]])
        print("    hb ", cover_hb)
        print("    concur ", cover_concur)
        #print("undeter_hb ", undet_hb)
        #print("undeter_concur ", undet_concur)
        var_cnt = 1
        sets_edges = []
        for k, v in result_edges.items():
            var_cnt *= len(v)
            sets_edges.append([(k, v_i) for v_i in v])

        comb_edges = list(itertools.product(*sets_edges))
        print(f"    Combinations of entering edges: {len(comb_edges)}")
        # print(f"    combinations of entering edges: {comb_edges}")

        with open("%d_combination.txt" % set_idx, "w") as f:
            for itm in comb_edges:
                for e in itm:
                    f.write("%s,%s,%s," % (e[0][0], e[0][1], e[1]))
                f.write("\n") 

        for combidx, cv_edge_comb in enumerate(comb_edges):
            print(f"  Considering combination of entering edge {set_idx}, comb {combidx}")
            total_combs += 1
            DG = nx.DiGraph()

            print("    Adding HB edges")
            for e in hb_edge:
                if e[0] in aSet and e[1] in aSet:
                    DG.add_edge(e[0], e[1])
            concur_in_comb = []
            print("    Adding entering comb edges")
            for e in cv_edge_comb:
                t_ = e[1]
                p = e[0]
                if t_ == '>':
                    DG.add_edge(p[0], p[1])
                if t_ == '<':
                    DG.add_edge(p[1], p[0])
                if t_ == '=':
                    concur_in_comb.append([p[0],p[1]])
                    

            # concurrent tagged through same color 
            color_cnt=4
            node_colors = {}
            for itm in enter_concurrent_pairs:
                a, b = itm 
                if a in aSet and b in aSet:
                    c = None
                    if itm[0] in node_colors:
                        c = node_colors[itm[0]]
                    elif itm[1] in node_colors:
                        c = node_colors[itm[1]]

                    if c is None:
                        c = color_cnt
                        color_cnt += 1
                    
                    node_colors[a] = c
                    node_colors[b] = c


            # same iid leave order same as enter order
            implied_edges_same_iid = []

            edge_weight = {}
            iid_map_tmp = iid_map

            print("    Adding nodes")
            for itm in aSet:
                DG.add_node(itm)

                if "__final" in itm:
                    non_final_itm = itm.replace("__final", "")
                    edge_weight[(non_final_itm, itm)] = \
                        [t for t in range(1, max_cyc_per_pl[non_final_itm])] #max #[int(r)-1 for r in cyc]
                    iid_map_tmp[itm] = iid_map_tmp[non_final_itm]

            print("    Adding edges between first and last visit")
            for itm in aSet:
                if "__final" in itm:
                    # since its same ufsm, if entering e[0] happens-before entering
                    # e[1], leaving e[0] should also happens-before entering e[1]
                    for e in DG.out_edges(non_final_itm):
                        if iid_map_tmp[e[0]] == iid_map_tmp[e[1]]:
                            implied_edges_same_iid.append((itm, e[1]))

                    DG.add_edge(non_final_itm, itm)
                    #print("adding edge between first and last visit: ", (non_final_itm, itm))
            
            # node_colors always concurrent -> constraint on the edge weight 
            for itm in aws_concur_leaving_pairs:
                if itm[0] in DG.nodes() and itm[1] in DG.nodes():
                    c = None
                    if itm[0] in node_colors:
                        c = node_colors[itm[0]]
                    elif itm[1] in node_colors:
                        c = node_colors[itm[1]]

                    if c is None:
                        c = color_cnt
                        color_cnt += 1
                    node_colors[itm[0]] = c
                    node_colors[itm[1]] = c


            print("    Adding implied edges between same iid")
            for e in implied_edges_same_iid:
                DG.add_edge(*e)

            print("    Adding leaving HB proven edges")
            for itm in leaving_hb_proven_res_pairs:

                if itm[0] in DG.nodes() and itm[1] in DG.nodes():
                    DG.add_edge(itm[0], itm[1])
                    #print(f"Adding proven HB edge between: {itm[0]}, {itm[1]}")

            print("    Adding edges resulting from concurrent nodes")
            for e in enter_concurrent_pairs + aws_concur_leaving_pairs + concur_in_comb:
                a, b = e
                if not (a in DG.nodes() and b in DG.nodes()):
                    continue

                in_edges = DG.in_edges(e[0])
                for e_prime in in_edges:
                    assert(e_prime[1] == e[0])
                    DG.add_edge(e_prime[0], e[1])
                    #print(f"Adding edge because {e} are conccurent and {e_prime} are HB: {e_prime[0]}, {e[1]}")
                
                in_edges = DG.in_edges(e[1])
                for e_prime in in_edges:
                    assert(e_prime[1] == e[1])
                    DG.add_edge(e_prime[0], e[0])
                    #print(f"Adding edge because {e} are conccurent and {e_prime} are HB: {e_prime[0]}, {e[0]}")

                out_edges = DG.out_edges(e[0])
                for e_prime in out_edges:
                    assert(e_prime[0] == e[0])
                    DG.add_edge(e[1], e_prime[1])
                    #print(f"Adding edge because {e} are conccurent and {e_prime} are HB: {e[1]}, {e_prime[1]}")

                out_edges = DG.out_edges(e[1])
                for e_prime in out_edges:
                    assert(e_prime[0] == e[1])
                    DG.add_edge(e[0], e_prime[1])
                    #print(f"Adding edge because {e} are conccurent and {e_prime} are HB: {e[0]}, {e_prime[1]}")

            # Check for cycles more thoroughly
            cycles = list(nx.simple_cycles(DG))
            has_cycles = len(cycles) > 0
            
            # Also check if the graph is a DAG using NetworkX's built-in function
            is_dag = nx.is_directed_acyclic_graph(DG)
            
            if has_cycles or not is_dag:
                print("Issue %d, combidx %d cyclic" % (set_idx, combidx))
                print(f"    cv_edge_comb: {cv_edge_comb}")
                print(f"    cycles: {cycles}")
                continue
                
            TR = nx.transitive_reduction(DG)
            TC = nx.transitive_closure(DG, reflexive=False)
            reduce_e = list(TR.edges)

            #print(f"TR: {TR.edges}")
            #print(f"TC: {TC.edges}")
            #print(f"edge_weight: {edge_weight}")
            #print(f"implied_edges_same_iid: {implied_edges_same_iid}")
            #print(f"edge_weight_single: {edge_weight_single}")
            #print(f"concur: {enter_concurrent_pairs + concur_in_comb + aws_concur_leaving_pairs}")
            #print(f"whb_edge: {whb_edge}")


            ################################################################################ 
            # setup solver 
            ################################################################################ 
            edge_weight_single = []
            slv = MySolver(TR, edge_weight, implied_edges_same_iid, iid_map_tmp,
                    edge_weight_single, enter_concurrent_pairs + concur_in_comb +
                    aws_concur_leaving_pairs, whb_edge)
            r = slv.add_constraints()
            if not r:
                print("  Set idx %d, combidx %d not sat" % (set_idx, combidx))
                continue
            num_sat += 1

            ################################################################################ 
            # Get all edges that is not proven 
            ################################################################################ 

            print("    Computing final edges that are not proven")
            pairs_final = {}
            for idx, eorg in enumerate(edge):
                if not (eorg[0] in aSet and eorg[1] in aSet):
                    #print(f"Edge {eorg} not in set")
                    continue
                if (iid_map_tmp[eorg[0]] == iid_map_tmp[eorg[1]]):
                    #print(f"same iid map for edge {eorg}: {iid_map_tmp[eorg[0]]} {iid_map_tmp[eorg[1]]} ")
                    continue
                e_primes = [] 
                if eorg[0] + "__final" in TC.nodes() and eorg[1] in aSet:
                    e_primes.append([eorg[0] + "__final", eorg[1]])
                if eorg[0] in aSet and eorg[1] + "__final" in TC.nodes():
                    e_primes.append([eorg[0], eorg[1] + "__final"])
                if (eorg[1] + "__final" in TC.nodes()) and (eorg[0] + "__final" in TC.nodes()):
                    e_primes.append([eorg[0] + "__final" , eorg[1] + "__final"])
                if len(e_primes) == 0:
                    #print(f"no remaining edges to check: {eorg}")
                    continue
                for e in e_primes:
                    if tuple(e) in TC.edges() or (e[1], e[0]) in TC.edges():
                        #print("set idx %d comb %d already hb %s %s" % (set_idx, combidx, e[0], e[1])) 
                        continue
                    if e in edge_weight_single or (e[1], e[0]) in edge_weight_single:
                        #print("set idx %d comb %d edge weight single %s %s" % (set_idx, combidx, e[0], e[1]))
                        continue
                    if e in enter_concurrent_pairs or [e[1], e[0]] in enter_concurrent_pairs:
                        #print("set idx %d comb %d already concurrent %s %s" % (set_idx, combidx, e[0], e[1])) 
                        continue
                    if slv.check_imp_hb(e):
                        #print("set idx %d %d imp hb %s %s" % (set_idx, combidx, e[0], e[1]))
                        continue

                    can_be_hb = slv.check_hb_possibility(e)
                    if not can_be_hb:
                        #print("set idx %d %d imp can't be hb %s %s" % (set_idx, combidx, e[0], e[1]))
                        continue
                    # if no hb relation between enter nodes we skip...
                    #enter_nodes = [e[0].split("__final")[0], e[1].split("__final")[0]]
                    #if slv.check_hb_possibility(enter_nodes) and slv.check_hb_possibility([enter_nodes[1],enter_nodes[0]]):
                    #    print("???!!! no fixed order in enter node?", e[1], e[0])
                    #    continue

                    if e[0] < e[1]:
                        if (e[0], e[1]) in pairs_final:
                            # e[0] HB e[1]
                            pairs_final[(e[0], e[1])].append(">")
                        else:
                            pairs_final[(e[0], e[1])] = [">", "="]
                    else:
                        if (e[1], e[0]) in pairs_final:
                            pairs_final[(e[1], e[0])].append("<")
                        else:
                            pairs_final[(e[1], e[0])] = ["<", "="]
                           
            cnt_setidx = 0
            print(f"    Pairs final")
            for k, v in pairs_final.items():
                print("      (%s, %s): %s" % (k[0], k[1], ",".join(v)))
                cnt_todo_cover_final += len(v)
                cnt_setidx += len(v)


            
            print("    Issue %d, combidx %d" % (set_idx, combidx))
            # print(f"    {cnt_setidx}")
            
            #pairs_todo_pruned = {}
            #for k, v in pairs_todo.items():
            #    pairs_todo_pruned[k] = v
            #    print("(%s, %s): %s" % (k[0], k[1], ",".join(v)))
            #    cnt_todo_cover_final += len(v)
            #print("========================================")

            with open("%d_%d_final_edge_todo_per_set.txt" % (set_idx, combidx), "w") as f:
                for k, v in pairs_final.items():
                    f.write("%s,%s:%s\n" % (k[0], k[1], ",".join(v)))
                    
            print("    Adding cover properties")
            tem = '''cover -name cvr_rtl2mupath_set_{idx}_comb_{combidx} {{(@(posedge {prefix}fv_clk) {set} & {asums})}};\n'''
            if cnt_setidx == 0:
                print("      No final edges to cover, only adding cover property for entering edge combination")
                if len(comb_edges) > 1:
                    # with open("out_complete_2_setcover/com_%d_%d.sv" % (set_idx, combidx), "w") as f:
                        # f.write(h_)
                    s = ""
                    ns = ""
                    all = ""
                    for pl in cv_perflocs_with_final:
                        if "__final" not in pl:
                            all += "{prefix}{s1} || ".format(s1=pl, prefix=prefix)
                        if not pl in aSet:
                            # f.write(no_s1_t.format(s1=pl))
                            ns += "{prefix}{s1}_hpn || ".format(s1=pl, prefix=prefix)
                        else:
                            # f.write(hpn_reg_t2.format(s1=pl))
                            s += "{prefix}{s1}_hpn && ".format(s1=pl, prefix=prefix)
                    s += "1'b1 "
                    ns += "1'b0 "
                    all += "1'b0 "
                    set = s + " & !(%s)" % ns + " & !(%s)" % all
                    # f.write("wire set_r = %s;\n" % s)
                    asums = ""
                    for e in cv_edge_comb:
                        t_ = e[1]
                        p = e[0]
                        assert(not("__final" in p[0] or "__final" in p[1]))

                        if t_ == '>':
                            # f.write(A_enter_hb_enter.format(e0=p[0], e1=p[1]))
                            asum = A_enter_hb_enter_expr_only.format(e0=p[0], e1=p[1], prefix=prefix)
                            nm = p[0] + "_HB_" + p[1] + "_contradict_hpn"
                            if nm not in assumption_names:
                                h_ += contradict_flag_hpn_reg_nm_t.format(nm=nm, s1=asum)
                                assumption_names.append(nm)
                            asums +=  "!" + prefix + nm + " && "
                        if t_ == '<':
                            # f.write(A_enter_hb_enter.format(e0=p[1], e1=p[0]))
                            asum = A_enter_hb_enter_expr_only.format(e0=p[1], e1=p[0], prefix=prefix)
                            nm = p[1] + "_HB_" + p[0] + "_contradict_hpn"
                            if nm not in assumption_names:
                                assumption_names.append(nm)
                                h_ += contradict_flag_hpn_reg_nm_t.format(nm=nm, s1=asum)
                            asums += "!" + prefix + nm + " && "
                        if t_ == '=':
                            # f.write(A_enter_concur_enter.format(e0=p[0], e1=p[1]))
                            asum = A_enter_concur_enter_expr_only.format(e0=p[0], e1=p[1], prefix=prefix)
                            nm = p[0] + "_CONCUR_" + p[1] + "_contradict_hpn"
                            if nm not in assumption_names:
                                h_ += contradict_flag_hpn_reg_nm_t.format(nm=nm, s1=asum)
                                assumption_names.append(nm)
                            asums += "!" + prefix + nm + " && "
                    asums += "1'b1"
                    htcl_ += tem.format(idx=set_idx, prefix=prefix, set=set, asums=asums, combidx=combidx)

                else:
                    print("      Entering edge combination is empty")
            else:
                print("      Adding properties for final edges to cover:")

                #os.system("cp ./prove_from.tcl out_complete_2/com_%d_%d.tcl" % (set_idx, combidx))
                #with open("out_complete_2/com_%d_%d.sv" % (set_idx, combidx), "w") as f:
                    # f.write(h_)
                s = ""
                ns = ""
                all = ""
                for pl in cv_perflocs_with_final:
                    if "__final" not in pl:
                        all += "{prefix}{s1} || ".format(s1=pl, prefix=prefix)
                    if not pl in aSet:
                        # f.write(no_s1_t.format(s1=pl))
                        ns += "{prefix}{s1}_hpn || ".format(s1=pl, prefix=prefix)
                    else:
                        # f.write(hpn_reg_t2.format(s1=pl))
                        s += "{prefix}{s1}_hpn && ".format(s1=pl, prefix=prefix)
                s += "1'b1 "
                ns += "1'b0 "
                all += "1'b0 "
                set = s + " & !(%s)" % ns + " & !(%s)" % all
                # f.write("wire set_r = %s;\n" % s)
                asums = ""
                for e in cv_edge_comb:
                    t_ = e[1]
                    p = e[0]
                    assert(not("__final" in p[0] or "__final" in p[1]))

                    if t_ == '>':
                        # f.write(A_enter_hb_enter.format(e0=p[0], e1=p[1]))
                        asum = A_enter_hb_enter_expr_only.format(e0=p[0], e1=p[1], prefix=prefix)
                        nm = p[0] + "_HB_" + p[1] + "_contradict_hpn"
                        if nm not in assumption_names:
                            assumption_names.append(nm)
                            h_ += contradict_flag_hpn_reg_nm_t.format(nm=nm, s1=asum)
                        asums += "!" + prefix + nm + " && "
                    if t_ == '<':
                        # f.write(A_enter_hb_enter.format(e0=p[1], e1=p[0]))
                        asum = A_enter_hb_enter_expr_only.format(e0=p[1], e1=p[0], prefix=prefix)
                        nm = p[1] + "_HB_" + p[0] + "_contradict_hpn"
                        if nm not in assumption_names:
                            assumption_names.append(nm)
                            h_ += contradict_flag_hpn_reg_nm_t.format(nm=nm, s1=asum)
                        asums += "!" + prefix + nm + " && "
                    if t_ == '=':
                        # f.write(A_enter_concur_enter.format(e0=p[0], e1=p[1]))
                        asum = A_enter_concur_enter_expr_only.format(e0=p[0], e1=p[1], prefix=prefix)
                        nm = p[0] + "_CONCUR_" + p[1] + "_contradict_hpn"
                        if nm not in assumption_names:
                            assumption_names.append(nm)
                            h_ += contradict_flag_hpn_reg_nm_t.format(nm=nm, s1=asum)
                        asums += "!" + prefix + nm + " && "
                asums += "1'b1"
                if len(comb_edges) > 1:
                    htcl_ += tem.format(idx=set_idx, prefix=prefix, set=set, asums=asums, combidx=combidx)
                else:
                    print("      Entering edge combination is empty, only adding properties for final edges to cover")
                for k, v in pairs_final.items():
                    for tt in v:
                        if ">" == tt:
                            print(f"      {k[0]} > {k[1]}")
                            if '__final' in k[0] and '__final' in k[1]:
                                htcl_ += C_final_hb_final_tcl.format(e0nm=k[0], e1nm=k[1], e0=k[0][:-7], e1=k[1][:-7], set=set, asums=asums, prefix=prefix, idx=set_idx, combidx=combidx)
                            elif '__final' in k[0] and (not '__final' in k[1]):
                                htcl_ += C_final_hb_enter_tcl.format(e0nm=k[0], e1nm=k[1], e0=k[0][:-7], e1=k[1], set=set, asums=asums, prefix=prefix, idx=set_idx, combidx=combidx)
                            elif (not '__final' in k[0]) and '__final' in k[1]:
                                htcl_ += C_enter_hb_final_tcl.format(e0nm=k[0], e1nm=k[1], e0=k[0], e1=k[1][:-7], set=set, asums=asums, prefix=prefix, idx=set_idx, combidx=combidx)
                            else:
                                assert(0)

                        elif "<" == tt:
                            print(f"      {k[0]} < {k[1]}")
                            if '__final' in k[1] and '__final' in k[0]:
                                htcl_ += C_final_hb_final_tcl.format(e0nm=k[1], e1nm=k[0], e0=k[1][:-7], e1=k[0][:-7], set=set, asums=asums, prefix=prefix, idx=set_idx, combidx=combidx)
                            elif '__final' in k[1] and (not '__final' in k[0]):
                                htcl_ += C_final_hb_enter_tcl.format(e0nm=k[1], e1nm=k[0], e0=k[1][:-7], e1=k[0], set=set, asums=asums, prefix=prefix, idx=set_idx, combidx=combidx)
                            elif (not '__final' in k[1]) and '__final' in k[0]:
                                htcl_ += C_enter_hb_final_tcl.format(e0nm=k[1], e1nm=k[0], e0=k[1], e1=k[0][:-7], set=set, asums=asums, prefix=prefix, idx=set_idx, combidx=combidx)
                            else:
                                assert(0)
                        else:
                            print(f"      {k[0]} = {k[1]}")
                            if '__final' in k[0] and '__final' in k[1]:
                                htcl_ += C_final_concur_final_tcl.format(e0nm=k[0], e1nm=k[1], e0=k[0][:-7], e1=k[1][:-7], set=set, asums=asums, prefix=prefix, idx=set_idx, combidx=combidx)
                            elif '__final' in k[0] and (not '__final' in k[1]):                                      
                                htcl_ += C_final_concur_enter_tcl.format(e0nm=k[0], e1nm=k[1], e0=k[0][:-7], e1=k[1], set=set, asums=asums, prefix=prefix, idx=set_idx, combidx=combidx)
                            elif (not '__final' in k[0]) and '__final' in k[1]:                                      
                                htcl_ += C_enter_concur_final_tcl.format(e0nm=k[0], e1nm=k[1], e0=k[0], e1=k[1][:-7], set=set, asums=asums, prefix=prefix, idx=set_idx, combidx=combidx)
                            else:
                                assert(0)
            print("========================================")

    with open (f"{JOB}.tcl", "w") as f:
        f.write(htcl_)
        f.write("set props [get_property_list -include {name cvr_rtl2mupath_*}]\n")
        f.write("prove -property $props\n")
        f.write("report -property $props -csv -results -file %s.csv -force\n" % JOB)
        #f.write("save %s.db -force\n" % JOB)
        f.write("file copy %s.csv %s/.\n" % (JOB, os.getcwd()))
        f.write("exit\n")
    with open (f"{JOB}.sv", "w") as f:
        f.write(h_)
        f.write(e_)

    #print("cnt todo:", cnt_todo_cover)
    print("cnt_todo_cover_final", cnt_todo_cover_final)
    print(f"COVERED: {covered}")
    print(f"Skipped no final: {skipped_no_final}")
    print(f"total sets: {total_sets}")
    print(f"total combs: {total_combs}")
    print(f"num sat: {num_sat}")




def gen_s2():

    global h_
    global htcl_
    # if not os.path.isdir("out_complete_2"):
    #     os.mkdir("out_complete_2")

    # if not os.path.isdir("out_complete_2_setcover"):
        # os.mkdir("out_complete_2_setcover")

    cnt_todo_cover_final = 0

    df = pd.read_csv(f"../xCollectReEval/{JOB_enter_order}.csv", dtype=mydtypes)
    df2 = pd.read_csv(f"{JOB}.csv", dtype=mydtypes)

    covered = 0
    total_sets = 0
    total_combs = 0
    skipped_no_final = 0
    num_sat = 0

    assumption_names = list()
    for set_idx, aSet in enumerate(reachable_sets):
        total_sets += 1
        cover_hb = []
        cover_concur = []

        undet_hb = []
        undet_concur = []

        print("===== SET idx: %d ====" % set_idx)
        print(aSet)

        result_edges = {}
        print("  Getting entering edge results")
        with open("../xCollectReEval/%d_edge_todo_per_set.txt" % set_idx, "r") as f:
            for line in f:
                pair = (line.split(":")[0]).split(",")
                seqs = (line[:-1].split(":")[1]).split(",")
                assert(df is not None)

                for hbtype in seqs:
                    prop = None
                    if hbtype == ">":
                        prop = "cvr_rtl2mupath_CS_{idx}_{e0}_hb_{e1}".format(idx=set_idx, e0=pair[0], e1=pair[1])
                        res, bnd, time = df_query(df, prop, exact_name=True)
                        if res == "covered":
                            covered += 1 
                            cover_hb.append([pair[0], pair[1]])
                            if ((pair[0], pair[1]) in result_edges):
                                result_edges[(pair[0], pair[1])].append(">")
                            else:
                                result_edges[(pair[0], pair[1])] = [">"]
                        elif res == "undetermined":
                            undet_hb.append([pair[0], pair[1]])
                    if hbtype == "<":
                        prop = "cvr_rtl2mupath_CS_{idx}_{e0}_hb_{e1}".format(idx=set_idx, e0=pair[1], e1=pair[0])
                        res, bnd, time = df_query(df, prop, exact_name=True)
                        if res == "covered":
                            covered += 1
                            cover_hb.append([pair[1], pair[0]])
                            if ((pair[0], pair[1]) in result_edges):
                                result_edges[(pair[0], pair[1])].append("<")
                            else:
                                result_edges[(pair[0], pair[1])] = ["<"]
                        elif res == "undetermined":
                            undet_hb.append([pair[0], pair[1]])
                    if hbtype == "=":
                        prop = "cvr_rtl2mupath_CS_{idx}_{e0}_concur_{e1}".format(idx=set_idx, e0=pair[1], e1=pair[0])
                        res, bnd, time = df_query(df, prop, exact_name=True)
                        if res == "covered":
                            covered += 1
                            cover_concur.append([pair[0], pair[1]])
                            if ((pair[0], pair[1]) in result_edges):
                                result_edges[(pair[0], pair[1])].append("=")
                            else:
                                result_edges[(pair[0], pair[1])] = ["="]
                        elif res == "undetermined":
                            undet_concur.append([pair[0], pair[1]])
        print("    hb ", cover_hb)
        print("    concur ", cover_concur)
        #print("undeter_hb ", undet_hb)
        #print("undeter_concur ", undet_concur)
        var_cnt = 1
        sets_edges = []
        for k, v in result_edges.items():
            var_cnt *= len(v)
            sets_edges.append([(k, v_i) for v_i in v])

        comb_edges = list(itertools.product(*sets_edges))
        print(f"    Combinations of entering edges: {len(comb_edges)}")
        # print(f"    combinations of entering edges: {comb_edges}")

        with open("%d_combination.txt" % set_idx, "w") as f:
            for itm in comb_edges:
                for e in itm:
                    f.write("%s,%s,%s," % (e[0][0], e[0][1], e[1]))
                f.write("\n") 

        for combidx, cv_edge_comb in enumerate(comb_edges):
            print(f"  Considering combination of entering edge {set_idx}, comb {combidx}")

            total_combs += 1
            DG = nx.DiGraph()

            print("    Adding HB edges")
            for e in hb_edge:
                if e[0] in aSet and e[1] in aSet:
                    DG.add_edge(e[0], e[1])
            concur_in_comb = []
            print("    Adding entering comb edges")
            for e in cv_edge_comb:
                t_ = e[1]
                p = e[0]
                if t_ == '>':
                    DG.add_edge(p[0], p[1])
                if t_ == '<':
                    DG.add_edge(p[1], p[0])
                if t_ == '=':
                    concur_in_comb.append([p[0],p[1]])
                    

            # concurrent tagged through same color 
            color_cnt=4
            node_colors = {}
            for itm in enter_concurrent_pairs:
                a, b = itm 
                if a in aSet and b in aSet:
                    c = None
                    if itm[0] in node_colors:
                        c = node_colors[itm[0]]
                    elif itm[1] in node_colors:
                        c = node_colors[itm[1]]

                    if c is None:
                        c = color_cnt
                        color_cnt += 1
                    
                    node_colors[a] = c
                    node_colors[b] = c


            # same iid leave order same as enter order
            implied_edges_same_iid = []

            edge_weight = {}
            iid_map_tmp = iid_map

            print("    Adding nodes")
            for itm in aSet:
                DG.add_node(itm)

                if "__final" in itm:
                    non_final_itm = itm.replace("__final", "")
                    edge_weight[(non_final_itm, itm)] = \
                        [t for t in range(1, max_cyc_per_pl[non_final_itm])] #max #[int(r)-1 for r in cyc]
                    iid_map_tmp[itm] = iid_map_tmp[non_final_itm]

            print("    Adding edges between first and last visit")
            for itm in aSet:
                if "__final" in itm:
                    # since its same ufsm, if entering e[0] happens-before entering
                    # e[1], leaving e[0] should also happens-before entering e[1]
                    for e in DG.out_edges(non_final_itm):
                        if iid_map_tmp[e[0]] == iid_map_tmp[e[1]]:
                            implied_edges_same_iid.append((itm, e[1]))

                    DG.add_edge(non_final_itm, itm)
                    #print("adding edge between first and last visit: ", (non_final_itm, itm))
            
            # node_colors always concurrent -> constraint on the edge weight 
            for itm in aws_concur_leaving_pairs:
                if itm[0] in DG.nodes() and itm[1] in DG.nodes():
                    c = None
                    if itm[0] in node_colors:
                        c = node_colors[itm[0]]
                    elif itm[1] in node_colors:
                        c = node_colors[itm[1]]

                    if c is None:
                        c = color_cnt
                        color_cnt += 1
                    node_colors[itm[0]] = c
                    node_colors[itm[1]] = c


            print("    Adding implied edges between same iid")
            for e in implied_edges_same_iid:
                DG.add_edge(*e)

            print("    Adding leaving HB proven edges")
            for itm in leaving_hb_proven_res_pairs:

                if itm[0] in DG.nodes() and itm[1] in DG.nodes():
                    DG.add_edge(itm[0], itm[1])
                    #print(f"Adding proven HB edge between: {itm[0]}, {itm[1]}")

            print("    Adding edges resulting from concurrent nodes")
            for e in enter_concurrent_pairs + aws_concur_leaving_pairs + concur_in_comb:
                a, b = e
                if not (a in DG.nodes() and b in DG.nodes()):
                    continue

                in_edges = DG.in_edges(e[0])
                for e_prime in in_edges:
                    assert(e_prime[1] == e[0])
                    DG.add_edge(e_prime[0], e[1])
                    #print(f"Adding edge because {e} are conccurent and {e_prime} are HB: {e_prime[0]}, {e[1]}")
                
                in_edges = DG.in_edges(e[1])
                for e_prime in in_edges:
                    assert(e_prime[1] == e[1])
                    DG.add_edge(e_prime[0], e[0])
                    #print(f"Adding edge because {e} are conccurent and {e_prime} are HB: {e_prime[0]}, {e[0]}")

                out_edges = DG.out_edges(e[0])
                for e_prime in out_edges:
                    assert(e_prime[0] == e[0])
                    DG.add_edge(e[1], e_prime[1])
                    #print(f"Adding edge because {e} are conccurent and {e_prime} are HB: {e[1]}, {e_prime[1]}")

                out_edges = DG.out_edges(e[1])
                for e_prime in out_edges:
                    assert(e_prime[0] == e[1])
                    DG.add_edge(e[0], e_prime[1])
                    #print(f"Adding edge because {e} are conccurent and {e_prime} are HB: {e[0]}, {e_prime[1]}")

            # Check for cycles more thoroughly
            cycles = list(nx.simple_cycles(DG))
            has_cycles = len(cycles) > 0
            
            # Also check if the graph is a DAG using NetworkX's built-in function
            is_dag = nx.is_directed_acyclic_graph(DG)
            
            if has_cycles or not is_dag:
                print("Issue %d, combidx %d cyclic" % (set_idx, combidx))
                print(f"    cv_edge_comb: {cv_edge_comb}")
                print(f"    cycles: {cycles}")
                continue
                
            TR = nx.transitive_reduction(DG)
            TC = nx.transitive_closure(DG, reflexive=False)
            reduce_e = list(TR.edges)

            #print(f"TR: {TR.edges}")
            #print(f"TC: {TC.edges}")
            #print(f"edge_weight: {edge_weight}")
            #print(f"implied_edges_same_iid: {implied_edges_same_iid}")
            #print(f"edge_weight_single: {edge_weight_single}")
            #print(f"concur: {enter_concurrent_pairs + concur_in_comb + aws_concur_leaving_pairs}")
            #print(f"whb_edge: {whb_edge}")


            ################################################################################ 
            # setup solver 
            ################################################################################ 
            edge_weight_single = []
            slv = MySolver(TR, edge_weight, implied_edges_same_iid, iid_map_tmp,
                    edge_weight_single, enter_concurrent_pairs + concur_in_comb +
                    aws_concur_leaving_pairs, whb_edge)
            r = slv.add_constraints()
            if not r:
                print("  Set idx %d, combidx %d not sat" % (set_idx, combidx))
                continue
            num_sat += 1

            ################################################################################ 
            # Get all edges that is not proven 
            ################################################################################ 

            print("    Computing final edges that are not proven")
            pairs_final = {}
            for idx, eorg in enumerate(edge):
                if not (eorg[0] in aSet and eorg[1] in aSet):
                    #print(f"Edge {eorg} not in set")
                    continue
                if (iid_map_tmp[eorg[0]] == iid_map_tmp[eorg[1]]):
                    #print(f"same iid map for edge {eorg}: {iid_map_tmp[eorg[0]]} {iid_map_tmp[eorg[1]]} ")
                    continue
                e_primes = [] 
                if eorg[0] + "__final" in TC.nodes() and eorg[1] in aSet:
                    e_primes.append([eorg[0] + "__final", eorg[1]])
                if eorg[0] in aSet and eorg[1] + "__final" in TC.nodes():
                    e_primes.append([eorg[0], eorg[1] + "__final"])
                if (eorg[1] + "__final" in TC.nodes()) and (eorg[0] + "__final" in TC.nodes()):
                    e_primes.append([eorg[0] + "__final" , eorg[1] + "__final"])
                if len(e_primes) == 0:
                    #print(f"no remaining edges to check: {eorg}")
                    continue
                for e in e_primes:
                    if tuple(e) in TC.edges() or (e[1], e[0]) in TC.edges():
                        #print("set idx %d comb %d already hb %s %s" % (set_idx, combidx, e[0], e[1])) 
                        continue
                    if e in edge_weight_single or (e[1], e[0]) in edge_weight_single:
                        #print("set idx %d comb %d edge weight single %s %s" % (set_idx, combidx, e[0], e[1]))
                        continue
                    if e in enter_concurrent_pairs or [e[1], e[0]] in enter_concurrent_pairs:
                        #print("set idx %d comb %d already concurrent %s %s" % (set_idx, combidx, e[0], e[1])) 
                        continue
                    if slv.check_imp_hb(e):
                        #print("set idx %d %d imp hb %s %s" % (set_idx, combidx, e[0], e[1]))
                        continue

                    can_be_hb = slv.check_hb_possibility(e)
                    if not can_be_hb:
                        #print("set idx %d %d imp can't be hb %s %s" % (set_idx, combidx, e[0], e[1]))
                        continue
                    # if no hb relation between enter nodes we skip...
                    #enter_nodes = [e[0].split("__final")[0], e[1].split("__final")[0]]
                    #if slv.check_hb_possibility(enter_nodes) and slv.check_hb_possibility([enter_nodes[1],enter_nodes[0]]):
                    #    print("???!!! no fixed order in enter node?", e[1], e[0])
                    #    continue

                    if e[0] < e[1]:
                        if (e[0], e[1]) in pairs_final:
                            # e[0] HB e[1]
                            pairs_final[(e[0], e[1])].append(">")
                        else:
                            pairs_final[(e[0], e[1])] = [">", "="]
                    else:
                        if (e[1], e[0]) in pairs_final:
                            pairs_final[(e[1], e[0])].append("<")
                        else:
                            pairs_final[(e[1], e[0])] = ["<", "="]
                           
            cnt_setidx = 0
            print(f"    Pairs final")
            for k, v in pairs_final.items():
                print("      (%s, %s): %s" % (k[0], k[1], ",".join(v)))
                cnt_todo_cover_final += len(v)
                cnt_setidx += len(v)


            
            print("    Issue %d, combidx %d" % (set_idx, combidx))
            # print(f"    {cnt_setidx}")
            
            #pairs_todo_pruned = {}
            #for k, v in pairs_todo.items():
            #    pairs_todo_pruned[k] = v
            #    print("(%s, %s): %s" % (k[0], k[1], ",".join(v)))
            #    cnt_todo_cover_final += len(v)
            #print("========================================")

            with open("%d_%d_final_edge_todo_per_set.txt" % (set_idx, combidx), "w") as f:
                for k, v in pairs_final.items():
                    f.write("%s,%s:%s\n" % (k[0], k[1], ",".join(v)))
                    
            print("    Adding cover properties")
            if cnt_setidx == 0:
                print("      No final edges to cover, only adding cover property for entering edge combination")
            else:
                check_comb = True
                if len(comb_edges) > 1:
                    prop_name = f"cvr_rtl2mupath_set_{set_idx}_comb_{combidx}"
                    res, bnd, time = df_query(df2, prop_name, exact_name=True)
                    if res != "covered":
                        print("      Set/comb is not covered.")
                        check_comb = False
                if check_comb:

                    s = ""
                    ns = ""
                    all = ""
                    for pl in cv_perflocs_with_final:
                        if "__final" not in pl:
                            all += "{prefix}{s1} || ".format(s1=pl, prefix=prefix)
                        if not pl in aSet:
                            # f.write(no_s1_t.format(s1=pl))
                            ns += "{prefix}{s1}_hpn || ".format(s1=pl, prefix=prefix)
                        else:
                            # f.write(hpn_reg_t2.format(s1=pl))
                            s += "{prefix}{s1}_hpn && ".format(s1=pl, prefix=prefix)
                    s += "1'b1 "
                    ns += "1'b0 "
                    all += "1'b0 "
                    set = s + " & !(%s)" % ns + " & !(%s)" % all
                    # f.write("wire set_r = %s;\n" % s)
                    asums = ""
                    for e in cv_edge_comb:
                        t_ = e[1]
                        p = e[0]
                        assert(not("__final" in p[0] or "__final" in p[1]))

                        if t_ == '>':
                            asum = A_enter_hb_enter_expr_only.format(e0=p[0], e1=p[1], prefix=prefix)
                            # f.write(A_enter_hb_enter.format(e0=p[0], e1=p[1]))
                            nm = p[0] + "_HB_" + p[1] + "_contradict_hpn"
                            if nm not in assumption_names:
                                assumption_names.append(nm)
                                h_ += contradict_flag_hpn_reg_nm_t.format(nm=nm, s1=asum)
                            asums += "!" + prefix + nm + " && "
                        if t_ == '<':
                            asum = A_enter_hb_enter_expr_only.format(e0=p[1], e1=p[0], prefix=prefix)
                            # f.write(A_enter_hb_enter.format(e0=p[1], e1=p[0]))
                            nm = p[1] + "_HB_" + p[0] + "_contradict_hpn"
                            if nm not in assumption_names:
                                assumption_names.append(nm)
                                h_ += contradict_flag_hpn_reg_nm_t.format(nm=nm, s1=asum)
                            asums += "!" + prefix + nm + " && "
                        if t_ == '=':
                            asum = A_enter_concur_enter_expr_only.format(e0=p[0], e1=p[1], prefix=prefix)
                            # f.write(A_enter_concur_enter.format(e0=p[0], e1=p[1]))
                            nm = p[0] + "_CONCUR_" + p[1] + "_contradict_hpn"
                            if nm not in assumption_names:
                                assumption_names.append(nm)
                                h_ += contradict_flag_hpn_reg_nm_t.format(nm=nm, s1=asum)
                            asums += "!" + prefix + nm + " && "
                    asums += "1'b1"
                    for k, v in pairs_final.items():
                        for tt in v:
                            if ">" == tt:
                                print(f"      {k[0]} > {k[1]}")
                                if '__final' in k[0] and '__final' in k[1]:
                                    htcl_ += C_final_hb_final_tcl.format(e0nm=k[0], e1nm=k[1], e0=k[0][:-7], e1=k[1][:-7], set=set, asums=asums, prefix=prefix, idx=set_idx, combidx=combidx)
                                elif '__final' in k[0] and (not '__final' in k[1]):
                                    htcl_ += C_final_hb_enter_tcl.format(e0nm=k[0], e1nm=k[1], e0=k[0][:-7], e1=k[1], set=set, asums=asums, prefix=prefix, idx=set_idx, combidx=combidx)
                                elif (not '__final' in k[0]) and '__final' in k[1]:
                                    htcl_ += C_enter_hb_final_tcl.format(e0nm=k[0], e1nm=k[1], e0=k[0], e1=k[1][:-7], set=set, asums=asums, prefix=prefix, idx=set_idx, combidx=combidx)
                                else:
                                    assert(0)

                            elif "<" == tt:
                                print(f"      {k[0]} < {k[1]}")
                                if '__final' in k[1] and '__final' in k[0]:
                                    htcl_ += C_final_hb_final_tcl.format(e0nm=k[1], e1nm=k[0], e0=k[1][:-7], e1=k[0][:-7], set=set, asums=asums, prefix=prefix, idx=set_idx, combidx=combidx)
                                elif '__final' in k[1] and (not '__final' in k[0]):
                                    htcl_ += C_final_hb_enter_tcl.format(e0nm=k[1], e1nm=k[0], e0=k[1][:-7], e1=k[0], set=set, asums=asums, prefix=prefix, idx=set_idx, combidx=combidx)
                                elif (not '__final' in k[1]) and '__final' in k[0]:
                                    htcl_ += C_enter_hb_final_tcl.format(e0nm=k[1], e1nm=k[0], e0=k[1], e1=k[0][:-7], set=set, asums=asums, prefix=prefix, idx=set_idx, combidx=combidx)
                                else:
                                    assert(0)
                            else:
                                print(f"      {k[0]} = {k[1]}")
                                if '__final' in k[0] and '__final' in k[1]:
                                    htcl_ += C_final_concur_final_tcl.format(e0nm=k[0], e1nm=k[1], e0=k[0][:-7], e1=k[1][:-7], set=set, asums=asums, prefix=prefix, idx=set_idx, combidx=combidx)
                                elif '__final' in k[0] and (not '__final' in k[1]):                                      
                                    htcl_ += C_final_concur_enter_tcl.format(e0nm=k[0], e1nm=k[1], e0=k[0][:-7], e1=k[1], set=set, asums=asums, prefix=prefix, idx=set_idx, combidx=combidx)
                                elif (not '__final' in k[0]) and '__final' in k[1]:                                      
                                    htcl_ += C_enter_concur_final_tcl.format(e0nm=k[0], e1nm=k[1], e0=k[0], e1=k[1][:-7], set=set, asums=asums, prefix=prefix, idx=set_idx, combidx=combidx)
                                else:
                                    assert(0)
            print("========================================")

    with open (f"{JOB2}.tcl", "w") as f:
        f.write(htcl_)
        f.write("set props [get_property_list -include {name cvr_rtl2mupath_*}]\n")
        f.write("prove -property $props\n")
        f.write("report -property $props -csv -results -file %s.csv -force\n" % JOB2)
        f.write("save %s.db -force\n" % JOB2)
        f.write("file copy %s.csv %s/.\n" % (JOB2, os.getcwd()))
        f.write("exit\n")
    with open (f"{JOB2}.sv", "w") as f:
        f.write(h_)
        f.write(e_)

    #print("cnt todo:", cnt_todo_cover)
    print("cnt_todo_cover_final", cnt_todo_cover_final)
    print(f"total sets: {total_sets}")


if len(sys.argv) < 2:
    print("gen/pp/stats")
    exit(0)

opt = sys.argv[1]
if opt == "gen":
    gen()
if opt == "gen_s2":
    gen_s2()
elif opt == "pp":
    pp()
elif opt == "stats":
    stats()
        
