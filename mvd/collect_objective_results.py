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

from math import log10
from pathlib import Path
import re
import sys
from typing import Callable
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, Namespace

sys.path.append(Path(__file__).parent)

from configure_experiment import add_test_point_arguments, DEFAULT_VIEW_IDS

RE_QMIV_PSNR = re.compile(r"PSNR\s+Y:Cb:Cr\s+([0-9\.]+) dB\s+[0-9\.]+ dB\s+[0-9\.]+ dB\s*")
RE_QMIV_IVSSIM = re.compile(r"IVSSIM\s+([0-9\.]+)\s*")


class CollectObjectiveResults:
    def __init__(self, args: Namespace):
        self.args = args

    def collect(self):
        for self.__frame_count in self.args.frame_counts:
            with open(
                f"out/objective-results-{self.__frame_count}F.md", mode="w", encoding="utf8"
            ) as stream:
                stream.write(f"# Objective results for {self.__frame_count} coded frames\n")
                self.__collect_for_one_frame_count(stream)

    def __collect_for_one_frame_count(self, stream):
        for self.__content_id in self.args.content_ids:
            stream.write(f"## Objective results for {self.__content_id}\n\n")
            self.__write_table_header(stream)

            for self.__rate_id in self.args.rate_ids:
                self.__write_table_row(stream)

            stream.write("\n")

    def __write_table_header(self, stream):
        stream.write("| Rate point")

        for condition_id in self.args.condition_ids:
            stream.write(f" | {condition_id} bitrate (Mbps)")

        for condition_id in self.args.condition_ids:
            stream.write(f" | {condition_id} PSNR")

        for condition_id in self.args.condition_ids:
            stream.write(f" | {condition_id} IV-SSIM")

        stream.write(" |\n")

        for condition_id in self.args.condition_ids:
            stream.write("|--|--|--")

        stream.write("|--|\n")

    def __write_table_row(self, stream):
        stream.write(f"| {self.__rate_id}")

        for self.__condition_id in self.args.condition_ids:
            stream.write(f" | {self.__bitrate()}")

        for self.__condition_id in self.args.condition_ids:
            stream.write(f" | {self.__psnr()}")

        for self.__condition_id in self.args.condition_ids:
            stream.write(f" | {self.__ivssim()}")

        stream.write(" |\n")

    def __bitrate(self) -> float:
        bitstream_file = Path(
            f"out/{self.__condition_id}{self.__frame_count}/{self.__content_id}/{self.__rate_id}"
            f"/TMIV_{self.__condition_id}{self.__frame_count}_{self.__content_id}"
            f"_{self.__rate_id}.bit"
        )
        return 8e-6 * bitstream_file.stat().st_size * self.__frame_rate() / self.__frame_count

    def __psnr(self) -> float:
        view_ids = DEFAULT_VIEW_IDS[self.__content_id]
        sum_mse = 0.0

        for self.__view_id in view_ids:
            metrics = self.__objective_metrics()
            sum_mse = sum_mse + 10.0 ** (-0.1 * metrics["PSNR"])

        return -10.0 * log10(sum_mse / len(view_ids))

    def __ivssim(self) -> float:
        view_ids = DEFAULT_VIEW_IDS[self.__content_id]
        sum_ssim = 0.0

        for self.__view_id in view_ids:
            metrics = self.__objective_metrics()
            sum_ssim = sum_ssim + metrics["IVSSIM"]
        
        return sum_ssim / len(view_ids)

    def __objective_metrics(self) -> dict:
        file = Path(
            f"out/{self.__condition_id}{self.__frame_count}/{self.__content_id}/{self.__rate_id}"
            f"/{self.__condition_id}{self.__frame_count}_{self.__content_id}_{self.__rate_id}"
            f"_{self.__view_id}.qmiv"
        )

        result = {}

        with open(file, encoding="utf8") as stream:
            for line in stream.readlines():
                if match := RE_QMIV_PSNR.match(line):
                    result["PSNR"] = float(match[1])
                elif match := RE_QMIV_IVSSIM.match(line):
                    result["IVSSIM"] = float(match[1])

        return result

    def __frame_rate(self) -> float:
        return {"Breakfast": 30.0, "Bartender": 30.0, "DanceMoves": 15.0}[self.__content_id]


def parse_arguments() -> Namespace:
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)

    add_test_point_arguments(parser)

    return parser.parse_args()


def main(args: Namespace):
    CollectObjectiveResults(args).collect()


if __name__ == "__main__":
    main(parse_arguments())
