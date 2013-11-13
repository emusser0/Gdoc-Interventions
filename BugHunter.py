import gDocsImport as gd
import sys, os

from multiprocessing import Process, Queue, cpu_count

from math import ceil
try:
    from collections import OrderedDict
    print "\n*** Python 2.7+, loading OrderedDict from Collections ***"
except:
    from OrderedDict import OrderedDict
    print "\n*** OrderedDict not found in collections, using drop in version ***"
    
paramsLine = "Output Folder,Subpopulation Directory"
toFromLine = "To Subpopulation,From Subpopulation"
EFO6Line = "EFO6 Files To Analyze"

def fixLengths(matrix):
    None

def printList(list):
    text = ""
    for item in list:
        text += '\t' + str(item) + '\n'
    return text

def prepDir(directory):
    while '//' in directory:
        directory = directory.replace('//','/')
    if directory[-1] != '/':
        directory += '/'
    return directory
      
def filterIDs(directory, count):
    try:
        popfile = open(directory)
    except:
        print "Error: population file not found at", directory
        return 'error'
    ids = set()              
    line = 0
    while True:
            testline = popfile.readline()
            if len(testline) == 0:
                break
            if not testline.startswith("#"):
                ids.add(int(testline))
                line += 1
                
    idstemp =  sorted(list(ids))      
    print '\tSubpop', count, str(line), "entries with IDS", int(idstemp[0]), "through", int(idstemp[line-1]), "loaded"
    return ids

def findIgnores(trimmed, subpopLoaded, out_q, core, iterations, disjoint):
    length = length0 =  len(trimmed)
    days = comments = filtered = pos = 0
    notifyEvery = 50000
    print "Core", core, "preparing to filter population, size:", length0
    outdict = {}
    content = {}
    
    for pos in range(length):
        adjusted = pos + disjoint
        if '#' in trimmed[pos]:
		print "Ignoring comment:", trimmed[pos]
		disjoint -= 1
		comments += 1
        else:
	   temp = trimmed[pos][0]
	   if temp not in subpopLoaded:
	           disjoint -=1
	   else:
    	       content[adjusted] = map(int,trimmed[pos])	      
    	
    	pos += 1
        if (pos+filtered)%notifyEvery == 0:
            print "Core", core, "filtering", pos+filtered, "out of", length0, "entries"
    
    print "Core", core, "filtering complete, beginning sort by day"
    for key, entry in content.iteritems():
        days =  max(days, entry[2])
        
    iterXDay = [[0 for pos1 in range(days+1)] for pos2 in range(iterations)]
    for key, entry in content.iteritems():
	iterXDay[entry[1]][entry[2]] += 1
    
    print "Core", core, "task complete"
    
    filtered = length - comments - len(outdict)
    outdict['comments'+str(core)] = comments
    outdict['filtered'+str(core)] = filtered
    outdict['byDay' + str(core)] = iterXDay
    outdict['days' + str(core)] = days
    out_q.put(outdict)

def getCrossTalk(trimmed, crossTalkSubs, iterations, disjoint, out_q, core):
    toSubpop = crossTalkSubs['toPop']
    toType = crossTalkSubs['toType']
    toName = crossTalkSubs['toName']
    fromSubpop =  crossTalkSubs['fromPop']
    fromType =  crossTalkSubs['fromType']
    fromName = crossTalkSubs['fromName']

    length = length0 =  len(trimmed)
    days = comments = filtered = pos = 0
    notifyEvery = 50000
    print "Core", core, "preparing to filter population, size:", length0
    outdict = {}
    content = {}
    
    for pos in range(length):
        adjusted = pos + disjoint
        if '#' in trimmed[pos]:
		print "Ignoring comment:", trimmed[pos]
		disjoint -= 1
		comments += 1
        else:
	   toID = trimmed[pos][0]
	   fromID = trimmed[pos][3]
	   if (((toID in toSubpop) or toName == 'ANY') != toType) or (((fromID in fromSubpop) or fromName == 'ANY') != fromType):
	       disjoint -=1
	   else:
    	       content[adjusted] = trimmed[pos]	      
    	
    	pos += 1
        if (pos+filtered)%notifyEvery == 0:
            print "Core", core, "filtering", pos+filtered, "out of", length0, "entries"
    
    print "Core", core, "filtering complete, beginning sort by day"
    for key, entry in content.iteritems():
        days =  max(days, entry[2])
        
    iterXDay = [[0 for pos1 in range(days+1)] for pos2 in range(iterations)]
    for key, entry in content.iteritems():
	iterXDay[entry[1]][entry[2]] += 1
    
    print "Core", core, "task complete"
    
    filtered = length - comments - len(outdict)
    outdict['byDay' + str(core)] = iterXDay
    outdict['days' + str(core)] = days
    out_q.put(outdict)
    
    
    
