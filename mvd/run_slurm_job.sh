#!/bin/bash
# --------------------------------------------------------------------------------
# Copyright © 2025, Koninklijke Philips N.V.
#
# Licensed under the License terms and conditions for use, reproduction, and
# distribution of 5G-MAG software (the “License”).  You may not use this file
# except in compliance with the License.  You may obtain a copy of the License at
# https://www.5g-mag.com/reference-tools.  Unless required by applicable law or
# agreed to in writing, software distributed under the License is distributed on
# an “AS IS” BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
# or implied.
#
# See the License for the specific language governing permissions and limitations
# under the License.
# --------------------------------------------------------------------------------

# This script blocks on a Slurm batch job

# Submit the batch job
job_output=$(sbatch "$@")
job_id=$(echo $job_output | awk '{print $NF}')

if [ -z "$job_id" ]
then
  echo "Failed to submit job"
  exit 1
fi

# Cancel the job when this script is interrupted (Ctrl+C)
trap "scancel $job_id" SIGINT

# Wait for the job to leave the queue
job_is_running() {
  job_status=$(squeue -j $job_id --noheader)
  [[ "$job_status" =~ "$job_id" ]]
}

while job_is_running
do
  sleep 5
done

# Check if the job was successful
job_has_completed() {
  job_status=$(sacct -j $job_id -X --noheader)
  [[ "$job_status" =~ COMPLETED ]]
}

if ! job_has_completed
then
  echo "Job $job_id failed"
  exit 1
fi

exit 0
