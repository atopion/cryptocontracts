#!/usr/bin/env bash

nPdf=$1
nKey=$2
path="$(dirname $0)/generated-files/"

if ! [[ "$nPdf" =~ ^[0-9]+$ ]] || ! [[ "$nKey" =~ ^[0-9]+$ ]]; then
  echo -e "$0 requires 2 arguments:\n1st: amount of pdfs to create\n2nd: amount of keys to create"
  exit
fi

for i in $(seq -w 1 $nPdf);
do
  base64 /dev/urandom | awk '{print(0==NR%10)?"":$1}' | sed 's/[^[:alpha:]]/ /g' | head -50 | pr | groff -Tpdf > "$path/pdf-$i.pdf"
done

for i in $(seq -w 1 $nKey);
do
  ssh-keygen -P '' -C "generated-key-$i" -f "$path/key-$i"
done