def loadCrossTalk(crossTalkEFO6, crossTalkSubs):
    EFO6 = crossTalkEFO6['EFO6']
    iterations = crossTalkEFO6['iterations']
    toSubpop = crossTalkSubs['toPop']
    toType = crossTalkSubs['toType']
    fromSubpop =  crossTalkSubs['fromPop']
    fromType =  crossTalkSubs['fromType']
    length0 =  len(EFO6)

    #trimmed = content[popSize+2:]
    #length0 = len(trimmed)
    #days =comments = filtered = pos = 0
    lengths = []
    #isEmpty = False
    
    print "\nChecking for non epidemic iterations.."
        
    cores = cpu_count()
    out_q = Queue()
    block =  int(ceil(length0/float(cores)))
    processes = []
    
    for i in range(cores):
        p = Process(target = findIgnores, args = (EFO6[block*i:block*(i+1)], toSubpop, out_q, i, iterations, block*i))
        processes.append(p)
        p.start() 
    merged = {}
    for i in range(cores):
        merged.update(out_q.get())
    for p in processes:
        p.join()
    
    for i in range(cores):
        lengths.append(merged["days" + str(i)])
        
    for i in range(iterations):
        for k in range(cores):
            print "LENGTH", i, len(merged['byDay'+ str(1)][i])
        
    days = max(lengths)
   
    print "Subproccesses complete, merging results" 
    iterXDay = [[0 for pos1 in range(days+1)] for pos2 in range(iterations)]
    for i in range(days):
        for j in range(iterations):
            summed = 0
            for k in range(cores):
                if i <= lengths[k]:
                    summed += merged['byDay' + str(k)][j][i]
            iterXDay[j][i] += summed
            
    print "Results merge complete, beginning checking for iteration epidemic status"
    
    attackRates = []
    ignore = [False]*iterations
    empty = [False]*(iterations+1)
    ignored = 0
    for pos in range(iterations):
        attackRates.append(sum(iterXDay[pos]))
    meanAttack = sum(attackRates)/iterations
    print "Attack Rates:", attackRates
    print "Mean:", meanAttack
    
    epiAttack = 0
    for pos in range(iterations):
        if attackRates[pos] < meanAttack/10 or attackRates[pos] == 0:
            ignore[pos] =  True
            ignored += 1
            print "Iteration",pos,"did not reach epidemic status"
	if attackRates[pos] == 0:
	   print "Iteration",pos,"no infections found"
	   empty[pos] = True
        else:
            epiAttack += attackRates[pos]
    print "Ignored:", ignored
    if ignored != iterations:
        epiMean = epiAttack/(iterations-ignored)
    else:
        epiMean = 0
    epiPercent = ((iterations-ignored)/iterations)*100
    print "Percent Reaching Epidemic:", epiPercent
    print "Mean epdidemic attack rate:", epiMean
    
    meanCurve = []
    for pos1 in range(days):
        temp = 0
        for pos2 in range(iterations):
            if not ignore[pos2]:
                temp += iterXDay[pos2][pos1]   
        if iterations != ignored:
            meanCurve.append(int((float(temp)/(iterations-ignored))+.5))
    
    if sum(meanCurve) == 0:
        empty[iterations] = True    
    
    print "\nChecking for crosstalk"
        
    cores = cpu_count()
    out_q = Queue()
    block =  int(ceil(length0/float(cores)))
    processes = []
    
    for i in range(cores):
        #p = Process(target = getCrossTalk, args = (EFO6[block*i:block*(i+1)], toSubpop, out_q, i, iterations, block*i))
        p = Process(target = getCrossTalk, args = (EFO6[block*i:block*(i+1)], crossTalkSubs, iterations, block*i, out_q, i))
        processes.append(p)
        p.start() 
    merged2 = {}
    for i in range(cores):
        merged2.update(out_q.get())
    for p in processes:
        p.join()
        
    for i in range(cores):
        lengths.append(merged2["days" + str(i)])
        
    for i in range(iterations):
        for k in range(cores):
            print "LENGTH", i, len(merged2['byDay'+ str(1)][i])
       
    print "Subproccesses complete, merging results" 
    crossTalk = [[0 for pos1 in range(days+1)] for pos2 in range(iterations)]
    for i in range(days):
        for j in range(iterations):
            summed = 0
            for k in range(cores):
                if i <= lengths[k]:
                    #print k, i, j
                    try:
                        summed += merged2['byDay' + str(k)][j][i]
                    except:
                        print "Errrm....."
            crossTalk[j][i] += summed
            
    print "Results merge complete, beginning analysis"
    
    ctRates = []
    for pos in range(iterations):
        ctRates.append(sum(crossTalk[pos]))
    meanCT = sum(ctRates)/iterations
    print "Cross Talk Rates:", ctRates
    print "Mean:", meanCT
    
    isEpidemic = [0]*iterations
    for i in range(iterations):
        isEpidemic[i] = not(ignore[i])
        
    ctMean = []
    for pos1 in range(days):
        temp = 0
        for pos2 in range(iterations):
            if not ignore[pos2]:
                temp += crossTalk[pos2][pos1]   
        if iterations != ignored:
            ctMean.append(int((float(temp)/(iterations-ignored))+.5))
    
    if sum(meanCurve) == 0:
        empty[iterations] = True    
    
    return {'epiCurves':iterXDay,'crossTalkCurves':crossTalk,'meanCurve':meanCurve,"meanCrossTalkCurve":ctMean, "isEpidemic":isEpidemic, 'length':days}

