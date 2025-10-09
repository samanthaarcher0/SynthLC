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
h_ = "".join(lines[:-5])
e_ = "".join(lines[-5:])


HEADERTCL='../header.tcl'
htcl_ = ""
with open(HEADERTCL, "r") as f:
    for line in f:
        htcl_ += line

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
# edge = get_array("../../xGenPerfLocDfgDiv/dfg_e.txt")
edge = get_array("../xCoverCandidateHBEdges/covered_edges.txt")

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
    
#print("TODO: for pair of nodes after transitive reduction we shoudl check if \
#its possible to have two happen concurrently if not we should see if per PL set \
#is always one way or the other")

enter_concurrent_pairs = get_array("../xHBPerfG_dfg_v3_div/aws_concurrent.txt", exit_on_fail=False)
# print(type(enter_concurrent_pairs[0]))
whb_edge = get_array("../xHBPerfG_dfg_v3_div/whb_proven.txt", exit_on_fail=False)
hb_edge = get_array("../xHBPerfG_dfg_v3_div/hb_proven.txt", exit_on_fail=False)
print("HB edge:", hb_edge)
reachable_sets = get_array("../xPerfLocCycleCount/new_reachable_sets.txt", arr_as_ele = True)

max_cyc_per_pl_raw = get_array("../xPerfLocCycleCount/max_cycle_per_pl.txt")

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


cv_perflocs_with_final = list()
for itm in cv_perflocs:
    h_ += hpn_reg_t2.format(s1=itm)
    h_ += prev_hpn_reg_t.format(s1=itm)
    h_ += pl_repeated_hpn_reg_nm_t.format(s1=itm, nm=itm+"__final")
    cv_perflocs_with_final.append(itm)

for PL, cnt in max_cyc_per_pl.items():
    if cnt > 1:
        cv_perflocs_with_final.append(PL+"__final")



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



JOB_enter_order = "rtl2mupath_enter_order"
JOB_enter_order_combo = "rtl2mupath_leave_order"
JOB_leave_order = "rtl2mupath_leave_order"
JOB = "rtl2mupath_construct_paths_final"

intra_single_cyc = {}


node_rows = {}
label_s = ""
row = 0
for _, v in enumerate(list_rows):
    node_rows[v] = row
    label_s += label.format(nm=v,loc=row)
    row += 1
    if v in max_cyc_per_pl and max_cyc_per_pl[v] > 1:
    #if v in over1cyc_pl:
        label_s += label.format(nm = v + "__final", loc=row)
        node_rows[v + "__final"] = row
        row += 1

path_cnt = 0

