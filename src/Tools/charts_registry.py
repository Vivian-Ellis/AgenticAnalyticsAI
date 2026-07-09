# import matplotlib.pyplot as plt
# import seaborn as sns
import sys
sys.path.append("../src/Analysis")
sys.path.append("../src/Tools")
# from datetime import datetime
from Tools.registries.chart_tool_registry import register_chart,get_chart_tool
from pathlib import Path
from bokeh.plotting import figure, column,output_file, save,ColumnDataSource
from bokeh.models import NumeralTickFormatter
from bokeh.models.tools import HoverTool
import json
import numpy as np

CHARTS_DIR = Path(__file__).resolve().parents[2] / "chart_files"
CHARTS_DIR.mkdir(parents=True, exist_ok=True) #if not exist create

PROJECT_ROOT = Path(__file__).resolve().parents[2]
with open(PROJECT_ROOT / "data" / "date_labels.json", "r") as f:
    DATE_LABELS = json.load(f)

def date_cleanup(table):
    for grain in ["WEEK", "MONTH", "QUARTER"]:
        if grain in table.columns:
            table[grain] = (
                table[grain]
                .astype(str)
                .map(DATE_LABELS[grain]))

class Chart:
    def __init__(self,results,chart_type,data_loader):
        self.results=results
        self.chart_type = chart_type
        self.data_loader=data_loader

    def run(self):
        chart_tool = get_chart_tool(self.chart_type)
        return chart_tool["function"](self.results,self.data_loader).plot()

@register_chart(
    "ranking_bar",
    description="Standard sorted bar chart",
    output_type="file_path")
def build_ranking_chart(results,data_loader):
    chart_df = results.original_df.copy()
    chart_df["is_color"] = chart_df["Value"].isin(results.ranked_df["Value"])
    chart_df["color"] = np.where(chart_df["is_color"],"#87a6d4","#d3d3d3")
    # print(chart_df)
    # print(results)
    min_date_observation=chart_df[results.date_grain].min()
    title=f"Ranking {results.series_ids[0]} Since {min_date_observation}"
    chart_df.sort_values(results.date_grain)
    date_cleanup(chart_df)
    return Bar(
        chart_df[results.date_grain],
        chart_df["Value"],
        title,
        chart_df["color"],
        data_loader)

@register_chart(
    "comparison_bar",
    description="Standard bar chart",
    output_type="file_path")
def build_comparison_chart(results,data_loader):
    chart_df = results.descriptive_statistics.copy()
    date_cleanup(chart_df)
    chart_df["color"] ="#87a6d4"
    return Bar(
        chart_df[results.date_grain],
        chart_df["Value"],
        "Comparison Chart",
        chart_df["color"],
        data_loader)

@register_chart(
    "correlation_scatter",
    description="Standard scatter chart",
    output_type="file_path")
def build_correlation_chart(results,data_loader):
    # Only use this when original_df is wide
    return Scatter(
        results.original_df,
        results.series_ids,
        "Correlation Scatter Chart",
        data_loader
    )

@register_chart(
    "trends_timeseries",
    description="Standard timeseries chart",
    output_type="file_path")
def build_timeseries_chart(results,data_loader):
    return TimeSeries(results.original_df,data_loader)
    
class TimeSeries:
    def __init__(self,df,data_loader):
        self.df=df
        self.data_loader=data_loader

    def plot(self):
        x='date'
        y='value'

        min_date_observation=self.df.date.min().strftime("%Y")

        units=self.data_loader.fred_metadata['new_units'][0]
        if units == "Thousands of Persons":
            y_values = self.df[y] / 1000
            units="Millions of Persons"
        else:
            y_values=self.df[y]

        source = ColumnDataSource(data=dict(date=self.df[x], y=y_values))

        y_axis_label=f"Value ({units})"
        title=f"{self.data_loader.fred_metadata['title'][0]} Trends Since {min_date_observation}, {self.data_loader.fred_metadata['seasonal_adjustment'][0]}"

        fig = figure(width=600,
                    height=600,   # square
                    tools="xpan,xwheel_zoom,reset",
                    x_axis_type="datetime",
                    x_axis_location="above",
                    window_axis="x",
                    sizing_mode="scale_width",
                    title=title,
                    y_axis_label=y_axis_label
                    )

        # title
        fig.title.align = "center"
        fig.title.text_color = "black"
        fig.title.text_font_size = "16px"
        fig.title.text_font_style = "normal"
        fig.title.text_font = "Sans-Serif"

        # axis labels
        fig.xaxis.axis_label_text_font_size = "12pt"
        fig.yaxis.axis_label_text_font_size = "12pt"
        fig.xaxis.axis_label_text_font_style = "normal"
        fig.yaxis.axis_label_text_font_style = "normal"
        # tick labels
        fig.xaxis.major_label_text_font_style = "normal"
        fig.yaxis.major_label_text_font_style = "normal"

        # remove outer plot border
        # fig.outline_line_color = None

        # remove axis lines
        fig.xaxis.axis_line_color ="grey"
        fig.yaxis.axis_line_color ="grey"

        # remove tick marks
        fig.xaxis.major_tick_line_color = None
        fig.xaxis.minor_tick_line_color = None
        fig.yaxis.major_tick_line_color = None
        fig.yaxis.minor_tick_line_color = None

        fig.line('date', 'y', source=source,color="#87a6d4",line_width=2)

        fig.add_tools(
            HoverTool(
                tooltips=[
                    ("Date", "@date{%Y-%m}"),
                    (y_axis_label, "@y{0.00}")
                ],
                formatters={
                    "@date": "datetime"
                },
                mode='vline'
            )
        )

        full_trend_layout = column(fig,background="white", sizing_mode="scale_width")
        output_file(f'{CHARTS_DIR}/{title}.html')
        save(full_trend_layout)
        return full_trend_layout

