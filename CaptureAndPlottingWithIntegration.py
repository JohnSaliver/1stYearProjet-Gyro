# Import libraries 
from numpy import * 
from pyqtgraph.Qt import QtGui, QtCore 
import pyqtgraph as pg 
import serial 
import keyboard
from CSVFunc import capture_to_csv, csv_reader
import time
from rnn import sample, hidden_size

class buffer:
    def __init__(self,n):
        self.L = [(0,0) for i in range(n)]
    def push(self, cc):
        self.L[:-1]=self.L[1:]
        self.L[-1] = cc
    def val(self, k):
        return self.L[k]
    def disp(self):
        for k in self.L:
            print(k)        
    def ls(self):
        return self.L


# Create object serial port 

portName = "COM5"
baudrate = 250000 
try: 
    ser = serial.Serial(portName,baudrate) 
except: 
    print("Serial port not found, only replay will work.")

# START QtApp ##### 
app = QtGui.QApplication([])   # you MUST do this once (initialize things) 
#

win = pg.GraphicsWindow(title="Signal from serial port") # creates a window 
px = win.addPlot(title="Gyro my dude")# creates empty space for the plot in the window  
maxY = 10000
px.setYRange(-maxY,maxY)
h_ = zeros((hidden_size,1))

windowWidth = 500      # width of the window displaying the curvex 
Xm = linspace(0,0,windowWidth)
Ym = linspace(0,0,windowWidth)
Zm = linspace(0,0,windowWidth)
Em = linspace(0,0,windowWidth)
Ixm = linspace(0,0,windowWidth)
Iym = linspace(0,0,windowWidth)
Izm = linspace(0,0,windowWidth)   # create array that will contain the relevant time series  

#create the dictionaries containing the repective time series 
axes = 'Y' #char of the curves to be plotted
R_ = {'x': (Xm, 'r'), 'y': (Ym, 'b'), 'z': (Zm, 'g') , 'e' : (Em, 'w'), 'X': (Ixm, 'r'), 'Y': (Iym, 'b'), 'Z': (Izm, 'g')}
R, curvsax, Color = {}, {}, {}
Id = {'x' : 0, 'y' : 1, 'z': 2} 

for i in axes: #only setup the curves that are chosen
    if i.isupper(): #this case if necessary as integration requires to keep track of the normal values as well
        R[i] = R_[i][0]
        R[i.lower()] = R_[i.lower()][0]
        Color[i] = R_[i][1]
        Color[i.lower()] = R_[i.lower()][1]
    else: 
        R[i] = R_[i][0]
        Color[i] = R_[i][1]
    curvsax[i] = px.plot()
    

ptr = windowWidth     # set first x position 

def average(L,nb_pts, pos): #the element L[pos] will be the average of the surronding nb_pts elements
    avg = 0
    for i in range(nb_pts):
        try :
            avg += L[pos + i]
            avg += L[pos - i]
        except: 
            raise('out of list indexes for avergae thingy') #debugging, should never happen
    return avg/(nb_pts*2+1)

def readport(): #read the serial port and return the decoded measures
        ser.flushInput() #empty the serial buffer
        ser_bytes = ser.readline() #read until \n
        #print(ser.inWaiting())
        decoded_bytes = ser_bytes[0:len(ser_bytes)-2].decode("utf-8") #decode

        return decoded_bytes

# Realtime data plot. Each time this function is called, the data display is updated 
def update_capture(t_now, t_last, avg = 0, save = False, disp = True, predict = False):
    global curvsax, ptr, R, Color, h_ #the programs works with global variables, gotta declare them
    decoded_bytes = readport()  # read line from the serial port
    deltaT = t_now - t_last # time since the last value, only for the integration
    if disp and len(decoded_bytes.split()) == 3: #only display if display is enabled and if no values were lost (for consistency)
            for i in axes: # go through the string to display the axes
                R[i][:-1] = R[i][1:] # shift data in the temporal mean 1 sample left 
                if i == 'e' and not(predict): #if we are predicting in real time, non need to display the index e
                    if keyboard.is_pressed(' '):
                        R[i][-1] = maxY/2
                    else:
                        R[i][-1] = 0
                    curvsax[i].setData(R[i])
                    
               
                elif i =='e' and predict and len(decoded_bytes.split()) == 3: #so that we can predict in real time
                        pred, h_ = sample(h_, [float(p) for p in decoded_bytes.split()], squished = 0) #call the sample method from rnn.py
                        print(pred)
                        R[i][-1] = pred*maxY/2
                        curvsax[i].setData(R[i])
                elif i.isupper(): #if the current plot is one of integration, we calculate the actual integration
                    print(i)

                    R[i.lower()][-1] = float(decoded_bytes.split()[Id[i.lower()]])
                    R[i][-1] = R[i][-2] + 0.5*(R[i.lower()][-2]+R[i.lower()][-1])*deltaT
                    if R[i][-1]>15000:
                        R[i][-1] = 0
                    print(R[i][-1])
                    curvsax[i].setData(R[i]) 
                else:
                    R[i][-1] = float(decoded_bytes.split()[Id[i]])
                    if avg != 0:
                        R[i][len(R[i])-avg -1] = average(R[i], avg, len(R[i])-avg -1)
                        curvsax[i].setData(R[i][:len(R[i])-avg])
                        # update x position for displaying the curvex     
                    else: 
                        curvsax[i].setData(R[i]) 
                
                ptr += 1
                curvsax[i].setPos(ptr,0)     # set x position in the graph to 0 
                QtGui.QApplication.processEvents() # you MUST process the plot now 
                #print(R[i][len(R[i])-2 -1])
        
    if save and len(decoded_bytes.split()) == 3: #Save Rx Ry Rz regardless of the display
            if keyboard.is_pressed(' '):
                eps = 1
            else:
                eps = 0
            capture_to_csv(t_now, decoded_bytes, eps) #Last argument is the label, epsilon
    
        
