import gDocsImport
import sys, os

def writeToFiles(directory, runList, refMatrix, valMatrix, xTitles, yTitles, title):
    if not os.path.exists(directory):
        os.mkdir(directory)
    writeOut = open(directory+title,'w')
    xLen = len(xTitles)
    yLen = len(yTitles)
    writeOut.write('EFO6 Length Values' + ', '*(xLen) + '\n, ') 
    pos = 0
    while pos < xLen:
        writeOut.write(xTitles[pos] + ', ')
        pos += 1
    writeOut.write('\n')
    posY =0
    while posY < yLen:
        writeOut.write(yTitles[posY] + ', ')
        posX = 0
        while posX < xLen:
            writeOut.write(str(valMatrix[posX][posY]) + ', ')
            posX += 1
        posY += 1
        writeOut.write('\n')
    writeOut.write('\nQsubList Line References' + ', '*(xLen) + '\n, ')
    pos = 0
    while pos < xLen:
        writeOut.write(xTitles[pos] + ', ')
        pos += 1
    writeOut.write('\n')
    posY =0
    while posY < yLen:
        writeOut.write(yTitles[posY] + ', ')
        posX = 0
        while posX < xLen:
            writeOut.write(str(refMatrix[posX][posY]) + ', ')
            posX += 1
        posY += 1
        writeOut.write('\n')
    pos = 0
    writeOut.write('\nLines Ran' + ', '*(xLen) + '\n')
    while pos < len(runList):
        print runList[pos]
        writeOut.write(runList[pos] + ', '*(xLen) + '\n')
        pos += 1
    writeOut.close()

def writeAll(directory,title,data):
    if not os.path.exists(directory):
        os.mkdir(directory)
    summaryOut = open(directory+title+'Summary.txt','w')
    chartsOut = open(directory+title+'Charts.csv','w')
    summaryOut.write("Directory:/t" + str(data['directory']))
    summaryOut.write("\nPopsize:/t" + str(data['popsize']))
    summaryOut.write("\nIterations:/t" + str(data['iterations']))
    summaryOut.write("\nAttack Rates:/t" + str(data['directory']))
    summaryOut.write("\nPeak Day:/t" + str(data['peakDay']))
    summaryOut.write("\nPeak Number:/t" + str(data['peakNumber']))
    summaryOut.write("\nIgnored:/t" + str(data['ignored']))
    summaryOut.write("\nPercent Reaching Epidemic:/t" + str(data['epiPercent']))
    summaryOut.write("\nEpidemic Mean Attack Rate:/t" + str(data['epiMean']))
    summaryOut.write("\nSecondary Maxima:/t" + str(data['secondaryMaxima']))
    summaryOut.close()
    chartsOut.write('ATTACK RATE V DAY' + ','*(data['iterations']+1) + '\n')
    chartsOut.write('DAY, ')
    pos = 0
    while pos < data['iterations']:
        chartsOut.write(',' + str(pos) + ' ')
        pos += 1
    chartsOut.write(', MEAN\n')
    pos1 = 0
    while pos1 < data['days']:
        pos2 = 0
        chartsOut.write(str(pos1) + ', ')
        while pos2 < data['iterations']:
            chartsOut.write(str(data['iterationsByDay'][pos2][pos1]) + ', ')
            pos2 += 1
        chartsOut.write(str(data['MeanCurve'][pos1]) + '\n')
        pos1 += 1
    chartsOut.close()

