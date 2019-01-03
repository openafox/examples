import numpy as np
import scipy as sp
import matplotlib.pyplot as plt
from matplotlib.patches import Arc

class AnnoteFinder(object):
    """callback for matplotlib to display an annotation when points are
    clicked on.  The point which is closest to the click and within
    xtol and ytol is identified.
    Modified from: https://scipy-cookbook.readthedocs.io/items/Matplotlib_Interactive_Plotting.html
    
    Register this function like this:
    
    fig, ax = plt.subplots()
    ax.scatter(x, y)
    af =  AnnoteFinder(x, y, ax=ax)
    fig.canvas.mpl_connect('button_press_event', af)

    Attributes:
        data (list): (x,y,anotation) data.
        links (list): ToDo.
        points (list): selected points.
        clicks (list): clicked points.
        drawnAnnotations(list): points that have been drawn and annotated.
    """

    def __init__(self, xdata, ydata, annotes=None, ax=None, xtol=None, ytol=None):
        """ 
        Args:
        xdata (list): ploted x data.
        ydata (list): ploted y data.
        annotes (:obj:'list', optional): list same length as xdata and y data of anotation text.
        ax (:obj:'mplax', optional): matplot lib axis to plot on.
        xtol (:obj:`int`, optional): tolerance for finding x from click.
        ytol (:obj:`int`, optional): tolerance for finding y from click.
        """
        # Value checking, create self.data:
        if len(ydata) != len(xdata):
                raise ValueError('xdata and ydata must be same lenght')
        if annotes:
            if len(annotes) != len(xdata):
                raise ValueError('annotes must be same lenght as xdata and ydata')
            self.data = list(zip(xdata, ydata, annotes))
        else:
            annotes = [''] * len(xdata)
            self.data = list(zip(xdata, ydata, annotes))
            
        # x tolerance
        if xtol is None:
            xtol = ((max(xdata) - min(xdata))/float(len(xdata)))/2
        # y tolerance
        if ytol is None:
            ytol = ((max(ydata) - min(ydata))/float(len(ydata)))/2
        self.xtol = xtol
        self.ytol = ytol
        # axis to plot on
        if ax is None:
            self.ax = plt.gca()
        else:
            self.ax = ax
        # init some things
        self.drawnAnnotations = {}
        self.links = []
        self.points = []
        self.clicks = []

    def distance(self, x1, x2, y1, y2):
        """
        return the distance between two points.
        unused!!
        """
        return(np.sqrt((x1 - x2)**2 + (y1 - y2)**2))

    def __call__(self, event):

        if event.inaxes:

            clickX = event.xdata
            clickY = event.ydata
            # self.clicks.append([clickX, clickY])
            if (self.ax is None) or (self.ax is event.inaxes):
                annotes = []
                # print(event.xdata, event.ydata)
                for ii, (x, y, a) in enumerate(self.data):
                    if ((clickX-self.xtol < x < clickX+self.xtol) and
                            (clickY-self.ytol < y < clickY+self.ytol)):
                        annotes.append((ii, x, y, a))
                if annotes:
                    #annotes.sort()
                    #ind, x, y, annote = annotes[0]
                    for ann in annotes:
                        ind, x, y, annote = ann
                        self.drawAnnote(event.inaxes, ind, x, y, annote)
                        for l in self.links:
                            l.drawSpecificAnnote(annote)

    def drawAnnote(self, ax, ind, x, y, annote):
        """
        Draw the annotation on the plot
        """
        # remove if already there
        if ind in self.drawnAnnotations:
            markers = self.drawnAnnotations[ind]
            #for m in markers:
                #m.set_visible(not m.get_visible())
            if markers[0]:
                markers[0].remove()  # text
            markers[1].remove()  # markers
            ax.figure.canvas.draw_idle()
            # delete from drawnAnnotations and points
            del self.drawnAnnotations[ind]
            self.points.remove([ind, x, y])
        else:
            if annote:
                t = ax.text(x, y, " - %s" % (annote),)
            else:
                t = None
            m = ax.scatter([x], [y], marker='d', c='r', zorder=100)
            self.points.append([ind, x, y])
            self.drawnAnnotations[ind] = (t, m)
            ax.figure.canvas.draw_idle()

    def drawSpecificAnnote(self, annote):
        annotesToDraw = [(x, y, a) for x, y, a in self.data if a == annote]
        for x, y, a in annotesToDraw:
            self.drawAnnote(self.ax, x, y, a)

