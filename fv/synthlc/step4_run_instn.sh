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


########## 
## STEP 4
########## 
cd $INAME
INAME_DIR=$(realpath .)

echo "
================================================================================
STEP 4 at $(pwd) $(date)
================================================================================
"

DIR=xHBPerfG_dfg_v3_div
PYSCRPT=xHBPerf_dfg_v3
if [ -d "${DIR}" ]; then 
    echo "Directory exists ${DIR} and skip"
else 
    JOB1="rtl2mupath_HB_1"
    JOB2="rtl2mupath_HB_2"

    SVFILE=$(realpath ${DIR})/${JOB1}.sv
    TCLFILE1=$(realpath ${DIR})/${JOB1}.tcl
    TCLFILE2=$(realpath ${DIR})/${JOB2}.tcl

    # Generate SV and TCL for HB properties
    cp -r ../${DIR} .
    cd ${DIR}; python3 ${PYSCRPT}.py gen; cd ..

    # Run Jasper to get HB property results
    cd ../..
    ./run.sh ${FV_UNITDIR} ${TCLFILE1} ${SVFILE}

    # Generate SV and TCL for WHB properties
    cd ${INAME_DIR}/${DIR};
    python3 ${PYSCRPT}.py gen_s2

    # Run Jasper to get WHB property results
    cd ../../..
    ./run.sh ${FV_UNITDIR} ${TCLFILE2} ${SVFILE}

fi


# Post process HB property results
cd ${INAME_DIR}/${DIR};
python3 ${PYSCRPT}.py pp; 
#python3 ${PYSCRPT}.py stats; 
cd ../