def update_replay(dataslice): # new function for replaying data, simpler because less cases to process
    global curvsax, ptr, R, Color
    
    for i in range(len(R)): # we can still choose which of the axes to display, however integration on replay isnt supported
            R[i][:-1] = R[i][1:] # shift data in the temporal mean 1 sample left 
            if not(NoE) and i == len(R)-1:
                if keyboard.is_pressed(' '):
                    R[i][-1] = maxY/2
                else:
                    R[i][-1] = 0
            else: 
                R[i][-1] = float(dataslice[i]) # vector containing the instantaneous values
            ptr += 1
            curvsax[i].setData(R[i])      # set the curvex with this data 
        
            curvsax[i].setPos(ptr,0)     # set x position in the graph to 0 
            QtGui.QApplication.processEvents() # you MUST process the plot now 
            #print(R[i][len(R[i])-2 -1])
    
def Conf(): # waits for the calibration to finish
    decoded_bytes = readport()
    while decoded_bytes != "done!":
        print("Conf: ",decoded_bytes)
        decoded_bytes = readport()

def main_loop(replay = 0, replay_speed = 1, capture_ix = 0,config = 1, save = 0, predict = 0):
    global h_
    running = 1
    
    #Code for replaying capture from 'file' pointed by 'capture_ix'
    if replay == 1: #replay loop, allows for different replay speeds 
        q = 0
        print("Replaying capture, ")
        file = str(input("dataset to replay?"))
        try :
            capt = csv_reader(file)[capture_ix]
            print(capt)
        except:
            raise TypeError("Capture index out of range or no such file.")
        t_st = round(time.time(), 4)
        print(t_st)
        print("Replaying at " + str(round(replay_speed*100)) + '%' )
        for datasliceWT_ix in range(len(capt)-1):
            print(str(datasliceWT_ix) + "/" + str(len(capt)))
            dataslice = capt[datasliceWT_ix][1:]
            deltaT = (capt[datasliceWT_ix+1][0] - capt[datasliceWT_ix][0])/replay_speed
            t_before = round(time.time(),4)
            update_replay(dataslice)
            deltaTact = round(time.time(),4) - t_before
            if deltaTact<deltaT:
                #print("deltaT " + str(deltaT) + "  DeltaTact " + str(deltaTact) + "\ndelay " + str(replay_speed*(deltaT-deltaTact)))
                time.sleep((deltaT-deltaTact)/replay_speed)
            else:
                print("Display cannot keep up, replay speed not guaranteed.")
            if keyboard.is_pressed('q'):
                        print("Paused replay, press r to resume.")
                        running = 0
                        q = 1
            while q == 1:
                if keyboard.is_pressed('r'):
                    q = 0
                    print('Resumed.')
        print('Data sequence replayed')
        a = input("Replay next sequence in the same file? (y or n)")

        if a == 'y':
            main_loop(1, replay_speed, capture_ix+1)
        elif a=='n':
            pg.QtGui.QApplication.exec_()
            return 0
        else:
            pg.QtGui.QApplication.exec_()
            raise TypeError('Incorrect type, please enter y or n')
        pg.QtGui.QApplication.exec_()
        return 0

    else: # capture, not replay
        print("Starting new capture.")
        Conf() #we have to call conf every time because the arduino resets everytime the serial is turned on hence restarting the calibration 
        if save: capture_to_csv(0,"S",0)
        t_st = round(time.time(), 4) # define time of start of capture
        t = t_st
        
        while True:
            #try :
            if not(keyboard.is_pressed("q")):
                q = 0
            
            if keyboard.is_pressed('r'): #unpause
                print("Restarted capture.")
                if save: capture_to_csv(0, "S", 0)
                h_ = zeros((hidden_size,1))
                running = 1
                t_st = round(time.time(), 4)
            #except:
            #    pass
            if keyboard.is_pressed('q') and q == 0: #stops everything properly if q is pressed once paused
                print("Exiting.")
                ser.close()
                break
            while running == 1: 
                 #try: 
                    if keyboard.is_pressed('q'): # pause
                        print("Stopped Capture.")
                        running = 0
                        q = 1
                        break
                    t_last = t
                    t = round(time.time(),4) - t_st
                    update_capture(t, t_last,save = save, disp = 1, predict = predict)
                 #except:
                    #pass
            




main_loop(replay = 0, save = 0, predict = False) #actual thing to call for everything to run

#qqprint(csv_reader("data.csv"))
### END QtApp #### 
pg.QtGui.QApplication.exec_() # you MUST put this at the end 
