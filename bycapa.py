import enum
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from enum import Enum
import argparse
from datetime import datetime

from mdata import MData

class Bycapa(MData):
    def __init__(self, args):
        super().__init__(args)

    def run(self):
        sumstats = super().run()
        print(f"self sufficiency %          {sumstats['self sufficiency %'].mean()}")


    def compute(self):
        stats = {}

        df = self.df
        df = df[df["year"] == self.year].copy().reset_index()
    
        if df.empty:
            return stats
    

        c = 0
        burndown = []
        for i in range(0, len(df.index)):
            s = df.iloc[i]["surplus"]
            c = c + s
            if c > self.capa:
                c = self.capa 
            if c < 0:
                c = 0
            burndown.append(c)
    
        df["burndown"] = burndown
        df["is selfsufficient day"] = (df["burndown"].shift() + df["yield"] > df["target"]) & (df["burndown"] > df["target_night"])
        df["exess Wh"] = (df["burndown"].shift() + df["yield"] - self.capa).clip(lower=0)
        df["deficient Wh"] = ((df["burndown"].shift(-1) + df["yield"] - self.capa) * -1).clip(lower=0)
        df["savings Wh"] = df["yield"]
        df.loc[df["is selfsufficient day"], "savings Wh"] = df["target"]

        self.showplot(df)

        return self.make_stats(df)
    
    

    def showplot(self, df):
        super().showplot(df)

    def make_stats(self, df):
        s = super().make_stats(df)
        s["self sufficiency %"] = df["is selfsufficient day"].sum() / len(df.index) * 100
        return s
