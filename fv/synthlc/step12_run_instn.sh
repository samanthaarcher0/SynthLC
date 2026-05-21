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

cp $INSTNDIR/$fnm "${INAME}/idef.sv"

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
STEP 12 at $(pwd) $(date)
================================================================================
"

DIR=xRunSpv
#PYSCRPT=xRunSpv
PYSCRPT=xRunIFT
confirmed="y"
if [ -d "${DIR}" ]; then
    echo "Directory exists $INAME. Redo step? [y/n]"
    read confirmed
fi
if [ $confirmed == "y" ]; then
    #JOB="spv_rtl2mupath_taint_rs1"
    JOB="ift_rtl2mupath_taint_rs1"

    SVFILE=$(realpath ${DIR})/${JOB}.sv
    TCLFILE=$(realpath ${DIR})/${JOB}.tcl

    # Generate SV and TCL for HB properties
    cp -r ../${DIR} .
    cd ${DIR}; python3 ${PYSCRPT}.py gen; cd ..

    # Run Jasper to get HB property results
    cd ../..
    #./run.sh ${FV_UNITDIR} ${TCLFILE} ${SVFILE}
    #./RUN_JG.sh -j ${INAME_DIR}/${DIR} -s ${SVFILE} -t ${TCLFILE} -g 1 --spv 1
#    ./RUN_JG_ift.sh -j {job} -s {filename} -h src_ift/hdl.f -f src_ift/cellift_top_rewrite.sv -p src_ift/common_header.sv -t src_ift/jg.tcl -g 1
    ./RUN_JG_ift.sh -j ${INAME_DIR}/${DIR} -t ${TCLFILE} -s ${SVFILE} -h src_ift/hdl.f -f src_ift/cellift_top_rewrite.sv -p src_ift/common_header.sv -g 1
fi


# Post process HB property results
cd ${INAME_DIR}/${DIR};
python3 ${PYSCRPT}.py pp; 
#python3 ${PYSCRPT}.py stats; 
cd ../
