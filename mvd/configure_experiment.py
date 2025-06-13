#!/usr/bin/env python3
# --------------------------------------------------------------------------------
# Copyright © 2025, Koninklijke Philips N.V.
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
# --------------------------------------------------------------------------------

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, Namespace
from ninja.ninja_syntax import Writer as NinjaWriter
from pathlib import Path
from typing import Callable
import sys

LINE_WIDTH = 100
DEFAULT_CONDITIONS = ["A", "FV", "SCV"]
DEFAULT_FRAME_COUNTS = [3, 65]
DEFAULT_CONTENT_IDS = ["Bartender", "Breakfast", "DanceMoves"]
DEFAULT_RATE_IDS = ["RP1", "RP2", "RP3", "RP4"]

DEFAULT_VIEW_IDS = {
    "Breakfast": [f"v{i}" for i in range(15)],
    "Bartender": [f"v{i:02}" for i in range(21)],
    "DanceMoves": [f"v{i}" for i in range(6)],
}

DEFAULT_POSE_TRACE_IDS = {
    "Breakfast": ["p02"],
    "Bartender": ["p01"],
    "DanceMoves": ["p02"],
}


class MvdExperiment:
    def __init__(self, args: Namespace):
        self.args = args

    def configure(self):
        if self.args.slurm:
            self.__write_slurm_script()

        self.__write_ninja_build_file()

    def __write_slurm_script(self):
        self.slurm_script_file = Path("slurm_script.sh")

        if not self.slurm_script_file.is_file():
            with open(self.slurm_script_file, mode="w", encoding="utf8") as stream:
                stream.write("#!/bin/sh\n")
                stream.write("# Additional sbatch parameters can be added here.")
                stream.write(" See https://slurm.schedmd.com/sbatch.html\n\n")
                stream.write("set -e\n")
                stream.write('/bin/time -v "@"\n')

            self.slurm_script_file.chmod(0o755)

    def __write_ninja_build_file(self):
        with open("build.ninja", mode="w") as stream:
            self.__writer = NinjaWriter(stream, width=LINE_WIDTH)  # type: ignore
            self.__write_preamble()

            self.__write_encode_rp0_rule()
            self.__write_encode_rpx_rule()
            self.__write_reconstruct_rule()
            self.__write_interpolation_rule()
            self.__write_measure_rule()

            self.__each_rp0_encoding(self.__write_encode_rp0_step)
            self.__each_rpx_encoding(self.__write_encode_rpx_step)
            self.__each_reconstruction(self.__write_reconstruct_step)
            self.__each_interpolation(self.__write_interpolation_step)
            self.__each_reconstruction(self.__write_measure_step)

    def __write_preamble(self):
        self.__writer.variable("ninja_required_version", "1.11")
        self.__writer.variable("python", sys.executable)
        self.__writer.variable("content_dir", self.args.content_dir)
        self.__writer.variable("thread_count", str(self.args.thread_count))
        self.__writer.newline()

    def __write_encode_rp0_rule(self):
        job_name = "E_${condition_id}_${frame_count}_${content_id}"
        self.__writer.rule(
            name="encode_RP0",
            command=f"{self.__launch(job_name)}$python tmiv/bin/encode.py"
            " --input-dir $content_dir"
            " --output-dir out"
            " --content-id $content_id"
            " --frame-count $frame_count"
            " --rate-id RP0"
            " --encoder-config-file config/conditions/$condition_id"
            "/${condition_id}_1_TMIV_encode.json"
            " --video-encoder-id HM"
            " --install-dir tmiv"
            " --config-dir config"
            " --thread-count $thread_count",
            description="Encode $condition_id$frame_count $content_id RP0",
        )
        self.__writer.newline()

    def __write_encode_rpx_rule(self):
        job_name = "E_${condition_id}_${frame_count}_${content_id}_${rate_id}"
        self.__writer.rule(
            name="encode_RPx",
            command=f"{self.__launch(job_name)}$python tmiv/bin/encode.py"
            " --input-dir $content_dir"
            " --output-dir out"
            " --content-id $content_id"
            " --frame-count $frame_count"
            " --rate-id $rate_id"
            " --encoder-config-file config/conditions/$condition_id"
            "/${condition_id}_1_TMIV_encode.json"
            " --multiplexer-config-file config/conditions/$condition_id"
            "/${condition_id}_3_TMIV_mux.json"
            " --video-encoder-config-file tmiv/share/config/hm/encoder_randomaccess_main10.cfg"
            " --qp-file config/fixed_QPs.csv"
            " --video-encoder-id HM"
            " --config-dir config"
            " --install-dir tmiv"
            " --thread-count $thread_count",
            description="Encode $condition_id$frame_count $content_id $rate_id",
        )
        self.__writer.newline()

    def __write_reconstruct_rule(self):
        job_name = (
            "R_${condition_id}_${frame_count}_${content_id}_${rate_id}_${view_id}"
        )
        self.__writer.rule(
            name="reconstruct",
            command=f"{self.__launch(job_name)}tmiv/bin/TmivDecoder"
            " -s $content_id"
            " -n $frame_count"
            " -N $frame_count"
            " -r $rate_id"
            " -v $view_id"
            " -c config/conditions/$condition_id/${condition_id}_4_TMIV_decode.json"
            " -p configDirectory config"
            " -p inputDirectory out"
            " -p outputDirectory out"
            " -j $thread_count",
            description="Reconstruct $condition_id$frame_count $content_id $rate_id $view_id",
        )
        self.__writer.newline()

    def __write_interpolation_rule(self):
        job_name = (
            "I_${condition_id}_${frame_count}_${content_id}_${rate_id}_${pose_trace_id}"
        )
        self.__writer.rule(
            name="interpolate",
            command=f"{self.__launch(job_name)}tmiv/bin/TmivDecoder"
            " -s $content_id"
            " -n $frame_count"
            " -N $output_frame_count"
            " -r $rate_id"
            " -P $pose_trace_id"
            " -c config/conditions/$condition_id/${condition_id}_4_TMIV_decode.json"
            " -p configDirectory config"
            " -p inputDirectory out"
            " -p outputDirectory out"
            " -j $thread_count",
            description="Interpolate $condition_id$frame_count $content_id $rate_id $pose_trace_id",
        )
        self.__writer.newline()

    def __write_measure_rule(self):
        job_name = (
            "M_${condition_id}_${frame_count}_${content_id}_${rate_id}_${view_id}"
        )
        self.__writer.rule(
            name="measure",
            command="rm out/$condition_id$frame_count/$content_id/$rate_id"
            "/$condition_id${frame_count}_${content_id}_${rate_id}_${view_id}.qmiv"
            f" && {self.__launch(job_name)}./qmiv"
            " -i0 $content_dir/$content_id/${view_id}_texture_1920x1080_yuv420p10le.yuv"
            " -i1 out/$condition_id$frame_count/$content_id/$rate_id/$condition_id${frame_count}"
            "_${content_id}_${rate_id}_${view_id}_tex_1920x1080_yuv420p10le.yuv"
            " -r out/$condition_id$frame_count/$content_id/$rate_id/$condition_id${frame_count}"
            "_${content_id}_${rate_id}_${view_id}.qmiv"
            " -pw 1920 -ph 1080 -bd 10 -cf 420"
            " -s0 0 -s1 0 -nf $frame_count"
            " -nth $thread_count",
            description="Measure $condition_id$frame_count $content_id $rate_id $view_id",
        )
        self.__writer.newline()

    def __launch(self, job_name: str) -> str:
        if self.args.slurm:
            Path("out/slurm").mkdir(parents=True, exist_ok=True)
            return (
                f"sbatch --job-name={job_name}"
                f" --error=out/slurm/{job_name}-%A.log --output=out/slurm/{job_name}-%A.log"
                f" --cpus-per-task=$thread_count {self.slurm_script_file} -- "
            )

        return ""

    def __each_rp0_encoding(self, visitor: Callable[[], None]):
        for self.__condition_id in self.args.condition_ids:
            for self.__frame_count in self.args.frame_counts:
                for self.__content_id in self.args.content_ids:
                    visitor()

    def __each_rpx_encoding(self, visitor: Callable[[], None]):
        for self.__condition_id in self.args.condition_ids:
            for self.__frame_count in self.args.frame_counts:
                for self.__content_id in self.args.content_ids:
                    for self.__rate_id in self.args.rate_ids:
                        visitor()

    def __each_reconstruction(self, visitor: Callable[[], None]):
        for self.__condition_id in self.args.condition_ids:
            for self.__frame_count in self.args.frame_counts:
                for self.__content_id in self.args.content_ids:
                    for self.__rate_id in self.args.rate_ids:
                        for self.__view_id in self.__view_ids():
                            visitor()

    def __each_interpolation(self, visitor: Callable[[], None]):
        for self.__condition_id in self.args.condition_ids:
            for self.__frame_count in self.args.frame_counts:
                for self.__content_id in self.args.content_ids:
                    for self.__rate_id in self.args.rate_ids:
                        for self.__pose_trace_id in self.__pose_trace_ids():
                            visitor()

    def __view_ids(self) -> list[str]:
        return DEFAULT_VIEW_IDS[self.__content_id]

    def __pose_trace_ids(self) -> list[str]:
        return DEFAULT_POSE_TRACE_IDS[self.__content_id]

    def __write_encode_rp0_step(self):
        self.__writer.build(
            outputs=[self.__rp0_bitstream_file()],
            rule="encode_RP0",
            variables={
                "condition_id": self.__condition_id,
                "frame_count": self.__frame_count,
                "content_id": self.__content_id,
            },
        )
        self.__writer.newline()

    def __write_encode_rpx_step(self):
        self.__writer.build(
            outputs=[self.__rpx_bitstream_file()],
            inputs=[self.__rp0_bitstream_file()],
            rule="encode_RPx",
            variables={
                "condition_id": self.__condition_id,
                "frame_count": self.__frame_count,
                "content_id": self.__content_id,
                "rate_id": self.__rate_id,
            },
        )
        self.__writer.newline()

    def __write_reconstruct_step(self):
        self.__writer.build(
            outputs=[self.__reconstructed_file()],
            inputs=[self.__rpx_bitstream_file()],
            rule="reconstruct",
            variables={
                "condition_id": self.__condition_id,
                "frame_count": self.__frame_count,
                "content_id": self.__content_id,
                "rate_id": self.__rate_id,
                "view_id": self.__view_id,
            },
        )
        self.__writer.newline()

    def __write_interpolation_step(self):
        self.__writer.build(
            outputs=[self.__interpolated_file()],
            inputs=[self.__rpx_bitstream_file()],
            rule="interpolate",
            variables={
                "condition_id": self.__condition_id,
                "frame_count": self.__frame_count,
                "output_frame_count": 4 * self.__frame_count,
                "content_id": self.__content_id,
                "rate_id": self.__rate_id,
                "pose_trace_id": self.__pose_trace_id,
            },
        )
        self.__writer.newline()

    def __write_measure_step(self):
        self.__writer.build(
            outputs=[self.__metrics_file()],
            inputs=[self.__reconstructed_file()],
            rule="measure",
            variables={
                "condition_id": self.__condition_id,
                "frame_count": self.__frame_count,
                "content_id": self.__content_id,
                "rate_id": self.__rate_id,
                "view_id": self.__view_id,
            },
        )
        self.__writer.newline()

    def __rp0_bitstream_file(self) -> str:
        return (
            f"{self.__rp0_dir()}/TMIV_{self.__condition_id}{self.__frame_count}"
            f"_{self.__content_id}_RP0.bit"
        )

    def __rpx_bitstream_file(self) -> str:
        return (
            f"{self.__rpx_dir()}/TMIV_{self.__condition_id}{self.__frame_count}"
            f"_{self.__content_id}_{self.__rate_id}.bit"
        )

    def __reconstructed_file(self) -> str:
        return (
            f"{self.__rpx_dir()}/{self.__condition_id}{self.__frame_count}_{self.__content_id}"
            f"_{self.__rate_id}_{self.__view_id}_tex_1920x1080_yuv420p10le.yuv"
        )

    def __metrics_file(self) -> str:
        return (
            f"{self.__rpx_dir()}/{self.__condition_id}{self.__frame_count}_{self.__content_id}"
            f"_{self.__rate_id}_{self.__view_id}.qmiv"
        )

    def __interpolated_file(self) -> str:
        return (
            f"{self.__rpx_dir()}/{self.__condition_id}{self.__frame_count}_{self.__content_id}"
            f"_{self.__rate_id}_{self.__pose_trace_id}_tex_1920x1080_yuv420p10le.yuv"
        )

    def __rp0_dir(self) -> str:
        return f"out/{self.__condition_id}{self.__frame_count}/{self.__content_id}/RP0"

    def __rpx_dir(self) -> str:
        return f"out/{self.__condition_id}{self.__frame_count}/{self.__content_id}/{self.__rate_id}"


