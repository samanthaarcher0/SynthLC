#!/usr/bin/bash
FV_UNITDIR=$(realpath ../..)
CWD=$(realpath .)
USER_FILES_DIR=$(realpath ../user_provided_files)

basic_header_sv="${USER_FILES_DIR}/basic_header.sv"
basic_header_tcl="${USER_FILES_DIR}/basic_header.tcl"

# Copying TCL header file
cp ${basic_header_tcl} header.tcl
cat ${CWD}/synthlc/assumptions/assumptions_base.tcl >> header.tcl
cat ${CWD}/synthlc/assumptions/assumptions.tcl >> header.tcl

if [ ! -f xDUVPLs/reachable_duvpls.sv ];
then
    echo "Starting"
    # Get signal widths: 1. Generate get_sig_width.tcl
    cd xDUVPLs
    python3 gen.py get_width
    TCLFILE=$(realpath rtl2mupath_get_sig_width.tcl)
    cp ${basic_header_tcl} ${TCLFILE}
    cat get_sig_width.tcl >> ${TCLFILE}

    # Get signal widths: 2. Run Jasper to get signal widths
    cd ${CWD}
    ./run.sh ${FV_UNITDIR} ${TCLFILE} ${basic_header_sv} 
    
    # Get DUV PLs: 1. Generate SV and TCL files to check if DUV PLs are reachable
    cd ${CWD}/xDUVPLs
    python3 gen.py gen_duv_pl_checks
    SVFILE=${CWD}/xDUVPLs/rtl2mupath_perf_loc.sv
    TCLFILE=${CWD}/xDUVPLs/rtl2mupath_perf_loc.tcl
    head -n -5 ${basic_header_sv} > ${SVFILE} 
    echo "// Annotate with all candidate PLs" >> ${SVFILE} 
    cat perf_loc.sv >> ${SVFILE}
    tail -n 6 ${basic_header_sv}  >> ${SVFILE}
    
    cp ../header.tcl ${TCLFILE}
    cat perf_loc.tcl >> ${TCLFILE}
    
    # Get DUV PLs: 2. Run Jasper to get reachable PLs
    cd ${CWD}
    ./run.sh ${FV_UNITDIR} ${TCLFILE} ${SVFILE} 

    # Get DUV PLs: 3. Post process results 
    # Generate reachable_duvpls.sv with all reachable PLs
    cd ${CWD}/xDUVPLs
    python3 gen.py pp
    cd ../
fi


# Copying SV header file 
head -n -5 ${basic_header_sv} > header.sv
echo "
// =============================================================================
// ## Performing location annotation
// ============================================================================= 
" >> header.sv
cat ${CWD}/xDUVPLs/reachable_duvpls.sv >> header.sv
tail -n 5 ${basic_header_sv} >> header.sv

