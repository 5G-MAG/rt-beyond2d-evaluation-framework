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

import os, platform, sys, argparse, glob
import subprocess, csv
from pathlib import Path

#local
commonDir = Path(__file__).resolve(strict=True).parent.joinpath("../common")
sys.path.append(str(Path(commonDir)))
import utils as utils

def parseArgs():
    global parser
    parser = argparse.ArgumentParser(description='Extract metrics from encoding, decoding and mmetrics log files')
    parser.add_argument('--encoderFile', help="Input encoder log file")
    parser.add_argument('--decoderFile', help="Input decoder log file")
    parser.add_argument('--mmFile',      help="Input mm log file")
    return parser.parse_args()

def extract_metrics(encLogfile, decLogfile, mmLogfile=""):
    metadata = 0
    geometry = 0
    attribute = 0
    total = 0
    nbFrame = 0
    encodingTimes = [0, 0, 0]
    decodingTimes = [0, 0, 0]
    memory = [0, 0]
    results = [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0,0]]
    
    try:
        with open(encLogfile, 'r') as outlogfile:
            for line in outlogfile:
                if 'frameCount                                 '    in line:
                    words = line.split()
                    nbFrame += int(words[1])
                elif '  Total:            ' in line:
                    words = line.split()
                    total += int(words[1])
                elif '  TotalMetadata:'    in line:
                    words = line.split()
                    metadata += int(words[1])
                elif '  TotalGeometry:'    in line:
                    words = line.split()
                    geometry += int(words[1])
                elif '  TotalAttribute:'   in line:
                    words = line.split()
                    attribute += int(words[1])
                elif 'points with same'    in line:
                    words = line.split()
                    results[5][2] += int(words[1])
                elif 'Point cloud sizes'   in line:
                    words = line.split()
                    results[5][0] += int(words[12].replace(",",""))
                    results[5][1] += int(words[13].replace(",",""))
                elif 'Processing time (wall):' in line:
                    words = line.split()
                    encodingTimes[0] =  words[3]
                elif 'Processing time (user.self):' in line:
                    words = line.split()
                    encodingTimes[1] =  words[3]
                elif 'Processing time (user.children):' in line:
                    words = line.split()
                    encodingTimes[2] =  words[3]
                elif 'Peak memory:' in line:
                    words = line.split()
                    memory[0] =  words[2]

        with open(decLogfile, 'r') as outlogfile:
            for line in outlogfile:
                if 'Processing time (wall):' in line:
                    words = line.split()
                    decodingTimes[0] =  words[3]
                elif 'Processing time (user.self):' in line:
                    words = line.split()
                    decodingTimes[1] =  words[3]
                elif 'Processing time (user.children):' in line:
                    words = line.split()
                    decodingTimes[2] =  words[3]
                elif 'Peak memory:' in line:
                    words = line.split()
                    memory[1] =  words[2]

        if not mmLogfile:
            #print ("TMC2 should be taken")
            with open(encLogfile, 'r') as outlogfile:
                for line in outlogfile:
                    if 'mse1,PSNR (p2point):' in line:
                        words = line.split()
                        results[0][0] += float(words[2])
                    elif 'mse2,PSNR (p2point):' in line:
                        words = line.split()
                        results[0][1] += float(words[2])
                    elif 'mseF,PSNR (p2point):' in line:
                        words = line.split()
                        results[0][2] += float(words[2])
                    elif 'mse1,PSNR (p2plane):' in line:
                        words = line.split()
                        results[1][0] += float(words[2])
                    elif 'mse2,PSNR (p2plane):' in line:
                        words = line.split()
                        results[1][1] += float(words[2])
                    elif 'mseF,PSNR (p2plane):' in line:
                        words = line.split()
                        results[1][2] += float(words[2])
                    elif 'c[0],PSNR1'          in line:
                        words = line.split()
                        results[2][0] += float(words[2])
                    elif 'c[0],PSNR2'          in line:
                        words = line.split()
                        results[2][1] += float(words[2])
                    elif 'c[0],PSNRF'          in line:
                        words = line.split()
                        results[2][2] += float(words[2])
                    elif 'c[1],PSNR1'          in line:
                        words = line.split()
                        results[3][0] += float(words[2])
                    elif 'c[1],PSNR2'          in line:
                        words = line.split()
                        results[3][1] += float(words[2])
                    elif 'c[1],PSNRF'          in line:
                        words = line.split()
                        results[3][2] += float(words[2])
                    elif 'c[2],PSNR1'          in line:
                        words = line.split()
                        results[4][0] += float(words[2])
                    elif 'c[2],PSNR2'          in line:
                        words = line.split()
                        results[4][1] += float(words[2])
                    elif 'c[2],PSNRF'          in line:
                        words = line.split()
                        results[4][2] += float(words[2])
            if nbFrame != 0:
                results[0][2] = results[0][2]/nbFrame
                results[1][2] = results[1][2]/nbFrame
                results[2][2] = results[2][2]/nbFrame
                results[3][2] = results[3][2]/nbFrame
                results[4][2] = results[4][2]/nbFrame                
            
        else:
            #print ("mm should be taken")
            with open(mmLogfile, 'r') as mmlogfile:
                for line in mmlogfile:
                    if 'mseF, PSNR(p2point) Mean=' in line:
                        words = line.split("=")
                        results[0][2] = float(words[1])
                    elif 'mseF, PSNR(p2plane) Mean=' in line:
                        words = line.split("=")
                        results[1][2] = float(words[1])
                    elif 'c[0],PSNRF          Mean=' in line:
                        words = line.split("=")
                        results[2][2] = float(words[1])
                    elif 'c[1],PSNRF          Mean=' in line:
                        words = line.split("=")
                        results[3][2] = float(words[1])
                    elif 'c[2],PSNRF          Mean=' in line:
                        words = line.split("=")
                        results[4][2] = float(words[1])
                    elif 'PCQM Mean=' in line:
                        words = line.split("=")
                        results[6][0] = float(words[1])
                    elif 'PCQM-PSNR Mean=' in line:
                        words = line.split("=")
                        results[6][1] = float(words[1])
          
    except FileNotFoundError:
        print(utils.RED + "FileNotFoundError Exception:",encLogfile, "or", decLogfile, utils.ENDC)
        return None
    
    return results, total, metadata, geometry, attribute, nbFrame, encodingTimes, decodingTimes, memory

