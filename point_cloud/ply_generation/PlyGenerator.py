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

class PlyGenerator:

    def __init__ (self, config_manager, test=None):
        
        self.config_manager = config_manager
        self.cmd = utils.pathStr(Path(config_manager.scriptDir).joinpath("obj2ply_mm.py"))
        self.argList = []

        if (not test==None):
            self.addTest(config_manager, test)
        else:
            for seq in self.config_manager.inputList:
                self.addTest(self.config_manager, seq)
    
    def addTest(self, config_manager, seq):
        
        cmdArgs  = " ".join([
        "--qp"              , str(seq['qp']), 
        "--ratio"           , str(seq['ratio']), 
        "-i"                , str(seq['meshObjPath']), 
        "-m"                , str(seq['meshTxtPath']),
        "-o"                , str(seq['outputDir']),
        "--outputPlyFormat" , str(seq['outputFormat']),
        "--firstFrame"      , str(seq['firstFrameId']),
        "--nbFrame"         , str(seq['nbFrame']),
        "--mmExe"           , str(config_manager.getMmExePath())
        ])      

        self.argList.append(cmdArgs)

    def buildCmd(self, cmdArgs):
        cmd = ['python', self.cmd]
        for arg in cmdArgs.split():
            #print(arg)
            cmd.append(arg)
        return cmd

    def run(self):
        for args in self.argList:
            print ("local:", self.cmd, flush=True)
            self.startLocalTask(args)

    def startLocalTask(self, cmdArgs):
        cmd = self.buildCmd(cmdArgs)
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

