#!/usr/bin/python
import readline
import subprocess
import os 
import sys
import glob
import tarfile
import shutil
import datetime
import socket
import time

#setup environment and PWD
#setup environment and PWD
patDir = "/var/opt/sca/patterns/"
try:
  os.chdir(os.environ["PWD"])
  setup = os.environ["SCA_READY"]
except Exception:
  print >> sys.stderr, "Error: Do not run directly"
  sys.exit()
if not setup:
  sys.exit()

#commands MUST have a function with the same name.
COMMANDS = ["analyze", "exit", "view", "help"]
#help pages: 
#<command name>: <what it does>\n example: <command example>\n <other info>
COMMANDS_HELP = ["analyze: analyze a supportconfig\nexample: analyze /path/to/supportconfig\nIf no supportconfig is given this will run a supportconfig then analyze the newly created supportconfig",
		 "view: view report files\nexample: view /path/to/report.html\nIf no path given it will try to open newly created report."]
command = ""
def tabSystem(text, size):
  commandBuffer = readline.get_line_buffer()
  compleateCommands = []
  for i in COMMANDS:
    #auto complete to command name
    if i == commandBuffer.split(" ")[0]:
      #if the command has an argument auto complete to path names (unless the command is help)
      if len(commandBuffer.split(" ")) > 0 and commandBuffer.split(" ")[0] != "help":
	if os.path.isdir((glob.glob(commandBuffer.split(" ")[1]+'*'))[size]):
	  return (glob.glob(commandBuffer.split(" ")[1]+'*'))[size] + "/"
	return (glob.glob(commandBuffer.split(" ")[1]+'*'))[size]
    if i.startswith(text):
      compleateCommands.append(i)
  if size < len(compleateCommands):
      return compleateCommands[size]
  else:
      return None
      

#setup globals
global results
global knownClasses
global HTML
global outputFileGiven
global HtmlOutputFile 
global KeepArchive
outputFileGiven = False
knownClasses = []
results = []
HtmlOutputFile = ""
KeepArchive = False

#returns html code. This is the about server part.
####example####
#Server Information
#Analysis Date:	/10/7/2013 12:39
#Archive File:	/home/david/nts_DOCvGRPSdr_130528_1137.html
 
#Server Name:      <Server Name>                                    Hardware:              VMware Virtual Platform
#Distribution:     SUSE Linux Enterprise Server 10 (x86_64)      Service Pack:          4
#OES Distribution: Novell Open Enterprise Server 2.0.3 (x86_64)  OES Service Pack:      3
#Hypervisor:       VMware (hardware platform)                    Identity:              Virtual Machine (hardware platform)
#Kernel Version:   2.6.16.60-0.99.1-default                      Supportconfig Version: 2.25-359