def printMetrics(results, total, metadata, geometry, attribute, nbFrame, encodingTimes, decodingTimes, memory):
    
    print("\tframe number            =",nbFrame);
    print("\ttotal (in bits)         =",total*8);    
    print("\tgeometry (in bits)      =",geometry*8);
    print("\tmetadata (in bits)      =",metadata*8);
    print("\tattribute (in bits)     =",attribute*8);
    print("\tPoint 2 Point (PSNR)    = {:.7f}".format(results[0][2]));
    print("\tPoint 2 Plane (PSNR)    = {:.7f}".format(results[1][2]));
    print("\tc[0]          (PSNR)    = {:.7f}".format(results[2][2]));
    print("\tc[1]          (PSNR)    = {:.7f}".format(results[3][2]));
    print("\tc[2]          (PSNR)    = {:.7f}".format(results[4][2]));
    print("\tPCQM                    = {:.7f}".format(results[6][0]));
    print("\tPCQM          (PSNR)    = {:.7f}".format(results[6][1]));
    print("\tNumPtOrg                =",results[5][0]);
    print("\tNumPtDec                =",results[5][1]);
    print("\tMeanDup                 =",results[5][2]);
    print("\tEncTime (wall)          =",encodingTimes[0]);
    print("\tEncTime (user.self)     =",encodingTimes[1]);
    print("\tEncTime (user.children) =",encodingTimes[2]);
    print("\tDecTime (wall)          =",decodingTimes[0]);
    print("\tDecTime (user.self)     =",decodingTimes[1]);
    print("\tDecTime (user.children) =",decodingTimes[2]);
    print("\tPeakPeakEncoderMemory   =",memory[0]);
    print("\tPeakDecoderMemory       =",memory[1]);

