#!/bin/bash

set -ex

for i in {1..1000}; do
    python solve.py &
    sleep 10
done

wait

