import enum
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from enum import Enum
import argparse

from mdata import MData
from burndown import Burndown
from bycapa import Bycapa


def min_capacity():
    print("AOEU")

parser = argparse.ArgumentParser()
parser.add_argument("tool", help="allyear, summer, bycapa")
parser.add_argument("--effcoef", help="Efficiency coefficient")
parser.add_argument("--a", help="Panel area in m²")
parser.add_argument("--target", help="Energy consumption every day in Wh")
parser.add_argument("--target_day", help="Energy consumption every day in Wh at daytime")
parser.add_argument("--target_night", help="Energy consumption every day in Wh at nighttime")
parser.add_argument("--year", help="What year to process")
parser.add_argument("--year_from", help="What year to process")
parser.add_argument("--year_to", help="What year to process")
parser.add_argument("--capa", help="Size of the energy storage in Wh")
parser.add_argument("--price_sell", help="kWh price for selling exess")
parser.add_argument("--price_buy", help="kWh price for buying")

parser.add_argument("--show", action="store_true", help="Shows plots")
parser.add_argument("--show_exess", action="store_true", help="Shows plots")
parser.add_argument("--verbose", action="store_true", help="Verbose printing")

args = parser.parse_args()

print(args)
if args.tool == "allyear":
    bd = Burndown(args)
    bd.run()

elif args.tool == "summer":
    bd = Burndown(args)
    bd.run()

elif args.tool == "bycapa":
    bc = Bycapa(args)
    bc.run()

else:
    parser.print_help()
