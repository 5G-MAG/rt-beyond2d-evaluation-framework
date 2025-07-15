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
from pathlib import Path
import subprocess
#local
import compute as metrics
commonDir = Path(__file__).resolve(strict=True).parent.joinpath("../common")
sys.path.append(str(Path(commonDir)))
import utils as utils

def parseArgs():
    global parser
    parser = argparse.ArgumentParser(description='encode quantized point cloud files using TMC2 reference software (V-PCC), decode and compute metrics')
    parser.add_argument('-s', '--seq',         help="Output sequence Number (default=58)", default="58", type=str, required=True)
    parser.add_argument(      '--seqCfgFile',  help="Path to sequence cfg file given as input to TMC2", type=str, required=True)
    parser.add_argument(      '--name',        help="Output test name", type=str, required=True)
    parser.add_argument('-i', '--inputDir',    help="Input PLY directory (optional)", nargs="?", type=str, required=True)
    parser.add_argument('-o', '--outputDir',   help="Output BIN directory", default="tmp", type=str, required=True)
    parser.add_argument('-n', '--frameNumber', help="Number of frames to process (optional, default=1, 1000 corresponds to all frames in inputDir)", nargs="?", default="1", type=int)
    parser.add_argument('-r', '--rate',        help="Compression rate index (for naming output)", nargs="?", default="5", type=int)
    parser.add_argument(      '--condition',   help="Condition AI (all Intra) or RA (Random Access) (optional, default=RA)", nargs="?", default="RA", type=str, choices=["RA","AI"])
    parser.add_argument(      '--nbThreads',   help="Number of thread to use (optional, default=1)", nargs="?", default="1", type=int)
    parser.add_argument(      '--tmc2Dir',     help="Path to TMC2 reference software", nargs="?", type=str, required=True)
    parser.add_argument(      '--mmDir',       help="Path to mpeg-pcc-mmetric tools (optional, default=c:/code/MPEG/mpeg-pcc-mmetric)", required=True, type=str)
    parser.add_argument(      '--forceEncode', help="Force the encoding (optional, default=False)", nargs="?", default=False, const=True, type=utils.str2bool)
    parser.add_argument(      '--forceDecode', help="Force the decoding (optional, default=False)", nargs="?", default=False, const=True, type=utils.str2bool)
    parser.add_argument(      '--forceMetric', help="Force the metric computation  (optional, default=False)", nargs="?", default=False, const=True, type=utils.str2bool)
    parser.add_argument(      '--forceClean',  help="Force the clean of decoded PLY (optional, default=False)", nargs="?", default=False, const=True, type=utils.str2bool)
    parser.add_argument(      '--testName',    help="Set test Name", nargs="?", required=True, type=str)
    parser.add_argument(      '--encOptions',  help="Option to set to the encoder (optional, default="")", nargs="?", default="", type=str)
    return parser.parse_args()

def getConditionFileName(condition):
    condInfo = {
    'RA':"ctc-random-access.cfg",
    'AI':"ctc-all-intra.cfg"
    }
    return condInfo[condition]

def isEncodeProcessSuccess(compressBinFile, encoderFile):
    if encoderFile.exists():
        with open(encoderFile, 'r') as file:
            content = file.read()
            if 'Processing time (wall):' in content:
                isSuccess = True
            else:
                isSuccess = False

    if compressBinFile.exists() and isSuccess == True:
        return True
    else:
        return False

def isDecodeProcessSuccess(decoderFile):
    if decoderFile.exists():
        with open(decoderFile, 'r') as file:
            content = file.read()
            if 'Processing time (wall):' in content:
                return True
            else:
                return False

def isMetricProcessSuccess(mmFile):
    if mmFile.exists():
        with open(mmFile, 'r') as file:
            content = file.read()
            if 'Time on overall processing:' in content:
                return True
            else:
                return False

def extract_ply_header(file_path):
    header_lines = []
    with open(file_path, 'r') as file:
        for line in file:
            header_lines.append(line)
            if line.strip() == "end_header":
                break
    return ''.join(header_lines)

def extract_binary_ply_header(file_path):
    header = bytearray()
    with open(file_path, 'rb') as file:
        while True:
            byte = file.read(1)
            if not byte:
                break  # Reach end of file
            header.append(byte[0])        
            # Check if header contains "end_header"
            if header[-10:] == b'end_header':
                break
    # Decode header in Ascii
    header_str = header.decode('ascii', errors='ignore')
    return header_str

def hasNormals(plyFile, start):
    fisrtFile = str(plyFile).replace("%04d", '%0*d' % (4, start), 1)
    try:
        header = extract_binary_ply_header(fisrtFile)
    except UnicodeDecodeError:
        header = extract_ply_header(fisrtFile)
    if "nx" in header :
        normalsPresent = True
    else:
        normalsPresent = False   
    return normalsPresent    
    
