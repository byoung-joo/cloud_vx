#!/bin/ksh

files="bin/MET/driver_script_with_python.ksh bin/MET/driver_script_with_python_manual.ksh \
       xml/check_cloud_vx.ksh xml/cloud_vx.xml xml/run_cloud_vx.ksh xml/stat_cloud_vx.ksh"

DIR=`pwd`
echo $DIR

USER=`whoami`
echo $USER

sed -i -e "s#REL_DIR#${DIR}#" ${files}
sed -i -e "s#REL_USER#${USER}#" ${files}
