import sys
import os
import chopper
import gDocsImport
import shutil


## Denotes separation on gdocs spreadsheet for web loading


varFolders = False
paramsStart = "Study Name Prefix (optional),Diagnosis Based"
avStart = "Condition Threshold Subpopulation,Condition Date"
startWord = "Subpopulation,Day/'enum',Length of Spread"
stopWord = "Diagnosis Model Version,Antiviral Model Version,"
    
## Writes antiviral and diagnosis scripts to directory 
  
  
def writeAvScript(avScript, diagParams, outName, directory):
    print "\nOutputting antiviral and diagnosis scripts %s and %s to directory %s" % (outName+'Antiviral',outName+'Diagnosis', directory)
    diagFile = open(directory + outName + "Diagnosis", 'w')
    avFile = open(directory + outName + "Antiviral", 'w')
    
    diagFile.write("# ----- RollVac.py Autogenerated Diagnosis File -----")
    diagFile.write("\nModelVersion = " + str(diagParams[0]))
    diagFile.write("\nProbSymptomaticToHospital = " + diagParams[3])
    diagFile.write("\nProbDiagnoseSymptomatic = " + diagParams[4])
    diagFile.write("\nDiagnosedDuration = " + diagParams[5])
    diagFile.write("\n# ----- End of Generated Diagnosis File -----")
    
    diagFile.close()
    
    avFile.write("# ----- RollVac.py Autogenerated Antiviral File -----")
    avFile.write("\n# Global parameters")
    avFile.write("\nAntiviralConfigVersion = " + diagParams[1])
    avFile.write("\nTotalAntiviralSupply = " + diagParams[2])
    
    pos = 0
    length = len(avScript)
    
    while pos < length:
        avFile.write("\n# -----------------------")
        avFile.write("\nInterventionId = " + str(pos+1))
        if len(avScript[pos][1]) != 0:
            avFile.write("\nConditionDate = " + avScript[pos][1])
        if percentFix(avScript[pos][2]) >= 1:
            avFile.write("\nConditionThresholdValue = " + avScript[pos][2])
        else:
            avFile.write("\nConditionThresholdFraction = " + str(percentFix(avScript[pos][2])))
        if len(avScript[pos][0]) != 0:
            avFile.write("\nConditionThresholdSubpopulation = " + avScript[pos][0])
        if isYes(avScript[pos][3], "Condition Diagnosis"):
            avFile.write("\nConditionDiagnosis = Required")
        if len(avScript[pos][4]) != 0:
            avFile.write("\nConditionMembership = " + directory + avScript[pos][4])
        if isYes(avScript[pos][5], "Condition Mutually Exclusive"):
            avFile.write("\nConditionMutex = Required")
        
        avFile.write("\n\nCompliance = " + avScript[pos][6])
        avFile.write("\nDelay = " + avScript[pos][7])
        avFile.write("\nDuration = " + avScript[pos][8])
        avFile.write("\nUnitNumberEachDay = " + avScript[pos][9])
        avFile.write("\nEfficacyIn = " + avScript[pos][10])
        avFile.write("\nCompliance = " + avScript[pos][11])
        
        pos +=1
    avFile.write("\n# ----- End of Generated Antiviral File ----")
    avFile.close()
    
    print "Antiviral treatment scripting complete"
    return length

    

## User interactive mode enumeration input


def getEnum():
    while True:
        print """\nEnter enumeration day and number list, format: 0 1; 1 5; 2 10; 3 14
per a given intervention, all enumeration must be taken care of in one call
further enumeration may lead to overlap with undesirable results for certain interventions"""
        enumerator =str(raw_input(":"))
        if len(enumerator) == 0:
            print "Nothing entered, defaulting to '0 1; 1 2; 3 5; 4 8'\n"
            enumerator = "0 1; 1 2; 3 5; 4 8"
        enumerator = enumerator.replace(";"," ; ")
        if checkEnum(enumerator):
            break
    return parseEnum(enumerator)
         
         
