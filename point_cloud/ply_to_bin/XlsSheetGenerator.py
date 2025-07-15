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
import traceback, subprocess, sys, argparse, os, fnmatch
from pathlib import Path, PurePath

commonDir = Path(__file__).resolve(strict=True).parent.joinpath("../common")
sys.path.append(str(Path(commonDir)))
import utils as utils


import ExtractMetrics as metrics
import FillSpreadsheet as fillSpeadsheet

class XlsSheetGenerator:

    def __init__ (self, config_manager, test=None):
        
        self.config_manager = config_manager
        self.cmd = utils.pathStr(Path(config_manager.scriptDir).joinpath("compute.py"))
       
        self.argList   = []
        self.encParams = []

    def run(self):
        for test in self.config_manager.testConfigData['TestList']:
            profile = test['Profile']
            seqList = test['SeqList']
            nbTests, nbSuccess = self.config_manager.getTestResults(profile, seqList)
            forceMetrics = True
            
            # create CSV
            self.csvFileList = []
            if nbTests == nbSuccess or forceMetrics:
                sIdx, fIdx, rIdx = self.csvCreate(profile, seqList)
            
            # file XLSM sheet (this only works if we got 5 rates per sequence per profile)
            if nbSuccess == (sIdx+1)*(rIdx+1)*(fIdx+1): # number to fill per profile = 5 sequences * 5 rates minimum
                self.createWorkbook(profile, seqList)
            else:
                print(utils.RED, "Cannot generate workbook Profile", f"{profile:10}", "nbTest= ", nbTests, "nbSuccess= ", nbSuccess, "Tests on going or failed", utils.ENDC)

    def buildCsvFileMetrics(self, profile, seqId, condition, rate, fps, geoQP, attQP, occPrec, encoderFile, decoderFile, mmFile, csvFile, csvFileTmc2):
            
        if encoderFile and decoderFile and mmFile:
            [results, total, metadata, geometry, attribute, nbFrame, encodingTimes, decodingTimes, memory] = metrics.extract_metrics(encoderFile, decoderFile, mmFile)
            #print("MM METRICS", seqId, condition, rate, geoQP, attQP, occPrec)
            #metrics.printMetrics(results, total, metadata, geometry, attribute, nbFrame, encodingTimes, decodingTimes, memory)

            # Write into CSV file
            strSeq="".join(["S", str(seqId)])
            strRate="".join(["R%02d" % rate])       
            #print("CSV File :", csvFile)
            bitrate = int(total)*8 * int(fps) / int(nbFrame) / 1000000
            #print(profile, strSeq, strRate, "geoQP", geoQP, "attQP", attQP, "occPrec", occPrec, "rate", bitrate, "Mbps")
            
            #print (f"{profile:10}", f"S{int(seqId):02}", f"F{int(nbFrame):03}", " C2", condition, f"R{int(rate):04}","geoQP", geoQP, "attQP", attQP, "occPrec", occPrec, "rate", bitrate, "Mbps")
            metrics.writeCsv(strSeq, "".join(["C2", condition]), strRate, results, total, metadata, geometry, attribute, nbFrame, encodingTimes, decodingTimes, memory, bitrate, geoQP, attQP, occPrec, str(csvFile))
            
            # [results, total, metadata, geometry, attribute, nbFrame, encodingTimes, decodingTimes, memory] = metrics.extract_metrics(encoderFile, decoderFile)
            # print("TMC2 METRICS", seqId, condition, rate, geoQP, attQP, occPrec)
            # metrics.printMetrics(results, total, metadata, geometry, attribute, nbFrame, encodingTimes, decodingTimes, memory)
            # 
            # # Write into CSV file
            # strSeq="".join(["S", str(seqId)])
            # strRate="".join(["R%02d" % rate])       
            # #print("CSV File :", csvFile)
            # bitrate = int(total)*8 * int(fps) / int(nbFrame) / 1000000
            # #print(profile, strSeq, strRate, "geoQP", geoQP, "attQP", attQP, "occPrec", occPrec, "rate", bitrate, "Mbps")
            # print (f"{profile:10}", f"S{int(seqId):02}", f"F{int(nbFrame):03}", " C2", condition, f"R{int(rate):04}","geoQP", geoQP, "attQP", attQP, "occPrec", occPrec, "rate", bitrate, "Mbps")
            # metrics.writeCsv(strSeq, "".join(["C2", condition]), strRate, results, total, metadata, geometry, attribute, nbFrame, encodingTimes, decodingTimes, memory, bitrate, geoQP, attQP, occPrec, str(csvFileTmc2))

    def csvCreate(self, profile, seqList):

        # remove previous csv file for that test
        extension = '*.csv'
        search_string = PurePath(self.config_manager.testConfigJson).stem
        for root, dirs, files in os.walk(self.config_manager.outputDir):
            for filename in files:
                if fnmatch.fnmatch(filename, extension) and search_string in filename:
                    file_path = os.path.join(root, filename)
                    os.remove(file_path)
                    #print(utils.RED, f"File suppressed : {file_path}", utils.ENDC)

        # build CSV 
        for sIdx, seq in enumerate(seqList) :
            seqId     = seq['SeqId']
            condition = seq['Condition']
            rateList  = seq['RateList']
            nbFrameList = seq['FrameNbList']
            for fIdx, nbFrame in enumerate(nbFrameList):
                
                csvFile, csvFileTmc2 = self.config_manager.getCsvPath(fIdx, profile,condition)
                
                for rIdx, rate in enumerate(rateList):
                    rateId  = rate['RateId']
                    geoQP   = rate['geometryQP']
                    attQP   = rate['attributeQP']
                    occPrec = rate['occupancyPrecision']                            

                    name, fps, config, ply, maxNbFrame = self.config_manager.getSequenceInfo(seqId, self.config_manager.sequenceData)
                    
                    effectiveNbFrame = nbFrame
                    if maxNbFrame < int(nbFrame):
                        #print (utils.RED, "available:", maxNbFrame, " asked:", nbFrame, utils.ENDC)
                        effectiveNbFrame = maxNbFrame                                
                    
                    encoderLogFile, decoderLogFile, mmLogFile = self.config_manager.getLogFiles(profile, seqId, str(effectiveNbFrame), condition, rateId, name)
                    
                    self.buildCsvFileMetrics(profile, seqId, condition, rateId, fps, geoQP, attQP, occPrec, encoderLogFile, decoderLogFile, mmLogFile, csvFile, csvFileTmc2)                
                    csvFileInit = True
                    

                if csvFile not in self.csvFileList:
                    self.csvFileList.append(csvFile)
        return sIdx, fIdx, rIdx

    def createWorkbook(self, profile, seqList):

        sourceXlsm=Path(self.config_manager.scriptDir).joinpath("templates", "".join(["FALL_3GPP_template.xlsm"])).resolve(strict=True)

        for sIdx, seq in enumerate(seqList) :
            self.workbookList = []
            nbFrameList = seq['FrameNbList']
            condition   = seq['Condition']
            rateList    = seq['RateList']
            for idx, csvFile in enumerate(self.csvFileList):
                outputXlsm = self.config_manager.getWorkbookPath(idx, profile, condition)
                if csvFile.exists() :
                    #print("Fill workbook : ",str(outputXlsm))
                    fillSpeadsheet.fillXlsm( str(sourceXlsm), str(outputXlsm), str(csvFile), int(nbFrameList[idx]), len(seqList), len(rateList) )
                    if outputXlsm not in self.workbookList:
                        self.workbookList.append(str(outputXlsm))
                else:
                    print(utils.RED,"check csv ", csvFile, utils.ENDC)
        print(utils.GREEN, "Generate Workbook : Profile", f"{profile:10}\n", utils.ENDC, "\n".join(self.workbookList), sep='')
    
    def startLocalTask(self, cmdArgs, encParams):
        cmd = self.buildCmd(cmdArgs, encParams)
        print(cmd)
        print("running subprocess\n", flush=True)
        subprocess.run(cmd)
        print()

def parseArgs():
    global parser
    parser = argparse.ArgumentParser(description='Call "decoder.sh" script for all vpcc streams in tests.json ')
    parser.add_argument(      '--testJson',     help="Json that contains the test to be done", type=str, default="test.json", nargs="?")
    parser.add_argument(      '--confJson',     help="Json that contains the configuration", type=str, default="config.json", nargs="?")
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
        
        cm = ConfigManager(args.outputDir, args.inputJson, 0)
       
    except Exception as e:
        print(utils.RED, traceback.format_exc())
        print ("Exception:", e, utils.ENDC)
        sys.exit();

