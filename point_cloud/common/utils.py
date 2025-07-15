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

import os, shutil
from pathlib import Path, PurePath, PurePosixPath
from hashlib import md5

GREEN = '\033[92m'
BLUE  = '\033[94m'
RED   = '\033[91m'
PURPLE = '\033[95m'
ENDC  = '\033[m' # reset to the defaults


def printArgs(args):
    print(BLUE + "Argument values:")
    for arg in vars(args):
        print(BLUE + "  - %-20s = %s" % (arg, getattr(args, arg)))
    print (ENDC, flush=True)

def str2bool(v):
    if isinstance(v, bool):           return v
    if v.lower() in ('true', '1'):    return True
    elif v.lower() in ('false', '0'): return False
    else:                             raise os.ArgumentTypeError('Boolean value expected.')

def isSameString(string, file):
    status = False
    if file.exists():
        if string == open(file).read().rstrip():
            status = True
    return status

def copyFile2Dir(srcFile, destDir):
    os.makedirs(destDir, exist_ok=True)
    outputFile = Path(destDir).joinpath(PurePath(srcFile).name)        
    if not os.path.exists(outputFile):
        shutil.copyfile(srcFile, outputFile)
    return outputFile

def pathStr(p:Path):
    return str(PurePosixPath(p))

def createPath(p:Path):
    p.mkdir(parents=True, exist_ok=True)
    return p

def tryRelativePath(path:Path, source_path:Path ):
    if path.is_absolute():
        return path
    else:
        return source_path.joinpath(path)
    
def computeMd5(file_path):
    hasher = md5()
    with open(file_path, 'rb') as f:
        for line in f :
            #normalize line ending Window/Linux issue
            if line.endswith(b'\r\n'):
                line = line[:-2] + b'\n'
            elif line.endswith(b'\r'):
                line = line[:-1] + b'\n'
            hasher.update(line)
    return hasher.hexdigest()

def exportMd5(path:Path):
    sum = computeMd5(path)
    sum_file=path.parent.joinpath(path.stem, "_MD5.txt")
    sum_file.open('+w')
    sum_file.write_text(f"File   : {path}\nMD5 Sum: {sum}")
    sum_file.close()
      