## Returns true if given properly formatted enumeration   
     
     
def checkEnum(enumerator):
    cmds = enumerator.split()
    pos = 0
    lim = len(cmds) 
    if lim%3 != 2:
        print "Error: enumerator missing/ extra terms"
        return False
    while pos < lim:
        if pos%3 ==1:
            if not chopper.isInt(cmds[pos]):
                if '%' in cmds[pos]:
                    cmds[pos] = cmds[pos].replace('%','')
                    try:
                        temp = float(cmds[pos])/ 100
                        if temp > 1 or temp <= 0:
                            print "Error: non integer enumerator outside of 0-100% range"
                            return False
                    except:
                        print "Error: improperly formatted percentage enumerator"
                        return False
                else:
                    try:
                        temp = float(cmds[pos])
                        if temp > 1 or temp <= 0:
                            print "Error: non integer enumerator outside of 0-100% range"
                            return False
                    except:
                        print "Error: improper string value, cannot convert"
                        return False
            else:
                if cmds[pos]<0:
                    print "Error: enumerator must be a positive integer or percentage"
                    return False
        
        if pos%3 == 0:
            if not chopper.isInt(cmds[pos]) or cmds[pos] < 0:
                print "Error: enumeration entry at pos", len, "is not a positive integer"
                return False
        if pos%3 == 2:
            if cmds[pos] != ";":
                print "Error: semicolon seperator not found"
                return False
        pos += 1
    return True
    

## Parses string enumeration commands to integer enumeration list    
    
    
def parseEnum(enumerator):
    enums = []
    cmds = enumerator.split()
    pos = 0
    lim = len(cmds) 
    while pos < lim:
        if pos%3 == 0:
            enums.append(int(cmds[pos]))
        if pos%3 == 1:
            enums.append(percentFix(cmds[pos]))
        pos += 1
    print "Valid intervention enumeration recieved:", enums
    return enums
 
       
## Sorts enumerations by day and combines same day interventions   
 
 
def cleanEnum(enumerator):
    workEnum = enumerator[:]
    oldEnum = workEnum[:]
    limit = len(workEnum)
    if len(workEnum) == 2:
        return workEnum
    used = False
    pos1 = 0
    while pos1 < limit-2:
        pos2 = pos1 +2
        while pos2 < limit:
            if workEnum[pos1] == workEnum[pos2]:
                workEnum[pos1+1] += workEnum[pos2+1]
                del workEnum[pos2:pos2+2]
                limit -= 2
                pos2 -= 2
                used = True
            if workEnum[pos1] > workEnum[pos2]:
                workEnum[pos1],workEnum[pos1+1], workEnum[pos2], workEnum[pos2+1] = workEnum[pos2], workEnum[pos2+1], workEnum[pos1], workEnum[pos1+1]
                used = True
            pos2 += 2
        pos1 += 2
        
    if used:
        print "Enumeration list cleaned up from original:", oldEnum
        print "to new:", workEnum, '\n'
    return workEnum

    
## Fixes user input percentage denoted values to internaldecimal notation  
         
         
def percentFix(value):
    if '%' in value :
                value = value.replace('%','')
                return float(value)/100
    else:
        return float(value)

        
## Replaces percentage enumerations with actual population specific integer values
           
                                     
def percentEnum(enumerator,size):
    pos1 = 1
    print
    workEnum =  enumerator[:]
    limit =  len(workEnum)    
    while pos1 < limit+1:
        temp = float(workEnum[pos1])
        if temp < 1:
            workEnum[pos1] = int(temp*size+0.5)
            if workEnum[pos1] == 0:
                print "Percentage", temp*100, "% of population size", size, "resulted in", workEnum[pos1], "individuals, entry ignored for enumeration" 
                del workEnum[pos1-1:pos1+1]
                limit -= 2
                pos1 -= 2
            else:
                print "Percentage", temp*100, "% of population size", size, "converted to", workEnum[pos1], "individuals for enumeration" 
        else:
            workEnum[pos1] = int(workEnum[pos1])
        pos1 += 2
    return workEnum


# User input checker, returns true/ false for yes/ no


def isYes(response, use):
    response = response.lower()   
    if response == 'y' or response == 'yes':
        result = True
    elif response == 'n' or response == 'no':
        result = False
    else:
        result = False
        print "Error, please enter 'y' or 'n' for %s, defaulting to 'n'" %(use)  
    return result  
                        


## MAIN



def main(arg1, arg2, arg3, arg4):
        

    print arg1, arg2, arg3, arg4
    
    if __name__ != '__main__':
        sys.argv = ['RollVac.py',arg1,arg2,arg3,arg4]
        print "huzzah!"
    
    if arg1 == "poly":
        del sys.argv[3:5]

 
    trigger = 1
    subnum = 0
    path = ""
    population = "" 
    pos = 0
    iCode = 0
    
    vacTotal =  0
    avTotal = 0
    socialTotal = 0
    workTotal = 0
    schoolTotal = 0
    avTreatments = 0
    
#    vacEnum = False
#    avEnum = False
#    socialEnum = False
#    workEnum = False
#    schoolEnum = False