class Bar:
    def __init__(self,x,y,title,colors,data_loader):
        self.x=x
        self.y=y
        self.colors = colors
        self.title=title
        self.data_loader=data_loader

    def plot(self):
        x_values = self.x.astype(str).tolist()
        y_values = self.y.tolist()
    
        table_source = ColumnDataSource(data=dict(
            x=x_values,
            y=y_values,
            color=self.colors))

        table_fig = figure(
            x_range=x_values,
            title=self.title,
            y_axis_label="Value",
            x_axis_label="",
            width=600,
            height=600,   # square
            sizing_mode="scale_width",
            toolbar_location=None
        )

        table_fig.vbar(
            x="x",
            top="y",
            source=table_source,
            width=0.85,
            color="color")

        # title
        table_fig.title.align = "center"
        table_fig.title.text_color = "black"
        table_fig.title.text_font_size = "16px"
        table_fig.title.text_font_style = "normal"
        table_fig.title.text_font = "Sans-Serif"
        # axis labels
        table_fig.xaxis.axis_label_text_font_size = "12pt"
        table_fig.yaxis.axis_label_text_font_size = "12pt"
        table_fig.xaxis.axis_label_text_font_style = "normal"
        table_fig.yaxis.axis_label_text_font_style = "normal"
        # tick labels
        table_fig.xaxis.major_label_text_font_style = "normal"
        table_fig.yaxis.major_label_text_font_style = "normal"
        # remove gridlines
        table_fig.xgrid.grid_line_color = None
        # remove outer plot border
        table_fig.outline_line_color = None
        # remove axis lines
        table_fig.xaxis.axis_line_color = None
        table_fig.yaxis.axis_line_color = None
        # remove tick marks
        table_fig.xaxis.major_tick_line_color = None
        table_fig.xaxis.minor_tick_line_color = None
        table_fig.yaxis.major_tick_line_color = None
        table_fig.yaxis.minor_tick_line_color = None
        # optional numeric formatting
        table_fig.yaxis[0].formatter = NumeralTickFormatter(format="0.00")
        table_fig.add_tools(
            HoverTool(tooltips=[
                # ("Year", "@x"),
                ("Value", "@y{0.00}")
            ])
        )

        full_rating_layout = column(table_fig,background="white", sizing_mode="scale_width")
        output_file(f'{CHARTS_DIR}/{self.title}.html')
        save(full_rating_layout)
        return full_rating_layout

class Scatter:
    def __init__(self,table,series,title,data_loader):
        self.table=table
        self.series=series
        self.title=title
        self.data_loader=data_loader

    def plot(self):
        x_label=f"{self.data_loader.fred_metadata['title'][0]} ({self.data_loader.fred_metadata['new_units'][0]})"
        y_label=f"{self.data_loader.fred_metadata['title'][1]} ({self.data_loader.fred_metadata['new_units'][1]})"
        simple_x_label=self.series[0]
        simple_y_label=self.series[1]
        table_fig = figure(title=self.title,
                           sizing_mode="scale_width",
                            y_axis_label=y_label,
                            x_axis_label=x_label,
                            width=600,
                            height=600,
                            toolbar_location=None)

        # add a scatter circle renderer with a size, color, and alpha
        table_fig.scatter(x=self.table[self.series[0]],y=self.table[self.series[1]], size=20, color="#87a6d4", alpha=0.5)

        # title
        table_fig.title.align = "center"
        table_fig.title.text_color = "black"
        table_fig.title.text_font_size = "16px"
        table_fig.title.text_font_style = "normal"
        table_fig.title.text_font = "Sans-Serif"
        # axis labels
        table_fig.xaxis.axis_label_text_font_size = "12pt"
        table_fig.yaxis.axis_label_text_font_size = "12pt"
        table_fig.xaxis.axis_label_text_font_style = "normal"
        table_fig.yaxis.axis_label_text_font_style = "normal"
        # tick labels
        table_fig.xaxis.major_label_text_font_style = "normal"
        table_fig.yaxis.major_label_text_font_style = "normal"
        # remove outer plot border
        table_fig.outline_line_color = None
        # remove tick marks
        table_fig.xaxis.major_tick_line_color = None
        table_fig.xaxis.minor_tick_line_color = None
        table_fig.yaxis.major_tick_line_color = None
        table_fig.yaxis.minor_tick_line_color = None
        # optional numeric formatting
        table_fig.yaxis[0].formatter = NumeralTickFormatter(format="0.00")
        table_fig.add_tools(
            HoverTool(tooltips=[
                (simple_x_label, "@x{0.00}"),
                (simple_y_label, "@y{0.00}")
            ])
        )

        full_layout = column(table_fig,background="white",sizing_mode="scale_width")
        output_file(f'{CHARTS_DIR}/{self.title}.html')
        save(full_layout)
        return full_layout