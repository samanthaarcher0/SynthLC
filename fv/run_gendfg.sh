#!/usr/bin/bash
# def_val=1
def_val=0
BYPASS=${BYPASS:-$def_val}

CWD=$(realpath .)

FV_UNITDIR=$(realpath ../..)

if [ $BYPASS -eq 1 ];
then
    cp expected_output/dfg_e.txt .
else
    JOB=get_dfg
    DIR=synthlc/xGenPerfLocDfgDiv
    SVFILE=$(realpath ${CWD}/${DIR}/${JOB}".sv")
    TCLFILE=$(realpath ${CWD}/${DIR}/${JOB}".tcl")
    
    # Generate TCL/SV files
    cd ${DIR}
    python3 gen_dfg_all_pls.py gen

    # Run Jasper
    cd ${CWD}
    ./run.sh ${FV_UNITDIR} ${TCLFILE} ${SVFILE}

    # Post process results 
    cd ${CWD}/${DIR}
    python3 gen_dfg_all_pls.py pp

fi 
cd ../../