## UNIX PASSED ARGUMENTS DECISION TREE
    
    
    if len(sys.argv) <= 1:
        print "Missing arguments, defaulting to user mode with file prefix 'Default'\n"
        arg =  "user"
        outName = "Default"
    elif sys.argv[1] == "help":
        print """\nArguments: chopper.py {filepath/user} {intervention outfile}
        (Filepath): loads vaccination spread commands from an external script at (filepath)
        user: manual mode, enter each vaccination manually, enter (done) to quit\n"""
        quit()
    elif len(sys.argv) == 2:
        print "Missing 2nd argument, defaulting to file prefix 'Default'"
        arg = sys.argv[1]
        outName = "Default"
    elif len(sys.argv) > 3:


## LOADS PUBLIC/ PRIVATE DATA FROM GDOC IF PASSED
   
        if sys.argv[1] == "gdoc" or sys.argv[1] == "poly":
            arg = "gDoc"
            if len(sys.argv) == 4:
                sys.argv.insert(3,'null') 
            else:
                print "Ignoring", len(sys.argv) - 3, "excess arguments\n"
    elif len(sys.argv) == 3:
        if sys.argv[1] == "gdoc" or sys.argv[1] == "poly":
            arg = "gDoc" 
            sys.argv.insert(2,'null')
            sys.argv.insert(2,'null')
        else:
            outName = sys.argv[2]
            arg = sys.argv[1]


## LOADS AND WRITES AV/ DIAG SCRIPT FROM GOOGLE DOC, NOT IMPLEMENTED FOR USER/ LOCAL SCRIPT MODE
 
                                               
    print sys.argv
    if arg == "gDoc":
        
        if sys.argv[1] == "poly":
            isPoly = True
            sys.argv[3] = 'null'
            path = arg2
            if os.path.exists(path):
                shutil.rmtree(path)
            os.makedirs(path)
        else:
            isPoly = False
        loadType = "intervention script"
        print sys.argv
        script = gDocsImport.getScript(sys.argv[2], sys.argv[3], sys.argv[4], startWord, stopWord, loadType, isPoly)
        params = gDocsImport.getLine(sys.argv[2], sys.argv[3], sys.argv[4],paramsStart, isPoly)
        
        outName = params[0]

        if len(outName) == 0:
            print "No name prefix stored, using default intervention, antiviral, and diagnosis"
            outName = ""
            
        print "Will write to intervention file '%sIntervention'\n" % outName

        diag = params[1]
        diagnosis = isYes(diag, "diagnosis")
        
        if not diagnosis:
            sys.argv[3] = "null"
        else:
            loadType = "default"
            avScript = gDocsImport.getScript(sys.argv[2], sys.argv[3], sys.argv[4], avStart, 0, loadType, isPoly)
            diagParams = gDocsImport.getLine(sys.argv[2], sys.argv[3], sys.argv[4], stopWord, isPoly)
            sys.argv[3] = "null"               
            avTreatments = writeAvScript(avScript, diagParams, outName, path)
        
        
    if arg != "user" and arg != "gDoc" and arg != "gdoc" and (not os.path.isfile(arg)):
        print arg
        print "Error, cannot open file or directory\n"
        quit()     
        
    done = False
    
    
## LOCAL SCRIPT FILE LOADING
    
    
    if arg != "user" and arg != "gDoc":
        scriptfile = open(arg)    
        script = []    
        line = 0
        gotPath = False
        while True:
                testline = scriptfile.readline()
                if len(testline) == 0:
                    break
                if not testline.startswith("#"):
                    if testline.startswith("Directory"):
                        gotPath =  True
                        temp = testline.split()
                        if len(temp) <2:
                            path = ""
                        else:
                            path = testline.split()[1]
                            if (path == "local" or path == "Local"):
                                path = ""
                    else:
                        script.append(testline)
                        line += 1
        if not gotPath:
            path = ""
        
              
## USER FILE LOADING       
            
            
    if arg == "user":
        print """\nEnter desired intervention & subpopulation storage directory
Subpops will be created in local subpops folder, though intervention file will point to said directory
Enter 'local' to use current working directory or 'explicit' for a direct link"""
        path=str(raw_input(":"))
        if path == "explicit":
            path = os.getcwd()
        if (path == "local") or (path == "home") or (len(path) == 0):
            path = ""
            
        print "\nEnter desired intervention start number, default 1, useful for appending interventions to pre-existing files"
        number=raw_input(":")
        try:
            trigger = int(number)
            if trigger <= 0:
                print "Entry must be greater than 0, defaulting to 1\n"
                trigger = 1
        except:
            print "No entry/ invalid entry, defaulting to 1\n"
            trigger = 1


