# Multi-view plus depth evaluation framework

## Getting started

### Minimum requirements

Please verify that the following requirements have been met:

* 32 GB RAM
* Test content on an accessible path
* 1 TB free disk space
* Ubuntu 24.04.02+ LTS
* For Windows: WSL 2
* Internet connectivity

### Building the software

Open a Bash terminal to clone the project and build the software:

```shell
git clone git@github.com:5G-MAG/rt-beyond2d-evaluation-framework.git beyond2d
cd beyond2d/mvd
./setup.sh --system
```

The `--system` argument will `sudo apt` the required Ubuntu packages. Alternatively, the packages
can be manually installed, and in that case the `--system` argument can be omitted.

### Configuring the experiment

Run the following to configure the experiment. This script will create a `build.ninja` file with a
dependency graph of all jobs to execute to complete the experiment.

```shell
. venv/bin/activate
./configure_experiment.py --content-dir /your/content/dir
```

> [!TIP]
> It is is possible to mount UNC network paths in WSL:
>
> ```shell
> sudo mount -t drvfs '\\MY\UNC\PATH' /mnt/my_mount
> ```

Some relevant options are:

* `--slurm`: Run the experiment on multiple nodes of a Slurm load-balancing compute server.
* `--thread-count`: Number of threads for each of the TMIV encoder and decoder invocations.
* `--help`: Overview of all available options:

```shell
usage: configure_experiment.py [-h] --content-dir CONTENT_DIR [--condition-ids [CONDITION_IDS ...]] [--frame-counts [FRAME_COUNTS ...]] [--content-ids [CONTENT_IDS ...]] [--rate-ids [RATE_IDS ...]] [--slurm] [--thread-count THREAD_COUNT]

options:
  -h, --help            show this help message and exit
  --content-dir CONTENT_DIR
                        base directory of the content with a sub-directory for each content item (default: None)
  --condition-ids [CONDITION_IDS ...]
                        list of coding conditions to evaluate (default: ['A', 'FV', 'SCV'])
  --frame-counts [FRAME_COUNTS ...]
                        list of input frame counts to evaluate (default: [3, 65])
  --content-ids [CONTENT_IDS ...]
                        list of content items to evaluate (default: ['Bartender', 'Breakfast', 'DanceMoves'])
  --rate-ids [RATE_IDS ...]
                        list of rate points to evaluate (default: ['RP1', 'RP2', 'RP3', 'RP4'])
  --slurm               run each job as a batch job on the default partition of a Slurm cluster (default: False)
  --thread-count THREAD_COUNT
                        specify the maximum number of threads per job (default: 4)
```

### Running the experiment

Ideally, it is enough to run `ninja` to complete the entire experiment.

The encoding and decoding jobs are memory intensive. When running the experiment on a single
machine, it is advisable to limit the number of jobs in parallel:

```shell
ninja -j 2
```

With `--slurm`, the steps are run as batch jobs and we should keep the Slurm job queue filled:

```shell
ninja -j 0  # infinite jobs
```

By providing a specific output file, Ninja will only run the jobs that are needed to create it:

```shell
ninja out/A3/Bartender/RP3/A3_Bartender_RP3_v00_tex_1920x1080_yuv420p10le.yuv
```

For more options, see `ninja --help`.

### Output of the experiment

The experiment has the following types of outputs:

| Example file                                             | Description                                                |
| -------------------------------------------------------- | ---------------------------------------------------------- |
| `TMIV_A3_Bartender_RP0.bit`                              | Intermediate MIV bitstreams (RP0) w/o video sub bitstreams |
| `TMIV_A3_Bartender_RP0_geo_c00_960x2304_yuv420p10le.yuv` | Codable video data (RP0)                                   |
| `TMIV_A3_Bartender_RP3_geo_c00.bit`                      | Coded video sub bitstream (RP*x*)                          |
| `TMIV_A3_Bartender_RP3.bit`                              | Final MIV bitstream (RP*x*) with video sub bitstreams      |
| `A3_Bartender_RP3_v00_tex_1920x1080_yuv420p10le.yuv`     | Reconstructed source view YUV files                        |
| `A3_Bartender_RP3_v00.qmiv`                              | Objective metrics                                          |
| `A3_Bartender_RP3_p01_tex_1920x1080_yuv420p10le.yuv`     | Interpolated pose trace YUV files                          |

In addition, there are the following files for analysis purposes:

| File extension | Description         |
| -------------- | ------------------- |
| `.hls`         | TMIV parser log     |
| `.log`         | Log file            |
| `.csv`         | TMIV bitrate report |