def checkLines(fileName):
    wholeThing = open(fileName)
    content = wholeThing.readlines()
    params = content[0].split(' ')    
    popSize = int(params[1])
    iterations = int(params[3])
    trimmed = content[popSize+2:]
    pos = 0
    length =  len(trimmed)
    days = 0
    while pos < length:
	if '#' in trimmed[pos]:
		print "Ignoring comment:", trimmed[pos]
		del trimmed[pos]
		length -= 1
	else:
        	trimmed[pos] = map(int,trimmed[pos].split(' '))
        	days =  max(days, trimmed[pos][2])
        	pos += 1
    limit =  len(trimmed)
    
    pos = 0
    iterXDay = [[0 for pos1 in range(days+1)] for pos2 in range(iterations)]
    while pos < limit:
	#print trimmed[pos]
	iterXDay[trimmed[pos][1]][trimmed[pos][2]] += 1
        pos += 1
    
    print iterXDay
    pos = 0
    attackRates = []
    ignore = [False]*iterations
    ignored = 0
    maxDay = []
    maxNumber = []
    while pos < iterations:
        attackRates.append(sum(iterXDay[pos]))
        maxima = max(iterXDay[pos])
        maxNumber.append(max(iterXDay[pos]))
        maxDay.append(iterXDay[pos].index(maxima))
        pos += 1
    meanAttack = sum(attackRates)/iterations
    print "Attack Rates:", attackRates
    print "Mean:", meanAttack
    print "Peak Days:", maxDay
    print "Peak Infected:", maxNumber
    
    pos = 0
    epiAttack = 0
    while pos < iterations:
        if attackRates[pos] < meanAttack/10:
            ignore[pos] =  True
            ignored += 1
            print "Iteration",pos,"did not reach epidemic status"
        else:
            epiAttack += attackRates[pos]
        pos += 1
    print "Ignored:", ignored
    epiMean = epiAttack/(iterations-ignored)
    epiPercent = (iterations-ignored)/iterations
    print "Percent Reaching Epidemic:", epiPercent*100
    print "Mean epdidemic attack rate:", epiMean
    
    pos1 = 0
    meanCurve = []
    while pos1 < days:
        pos2 = temp = 0
        while pos2 < iterations:
            if not ignore[pos]:
                temp += iterXDay[pos2][pos1]
            pos2 += 1
        meanCurve.append(temp/(iterations-ignored))
    
    leftBounds = []
    rightBounds = []
    lengths = []
    secondaryMaxima = [""]*iterations
    curveWidth = .95
    searchWidth = .20
    peakToLocal = 10
    localSNR = 2
    pos1 = 0
    while pos1 < iterations:
        pos2 = temp = 0
        outside = (1-curveWidth)*attackRates[pos1]*0.5
        while pos2 < days:
            temp += iterXDay[pos1][pos2]
            if temp > outside:
                leftBounds.append(pos2)
                print "left bound:",pos2
		break
            pos2 += 1
        pos2 = days-1
        temp = 0
        while pos2 > 0:
            temp += iterXDay[pos1][pos2]
            if temp > outside:
		print "right bound:",pos2
                rightBounds.append(pos2)
                break
            pos2 -= 1
        lengths.append(rightBounds[pos1]-leftBounds[pos1])
        sliceWidth = int(lengths[pos1]*searchWidth)
        pos2 = leftBounds[pos1]
        while pos2 + sliceWidth < rightBounds[pos1]:
            tempSlice = iterXDay[pos1][pos2:min(pos2+sliceWidth+1,days)]
            localPeak = max(tempSlice)
	    print tempSlice, localPeak
            localMaxima = tempSlice.index(localPeak)
            
	    if localMaxima == 0:
		pos2 += 1
            elif localMaxima > sliceWidth/2:
                pos2 += localMaxima - sliceWidth/2
            elif localPeak*peakToLocal >= maxNumber[pos1] and localPeak != maxNumber[pos1] and str(localMaxima + pos2) not in secondaryMaxima[pos1]:
                leftSlice = tempSlice[0:localMaxima]
                rightSlice = tempSlice[localMaxima:len(tempSlice)+1]
		leftMin = min(leftSlice)
                rightMin = min(rightSlice)
                if localPeak>(leftMin+rightMin)*0.5*localSNR:
		    pos2 += localMaxima
                    secondaryMaxima[pos1] += str(localMaxima+pos2) + ' '
                    print "Secondary Maxima found in iteration %s on day %s" % (str(pos1),str(pos2+localMaxima))   
            	else:
			pos2 += 1
	    else:
                pos2 += 1
        pos1 += 1
        
    return {'directory':fileName,'days':days,'meanCurve':meanCurve,'popsize':popSize,'iterations':iterations,'attackRates':attackRates,"Ignored":ignored,'epiMean':epiMean,'epiPercent':epiPercent,'peakDay':maxDay,'peakNumber':maxNumber,'secondaryMaxima':secondaryMaxima,"iterationsByDay":iterXDay}
    
