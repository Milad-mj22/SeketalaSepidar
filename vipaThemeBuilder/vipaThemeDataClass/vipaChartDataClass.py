from dataclasses import dataclass, field
from typing import List, Optional

#----------------------------------------------------------------------------------------
#                                            Bar Chart
#----------------------------------------------------------------------------------------
@dataclass
class barChartSeries:
    name:str
    data:list[int|float]

@dataclass
class barChartDataClass:
    title:str
    chart_id:str
    categories:list[str]
    series:list[barChartSeries]
    description:str=''
    axis_y_max:int = 200
    chart_height:str = "200px"
    has_filter:bool = False
    chart_data_id:str|None = None
    colors:list[str]|tuple[str] = ("#009ef7", '#f5f8fa', '#50cd89', '#ffbf00')


#----------------------------------------------------------------------------------------
#                                            Line Chart
#----------------------------------------------------------------------------------------



@dataclass
class lineChartSeries:
    name: str
    data: List[int | float]
    color: str = "#1b84ff"  

@dataclass
class lineChartDataClass:
    title: str = "نمودار"
    chart_id: str = "line_chart"
    chart_data_id: Optional[str] = None
    categories: List[str] = field(default_factory=list)
    series: List[lineChartSeries] = field(default_factory=list)
    height: int = 300
    stroke_curve: str = "smooth"  # smooth, straight, stepline
    show_legend: bool = True
    show_grid: bool = True
    xaxis_title: str = ""
    yaxis_title: str = ""
    gradient_colors: List[str] = field(default_factory=lambda: ["#1b84ff", "#17c653"])