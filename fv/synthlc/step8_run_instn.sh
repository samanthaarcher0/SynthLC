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
# STEP 8
######### 
cd $INAME
INAME_DIR=$(realpath .)

echo "
================================================================================
STEP 8 at $(pwd) $(date)
================================================================================
"

# 1. ...
# 2. ...
DIR=xCollectReEvalLeaveOrder
PYSCRPT=aggregate_cyccnt_comp
if [ -d "${DIR}" ]; then 
    echo "Directory exists ${DIR} and skip"
else 
    cp -r ../${DIR} .

   
    JOB=rtl2mupath_leave_order
    TCLFILE=$(realpath ${DIR})/${JOB}.tcl
    SVFILE=$(realpath ${DIR})/${JOB}.sv

    cd ${DIR}; 
    python3 ${PYSCRPT}.py gen; 

    # Run Jasper to get all combinations of leaving order given entering orders
    cd ../../..
    ./run.sh ${FV_UNITDIR} ${TCLFILE} ${SVFILE}

fi

# at $INAME
cd ${INAME_DIR}/${DIR}; 