def main():
    try:
        # Parse arguments
        args = parseArgs()
        if len(sys.argv)==1:
            parser.print_help(sys.stderr)
            raise ValueError("bad arguments")
        
        print("encOptions" , args.encOptions)
        utils.printArgs(args)
        
        scriptDir = Path(__file__).resolve(strict=True)
        inputDir  = Path(args.inputDir).resolve(strict=True)    
        outputDir = Path(args.outputDir).resolve()
        tmc2Dir   = Path(args.tmc2Dir).resolve()
        mmDir     = Path(args.mmDir).resolve()
        
        # check options
        
        frameNumber = args.frameNumber
        if (args.frameNumber == 1000):
            frameNumber = len(glob.glob1(inputDir,"*.ply"))
            
        plt = platform.system()
        if plt == "Windows":
            print(utils.BLUE + "Your system is Windows", utils.ENDC)
            encoder=Path(tmc2Dir).joinpath("bin", "Release", "PccAppEncoder.exe")
            decoder=Path(tmc2Dir).joinpath("bin", "Release", "PccAppDecoder.exe")
            mm=Path(mmDir).joinpath("build", "Release", "bin", "Release", "mm.exe")
        elif plt == "Linux":
            print(utils.BLUE + "Your system is Linux", utils.ENDC)
            encoder=Path(tmc2Dir).joinpath("bin", "PccAppEncoder")
            decoder=Path(tmc2Dir).joinpath("bin", "PccAppDecoder")
            mm=Path(mmDir).joinpath("build", "Release", "bin", "mm")
        else:
            raise ValueError("Your system is not supported")
        
        if not encoder.exists():
            raise ValueError("Exe not found : ", encoder)
        if not decoder.exists():
            raise ValueError("Exe not found : ", decoder)
        if not mm.exists():
            raise ValueError("Exe not found : ", mm)
        
        #search info in Sequence cfg file
        with open(args.seqCfgFile) as f:
            for line in f:
                if "startFrameNumber" in line:
                    startFrameNb = int(line.split(":")[1])
                if "uncompressedDataPath" in line:
                    uncompressedDataPath = str(line.split(":")[1]).strip()
                if "geometry3dCoordinatesBitdepth" in line:
                    resolution = 1023 if int(line.split(":")[1]) == 10 else 2047
                
        #testName        = "".join(["S", args.seq, "_F", str(frameNumber), "_", args.profileName])
        testName        = "".join(["F", str(frameNumber), "_", args.testName])
        testDir         = "".join(["S", args.seq, "C2", args.condition, "_", args.name])
        ## ! outputPrefix shall be the same than in XlsSheetGenerator.py named "outputPrefix"
        outputPrefix    = "".join(["S", args.seq, "C2", args.condition, "R%04d" % args.rate, "_", args.name]);
        compressedPath  = Path(outputDir).joinpath(testName, testDir)
        cmdFile         = Path(compressedPath).joinpath("".join([outputPrefix, "_command.log"]))
        encoderFile     = Path(compressedPath).joinpath("".join([outputPrefix, "_encoder.log"]))
        decoderFile     = Path(compressedPath).joinpath("".join([outputPrefix, "_decoder.log"]))
        mmFile          = Path(compressedPath).joinpath("".join([outputPrefix, "_mm.log"]))
        compressBinFile = Path(compressedPath).joinpath("".join([outputPrefix, "_enc.bin"]))
        plyDecPath      = Path(compressedPath).joinpath("".join([outputPrefix, "_dec_%04d.ply"]))
        #csvFile         = Path(outputDir).joinpath(testName, "".join([testName, "_metrics.csv"]))
        plySourcePath   = Path(inputDir).joinpath(uncompressedDataPath)
        #detect if source had normals
        if hasNormals(plySourcePath, startFrameNb):
            nrmSourcePath   = Path(inputDir).joinpath(uncompressedDataPath)
        else:
            nrmSourcePath   = ""
        
        #print("output encoderFile =", encoderFile, flush=True)
        #print("output decoderFile =", decoderFile, flush=True)
        #print("output mmFile      =", mmFile, flush=True)
        isEncodeDone = isEncodeProcessSuccess(compressBinFile, encoderFile)
        isDecodeDone = isDecodeProcessSuccess(decoderFile)
        isMetricDone = isMetricProcessSuccess(mmFile)
        
        print("mmFile=", mmFile, "isMetricDone=", isMetricDone)
        
        #create outputDir if does not exist
        if not compressedPath.exists():
            print("create dir:", compressedPath, flush=True);
            os.makedirs(compressedPath, exist_ok=True)
        
        # used to force decoding and metric computation if something change
        isEncodedProcessDone = False
        isDecodedProcessDone = False
        isMetricsProcessDone = False
        
        # ENCODER
        if not isEncodeDone or args.forceEncode:
            print (utils.GREEN  + "Encode: ", compressBinFile,  utils.ENDC, flush=True)
            config = "".join(
                        [
                        " --config=", str(Path(tmc2Dir).joinpath("cfg", "common", "ctc-common.cfg")),
                        " --config=", str(Path(tmc2Dir).joinpath("cfg", "condition", getConditionFileName(args.condition))),
                        " --config=", str(args.seqCfgFile),
                        #" --config=", str(Path(tmc2Dir).joinpath("cfg", "rate", "".join(["ctc-r", str(args.rate), ".cfg"]))),
                        " --configurationFolder=", str(Path(tmc2Dir).joinpath("cfg")),os.sep,
                        " --uncompressedDataFolder=", str(inputDir), os.sep,
                        " --compressedStreamPath=", str(compressBinFile),
                        " --normalDataPath=", str(nrmSourcePath),
                        " --nbThread=", str(args.nbThreads),                                                   
                        " --frameCount=", str(frameNumber),                                                 
                        " --resolution=", str(resolution),
                        " ", str(args.encOptions),
                        " > ", str(encoderFile)
                        ])
        
            cmd = " ".join([str(encoder), config]) 
            f = open(cmdFile,'w')
            print(cmd, file=f) 
            print("CMD=", cmd)
            f.close()        
            subprocess.check_call(cmd, shell=True)
            encodingProcessDone = True
        
        else:
            print (utils.GREEN  + "Already encoded: ",compressBinFile,  utils.ENDC, flush=True)
        
        # DECODER  
        if not isDecodeDone or args.forceDecode or isEncodedProcessDone:      
        #if (len(glob.glob1(compressedPath,"".join([outputPrefix,"*.ply"]))) != frameNumber) or args.forceDecode:
            print (utils.GREEN  + "Decode", compressBinFile, utils.ENDC, flush=True)
        
            config = "".join(
                        [" --startFrameNumber=", str(startFrameNb),
                        " --compressedStreamPath=", str(compressBinFile),
                        " --reconstructedDataPath=", str(plyDecPath),
                        " --inverseColorSpaceConversionConfig=", str(Path(tmc2Dir).joinpath("cfg", "hdrconvert", "yuv420toyuv444_16bit.cfg")),
                        " --nbThread=1 > ", str(decoderFile)])
            cmd = " ".join([str(decoder), config]) 
            f = open(cmdFile,'a')
            print(cmd, file=f) 
            f.close()
            subprocess.check_call(cmd, shell=True)
            isDecodedProcessDone = True
        else:
            print (utils.GREEN  + "Already decoded: ",compressBinFile,  utils.ENDC, flush=True)
        
        # METRICS
        if not isMetricDone or args.forceMetric or isEncodedProcessDone or isDecodedProcessDone:
                        
            print (utils.GREEN  + "Compute Metrics", plySourcePath, "versus", plyDecPath, utils.ENDC, flush=True)
            config = "".join(
                        ["sequence --firstFrame ", str(startFrameNb), " --lastFrame ", str(startFrameNb+frameNumber-1), " END ",
                         "compare --mode pcc  --inputModelA ", str(plySourcePath), " --inputModelB ", str(plyDecPath), " END ",
                         "compare --mode pcqm --inputModelA ", str(plySourcePath), " --inputModelB ", str(plyDecPath), " > ", str(mmFile)])
            cmd = " ".join([str(mm), config]) 
            f = open(cmdFile,'a')
            print(cmd, file=f) 
            f.close()
            subprocess.check_call(cmd, shell=True)
                                    
            isMetricsProcessDone = True
            
        else:
            print (utils.GREEN  + "Already metric done: ",compressBinFile,  utils.ENDC, flush=True)        
        
        if args.forceClean:
            print (utils.GREEN  + "Remove decoded PLY in : ", compressedPath, "containing : ", outputPrefix, utils.ENDC, flush=True)            
            for plyfile in os.listdir(compressedPath):
                if plyfile.endswith("ply") and outputPrefix in plyfile:
                    if Path(compressedPath).joinpath(plyfile).exists():
                        os.remove(Path(compressedPath).joinpath(plyfile))

        # keep this print line to be able to retreive log files
        print (utils.GREEN  + "Process is done.", utils.ENDC, flush=True)
                                   
    except Exception as e:
        print (utils.RED + "Exception:", e, utils.ENDC, flush=True)
        sys.exit(e.returncode)
    except subprocess.CalledProcessError as e:
        print(utils.RED + "subprocess Exception:", e.returncode, utils.ENDC, flush=True)
        print(utils.RED + e.cmd, utils.ENDC, flush=True)
        print(utils.RED + e.output, utils.ENDC, flush=True)        
        sys.exit(e.returncode)


##################
if __name__ == "__main__":
    
    main()

