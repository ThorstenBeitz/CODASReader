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
It is completely lossless and it is neccessary for reading large files at once.

After reading the different sections of the CODAS file, information from the header can be printed or returned using the respective functions.
Information that can be otained this way include:
  Number of acquired channels
  Start time and date of data acquesition
  End time and date of data acquesition
  Duration of data acquesition
  Channel information from the header
  Sample rate

The class also supports printing the header and the trailer of the file to the console.
The ADC data can be saved as a csv file with a custom header to the sepcified file location using saveADCToCSV().

The class is entirely compatible with packed and HiRes files as described by CODAS file format document.

The CODASReader.py file can also be run from the comman line using command line arguments.
The file header and file trailer are read automatically from the specified file location.
The command line arguments allow limited access to the api including:
  Print header
  Print trailer
  Print start time of acquesition
  Print duration of acquesition
  Print number pf acquired channels
  Print sampling rate
  
Additionally the ADC data can be read and save to a csv file.
Using additional arguments, the channels that should be read, the time frame, the name of the csv file and a custom header for the file can be specified.

###########################################################################

CSV File format description:
  First line:     custom header
  Second line:    channel number of data in column below (channel 1 = 0, ...)
  Third line:     scaling factor for data in column below
  
  All subsequent lines are the adc data section and the corresponding time stamps:
    First column:       running timer since first data point in csv file (not since acquesition) in seconds
    Following columns:  data from each channel recorded, data corresponds to channel number in line 2 in the
                        same column and should be multiplied by scaling factor in line 3
    penultimate column: date of recording of data points on this line
    last column:        UTC time of recording of data points on this line, accurate to 1 second
    
############################################################################

CODASReader class methods:

__init__
  initialize a new reader
   PARAMETERS:
    location: str, file name / location
    readHeader: bool, optional, determines whether header should be read automatically, default: true
                since the header must be read first, this should be left true.

readHeader
  reads the file header
  ALWAYS call this before using further class methods,

readADC
  reads the ADC data section of the file
  PARAMETERS:
        channels : int or array-like of int, optional
            Must be able to be converted into a numpy array.
            A list of all channels from which data should be read.
            The first channel has index 0.
            Default is reading all acquired channels.
            Use 'printAcqChannels' to see number the number of
            acquired channels.
        start_time : float, optional
            Time in seconds since start of data acquesition at which
            the first ADC data should be read.
            Default is 0
        end_time : float, optional
            Time in seconds since start of data acquesition at which
            the last ADC data should be read.
            Default is until end of ADC data section in file.
        save_memory : bool, optional
            Decides whether the scaling factor is applied to the data
            before it is saved to the array
            or if the scaling factor is saved in a separate array.
            Default is True.
            It is recommended to use save_memory = True for large files
            and / or for systems with limited ram.
    
readTrailer
  reads the file trailer
  
printHeader
  prints the file header with the name of each element where available and respecitve values
  for more information on what each header element means, read the CODAS file dormat document
  
saveADCsToCSV
  saves the ADC data to a CSV file of given name
  the layout of the produced CSV file can be seen above
  PARAMETERS:
    name : str
      Name of the CSV file the ouput will be saved to
    delim : str, optional
      delimeter between elements for the CSV file.
      Default: ","
    header : list, optional
      custom header for the CSV file that will be written in the first line

printTrailer
  prints the file trailer
  
printChannelInfo
  prints the channel information that is stored in the file header for all specified channels
  PARAMETERS:
    number: int or list of int, optional
      Channel number(s) of channels that should be printed.
      Default is all channels.
      
--Additional methods for accessing header information--
  All following methods print or return different information stored in the file header.

printHeaderLength
  prints header length in bytes

printADCDataLength
  prints ADC data section length in bytes

printAcqTime
  prints start time and date of data acquesition

printFinishTime
  prints end time and date of data acquesition

printMeasurementTimeFrame
  prints length of data acquesition in seconds
  
printAcqChannels
  prints number of acquired channels

printTimeBetweenSamples
  prints time between samples
  
printSampleRate
  prints the total sample rate from all channels combined in samples / s
  

getHeaderLength
  return header length in bytes

getADCDataLength
  return ADC data section length in bytes

getAcqTime
  return start time and date of data acquesition

getFinishTime
  return end time and date of data acquesition

getMeasurementTimeFrame
  return length of data acquesition in seconds
  
getAcqChannels
  return number of acquired channels

getTimeBetweenSamples
  return time between samples
  
getSampleRate
  return the total sample rate from all channels combined in samples / s
  
