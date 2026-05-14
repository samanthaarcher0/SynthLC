#!/usr/bin/bash
# ./run.sh ${FV_UNITDIR} ${TCLFILE} ${SVFILE}
dir=${1}
tcl=${2}
sv=${3}
python3 host_batch_run_template_v2.py ${dir} ${out}
