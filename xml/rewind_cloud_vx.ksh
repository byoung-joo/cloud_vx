#!/bin/ksh
pathnam=/glade/scratch/`whoami`/cloud_vx/xml
pathroc=/glade/u/home/harrop/opt/rocoto/1.2.4-p1

cycle1=201811010000
cycle2=201811020000
cycle3=201811030000
cycle4=201811040000
cycle5=201811050000
cycle6=201811060000
cycle7=201811070000
cycle8=201811080000

task03="point_stat_EPIC_Cloud_Mask_03"
task06="point_stat_EPIC_Cloud_Mask_06"
task09="point_stat_EPIC_Cloud_Mask_09"
task12="point_stat_EPIC_Cloud_Mask_12"
task15="point_stat_EPIC_Cloud_Mask_15"
task18="point_stat_EPIC_Cloud_Mask_18"
task21="point_stat_EPIC_Cloud_Mask_21"
task24="point_stat_EPIC_Cloud_Mask_24"
task27="point_stat_EPIC_Cloud_Mask_27"
task30="point_stat_EPIC_Cloud_Mask_30"
task33="point_stat_EPIC_Cloud_Mask_33"
task36="point_stat_EPIC_Cloud_Mask_36"
task39="point_stat_EPIC_Cloud_Mask_39"
task42="point_stat_EPIC_Cloud_Mask_42"
task45="point_stat_EPIC_Cloud_Mask_45"
task48="point_stat_EPIC_Cloud_Mask_48"

pwd
${pathroc}/bin/rocotorewind -w ${pathnam}/cloud_vx.xml -d ${pathnam}/cloud_vx.db -c ${cycle1} -c ${cycle2} -c ${cycle3} -c ${cycle4} -c ${cycle5} -c ${cycle6} -c ${cycle7} -c ${cycle8} -t ${task03} -t ${task06} -t ${task09} -t ${task12} -t ${task15} -t ${task18} -t ${task21} -t ${task24} -t ${task27} -t ${task30} -t ${task33} -t ${task36} -t ${task39} -t ${task42} -t ${task45} -t ${task48}    

#/glade/u/home/harrop/opt/rocoto/1.2.4-p1/bin/rocotorewind -w /glade/scratch/jwolff/CAF/met/draft_3rd_cs/xml/cloud_vx.xml -d /glade/scratch/jwolff/CAF/met/draft_3rd_cs/xml/cloud_vx.db -c 201811010000 -t taskname
