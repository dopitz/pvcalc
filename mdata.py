from enum import Enum
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

class Units(Enum):
    Wh = 0
    kWh = 1
    J = 2

Jcm2_to_Wm2 = 10000.0 / 3600.0

class MData:
    def __init__(self, args):
        self.Unit = Units.kWh

        self.effcoef = float(args.effcoef) if args.effcoef else 0.16
        self.a = float(args.a) if args.a else 12
        self.target_day = float(args.target_day) if args.target_day else 2000
        self.target_night = float(args.target_night) if args.target_night else 2000
        self.target = self.target_day + self.target_night
        self.capa = float(args.capa) if args.capa else 10000
        self.price_sell = float(args.price_sell) if args.price_sell else 0.0623
        self.price_buy = float(args.price_buy) if args.price_buy else 0.39

        self.show = args.show
        self.show_exess = args.show_exess
        self.verbose = args.verbose

        self.read_data()

        self.year_from = int(args.year_from) if args.year_from else self.df["year"].min()
        self.year_to = int(args.year_to) if args.year_to else self.df["year"].max() + 1
        if args.year:
            self.year_from = int(args.year)
            self.year_to = self.year_from + 1


    def read_data(self):
        df = pd.read_csv("produkt_st_tag_19790101_20220831_05906.txt", sep=";")[["MESS_DATUM", "FG_STRAHL", "SD_STRAHL"]].rename(
            columns={"MESS_DATUM": "date", "FG_STRAHL": "fg", "SD_STRAHL": "sd"}
        )
    
        df = df[df["fg"] != -999.0]
    
        df["date"] = pd.to_datetime(df["date"], format="%Y%m%d")
        df["year"] = pd.DatetimeIndex(df["date"]).year
        df["month"] = pd.DatetimeIndex(df["date"]).month
        df["season"] = "winter"
        df.loc[(df["month"] > 4) & (df["month"] < 9), "season"] = "summer"
    
        # Change units from J/cm² to W/m²
        df["fg"] = df["fg"] * Jcm2_to_Wm2
        df["yield"] = df["fg"] * self.a * self.effcoef
        df["surplus"] = df["yield"] - self.target
        df["yield < target"] = df["surplus"] < 0
        df["target"] = self.target
        df["target_day"] = self.target_day
        df["target_night"] = self.target_night
        self.df = df

    def run(self):
        self.init_sumstats()
        for y in range(self.year_from, self.year_to):
            self.year = y
            s = self.compute()
            if s:
                self.append_sumstats(s)

        sumstats = pd.DataFrame(self.stats)

        print("\n\n\n")
        print("SUM \n")
        print(f"avg yield min Wh            {sumstats['yield min'].mean()}")
        print(f"avg yield min date          {sumstats['yield min date'].apply(lambda x: x.timetuple().tm_yday).mean()}")
        print(f"avg yield max Wh            {sumstats['yield max'].mean()}")
        print(f"avg yield max date          {sumstats['yield max date'].apply(lambda x: x.timetuple().tm_yday).mean()}")
        print(f"avg #days yield < target    {sumstats['#days yield < target'].mean()}")
        print(f"avg #days yield > target    {sumstats['#days yield > target'].mean()}")
        print(f"avg generated Wh            {sumstats['generated Wh'].mean()}")
        print(f"avg exess Wh                {sumstats['exess Wh'].mean()}")
        print(f"avg deficient Wh            {sumstats['deficient Wh'].mean()}")
        print(f"avg savings Wh              {sumstats['savings Wh'].mean()}")
        print(f"avg yearly savings €        {sumstats['savings Euro'].mean()}")
        return sumstats

    def compute(self):
        stats = {}
        return stats

    def init_sumstats(self):
        self.stats = []

    def make_stats(self, df):
        stats = {}
        stats["year"] = self.year
        stats["yield min"] = df["yield"].min()
        stats["yield min date"] = df[df["yield"] == stats["yield min"]]["date"].iloc[0].date()
        stats["yield max"] = df["yield"].max()
        stats["yield max date"] = df[df["yield"] == stats["yield max"]]["date"].iloc[0].date()
        stats["#days yield < target"] = df["yield < target"].value_counts()[True]
        stats["#days yield > target"] = df["yield < target"].value_counts()[False]
        stats["generated Wh"] = df["yield"].sum()
        stats["exess Wh"] = df["exess Wh"].sum()
        stats["deficient Wh"] = df["deficient Wh"].sum()
        stats["savings Wh"] = df["savings Wh"].sum()
        stats["savings Euro"] = stats["exess Wh"] / 1000 * self.price_sell + stats["savings Wh"] / 1000 * self.price_buy
        return stats

    def append_sumstats(self, s):
        self.stats.append(s)
        if self.verbose:
            print(f"YEAR   {s['year']}")
            print(f"----------------------\n")
            print(f"yield min               {s['yield min']}")
            print(f"yield min date          {s['yield min date']}")
            print(f"yield max               {s['yield max']}")
            print(f"yield max date          {s['yield max date']}")
            print(f"#days yield < target    {s['#days yield < target']}")
            print(f"#days yield > target    {s['#days yield > target']}")

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
                y=df["yield"],
                mode="lines",
                name="yield",
                line_color="orange",
            ),
        )
        fig.add_trace(
            go.Scatter(
                x=df.date,
                y=df.burndown,
                mode="lines",
                name="burndown",
                line_color="blue",
            ),
        )
        fig.add_trace(
            go.Scatter(
                x=df.date,
                y=df["target"],
                mode="markers+lines",
                name="not self sufficient days",
                marker_color=df["is selfsufficient day"].apply(lambda x: "green" if x else "red"),
                line_color="gray",
            ),
        )
        if self.show_exess:
            fig.add_trace(
                go.Scatter(
                    x=df.date,
                    y=df["exess Wh"].cumsum(),
                    mode="lines",
                    name="exess",
                    line_color="green",
                ),
            )
            fig.add_trace(
                go.Scatter(
                    x=df.date,
                    y=df["deficient Wh"].cumsum(),
                    mode="lines",
                    name="deficient",
                    line_color="red",
                ),
            )
    
        fig.show(
            config={
                "scrollZoom": True,
                "modeBarButtonsToAdd": ["drawrect", "eraseshape"],
                "modeBarButtonsToRemove": ["select", "lasso2d"],
            }
        )



    def print_w(self, watts):
        if self.Unit == Units.Wh:
            return watts
        elif self.Unit == Units.kWh:
            return watts / 1000.0
        else:  # PRINT_UNIT == Units.J:
            return watts * 3600
