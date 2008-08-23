#!/usr/bin/python

#	Copyright (c) 2008 Matthew Ball
# 
#	Permission is hereby granted, free of charge, to any person
#	obtaining a copy of this software and associated documentation
#	files (the "Software"), to deal in the Software without
#	restriction, including without limitation the rights to use,
#	copy, modify, merge, publish, distribute, sublicense, and/or sell
#	copies of the Software, and to permit persons to whom the
#	Software is furnished to do so, subject to the following
#	conditions:
# 
#	The above copyright notice and this permission notice shall be
#	included in all copies or substantial portions of the Software.
#
#	THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#	EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
#	OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
#	NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
#	HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
#	WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#	FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
#	OTHER DEALINGS IN THE SOFTWARE.

import getopt, sys, os, fnmatch
from xml.dom import minidom

def usage ():
	sys.stderr.write('''\
	Usage: doxyclean.py [-h] [-i indir] [-o outdir]

	Options:	-h			Converts the cleaned XML to XHTML styled similarly to Apple's documentation
				-i indir	Specifies the directory with XML files generated by Doxygen
				-o outdir	Specifies the directory to place the cleaned XML files

	Converts the XML files generated by Doxygen to 
	be more easily-read and more catered to Objective-C.
''')
	sys.exit(1)
	
def _mkdir(newdir):
    """works the way a good mkdir should :)
        - already exists, silently complete
        - regular file in the way, raise an exception
        - parent directory(ies) does not exist, make them as well
    """
    if os.path.isdir(newdir):
        pass
    elif os.path.isfile(newdir):
        raise OSError("a file with the same name as the desired " \
                      "dir, '%s', already exists." % newdir)
    else:
        head, tail = os.path.split(newdir)
        if head and not os.path.isdir(head):
            _mkdir(head)

        if tail:
            os.mkdir(newdir)

def fileIsDocumented(filePath):
	# Check if the object is documented
	originaldoc = minidom.parse(filePath)
	briefList = originaldoc.getElementsByTagName('briefdescription')
	detailList = originaldoc.getElementsByTagName('detaileddescription')
	
	for briefItem in briefList:
		paraList = briefItem.getElementsByTagName('para')
		if len(paraList) > 0:
			return 1
			
	for detailItem in detailList:
		paraList = detailItem.getElementsByTagName('para')
		if len(paraList) > 0:
			return 1

	return 0

def cleanXML(fileName, inputDirectory, outputDirectory):
	_mkdir(outputDirectory)
	
	# Perform the XSL Transform
	inputPath = inputDirectory + '/' + fileName
	tempPath = outputDirectory + '/' + fileName
	stylesheetPath = sys.path[0] + '/object.xslt'
	os.system('xsltproc -o "' + tempPath + '" "' + stylesheetPath + '" "' + inputPath + '"')

	# We will get values from the xml file
	xmldoc = minidom.parse(tempPath)

	# Get the object name
	nameList = xmldoc.getElementsByTagName('name')
	objectName = nameList[0].firstChild.data

	# Get the object type
	objectList = xmldoc.getElementsByTagName('object')
	objectType = objectList[0].attributes['kind'].value

	if objectType == 'class':
		finalPath = outputDirectory + '/Classes'
	elif objectType == 'category':
		finalPath = outputDirectory + '/Categories'

		# Set the filename to something more URL-friendly
		objectName = objectName.replace('(', '_').replace(')', '')
	elif objectType == 'protocol':
		finalPath = outputDirectory + '/Protocols'
		
	_mkdir(finalPath)

	finalPath += '/' + objectName + '.xml'

	os.system('mv "' + tempPath + '" "' + finalPath + '"')

	return (objectName, objectType)
	
def convertToXHTML(objectName, objectType, inputDirectory, outputDirectory):
	# Set the path for different kinds of objects
	classXHTMLPath = xhtmlOutputDirectory + '/Classes'
	categoryXHTMLPath = xhtmlOutputDirectory + '/Categories'
	protocolXHTMLPath = xhtmlOutputDirectory + '/Protocols'

	if objectType == 'class':
		inputDirectory += '/Classes'
		outputDirectory += '/Classes'
	elif objectType == 'category':
		inputDirectory += '/Categories'
		outputDirectory += '/Categories'
	elif objectType == 'protocol':
		inputDirectory += '/Protocols'
		outputDirectory += '/Protocols'
	_mkdir(outputDirectory)

	inputPath = inputDirectory + '/' + objectName + '.xml'
	outputPath = outputDirectory + '/' + objectName + '.html'

	stylesheetPath = sys.path[0] + '/object2xhtml.xslt'
	os.system('xsltproc -o "' + outputPath + '" "' + stylesheetPath + '" "' + inputPath + '"')
	
