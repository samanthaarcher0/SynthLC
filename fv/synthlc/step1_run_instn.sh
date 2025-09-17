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

if [ -d "$INAME" ]; then 
    echo "Directory exists $INAME. Remove [y/n]"
    read confirmed
    if [ $confirmed == "y" ]; then
        rm -rf "$INAME"
        mkdir $INAME
    fi
else
    echo "Working on $INAME"
    mkdir $INAME
fi

INSTN="$INSTNDIR/$fnm"
echo "=========== INSTN ============="
echo "- Directory: $INAME"
echo "- Instruction file: $INSTN"
cat $INSTN
echo "==============================="


echo ${PWD}
echo ${PWD_PREFIX}



# Shared by all instructions 
#if [ ! -f "xGenPerfLocDfgDiv/dfg_e.txt" ]; then
#    exit
#fi 
echo "========== DFG E prepared ========== "

FV_UNITDIR=$(realpath ../../..)


##### per instruction header file generation#####

HEADERFILE=$(realpath ../header.sv)
echo "HEADERFILE: $HEADERFILE"
HEADERFILE_TCL=$(realpath ../header.tcl)
echo "HEADERFILE_TCL: $HEADERFILE_TCL"

head -n -5 $HEADERFILE > $INAME/header.sv
tail -n 5 $HEADERFILE >> $INAME/header.sv

cat $HEADERFILE_TCL > $INAME/header.tcl
cat ${INSTNDIR}/${fileprefix}.tcl >> $INAME/header.tcl


########## 
## STEP 1 
########## 
cd $INAME
INAME_DIR=$(realpath .)

echo "
================================================================================
STEP 1 at $(pwd) $(date)
================================================================================
"

DIR=xCoverAPerflocDiv
PYSCRPT=gen
if [ -d "${DIR}" ]; then 
    echo "Directory exists ${DIR} and do only post-proc step"
else 
    JOB="rtl2mupath_instn_reachable_perf_loc"
    SVFILE=$(realpath ${DIR})/${JOB}".sv"
    TCLFILE=$(realpath ${DIR})/${JOB}".tcl"

    # Generate SV and TCL files to check if DUV PLs are reachable by this instruction
    cp -r ../${DIR} .
    cd ${DIR}; python3 ${PYSCRPT}.py gen; cd ..
    

    # Run Jasper to get INSN reachable perf locs
    cd ../..
    ./run.sh ${FV_UNITDIR} ${TCLFILE} ${SVFILE}

    # Additional pruning that we are not doing here
    # cd ${INAME_DIR}/${DIR}; python3 ${PYSCRPT}.py gen_s2
    
fi

# Post process results
cd ${INAME_DIR}/${DIR};
python3 ${PYSCRPT}.py pp; 
python3 ${PYSCRPT}.py stats; 
cd ../