def plot_scatter(xdata, ydata, xlabel, ylabel, ax):
    """plots and fits with a 1d line
    returns: ax"""

    # Axis Lables
    ax.set_xlabel(xlabel, fontsize=16)
    ax.set_ylabel(ylabel, fontsize=16)

    # make the scatter plot
    ax.plot(xdata, ydata, linestyle='', marker='o')
    
    return ax
    
class FitLinear(object):
    """Fit line to x, y data and plot on matplotlib ax.
    
    Register this function like this:
    
    fig, ax = plt.subplots()
    ax.scatter(x, y)
    fit = FitLinear(x, y, ax=ax)

    Attributes:
        self.x
        self.y
        self.slope
        self.intercept
        self.rsqd
        self.fit
    """

    def __init__(self, xdata, ydata, ax=None):
        """ 
        Args:
        xdata (list): ploted x data.
        ydata (list): ploted y data.
        ax (:obj:'mplax', optional): matplot lib axis to plot on.
        fit (:obj:'mplax', optional): List pf mlp objects (line, yerrUpper, yerrLower, text).
        """
        # Value checking, create self.data:
        if len(ydata) != len(xdata):
                raise ValueError('xdata and ydata must be same lenght')
        self.x = xdata
        self.y = ydata
        # axis to plot on
        if ax is None:
            self.ax = plt.gca()
        else:
            self.ax = ax
        # get fit data
        self.slope, self.intercept, self.rsqd = self.get_fit(self.x, self.y)
        # plot it
        self.fit = self._plot_fit()
    
    def update_fit(self, xnew, ynew):
        """Updates plot with new data"""
        self.x = xnew
        self.y = ynew
        # get fit data
        self.slope, self.intercept, self.rsqd = self.get_fit(self.x, self.y)
        # get data for ploting
        xl, yl, xs, yerrLower, yerrUpper, eq_txt = self._get_fit_data()
        
        # Update data
        self.fit[3].set_text(eq_txt)
        # line
        self.fit[0].set_xdata(xl)
        self.fit[0].set_ydata(yl)
        # l_yerr
        self.fit[1].set_xdata(xs)
        self.fit[1].set_ydata(yerrLower)
        # u_yerr
        self.fit[2].set_xdata(xs)  
        self.fit[2].set_ydata(yerrUpper)
        
        # redraw
        self.ax.figure.canvas.draw_idle()
        #ax.relim()
        #ax.autoscale_view()
        
    def get_fit(self, xdata, ydata):
        """determine best fit line and fit parameters"""
        # get Fit!!!
        par = np.polyfit(xdata, ydata, 1, full=True)
        # get line eq
        slope = par[0][0]
        intercept = par[0][1]
        # coefficient of determination
        variance = np.var(ydata)
        residuals = np.var([(slope*xx + intercept - yy)  for xx, yy in zip(xdata, ydata)])
        rsqd = np.round(1-residuals/variance, decimals=2)
        return (slope, intercept, rsqd)
        
    def _get_fit_data(self):
        """gets extra data for plotting (line, l_yerr, u_yerr, txt)"""
        # get line
        xl = [min(self.x), max(self.x)]
        yl = [self.slope*xx + self.intercept  for xx in xl]
        # get error bounds
        yerr = [abs(self.slope*xx + self.intercept - yy)  for xx,yy in zip(self.x, self.y)]
        par = np.polyfit(self.x, yerr, 2, full=True)
        # sort the data (makes plot clean)
        reorder = sorted(range(len(self.x)), key = lambda ii: self.x[ii])
        xs = [self.x[ii] for ii in reorder]
        ys = [self.x[ii] for ii in reorder]
        # error lines
        yerrUpper = [(xx*self.slope+self.intercept)+(par[0][0]*xx**2 + par[0][1]*xx + par[0][2]) for xx, yy in zip(xs, ys)]
        yerrLower = [(xx*self.slope+self.intercept)-(par[0][0]*xx**2 + par[0][1]*xx + par[0][2]) for xx, yy in zip(xs, ys)]
        # text to add to plot
        eq_txt = 'y=%0.2f$x + %0.2f$ \n$R^2 = %0.2f$' % (self.slope, self.intercept, self.rsqd)

        return (xl, yl, xs, yerrLower, yerrUpper, eq_txt)
    
    def _plot_fit(self):
        # get data for plotting:
        xl, yl, xs, yerrLower, yerrUpper, eq_txt = self._get_fit_data()
        # plot All
        txt = self.ax.text(min(self.x),.9*max(self.y) ,eq_txt, fontsize=24)
        line, = self.ax.plot(xl, yl, '-r')
        l_yerr, = self.ax.plot(xs, yerrLower, '--r')
        u_yerr, = self.ax.plot(xs, yerrUpper, '--r')
        # save plot objects
        fit = [line, l_yerr, u_yerr, txt]
        return fit
    
