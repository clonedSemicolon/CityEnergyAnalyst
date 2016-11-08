#!/usr/bin/env sh

# parameters
N=${N:-1}
METHOD=${METHOD:-morris}
SAMPLES_FOLDER=${SAMPLES_FOLDER:-${SCRATCH}/samples_${METHOD}_${N}}
CALC_SECOND_ORDER=${CALC_SECOND_ORDER:-0}
GRID_JUMP=${GRID_JUMP:-2}
NUM_LEVELS=${NUM_LEVELS:-4}
VARIABLE_GROUPS=${VARIABLE_GROUPS:-THERMAL}

mkdir -p $SAMPLES_FOLDER

# create the samples
python -m cea.analysis.sensitivity.sensitivity_demand_samples --samples-folder $SAMPLES_FOLDER -n $N \
          --method $METHOD --calc-second-order $CALC_SECOND_ORDER --grid-jump $GRID_JUMP --num-levels $NUM_LEVELS \
          --variable-groups $VARIABLE_GROUPS
