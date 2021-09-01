#!/bin/bash

clear-cache()
{
    echo "[INFO] Deleting location cache"
    rm -fv ~/.gqc/gqc.reverse-lookup.cache
}

clear-logs()
{
    echo "[INFO] Deleting all logfiles"
    rm -fv ~/.gqc/log/*.log
}

run-all-tests()
{
    echo "[INFO] Running all tests"
    run-unit-tests "${*}" && run-functional-tests "${*}"
}

run-functional-tests()
{
    echo "[INFO] Running functional tests"
    echo "[INFO]  ... testing with empty location cache" && \
    clear-cache && \
    test/functional-test "${*}" && \
    echo "[INFO]  ... testing with existing location cache" && \
    test/functional-test "${*}"
}

run-unit-tests() 
{
    echo "[INFO] Running unit tests"
    for t in ~/iCloudDocs/Programming/Selby/Botany/gqc/test/unit.*.py;
    do
        $t;
    done
}

