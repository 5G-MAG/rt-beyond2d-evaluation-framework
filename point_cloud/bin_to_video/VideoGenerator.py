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

import subprocess, sys, os
from pathlib import Path

from ConfigManager import ConfigManager

commonDir = Path(__file__).resolve(strict=True).parent.joinpath("../common")
sys.path.append(str(Path(commonDir)))
import utils

class VideoGenerator:

    def __init__ (self, config_manager, test=None, force=False):

        self.force=force
        self.cmd = utils.pathStr(config_manager.renderer)

        self.testList=[]

        if(not test==None):
            self.addTest(config_manager, test)

        else:
            for test in config_manager.testData['TestList']:
               self.addTest(config_manager, test)


    def addTest(self, config_manager, test):

        name = test['Name']
        pathDec = test['PathDec']
        pathVid = test['PathVid']
        fps = test.get('FPS', 30)
        config = test.get('Config', None)
        renderJobs = []
        if not config_manager.renderjobs == None:
            renderJobs += config_manager.renderjobs
        if len(renderJobs) == 0:
            print("No render job found in configuration file, using default job (cube size1)")
            renderJobs={"name": "default_cube_size1", "args": "--rendererId=0 --psize=1"}

        conf_arg=""
        if config:
            conf_arg=f"--config={utils.tryRelativePath(Path(config), Path(config_manager.testJsonPath).parent)}"

        if (isinstance(test['CameraPath'], int)):
            cam = f" --cameraPathIndex={test['CameraPath']}"
        else:
            cam = f" --camera={utils.pathStr(config_manager.cam_dir.joinpath(test['CameraPath']).resolve(strict=True))}"
        testArgs=[]
        for j in renderJobs:
            vid_dir = Path(config_manager.vid_dir.joinpath(pathVid))
            vid_name = f"{name}_{j['name']}"
            
            exist=False
            if os.path.exists(vid_dir):
                for v in os.listdir(vid_dir):
                    if v.startswith(vid_name):
                        exist=True
                        break
            
            if not exist or self.force==True:
                job_args = f"{config_manager.render_args} {j['args']} --width={config_manager.width} --height={config_manager.height}"
                vid = utils.createPath(config_manager.vid_dir.joinpath(pathVid)).joinpath(f"{name}_{j['name']}")
                ply = utils.pathStr(config_manager.dec_ply_dir.joinpath(pathDec).resolve(strict=True))
                cmdArgs = f" -d {ply}/ -o {utils.pathStr(vid)} {cam} {job_args} --fps={fps}"
                if j.get('use_background', 0)==1:
                    cmdArgs=(f"{cmdArgs} {conf_arg}")                
                
                testArgs.append(cmdArgs)

                if exist and self.force==True:
                    for v in os.listdir(vid_dir):
                        if v.startswith(vid_name):
                            os.remove(Path(vid_dir).joinpath(v))
            
            else:
                print(f"[Renderer] | job {vid_name} skipped, file already exists")
        if testArgs:
            self.testList.append(testArgs)
        


    def run(self):
        for test in self.testList:
            for args in test:
                print ("local:", self.cmd, args, "\n\n", flush=True)
                subprocess.run(f"{self.cmd} {args}", shell=True)  
        
    def toFile(self, path):
        fpath=Path(path)
        if self.testList:
            f = open(fpath,"w")
            for test in self.testList:
                for args in test:
                    f.write(f"{self.cmd} {args}\n\n")
            f.close()
            fpath.chmod(0o774)
            return 1
        else:
            return 0
    
    def toSeparateFilesTests(self, path_prefix):
        if self.testList:
            for i,test in enumerate(self.testList):
                fpath=Path(f"{path_prefix}_{i}.sh")
                f = open(fpath,"w")
                for args in test:
                    f.write(f"{self.cmd} {args}\n\n")
                f.close()
                fpath.chmod(0o774)
            return len(self.testList)
        else:
            return 0

        
    def toSeparateFilesJobs(self, path_prefix):
        k=0
        if self.testList:
            for i,test in enumerate(self.testList):
                if test:
                    for j,args in enumerate(test):
                        fpath=Path(f"{path_prefix}_{i}_{j}.sh")
                        f = open(fpath,"w")
                        f.write(f"{self.cmd} {args}\n\n")
                        f.close()
                        fpath.chmod(0o774)
                        k=k+1
        return k