def getHeader(*arg):
  #reset variables
  supportconfigVersion = ""
  oesVersion = ""
  oesPatchLevel = ""
  OS = ""
  OSVersion = ""
  patchLevel = ""
  kernelVersion = ""
  serverName = ""
  hardWare = ""
  virtualization = ""
  vmIdentity = ""
  timeString = ""
  returnHTML = ""
  
  #set archive name if given
  if len(arg) == 2:
    arcName = arg[1]
  else:
    arcName = ""
  TIME = datetime.datetime.now()
  
  #set timeString (example: /10/7/2013 10:14)
  timeString = "/" + str(TIME.month) + "/" + str(TIME.day) + "/" + str(TIME.year) + " " + str(TIME.hour) + ":" + str(TIME.minute).zfill(2)
  
  #open basic-environment
  File = open(arg[0] + "basic-environment.txt")
  File.readline()
  File.readline()
  
  #get supportconfig version
  supportconfigVersion = File.readline().split(':')[-1].strip()
  
  #read basic-environment line by line to pull out data. (pull: serverName, oesVersion, oesPatchLevel, etc)
  while True:
    line = File.readline()
    if not line:
      break
      
    #get hardWare
    if line.startswith("Hardware:"):
      hardWare = line.split(":")[1].strip()
      
    #get virtualization
    if line.startswith("Hypervisor:"):
      virtualization = line.split(":")[1].strip()
      
    #get virtualization identity
    if line.startswith("Identity:"):
      vmIdentity = line.split(":")[1].strip()
      
    #get kernel version and server name
    if "/bin/uname -a" in line:
      tmp = File.readline().split(" ")
      kernelVersion = tmp[2].strip()
      serverName = tmp[1].strip()
      
    #get OS Version and patch level
    if "/etc/SuSE-release" in line:
      OS = File.readline().strip()
      OSVersion = File.readline().split('=')[-1].strip()
      patchLevel = File.readline().split('=')[-1].strip()
      
    #get OES version and pathch level
    if "/etc/novell-release" in line:
      oesVersion = File.readline().strip()
      #we don't need the oes version just SP so skip the next line
      File.readline()
      oesPatchLevel = File.readline().split('=')[-1].strip()
  File.close()
  
  #create HTML from the data we just got
  returnHTML = returnHTML + '<H1>Supportconfig Analysis Report</H1>\n'
  returnHTML = returnHTML + '<H2><HR />Server Information</H2>\n'

  returnHTML = returnHTML + '<TABLE WIDTH=100%>\n'
  returnHTML = returnHTML + '<TR><TD><B>Analysis Date:</B></TD><TD>'
  returnHTML = returnHTML + timeString
  returnHTML = returnHTML + '</TD></TR>\n'
  returnHTML = returnHTML + '<TR><TD><B>Archive File:</B></TD><TD>'
  returnHTML = returnHTML + arcName
  returnHTML = returnHTML + '</TD></TR>\n'
  returnHTML = returnHTML + '</TABLE>\n'
  
  returnHTML = returnHTML + '<TABLE CELLPADDING="5">\n'
  
  returnHTML = returnHTML + '<TR><TD>&nbsp;</TD></TR>\n'
  
  returnHTML = returnHTML + '<TR></TR>\n'
  
  #Server name and hardWare
  returnHTML = returnHTML + '<TR><TD><B>Server Name:</B></TD><TD>'
  returnHTML = returnHTML + serverName
  returnHTML = returnHTML + '</TD><TD><B>Hardware:</B></TD><TD>'
  returnHTML = returnHTML + hardWare
  returnHTML = returnHTML + '</TD></TR>\n'
  
  #OS and PatchLevel
  returnHTML = returnHTML + '<TR><TD><B>Distribution:</B></TD><TD>'
  returnHTML = returnHTML + OS
  returnHTML = returnHTML + '</TD><TD><B>Service Pack:</B></TD><TD>'
  returnHTML = returnHTML + patchLevel
  returnHTML = returnHTML + '</TD></TR>\n'
  
  if oesVersion != "":
    #OES version and OES patchLevel
    returnHTML = returnHTML + '<TR><TD><B>OES Distribution:</B></TD><TD>'
    returnHTML = returnHTML + oesVersion
    returnHTML = returnHTML + '</TD><TD><B>OES Service Pack:</B></TD><TD>'
    returnHTML = returnHTML + oesPatchLevel
    returnHTML = returnHTML + '</TD></TR>\n'
    
  if virtualization != "None" and virtualization != "":
    #hypervisor stuff
    returnHTML = returnHTML + '<TR><TD><B>Hypervisor:</B></TD><TD>'
    returnHTML = returnHTML + virtualization
    returnHTML = returnHTML + '</TD><TD><B>Identity:</B></TD><TD>'
    returnHTML = returnHTML + vmIdentity
    returnHTML = returnHTML + '</TD></TR>\n'
    
  #kernel Version and Supportconfig version
  returnHTML = returnHTML + '<TR><TD><B>Kernel Version:</B></TD><TD>'
  returnHTML = returnHTML + kernelVersion
  returnHTML = returnHTML + '</TD><TD><B>Supportconfig Version:</B></TD><TD>'
  returnHTML = returnHTML + supportconfigVersion
  returnHTML = returnHTML + '</TD></TR>\n'
  returnHTML = returnHTML + '</TABLE>\n'
  returnHTML = returnHTML + '<HR />\n'
  return returnHTML



#take a look at the html
#once analyze is run you can use "view" to look at the data
#use: "view" or "view <path to html>"
def view(*arg):
  global HtmlOutputFile
  #if no path given. try to view the global html output file.
  if len(arg) == 0:
    try:
      
      #check path and see if output file is set
      if HtmlOutputFile == "":
	print >> sys.stderr, "Error: Cannot open output file. Have you run analyze yet?"
	return
      if os.path.isfile(HtmlOutputFile):
	#check that this is html
	if HtmlOutputFile.endswith(".htm") or HtmlOutputFile.endswith(".html"):
	  os.system("w3m " + HtmlOutputFile)
	else:
	  print >> sys.stderr, HtmlOutputFile + " is not a html file"
      else:
	print >> sys.stderr, HtmlOutputFile + " is not a file."
    except Exception:
      print >> sys.stderr, "Error: Cannot open output file. Have you run analyze yet?"
      
  #A path was given
  elif len(arg) == 1:
    try:
      #check the path
      if os.path.isfile(arg[0]):
	#check that this is html
	if arg[0].endswith(".htm") or arg[0].endswith(".html"):
	  os.system("w3m " + arg[0])
	else:
	  print >> sys.stderr, arg[0] + " is not a html file"
      else:
	print >> sys.stderr, arg[0] + " is not a file."
    except Exception:
      pass
    
  #....More then two arguments given. Nice :)
  else:
    print >> sys.stderr, "Please run \"help view\""
  
