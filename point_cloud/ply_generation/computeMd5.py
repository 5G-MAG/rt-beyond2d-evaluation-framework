#!/usr/bin/python3
#--------------------------------------------------------------------------------
# Copyright (c) 2025 InterDigital CE Patent Holdings
# 
# Licensed under the License terms and conditions for use, reproduction, and
# distribution of 5G-MAG software (the “License”).  You may not use this file
# except in compliance with the License.  You may obtain a copy of the License at
# https://www.5g-mag.com/reference-tools.  Unless required by applicable law or
# agreed to in writing, software distributed under the License is distributed on
# an “AS IS” BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
# or implied.
# 
# See the License for the specific language governing permissions and limitations
# under the License.
#--------------------------------------------------------------------------------

#import pymeshlab
import os
import subprocess
import re, sys, argparse
import operator
import fileinput
from pathlib import Path
import hashlib
import numpy as np

#local
import framework_utils as frameworkUtils
            
def logPlyInfo(strId, logF, plyList):
    f = open(logF,'w')
    sumVertex = 0
    print(f"{strId} Log Info: ", file=f)
    for filename in plyList:
        md5 = computeMd5(filename)
        with open(filename, 'r', errors='ignore') as file:
            lines=file.readlines()[0:8]
            for line in lines[1:]:
                if line.find("element vertex") == 0:
                    nbVertex = int(line.split(" ")[2])
                    sumVertex += nbVertex
                    print(f"\t{filename} : {nbVertex} points\tmd5sum:", {md5}, file=f) 
    
    averagePts=round(sumVertex/len(plyList))
    print(f"Nb Points Mean=", averagePts, file=f) 
    f.close() 

def computeMd5(file_path):
    hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        for line in f :
            #normalize line ending Window/Linux issue
            if line.endswith(b'\r\n'):
                line = line[:-2] + b'\n'
            elif line.endswith(b'\r'):
                line = line[:-1] + b'\n'
            hasher.update(line)
    return hasher.hexdigest()
    
parser = argparse.ArgumentParser(description='export OBJ files into PLY files using mm from MPEG (process done are : sample, quantize, remove duplicates')
parser.add_argument('-i',  '--plyPath',    help="Input PLY path", type=str)
parser.add_argument(       '--plyFormat',  help="Input PLY file fomat", type=str)
parser.add_argument(       '--qp',         help="Geometry quantization bitdepth", type=int)
parser.add_argument(       '--ratio',      help="Ratio for sample", type=float)
parser.add_argument(       '--firstFrame', help="Sets the first frame of the sequence included", type=int)
parser.add_argument(       '--nbFrame',    help="Sets the number of frame of the sequence", type=int)

##################
def main():

    try:
        
        if len(sys.argv) == 1:
            parser.print_help(sys.stderr)
            sys.exit(1)
        args = parser.parse_args()
               
        print ("-------------------------------------------")
        print (frameworkUtils.BLUE + "Input Arguments :" , frameworkUtils.ENDC)
        print (frameworkUtils.BLUE + "\tPlyPath          =", args.plyPath , frameworkUtils.ENDC)
        print (frameworkUtils.BLUE + "\tPlyFormat        =", args.plyFormat , frameworkUtils.ENDC)
        print (frameworkUtils.BLUE + "\tfirstFrame       =", args.firstFrame , frameworkUtils.ENDC)
        print (frameworkUtils.BLUE + "\tnbFrame          =", args.nbFrame , frameworkUtils.ENDC)
        print ("-------------------------------------------", flush=True)

        # analyse and sample input mesh
        plyDir = Path(args.plyPath).resolve()
        if not plyDir.exists():
            print("create dir:", plyDir, flush=True);
            os.makedirs(plyDir, exist_ok=True)
        
        lastFrame = args.firstFrame + args.nbFrame - 1
        
        plyModel   = "".join([str(plyDir), "/", args.plyFormat])
        logFile    = "".join([str(plyDir), "/", args.plyFormat.split("%")[0], "output_withNormalizedLineEndings.log"])
        outPlyList = [plyModel % i for i in range(args.firstFrame, lastFrame + 1)] 
        
        print (logFile)
        print (outPlyList)
        
        if not os.path.exists(logFile):           
            # output in log number of points per frame and md5
            logPlyInfo("grid Sampled + Quantized + RmDuplicate", logFile, outPlyList)      
        else:
            print(frameworkUtils.RED, "process already done.", frameworkUtils.ENDC, flush=True)          
        
    except Exception as e:
        print (frameworkUtils.RED + "Exception:", e, frameworkUtils.ENDC, flush=True)
        sys.exit();
    except subprocess.CalledProcessError as e:
        print(frameworkUtils.RED + "subprocess Exception:", e.returncode, frameworkUtils.ENDC)
        print(frameworkUtils.RED + e.cmd, frameworkUtils.ENDC)
        print(frameworkUtils.RED + e.output, frameworkUtils.ENDC, flush=True)        
        sys.exit();        
        
if __name__ == "__main__":
    main()
