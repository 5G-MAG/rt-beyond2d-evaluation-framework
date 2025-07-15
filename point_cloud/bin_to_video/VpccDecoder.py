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

import sys, traceback, subprocess, argparse
from pathlib import Path

from ConfigManager import ConfigManager

commonDir = Path(__file__).resolve(strict=True).parent.joinpath("../common")
sys.path.append(str(Path(commonDir)))
import utils

class VpccDecoder:

    def __init__ (self, config_manager:ConfigManager, test=None, force=False):
        self.cmd = utils.pathStr(config_manager.pcc_dec)
        self.argList=[]
        self.force=force

        if (not test==None):
            self.addTest(config_manager, test)
        else:
            for test in config_manager.testData['TestList']:
                self.addTest(config_manager, test)

    def addTest(self, config_manager, test):
        name = str(test['Name'])
        
        if test.get('PathEnc', "") != "":
            output_dir = Path(config_manager.dec_ply_dir.joinpath(test['PathDec']))
            if not output_dir.exists() or self.force == True:
                output_dir = utils.createPath(output_dir)
                output_path = utils.pathStr(output_dir.joinpath(name))
                stream_path = utils.pathStr(utils.tryRelativePath(Path(test['PathEnc']), config_manager.outputDir))
                col_conv = utils.pathStr(config_manager.col_conv)

                cmdArgs  = "".join([
                " --compressedStreamPath=", stream_path,
                " --inverseColorSpaceConversionConfig=", col_conv,
                " --nbThread=", str(config_manager.nb_th_dec),
                " --frameCount=", str(config_manager.nb_fr_dec),
                " --reconstructedDataPath=", output_path, "_dec_%04d.ply"
                ])

                self.argList.append(cmdArgs)
            else:
                print(f"[Decoder] | test {name} skipped, output folder already exists")
        else:
            print (f"[Decoder] | test {name} skipped, no encoded path provided")

    def run(self):
        for args in self.argList:
            print ("local:", self.cmd, args, "\n", flush=True)
            cmd = f"{self.cmd} {args}"
            subprocess.run(cmd, shell=True)   
                
    def toFile(self, path):
        fpath=Path(path)
        f = open(fpath,"w")
        for args in self.argList:
            f.write(f"{self.cmd} {args}\n")
        f.close()
        fpath.chmod(0o774)
        return 1

    def toSeparateFiles(self,path_prefix):
        for i,args in enumerate(self.argList):
            fpath=Path(f"{path_prefix}_{i}.sh")
            f = open(fpath,"w")
            f.write(f"{self.cmd} {args}\n")
            f.close()
            fpath.chmod(0o774)
        return len(self.argList)