## Software bill of materials

### System packages

This framework was developed on Ubuntu 24.04.02 LTS. The following packages and their depedencies were installed.

| Name             | Version              | Architecture | Description                                                               |
| ---------------- | -------------------- | ------------ | ------------------------------------------------------------------------- |
| build-essential  | 12.10ubuntu1         | amd64        | Informational list of build-essential packages                            |
| clang            | 1:18.0-59~exp2       | amd64        | C, C++ and Objective-C compiler (LLVM based), clang binary                |
| git              | 1:2.43.0-1ubuntu7.2  | amd64        | fast, scalable, distributed revision control system                       |
| libc++-dev:amd64 | 1:18.0-59~exp2       | amd64        | LLVM C++ Standard library (development files)                             |
| libclang-rt-dev  | 1:18.0-59~exp2       | amd64        | Compiler-rt - Development package                                         |
| llvm             | 1:18.0-59~exp2       | amd64        | Low-Level Virtual Machine (LLVM)                                          |
| python3          | 3.12.3-0ubuntu2      | amd64        | interactive high-level object-oriented language (default python3 version) |
| python3-pip      | 24.0+dfsg-1ubuntu1.1 | all          | Python package installer                                                  |
| python3-venv     | 3.12.3-0ubuntu2      | amd64        | venv module for python3 (default python3 version)                         |
| ubuntu-minimal   | 1.539.2              | amd64        | Minimal core of Ubuntu                                                    |
| ubuntu-wsl       | 1.539.2              | amd64        | Ubuntu on Windows tools - Windows Subsystem for Linux integration         |

> [!NOTE]
> This list was created by filtering the output of `dpkg -l $(find apt-mark showmanual)`. Exact package versions may change over time.

### Python packages

The following Python packages are required:

| Name  | Version  | License    | Description                                         |
| ----- | -------- | ---------- | --------------------------------------------------- |
| black | 25.1.0   | MIT        | The uncompromising code formatter                   |
| cmake | 4.0.2    | Apache 2.0 | CMake build generator                               |
| ninja | 1.11.1.4 | Apache 2.0 | Ninja is a small build system with a focus on speed |

> [!NOTE]
> The license type was copied and may be incorrect.

> [!NOTE]
> In case of a mismatch the version in [requirements.txt](requirements.txt) is leading.

### C++ libraries

The multi-view plus depth evaluation framework will (indirectly) build the following C++ libraries from source. Advanced users may avoid or substitute some of the dependencies.

| Dependency | Version | License                                                    | URL                                                                            |
| ---------- | ------- | ---------------------------------------------------------- | ------------------------------------------------------------------------------ |
| TMIV       | 24.0    | BSD-3-Clause "New" or "Revised"                            | [gitlab.com/mpeg-i-visual/tmiv.git](https://gitlab.com/mpeg-i-visual/tmiv.git) |
| QMIV       | 2.0     | BSD-3-Clause "New" or "Revised"                            | [gitlab.com/mpeg-i-visual/qmiv.git](https://gitlab.com/mpeg-i-visual/qmiv.git) |
| Catch2     | 3.7.1   | BSL-1.0                                                    | [github.com/catchorg/Catch2.git](https://github.com/catchorg/Catch2.git)       |
| {fmt}      | 11.0.2  | [{fmt}](https://github.com/fmtlib/fmt/blob/11.2.0/LICENSE) | [github.com/fmtlib/fmt.git](https://github.com/fmtlib/fmt.git)                 |
| {fmt}      | 10.2.1  | [{fmt}](https://github.com/fmtlib/fmt/blob/10.2.1/LICENSE) | [github.com/fmtlib/fmt.git](https://github.com/fmtlib/fmt.git)                 |
| VVdeC      | 2.3.0   | BSD-3-Clause-Clear                                         | [github.com/fraunhoferhhi/vvdec](https://github.com/fraunhoferhhi/vvdec)       |
| VVenC      | 1.12.0  | BSD-3-Clause-Clear                                         | [github.com/fraunhoferhhi/vvenc](https://github.com/fraunhoferhhi/vvenc)       |
| HM         | 18.0    | BSD-3-Clause "New" or "Revised"                            | [vcgit.hhi.fraunhofer.de/jvet/HM](https://vcgit.hhi.fraunhofer.de/jvet/HM)     |
| Kvazaar    | m71800  | BSD-3-Clause license                                       | [github.com/bart-kroon/kvazaar](https://github.com/bart-kroon/kvazaar)         |

> [!NOTE]
> The license type was copied and may be incorrect.