# FLUSH INTERVENTION FILE
        
        
    outFile = open(path + outName + "Intervention", 'w')
    outFile.write("# ----- RollVac.Py Autogenerated Intervention File -----\n")
    outFile.close()

        
## GENERATING OUTPUT FILE LOOP
    
    
    while not done:
    
        subnum += 1
        enum = False
    

## USER CONTROLLED CHOPPING
    
            
        if arg == "user":
            
            while True:
                print "\nEnter source population filename/ directory"
                population=str(raw_input(":"))
                if len(population) == 0:
                    print "Nothing entered, defaulting to 'SUBPOP'\n"
                    population = "SUBPOP"
                if population == "done":
                    print "Data entry complete, quitting now!\n"
                    done = True
                    break
                if len(population) == 0:
                    population = "EFO6"
                try:
                    with open(population): pass
                    break
                except:
                    print "Error: population file", population, "not found\n"
            
            if done:
                break
            
            while True:   
                print "\nEnter desired intervention trigger day/ 'enum' for enumerated intervention"
                number=raw_input(":")
                if str(number) == 'enum' or str(number) == 'e':
                    enum = True
                    enumList = getEnum()
                    break
                else:
                    try:
                        day = int(number)
                        if day <= 0:
                            print "Error: invalid entry, please enter a positive integer or 'enum'\n"
                        else:
                            break
                    except:
                        print "Error: invalid entry, please enter a positive integer\n"
    
            
            while not enum:
                print "\nEnter desired intervention time to completion"
                number=raw_input(":")
                try:
                    length = int(number)
                    if length <= 0:
                        print "Error: invalid entry, please enter a positive integer\n"
                    else:
                        break
                except:
                    print "Error: invalid entry, please enter a positive integer\n"
        
            while True:
                print """\nEnter intervention type with numerical parameters (ex: Vaccination 10 0.5 .7)
Text will be saved to intervention file exactly as entered with generated
action number and subpopulation directory appended"""
                interv=str(raw_input(":"))
                temp =  interv.split()
                if len(temp) == 0:
                    print "Error: please enter intervention command\n"
                else:   
                    method = temp[0]
                    target = 0
                    if method == "Vaccination":
                        target = 4
                        meth = "v"
                        iCode = 0
                    elif method == "Antiviral":
                        target = 5
                        meth = "av"
                        iCode = 1000
                    elif method == "SocialDistancing":
                        target = 3
                        meth = "sd"
                        iCode= 2000
                    elif method == "WorkClosure":
                        target = 3
                        meth = "cw"
                        iCode = 3000
                    elif method == "SchoolClosure":
                        target = 3
                        meth =  "cs"
                        iCode = 4000
                    if (len(temp) != target):
                        print "Error:",  len(temp), "parameters found,", target, "expected for intervention type", method, "\n"
                    elif target == 0:
                        print "Error:", method, "method not recognized\n"
                    else:
                        if not temp[1].isdigit():
                            print "Error: second value must be an integer"
                        else:
                            pos2 = 1
                            allGood = True
                            while pos2 < target:
                                if not chopper.isInt(temp[pos2]):
                                    allGood = False
                                pos2 += 1
                            if not allGood:
                                print temp
                                print "Error: non-numerical parameters found\n"
                            else:
                                break  
  
                                                                              
##  LOCAL SCRIPT/ GDOC CONTROLLED CHOPPING                                                                         
                                                                                                                    
                                                                                                                                                                                                
        else:
            if pos == len(script):
                done = True
                break
                
            cmd = script[pos]
            items = cmd.split()
            population =  items[0]
            try:
                with open(population): pass
            except:
                print "Error: population file", population, "not found\n"
                quit()
            
            if str(items[1]) == 'enum':
                enum = True
                cmd = cmd.replace("enum","null null")
                items = cmd.split()
                pos += 1
                enumList = script[pos].replace(";"," ; ")
                if checkEnum(enumList):
                    enumList = parseEnum(enumList)
                else:
                    print "Error: misformatted enumeration list", enumList
                    quit()
            
            if not enum:
                try:
                    day = int(items[1])
                    if day <= 0:
                        print "Error, day must be an integer greater than zero\n"
                        quit()
                except:
                    print "Error, day must be an integer greater than zero\n"
                    quit()
                try:
                    length = int(items[2])
                    if length <= 0:
                        print "Error, length must be an integer greater than zero\n"
                        quit()
                except:
                    print "Error, length must be an integer greater than zero\n"
                    quit()
            
            temp = cmd.split()
            print "Generating interventions with parameters:",cmd
            method = temp[3]
            if method == "Vaccination":
                target = 7
                meth = "v"
                iCode = 0
            elif method == "Antiviral":
                target = 8
                meth = "av"
                iCode = 1000
            elif method == "SocialDistancing":
                target = 6
                meth = "sd"
                iCode = 2000
            elif method == "WorkClosure":
                target = 6
                meth = "cw"
                iCode = 3000
            elif method == "SchoolClosure":
                target = 6
                meth = "cs"
                iCode = 4000
            else:
                print "Error:", method, "method not recognized\n"
                quit()
            if (len(temp) != target):
                print "Error:",  len(temp), "parameters found,", target, "expected for intervention type", method, "\n"
                quit()
            
            
            interv = " ".join(temp[3:target])
            pos += 1
    
        suffix = str(subnum) + meth

