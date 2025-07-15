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
import platform, sys ,json
from pathlib import Path

commonDir = Path(__file__).resolve(strict=True).parent.joinpath("../common")
sys.path.append(str(Path(commonDir)))
import install_deps as install_deps

class ConfigManager:

    def __init__ (self, confJsonPath, testJsonPath, outputDir, verbose=None):

        self.verbose = verbose or 0
        self.outputDir = outputDir
        # ############# #
        # SET UP CONFIG #
        # ############# #

        #read config JSON file
        self.confJsonPath = confJsonPath
        with open(self.confJsonPath, 'r') as conf_file:
            self.confData = json.load(conf_file)
        
        #TMC2 config
        self.tmc2_dir  = install_deps.buildDepsTmc2(self.outputDir)
        self.col_conv = self.tmc2_dir.joinpath("cfg", "hdrconvert", "yuv420torgb444.cfg")
        if platform.system() == "Windows":
            self.pcc_dec = self.tmc2_dir.joinpath("bin", "Release", "PccAppDecoder.exe")
        elif platform.system() == "Linux":
            self.pcc_dec = self.tmc2_dir.joinpath("bin", "PccAppDecoder")

        self.nb_th_dec = self.confData.get('nb_th_dec', 1)
        self.nb_fr_dec = self.confData.get('nb_fr_dec', 300)
        self.dec_ply_dir = outputDir

        #Renderer config
        self.renderer_dir  = install_deps.buildDepsRenderer(self.outputDir)
        if platform.system() == "Windows":
            self.renderer = Path(self.renderer_dir).joinpath("bin", "windows", "Release", "PccAppRenderer.exe").resolve(strict=True)
        elif platform.system() == "Linux":
            self.renderer = Path(self.renderer_dir).joinpath("bin", "linux", "Release", "PccAppRenderer").resolve(strict=True)
        self.vid_dir = outputDir
        self.cam_dir = testJsonPath.parent
        self.width = self.confData.get('width', 1920)
        self.height = self.confData.get('height', 1080)

        if 'render_jobs' in self.confData:
            self.renderjobs=self.confData['render_jobs']
        else:
            self.renderjobs=None
        self.render_args=self.confData.get('render_args', "")
        self.video_type=self.confData.get('video_type', 2)

        # ############ #
        # SET UP TESTS #
        # ############ #

        #read test JSON file
        self.testJsonPath = testJsonPath
        with open(self.testJsonPath, 'r') as file:
            self.testData = json.load(file)


