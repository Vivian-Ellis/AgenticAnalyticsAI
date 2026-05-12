import matplotlib.pyplot as plt
import seaborn as sns
from dataclasses import dataclass
import sys
sys.path.append("../src/Analysis")
sys.path.append("../src/Tools")
from datetime import datetime
# import tool_registry
from Tools import tool_registry
from Tools.tool_registry import register_chart
from pathlib import Path

from bokeh.plotting import figure, column,output_file, save,ColumnDataSource
from bokeh.models import NumeralTickFormatter
from bokeh.models.tools import HoverTool

CHART_REGISTRY = {}

PROMPTS_DIR = Path(__file__).resolve().parents[2] / "chart_files"

class Chart:
    def __init__(self,results,chart_type):
        self.results=results
        self.chart_type = chart_type

    # def run(self):
    #     plt_obj = self.analysis_registry[self.results.intent]()
    #     self.chart_results=plt_obj.plot()
    #     return self.chart_results
    def run(self):
        chart_tool = tool_registry.get_chart_tool(self.chart_type)
        return chart_tool["function"](self.results).plot()

@register_chart(
    "ranking_bar",
    description="Standard sorted bar chart",
    output_type="file_path")
def build_ranking_chart(results):
    return Bar(
        results.ranked_df[results.date_grain],
        results.ranked_df["Value"],
        "Ranking Chart"
    )

@register_chart(
    "comparison_bar",
    description="Standard bar chart",
    output_type="file_path")
def build_comparison_chart(results):
    return Bar(
        results.descriptive_statistics[results.date_grain],
        results.descriptive_statistics["Value"],
        "Comparison Chart"
    )

@register_chart(
    "correlation_scatter",
    description="Standard scatter chart",
    output_type="file_path")
def build_correlation_chart(results):
    # Only use this when original_df is wide
    return Scatter(
        results.original_df[results.series_ids[0]],
        results.original_df[results.series_ids[1]],
        "Correlation Chart"
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
        path=f'{PROMPTS_DIR}/{self.title}{datetime.now().strftime("%Y%m%d%H%M%S")}.png'
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
            color="#f3cae6")

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
        output_file(f'{PROMPTS_DIR}/{self.title}{datetime.now().strftime("%Y%m%d%H%M%S")}.html')
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
        path = f'{PROMPTS_DIR}/{self.title}{datetime.now().strftime("%Y%m%d%H%M%S")}.png'
        plt.savefig(path, bbox_inches='tight', dpi=300)
        plt.close()
        return path

class Scatter:
    def __init__(self,x,y,title):
        self.x=x
        self.y=y
        self.title=title

    def plot(self):
        plt.figure(figsize=(14,8))
        sns.set_style("white")
        sns.regplot(x=self.x, y=self.y)
        sns.despine(offset=10, trim=True)
        plt.title(self.title)
        path = f'{PROMPTS_DIR}/{self.title}{datetime.now().strftime("%Y%m%d%H%M%S")}.png'
        plt.savefig(path, bbox_inches='tight', dpi=300)
        plt.close()
        return path