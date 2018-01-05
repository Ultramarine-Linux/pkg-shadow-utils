#!/bin/bash
. /usr/bin/rhts-environment.sh
. /usr/share/beakerlib/beakerlib.sh || exit 1

rlJournalStart
rlFileBackup --clean /etc/default/useradd- /etc/default/useradd
setenforce 0
python sanity_test.py -v
setenforce 1
rlFileRestore

EXIT=$?
if [[ $EXIT -eq 0 ]]; then
    RESULT="PASS"
else
    RESULT="FAIL"
fi


rlJournalEnd

echo "Result: $RESULT"
echo "Exit: $EXIT"
report_result $TEST $RESULT $EXIT