def parse_arguments() -> Namespace:
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)

    parser.add_argument(
        "--content-dir",
        type=Path,
        required=True,
        help="base directory of the content with a sub-directory for each content item",
    )
    parser.add_argument(
        "--condition-ids",
        type=str,
        nargs="*",
        default=DEFAULT_CONDITIONS,
        help="list of coding conditions to evaluate",
    )
    parser.add_argument(
        "--frame-counts",
        type=int,
        nargs="*",
        default=DEFAULT_FRAME_COUNTS,
        help="list of input frame counts to evaluate",
    )
    parser.add_argument(
        "--content-ids",
        type=str,
        nargs="*",
        default=DEFAULT_CONTENT_IDS,
        help="list of content items to evaluate",
    )
    parser.add_argument(
        "--rate-ids",
        type=str,
        nargs="*",
        default=DEFAULT_RATE_IDS,
        help="list of rate points to evaluate",
    )
    parser.add_argument(
        "--slurm",
        action="store_true",
        help="run each job as a batch job on the default partition of a Slurm cluster",
    )
    parser.add_argument(
        "--thread-count",
        type=int,
        default=4,
        help="specify the maximum number of threads per job",
    )

    return parser.parse_args()


def main(args: Namespace):
    MvdExperiment(args).configure()


if __name__ == "__main__":
    main(parse_arguments())