def gen():
    global h_
    global htcl_
    cnt_todo_cover_final = 0

    df_enter_order = pd.read_csv(f"../xCollectReEval/{JOB_enter_order}.csv", dtype=mydtypes)
    df_enter_comb = pd.read_csv(f"../xCollectReEvalLeaveOrder/{JOB_enter_order_combo}.csv", dtype=mydtypes)
    df_leave_order = pd.read_csv(f"../xCollectReEvalLeaveOrder/{JOB_leave_order}.csv", dtype=mydtypes)
    
    assumption_names = list()

    for set_idx, aSet in enumerate(reachable_sets):

        cover_hb = []
        cover_concur = []

        undet_hb = []
        undet_concur = []

        print("===== SET idx: %d ====" % set_idx)

        result_edges = {}
        print("  Getting entering edge results")
        with open("../xCollectReEval/%d_edge_todo_per_set.txt" % set_idx, "r") as f:
            df = None
            for line in f:
                #f.write("%s,%s:%s\n" % (k[0], k[1], ",".join(v)))
                pair = (line.split(":")[0]).split(",")
                seqs = (line[:-1].split(":")[1]).split(",")

                for hbtype in seqs:
                    prop = None
                    if hbtype == ">":
                        prop = "cvr_rtl2mupath_CS_{idx}_{e0}_hb_{e1}".format(idx=set_idx, e0=pair[0], e1=pair[1])
                        res, bnd, time = df_query(df_enter_order, prop, exact_name=True)
                        if res == "covered":
                            cover_hb.append([pair[0], pair[1]])
                            if ((pair[0], pair[1]) in result_edges):
                                result_edges[(pair[0], pair[1])].append(">")
                            else:
                                result_edges[(pair[0], pair[1])] = [">"]
                        elif res == "undetermined":
                            undet_hb.append([pair[0], pair[1]])
                    if hbtype == "<":
                        prop = "cvr_rtl2mupath_CS_{idx}_{e0}_hb_{e1}".format(idx=set_idx, e0=pair[1], e1=pair[0])
                        res, bnd, time = df_query(df_enter_order, prop, exact_name=True)
                        if res == "covered":
                            cover_hb.append([pair[1], pair[0]])
                            if ((pair[0], pair[1]) in result_edges):
                                result_edges[(pair[0], pair[1])].append("<")
                            else:
                                result_edges[(pair[0], pair[1])] = ["<"]
                        elif res == "undetermined":
                            undet_hb.append([pair[0], pair[1]])
                    if hbtype == "=":
                        prop = "cvr_rtl2mupath_CS_{idx}_{e0}_concur_{e1}".format(idx=set_idx, e0=pair[1], e1=pair[0])
                        res, bnd, time = df_query(df_enter_order, prop, exact_name=True)
                        if res == "covered":
                            cover_concur.append([pair[0], pair[1]])
                            if ((pair[0], pair[1]) in result_edges):
                                result_edges[(pair[0], pair[1])].append("=")
                            else:
                                result_edges[(pair[0], pair[1])] = ["="]
                        elif res == "undetermined":
                            undet_concur.append([pair[0], pair[1]])
        print("hb ", cover_hb)
        print("concur ", cover_concur)
        #print("undeter_hb ", undet_hb)
        #print("undeter_concur ", undet_concur)
        var_cnt = 1
        sets_edges = []
        for k, v in result_edges.items():
            var_cnt *= len(v)
            sets_edges.append([(k, v_i) for v_i in v])
            #print(k, v)

        # print("var cnt ", var_cnt)
        comb_edges = list(itertools.product(*sets_edges))
        print(f"    Combinations of entering edges: {len(comb_edges)}")
        #print(comb_edges)
        #continue

        cover_hb = []
        cover_concur = []
        undet_hb = []
        undet_concur = []

        for combidx, cv_edge_comb in enumerate(comb_edges):
            #if combidx != 15:
            #    continue
            result_edges_final = {}

            undetermined_comb_entering = False

            cnt_todo = 0
            if not os.path.exists("../xCollectReEvalLeaveOrder/%d_%d_final_edge_todo_per_set.txt" % (set_idx, combidx)):
                print("set %d combidx %d cyclic" % (set_idx, combidx))
                continue

            with open("../xCollectReEvalLeaveOrder/%d_%d_final_edge_todo_per_set.txt" % (set_idx, combidx), "r") as f:
                for line in f:
                    cnt_todo += 1
            if cnt_todo == 0:
                print("!! setidx %d %d has fix set of order on final nodes" % (set_idx, combidx))
                print("TODO: res on set_r")
                #res, bnd, time = df_query(df, "set_r", exact_name=True)
                # check
                # continue
            print("set idx %d combidx %d" % (set_idx, combidx))
            prop_set_comb0 = f"cvr_rtl2mupath_set_{set_idx}_comb_{combidx}"
            # res, bnd, time = df_query(df_enter_comb, prop_set_comb0, exact_name=True)
            res, bnd, time = df_query_return_on_no_exist(df_enter_comb, prop_set_comb0, exact_name=True)
            if res == None:
                print("  Didn't find set combo prop")
                res = "covered"
                # continue

            print("set_r is covered? ", res)
            if not res == "covered":
                print("set/comb idx %d %d is not covered? " % (set_idx, combidx))
                continue
            with open("../xCollectReEvalLeaveOrder/%d_%d_final_edge_todo_per_set.txt" % (set_idx, combidx), "r") as f:
                df = None
                for line in f:
                    pair = (line.split(":")[0]).split(",")
                    seqs = (line[:-1].split(":")[1]).split(",")

                    for hbtype in seqs:
                        prop = None
                        if hbtype == ">":
                            prop = "cvr_rtl2mupath_CS_set{idx}_comb{combidx}_{e0}_hb_{e1}".format(idx=set_idx, combidx=combidx, e0=pair[0], e1=pair[1])
                            res, bnd, time = df_query_return_on_no_exist(df_leave_order, prop, exact_name=True)
                            if res == "covered":
                                cover_hb.append([pair[0], pair[1]])
                                if ((pair[0], pair[1]) in result_edges_final):
                                    result_edges_final[(pair[0], pair[1])].append(">")
                                else:
                                    result_edges_final[(pair[0], pair[1])] = [">"]
                            elif res == "undetermined":
                                undet_hb.append([pair[0], pair[1]])
                        if hbtype == "<":
                            prop = "cvr_rtl2mupath_CS_set{idx}_comb{combidx}_{e0}_hb_{e1}".format(idx=set_idx, combidx=combidx, e0=pair[1], e1=pair[0])
                            res, bnd, time = df_query_return_on_no_exist(df_leave_order, prop, exact_name=True)
                            if res == "covered":
                                cover_hb.append([pair[1], pair[0]])
                                if ((pair[0], pair[1]) in result_edges_final):
                                    result_edges_final[(pair[0], pair[1])].append("<")
                                else:
                                    result_edges_final[(pair[0], pair[1])] = ["<"]
                            elif res == "undetermined":
                                undet_hb.append([pair[0], pair[1]])
                        if hbtype == "=":
                            prop = "cvr_rtl2mupath_CS_set{idx}_comb{combidx}_{e0}_concur_{e1}".format(idx=set_idx, combidx=combidx, e0=pair[0], e1=pair[1])
                            res, bnd, time = df_query_return_on_no_exist(df_leave_order, prop, exact_name=True)                            
                            if res == "covered":
                                cover_concur.append([pair[0], pair[1]])
                                if ((pair[0], pair[1]) in result_edges_final):
                                    result_edges_final[(pair[0], pair[1])].append("=")
                                else:
                                    result_edges_final[(pair[0], pair[1])] = ["="]
                            elif res == "undetermined":
                                undet_concur.append([pair[0], pair[1]])

            var_cnt_final = 1
            sets_edges_final = []
            for k, v in result_edges_final.items():
                # assert(len(v) == len(set(v)))
                var_cnt_final *= len(v)
                sets_edges_final.append([(k, v_i) for v_i in v])
                print(k, v)

            print("var cnt final ", var_cnt_final)
            comb_edges_final = list(itertools.product(*sets_edges_final))
            print(len(comb_edges_final))
            noncyc=0
            for combidx_final, cv_edge_comb_final in enumerate(comb_edges_final):
                print("particular orders", len(cv_edge_comb_final), len(cv_edge_comb))
                print("particular orders", cv_edge_comb_final, cv_edge_comb)
                DG = nx.DiGraph()

                for e in hb_edge:
                    if e[0] in aSet and e[1] in aSet:
                        DG.add_edge(e[0], e[1])
                concur_in_comb = []
                for e in cv_edge_comb:
                    t_ = e[1]
                    p = e[0]
                    if t_ == '>':
                        DG.add_edge(p[0], p[1])
                    if t_ == '<':
                        DG.add_edge(p[1], p[0])
                    if t_ == '=':
                        concur_in_comb.append([p[0],p[1]])
                for e in cv_edge_comb_final:
                    t_ = e[1]
                    p = e[0]
                    if t_ == '>':
                        DG.add_edge(p[0], p[1])
                    if t_ == '<':
                        DG.add_edge(p[1], p[0])
                    if t_ == '=':
                        concur_in_comb.append([p[0],p[1]])
                        
                print("concur_in_comb", concur_in_comb) 
                # concurrent tagged through same color 
                color_cnt=4
                node_colors = {}

                # same iid leave order same as enter order
                implied_edges_same_iid = []

                edge_weight = {}
                iid_map_tmp = iid_map
                
                # SAMANTHA TO FIX ABOVE
                print("    Adding nodes")
                for itm in aSet:
                    DG.add_node(itm)

                    if "__final" in itm:
                        non_final_itm = itm.replace("__final", "")
                        edge_weight[(non_final_itm, itm)] = \
                            [t for t in range(1, max_cyc_per_pl[non_final_itm])] #max #[int(r)-1 for r in cyc]
                        iid_map_tmp[itm] = iid_map_tmp[non_final_itm]

                print("    Adding edges between first and last visit")
                whb_finals = []
                for itm in aSet:
                    if "__final" in itm:
                        # since its same ufsm, if entering e[0] happens-before entering
                        # e[1], leaving e[0] should also happens-before entering e[1]
                        for e in DG.out_edges(non_final_itm):
                            if iid_map_tmp[e[0]] == iid_map_tmp[e[1]]:
                                implied_edges_same_iid.append((itm, e[1]))
                        whb_finals.append((non_final_itm, itm))
                        DG.add_edge(non_final_itm, itm)
                        #print("adding edge between first and last visit: ", (non_final_itm, itm))
                # END SAMANTHA TO FIX
                
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



                # heuristic
                edge_weight_single = []
                #if intra_single_cyc.get(set_idx) is not None:
                #    for e in intra_single_cyc[set_idx]:
                #        # only use for source not longer than 1 cycle: (otherwise if its
                #        # staying longer than 1 cycle it will implies many more things  more correlation..)
                #        if not e[0] + "__final" in iid_map_tmp:
                #            print("heuristic", set_idx, e)
                #            edge_weight_single.append(e)
                #            DG.add_edge(e[0], e[1])
                #else:
                #    print("intra_single_cyc don't have key ", set_idx)



                #print(hb_edge)
                for e in implied_edges_same_iid:
                    DG.add_edge(*e)

                for itm in leaving_hb_proven_res_pairs:
                    if itm[0] in DG.nodes() and itm[1] in DG.nodes():
                        DG.add_edge(itm[0], itm[1])

                #for itm in aws_concur_leaving_pairs:
                #    if itm[0] in DG.nodes() and itm[1] in DG.nodes():

                for e in enter_concurrent_pairs + aws_concur_leaving_pairs + concur_in_comb:
                    a, b = e
                    if not (a in DG.nodes() and b in DG.nodes()):
                        continue

                    in_edges = DG.in_edges(e[0])
                    for e_prime in in_edges:
                        assert(e_prime[1] == e[0])
                        #if e_prime[0] != e[1]:
                        if True:
                            DG.add_edge(e_prime[0], e[1])

                    in_edges = DG.in_edges(e[1])
                    for e_prime in in_edges:
                        assert(e_prime[1] == e[1])
                        #if e_prime[0] != e[0]:
                        if True:
                            DG.add_edge(e_prime[0], e[0])

                    out_edges = DG.out_edges(e[0])
                    for e_prime in out_edges:
                        assert(e_prime[0] == e[0])
                        #if e[1] != e_prime[1]:
                        if True:
                            DG.add_edge(e[1], e_prime[1])

                    out_edges = DG.out_edges(e[1])
                    for e_prime in out_edges:
                        assert(e_prime[0] == e[1])
                        #if e[0] != e_prime[1]:
                        if True:

                            DG.add_edge(e[0], e_prime[1])

                if len(list(nx.simple_cycles(DG))) > 0:
                    print("Issue %d, combidx %d %d cyclic" % (set_idx, combidx, combidx_final))
                    #print(list(nx.simple_cycles(DG)))
                    #assert(0)
                    continue

                TR = nx.transitive_reduction(DG) #, reflexive=False)
                TC = nx.transitive_closure(DG, reflexive=False)
                reduce_e = list(TR.edges)

                ################################################################################ 
                # setup solver 
                ################################################################################ 
                slv = MySolver(TR, edge_weight, implied_edges_same_iid, iid_map_tmp,
                        edge_weight_single, enter_concurrent_pairs + concur_in_comb +
                        aws_concur_leaving_pairs, whb_edge, whb_finals)
                slv.add_constraints(debug=(set_idx == 64))
                res = slv.add_constraints()
                if res == False:
                    print(list(TR.edges()))
                    print("Issue %d, combidx %d cyclic (sat)" % (set_idx, combidx))
                    continue

                noncyc += 1
                cnt_todo_cover_final += 1
                # with open("out_complete_3/com_%d_%d_%d.sv" % (set_idx, combidx, combidx_final), "w") as f:
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

                for e in cv_edge_comb_final:
                    t_ = e[1]
                    p = e[0]
                    # k = e[0]

                    if t_ == '>':
                        if '__final' in p[0] and '__final' in p[1]:
                            # f.write(A_final_hb_final.format(e0nm=k[0], e1nm=k[1], e0=k[0][:-8], e1=k[1][:-8]))
                            asum = A_final_hb_final_expr_only.format(e0=p[0].replace("__final",""), e1=p[1].replace("__final",""), prefix=prefix)
                            nm = p[0] + "_HB_" + p[1] + "_contradict_hpn"
                            if nm not in assumption_names:
                                assumption_names.append(nm)
                                h_ += contradict_flag_hpn_reg_nm_t.format(nm=nm, s1=asum)
                            asums += "!" + prefix + nm + " && "
                        elif '__final' in p[0] and (not '__final' in p[1]):
                            # f.write(A_final_hb_enter.format(e0nm=k[0], e1nm=k[1], e0=k[0][:-8], e1=k[1]))
                            asum = A_final_hb_enter_expr_only.format(e0=p[0].replace("__final",""), e1=p[1], prefix=prefix)
                            nm = p[1] + "_HB_" + p[0] + "_contradict_hpn"
                            if nm not in assumption_names:
                                assumption_names.append(nm)
                                h_ += contradict_flag_hpn_reg_nm_t.format(nm=nm, s1=asum)
                            asums += "!" + prefix + nm + " && "
                        elif (not '__final' in p[0]) and '__final' in p[1]:
                            # f.write(A_enter_hb_final.format(e0nm=k[0], e1nm=k[1], e0=k[0], e1=k[1][:-8]))
                            asum = A_enter_hb_final_expr_only.format(e0=p[0], e1=p[1].replace("__final",""), prefix=prefix)
                            nm = p[1] + "_HB_" + p[0] + "_contradict_hpn"
                            if nm not in assumption_names:
                                assumption_names.append(nm)
                                h_ += contradict_flag_hpn_reg_nm_t.format(nm=nm, s1=asum)
                            asums += "!" + prefix + nm + " && "
                        else:
                            assert(0)
                    if t_ == '<':
                        if '__final' in p[1] and '__final' in p[0]:
                            # f.write(A_final_hb_final.format(e0nm=k[1], e1nm=k[0], e0=k[1][:-8], e1=k[0][:-8]))
                            asum = A_final_hb_final_expr_only.format(e0=p[1].replace("__final",""), e1=p[0].replace("__final",""), prefix=prefix)
                            nm = p[0] + "_HB_" + p[1] + "_contradict_hpn"
                            if nm not in assumption_names:
                                assumption_names.append(nm)
                                h_ += contradict_flag_hpn_reg_nm_t.format(nm=nm, s1=asum)
                            asums += "!" + prefix + nm + " && "
                        elif '__final' in p[1] and (not '__final' in p[0]):
                            # f.write(A_final_hb_enter.format(e0nm=k[1], e1nm=k[0], e0=k[1][:-8], e1=k[0]))
                            asum = A_final_hb_enter_expr_only.format(e0=p[1].replace("__final",""), e1=p[0], prefix=prefix)
                            nm = p[1] + "_HB_" + p[0] + "_contradict_hpn"
                            if nm not in assumption_names:
                                assumption_names.append(nm)
                                h_ += contradict_flag_hpn_reg_nm_t.format(nm=nm, s1=asum)
                            asums += "!" + prefix + nm + " && "
                        elif (not '__final' in p[1]) and '__final' in p[0]:
                            # f.write(A_enter_hb_final.format(e0nm=k[1], e1nm=k[0], e0=k[1], e1=k[0][:-8]))
                            asum = A_enter_hb_final_expr_only.format(e0=p[1], e1=p[0].replace("__final",""), prefix=prefix)
                            nm = p[1] + "_HB_" + p[0] + "_contradict_hpn"
                            if nm not in assumption_names:
                                assumption_names.append(nm)
                                h_ += contradict_flag_hpn_reg_nm_t.format(nm=nm, s1=asum)
                            asums += "!" + prefix + nm + " && "
                        else:
                            assert(0)
                    if t_ == '=':
                        #f.write(A_enter_concur_enter.format(e0=p[0], e1=p[1]))
                        if '__final' in p[0] and '__final' in p[1]:
                            # f.write(A_final_concur_final.format(e0nm=k[0], e1nm=k[1], e0=k[0][:-8], e1=k[1][:-8]))
                            asum = A_final_concur_final_expr_only.format(e0=p[0].replace("__final",""), e1=p[1].replace("__final",""), prefix=prefix)
                            nm = p[0] + "_HB_" + p[1] + "_contradict_hpn"
                            if nm not in assumption_names:
                                assumption_names.append(nm)
                                h_ += contradict_flag_hpn_reg_nm_t.format(nm=nm, s1=asum)
                            asums += "!" + prefix + nm + " && "
                        elif '__final' in p[0] and (not '__final' in p[1]):                                      
                            # f.write(A_final_concur_enter.format(e0nm=k[0], e1nm=k[1], e0=k[0][:-8], e1=k[1]))
                            asum = A_final_concur_enter_expr_only.format(e0=p[0].replace("__final",""), e1=p[1], prefix=prefix)
                            nm = p[1] + "_HB_" + p[0] + "_contradict_hpn"
                            if nm not in assumption_names:
                                assumption_names.append(nm)
                                h_ += contradict_flag_hpn_reg_nm_t.format(nm=nm, s1=asum)
                            asums += "!" + prefix + nm + " && "
                        elif (not '__final' in p[0]) and '__final' in p[1]:                                      
                            # f.write(A_enter_concur_final.format(e0nm=k[0], e1nm=k[1], e0=k[0], e1=k[1][:-8]))
                            asum = A_enter_concur_final_expr_only.format(e0=p[0], e1=p[1].replace("__final",""), prefix=prefix)
                            nm = p[1] + "_HB_" + p[0] + "_contradict_hpn"
                            if nm not in assumption_names:
                                assumption_names.append(nm)
                                h_ += contradict_flag_hpn_reg_nm_t.format(nm=nm, s1=asum)
                            asums += "!" + prefix + nm + " && "
                        else:
                            assert(0)
    
                asums += "1'b1"
                htcl_ += f"cover -name cvr_rtl2mupath_set_{set_idx}_comb_{combidx}_combfinal_{combidx_final} {{(@(posedge {prefix}fv_clk) {set} && {asums})}};\n\n"
                print("set idx ", set_idx, "combidx", combidx, "combidx_final", combidx_final, " noncyc", noncyc)

        print("========================================")

    with open (f"{JOB}.tcl", "w") as f:
        f.write(htcl_)
        f.write("set props [get_property_list -include {name cvr_rtl2mupath_*}]\n")
        f.write("prove -property $props\n")
        f.write("report -property $props -csv -results -file %s.csv -force\n" % JOB)
        f.write("save %s.db -force\n" % JOB)
        f.write("file copy %s.csv %s/.\n" % (JOB, os.getcwd()))
        f.write("#exit\n")
    with open (f"{JOB}.sv", "w") as f:
        f.write(h_)
        f.write(e_)

    #print("cnt todo:", cnt_todo_cover)
    print("cnt_todo_cover_final", cnt_todo_cover_final)
    # print(f"COVERED: {covered}")
    # print(f"Skipped no final: {skipped_no_final}")
    # print(f"total sets: {total_sets}")
    # print(f"total combs: {total_combs}")
    # print(f"num sat: {num_sat}")



if len(sys.argv) < 2:
    print("gen/pp/stats")
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
        
