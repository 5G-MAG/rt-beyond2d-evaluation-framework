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
from pyntcloud import PyntCloud
import numpy as np

#local include
commonDir = Path(__file__).resolve(strict=True).parent.joinpath("../common")
sys.path.append(str(Path(commonDir)))
import utils as utils

def replace_in_file(file_path, search_text, new_text):
    with fileinput.input(file_path, inplace=True) as file:
        for line in file:
            new_line = line.replace(search_text, new_text)
            print(new_line, end='')

def remove_duplicates(input_file,output_file, binaryMode):
    out_vox_ply_point_cloud = PyntCloud.from_file(input_file)            
    out_vox_ply_point_cloud.points = (out_vox_ply_point_cloud.points).groupby(["x", "y", "z"]).mean().reset_index()            
    out_vox_ply_point_cloud.points = out_vox_ply_point_cloud.points.astype({"x": "uint32", "y": "uint32", "z": "uint32", "nx": "float32", "ny": "float32", "nz": "float32", "green": "uint8", "blue": "uint8", "red": "uint8"})
    out_vox_ply_point_cloud.to_file(output_file, as_text=True) #as_text=operator.not_(binaryMode))
    print(out_vox_ply_point_cloud, flush=True)
    ## replace header type of vertex to be compatible with renderer
    replace_in_file(output_file, 'property uchar x', 'property float x')
    replace_in_file(output_file, 'property uchar y', 'property float y')
    replace_in_file(output_file, 'property uchar z', 'property float z')
    out_vox_ply_point_cloud = PyntCloud.from_file(output_file)            
    out_vox_ply_point_cloud.to_file(output_file, as_text=operator.not_(binaryMode))
    print(out_vox_ply_point_cloud, flush=True)
            
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
parser.add_argument('-i',  '--inputMesh',       help="Input MESH OBJ path ", type=str)
parser.add_argument('-m',  '--inputTexture',    help="Input MESH TXT path", type=str)
parser.add_argument('-o',  '--outputPlyPath',   help="Output  PLY path", type=str)
parser.add_argument(       '--outputPlyFormat', help="Output PLY file fomat", type=str)
parser.add_argument(       '--qp',              help="Geometry quantization bitdepth", type=int)
parser.add_argument(       '--ratio',           help="Ratio for sample", type=float)
parser.add_argument(       '--firstFrame',      help="Sets the first frame of the sequence included", type=int)
parser.add_argument(       '--nbFrame',         help="Sets the number of frame of the sequence", type=int)
parser.add_argument('-b',  '--binary',          help="if True, PLY is saved in binary mode, else PLY is saved in ascii mode", type=utils.str2bool)
parser.add_argument(       '--mmExe',           help="Path to mm tool executable", type=str)

cleanMode = 2 #0:noclean 1:remove quantized 2:remove sampled and quantized