def prepDir(directory):
    return (directory+'/').replace('//','/')

def main():
    
    if len(sys.argv) > 2:
        if len(sys.argv) == 3:
            sys.argv.insert(2,'null') 
        else:
            print "Ignoring", len(sys.argv) - 2, "excess arguments\n"
    elif len(sys.argv) == 2:
            sys.argv.insert(1,'null')
            sys.argv.insert(1,'null')

    script = gDocsImport.getScript(sys.argv[1], sys.argv[2], sys.argv[3], 0, -1, "default", False, [])
    sys.argv = None
    print script
    
    column = 1
    while column < len(script[0]):
        params = []
        pos = 0
        limit  = len(script)
        while pos < limit:
            params.append(script[pos][column])
            pos += 1
        
        print params
        directoryIn = prepDir(params[0])
        directoryOut = prepDir(params[1])
        studyName = params[2]
        qsubDir = params[3]
        target = params[4]
        runAll = params[14].lower()[0] == 'y'
    
        xID = int(params[7])
        xFind = params[8].split(' ')
        xFLen = len(xFind)
        toFindX = xFLen > 0
        xIgnore = params[9].split(' ')
        xILen = len(xIgnore)
        toIgnoreX = xIgnore != ['']
        
        yID =  int(params[10])
        yFind = params[11].split(' ')
        yFLen =  len(yFind)
        toFindY = yFLen > 0
        yIgnore = params[12].split(' ')
        yILen = len(yIgnore)
        toIgnoreY = yIgnore != ['']
        
        const =  params[13].split(' ')
        cLen = len(const)
        
        
        fileIn = open(directoryIn + qsubDir)
        qsubList = fileIn.readlines()
        fileIn.close()
        
        pos = 0
        
        splitList =[]
        if "chmod -R 775" in qsubList:
            del qsubList[qsubList.index("chmod -R 775")]
        limit = len(qsubList)
        while pos < limit:
            if runAll:
                qsubList[pos] = qsubList[pos].replace('qsub ','').replace('qsub','').replace('/\n','')
            else:
                qsubList[pos] = qsubList[pos].replace('qsub ','').replace('qsub','').replace(directoryIn,'').replace('/\n','')
            if qsubList[pos].split('/') not in splitList:
		splitList.append(qsubList[pos].split('/'))
		pos += 1
	    else:
		print "Duplicate entry on line %s ignored" % (pos)
		del qsubList[pos]
		limit -= 1

        width = qsubList[0].count('/') + 1 
        
        if not runAll:
        
            limit = len(splitList)
            targetStrings = ['']*width
            tracker = [0] * width
            pos1 = 0
            while pos1 < limit:
                pos2 = 0
                while pos2 < width:
                    word = splitList[pos1][pos2]
                    keep = True
                    isAxis = True
                    if pos2 == xID:
                        found = False
                        pos3 = 0
                        while pos3 < xFLen:
                            if xFind[pos3] in word:
                                found = True
                                break
                            pos3 += 1
                        pos3 = 0
                        while pos3 < xILen and toIgnoreX:
                            if xIgnore[pos3] in word:
                                keep = False
                                break
                            pos3 += 1
                        if toFindX and not found:
                            keep = False
                    elif pos2 == yID:
                        found = False
                        pos3 = 0
                        while pos3 <yFLen:
                            if yFind[pos3] in word:
                                found = True
                                break
                            pos3 += 1
                        pos3 = 0
                        while pos3 < yILen and toIgnoreY:
                            if yIgnore[pos3] in word:
                                keep = False
                                break
                            pos3 += 1
                        if toFindY and not found:
                            keep = False
                    else:
                        isAxis = False
                        if word in const and word not in targetStrings[pos2]:
                            tracker[pos2] += 1
                            targetStrings[pos2] += word + ' ' 
                    if isAxis and keep and word not in targetStrings[pos2]:
                        targetStrings[pos2] += word + ' '
                        tracker[pos2] += 1
                    pos2 += 1
                pos1 += 1
            
            targetList = [[]]*width
            pos = 0
            while pos < width:
                count = targetStrings[pos].count(' ')
                if pos == xID:
                    if count == 0:
                        print "Error: no variables found for X axis"
                        quit()
                    elif count == 1:
                        print "Warning: only one variable found for X axis"
                elif pos == yID:
                    if count == 0:
                        print "Error: no variables found for Y axis"
                        quit()
                    elif count == 1:
                        print "Warning: only one variable found for Y axis"
                else:
                    if count > 1:
                        print "Error, multiple variables found for const #%s, operators = %s" % (str(pos), const)
                targetList[pos] = targetStrings[pos].split(' ') [:-1]
                pos += 1
                
            runList = []
            xCols =  len(targetList[xID])
            yRows =  len(targetList[yID])
            refMatrix = [[0 for pos1 in range(yRows)] for pos2 in range(xCols)]
            valMatrix = [[0 for pos1 in range(yRows)] for pos2 in range(xCols)]
            dirMatrix = [[0 for pos1 in range(yRows)] for pos2 in range(xCols)]
            testMatrix = [[0 for pos1 in range(yRows)] for pos2 in range(xCols)]
            
            
            pos1 = 0
            limit = len(splitList)
            while pos1 < limit:
                pos2 = 0
                keepLine = True
                while pos2 <  width:
                    if splitList[pos1][pos2] not in targetStrings[pos2]:
                        keepLine = False
                        break
                    pos2 += 1
                if keepLine:
                    xPos =  targetList[xID].index(splitList[pos1][xID])
                    yPos = targetList[yID].index(splitList[pos1][yID])
                    print xPos, yPos
                    refMatrix[xPos][yPos] = pos1
                    testMatrix[xPos][yPos] = xPos
                    dirMatrix[xPos][yPos] = directoryIn + qsubList[pos1] + '/' + target
                    temp = checkLines(dirMatrix[xPos][yPos])
                    valMatrix[xPos][yPos] = temp['epiMean']          
                    print pos1
                    print qsubList[pos1]
                    runList.append(qsubList[pos1])
                    
                pos1 += 1
            print runList
            print refMatrix
            print valMatrix
            
            xTitles = targetList[xID]
            yTitles = targetList[yID]
            print xTitles
            print yTitles
        
            writeToFiles(directoryOut, runList, refMatrix, valMatrix, xTitles, yTitles, studyName)
        
        if runAll:
            pos = 0
            limit = len(qsubList)
            attackOut = open(directoryOut + '/' + studyName + 'AttackList.txt','w')
            attackOut.close()
            attackOut = open(directoryOut + '/' + studyName + 'AttackList.txt','a+b')
            attackOut.write("# Attack Rate List\n")
            while pos < min(limit,10):
                data = checkLines(qsubList(pos))
                writeAll(directoryOut, studyName+qsubList(pos).replace('/','_'), data)
                attackOut.write(qsubList(pos) + ' ' + str(data['epiMean']))
                pos += 1
                
        
        column += 1
        
    print "Finished analyses, quitting now"
        
        
    

    
    
                
                    
                
    

    



main()
quit()