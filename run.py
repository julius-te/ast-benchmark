#!/usr/bin/env python

from typing import Any
import os
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from tabulate import tabulate
from tqdm import tqdm
from enum import Enum
from multiprocessing import Pool
from functools import partial

OPTIONS = "%OPTIONS%"

class Bound(Enum):
    FINITE = 1
    INFINITE = 2
    ERROR = 3

    def __str__(self) -> str:
        if self == Bound.FINITE:
            return "\033[92mF\033[0m"
        elif self == Bound.INFINITE:
            return "\033[91m∞\033[0m"
        else:
            return "?"

    @staticmethod
    def parse_output(output: str) -> str:
        if "Infinity" in output or "Infinite" in output:
            return Bound.INFINITE
        elif "Arg_" in output or "Finite" in output or "O(1)" in output:
            return Bound.FINITE
        else:
            print(output)
            return Bound.ERROR

    def __lt__(self, other):
        if self == Bound.ERROR:
            return False
        if other == Bound.ERROR:
            return True
        return self.value < other.value

def process_tool_and_file(file: str, cmd: str, options: dict[str, str]) -> str:
    min_bound, min_option = Bound.ERROR, ""
    for optionName in options:
        exec = cmd.replace(OPTIONS, options[optionName])
        output = os.popen(exec + " " + file).read()
        result = Bound.parse_output(output)
        if result < min_bound:
            min_bound = result
            min_option = optionName
        if min_bound == Bound.FINITE:
            break

    if min_bound != Bound.FINITE or min_option == "default":
        return min_bound
    else:
        return f"{min_bound} [{min_option}]"

def process_file(file: str, tools: dict[str, Any]) -> list[str]:
    row = [file]
    for toolName in tools:
        cmd = tools[toolName]["cmd"]
        options = tools[toolName]["options"]
        row.append(process_tool_and_file(file, cmd, options))
    return row

def cartesian_product(*options: dict[str, str]) -> dict[str, str]:
    """
    For input {"a": "1", "b": "2"}, {"c": "3"}, {"d": "4", "e": "5"} return
    {"a,c,d": "1 3 4", "a,c,e": "1 3 5", "b,c,d": "2 3 4", "b,c,e": "2 3 5"}
    """
    if len(options) == 1:
        return options[0]
    else:
        result = {}
        for key in options[0]:
            for sub_key, sub_value in cartesian_product(*options[1:]).items():
                result[key + ", " + sub_key] = options[0][key] + " " + sub_value
        return result

parser = ArgumentParser(description="Benchmark termination analysis tools", formatter_class=ArgumentDefaultsHelpFormatter)
parser.add_argument("-k", "--koat", type=str, default="./koat", help="path to the KoAT executable", metavar="PATH_TO_KOAT")
parser.add_argument("-p", "--programs", type=str, default="examples", help="path to a folder with programs to benchmark", metavar="FOLDER")
args = parser.parse_args()

path_to_koat = args.koat

koat_options = cartesian_product(
    {
        "past": "--goal PAST --plrf ED",
        "\033[93mast ed\033[0m": "--goal AST --plrf ED",
        "\033[94mast asd\033[0m": "--goal AST --plrf ASD",
    },
    {
        "cfr off": "",
        "cfr fvs": "--pe --pe-fvs",
        "cfr loop heads": "--pe",
    },
    {
        "twn off, mprf off": "",
        "twnlog, mprf off": "--classic-local twnlog",
        "twn, mprf off": "--classic-local twn",
        "twnlog, mprf on": "--classic-local twnlog,mprf",
        "twn, mprf on": "--classic-local twn,mprf",
    },
)

tools = {
    "KoAT2": {
        "cmd": f"{path_to_koat} prob-analyse {OPTIONS} -i",
        "options": koat_options
    }
}

directoy = args.programs
extension = ".koat"


files = [os.path.join(dp, f) for dp, dn, filenames in os.walk(directoy) for f in filenames if f.endswith(extension)]

with Pool() as pool:
    table = list(tqdm(pool.imap(partial(process_file, tools=tools), files), total=len(files)))

print(tabulate(table, headers=["File"] + [tool for tool in tools], tablefmt="plain"))
