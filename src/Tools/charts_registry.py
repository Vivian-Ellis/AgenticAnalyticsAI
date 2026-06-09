import matplotlib.pyplot as plt
import seaborn as sns
import sys
sys.path.append("../src/Analysis")
sys.path.append("../src/Tools")
from datetime import datetime
from Tools.registries.chart_tool_registry import register_chart,get_chart_tool
from pathlib import Path
from bokeh.plotting import figure, column,output_file, save,ColumnDataSource
from bokeh.models import NumeralTickFormatter
from bokeh.models.tools import HoverTool
import json

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
    def __init__(self,results,chart_type):
        self.results=results
        self.chart_type = chart_type

    def run(self):
        chart_tool = get_chart_tool(self.chart_type)
        return chart_tool["function"](self.results).plot()

@register_chart(
    "ranking_bar",
    description="Standard sorted bar chart",
    output_type="file_path")
def build_ranking_chart(results):
    chart_df = results.ranked_df.copy()
    date_cleanup(chart_df)
    return Bar(
        chart_df[results.date_grain],
        chart_df["Value"],
        "Ranking Chart")

@register_chart(
    "comparison_bar",
    description="Standard bar chart",
    output_type="file_path")
def build_comparison_chart(results):
    chart_df = results.descriptive_statistics.copy()
    date_cleanup(chart_df)
    return Bar(
        chart_df[results.date_grain],
        chart_df["Value"],
        "Comparison Chart")

@register_chart(
    "correlation_scatter",
    description="Standard scatter chart",
    output_type="file_path")
def build_correlation_chart(results):
    # Only use this when original_df is wide
    return Scatter(
        results.original_df,
        results.series_ids,
        "Correlation Scatter Chart"
    )
    
class TimeSeries:
    def __init__(self,df,x,y,title):
        self.df=df
        self.x=x
        self.y=y
        self.title=title

    def plot(self):
        plt.figure(figsize=(12,6))
        plt.plot(self.df[self.x], self.df[self.y])
        plt.title(self.title)
        plt.xlabel(self.x)
        plt.ylabel(self.y)
        path=f'{CHARTS_DIR}/{self.title}{datetime.now().strftime("%Y%m%d%H%M%S")}.png'
        plt.savefig(path)
        plt.close()
        return path

class Bar:
    def __init__(self,x,y,title):
        self.x=x
        self.y=y
        self.title=title

    def plot(self):
        x_values = self.x.astype(str).tolist()
        y_values = self.y.tolist()
    
        table_source = ColumnDataSource(data=dict(
            x=x_values,
            y=y_values))

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
            color="#87a6d4")

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
        output_file(f'{CHARTS_DIR}/{self.title}{datetime.now().strftime("%Y%m%d%H%M%S")}.html')
        save(full_rating_layout)
        return full_rating_layout

    def basic_plot(self):
        plt.figure(figsize=(14,8))
        sns.set_style("whitegrid")
        sns.barplot(
            # data=df,
            x=self.x,
            y=self.y,
            order=self.x,
            color="#EAADD4"
        ).set(title=self.title)
        plt.xticks(rotation=45)
        sns.despine()
        path = f'{CHARTS_DIR}/{self.title}{datetime.now().strftime("%Y%m%d%H%M%S")}.png'
        plt.savefig(path, bbox_inches='tight', dpi=300)
        plt.close()
        return path

class Scatter:
    def __init__(self,table,series,title):
        self.table=table
        self.series=series
        self.title=title

    def plot(self):
        x_label=self.series[0]
        y_label=self.series[1]
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
                (x_label, "@x{0.00}"),
                (y_label, "@y{0.00}")
            ])
        )

        full_layout = column(table_fig,background="white",sizing_mode="scale_width")
        output_file(f'{CHARTS_DIR}/{self.title}{datetime.now().strftime("%Y%m%d%H%M%S")}.html')
        save(full_layout)
        return full_layout

    def basic_plot(self):
        plt.figure(figsize=(14,8))
        sns.set_style("white")
        sns.regplot(x=self.x, y=self.y)
        sns.despine(offset=10, trim=True)
        plt.title(self.title)
        path = f'{CHARTS_DIR}/{self.title}{datetime.now().strftime("%Y%m%d%H%M%S")}.png'
        plt.savefig(path, bbox_inches='tight', dpi=300)
        plt.close()
        return path