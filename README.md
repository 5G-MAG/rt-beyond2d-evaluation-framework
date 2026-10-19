<p align="center">
  <img src=".github/banner.svg" width="100%" alt="Testbeds · Beyond 2D Evaluation Framework: Beyond 2D Video Evaluation Framework">
</p>

<p align="center">
  Scripts and configuration files for reproducible evaluation in the 3GPP SA4
  <em>Feasibility Study on Beyond 2D Video</em> (FS_Beyond2D).
</p>

<p align="center">
  <img alt="Status" src="https://img.shields.io/endpoint?url=https%3A%2F%2Fwww.5g-mag.com%2Fbadges%2Fstatus%2Frt-beyond2d-evaluation-framework.json">
  <a href="https://github.com/5G-MAG/rt-beyond2d-evaluation-framework/releases"><img alt="Version"
    src="https://img.shields.io/github/v/release/5G-MAG/rt-beyond2d-evaluation-framework?label=Version"></a>
  <a href="LICENSE.md"><img alt="License: 5G-MAG Public License v1.0"
    src="https://img.shields.io/badge/License-5G--MAG%20PL%20v1.0-blue"></a>
</p>

<p align="center">
  <a href="https://www.5g-mag.com/testbeds/beyond-2d/">Project page</a> &nbsp;&middot;&nbsp;
  <a href="https://github.com/5G-MAG/rt-beyond2d-evaluation-framework/issues">Issues</a> &nbsp;&middot;&nbsp;
  <a href="https://www.5g-mag.com/contributing">Contributing</a>
</p>

---

## At a glance

|  |  |
|---|---|
| **Supports** | 3GPP SA4 *Feasibility Study on Beyond 2D Video* (FS_Beyond2D), [SP-240479](https://www.3gpp.org/ftp/tsg_sa/TSG_SA/TSGS_103_Maastricht_2024-03/Docs/SP-240479.zip); the study will result in [TR 26.956](https://www.3gpp.org/dynareport/26956.htm) |
| **Part of** | [Beyond 2D Evaluation Framework](https://www.5g-mag.com/testbeds/beyond-2d/) |

## Introduction

This repository provides the evaluation framework for the *Feasibility Study on Beyond 2D Video*
(FS_Beyond2D) in [3GPP](https://www.3gpp.org) TSG SA
[WG4](https://www.3gpp.org/3gpp-groups/service-system-aspects-sa/sa-wg4) (SA4). The study covers
several Beyond 2D representations and service scenarios, and this repository holds scripts and
configuration files to evaluate them reproducibly. Source sequences, bitstreams and rendered pose
trace videos are on separate servers, listed in the TR.

The study is based on [SP-240479](https://www.3gpp.org/ftp/tsg_sa/TSG_SA/TSGS_103_Maastricht_2024-03/Docs/SP-240479.zip),
*New SID on Feasibility Study on Beyond 2D Video*, and will result in technical report
[TR 26.956](https://www.3gpp.org/dynareport/26956.htm).

The repository has two frameworks, each with its own instructions:

| Folder | Framework |
|---|---|
| [mvd/](mvd/README.md) | Multi-view plus depth evaluation framework |
| [point_cloud/](point_cloud/README.md) | V-PCC framework: tools to generate, decode and analyse V-PCC content |

### Scenarios

The scenarios this repository evaluates are listed below; their descriptions are still to be written.

- Scenario 1: UE-to-UE stereoscopic video live streaming
- Scenario 2: Streaming of professionally produced volumetric video with a single asset containing
  people
- Scenario 3: On-demand streaming of multi-view plus depth

## Contributing

Contributions are welcome. How to raise an issue, fork the repository and open a pull request, and
the Contributor License Agreement required before code can be merged, are described at
<https://www.5g-mag.com/contributing>.

## License

Distributed under the 5G-MAG Public License v1.0. See [LICENSE.md](LICENSE.md).
