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
# STEP 6
######### 
cd $INAME
INAME_DIR=$(realpath .)

echo "
================================================================================
STEP 6 at $(pwd) $(date)
================================================================================
"

# 1. ...
# 2. ...
DIR=xHBPerfG_leaving
PYSCRPT=xHBPerfG_leaving
if [ -d "${DIR}" ]; then 
    echo "Directory exists ${DIR} and skip"

#else 
    #cp -r ../${DIR} .

  
    JOB1=rtl2mupath_revisit_hb_leaving1
    JOB2=rtl2mupath_revisit_hb_leaving2 
    TCLFILE1=$(realpath ${DIR})/${JOB1}.tcl
    SVFILE1=$(realpath ${DIR})/${JOB1}.sv
    TCLFILE2=$(realpath ${DIR})/${JOB2}.tcl
    SVFILE2=$(realpath ${DIR})/${JOB2}.sv

    # Generate properties to determine HB edges for the last visit of a repeated PL
    #cd ${DIR}; 
    #python3 ${PYSCRPT}.py gen; 

    # Run Jasper to get HB edges for the last cycle of a repeated PL
    #cd ../../..
    #./run.sh ${FV_UNITDIR} ${TCLFILE1} ${SVFILE1}

    # Generate properties for WHB and concurrent relationships between a PL and a final visit to a repeated node
    cd ${INAME_DIR}/${DIR};
    python3 ${PYSCRPT}.py gen_s2;

    # Run Jasper to get WHB and CONCUR relations for counterexamples found in step 1
    cd ../../..
    ./run.sh ${FV_UNITDIR} ${TCLFILE2} ${SVFILE2}

fi

# at $INAME
cd ${INAME_DIR}/${DIR}; 
python3 ${PYSCRPT}.py pp; 
