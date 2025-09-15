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
## STEP 2
########## 
cd $INAME
INAME_DIR=$(realpath .)

echo "
================================================================================
STEP 2 at $(pwd) $(date)
================================================================================
"
DIR=xPairwiseDepDiv
PYSCRPT=xPairwiseDep_post
if [ -d "${DIR}" ]; then 
    echo "Directory exists ${DIR} and skip"
else 
    cp -r ../${DIR} .
fi

# Generate SV and TCL for pairwise dep check
JOB="rtl2mupath_pairwise_dep"
SVFILE=$(realpath ${DIR})/${JOB}".sv"
TCLFILE=$(realpath ${DIR})/${JOB}".tcl"
cd ${DIR}; python3 ${PYSCRPT}.py gen; cd ..

# Run Jasper to get pairwise dep check results
cd ../..
./run.sh ${FV_UNITDIR} ${TCLFILE} ${SVFILE}

# Post process pairwise dep check results
cd  ${INAME_DIR}/${DIR}
python3 ${PYSCRPT}.py pp;
python3 ${PYSCRPT}.py stats; 
cd ../