def writeCsv(strSeq, condition, strRate, results, total, metadata, geometry, attribute, nbFrame, encodingTimes, decodingTimes, memory, bitrate, geoQP, attQP, occPrec, csvFile):
    #print("Metrics written to    :",csvFile)
    if not os.path.isfile(csvFile):
        header = ['SeqId', 'CondId', 'RateId', 'nbFrame', 'NbInputPoints', 'NbOutputPoints', 'MeanOutputPoints', 'MeanDuplicatePoints', 'TotalBitstreamBits', 'geometryBits', 'metadataBits', 'attributeBits', 'D1Mean', 'D2Mean', 'LumaMean', 'CbMean', 'CrMean', 'PCQM', 'SelfEncoderRuntime', 'ChildEncoderRuntime', 'SelfDecoderRuntime', 'ChildDecoderRuntime', 'bitrate', 'geoQP', 'attQP', 'occPrec']
        with open(csvFile, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(header)
    
    strResults = [strSeq, condition, strRate, nbFrame, results[5][0], results[5][1], results[5][1]/nbFrame, results[5][2]/nbFrame, total*8, geometry*8, metadata*8, attribute*8, results[0][2], results[1][2], results[2][2], results[3][2], results[4][2], results[6][1], encodingTimes[1], encodingTimes[2], decodingTimes[1], decodingTimes[2], bitrate, geoQP, attQP, occPrec]
    with open(csvFile, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(strResults)   

##################
if __name__ == "__main__":
    try:

        # Parse arguments
        args = parseArgs()
        if len(sys.argv)==1:
            parser.print_help(sys.stderr)
            raise ValueError("bad arguments")
        utils.printArgs(args)

        # Check options
        if not os.path.exists(args.encoderFile) :
            raise ValueError("Check file :", args.encoderFile)
        if not os.path.exists(args.decoderFile) :
            raise ValueError("Check file :", args.decoderFile)
        if not os.path.exists(args.mmFile) :
            raise ValueError("Check file :", args.mmFile)
                    
        plt = platform.system()
        if plt == "Windows":
            print(utils.BLUE + "Your system is Windows", utils.ENDC)
        elif plt == "Linux":
            print(utils.BLUE + "Your system is Linux", utils.ENDC)
        else:
            raise ValueError("Your system is not supported")

        # METRICS
        
        # metrics from TMC2 log files
        print (utils.GREEN  + "TMC2 Metrics only", args.encoderFile, "and", args.decoderFile, utils.ENDC, flush=True)        
        [results, total, metadata, geometry, attribute, nbFrame, encodingTimes, decodingTimes, memory] = extract_metrics(args.encoderFile, args.decoderFile)
        printMetrics(results, total, metadata, geometry, attribute, nbFrame, encodingTimes, decodingTimes, memory)
                
        # metrics from TMC2 and mm log files
        print (utils.GREEN  + "TMC2 and MM Metrics on", args.encoderFile, ",", args.decoderFile, "and", args.mmFile, utils.ENDC, flush=True)        
        [results, total, metadata, geometry, attribute, nbFrame, encodingTimes, decodingTimes, memory] = extract_metrics(args.encoderFile, args.decoderFile, args.mmFile)
        printMetrics(results, total, metadata, geometry, attribute, nbFrame, encodingTimes, decodingTimes, memory)
        
    except Exception as e:
        print (utils.RED + "Exception:", e, utils.ENDC)
        sys.exit(e.returncode)
    except subprocess.CalledProcessError as e:
        print(utils.RED + "subprocess Exception:", e.returncode, utils.ENDC)
        print(utils.RED + e.cmd, utils.ENDC)
        print(utils.RED + e.output, utils.ENDC)        
        sys.exit(e.returncode)        
