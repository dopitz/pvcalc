import enum
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from enum import Enum
import argparse
from datetime import datetime

from mdata import MData

class Burndown(MData):
    def __init__(self, args):
        super().__init__(args)

        self.year_from = int(args.year_from) if args.year_from else self.df["year"].min()
        self.year_to = int(args.year_to) if args.year_to else self.df["year"].max() + 1
        if args.year:
            self.year_from = int(args.year)
            self.year_to = self.year_from + 1
        self.show = args.show
        self.verbose = args.verbose

    def run(self):
        stats = []
        sumstats = {}
        sumstats["avg yield min"] = 0
        sumstats["avg yield min date"] = 356
        sumstats["avg yield max"] = 0
        sumstats["avg yield max date"] = 0
        sumstats["avg days below target"] = 0
        sumstats["avg days above target"] = 0
        sumstats["avg capacity"] = 0
        sumstats["num selfsufficient"] = 0
        for y in range(self.year_from, self.year_to):
            self.year = y
            s = self.compute()
            if s:
                stats.append(s)
                self.printstats(s, sumstats)

        d = self.year_to - self.year_from
        #sumstats["avg yield min date"] = min(sumstats["avg yield min date"], s["yield min date"])
        #sumstats["avg yield max date"] = min(sumstats["avg yield max date"], s["yield max date"])
        sumstats["avg days below target"] = sumstats["avg days below target"] / d
        sumstats["avg days above target"] = sumstats["avg days above target"] / d
        sumstats["avg capacity"] = sumstats["avg capacity"] / d
        sumstats["num selfsufficient"] = sumstats["num selfsufficient"] + s["is self sufficient"]

        print(f"avg yield min       {sumstats['avg yield min']} W")
        print(f"avg yield max       {sumstats['avg yield max']} W")
        print(f"avg days below tar  {sumstats['avg days below target']}")
        print(f"avg days above tar  {sumstats['avg days above target']}")
        print(f"avg capacity        {sumstats['avg capacity']} Wh")
        print(f"num selfsufficient  {sumstats['num selfsufficient']} of {d}")


    def compute(self):
        stats = {}

        df = self.df
        df = df[df["year"] == self.year].copy().reset_index()
    
        if df.empty:
            return stats
    
        stats["year"] = self.year
        stats["is self sufficient"] = True
        stats["yield min"] = df["yield"].min()
        stats["yield min date"] = df[df["yield"] == stats["yield min"]]["date"].iloc[0].date()
        stats["yield max"] = df["yield"].min()
        stats["yield max date"] = df[df["yield"] == stats["yield max"]]["date"].iloc[0].date()
        stats["days below target"] = df["missed_target"].value_counts()[True]
        stats["days above target"] = df["missed_target"].value_counts()[False]
    
        def make_burndown_range(capacity_start, r=range(0, len(df.index))):
            c = capacity_start
            burndown = []
            for i in r:
                s = df.iloc[i]["surplus"]
                c = c + s
                if c > 0:
                    c = 0
                burndown.append(c)
            return burndown  # pd.Series(burndown, name="burndown")
    
        def find_last_full_capa():
            full_capa = df[df["burndown"] == 0]
            if full_capa.empty:
                return None
            return full_capa.index[-1]
    
        # assume full capacity at Jan 1st and cummulate daily consumption
        df["burndown"] = make_burndown_range(0)
    
        i_last_full_capa = find_last_full_capa()
        if not i_last_full_capa:
            stats["is self sufficient"] = False
            return stats
    
        # find leftover capacity at year's end
        xx = make_burndown_range(0, range(i_last_full_capa, len(df.index)))
        capacity_start = -make_burndown_range(0, range(i_last_full_capa, len(df.index)))[-1]
    
        # compute breakdown with leftover capacity
        df["burndown"] = make_burndown_range(-capacity_start)
        # check that we are self sufficient
        i_last_full_capa = find_last_full_capa()
        if not i_last_full_capa:
            stats["is self sufficient"] = False
            return stats
        
        capacity = -df["burndown"].min()
        df["burndown"] = df["burndown"] + capacity

        stats["capacity"] = capacity


        self.showplot(df)

        return stats
    
    

    def showplot(self, df):
        if not self.show:
            return 

        fig = make_subplots(
            rows=1,
            cols=1,
            shared_xaxes=True,
        )
    
        fig.update_layout(title_text=f"{self.year}", barmode="relative", dragmode="pan")
    
        fig.add_trace(
            go.Scatter(
                x=df.date,
                y=df.surplus,
                mode="lines",
                name="surplus",
            ),
        )
        fig.add_trace(
            go.Scatter(
                x=df.date,
                y=df["yield"],
                mode="lines",
                name="surplus",
            ),
        )
        fig.add_trace(
            go.Scatter(
                x=df.date,
                y=df.burndown,
                mode="lines",
                name="burndown",
            ),
        )
    
        fig.show(
            config={
                "scrollZoom": True,
                "modeBarButtonsToAdd": ["drawrect", "eraseshape"],
                "modeBarButtonsToRemove": ["select", "lasso2d"],
            }
        )

    def printstats(self, s, ss):
        if self.verbose:
            print(f"YEAR   {s['year']}")
            print(f"----------------------\n")
            print(f"is self sufficient: {s['is self sufficient']}")
            print(f"yield min           {s['yield min']}")
            print(f"yield min date      {s['yield min date']}")
            print(f"yield max           {s['yield max']}")
            print(f"yield max date      {s['yield max date']}")
            print(f"days below target   {s['days below target']}")
            print(f"days above target   {s['days above target']}")
            print(f"min capacity        {s['capacity']}")

        ss["avg yield min"] = min(ss["avg yield min"], s["yield min"])
        #ss["avg yield min date"] = min(ss["avg yield min date"], s["yield min date"])
        ss["avg yield max"] = max(ss["avg yield max"], s["yield max"])
        #ss["avg yield max date"] = min(ss["avg yield max date"], s["yield max date"])
        ss["avg days below target"] = ss["avg days below target"] + s["days below target"]
        ss["avg days above target"] = ss["avg days above target"] + s["days above target"]
        ss["avg capacity"] = ss["avg capacity"] + s["capacity"]
        ss["num selfsufficient"] = ss["num selfsufficient"] + s["is self sufficient"]