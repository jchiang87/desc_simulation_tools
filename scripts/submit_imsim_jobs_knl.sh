#!/bin/bash -l

#SBATCH --partition=regular
#SBATCH --nodes=1
#SBATCH --time-min=06:00:00
#SBATCH --time=48:00:00
#SBATCH --job-name=v32678-z
#SBATCH --license=SCRATCH
#SBATCH --constraint=knl
#SBATCH --signal=B:USR1@120
#SBATCH --requeue
#SBATCH --open-mode=append

max_timelimit=48:00:00
ckpt_overhead=120
ckpt_command="echo checkpointing"

module load ata
. $ATA_DIR/etc/ATA_setup.sh

requeue_job func_trap USR1

export OMP_NUM_THREADS=1
export KMP_AFFINITY=disabled

export ROOTDIR=/global/cscratch1/sd/jchiang8/imsim_pipeline
export CWD=${ROOTDIR}/imSim/work/process_monitor_tests/zband
source ${ROOTDIR}/setup.sh

srun -n 1 -c 272 python ${CWD}/run_imsim.py &

wait
