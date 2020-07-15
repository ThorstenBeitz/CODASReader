# CODASReader
Python library to read CODAS files and convert them to ASCII or use directly in Python.  
For information on the CODAS file format visit https://www.dataq.com/resources/techinfo/ff.htm  
or view the document in this folder.  

To install: pip install .  
To upgrade: pip install --upgrade .  

A CODAS file can be read by initializing a new CODASReader object, giving the file location / name as an argument.  
The header of the file will then be read automatically (this is the default, can be changed if so desired) and stored in the object.  
The header must always be read first before reading other parts of the file or accessing information from it.  
The CODASReader class includes separate functions to read the file's ADC data section and the trailer.  
When reading the ADC data, the channels that should be read, as well as the time frame can be passed on as optional arguments.  
The readADC function also includes a saveMemory mode which is turned on by default.  
This reads and stores the data as a 16 bit integer and saves the scaling factor for each channel separately.  
It is completely lossless and it is neccessary for reading large files at once if system RAM is limited.  
If storing the data as float directly is neccessary, save_memory can be set to False.  

After reading the different sections of the CODAS file, information from the header can be printed or returned using the respective functions.  
Information that can be otained this way include:  
&emsp;&emsp;Number of acquired channels  
&emsp;&emsp;Start time and date of data acquesition  
&emsp;&emsp;End time and date of data acquesition  
&emsp;&emsp;Duration of data acquesition  
&emsp;&emsp;Channel information from the header  
&emsp;&emsp;Sample rate  

The class also supports printing the header and the trailer of the file to the console.  
The ADC data can be saved as a csv file with a custom header to the sepcified file location using saveADCToCSV().  

The class is entirely compatible with packed and HiRes files as described by CODAS file format document.  

The CODASReader.py file can also be run from the comman line using command line arguments.  
The file header and file trailer are read automatically from the specified file location.  
The command line arguments allow limited access to the api including:  
&emsp;&emsp;Print header  
&emsp;&emsp;Print trailer  
&emsp;&emsp;Print start time of acquesition  
&emsp;&emsp;Print duration of acquesition  
&emsp;&emsp;Print number pf acquired channels  
&emsp;&emsp;Print sampling rate  
  
Additionally the ADC data can be read and save to a csv file.  
Using additional arguments, the channels that should be read, the time frame, the name of the csv file and a custom header for the file can be specified.  

###########################################################################  

CSV File format description:  
&emsp;&emsp;First line:     custom header  
&emsp;&emsp;Second line:    channel number of data in column below (channel 1 = 0, ...)  
&emsp;&emsp;Third line:     scaling factor for data in column below  
  
&emsp;&emsp;All subsequent lines are the adc data section and the corresponding time stamps:  
&emsp;&emsp;&emsp;&emsp;First column:       running timer since first data point in csv file (not since acquesition) in seconds  
&emsp;&emsp;&emsp;&emsp;Following columns:  data from each channel recorded, data corresponds to channel number in line 2 in the  
&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;                   same column and should be multiplied by scaling factor in line 3  
&emsp;&emsp;&emsp;&emsp;penultimate column: date of recording of data points on this line (format: mm-dd-yyyy)  
&emsp;&emsp;&emsp;&emsp;last column:        Time of recording of data points on this line, accurate to 1 second (UTC or Arizona time)  
    
############################################################################  

CODASReader class methods:  

__init__  
&emsp;&emsp;initialize a new reader  
&emsp;&emsp;PARAMETERS:  
&emsp;&emsp;&emsp;&emsp;location: str, file name / location  
&emsp;&emsp;&emsp;&emsp;readHeader: bool, optional, determines whether header should be read automatically, default: true  
&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;since the header must be read first, this should be left true.  

readHeader  
&emsp;&emsp;reads the file header  
&emsp;&emsp;ALWAYS call this before using further class methods,  
&emsp;&emsp;does not need to be called if readHeader = true when initializing reader (Default)  

