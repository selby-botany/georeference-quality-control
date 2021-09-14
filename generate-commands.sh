#!/bin/bash

# set -xv

HOME=$(cd $(dirname "$0") && pwd)
DATE=$(date --utc '+%Y-%m-%d')
DATA=${HOME}/data/${DATE}
mkdir -p "${DATA}" -m 755 

column-map() {
    header=${1:?Need header line}
    result=
    i=0
    for f in $(echo "${header}" | sed 's/ /-/g' | sed 's/,/ /g' | tr A-Z a-z); do
        if [[ $f == 'sel-num' ]] || [[ $f == 'selby-number' ]] || [[ $f == 'number' ]]; then
            result="${result},accession-number:$i"
        elif [[ $f == 'countryid' ]]; then
            result="${result},country:$i"
        elif [[ $f == 'div1id' ]]; then
            result="${result},pd1:$i"
        elif [[ $f == 'latitudedd' ]] || [[ $f == 'latdd' ]]; then
            result="${result},latitude:$i"
        elif [[ $f == 'longitudedd' ]] || [[ $f == 'longdd' ]]; then
            result="${result},longitude:$i"
        fi
        i=$((i+1))
    done
    result=${result#,}
    (echo "${result}" | grep -q 'accession-number') || (echo "FATAL: missing accession number in header: ${header}" >/dev/stderr; exit 1)
    (echo "${result}" | grep -q 'country') || (echo "FATAL: missing country in header: ${header}" >/dev/stderr; exit 1)
    (echo "${result}" | grep -q 'pd1') || (echo "FATAL: missing pd1 in header: ${header}" >/dev/stderr; exit 1)
    (echo "${result}" | grep -q 'latitude') || (echo "FATAL: missing latitude in header: ${header}" >/dev/stderr; exit 1)
    (echo "${result}" | grep -q 'longitude') || (echo "FATAL: missing longitude in header: ${header}" >/dev/stderr; exit 1)
    echo "${result}"
}


field-cut-selector() {
    header=${1:?Need header line}
    result=
    i=1
    for f in $(echo "${header}" | sed 's/ /-/g' | sed 's/,/ /g' | tr A-Z a-z); do
        if [[ $f == 'sel-num' ]] || [[ $f == 'selby-number' ]] || [[ $f == 'number' ]] || \
           [[ $f == 'countryid' ]] || [[ $f == 'div1id' ]] || \
           [[ $f == 'latitudedd' ]] || [[ $f == 'latdd' ]] ||
           [[ $f == 'longitudedd' ]] || [[ $f == 'longdd' ]]; then
            result="${result},$i"
        fi
        i=$((i+1))
    done
    result=${result#,}
    echo "${result}"
}


execute() {
    for country in $(find "${HOME}/data" -type f -name '*.original.csv' | \
                     rev | \
                     cut -d/ -f1 | \
                     rev | \
                     sed -E 's/.original.csv$//' | \
                     grep -v johns-outliers | \
                     grep -v "${DATE}--" | \
                     cut -d- -f5- | \
                     sed -E 's/--[0-9]+$//g' | \
                     sed -E 's/--.*$//g' | \
                     sort | \
                     uniq
                    ); do
        inputfile="${DATA}/${DATE}--${country}.input.csv"
        resultsfile="${DATA}/${DATE}--${country}.results.csv"
        for datafile in $(find "data" -type f -name '*'${country}'.results.csv' | \
                          grep -v "${DATE}--" | \
                          sort | \
                          tail -n 1
                         ); do
            header=$(cat "${datafile}" | head -1 | sed -E 's/(^[ \t]*|[ \t]*$)//g')
            if [[ -z "${header}" ]]; then
                echo "ERROR: invalid datafile «${datafile}»" >/dev/stderr
            else
                columnMap=$(column-map "${header}")
                fields=$(field-cut-selector "${header}")
                echo "cat '${datafile}' | grep -v ',pass,matching-country-and-pd1,' | python ./csvcut.py -f${fields} | tee '${inputfile}' | python ./gqc.py > '${resultsfile}'"
            fi
        done
    done
}


( cd "${HOME}" && execute "${@}" )