def loadEFO6(fileName, out_q, count):
    outDict = {}
    print "\tReading file", count, ":", fileName
    wholeThing = open(fileName)
    content = wholeThing.readlines()
    params = content[0].split(' ')    
    popSize = int(params[1])
    iterations = int(params[3])
    trimmed = content[popSize+3:]
    for pos in range(len(trimmed)):
        trimmed[pos] =  map(int,trimmed[pos].split(' '))
    length0 = len(trimmed)
    print "\tFile", count, ":"
    print "\t\tPopsize:", popSize
    print "\t\tIterations:", iterations
    print "\t\tLines:", length0
    outDict[fileName] = trimmed
    outDict[fileName + "_size"] = popSize
    outDict[fileName + "_iterations"] = iterations   
    out_q.put(outDict)
    
def getEFO6s(directories):
    EFO6Files = {}
    dirList = []
    out_q = Queue()
    processes = []
    for experiment in directories:
        fileName = experiment[1]
        if fileName.startswith("qsub "):
            fileName = fileName.replace("qsub ","")
        if fileName.endswith("qsub"):
            fileName = fileName.replace("qsub","EFO6")
        try:
            open(fileName)
        except:
            print "Error: EFO6 file", fileName, "not found"
            quit()
        if fileName not in dirList:
            dirList.append(fileName)
        
    
    print "\nLoading EFO6 files:\n"
    count = 0
    for directory in dirList:
        count += 1
        p = Process(target = loadEFO6, args = (directory, out_q, count))
        processes.append(p)
        p.start() 
    for directory in dirList:
        EFO6Files.update(out_q.get())
    for p in processes:
        p.join()
    print "\nEFO6 loading complete"
    
    return EFO6Files
    
def loadSubpop(subpop, subPopDir, out_q, count):
    outDict = {}
    while '  ' in subpop:
        subpop = subpop.replace('  ',' ')
    while subpop[0] == ' ':
        subpop = subpop[1:]
    while subpop[-1] == ' ':
        subpop = subpop[:-1]
    params = subpop.split(' ')
    direct = True
    if params == ["NOT","ANY"]:
        print "Error: well that's not particularly useful, is it?"
        loadType = "error"
    while params[0] == "NOT":
        direct = not direct
        params = params[1:]
    if len(params) == 1:
        loadType = "normal"
    elif len(params) == 2:
        loadType = "error"
        print "Error: 2 arguments found, 'NOT' expected as first parameter"
    elif len(params) == 3:
        if params[1] == "AND" or params[1] == "OR":
           loadType = params[1].lower()
        else:
            loadType = "error"
            print "Error: 3 arguments found, 'AND' or 'OR' expected as second parameter"
    else:
        loadType = "error"
        print "Error, no/ excess arguments found"
    if loadType == "error":
        outDict[subpop] = 'error'
        print "Terminating process due to error"
    else:
        if loadType == "normal":
            if params[0] != 'ANY':
                print "\tDirectly loading subpop", count, ":", params[0]
                temp = filterIDs(subPopDir + params[0], count)
                if temp == 'error':
                    outDict[subpop] = 'error'
                    print "Terminating process due to error"
                else:
                    outDict[subpop] = temp
                    outDict[subpop + "_type"] = direct
            else:
                print "\tSubpop", count, ": 'ANY' specified, will pass values from general population"
                outDict[subpop] = []
                outDict[subpop + "_type"] = True
        elif loadType == "and":
            print "\tLoading intersection of subpops", count, ":", params[0], "and", params[2] 
            temp = filterIDs(subPopDir + params[0], count)
            temp2 = filterIDs(subPopDir + params[2], count)
            if temp == 'error' or temp2 == 'error':
                outDict[subpop] = 'error'
                print "Terminating process due to error"
            else:
                outDict[subpop] = temp.intersection(temp2)
                outDict[subpop + "_type"] = direct
        elif loadType == "or":
            print "\tLoading combined subpops", count, ':', params[0], "or", params[2] 
            temp = filterIDs(subPopDir + params[0], count)
            temp2 = filterIDs(subPopDir + params[2], count)
            if temp == 'error' or temp2 == 'error':
                outDict[subpop] = 'error'
                print "Terminating process due to error"
            else:
                outDict[subpop] = temp.union(temp2)
                outDict[subpop + "_type"] = direct
                
    if outDict[subpop] != "ANY" and outDict[subpop] != "error": 
        outDict[subpop + '_popSize'] = popSize = len(outDict[subpop])
        print "\t\tSupopulation size:", popSize
        print "\t\tLoad complete, returning subpop", count
    else:
        outDict[subpop + '_popSize'] = 0

    out_q.put(outDict)
    
