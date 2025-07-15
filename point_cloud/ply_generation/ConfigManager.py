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

import traceback, subprocess, platform, shutil
import sys, time
import argparse, json
from pathlib import Path

#import utils
#from utils import createPath

commonDir = Path(__file__).resolve(strict=True).parent.joinpath("../common")
sys.path.append(str(Path(commonDir)))
import utils 
import install_deps

class ConfigManager:

    def __init__ (self, outDir, confJsonPath, verbose=None):

        self.verbose = verbose or 0
        
        # ############# #
        # SET UP CONFIG #
        # ############# #

        #save input parameters
        self.outputDir    = Path(outDir).resolve()
        self.confJsonPath = Path(confJsonPath).resolve(strict=True)
        
        self.scriptDir    = Path(__file__).parent
        
        #install dependencies
        self.mmDir  = install_deps.buildDepsMmetric(self.outputDir)
        
        #read config JSON file
        with open(self.confJsonPath, 'r') as conf_file:
            self.confData = json.load(conf_file)

        #self.printConfig()
        self.buildInputInfo()
        
        # create directory to store command log, scripts
        #self.cmdDir = utils.createPath(Path(self.outputDir).joinpath("cmd"))
        self.cmdDir = Path(self.outputDir).joinpath("cmd")
        
        
    def buildInputInfo(self):
        self.inputList = []
        index = 0
        for idx, item in enumerate(self.confData['TestList']):
            myDict = {'seqId':0, 'name':'', 'qp':11, 'ratio':1, 'meshObjPath':'', 'meshTxtPath':'', 'firstFrameId':0, 'nbFrame':1, 'outputDir':'', 'outputFormat':''}
            
            myDict['seqId']        = int(self.confData['TestList'][idx]['SeqId'])
            myDict['name']         = self.confData['TestList'][idx]['Name']
            myDict['qp']           = self.confData['TestList'][idx]['Qp']
            myDict['ratio']        = self.confData['TestList'][idx]['Ratio']
            myDict['meshObjPath']  = Path(self.confData['TestList'][idx]['MeshObjPath'])
            myDict['meshTxtPath']  = Path(self.confData['TestList'][idx]['MeshTxtPath'])
            myDict['firstFrameId'] = self.confData['TestList'][idx]['FirstFrameId']
            myDict['nbFrame']      = self.confData['TestList'][idx]['NbFrame']
            
            prefix                 = "".join(["F", str(self.confData['TestList'][idx]['NbFrame']), "_quantized_vox", str(self.confData['TestList'][idx]['Qp']), "_r", str(self.confData['TestList'][idx]['Ratio'])])
            myDict['outputDir']    = Path(self.outputDir).joinpath(self.confData['TestList'][idx]['OutputDir'], prefix)
            myDict['outputFormat'] = self.confData['TestList'][idx]['OutputFormat']  

            self.inputList.append(myDict)

    def printInputInfo(self):
        if (self.verbose):
            for index, info in enumerate(self.inputList):
                print(utils.GREEN, "TEST [", index, "]")
                print(" id=",           info['seqId'],
                      " name=",         info['name'],
                      " qp=",           info['qp'],
                      " ratio=",        info['ratio'],
                      " meshObjPath=",  info['meshObjPath'],
                      " meshTxtPath=",  info['meshTxtPath'],
                      " firstFrameId=", info['firstFrameId'],
                      " nbFrame=",      info['nbFrame'],
                      " outputDir=",    info['outputDir'],
                      " outputFormat=", info['outputFormat'], utils.ENDC, sep='', flush=True) 

    def printConfig(self):
        if (self.verbose):
            print (utils.RED + "CONFIG from file ", self.confJsonPath, " :" )
            for key, value in self.confData.items():
                print("\t", key, " = ", value)
            print (utils.ENDC)

    def getMmExePath(self):
        plt = platform.system()
        if plt == "Windows":
            return Path(self.mmDir).joinpath("build/release/bin/release/mm.exe")
        elif plt == "Linux":
            return Path(self.mmDir).joinpath("build/Release/bin/mm")
        else:
            raise ValueError("Your system is not supported")

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
        
        cm = ConfigManager(args.outputDir, args.inputJson, 0)
        cm.printInputInfo()
        print("mm path dir = ", cm.getMmExePath())
               
    except Exception as e:
        print(utils.RED, traceback.format_exc())
        print ("Exception:", e, utils.ENDC)
        sys.exit();

