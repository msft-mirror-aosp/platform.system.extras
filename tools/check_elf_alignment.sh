#!/bin/bash
progname="${0##*/}"
progname="${progname%.sh}"

# usage: check_elf_alignment.sh [path to *.so files|path to *.apk]

cleanup_trap() {
  if [ -n "${tmp}" -a -d "${tmp}" ]; then
    rm -rf ${tmp}
  fi
  exit $1
}

usage() {
  echo "Host side script to check the ELF alignment of shared libraries."
  echo "Shared libraries are reported ALIGNED when their ELF regions are"
  echo "16 KB or 64 KB aligned. Otherwise they are reported as UNALIGNED."
  echo
  echo "Usage: ${progname} [input-path|input-APK]"
}

if [ ${#} -ne 1 ]; then
  usage
  exit
fi

case ${1} in
  --help | -h | -\?)
    usage
    exit
    ;;

  *)
    dir="${1}"
    ;;
esac

if ! [ -f "${dir}" -o -d "${dir}" ]; then
  echo "Invalid file: ${dir}" >&2
  exit 1
fi

if [[ ${dir} == *.apk ]]; then
  trap 'cleanup_trap' EXIT

  if { zipalign --help 2>&1 | grep -q "\-P <pagesize_kb>"; }; then
    echo "=== APK zip-alignment ==="
    zipalign -v -c -P 16 4 ${dir} | egrep 'lib/arm64-v8a|lib/x86_64|Verification'
    echo "========================="
  else
    echo "NOTICE: Zip alignment check requires build-tools version 35.0.0-rc3 or higher."
    echo "  You can install the latest build-tools by running the below command"
    echo "  and updating your \$PATH:"
    echo
    echo "    sdkmanager \"build-tools;35.0.0-rc3\""
  fi

  dir_filename=$(basename ${dir})
  tmp=$(mktemp -d -t ${dir_filename%.apk}_out_XXXXX)
  unzip ${dir} lib/arm64-v8a/* lib/x86_64/* -d ${tmp} >/dev/null 2>&1
  dir=${tmp}
fi

RED="\e[31m"
GREEN="\e[32m"
ENDCOLOR="\e[0m"

unaligned_libs=()

echo
echo "=== ELF alignment ==="

matches="$(find ${dir} -name "*.so" -type f)"
IFS=$'\n'
for match in $matches; do
  res="$(objdump -p ${match} | grep LOAD | awk '{ print $NF }' | head -1)"
  if [[ $res =~ "2**14" ]] || [[ $res =~ "2**16" ]]; then
    echo -e "${match}: ${GREEN}ALIGNED${ENDCOLOR} ($res)"
  else
    echo -e "${match}: ${RED}UNALIGNED${ENDCOLOR} ($res)"
    unaligned_libs+=(${match})
  fi
done

if [ ${#unaligned_libs[@]} -gt 0 ]; then
  echo -e "${RED}Found ${#unaligned_libs[@]} unaligned libs${ENDCOLOR}"
elif [ -n "${dir_filename}" ]; then
  echo -e "ELF Verification Successful"
fi
echo "====================="
