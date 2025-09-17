#!/usr/bin/bash
# non-interference case
# heuristic only handle undetermined cases line 435
set -e 
set -o pipefail

PWD=$(pwd)
PWD_PREFIX=$(basename ${PWD})
# assumption/opcdoe for the instn
INSTNDIR=opcodes_gen_all
# run over all
INSTN_FILES=$(ls $INSTNDIR)
fnm=DIV.sv
if [ -z $1 ];
then
    echo "Pass an argument such as as \`./run_an_instn_demo.sh LW.sv\`"
    exit
else
    echo "===> Processing: $1"
    fnm="$1"
fi


filename=$(basename $fnm)
fileprefix="${filename%.*}"

INAME="i_${fileprefix}_out" 
echo "${fnm}"

echo "Working on $INAME"

INSTN="$INSTNDIR/$fnm"
echo "=========== INSTN ============="
echo "- Directory: $INAME"
echo "- Instruction file: $INSTN"
cat $INSTN
echo "==============================="


echo ${PWD}
echo ${PWD_PREFIX}


# Shared by all instructions 
if [ ! -f "xGenPerfLocDfgDiv/dfg_e.txt" ]; then
    exit
fi 
echo "========== DFG E prepared ========== "


FV_UNITDIR=$(realpath ../../..)



######### 
# STEP 10
######### 
cd $INAME
INAME_DIR=$(realpath .)

echo "
================================================================================
STEP 10 at $(pwd) $(date)
================================================================================
"

# 1. Given all full paths found in last step, determine all decision points
DIR=xSummarize
PYSCRPT1=aggregate_cyccnt_stats_iso
PYSCRPT2=aggregate_cyccnt_stats_iso_follower_set_decision_regen_v2

if [ -d "${DIR}" ]; then 
    echo "Directory exists ${DIR} and skip"
else 
    cp -r ../${DIR} .
    cd ${DIR}
    #python3 ${PYSCRPT1}.py gen > stats_iso_trial5.log
    python3 ${PYSCRPT2}.py gen > run.log
    cd ..
fi