##################
def main():

    try:
        
        if len(sys.argv) == 1:
            parser.print_help(sys.stderr)
            sys.exit(1)
        args = parser.parse_args()
               
        print ("-------------------------------------------")
        print (utils.BLUE + "Input Arguments :" , utils.ENDC)
        print (utils.BLUE + "\tinputMesh        =", args.inputMesh , utils.ENDC)
        print (utils.BLUE + "\tinputTexture     =", args.inputTexture , utils.ENDC)
        print (utils.BLUE + "\toutputPlyPath    =", args.outputPlyPath , utils.ENDC)
        print (utils.BLUE + "\toutputPlyFormat  =", args.outputPlyFormat , utils.ENDC)
        print (utils.BLUE + "\tqp               =", args.qp , utils.ENDC)
        print (utils.BLUE + "\tratio            =", args.ratio , utils.ENDC)
        print (utils.BLUE + "\tfirstFrame       =", args.firstFrame , utils.ENDC)
        print (utils.BLUE + "\tnbFrame          =", args.nbFrame , utils.ENDC)
        print (utils.BLUE + "\tbinary           =", args.binary , utils.ENDC)
        print (utils.BLUE + "\tmmExe            =", args.mmExe , utils.ENDC)
        print ("-------------------------------------------", flush=True)
        
        # analyse and sample input mesh
        outputDir = Path(args.outputPlyPath).resolve()
        if not outputDir.exists():
            print("create dir:", outputDir, flush=True);
            os.makedirs(outputDir, exist_ok=True)
        
        lastFrame = args.firstFrame + args.nbFrame - 1
        mm = Path(args.mmExe).resolve(strict=True)
        
        outputSampledModel    = "".join([str(outputDir), "/", args.outputPlyFormat.replace("%", "sample_%")])
        outputQuantizedModel  = "".join([str(outputDir), "/", args.outputPlyFormat.replace("%", "quantize_%")])
        outputPlyModel        = "".join([str(outputDir), "/", args.outputPlyFormat])
        outputVar             = "".join([str(outputDir), "/", args.outputPlyFormat.split("%")[0], "analyse.txt"])
        cmdFile               = "".join([str(outputDir), "/", args.outputPlyFormat.split("%")[0], "command.log"])
        logFile               = "".join([str(outputDir), "/", args.outputPlyFormat.split("%")[0], "output.log"])
        outputSampledList     = [outputSampledModel % i for i in range(args.firstFrame, lastFrame + 1)]
        inQuantizePlyList     = [outputQuantizedModel % i for i in range(args.firstFrame, lastFrame + 1)]
        outPlyList            = [outputPlyModel % i for i in range(args.firstFrame, lastFrame + 1)] 
        
        if not os.path.exists(logFile):
            
            print (utils.GREEN  + "Analyse and Sample (grid): ", args.inputMesh,  utils.ENDC, flush=True)
            
            # to adapt with the ratio value
            gridSize=int ( (2 ** args.qp) *  np.sqrt(args.ratio))
            
            config = "".join([
                            " sequence"
                            " --firstFrame ", str(args.firstFrame),
                            " --lastFrame ", str(lastFrame),
                            " END"
                            " analyse"
                            " --inputModel ", args.inputMesh,
                            " --inputMap ", args.inputTexture,
                            " --outputVar ", outputVar,
                            " END"
                            " sample"
                            " --mode grid"
                            " --useNormal"                           
                            " --gridSize ", str(gridSize),
                            " --inputModel ", args.inputMesh,
                            " --inputMap ", args.inputTexture,
                            " --outputModel ", outputSampledModel,
                            " --hideProgress 1 ",
                            ])
                            
            cmd = " ".join([str(mm), config]) 
            f = open(cmdFile,'w')
            print(cmd, file=f) 
            f.close()      
            subprocess.check_call(cmd, shell=True)      
            
            # extract information from analyse
            with open(outputVar,'r') as f:
                target1 = [line for line in f if "globalMinPos" in line]
            with open(outputVar,'r') as f:
                target2 = [line for line in f if "globalMaxPos" in line]           
        
            globalMinPos = np.array(target1[0].split("=")[1].strip()[1:-1].split(" ")).astype(np.float64)
            globalMaxPos = np.array(target2[0].split("=")[1].strip()[1:-1].split(" ")).astype(np.float64)
            # to adapt with the ratio value
            globalMaxPosModified = globalMaxPos * ((2 ** args.qp) - 1.0) / (gridSize - 1.0)           
                    
            # quantize
            print (utils.GREEN  + "Quantize: ", outputSampledModel,  utils.ENDC, flush=True)
            config = "".join([
                            " sequence"
                            " --firstFrame ", str(args.firstFrame),
                            " --lastFrame ", str(lastFrame),
                            " END"
                            " quantize"                     
                            " --qp ", str(args.qp),
                            " --qc 8"
                            " --qn 0"
                            " --minPos ", '"' + str(globalMinPos)[1:-1] + '"',
                            " --maxPos ", '"' + str(globalMaxPosModified)[1:-1] + '"',
                            " --minCol \"0 0 0\""
                            " --maxCol \"255 255 255\""
                            " --useFixedPoint"
                            " --inputModel ", outputSampledModel,
                            " --outputModel ", outputQuantizedModel,
                            ])
            
            cmd = " ".join([str(mm), config]) 
            f = open(cmdFile,'a')
            print(cmd, file=f) 
            f.close()
            subprocess.check_call(cmd, shell=True)
            
            # output in log number of points per frame
            # logPlyInfo("grid Sampled ", logFile, outputSampledList)
            
            # directory cleaning
            if cleanMode == 2:
                for i in outputSampledList:
                    print (utils.GREEN  + "Remove sampled PLY",  utils.ENDC, flush=True)
                    os.remove(i) 
            
            # remove duplicates
            print (utils.GREEN  + "Remove duplicate points: ",  utils.ENDC, flush=True)        
            for i,j in zip(inQuantizePlyList, outPlyList):
               #print(f"Index {i}:{j}")
               print (utils.GREEN  + "Remove Duplicates: ", i,  utils.ENDC, flush=True)
               remove_duplicates(i,j, args.binary)
           
            # output in log number of points per frame and md5
            logPlyInfo("grid Sampled + Quantized + RmDuplicate", logFile, outPlyList)      
            
            # directory cleaning
            if cleanMode == 1 or cleanMode == 2:
                for i in inQuantizePlyList:
                    print (utils.GREEN  + "Remove intermediate quantized PLY",  utils.ENDC, flush=True)
                    os.remove(i)   
                    
        else:
            print(utils.RED, "process already done.", utils.ENDC, flush=True)          
        
    except Exception as e:
        print (utils.RED + "Exception:", e, utils.ENDC, flush=True)
        sys.exit();
    except subprocess.CalledProcessError as e:
        print(utils.RED + "subprocess Exception:", e.returncode, utils.ENDC)
        print(utils.RED + e.cmd, utils.ENDC)
        print(utils.RED + e.output, utils.ENDC, flush=True)        
        sys.exit();        
        
if __name__ == "__main__":
    main()