#run all patterns
#this is called by analyze.
#does not return anything; however, it does set results[]
def runPats(extractedSupportconfig):
  global results
  runEdir = False
  runFilr = False
  runGW = False
  runHA = False
  runOES = False
  runSamba = False
  SLE_SP = 0
  SLE_version = 0
  OES_SP = -1
  OES_version = -1
  #reset black list
  whatNotToRun = []
  results = []
  
  #black list anything that does not apply to the system
  
  #open rpm.txt
  rpmFile = open(extractedSupportconfig + "rpm.txt")
  RPMs = rpmFile.readlines()
  rpmFile.close()
  
  #open basic-environment
  #find Sles verson
  basicEnv = open(extractedSupportconfig + "basic-environment.txt")
  basicEnvLines = basicEnv.readlines()
  for lineNumber in range(0, len(basicEnvLines)):
    if "# /etc/SuSE-release" in basicEnvLines[lineNumber] :
      SLE_version = basicEnvLines[lineNumber + 2].split("=")[1].strip()
      SLE_SP = basicEnvLines[lineNumber + 3].split("=")[1].strip()
      
  #Check if various products are on system
  for line in RPMs:
    if "heartbeat" in line:
      runHA = True
    if "oes" in line:
      runOES = True
    if "edirectory" in line:
      runEdir = True
    if "groupwise" in line:
      runGW = True
    if "filr" in line:
      runFilr = True
    if line.startswith("samba"):
      runSamba = True
      
  #If we have OES what verson and what patters should we run
  #OES stuff:
  if runOES:
    for lineNumber in range(0, len(basicEnvLines)):
      if "# /etc/novell-release" in basicEnvLines[lineNumber] :
	OES_version = basicEnvLines[lineNumber + 2].split("=")[1].strip().split(".")[0]
	OES_SP = basicEnvLines[lineNumber + 3].split("=")[1].strip()
    #blacklist all OES patterns that are not for the OES version
    #for all sles versions
    for folder in os.walk(patDir + "OES"):
      #trim file name down to just the OES verson
      fileName = folder[0].split("/")[-1]
      #remove parent directory
      if fileName == "OES":
	continue
      #check that the verson name maches
      if "oes" + OES_version not in fileName and fileName != "all":
	whatNotToRun.append(fileName)
      else:
	if "oes" + OES_version + "sp" + OES_SP not in fileName and "oes" + OES_version + "all" not in fileName and fileName != "all":
	  whatNotToRun.append(fileName)
  #clean up open files
  basicEnv.close()
  
  #if we don't have product X installed... black list it
  print "System Definition:"
  if runHA:
    print "HA ",
  else:
    whatNotToRun.append("HAE")
  if runOES:
    print "OES ",
  else:
    whatNotToRun.append("OES")
  if runEdir:
    print "edir ",
  else:
    whatNotToRun.append("eDirectory")
  if runGW:
    print "GW ",
  else:
    whatNotToRun.append("GroupWise")
  if runFilr:
    print "filr ",
  else:
    whatNotToRun.append("Filr")
  if runSamba:
    print "samba ",
  else:
    whatNotToRun.append("Samba")
    
  print "\nSLES " + SLE_version + " SP" + SLE_SP
  if runOES:
    print "OES " + OES_version + " SP" + OES_SP
  
  #blacklist all sles patterns that are not for the SLES version
  #for all sles versions
  for folder in os.walk(patDir + "SLE"):
    #trim file name down to just the sles verson
    fileName = folder[0].split("/")[-1]
    #remove parent directory
    if fileName == "SLE":
      continue
    #check that the verson name maches
    if "sle" + SLE_version not in fileName and fileName != "all":
      whatNotToRun.append(fileName)
    else:
      if "sle" + SLE_version + "sp" + SLE_SP not in fileName and "sle" + SLE_version + "all" not in fileName and fileName != "all":
	whatNotToRun.append(fileName)

  
  
  #for all patterns in patDir.. Yes it does this recursively. :P
  for root, subFolders, files in os.walk(patDir):
    #exclued any black listed folders
    for remove in whatNotToRun:
      if remove in subFolders:
	subFolders.remove(remove)
    #exclude lib folder
    if 'lib' in subFolders:
      subFolders.remove('lib')
    for file in files:
      file = os.path.join(root, file)
      #run pattern.. or try to anyway.
      try:
	p = subprocess.Popen([file, '-p', extractedSupportconfig], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	out, error = p.communicate()
	
	#call parseOutput to see if output was expected
	if not parseOutput(out, error):
	  print >> sys.stderr, "Error in: " + files
	  print >> sys.stderr, "------------------"
	  print >> sys.stderr, error
	  print >> sys.stderr, "------------------"
	else:
	  #print the ........'s
	  sys.stdout.write('.')
	  sys.stdout.flush()
      except Exception:
	print >> sys.stderr, "\nError executing: " + file
  #make output look nice
  print


#find all class Names in results
#does not return anything
#side effect: set "knownClasses"
def getClasses():
  global knownClasses
  global results
  #reset knownClasses
  knownClasses = []
  for i in range(len(results)):
    if not (results[i][0].split("=")[1] in knownClasses):
      knownClasses.append(results[i][0].split("=")[1])

  
  
#create the html code. :)
#called by analyze
#must be run after runPats
def getHtml(OutPutFile, archivePath):
  global knownClasses
  global results
  global HTML
  
  #get known classes
  getClasses()
  
  
  #reset  stuff
  Main_Link = ""
  links = ""
  HTML = ""
  
  
  #html top bit:
  HTML = HTML +  "<!DOCTYPE html>" + "\n"
  HTML = HTML +  "<HTML>" + "\n"
  HTML = HTML +  "<HEAD>" + "\n"
  HTML = HTML +  "<TITLE>SCA Report for tfg-fs-2</TITLE>" + "\n"
  HTML = HTML +  "<STYLE TYPE=\"text/css\">" + "\n"
  HTML = HTML +  "   a {text-decoration: none}	/* no underlined links */" + "\n"
  HTML = HTML +  "   a:link {color:#0000FF;}	/* unvisited link */" + "\n"
  HTML = HTML +  "   a:visited {color:#0000FF;}	/* visited link */" + "\n"
  HTML = HTML +  "</STYLE>" + "\n"
  
  
  #html script...
  script = "<SCRIPT>\n\
  function toggle(className)\n\
  {\n\
  className = className.replace(/ /g,\".\");\n\
  var elements = document.querySelectorAll(\".\" + className); for(var i=0; i<elements.length; i++)\n\
  {\n\
    if( elements[i].style.display=='none' )\n\
      {\n\
	elements[i].style.display = '';\n\
      }\n\
      else\n\
      {\n\
	elements[i].style.display = 'none';\n\
      }\n\
  }\n\
  }\n\
</SCRIPT>"

  #add stuff to html.. :)
  HTML = HTML +  script + "\n"
  HTML = HTML +  "</HEAD>" + "\n"
  
  #get header html
  HTML = HTML +  "<BODY BGPROPERTIES=FIXED BGCOLOR=\"#FFFFFF\" TEXT=\"#000000\">" + "\n"
  HTML = HTML + getHeader(archivePath, OutPutFile)
  
  #Critical table
  HTML = HTML +  '<H2>Conditions Evaluated as Critical<A NAME="Critical"></A></H2>' + "\n"
  HTML = HTML +  '<TABLE STYLE="border:3px solid black;border-collapse:collapse;" WIDTH="100%" CELLPADDING="2">' + "\n"
  HTML = HTML +  '<TR COLOR="#000000"><TH BGCOLOR="#FF0000"></TH><TH BGCOLOR="#EEEEEE" COLSPAN="3">Category</TH><TH>Message</TH><TH>Solutions</TH><TH BGCOLOR="#FF0000"></TH></TR>' + "\n"
  HTML = HTML + getTableHtml(4)
  HTML = HTML +  "</TABLE>"  + "\n"
  
  #Warning table
  HTML = HTML + '<H2>Conditions Evaluated as Warning<A NAME="Warning"></A></H2>' + "\n"
  HTML = HTML + '<TABLE STYLE="border:3px solid black;border-collapse:collapse;" WIDTH="100%" CELLPADDING="2">' + "\n"
  HTML = HTML + '<TR COLOR="#000000"><TH BGCOLOR="#FFFF00"></TH><TH BGCOLOR="#EEEEEE" COLSPAN="3">Category</TH><TH>Message</TH><TH>Solutions</TH><TH BGCOLOR="#FFFF00"></TH></TR>' + "\n"
  HTML = HTML + getTableHtml(3)
  HTML = HTML +  "</TABLE>"  + "\n"
  
  #Recommended table
  HTML = HTML + '<H2>Conditions Evaluated as Recommended<A NAME="Recommended"></A></H2>' + "\n"
  HTML = HTML + '<TABLE STYLE="border:3px solid black;border-collapse:collapse;" WIDTH="100%" CELLPADDING="2">' + "\n"
  HTML = HTML + '<TR COLOR="#000000"><TH BGCOLOR="#1975FF"></TH><TH BGCOLOR="#EEEEEE" COLSPAN="3">Category</TH><TH>Message</TH><TH>Solutions</TH><TH BGCOLOR="#1975FF"></TH></TR>' + "\n"
  HTML = HTML + getTableHtml(1)
  HTML = HTML +  "</TABLE>"  + "\n"
  
  #Success table
  HTML = HTML + '<H2>Conditions Evaluated as Success<A NAME="Success"></A></H2>' + "\n"
  HTML = HTML + '<TABLE STYLE="border:3px solid black;border-collapse:collapse;" WIDTH="100%" CELLPADDING="2">' + "\n"
  HTML = HTML + '<TR COLOR="#000000"><TH BGCOLOR="#00FF00"></TH><TH BGCOLOR="#EEEEEE" COLSPAN="3">Category</TH><TH>Message</TH><TH>Solutions</TH><TH BGCOLOR="#00FF00"></TH></TR>' + "\n"
  HTML = HTML + getTableHtml(0)
  HTML = HTML +  "</TABLE>"  + "\n"
  
  #HTML end stuff
  HTML = HTML + "</BODY>" + "\n"
  HTML = HTML + "</HTML>" + "\n"
  
  #write HTML to the output file
  fh = open(OutPutFile, "w")
  fh.write(HTML)
  fh.close()
 
#takes a status(critical (4), warning (3), etc) and returns the corresponding table... in html
def getTableHtml(val):
  #reset number of hits. ( a hit in this case is a result that matches "val")
  numHits = 0
  #set the color.
  if val == 4:
    #red (critical)
    color = "FF0000"
  elif val == 3:
    #yellow (warning)
    color = "FFFF00"
  elif val == 1:
    #blue.. ish (recommended)
    color = "1975FF"
  elif val == 0:
    #green (success)
    color ="00FF00"
  else:
    #fallback (gray)
    color = "222222"
   

  returnString = ""
  tmpReturn = ""
  
  #sort by known classes
  for Class in knownClasses:
    numHits = 0
    tmpReturn = ""
    #for all results
    for i in range(len(results)):
      #for results of a pattern
      if results[i][0].split("=")[1] == Class and int(results[i][5].split("=")[1]) == val:
	numHits = numHits + 1
	#find main link
	Main_Link = ""
	for j in range(len(results[i])):
	  #if main link
	  if results[i][j].split('=')[0] == results[i][4].split("=")[1]:
	    
	    #remove the stuff before the first "="
	    tmp = results[i][j].split('=')
	    del tmp[0]
	    for LinkPart in tmp:
	      Main_Link = Main_Link + "=" + LinkPart
	    Main_Link = Main_Link.strip("=")
	    #clean up the "=" leftover
	    link_id = results[i][j].split('=')[0]
	    
	#find the rest of the links:
	links = ""
	linkUrl = ""
	#for all links
	for link in range(7, len(results[i])):
	  linkUrl = ""
	  #remove the stuff before the first "="
	  tmp2 = results[i][link].split("=")
	  linkName = tmp2[0].split("_")[-1]
	  del tmp2[0]
	  for LinkPart in tmp2:
	    linkUrl = linkUrl + "=" + LinkPart
	  #clean up the "=" leftover
	  linkUrl = linkUrl.strip("=")
	  
	  #put it in html form
	  links = links + '<A HREF="' + linkUrl + '" TARGET="_blank">' + linkName + " " + '</A>'
	tmpReturn = tmpReturn + ('<TR STYLE="border:1px solid black; background: #FFFFFF; display:none;" CLASS="'\
	  + Class + \
	    '"><TD BGCOLOR="#'\
	  + color +\
	    '" WIDTH="2%">&nbsp;</TD><TD BGCOLOR="#EEEEEE" WIDTH="6%">'\
	  + results[i][0].split("=")[1] + \
	  '</TD><TD BGCOLOR="#EEEEEE" WIDTH="5%">'\
	  + results[i][1].split("=")[1] + \
	  '</TD><TD BGCOLOR="#EEEEEE" WIDTH="5%">'\
	  + results[i][2].split("=")[1] +\
	  '</TD><TD><A HREF="'\
	  + Main_Link + \
	  '" TARGET="_blank">'\
	  + results[i][6].split("=")[1] +\
	   '</A>&nbsp;&nbsp;<A HREF="https://code.google.com/p/server-diagnostic-patterns/source/browse/trunk/patterns/'
	  +results[i][0].split("=")[1] +\
	   '/all/' \
	  + results[i][3].split("=")[1] +\
	       '" TARGET="_blank">&nbsp;</A></TD><TD WIDTH="8%">'\
	  + links +\
	       '&nbsp;&nbsp;</TD><TD BGCOLOR="#'\
	  + color + \
	       '" WIDTH="2%">&nbsp;</TD></TR>'  + "\n")
	     
    #collapse tags
    if numHits > 0:
      tmpReturn = ('<TR STYLE="border:1px solid black;color: #0000FF; background: #FFCC99; font-size:80%; font-weight:normal"><TD BGCOLOR="#'\
      + color +\
      '" WIDTH="2%">&nbsp;</TD><TD BGCOLOR="#FFCC99" WIDTH="6%"><A ID="NewClass" TITLE="Click to Expand/Collapse" HREF="#" onClick="toggle(\''\
      + Class +\
      '\');return false;">'\
      + Class +\
      '</A></TD><TD BGCOLOR="#FFCC99" WIDTH="5%">&nbsp;</TD><TD BGCOLOR="#FFCC99" WIDTH="5%">&nbsp;</TD><TD><A ID="NewClass" TITLE="Click to Expand/Collapse" HREF="#" onClick="toggle(\''\
      + Class +\
      '\');return false;">'\
      + str(numHits) + " " +  Class + " Message(s)" +\
      '</A></TD><TD WIDTH="8%">&nbsp;</TD><TD BGCOLOR="#'\
      + color +\
      '" WIDTH="2%">&nbsp;</TD></TR>'\
      + "\n" +tmpReturn)
      returnString = returnString + tmpReturn
  #well that was fun... return
  return(returnString)
  

#check output. If output is good add it to results
def parseOutput(out, error):
  global results
  #if no errors
  if error == "":
    output = out.strip().split("|")
    #if overall outcome of pattern was valid
    if int(output[5].split("=")[1]) >= 0 and int(output[5].split("=")[1]) < 5:
      results.append(output)
    return True
  else:
    return False
    
#analyze server or supportconfig
def analyze(*arg):
  global HtmlOutputFile
  global outputFileGiven
  global KeepArchive
  #reset stuff
  timeStamp = time.time()
  remoteSupportconfigName = ""
  remoteSupportconfigPath = ""
  extractedSupportconfig = ""
  supportconfigPath = ""
  extractedPath = ""
  deleteArchive = False
  isIP = False
  host = "None"
  if not outputFileGiven:
    HtmlOutputFile = ""
  cleanUp = True
  
  #if we want to run and analyze a supportconfig
  if len(arg) == 0:
    print "running supportconfig"
    #run supportconfig
    try:
      p = subprocess.Popen(['/sbin/supportconfig', '-b'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      #remove archive
      deleteArchive = True
    #if we cannot run supportconfig
    except Exception:
      print >> sys.stderr, "Error: Cannot run supportconfig. Please see http://www.novell.com/communities/node/2332/supportconfig-linux#install"
      return
    condition = True
    alloutput = ""
    lineNum = 0
    supportconfigPath = ""
    
    #this acts like a do-while. I love do-while :)
    #print output of the subprocess (supportconfig)
    #--DO--
    while condition:
      out = p.stdout.read(1)
      if out != '':
	  sys.stdout.write(out)
	  alloutput = alloutput + out
	  sys.stdout.flush()
	  if out == "\n":
	    lineNum = lineNum + 1
	    
    #--WHILE--
      condition = not bool(out == "" and p.poll() != None)
      
    #find tar ball
    for line in alloutput.split("\n"):
      if "Log file tar ball:" in line:
	supportconfigPath = line.split(":")[1].strip()
	
  #if a path was given. analyze given file/folder
  elif len(arg) == 1:
    #test if we have an IP
    try:
      socket.inet_aton(arg[0])
      host = arg[0]
      print "Received reply from server"
      isIP = True
    except socket.error:
      try:
	host = socket.gethostbyname(arg[0].strip("\n"))
	print "Received reply from server"
	isIP = True
      except:
	if isIP:
	  print >> sys.stderr, "Error: unable to reach server"
	  return

    if host == "None":
      #Not an IP. Lets hope it is a PATH
      supportconfigPath = arg[0]
    else:
      #we have an IP
      print "Please enter your credentials for " + arg[0]
      remoteSupportconfigName = timeStamp
      remoteSupportconfigPath = "/var/log"
      
      #print "lets take a look at that IP "
      try:
	#run ssh root@host "supportconfig -R /var/log -B <timeStamp>; echo -n \~; cat <path to new supportconfig
	#aka: run supportconfig then send the output back.
	p = subprocess.Popen(['ssh', "root@" + host, 'supportconfig -R ' + remoteSupportconfigPath + ' -B ' + str(remoteSupportconfigName) + ";echo -n \\~; cat " + remoteSupportconfigPath + "/nts_" + str(remoteSupportconfigName) + ".tbz" + "; rm " + remoteSupportconfigPath + "/nts_" + str(remoteSupportconfigName) + ".tbz*"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	#create a local verson of the supportconfig output
	localSupportconfig =  open(remoteSupportconfigPath + "/nts_" + str(remoteSupportconfigName) + "_local.tbz", 'w')
	#remove local archive
	deleteArchive = True
	condition = True
	endOfSupportcofing = False

	#this acts like a do-while. I love do-while :)
	#print output of the subprocess (the long ssh command)
	#--DO--
	while condition:
	  out = p.stdout.read(1)
	  #if the end of supportconfig output... start saving output
	  if(endOfSupportcofing):
	    #save to local supportconfig
	    localSupportconfig.write(out)
	  elif out != '':
	      #print non binary data to stdout
	      sys.stdout.write(out)
	      sys.stdout.flush()
	  #if we are ate the end of the file output
	  if out == "~":
	    endOfSupportcofing = True
		
	#--WHILE--
	  condition = not bool(out == "" and p.poll() != None)
	#close the local copy of the remote supportconfig.
	localSupportconfig.close()
	supportconfigPath = remoteSupportconfigPath + "/nts_" + str(remoteSupportconfigName) + "_local.tbz"
      except Exception:
	print >> sys.stderr, "Error: Cannot run supportconfig on " + arg[0] + "."
	return


      
  else:
    #too many arguments
    print >> sys.stderr, "please run: \"help analyze\""
    
  #if supportconfig not extract. Extract supportconfig
  if os.path.isfile(supportconfigPath):
    #extract file
    #find the extracting path
    print "Extracting " + supportconfigPath
    tmp = supportconfigPath.split('/')
    del tmp[-1]
    extractedPath = '/'.join(tmp) 
    
    #set TarFile and find the path of the soon to be extracted supportconfig
    try:
      TarFile = tarfile.open(supportconfigPath)
      extractedSupportconfig = extractedPath + "/" + TarFile.getnames()[0].split("/")[-2] + "/"
      if outputFileGiven:
	if os.path.isdir(HtmlOutputFile):
	  HtmlOutputFile = HtmlOutputFile + "/" + TarFile.getnames()[0].split("/")[-2] + ".html"
      else:
	HtmlOutputFile = extractedPath + "/" + TarFile.getnames()[0].split("/")[-2] + ".html"
      print "Extracted to " + extractedSupportconfig 
      TarFile.extractall(path=extractedPath, members=None)
    except tarfile.ReadError:
      #cannot open the tar file
      print >> sys.stderr, "Cannot open " + supportconfigPath
      return
  #if given an extracted supportconfig
  elif os.path.isdir(supportconfigPath):
    extractedSupportconfig = supportconfigPath
    if outputFileGiven:
      if os.path.isdir(HtmlOutputFile):
	HtmlOutputFile = HtmlOutputFile + "/" + extractedSupportconfig.strip("/").split("/")[-1] + ".html"
    else:
      HtmlOutputFile = extractedSupportconfig + extractedSupportconfig.strip("/").split("/")[-1] + ".html"
    #we don't want to delete something we did not create.
    cleanUp = False
  #lets check that this is a supportconfig...
  if not os.path.isfile(extractedSupportconfig + "/basic-environment.txt"):
    #not a supportconfig. quit out
    print >> sys.stderr, "Error: " + extractedSupportconfig + " does not look like a supportconfig"
    return
  
  #At this point we should have a extracted supportconfig 
  #run pats on supportconfig
  print "Running patterns"
  runPats(extractedSupportconfig)
  getHtml(HtmlOutputFile, extractedSupportconfig)
  print "output file: " + HtmlOutputFile

  #if command was run via console run view
  if command != "exit":
    print "run \"view\" or open " + HtmlOutputFile + " to see results"
    view()

  #clean up
  if cleanUp:
    shutil.rmtree(extractedSupportconfig)
  if deleteArchive and not KeepArchive:
    os.remove(supportconfigPath)
      
def help(*arg):
  
  #help run without any command name given. print available commands (if a help page is available for a command print first line of help page)
  if len(arg) == 0:
    printed = False
    print "Available Commands:\n"
    for i in range(0, len(COMMANDS)):
      printed = False
      for e in COMMANDS_HELP:
	if e.startswith(COMMANDS[i]):
	  print e.split("\n")[0]
	  printed = True
	  break
      if not printed:
	print COMMANDS[i]
    print "\nRun \"help <command name>\" for more help\n"
    
  #help was run with a command given
  if len(arg) == 1:
    #if valid command was given
    if arg[0] in COMMANDS:
      #find the help page
      for i in COMMANDS_HELP:
	if i.split(":")[0] == arg[0]:
	  #print i (without the command name)
	  print "\n" + i[len(arg[0])+2:] + "\n"
	  return
      print >> sys.stderr, "Error: No help page for command \"" + arg[0] + "\""
    else:
      print >> sys.stderr, "Error: " + arg[0] + " is not a command"

#read in arguments
arg = sys.argv[1:]
analyzeServer = False
analyzeFile = ""
autoExit = False
for x in range(0, len(arg)):
  #take a -h: scatool -h
  if arg[x].startswith("-") and "h" in arg[x]:
    autoExit = True
    print "       -h     Displays this screen.\n\
       -a /path/to/supportconfig/tarball\n\
              Analyze the tarred compressed tar ball spacified with the -a paramenter.\n\
       -o /path/to/output/file/\n\
              The  HTML report file will be written to this directory. If -o is not specified, the output file will be in the same location as the supportconfig file or directory.\n\
       -k     Keep archive files\n\
       -c     Enter SCAtool console"
  #take a -k: (keep archive files)
  if arg[x].startswith("-") and "k" in arg[x]:
    KeepArchive = True

  #take a -o: scatool -a <path to supportconfig> -o <path to output file>
  if arg[x].startswith("-") and "o" in arg[x]:
    if len(arg) > x + 1:
      outputFileGiven = True
      HtmlOutputFile = arg[x + 1]
    else:
      print >> sys.stderr, "Invalid startup arguments"
      sys.exit()
  # take a -a: scatool -a <path to supportconfig>
  if arg[x].startswith("-") and "a" in arg[x]:
    analyzeServer = True
    autoExit = True
    #run analyze and exit
    if (len(arg) >= 2) and not arg[x + 1].startswith("-"):
      analyzeFile = arg[x + 1]
    elif (len(arg) == 1) or arg[x + 1].startswith("-"):
      analyzeServer = True
    else:
      print >> sys.stderr, "Invalid startup arguments"
  
  
  #take a -c: (open console)
  if arg[x].startswith("-") and "c" in arg[x]:
    autoExit = False
    
#auto exit.. or not:
#if autoExit and analyzeServer:
if autoExit:
  command = "exit"
#clean off any "/" from the end of a path name:
if HtmlOutputFile.endswith("/"):
  HtmlOutputFile = HtmlOutputFile[:-1]
if analyzeServer == True and analyzeFile != "":
  analyze(analyzeFile)
elif analyzeServer == True and analyzeFile == "":
  analyze()

#get user input:
readline.set_completer_delims(' \t\n;')
readline.parse_and_bind("tab: complete")
#tell readline to use tab complete stuff
readline.set_completer(tabSystem)
#main command line input loop
while command != "exit":
  #get command (this will use the auto-complete I created.)
  command = raw_input("^^~ ")
  #run the command: <argument1>(<argument2>): example "analyze /home/support/nts_123456.tbz" will call "analyze(/home/support/nts_123456.tbz)"
  if len(command.split(" ")) > 1:
    if command.split(" ")[0] in COMMANDS:
      eval(command.split(" ")[0] + "(\"" + command.split(" ")[1] + "\")")
    else:
      print >> sys.stderr, command.split(" ")[0] + " command not found, please run \"help\""
  else:
    if command in COMMANDS:
      eval(command + "()")
    else:
      print >> sys.stderr, command + " command not found, please run \"help\""