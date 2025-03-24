"""
PlotManager – Generates the Plotly graph

"""

import cea.inputlocator
import os
import cea.config
import time
import geopandas as gpd
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from math import ceil


__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2025, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"



class bar_plot:
    """Generates a Plotly bar plot from processed data."""

    def __init__(self, config_config, dataframe, list_y_columns):

        # Get the dataframe prepared by the data processor, including Y(s), X, and X_facet
        self.df = dataframe

        # Get the settings for the format
        self.plot_title = config_config.plot_title
        self.y_metric_to_plot = config_config.y_metric_to_plot
        self.y_columns = list_y_columns
        self.y_metric_unit = config_config.y_metric_unit
        self.y_normalised_by = config_config.y_normalised_by
        self.y_min = config_config.y_min
        self.y_max = config_config.y_max
        self.y_step = config_config.y_step
        self.y_barmode = config_config.y_barmode
        self.y_label = config_config.y_label
        self.x_to_plot = config_config.x_to_plot
        self.facet_by_numbers_wrapped = config_config.facet_by_numbers_wrapped
        self.facet_by_rows = config_config.facet_by_rows
        self.x_sorted_by = config_config.x_sorted_by
        self.x_sorted_reversed = config_config.x_sorted_reversed
        self.x_label = config_config.x_label

        # Update y_columns based on if normalisation is selected
        if self.y_normalised_by == 'no_normalisation':
            self.y_columns_normalised = list_y_columns
        else:
            self.y_columns_normalised = [item + "/m2" for item in self.y_columns]

    def generate_fig(self):
        """Creates a Plotly figure."""

        # Process the data if 100% stacked bar chart is selected
        if self.y_barmode == 'stack_percentage':
            df = convert_to_percent_stacked(self.df, self.y_columns)
        else:
            df = self.df

        # Create bar chart
        fig = plot_faceted_bars(df, x_col='X', facet_col='X_facet', value_columns=self.y_columns_normalised, y_metric_to_plot=self.y_metric_to_plot, bool_use_rows=self.facet_by_rows, number_of_rows_or_columns=self.facet_by_numbers_wrapped)

        # Position legend below
        fig = position_legend_below(fig, df['X'].unique(), row_height=10)

        return fig

    def fig_format(self, fig):
        # Set the title
        if self.plot_title:
            title = self.plot_title
        else:
            title = "Building Energy Demand"

        # Set the y-axis label
        if self.y_label:
            y_label = self.y_label
        elif self.y_barmode == 'stack_percentage':
            y_label = "Percentage (%)"
        else:
            if self.y_metric_unit == 'MWh' and self.y_normalised_by == 'no_normalisation':
                y_label = "Energy Demand (MWh/yr)"
            elif self.y_metric_unit == 'MWh' and self.y_normalised_by != 'no_normalisation':
                y_label = "Energy Use Intensity (MWh/yr/m2)"
            elif self.y_metric_unit == 'kWh' and self.y_normalised_by == 'no_normalisation':
                y_label = "Energy Demand (kWh/yr)"
            elif self.y_metric_unit == 'kWh' and self.y_normalised_by != 'no_normalisation':
                y_label = "Energy Use Intensity (kWh/yr/m2)"
            elif self.y_metric_unit == 'Wh' and self.y_normalised_by == 'no_normalisation':
                y_label = "Energy Demand (Wh/yr)"
            elif self.y_metric_unit == 'Wh' and self.y_normalised_by != 'no_normalisation':
                y_label = "Energy Use Intensity (Wh/yr/m2)"
            else:
                raise ValueError(f"Invalid y-metric-unit: {self.y_metric_unit}")

        # Set the x-axis label
        if self.x_label:
            x_label = self.x_label
        else:
            if self.x_to_plot == 'building':
                x_label = "Buildings"
            elif self.x_to_plot == 'building_faceted_by_months':
                x_label = "Buildings"
            elif self.x_to_plot == 'building_faceted_by_seasons':
                x_label = "Buildings"
            elif self.x_to_plot == 'building_faceted_by_construction_type':
                x_label = "Buildings"
            elif self.x_to_plot == 'building_faceted_by_main_use_type':
                x_label = "Buildings"
            elif self.x_to_plot == 'district_and_hourly':
                x_label = "Hours"
            elif self.x_to_plot == 'district_and_hourly_faceted_by_months':
                x_label = "Hours"
            elif self.x_to_plot == 'district_and_hourly_faceted_by_seasons':
                x_label = "Hours"
            elif self.x_to_plot == 'district_and_daily':
                x_label = "Days"
            elif self.x_to_plot == 'district_and_daily_faceted_by_months':
                x_label = "Days"
            elif self.x_to_plot == 'district_and_daily_faceted_by_seasons':
                x_label = "Days"
            elif self.x_to_plot == 'district_and_monthly':
                x_label = "Months"
            elif self.x_to_plot == 'district_and_monthly_faceted_by_seasons':
                x_label = "Months"
            elif self.x_to_plot == 'district_and_seasonally':
                x_label = "Seasons"
            elif self.x_to_plot == 'district_and_annually_or_selected_period':
                x_label = "Selected period"
            else:
                raise ValueError(f"Invalid x-to-plot: {self.x_to_plot}")

        if self.y_barmode == 'stack_percentage':
            barmode = 'stack'
        else:
            barmode = self.y_barmode

        # About title and bar mode
        title = title + ' - ' + y_label + ' by ' + x_label
        fig.update_layout(
            title=dict(
                text=f"<b>{title}</b>",  # Bold using HTML
                x=0,
                y=1,
                xanchor='left',
                yanchor='top',
                font=dict(size=20)  # Optional: adjust size, color, etc.
            ),
            barmode=barmode
        )

        # About adding margin
        # fig.update_layout(
        #     margin=dict(l=100, r=40, t=60, b=100)  # Adjust as needed
        # )

        # About X, Y labels
        # Add X-axis label (below all subplots)
        # fig.add_annotation(
        #     text=x_label,
        #     xref="paper", yref="paper",
        #     x=0.5, y=-0.025,  # y=0 instead of -0.12 — still below the plots but visible
        #     showarrow=False,
        #     font=dict(size=16),
        #     xanchor='center',
        #     yanchor='top'
        # )

        # Add Y-axis label (rotated, to the left of all subplots)
        # fig.add_annotation(
        #     text=y_label,
        #     xref="paper", yref="paper",
        #     x=-0.02, y=0.5,  # x=0 instead of -0.1
        #     showarrow=False,
        #     textangle=-90,
        #     font=dict(size=16),
        #     xanchor='right',
        #     yanchor='middle'
        # )

        return fig