readADC  
&emsp;&emsp;reads the ADC data section of the file.  
&emsp;&emsp;call this before saveADCsToCSV.  
&emsp;&emsp;Do not call this if you are simply inquiring information from the file header since reading  
&emsp;&emsp;the ADC data typically takes some time and is not neccessary to use any of the methods  
&emsp;&emsp;specified under additional methods for accessing header information.  
&emsp;&emsp;PARAMETERS:  
&emsp;&emsp;&emsp;&emsp;channels : int or array-like of int, optional  
&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;Must be able to be converted into a numpy array.  
&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;A list of all channels from which data should be read.  
&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;The first channel has index 0.  
&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;Default is reading all acquired channels.  
&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;Use 'printAcqChannels' to see number the number of  
&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;acquired channels.  
&emsp;&emsp;&emsp;&emsp;start_time : float, optional  
&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;Time in seconds since start of data acquesition at which  
&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;the first ADC data should be read.  
&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;Default is 0  
&emsp;&emsp;&emsp;&emsp;end_time : float, optional  
&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;Time in seconds since start of data acquesition at which  
&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;the last ADC data should be read.  
&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;Default is until end of ADC data section in file.  
&emsp;&emsp;&emsp;&emsp;save_memory : bool, optional  
&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;Decides whether the scaling factor is applied to the data    
&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;or if the scaling factor is saved in a separate array  
&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;before it is saved to the array   
&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;If true, the data will be saved as int16, which is the  
&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;way it is natively stored in the file  
&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;(no loss of information)  
&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;If false, the data is stored as float.    
&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;Default is True   
&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;It is recommended to use save_memory = True for large files  
&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;and / or for systems with limited ram.   
&emsp;&emsp;&emsp;&emsp;az_time: bool, optional    
&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;Decides whether the time stamps are in UTC or in   
&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;Arizona local time (VERITAS telescope location)   
&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;Default is False (UTC time)   
    
readTrailer  
&emsp;&emsp;reads the file trailer-  
&emsp;&emsp;call this before printTrailer  
  
printHeader  
&emsp;&emsp;prints the file header with the name of each element where available and respecitve values  
&emsp;&emsp;for more information on what each header element means, read the CODAS file dormat document  
  
saveADCsToCSV  
&emsp;&emsp;saves the ADC data to a CSV file of given name.  
&emsp;&emsp;the layout of the produced CSV file can be seen above.  
&emsp;&emsp;PARAMETERS:  
&emsp;&emsp;&emsp;&emsp;name : str  
&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;Name of the CSV file the ouput will be saved to  
&emsp;&emsp;&emsp;&emsp;delim : str, optional  
&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;delimeter between elements for the CSV file.  
&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;Default: ","  
&emsp;&emsp;&emsp;&emsp;header : list, optional  
&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;custom header for the CSV file that will be written in the first line  

printTrailer  
&emsp;&emsp;prints the file trailer  
  
printChannelInfo  
&emsp;&emsp;prints the channel information that is stored in the file header for all specified channels  
&emsp;&emsp;PARAMETERS:  
&emsp;&emsp;&emsp;&emsp;number: int or list of int, optional  
&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;Channel number(s) of channels that should be printed.  
&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;Default is all channels.  
      
      
--Additional methods for accessing header information--  
&emsp;&emsp;All following methods print or return different information stored in the file header.  

printHeaderLength  
&emsp;&emsp;prints header length in bytes  

printADCDataLength  
&emsp;&emsp;prints ADC data section length in bytes  

printAcqTime  
&emsp;&emsp;prints start time and date of data acquesition  
&emsp;&emsp;PARAMETERS:   
&emsp;&emsp;&emsp;&emsp;az_time: bool, optional   
&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;Determines whether time is Arizona local time or UTC (default: Arizona time)   

printFinishTime  
&emsp;&emsp;prints end time and date of data acquesition  
&emsp;&emsp;PARAMETERS:   
&emsp;&emsp;&emsp;&emsp;az_time: bool, optional   
&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;Determines whether time is Arizona local time or UTC (default: Arizona time)   

printMeasurementTimeFrame  
&emsp;&emsp;prints length of data acquesition in seconds  
  
printAcqChannels  
&emsp;&emsp;prints number of acquired channels  

printTimeBetweenSamples  
&emsp;&emsp;prints time between samples  
  
printSampleRate  
&emsp;&emsp;prints the total sample rate from all channels combined in samples / s  
  

getHeaderLength  
&emsp;&emsp;return header length in bytes  

getADCDataLength  
&emsp;&emsp;return ADC data section length in bytes  

getAcqTime  
&emsp;&emsp;return start time and date of data acquesition  
&emsp;&emsp;PARAMETERS:   
&emsp;&emsp;&emsp;&emsp;az_time: bool, optional   
&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;Determines whether time is Arizona local time or UTC (default: Arizona time)   

getFinishTime  
&emsp;&emsp;return end time and date of data acquesition  
&emsp;&emsp;PARAMETERS:   
&emsp;&emsp;&emsp;&emsp;az_time: bool, optional   
&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;Determines whether time is Arizona local time or UTC (default: Arizona time)   

getMeasurementTimeFrame  
&emsp;&emsp;return length of data acquesition in seconds  
  
getAcqChannels  
&emsp;&emsp;return number of acquired channels  

getTimeBetweenSamples  
&emsp;&emsp;return time between samples  
  
getSampleRate  
&emsp;&emsp;return the total sample rate from all channels combined in samples / s  
  
