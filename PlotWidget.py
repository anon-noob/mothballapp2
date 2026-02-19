from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.ticker import MultipleLocator
from matplotlib.figure import Figure
from matplotlib.lines import Line2D

class PlotWidget(FigureCanvasQTAgg):
    "Widget for displaying a plot"
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(3.6, 3.6), facecolor="#393939", layout="constrained") # in inches
        self.ax = self.fig.add_subplot(111)

        super().__init__(self.fig)
        self.setParent(parent)
        self.setSizePolicy(self.sizePolicy().Expanding,self.sizePolicy().Expanding)
        self.updateGeometry()

        self.mainline: list[Line2D] = []
        self.data: list[Line2D] = []

        self.ax.set_facecolor("#5B5B5B")
        self.ax.tick_params(colors="white")
        self.ax.xaxis.label.set_color("white")
        self.ax.yaxis.label.set_color("white")
        self.ax.xaxis.set_major_locator(MultipleLocator(0.5))
        self.ax.xaxis.set_minor_locator(MultipleLocator(0.125))
        self.ax.yaxis.set_major_locator(MultipleLocator(0.5))
        self.ax.yaxis.set_minor_locator(MultipleLocator(0.125))
        self.ax.grid(which="both", linestyle="--", linewidth=0.5, color='white')

    def addMainLine(self, x, y):
        # print(self.mainline)
        if self.mainline:
            self.mainline[0].remove()
        self.mainline = self.ax.plot(x,y, marker="o", linestyle="-", color="lime")
        # print(self.mainline)
        self.ax.relim()
        self.ax.autoscale_view()
        
        self.draw()

    def addData(self, id, x,y, color = "lime"):
        "Set the x and y coordinates. Color can be given in hex"

        assert len(x) == len(y), "lists x and y are not the same length"
        
        if id < len(self.data):
            self.clearData(id)
            self.data[id], = self.ax.plot(x, y, marker="o", linestyle="-", color=color)
        else:
            a, = self.ax.plot(x, y, marker="o", linestyle="-", color=color)
            self.data.append(a)

        self.ax.relim()
        self.ax.autoscale_view()
        
        self.draw()
    
    def clearData(self, id, redraw=False):
        if id >= len(self.data):
            return
        if self.data[id].axes:
            self.data[id].remove()
        if redraw:
            self.draw()


    def clearDataAndReindex(self, id):
        if id < len(self.data):
            self.data[id].remove()
            del self.data[id]
        
            self.draw()

    def clearAllData(self):
        for art in list(self.ax.lines):
            art.remove()
