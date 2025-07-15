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

import traceback, shutil, sys, argparse, json
from pathlib import Path

commonDir = Path(__file__).resolve(strict=True).parent.joinpath("../common")
sys.path.append(str(Path(commonDir)))
import utils
import install_deps 

class ConfigManager:

    def __init__ (self, outDir, sequenceJson, testConfigJson, verbose=None):

        self.verbose = verbose or 0
        
        # ############# #
        # SET UP CONFIG #
        # ############# #

        #save input parameters
        self.outputDir    = Path(outDir).resolve()
        self.sequenceJson = Path(sequenceJson).resolve(strict=True)
        self.testConfigJson = Path(testConfigJson).resolve(strict=True)
                
        self.scriptDir    = Path(__file__).parent
        
        #install dependencies
        self.tmc2Dir  = install_deps.buildDepsTmc2(self.outputDir)
        self.mmDir  = install_deps.buildDepsMmetric(self.outputDir)

        # copy sequence configuration files
        shutil.copytree(Path(self.scriptDir).parent.joinpath("external_data","sequence_cfg"), Path(self.tmc2Dir).joinpath("cfg", "sequence"), dirs_exist_ok=True)
        
        # create directory to store command log, scripts
        self.cmdDir = Path(self.outputDir).joinpath("cmd")
        
        ####################################
        # READ AND FORMAT INPUT PARAMETERS #
        ####################################

        #read sequence JSON files
        with open(sequenceJson, 'r') as file:
            self.sequenceData = json.load(file)

        #read test config JSON files
        with open(testConfigJson, 'r') as file:
            self.testConfigData = json.load(file)

        
        #  #read config JSON file
        #  with open(self.confJsonPath, 'r') as conf_file:
        #      self.confData = json.load(conf_file)
        #  
        #  #self.printConfig()
        #  self.buildInputInfo()
        #  
        #  # create directory to store command log, scripts
        #  self.cmdDir = utils.createPath(Path(self.outputDir).joinpath("cmd"))
        
        
    def buildInputInfo(self):
        self.inputList = []
        index = 0
        for idx, item in enumerate(self.confData['TestList']):
            myDict = {'seqId':0, 'name':'', 'qp':11, 'ratio':1, 'meshObjPath':'', 'meshTxtPath':'', 'firstFrameId':0, 'nbFrame':1, 'outputDir':'', 'outputFormat':''}
            
            myDict['seqId']        = int(self.confData['TestList'][idx]['SeqId'])
            myDict['name']         = self.confData['TestList'][idx]['Name']
            myDict['qp']           = self.confData['TestList'][idx]['Qp']
            myDict['ratio']        = self.confData['TestList'][idx]['Ratio']
            myDict['firstFrameId'] = self.confData['TestList'][idx]['FirstFrameId']
            myDict['nbFrame']      = self.confData['TestList'][idx]['NbFrame']
            myDict['meshObjPath']  = utils.tryRelativePath(Path(self.confData['TestList'][idx]['MeshObjPath']), self.outputDir)
            myDict['meshTxtPath']  = utils.tryRelativePath(Path(self.confData['TestList'][idx]['MeshTxtPath']), self.outputDir)

            prefix                 = "".join(["F", str(self.confData['TestList'][idx]['NbFrame']), "_quantized_vox", str(self.confData['TestList'][idx]['Qp']), "_r", str(self.confData['TestList'][idx]['Ratio'])])
            myDict['outputDir']    = Path(self.outputDir).joinpath(self.confData['TestList'][idx]['OutputDir'], prefix)
            myDict['outputFormat'] = self.confData['TestList'][idx]['OutputFormat']  

            self.inputList.append(myDict)


    def printConfig(self):
        if (self.verbose):
            print (utils.RED + "CONFIG from file ", self.confJsonPath, " :" )
            for key, value in self.confData.items():
                print("\t", key, " = ", value)
            print (utils.ENDC)

    def getCsvPath(self, fIdx, profile, condition):
        csvFile     = self.outputDir.joinpath("".join(["FiDx", str(fIdx), "_", profile, "_C2", condition ,"_", Path(self.testConfigJson).stem, "_metrics.csv"]))
        csvFileTmc2 = self.outputDir.joinpath("".join(["FiDx", str(fIdx), "_", profile, "_C2", condition ,"_", Path(self.testConfigJson).stem, "_metrics_tmc2.csv"]))
        return csvFile, csvFileTmc2                

    def getWorkbookPath(self, fIdx, profile, condition):
        return self.outputDir.joinpath("".join([ "FiDx", str(fIdx), "_", profile, "_C2", condition , "_", Path(self.testConfigJson).stem, ".xlsm"]))

    def getJobName(self, profile, seqId, nbFrame, testName):
        return "".join([profile, "_S", str(seqId), "_F", str(nbFrame), "_", testName])
        
    def getSequenceInfo(self, seqId, jsonData):
        name=None
        fps=None
        cfg=None
        ply=None
        maxNbFrame=0
        for idx, item in enumerate(jsonData['SequenceList']):
            if item['SeqId'] == int(seqId):
                name = jsonData['SequenceList'][idx]['Name']
                fps  = jsonData['SequenceList'][idx]['Fps']
                cfg  = jsonData['SequenceList'][idx]['Config']
                ply  = utils.tryRelativePath(Path(jsonData['SequenceList'][idx]['PlyPath']), self.outputDir)

        seqCfgFile = Path(str(self.tmc2Dir), "cfg", "sequence", cfg).resolve(strict=True)  
        with open(seqCfgFile) as f:
            for line in f:
                if "frameCount" in line:
                    maxNbFrame = int(line.split(":")[1])

        return name, fps, cfg, ply, maxNbFrame            

    def getCompressedFilePath(self, profile, seqId, nbFrame, condition, name):
        testName        = "".join(["F", nbFrame, "_", profile])
        testDir         = "".join(["S", seqId, "C2", condition, "_", name])
        compressedPath  = self.outputDir.joinpath(testName, testDir)
        return (compressedPath)

    def getOutputPrefix(self, seqId, nbFrame, condition, rate, name):
        ## ! outputPrefix shall be the same than in compute.py named "outputPrefix"
        outputPrefix    = "".join(["S", seqId, "C2", condition, "R%04d" % int(rate), "_", str(name)]);
        return outputPrefix

    def getLogFiles(self, profile, seqId, nbFrame, condition, rate, name):
        compressedPath  = self.getCompressedFilePath(profile, str(seqId), nbFrame, condition, name)
        outputPrefix    = self.getOutputPrefix(str(seqId), nbFrame, condition, str(rate), name)
        encoderLogFile  = compressedPath.joinpath("".join([outputPrefix, "_encoder.log"]))    
        decoderLogFile  = compressedPath.joinpath("".join([outputPrefix, "_decoder.log"]))  
        mmLogFile       = compressedPath.joinpath("".join([outputPrefix, "_mm.log"]))

        if not encoderLogFile.exists():
            encoderLogFile = ""
        if not decoderLogFile.exists():
            decoderLogFile = ""
        if not mmLogFile.exists():
            mmLogFile = ""
        return encoderLogFile, decoderLogFile, mmLogFile  

    def taskIsSuccess(self, forceEnc, forceDec, forceMet, encoderLogFile, decoderLogFile, mmLogFile):
        isEncoded = self.isEncodeProcessSuccess(Path(encoderLogFile))
        isDecoded = self.isDecodeProcessSuccess(Path(decoderLogFile))
        isMetrics = self.isMetricProcessSuccess(Path(mmLogFile))

        if forceEnc or forceDec or forceMet:
            isSuccess = False
        elif isEncoded and isDecoded and isMetrics :
            isSuccess = True
        else:
            isSuccess = False
        
        return isSuccess, isEncoded, isDecoded, isMetrics

    def isEncodeProcessSuccess(self, encoderFile):
        if encoderFile.is_file():
            with open(encoderFile, 'r') as file:
                content = file.read()
                if 'Processing time (wall):' in content:
                    return True
                else:
                    return False
        else:
            return False

    def isDecodeProcessSuccess(self, decoderFile):
        if decoderFile.is_file():
            with open(decoderFile, 'r') as file:
                content = file.read()
                if 'Processing time (wall):' in content:
                    return True
                else:
                    return False
        else:
            return False

    def isMetricProcessSuccess(self, mmFile):
        if mmFile.is_file():
            with open(mmFile, 'r') as file:
                content = file.read()
                if 'Time on overall processing:' in content:
                    return True
                else:
                    return False
        else:
            return False

    def getTestResults(self, profile, seqList):
        nbTests   = 0
        nbSuccess = 0        
        for sIdx, seq in enumerate(seqList) :
            seqId     = seq['SeqId']
            condition = seq['Condition']
            rateList  = seq['RateList']
            nbFrameList = seq['FrameNbList']
            
            for fIdx, nbFrame in enumerate(nbFrameList):  

                for rIdx, rate in enumerate (rateList) :
                    rateId  = rate['RateId']                       
                    name, fps, config, ply, maxNbFrame = self.getSequenceInfo(seqId, self.sequenceData)
                    
                    effectiveNbFrame = nbFrame
                    if maxNbFrame < int(nbFrame):
                        #print (frameworkUtils.RED, "available:", maxNbFrame, " asked:", nbFrame, frameworkUtils.ENDC)
                        effectiveNbFrame = maxNbFrame 

                    nbTests+=1
                    encoderLogFile, decoderLogFile, mmLogFile  = self.getLogFiles(profile, seqId, str(effectiveNbFrame), condition, rateId, name)
                    isSuccess, isEncoded, isDecoded, isMetrics = self.taskIsSuccess(False, False, False, encoderLogFile, decoderLogFile, mmLogFile)
                    if isSuccess:
                        nbSuccess+=1
                    #print(encoderLogFile, ":", isSuccess, isEncoded, isDecoded, isMetrics)
        
        #print("nbTests=", nbTests, "nbSuccess=", nbSuccess)
        return nbTests, nbSuccess

def parseArgs():
    global parser
    parser = argparse.ArgumentParser(description='Call "decoder.sh" script for all vpcc streams in tests.json ')
    parser.add_argument('-i', '--inputJson', help="Json that contains the input meshes to process", type=str, required=True)
    parser.add_argument('-o', '--outputDir', help="Output PLY directory", type=str, required=True)
    return parser.parse_args()

def printArgs(args):
    print(utils.BLUE + "Argument values:")
    for arg in vars(args):
        print(utils.BLUE + "  - %-20s = %s" % (arg, getattr(args, arg)))
    print (utils.ENDC, flush=True)
   
if __name__ == "__main__":
    try:

        # Parse arguments
        args = parseArgs()
        if len(sys.argv) == 0:
            parser.print_help(sys.stderr)
            sys.exit(1)
        
        cm = ConfigManager(args.outputDir, args.sequenceJson, args.testConfJson, 0)
        #cm.printInputInfo()
        #print("mm path dir = ", cm.getMmExePath())
               
    except Exception as e:
        print(utils.RED, traceback.format_exc())
        print ("Exception:", e, utils.ENDC)
        sys.exit();

