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

import os, argparse, sys, subprocess
from pathlib import Path
from git import Repo

import utils

def parseArgs():
    global parser
    parser = argparse.ArgumentParser(description='This script generates point cloud frames (PLY) from meshes (OBJ+TXT)')
    parser.add_argument('-o', '--outputDir', help="Output PLY directory", type=str, required=True)
    return parser.parse_args()

#install and build tmc2
def buildDepsTmc2(outputDir):

    version="release-v25.0"
    tmc2Dir = Path(outputDir).joinpath("dependencies", "mpeg-pcc-tmc2", version)
    
    # clone if not done
    if not os.path.exists(tmc2Dir):
        tmc2Url="https://github.com/MPEGGroup/mpeg-pcc-tmc2.git"
        repo = Repo.clone_from(url=tmc2Url, to_path=tmc2Dir, branch=version, depth=1)        
        print (utils.GREEN  + "tmc2 cloned", tmc2Dir, utils.ENDC, flush=True)
    else:
        print (utils.GREEN  + "tmc2 already cloned", tmc2Dir, utils.ENDC, flush=True)
    
    # build release mode
    buildTool(tmc2Dir)
    return tmc2Dir

#install and build mmetrics
def buildDepsMmetric(outputDir):

    version="1_1_7"
    mmDir = Path(outputDir).joinpath("dependencies", "mpeg-pcc-mmetric", version)
    
    # clone if not done
    if not os.path.exists(mmDir):
        mmUrl="https://github.com/MPEGGroup/mpeg-pcc-mmetric"
        Repo.clone_from(mmUrl, mmDir, branch=version, depth=1)
        print (utils.GREEN  + "mmetric cloned", mmDir, utils.ENDC, flush=True)
    else:
        print (utils.GREEN  + "mmetric already cloned", mmDir, utils.ENDC, flush=True)
    
    # build release mode
    buildTool(mmDir)
    return mmDir

#install and build mpeg-3dg-renderer
def buildDepsRenderer(outputDir):
    
    commit_sha="c1e09f8"
    version="8.0"
    rendererDir = Path(outputDir).joinpath("dependencies", "mpeg-3dg-renderer", version)
    
    # clone if not done
    if not os.path.exists(rendererDir):
        rendererUrl="https://github.com/MPEGGroup/mpeg-3dg-renderer.git"
        repo = Repo.clone_from(rendererUrl, rendererDir, depth=1)
        repo.git.checkout(commit_sha)
        # repo.git.execute(['git', 'apply', f'{Path(__file__).parent.joinpath("patch.txt")}'])
        print (utils.GREEN  + "renderer cloned", rendererDir, utils.ENDC, flush=True)
    else:
        print (utils.GREEN  + "renderer already cloned", rendererDir, utils.ENDC, flush=True)
    
    # build release mode
    buildTool(rendererDir)
    return rendererDir

# build tools in release mode
def buildTool(toolDir):
        
    if not os.path.exists(Path(toolDir).joinpath("build")):        
        script = Path(toolDir).joinpath("build.sh")
        cmd = f"bash {utils.pathStr(script)}"
        os.chmod(script , 0o755)
        subprocess.check_call(cmd, shell=True)
        print(utils.GREEN + "compile done", toolDir, utils.ENDC, flush=True)
    else:
        print(utils.GREEN + "compile already done", toolDir, utils.ENDC, flush=True)

if __name__ == "__main__":

    try:
        # Parse arguments
        args = parseArgs()
        if len(sys.argv) == 0:
            parser.print_help(sys.stderr)
            sys.exit(1)
        
        #run build commands
        toolsDir = buildDepsTmc2(args.outputDir)
        print("toolsDir = ", toolsDir, flush=True)
        toolsDir = buildDepsMmetric(args.outputDir)
        print("toolsDir = ", toolsDir, flush=True)
        toolsDir = buildDepsRenderer(args.outputDir)
        print("toolsDir = ", toolsDir, flush=True)

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(utils.RED + "Exception:", e, "type:", exc_type, fname, exc_tb.tb_lineno, utils.ENDC, flush=True)
        sys.exit(e.returncode)
