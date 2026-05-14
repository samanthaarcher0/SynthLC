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
# STEP 5
######### 
cd $INAME
INAME_DIR=$(realpath .)

echo "
================================================================================
STEP 5 at $(pwd) $(date)
================================================================================
"

# 1. For each reachable PL set, get revisit information for each PL for 
# 2. For each IUV PLs, is it re-visitable and what is max cycle that it is
# revisited 
DIR=xPerfLocCycleCount
PYSCRPT=xPerfLocCycleCountAllSet
confirmed="y"
if [ -d "${DIR}" ]; then
    echo "Directory exists $INAME. Redo step? [y/n]"
    read confirmed
fi
if [ $confirmed == "y" ]; then
    cp -r ../${DIR} .
    
    JOB1=rtl2mupath_pl_revisit_possible
    JOB2=rtl2mupath_pl_subset_revisit_possible
    JOB3=rtl2mupath_pl_subset_combination_check
    TCLFILE1=$(realpath ${DIR})/${JOB1}.tcl
    SVFILE1=$(realpath ${DIR})/${JOB1}.sv
    TCLFILE2=$(realpath ${DIR})/${JOB2}.tcl
    SVFILE2=$(realpath ${DIR})/${JOB2}.sv
    TCLFILE3=$(realpath ${DIR})/${JOB3}.tcl
    SVFILE3=$(realpath ${DIR})/${JOB3}.sv


    # Generate properties to check for repeated PLs
    cd ${DIR}; 
    python3 ${PYSCRPT}.py gen;

    # Run Jasper to determine which PLs can be repeated in any subset
    cd ../../..
    #./run.sh ${FV_UNITDIR} ${TCLFILE1} ${SVFILE1}
    ./RUN_JG.sh -j ${INAME_DIR}/${DIR} -s ${SVFILE1} -t ${TCLFILE1} -g 1

    # Generate properties to check for whether a PL can be repeated in a particular subset
    #cd ${INAME_DIR}/${DIR};
    #python3 ${PYSCRPT}.py gen_s2;
     
    # Run Jasper to determine if a PL can be repeated within a particular subset
    #cd ../../..
    #./run.sh ${FV_UNITDIR} ${TCLFILE2} ${SVFILE2}


    # Generate properties to check for whether combinations of PLs are revisited/not revisited in a subset
    #cd ${INAME_DIR}/${DIR};
    #python3 ${PYSCRPT}.py gen_s3;

    # Run Jasper to determine if combinations of PLs can be repeated within a particular subset
    #cd ../../..
    #./run.sh ${FV_UNITDIR} ${TCLFILE3} ${SVFILE3}

fi

cd ${INAME_DIR}/${DIR};
#python3 ${PYSCRPT}.py pp; 
python3 ${PYSCRPT}.py pp_repeat_only;
