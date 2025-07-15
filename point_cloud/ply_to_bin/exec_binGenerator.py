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

import sys, os, argparse
from pathlib import Path

#local include
commonDir = Path(__file__).resolve(strict=True).parent.joinpath("../common")
sys.path.append(str(Path(commonDir)))
import utils as utils

from ConfigManager import ConfigManager
from BinGenerator import BinGenerator
from XlsSheetGenerator import XlsSheetGenerator

def parseArgs():
    global parser
    parser = argparse.ArgumentParser(description='This script generates point cloud frames (PLY) from meshes (OBJ+TXT)')
    parser.add_argument('-i', '--sequenceJson',     help="Json that contains the sequence to be done", type=str, required=True)
    parser.add_argument('-o', '--outputDir',        help="Output BIN directory", type=str, required=True)
    parser.add_argument('-t', '--testConfJson',     help="Json that contains the test configuration", type=str, required=True)
    return parser.parse_args()
      
if __name__ == "__main__":

    try:
        # Parse arguments
        args = parseArgs()
        if len(sys.argv) == 0:
            parser.print_help(sys.stderr)
            sys.exit(1)
        
        #create a config manager
        cm = ConfigManager(args.outputDir, args.sequenceJson, args.testConfJson, 0)
        
        #create a bin generator and run
        binGen = BinGenerator(cm)
        binGen.run()
        
        #create a xls sheet generator and run
        xlsGen = XlsSheetGenerator(cm)
        xlsGen.run()
        
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(utils.RED + "Exception:", e, "type:", exc_type, fname, exc_tb.tb_lineno, utils.ENDC, flush=True)
        sys.exit(e.returncode)