def createIndexXML(inputDirectory):
	# Create the index xml file
	outputPath = inputDirectory + '/index.xml'
	indexXML = minidom.Document()
	
	projectElement = indexXML.createElement("project")
	indexXML.appendChild(projectElement)
	
	# Define the various subdirectories
	classPath = inputDirectory + '/Classes'
	categoryPath = inputDirectory + '/Categories'
	protocolPath = inputDirectory + '/Protocols'
	
	# Get each class
	if os.path.exists(classPath):
		for fileName in os.listdir(classPath):
			classFile = minidom.parse(classPath + '/' + fileName)
		
			# Get the object name
			nameList = classFile.getElementsByTagName('name')
			objectName = nameList[0].firstChild.data
		
			# Get the object type
			objectList = classFile.getElementsByTagName('object')
			objectType = objectList[0].attributes['kind'].value
		
			# Create a <object> element
			objectElement = indexXML.createElement("object")
			objectElement.setAttribute("kind", "class")
			projectElement.appendChild(objectElement)
		
			# Create the <name> element
			nameElement = indexXML.createElement("name")
			objectElement.appendChild(nameElement)
			nameText = indexXML.createTextNode(objectName)
			nameElement.appendChild(nameText)
		
	# Get each category
	if os.path.exists(categoryPath):
		for fileName in os.listdir(categoryPath):
			categoryFile = minidom.parse(categoryPath + '/' + fileName)

			# Get the object name
			nameList = categoryFile.getElementsByTagName('name')
			objectName = nameList[0].firstChild.data

			# Get the object type
			objectList = categoryFile.getElementsByTagName('object')
			objectType = objectList[0].attributes['kind'].value

			# Create a <object> element
			objectElement = indexXML.createElement("object")
			objectElement.setAttribute("kind", "category")
			projectElement.appendChild(objectElement)

			# Create the <name> element
			nameElement = indexXML.createElement("name")
			objectElement.appendChild(nameElement)
			nameText = indexXML.createTextNode(objectName)
			nameElement.appendChild(nameText)
			
	# Get each protocol
	if os.path.exists(protocolPath):
		for fileName in os.listdir(protocolPath):
			protocolFile = minidom.parse(protocolPath + '/' + fileName)

			# Get the object name
			nameList = protocolFile.getElementsByTagName('name')
			objectName = nameList[0].firstChild.data

			# Get the object type
			objectList = protocolFile.getElementsByTagName('object')
			objectType = objectList[0].attributes['kind'].value

			# Create a <object> element
			objectElement = indexXML.createElement("object")
			objectElement.setAttribute("kind", "protocol")
			projectElement.appendChild(objectElement)

			# Create the <name> element
			nameElement = indexXML.createElement("name")
			objectElement.appendChild(nameElement)
			nameText = indexXML.createTextNode(objectName)
			nameElement.appendChild(nameText)
	
	# Write the index xml file
	f = open(outputPath, 'w')
	indexXML.writexml(f, "", "\t", "\n")
	f.close()
	
	return outputPath
	
def convertIndexToXHTML(xmlPath, outputDirectory):
	# Copy the CSS files over to the new path
	cssPath = sys.path[0] + '/css'
	os.system('cp -R "' + cssPath + '" "' + outputDirectory + '"')
	
	# Create the index html file
	stylesheetPath = sys.path[0] + '/index2xhtml.xslt'
	outputPath = outputDirectory + '/index.html'
	os.system('xsltproc -o "' + outputPath + '" "' + stylesheetPath + '" "' + xmlPath + '"')
	
	
if __name__ == '__main__':	
	# If no arguments are given, show the usage message
	if len(sys.argv) == 1:
		usage()
		sys.exit(0)
	
	# Set the default directories
	inputDirectory = os.getcwd()
	outputDirectory = os.getcwd()
	
	shouldConvertToXHTML = 0
	
	opts, args = getopt.getopt(sys.argv[1:], 'i:o:h')
	for option, value in opts:
		if option[1] == 'i':
			inputDirectory = value
		elif option[1] == 'o':
			outputDirectory = value
		elif option[1] == 'h':
			shouldConvertToXHTML = 1
	
	if not os.path.exists(inputDirectory):
		print 'ERROR: Input path does not exist: ' + inputDirectory
		sys.exit(1)
		
	_mkdir(outputDirectory)
		
	xmlOutputDirectory = outputDirectory + "/DoxyCleaned/xml"
	xhtmlOutputDirectory = outputDirectory + '/DoxyCleaned/xhtml'
		
	for fileName in os.listdir(inputDirectory):
		if fnmatch.fnmatch(fileName, 'interface_*.xml') or fnmatch.fnmatch(fileName, 'protocol_*.xml'):
			
			shouldConvert = fileIsDocumented(inputDirectory + '/' + fileName)

			if shouldConvert:
				(objectName, objectType) = cleanXML(fileName, inputDirectory, xmlOutputDirectory)
				
				if shouldConvertToXHTML:
					convertToXHTML(objectName, objectType, xmlOutputDirectory, xhtmlOutputDirectory)
	
	indexPath = createIndexXML(xmlOutputDirectory)

	if shouldConvertToXHTML:
		convertIndexToXHTML(indexPath, xhtmlOutputDirectory)