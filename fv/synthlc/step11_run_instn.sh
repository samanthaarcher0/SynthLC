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
# STEP 11
######### 
cd $INAME
INAME_DIR=$(realpath .)

echo "
================================================================================
STEP 11 at $(pwd) $(date)
================================================================================
"

# 1. ...
# 2. ...
DIR=xFollowerSetsOnly
PYSCRPT=xFollowerSetsOnly
confirmed="y"
if [ -d "${DIR}" ]; then
    echo "Directory exists $INAME. Redo step? [y/n]"
    read confirmed
fi
if [ $confirmed == "y" ]; then
    cp -r ../${DIR} .

   
    JOB1=rtl2mupath_followers
    JOB2=rtl2mupath_first_pls
    JOB3=rtl2mupath_first_pl_sets
    TCLFILE1=$(realpath ${DIR})/${JOB1}.tcl
    SVFILE1=$(realpath ${DIR})/${JOB1}.sv
    TCLFILE2=$(realpath ${DIR})/${JOB2}.tcl
    SVFILE2=$(realpath ${DIR})/${JOB2}.sv
    TCLFILE3=$(realpath ${DIR})/${JOB3}.tcl
    SVFILE3=$(realpath ${DIR})/${JOB3}.sv

    cd ${INAME_DIR}/${DIR};
    python3 ${PYSCRPT}.py gen; 

    cd ../../..
    #./run.sh ${FV_UNITDIR} ${TCLFILE1} ${SVFILE1}
    ./RUN_JG.sh -j ${INAME_DIR}/${DIR} -s ${SVFILE1} -t ${TCLFILE1} -g 1
    cd ${INAME_DIR}/${DIR};
    python3 ${PYSCRPT}.py gen_s2; 

    cd ../../..
    #./run.sh ${FV_UNITDIR} ${TCLFILE2} ${SVFILE2}
    ./RUN_JG.sh -j ${INAME_DIR}/${DIR} -s ${SVFILE2} -t ${TCLFILE2} -g 1

    cd ${INAME_DIR}/${DIR};
    python3 ${PYSCRPT}.py gen_s3; 

    cd ../../..
    #./run.sh ${FV_UNITDIR} ${TCLFILE3} ${SVFILE3}
    ./RUN_JG.sh -j ${INAME_DIR}/${DIR} -s ${SVFILE3} -t ${TCLFILE3} -g 1

    cd ${INAME_DIR}/${DIR};
    python3 ${PYSCRPT}.py pp

fi

