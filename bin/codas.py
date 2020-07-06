#! /usr/bin/env python3 

# only runs if program is run directly from file
if __name__ == "__main__":
    from CODASReader import CODASReader
    import sys
    import traceback
    import argparse
    desc = """Read CODAS files and translate them to ASCII. The result
    will be separated into the file header, the adc data and the file
    trailer. The header and trailer can be printed to the console and
    the adc data can be saved as a csv file."""
    # setting up argparse with all needed arguments
    parser = argparse.ArgumentParser(
        description=desc,
        formatter_class=argparse.MetavarTypeHelpFormatter)
    parser.add_argument("file", type=str)
    parser.add_argument("-H", "--header", action="store_true",
                        help="Print header of CODAS file")
    parser.add_argument("-t", "--trailer", action="store_true",
                        help="Print trailer of CODAS file")
    parser.add_argument("-p", "--printStartTime", action="store_true",
                        help="Print start time of data acquesition")
    parser.add_argument("-d", "--duration", action="store_true",
                        help="Print duration of data acquesition in seconds")
    parser.add_argument("-r", "--rate", action="store_true",
                        help="Print sample rate")
    parser.add_argument("-a", "--acqChannels", action="store_true",
                        help="Print number of acquired channels")
    parser.add_argument("-s", "--saveADC", action="store_true",
                        help="Save ADC data to csv, required for arguments below")
    parser.add_argument("-c", "--channel", type=int, action="append",
                        help="Add a channel to be read (default: all)")
    parser.add_argument("-b", "--beginTime", type=float,
                        help="""Time in seconds since start of data
                        acquesition at which the first ADC data should
                        be read. (default: 0)""")
    parser.add_argument("-e", "--endTime", type=float,
                        help="""Time in seconds since start of data
                        acquesition at which the last ADC data should
                        be read. (default: until last entry)""")
    parser.add_argument("-n", "--name", type=str,
                        help="""Name for the produced ADC data csv file
                        (default: 'name of file'.csv)""")
    parser.add_argument("-f", "--fileHeader", type=str, action="append",
                        help="""Add an element to the header of the csv file
                        (default: Samples per second = 'sample rate')""")
    input_args = parser.parse_args()

    # setting file location to entered file location and reading
    # header and trailer first (header read automatically)
    location = input_args.file
    try:
        codas_reader = CODASReader(location)
        codas_reader.readTrailer()
        channels = None
        header = header = ["Samples per second = "
                           + str(codas_reader.getSampleRate())]
    except Exception:
        traceback.print_exc()
        sys.exit(1)
    start_time = 0
    end_time = None
    name = location + ".csv"
    # checking all possible command line arguments
    if input_args.header:
        codas_reader.printHeader()
    if input_args.trailer:
        codas_reader.printTrailer()
    if input_args.printStartTime:
        codas_reader.printAcqTime()
    if input_args.duration:
        codas_reader.printMeasurementTimeFrame()
    if input_args.rate:
        codas_reader.printSampleRate()
    if input_args.acqChannels:
        codas_reader.printAcqChannels()
    if input_args.saveADC:
        if input_args.channel:
            channels = input_args.channel
        if input_args.beginTime:
            start_time = input_args.beginTime
        if input_args.endTime:
            end_time = input_args.endTime
        if input_args.name:
            name = input_args.name
        if input_args.fileHeader:
            header = input_args.fileHeader
        try:
            # read and print ADC data with appropriate options
            codas_reader.readADC(channels=channels, start_time=start_time,
                                end_time=end_time)
            codas_reader.saveADCsToCSV(name=name, header=header)
        except Exception:
            traceback.print_exc()
            sys.exit(1)
    sys.exit()
