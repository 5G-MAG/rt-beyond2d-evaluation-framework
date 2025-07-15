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
import traceback, subprocess, sys, argparse
from pathlib import Path

commonDir = Path(__file__).resolve(strict=True).parent.joinpath("../common")
sys.path.append(str(Path(commonDir)))
import utils as utils

class BinGenerator:

    def __init__ (self, config_manager, testInfo=None):
        
        self.config_manager = config_manager
        self.cmd = utils.pathStr(Path(config_manager.scriptDir).joinpath("compute.py"))
        
        self.argList   = []
        self.encParams = []

        if (not testInfo==None):
            (seqId, name, fps, config, ply, condition, effectiveNbFrame, 
            rateId, geoQP, attQP, occPrec, forceEnc, forceDec, forceMet, 
            forceClean, testName, encoderParams, threadNb) = testInfo
            self.addTest(seqId, name, fps, config, ply, 
                            condition, effectiveNbFrame, rateId, geoQP, attQP, occPrec, 
                            forceEnc, forceDec, forceMet, forceClean, 
                            testName, encoderParams, threadNb)
        else:
            for test in self.config_manager.testConfigData['TestList']:
                forceEnc      = False
                forceDec      = False
                forceMet      = False
                forceClean    = True        
                testName      = test['TestName']
                profile       = test['Profile']
                encoderParams = test['EncoderParams']
                seqList       = test['SeqList']

                print("testName", testName)
                for sIdx, seq in enumerate(seqList) :
                    taskIdx = 0
                    jobList = []  
                    firstTaskId = -1
                    nbFrameList   = seq['FrameNbList']
                    
                    for fIdx, nbFrame in enumerate(nbFrameList):
                        seqId     = seq['SeqId']
                        jobName   = self.config_manager.getJobName(profile, seqId, nbFrame, testName)
                        condition = seq['Condition']
                        rateList  = seq['RateList']
                        
                        for rIdx, rate in enumerate (rateList) :
                            rateId  = rate['RateId']
                            geoQP   = rate['geometryQP']
                            attQP   = rate['attributeQP']
                            occPrec = rate['occupancyPrecision']

                            name, fps, config, ply, maxNbFrame = self.config_manager.getSequenceInfo(seqId, self.config_manager.sequenceData)
                            taskIdx+=1
                            effectiveNbFrame = nbFrame
                            if maxNbFrame < int(nbFrame):
                                print (frameworkUtils.RED, "available:", maxNbFrame, " asked:", nbFrame, frameworkUtils.ENDC)
                                effectiveNbFrame = maxNbFrame
                            self.addTest(seqId, name, fps, config, ply, 
                                         condition, effectiveNbFrame, rateId, geoQP, attQP, occPrec, 
                                         forceEnc, forceDec, forceMet, forceClean, 
                                         testName, encoderParams)

        #print(self.argList)
    
    def addTest(self, seqId, name, fps, config, ply, 
                condition, effectiveNbFrame, rateId, geoQP, attQP, occPrec, 
                forceEnc, forceDec, forceMet, forceClean, 
                testName, encoderParams, nbThreads = 1):
                   
        cmdArgs,encParamsArgs = self.buildCmdArgs(seqId, name, fps, config, ply, 
                                    condition, effectiveNbFrame, rateId, geoQP, attQP, occPrec, 
                                    forceEnc, forceDec, forceMet, forceClean, 
                                    testName, encoderParams, self.config_manager.tmc2Dir, self.config_manager.mmDir, nbThreads)
        #print(taskIdx, "task=", cmdArgs)   

        self.argList.append(cmdArgs)
        self.encParams.append(encParamsArgs)

    ### Build command line args that call encode/decode/compute metrics process on grid or locally
    def buildCmdArgs(self, seqId, name, fps, config, plyPath, 
                     condition, nbFrame, rateId, geoQP, attQP, occPrec, 
                     forceEnc, forceDec, forceMet, forceClean, 
                     testName, encoderParams, tmc2Dir, mmDir, nbThreads = 1):
        
        inputDir   = Path(plyPath).resolve(strict=True)
        seqCfgFile = Path(str(tmc2Dir), "cfg", "sequence", config).resolve(strict=True)  
        
        testEncParams = "--encOptions="
        testEncParams += "".join(["--geometryQP=", str(geoQP), " --attributeQP=", str(attQP), " --occupancyPrecision=", str(occPrec)])
        for param in encoderParams:
            testEncParams += " " + param

        # build command's arguments
        args = " ".join(
                        [
                        "-s", str(seqId), 
                        "-o", str(self.config_manager.outputDir),
                        "--name", name,
                        "-i", str(inputDir),
                        "--seqCfg", str(seqCfgFile),
                        "-n", str(nbFrame),
                        "-r", str(rateId), 
                        "--condition", condition,
                        "--nbThreads", str(nbThreads),
                        "--tmc2Dir", str(tmc2Dir),
                        "--mmDir", str(mmDir),
                        "--forceEncode", str(forceEnc),
                        "--forceDecode", str(forceDec),
                        "--forceMetric", str(forceMet),
                        "--forceClean", str(forceClean),
                        "--testName", testName
                        ])    

        #print(args)
        return args, testEncParams

    def buildCmd(self, cmdArgs, encParams):

        cmd = ['python', self.cmd]
        for arg in cmdArgs.split():
            #print(arg)
            cmd.append(arg)
        cmd.append(encParams)
        return cmd

    def run(self):
        for idx, args in enumerate(self.argList) :
            print ("local:", self.cmd, flush=True)
            self.startLocalTask(args, self.encParams[idx])
    
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
        plyGen = PlyGenerator(cm)
        plyGen.run()
       
    except Exception as e:
        print(utils.RED, traceback.format_exc())
        print ("Exception:", e, utils.ENDC)
        sys.exit();