## ALL MODE CHOPPING EXECUTION

        if enum:
            populationSize = chopper.popSize(population)
            enumList = cleanEnum(percentEnum(enumList,populationSize))
            holder = chopper.main(population,'e'," ".join(map(str, enumList)),suffix, path)
            returnSize = holder['count']
            enumList = holder['enum']
            length = chopper.getEnumSize(enumList)
        else:
            holder = chopper.main(population,'b',str(length),suffix, path)
            returnSize = holder['count']

## NON TREATMENT BASED INTERVENTION TRACKING            
    
        if meth == "v":
            vacTotal += returnSize
        elif meth == "av":
            avTotal += returnSize
        elif meth == "sd":
            socialTotal += returnSize
        elif meth == "cw":
            workTotal += returnSize
        elif meth == "cs":
            schoolTotal += returnSize
        

# WRITING INTERVENTION FILE (AV TREATMENT & DIAG HANDLED SEPERATELY)
        
        if enum:
            pos2 = 0
            outFile = open(path + outName+'Intervention', 'a+b')
            while pos2 < len(enumList):
                subPopName = population + str(pos2/2) + suffix
                triggerOut = "Trigger " + str(trigger+iCode) + " Day " + str(enumList[pos2]) + "\n" 
                intervOut = "Action " + str(trigger+iCode) + " " + interv + " " + path + "/subpops/" + subPopName + "\n"
                print triggerOut, intervOut.replace('\n','')
                outFile.write(triggerOut)
                outFile.write(intervOut)
                trigger += 1
                pos2 += 2
            outFile.close()
            print
            
        else:
            pos2 = 0
            outFile = open(path + outName+'Intervention', 'a+b')
            while pos2 < length:
                subPopName = population + str(pos2) + suffix
                triggerOut = "Trigger " + str(trigger+iCode) + " Day " + str(day+pos2) + "\n" 
                intervOut = "Action " + str(trigger+iCode) + " " + interv + " " + path + "/subpops/" + subPopName + "\n"
                print triggerOut, intervOut.replace('\n','')
                outFile.write(triggerOut)
                outFile.write(intervOut)
                trigger += 1
                pos2 += 1
            outFile.close()
            print

## APPENDING NON TREATMENT INTERVENTION TOTALS               
                                              
    outFile = open(path + outName+'Intervention', 'a+b')
    outFile.write("""\n#----- End of Generated Intervention File -----\n\n# RollVac.Py Pre Compliance Intervention Totals- calculated per output,
does not account for over-application to a given set of IDs. 
Please apply only one of each type per sub pop, using enumerated
interventions for complex interventions.""")
    outFile.write("\n# Vaccination: " + str(vacTotal))
    outFile.write("\n# Antiviral Prophylaxis: " + str(avTotal))
    outFile.write("\n# Social Distancing: " + str(socialTotal))
    outFile.write("\n# Close Work: " + str(workTotal))
    outFile.write("\n# Close Schools: " + str(schoolTotal))
    outFile.write("\n# AV Treatment Programs: " + str(avTreatments))
    outFile.close()
    print """RollVac.Py Pre Compliance Intervention Totals- calculated per output,
does not account for over-application to a given set of IDs. 
Please apply only one of each type per sub pop, using enumerated 
interventions for complex interventions."""
    print "\nVaccination: " + str(vacTotal)
    print "Antiviral Prophylaxis: " + str(avTotal)
    print "Social Distancing: " + str(socialTotal)
    print "Close Work: " + str(workTotal)
    print "Close Schools:" + str(schoolTotal)
    print "AV Treatment Programs: " + str(avTreatments)
    
if __name__ == '__main__':    
    main(0,0,0,0)
    print "Intervention scripting succesfully completed, exiting now.\n"
    quit