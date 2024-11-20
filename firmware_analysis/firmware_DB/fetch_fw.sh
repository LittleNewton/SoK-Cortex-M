#!/bin/bash

FW=firmware
FW_TMP=${FW}.d
FW_ASM=firmware-disassembly
FW_ASM_TMP=${FW_ASM}.d

# 创建目标文件夹
rm -fr $FW $FW_ASM
mkdir $FW $FW_ASM $FW_TMP $FW_ASM_TMP

# 解压文件到临时文件夹
unzip "SoK-Cortex-M-firmware.zip" -d $FW_TMP
unzip "SoK-Cortex-M-firmware-disassembly.zip" -d $FW_ASM_TMP

# 移动固件到目标文件夹
mv -f ${FW_TMP}/firmware/* $FW
mv -f ${FW_ASM_TMP}/new/* $FW_ASM

# 删除临时文件夹
rm -fr ${FW_TMP}
rm -fr ${FW_ASM_TMP}

find . -iname '.DS_Store' -delete