def getSubpops(script, subpopDir):
    subpopFiles = {}
    subpopList = []
    out_q = Queue()
    processes = []
    for line in script:
        for subpop in line[:2]:
            if subpop not in subpopList:
                subpopList.append(subpop)
    
    print "\nLoading subpop files:"
    count = 0
    for subpop in subpopList:
        count += 1
        p = Process(target = loadSubpop, args = (subpop, subpopDir, out_q, count))
        processes.append(p)
        p.start() 
    for subpop in subpopList:
        subpopFiles.update(out_q.get())
    for p in processes:
        p.join()
    print "Subpop loading complete"
    
    return subpopFiles  

            
def main():
    if len(sys.argv) > 2:
        if len(sys.argv) == 3:
            sys.argv.insert(2,'null') 
        else:
            print "Ignoring", len(sys.argv) - 2, "excess arguments\n"
    elif len(sys.argv) == 2:
            sys.argv.insert(1,'null')
            sys.argv.insert(1,'null')

    #script = gDocsImport.getScript(sys.argv[1], sys.argv[2], sys.argv[3], 0, -1, "default", False, [])
    params = gd.getLine(sys.argv[1], sys.argv[2], sys.argv[3], paramsLine, False, [])
    script = gd.getScript(sys.argv[1], sys.argv[2], sys.argv[3], toFromLine, EFO6Line, "default", False, [])
    directories = gd.getScript(sys.argv[1], sys.argv[2], sys.argv[3], EFO6Line, -1, "default", False, [])
    sys.argv = None
    
    outDir = prepDir(params[0])
    subpopDir = prepDir(params[1])
    filesOut = []
    
    for line in script:
        if len(line[0]) == 0 or len(line[1]) == 0:
            print "Error, missing to or from subpop name, line:", line
            quit()
    
    for line in directories:
        if line[0] not in filesOut:
            filesOut.append(line[0])
            flush = open(outDir + line[0],'w'); flush.close()
        if len(line[0]) == 0 or len(line[1]) == 0:
            print "Error, missing file or directory name, line:", line
            quit()
    
    if len(outDir) == 0:
        print "Error, no output directory specified"
        quit()
    elif not os.path.isdir(subpopDir):
        print "Error, subpop diretory", subpopDir, "does not exist"
        quit()
    elif len(filesOut) == 0:
        print "Error, no analysis output directories specified"
        quit()
    
    if not os.path.isdir(outDir):
        os.makedir(outDir)
    
    print "Prepping experiment, parameters are:\n"
    print "Analysis Directory:\n\t", outDir, "\nSubpop Directory:\n\t", subpopDir
    print "Subpopulations to/ from:\n", printList(script)
    print "Analyses:\n", printList(directories)
    
    EFO6Files = getEFO6s(directories)
    subpopFiles = getSubpops(script, subpopDir)
    if "error" in subpopFiles:
        print "Error termination"
        quit()
    
    allCurves = []
    for experiment in directories:
        for subpop in script:
            crossTalkEFO6 = {'EFO6':EFO6Files[experiment[1]],'iterations':EFO6Files[experiment[1] +'_iterations']} 
            crossTalkSubs = {'toPop':subpopFiles[subpop[0]],
                            'toType':subpopFiles[subpop[0]+'_type'],
                            'toName':subpop[0],
                            'fromPop':subpopFiles[subpop[1]],
                            'fromType':subpopFiles[subpop[1] + '_type'],
                            'fromName':subpop[1]}
            print "Analyszing crosstalk for", experiment[1], " with subpops", subpop[0:2]
            crossTalk = loadCrossTalk(crossTalkEFO6, crossTalkSubs)
            allCurves.append(crossTalk)
            print printList(crossTalk['crossTalkCurves'])
    
    print "CrossTalk Analysis Complete, preparing output"
    
            
    
main()
quit()
