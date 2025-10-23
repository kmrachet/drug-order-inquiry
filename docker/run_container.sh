docker container run \
  -dit \
  --rm \
  -p 8989:8888 \
  --name drug-order-inquiry \
  --user root \
  --mount type=bind,source=$(cd $(dirname ${BASH_SOURCE:-$0}); pwd)/../,target=/home/jovyan/work \
  --mount type=bind,source=$(cd $(dirname ${BASH_SOURCE:-$0}); pwd)/../../DATA/mid-net-cuh,target=/home/jovyan/work/data \
  kmrachet/mid-net-cuh:jupy2025-08-11