def arc_pt_pos(cx, cy, px, py, th):
    """calculate the position (x,y) of a point th (deg) away from (px, py) on a circle with center (cx, cy)
        returns: (x,y)"""
    x = cx+(px-cx)*np.cos(th)+(cy-py)*np.sin(th)
    y = cy+(py-cy)*np.cos(th)+(cx-px)*np.sin(th)
    return x, y
    
def plot_wafer(mplax, size=[100, 100], center=[0,0], flatlocal=0):
    """Plot 100mm wafer
        mplax - matplotlib subplot"""

    #mplax.plot([x2,x2],[y1, y2], color="w")
    #mplax.plot([x1, x2],[y2, y2], color="w")
    
    # for flat calc
    cx = center[0]
    cy = center[1]
    x1 = cx-size[0]/2
    x2 = cx+size[0]/2
    y1 = cy-size[1]/2
    y2 = cy+size[1]/2
    px = x2
    py = 0
    
    # 270 is down 180 is left
    flat2 = 107 - flatlocal - 90
    flat1 = 107 + flatlocal - 90
    
    fx1, fy1 = arc_pt_pos(cx, cy, px, py, np.deg2rad(flat2))
    fx2, fy2 = arc_pt_pos(cx, cy, px, py, np.deg2rad(flat2 -34))
    mplax.plot([fx1, fx2],[fy1,fy2], color="black")
    wafer = Arc((0,0), height=y2-y1, width=x2-x1, angle=0,
            theta1=flat1, theta2=flat1-34, color="black", lw=1.5)

    mplax.add_patch(wafer)
    mplax.axis('off')
    return mplax

def plot_wafermap(mplax, x, y, z, size=[100000, 100000], center=[0,0], resolution=100, flatlocal=0, vmin= None, vmax=None, bins=20):
    """Plot Wafer Map"""

    cx = center[0]
    cy = center[1]
    x1 = cx-size[0]/2
    x2 = cx+size[0]/2
    y1 = cy-size[1]/2
    y2 = cy+size[1]/2
    
    if not vmin:
        vmin = np.min(z)
    if not vmax:
        vmax = np.max(z)
        
    # create coordinate arrays to vectorize function evaluations over a grid    
    xi, yi = np.mgrid[x1:x2:resolution, y1:y2:resolution]
    # interpolate z to grid
    zi = sp.interpolate.griddata((x, y), z, (xi, yi), method='cubic')
    # Plot
    plot_wafer(mplax, size, flatlocal=flatlocal)
    levels = np.linspace(vmin, vmax, bins)
    g = mplax.contourf(xi, yi, zi, levels, cmap='viridis', extend='both')
    plt.colorbar(g, ax=mplax, ticks=[vmin, vmax])
