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
import traceback, sys, argparse
from pathlib import Path

from ConfigManager import ConfigManager
from VpccDecoder import VpccDecoder
from VideoGenerator import VideoGenerator
# from VideoConverter import VideoConverter

commonDir = Path(__file__).resolve(strict=True).parent.joinpath("../common")
sys.path.append(str(Path(commonDir)))
import utils


def parseArgs():
    global parser
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter, 
                                     description=("Decode V-PCC bitstreams into .PLY point cloud sequences using the MPEG V-PCC reference software (TMC2) "
                                                 "and generate videos using the MPEG 3D Group Renderer.\n"
                                                 "Decoding and rendering operations will respectively be skipped if "
                                                 "existing point cloud sequences folders or video files are detected."),
                                                 usage=argparse.SUPPRESS,
                                                 epilog=("Usage:\n"
                                                         "  Nominal: \n"
                                                         "      %(prog)s -c path_to_config.json -i path_to_test.json -o outputdir\n"
                                                         "  Export only video generation commands per job, even if videos exists, and don't run:\n"
                                                         "      %(prog)s -c path_to_config.json -i path_to_test.json -o outputdir -v -s -scriptsMode job --noRun -f\n"))
    
    parser.add_argument('-c', '--configJson',      help="(REQUIRED) Path to the .json file containing the general configuration, including the rendering jobs", type=str, required=True, nargs="?")
    parser.add_argument('-i', '--inputJson' ,      help="(REQUIRED) Path to the .json file containing the input bitstreams and output videos informations", type=str, required=True, nargs="?")
    parser.add_argument('-o', '--outputDir' ,      help="(REQUIRED) Path to the output directory", type=str, required=True, nargs="?")
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument( '-d', '--decodeOnly',      help="\nRun vpcc decoding only (mutually exclusive with --videoOnly)", action='store_true', default=False)
    group.add_argument( '-v', '--videoOnly' ,      help="\nRun video generation only (mutually exclusive with --decodeOnly)", action='store_true', default= False)
    
    parser.add_argument('-f', '--force'     ,      help="\nForce decoding and/or video generation, even if files already exist", action='store_true', default= False)
    parser.add_argument('--noRun'           ,      help="\nParse the input files, but don't execute the commands (typ. to generate the scripts)", action='store_true', default=False )
    parser.add_argument('-s', '--scripts'   ,      help="\nExport the generated commands to bash scripts in the output directory.", action='store_true', default=False)
    parser.add_argument('--scriptsMode'     ,      help=("Set the script export mode:\n"
                                                        "   full            : Export all decoding commands in a dec.sh file and\n"
                                                        "                       all the video generation commands in a vid.sh files.\n"
                                                        "   test (default)  : Export all the commands for individual streams in\n "
                                                        "                       dec_<stream_id>.sh and vid_<stream_id>.sh.\n"
                                                        "   job             : Same as TEST for decoding commands, export the\n"
                                                        "                       video generation commands for each render job in\n"
                                                        "                       vid_<stream_id>_<job_id>.sh\n"),
                                                   choices=['full', 'test', 'job'], type=str, default='test')
    
    return parser.parse_args()

if __name__ == "__main__":
    try:

        # Parse arguments
        args = parseArgs()
       
        scriptDir = Path(__file__).parent.resolve(strict=True)

        #set config JSON path
        if args.configJson:
            confJsonPath = Path(args.configJson).resolve(strict=True)
        else:
            confJsonPath = Path(scriptDir).joinpath("jsons", args.configJson).resolve(strict=True)
        
        #set tests JSON path
        if args.inputJson:
            testJsonPath = Path(args.inputJson).resolve(strict=True)
        else:
            testJsonPath = Path(scriptDir).joinpath(args.inputJson).resolve(strict=True)
            
        #set ouptut path
        if args.outputDir:
            outputDir = utils.createPath(Path(args.outputDir))
        else:
            outputDir = utils.createPath(Path(scriptDir).joinpath(args.outputDir))

        #Parse config
        cm = ConfigManager(confJsonPath, testJsonPath, outputDir)

        #VPCC Decoding
        if not args.videoOnly:

            #Commands generation
            dec = VpccDecoder(cm, force=args.force)

            #Commands export
            if args.scripts:
                path_prefix = outputDir.joinpath("dec")
                if args.scriptsMode=='full':
                    dec.toFile(path_prefix)
                else:
                    dec.toSeparateFiles(path_prefix)
            
            #Commands execution
            if not args.noRun:
                dec.run()
        
        #Video generation
        if not args.decodeOnly:

            #Commands generation
            vid = VideoGenerator(cm, force=args.force)
            
            #Commands export
            if args.scripts:
                path_prefix = outputDir.joinpath("vid")
                if args.scriptsMode=='full':
                    vid.toFile(path_prefix)
                elif args.scriptsMode=='test':
                    vid.toSeparateFilesTests(path_prefix)
                else:
                    vid.toSeparateFilesJobs(path_prefix)
            
            #Commands execution
            if not args.noRun:
                vid.run()        
            
    except Exception as e:
        print(utils.RED, traceback.format_exc(), utils.ENDC)        
        sys.exit()
