# iPyParallel - Intro to Parallel Programming
from ipyparallel import Client
import ipyparallel
import time
import numpy as np
from matplotlib import pyplot as plt
# Problem 1
def initialize(blocking=True, closing=True):
    """
    Write a function that initializes a Client object, creates a Direct
    View with all available engines, and imports scipy.sparse as sparse on
    all engines. Return the DirectView.
    """
    client = Client()               #initialize a Client object
    dview = client[:]               #create a direct view with all available engines           
    dview.execute("import scipy.sparse as sparse")          #import scipy.sparse as sparse on all engines
    dview.block = blocking                                  #establish whether to use blocking or not
    if closing:
        client.close()
        return dview                                        #keep the client object open if we are going to reference it in future problems
    else:
        return dview, client
 
# Problem 2
def variables(dx):
    """
    Write a function variables(dx) that accepts a dictionary of variables. Create
    a Client object and a DirectView and distribute the variables. Pull the variables back and
    make sure they haven't changed. Remember to include blocking.
    """

    dview, client = initialize(blocking=True, closing=False)                #include blocking
    dview.push(dx)                      #store the variables
    for var in dx.keys():
        assert dx[var] == dview.pull(var)[0]                #access each variable and confirm that the values have not changed
    client.close()

# Problem 3
def prob3(n=1000000):
    """
    Write a function that accepts an integer n.
    Instruct each engine to make n draws from the standard normal
    distribution, then hand back the mean, minimum, and maximum draws
    to the client. Return the results in three lists.
    
    Parameters:
        n (int): number of draws to make
        
    Returns:
        means (list of float): the mean draws of each engine
        mins (list of float): the minimum draws of each engine
        maxs (list of float): the maximum draws of each engine.
    """
    dview, client = initialize(blocking=True, closing=False)
    dview.execute("import numpy as np")
    dview.execute("x = np.random.rand("+str(n)+")")                 #make each engine take n draws from the standard normal
    means = dview.pull("x.mean()")
    mins = dview.pull("x.min()")
    maxs = dview.pull("x.max()")                                    #calculate the means, mins, and maxs of each engine's draws
    client.close()
    return means, mins, maxs


# Problem 4
def prob4():
    """
    Time the process from the previous problem in parallel and serially for
    n = 1000000, 5000000, 10000000, and 15000000. To time in parallel, use
    your function from problem 3 . To time the process serially, run the drawing
    function in a for loop N times, where N is the number of engines on your machine.
    Plot the execution times against n.
    """
    ns = [1000000, 5000000, 10000000, 15000000]
    time1 = []
    time2 = []
    N = len(initialize().targets)                           #get the number of engines
    for n in ns:
        start = time.time()                                 #time the process using parallel computing
        prob3(n)
        time1.append(time.time()-start)

        start = time.time()
        for i in range(N):                                  #time the process using serial computing
            x = np.random.rand(n)
            a = x.mean()
            b = x.min()
            c = x.max()
        time2.append(time.time()-start)

    plt.plot(ns, time1, label='Parallel')                   #plot the computation times against the draw size
    plt.plot(ns, time2, label='Serial')
    plt.xlabel('n')
    plt.ylabel('time(seconds)')
    plt.legend()
    plt.show()

# Problem 5
def parallel_trapezoidal_rule(f, a, b, n=200):
    """
    Write a function that accepts a function handle, f, bounds of integration,
    a and b, and a number of points to use, n. Split the interval of
    integration among all available processors and use the trapezoidal
    rule to numerically evaluate the integral over the interval [a,b].

    Parameters:
        f (function handle): the function to evaluate
        a (float): the lower bound of integration
        b (float): the upper bound of integration
        n (int): the number of points to use; defaults to 200
    Returns:
        value (float): the approximate integral calculated by the
            trapezoidal rule
    """
    dview, client = initialize(blocking=True, closing=False)
    h = (b-a)/n                                 #calculate the step size
    points = np.linspace(a,b,n)                 #create our points
    dview.scatter('nums', points)               #partition the points among the engines
    dview['func'] = f                   
    dview['h'] = h                              #push our function as well as step size
    dview.execute("c = .5*h*(2*np.sum(func(nums[1:-1])) + func(nums[0]) + func(nums[-1]))")         #execute the trapezoid rule in each engine on its respective points
    total_ars = dview['c']
    client.close()
    return np.sum(total_ars)                        #sum the results of each engine to get the total area

def test5():
    f = lambda x: x**2
    a = 0
    b = 1
    print(parallel_trapezoidal_rule(f, a, b, n=1000))