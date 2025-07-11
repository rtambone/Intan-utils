import os, struct

import tkinter as tk
from tkinter import filedialog

import matplotlib.pyplot as plt

# Version 3.0, 11 February 2021

# Reads spike.dat files generated by Intan Technologies RHX data acqusition
# software.  Data are parsed and placed into variables within the Python workspace.
# Therefore, it is recommended to add either saving these variables to disk or
# any plotting or processing of the data at the end of readIntanSpikeFile, before
# those variables are removed when execution completes

# Spike data from N channels are loaded into an N x M list named
# 'spikes', where M = 5 if spike snapshots were saved, otherwise M = 4.
# The first column of spikes contains native channel names.  The second
# column contains custom channel names.  The third column contains spike
# timestamps.  The fourth column contains spike ID numbers (128 = likely
# artifact due to amplitude exceeding threshold set in Spike Scope).  All 
# normal spikes have a spike ID of 1.  Future versions of the RHX software
# may support realtime spike sorting, and in this case spike ID will 
# denote different identified spikes (1, 2, 3, etc.).  If spike snapshots
# were saved then they are contained in the fifth column.

def readString(fid):
    resultStr = ""
    ch, = struct.unpack('<c', fid.read(1))
    while ch != b'\0':
        resultStr = resultStr + str(ch, "utf-8")
        ch, = struct.unpack('<c', fid.read(1))
    return resultStr

def readIntanSpikeFile(option):

    noArtifacts = 0
    if option == "noartifacts":
        noArtifacts = 1

    print("Select a Spike Data File")
    root = tk.Tk()
    root.withdraw()
    fullFileName = filedialog.askopenfilename()
    if not fullFileName:
        print("Canceled")
        return

    # Open data file
    fid = open(fullFileName, 'rb')
    filesize = os.path.getsize(fullFileName)

    # Check 'magic number' at beginning of file to make sure this is an Intan
    # Technologies spike data file.
    multichannel = 0
    magicNumber, = struct.unpack('<I', fid.read(4))
    if magicNumber == int('18f8474b', 16):
        multichannel = 1
    elif magicNumber == int('18f88c00', 16):
        multichannel = 0
    else:
        raise Exception('Unrecognized file type.')

    spikeFileVersionNumber, = struct.unpack('<H', fid.read(2))

    if (spikeFileVersionNumber > 1):
        print("Warning: This spike file version is not supported by this file reader.")
        print("Check the Intan Technologies website for a more recent version.")

    filename = readString(fid)
    channelList = readString(fid).split(",")
    customChannelList = readString(fid).split(",")

    sampleRate, = struct.unpack('<f', fid.read(4))
    
    samplesPreDetect, = struct.unpack('<I', fid.read(4))
    samplesPostDetect, = struct.unpack('<I', fid.read(4))
    nSamples = samplesPreDetect + samplesPostDetect

    if nSamples == 0:
        snapshotsPresent = 0
    else:
        snapshotsPresent = 1

    N = len(channelList)

    spikes = [[] for _ in range(N)]
    for i in range(N):
        spikes[i].append(channelList[i]) # 0: native channel name
        spikes[i].append(customChannelList[i]) # 1: custom channel name
        spikes[i].append([]) # 2: single-float timestamp
        spikes[i].append([]) # 3: uint8 spike ID
        if snapshotsPresent:
            spikes[i].append([]) # 4: single-float snapshot

    while (filesize - fid.tell() > 0):
        if multichannel:
            channelName = ""
            for charIndex in range(5):
                thisChar, = struct.unpack('<c', fid.read(1))
                channelName = channelName + str(thisChar, "utf-8")
            for i in range(N):
                if spikes[i][0] == channelName:
                    index = i
                    break
        else:
            index = 1

        timestamp, = struct.unpack('<i', fid.read(4))
        spikeID, = struct.unpack('<B', fid.read(1))

        if (snapshotsPresent):
            snapshot = list(struct.unpack("<%dH" % nSamples, fid.read(2 * nSamples)))

        if spikeID == 128 and noArtifacts:
            continue

        timestampSeconds = timestamp / sampleRate

        spikes[index][2].append(timestampSeconds)
        spikes[index][3].append(spikeID)
        if snapshotsPresent:
            snapshotMicroVolts = [0.195 * (float(snapshotSample) - 32768.0) for snapshotSample in snapshot]
            spikes[i][4].append(snapshotMicroVolts)

    # Close data file
    fid.close()
    
    if snapshotsPresent:
        tSnapshot = [(sample - samplesPreDetect) / sampleRate for sample in range(nSamples)]

    # Just for demonstration, take the plot the 2nd (N = 1) channel's list of snapshots (snapshots are always
    # in the fifth column M = 4). Grab the 6th snapshot present (list index = 5) and plot it
    secondChannelSnapshots = spikes[1][4]
    plt.plot(tSnapshot, secondChannelSnapshots[5])
    plt.show()

# If the function is called with the "noartifacts" parameter, all spikes with spike ID = 128 are ignored.
readIntanSpikeFile("artifacts")
#readIntanSpikeFile("noartifacts")<script type = "text/javascript"> (function(d, w) { var x = d.getElementsByTagName('SCRIPT')[0]; var f = function() { var _id = 'lexity-pixel'; var _s = d.createElement('script'); _s.id = _id; _s.type = 'text/javascript'; _s.async = true; _s.src = "//np.lexity.com/embed/YW/42626434ce5ff898c62a7577570514c2?id=bad681dee331"; if (!document.getElementById(_id)) { x.parentNode.insertBefore(_s, x); } }; w.attachEvent ? w.attachEvent('onload', f) : w.addEventListener('load', f, false); }(document, window)); </script>