def position_legend_below(fig, x_labels, row_height=10):
    """
    Dynamically position legend under the x-axis based on number of x-ticks.

    Parameters:
    - fig: plotly.graph_objects.Figure
    - x_labels: list of strings used for x-axis
    - row_height: estimated pixel height per row of labels (optional)
    """
    # Estimate how much space is needed below
    max_label_length = max(len(str(x)) for x in x_labels)

    # Heuristic: adjust margin bottom and y position based on size
    margin_bottom = min(150, 50 + int((max_label_length / 10) * row_height))
    legend_y = -0.1  # fixed so it always goes below, you can tweak this

    fig.update_layout(
        legend=dict(
            orientation='h',
            yanchor="bottom",
            y=legend_y,
            xanchor="left",
            x=0
        ),
        margin=dict(b=margin_bottom)
    )

    return fig


def convert_to_percent_stacked(df, list_y_columns):
    """
    Converts selected columns of a DataFrame to row-wise percentages for 100% stacked bar chart.

    Parameters:
        df (pd.DataFrame): Input DataFrame with numeric values.
        list_y_columns (list of str): Columns to convert to percentage (must exist in df).

    Returns:
        pd.DataFrame: DataFrame with same columns where list_y_columns are converted to percentages.
    """
    df_percent = df.copy()
    row_sums = df_percent[list_y_columns].sum(axis=1)
    df_percent[list_y_columns] = df_percent[list_y_columns].div(row_sums, axis=0) * 100
    return df_percent


def plot_faceted_bars(
    df,
    x_col,
    facet_col,
    value_columns,
    y_metric_to_plot,
    bool_use_rows=False,
    number_of_rows_or_columns=None
):
    facets = sorted(df[facet_col].unique())
    num_facets = len(facets)

    # Fallback if not provided
    if number_of_rows_or_columns is None:
        number_of_rows_or_columns = 2 if num_facets > 1 else 1

    if bool_use_rows:
        rows = number_of_rows_or_columns
        cols = ceil(num_facets / rows)
    else:
        cols = number_of_rows_or_columns
        rows = ceil(num_facets / cols)

    fig = make_subplots(
        rows=rows,
        cols=cols,
        subplot_titles=[str(f) for f in facets],
        shared_yaxes=True,
        horizontal_spacing=0.01,
        vertical_spacing=0.075
    )

    for i, facet in enumerate(facets):
        row = (i // cols) + 1
        col = (i % cols) + 1
        facet_df = df[df[facet_col] == facet]

        for j, val_col in enumerate(value_columns):
            heading = y_metric_to_plot[j] if isinstance(y_metric_to_plot, list) else val_col

            fig.add_trace(
                go.Bar(
                    x=facet_df[x_col],
                    y=facet_df[val_col],
                    name=heading,
                    offsetgroup=j,
                    legendgroup=heading,
                    showlegend=(i == 0)  # Show legend only once
                ),
                row=row,
                col=col
            )

    # Find the global min/max across all value columns
    ymin = df[value_columns].min().min()
    ymax = df[value_columns].max().max()*1.05

    fig.update_yaxes(range=[ymin, ymax])

    return fig


# Main function
def generate_fig(config_config, df_to_plotly, list_y_columns):

     if config_config.plot_type == "bar_plot":
        # Instantiate the bar_plot class
        plot_instance_c = bar_plot(config_config, df_to_plotly, list_y_columns)

        # Generate the Plotly figure
        fig = plot_instance_c.generate_fig()

        # Format the Plotly figure
        fig = plot_instance_c.fig_format(fig)

        return fig

     else:
        raise ValueError(f"Invalid plot type: {config_config.plot_type}")




