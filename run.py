#!/usr/bin/env python

from typing import Callable, Any
import os
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

    if min_option == "default":
        return min_bound
    else:
        return f"{min_bound} ({min_option})"

def process_file(file: str, tools: dict[str, Any]) -> list[str]:
    row = [file]
    for toolName in tools:
        cmd = tools[toolName]["cmd"]
        options = tools[toolName]["options"]
        row.append(process_tool_and_file(file, cmd, options))
    return row

path_to_koat = "~/uni/ba/KoAT2/_build/default/bin/main.exe prob-analyse"

koat_options = {
    "default": "",
    "cfr fvs": "--pe --pe-fvs",
    "cfr loop heads": "--pe"
}

tools = {
    "KoAT2 PAST": {
        "cmd": f"{path_to_koat} --goal PAST --plrf ED {OPTIONS} -i",
        "options": koat_options
    },
    "KoAT2 AST (ED)": {
        "cmd": f"{path_to_koat} --goal AST --plrf ED {OPTIONS} -i",
        "options": koat_options
    },
    "KoAT2 AST (ASD)": {
        "cmd": f"{path_to_koat} --goal AST --plrf ASD {OPTIONS} -i",
        "options": koat_options
    }
}

directoy = "examples"
extension = ".koat"


files = [os.path.join(dp, f) for dp, dn, filenames in os.walk(directoy) for f in filenames if f.endswith(extension)]

with Pool() as pool:
    table = list(tqdm(pool.imap(partial(process_file, tools=tools), files), total=len(files)))

print(tabulate(table, headers=["File"] + [tool for tool in tools], tablefmt="plain"))
