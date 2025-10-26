#!/usr/bin/env python3

import sys, string, os, re, time, shutil
from os import urandom
from random import choice
from configparser import ConfigParser
import argparse
import traceback

char_set = {'small': 'abcdefghijklmnopqrstuvwxyz',
             'nums': '0123456789',
             'big': 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
             'special': '!#&$*@'
            }

class IllegalArgumentException(Exception):

    def __init__(self, lineno, msg):
        self.lineno = lineno
        self.msg = msg

    def __str__(self):
        s='Exception at line number %d => %s' % (self.lineno, self.msg)
        return s

def check_prev_char(password, current_char_set):
    #Function to ensure that there are no consecutive UPPERCASE/lowercase/numbers/special-characters.

    index = len(password)
    if index == 0:
        return False
    else:
        prev_char = password[index - 1]
        if prev_char in current_char_set:
            return True
        else:
            return False            

def generate_pass(length):
    #Function to generate a password

    password = []

    while len(password) < length:
        key = choice(char_set.keys())
        a_char = urandom(1)
        if a_char in char_set[key]:
            if check_prev_char(password, char_set[key]):
                continue
            else:
                password.append(a_char)
    return ''.join(password)


def buildPhoneConfig(macTemplate, mac, name, extension, address, password):
	# build Polycom line key configuration file so single MAC address
    try:
        with open(macTemplate, "r") as f:
            contents = f.read()
    except:
            print ("unable to open file" + macTemplate)
            sys.exit()
                
    contents = contents.replace('@DisplayName@'
        ,name).replace('@Address@'
        ,address).replace('@Label@'
        ,extension).replace('@Password@',password)
    
    try:
        with open(mac, "w") as f:
            f.write(contents)

    except Exception as e:
        print("unable to write file " + mac)
        traceback.print_exc()
        sys.exit()
        
	
def buildVoiceMailConfig(extension, name, email):
	# Build extension voice mail configuration 
	return extension + "=>" + extension + "," + name + "," + email + "\n"

def buildSIPConfig(sipTemplate, mac, name, extension, address, voicemail, secret):
	# build sip extension configuration
    try:
        with open(sipTemplate,"r") as f:
            contents = f.read()

        return contents.replace('@DisplayName@'
            ,name).replace('@Address@',address).replace('@Label@'
            ,extension).replace('@voicemail.context@',voicemail).replace('@secret@',secret)
    except:
        print("unable to open file" + sipTemplate)
        sys.exit()



def buildDirectory(dirTemplate, extension, firstname, lastname):
	# Build Polycom extension default directory file entry
    try:
        with open(dirTemplate,"r") as f:
            contents = f.read()

        return contents.replace('@Firstname@'
        ,firstname).replace('@Lastname@'
        ,lastname).replace('@Label@',extension)

    except:
        print("unable to open file" + dirTemplate)
        sys.exit()


	
def buildiSymphony(iSymphonyTemplate, extension, firstname, lastname, mac, vmcontext):
	# Build iSymphony extension configuration	
    try:
        with open(iSymphonyTemplate,"r") as f:
            contents = f.read()
             
        return contents.replace('@Firstname@'
            ,firstname).replace('@Lastname@'
            ,lastname).replace('@Label@'
            ,extension).replace('@Address@'
            ,mac).replace('@vmcontext@',vmcontext)

    except:
        print("unable to open file" + iSymphonyTemplate)
        sys.exit()


def buildGlobals(extension, name, address):
	# Build extension & SIP channel global dialplan variable
	fixname = "".join(name.split())
	# print(address)
	
	return "m" + fixname  + "=" + extension + "\ns" + fixname + "=" + "SIP/" + address + "\n"  

def buildExtensionDial(name):
	# Build extension dialplan dial statment
	fixname = "".join(name.split())
	# print(fixname)
	return "exten => ${m" + fixname + "},1,Gosub(standardVM,${EXTEN},1(${s" + fixname  + "},${CONTEXT},${EXTEN}))\n"  + buildHint(fixname)
	
def buildHint(name):
	# Build Asterisk extenion hint dialplan statment
	return "exten => ${m" + name +"},hint,${" + name +"}" + "\n"  

def openFiles(filename, att):
	# Return config file handle.
    try:
        return  open(filename,att)
                
    except:
        print("unable to open file" + filename)
        sys.exit()

def checkPhoneFlag(flag):
	if (flag == "mac"): return 0
	return 1
	
def checkPhonePass(secret):
	if (len(secret) > 0): return 2
	return 0

def PhoneSipConfig(flag, p, line, secret, sip):
	#Checks if extension or MAC address are used for registration
	#and whether a registration password needs to be assigned to the endpoint
	#then passes the corresponding fields to the config line builder
	
	#print "Flag  is " + str(checkPhoneFlag(flag)) + "\n"
	#print "Password  is " + str(checkPhonePass(line)) + "\n"
	
	total = checkPhoneFlag(flag) + checkPhonePass(secret)
	
	#print "Total is " + str(total) + "\n"
	
	if (total == 0): #address no pass
		buildPhoneConfig(p['templates.dir'] + os.sep 
			+ p['custom.conf'],p['gen.dir'] 
			+ os.sep + line[3] + "-tauk.cfg"
			,line[0],line[2],line[3],"")
		
		sip.write(buildSIPConfig(p['templates.dir'] + os.sep
                		+ p['sip.user.conf'],line[3],line[0]
                		,line[2],line[3],p['voicemail.context'],secret))		
		
	elif (total == 1): #extension no pass
		buildPhoneConfig(p['templates.dir'] + os.sep 
			+ p['custom.conf'],p['gen.dir'] 
			+ os.sep + line[3] + "-tauk.cfg"
			,line[0],line[2],line[2],"")
		
		sip.write(buildSIPConfig(p['templates.dir'] + os.sep
                		+ p['sip.user.conf'],line[3],line[0]
                		,line[2],line[2],p['voicemail.context'],secret))
	
	elif (total == 2): #address & pass
		buildPhoneConfig(p['templates.dir'] + os.sep 
			+ p['custom.conf'],p['gen.dir'] 
			+ os.sep + line[3] + "-tauk.cfg"
			,line[0],line[2],line[3],secret)
		
		sip.write(buildSIPConfig(p['templates.dir'] + os.sep
                		+ p['sip.user.conf'],line[3],line[0]
                		,line[2],line[3],p['voicemail.context'],secret))
	
	else: #extension and pass
		buildPhoneConfig(p['templates.dir'] + os.sep 
			+ p['custom.conf'],p['gen.dir'] 
			+ os.sep + line[3] + "-tauk.cfg"
			,line[0],line[2],line[2],secret)
		
		sip.write(buildSIPConfig(p['templates.dir'] + os.sep
                		+ p['sip.user.conf'],line[3],line[0]
                		,line[2],line[2],p['voicemail.context'],secret))

def make_argparser():
    parser = argparse.ArgumentParser(description='Tool to generate Tauk Asterisk and Polycom phone configurations.  \
                                     Outputs files to gen directory specified in property file')
    
    parser.add_argument("properties", help="Property file name containing application configuration and templates")
    parser.add_argument("extensions", help="Extension File CSV Format: First Last Name, Email, Extension, MAC Address " \
                        "Example: John Smith,js@specailai.com,8186,0004F214B68B")
    
    parser.add_argument('--device', '-d', default='extension',
                    help="Device name either 'extension' or 'mac', defaults to extension")
    parser.add_argument('--password', '-p', action='store_true',
                        help='Generate device passwords.')


    return parser

def main():
	
    # parse args
    arg_parser = make_argparser()
    args = arg_parser.parse_args()

    # open config file and add default contents to dict
    config_parser = ConfigParser()
    config_parser.read(args.properties)
    p = {}
    for key, val in config_parser.items('default'):
        p[key] = val

    # clear gen directory
    if os.path.exists(p['gen.dir']):
        shutil.rmtree(p['gen.dir'])        
    os.mkdir(p['gen.dir'])

    # open extension provisioning spread sheet
    f = openFiles(args.extensions, "r")

    # open target  configuration files
    globalcontext = openFiles(p['gen.dir'] + os.sep 
        + p['global.var.file'],"w")

    extenscontext = openFiles(p['gen.dir'] + os.sep 
        + p['master.context.file'],"w")

    voicemail = openFiles(p['gen.dir'] + os.sep 
        + p['voicemail.conf'],"w")

    sip = openFiles(p['gen.dir'] + os.sep 
        + p['sip.user.conf'],"w")

    directory = openFiles(p['gen.dir'] + os.sep 
        + p['directory.file'],"w")
    directory.write(p['directory.header'] + "\n")

    isymphony = openFiles(p['gen.dir'] + os.sep 
        + p['isymphony.file'],"w")
        
	# loop through each extension in provisionning sheet and build out configurations
    while(1):
        line = f.readline()

        if not line: break
        if line != "\n":
            # strip whitespace and break string into list
            provline = line.lstrip().rstrip().split(',')

        # lower case MAC address
        provline[3] = provline[3].lower()

        #gen password if flag is set
        if args.password:
            secret = generate_pass(8)
        else:
            secret = ""			

        # Write tauk polycom phone config & sip configuration
        PhoneSipConfig(args.device,p,provline,secret,sip)

        #Write vars in global context
        if (args.device == "mac"):
            #MAC
            globalcontext.write(buildGlobals(provline[2]
                ,provline[0],provline[3]))
        else:
            #Exten
            globalcontext.write(buildGlobals(provline[2]
                ,provline[0],provline[2]))		

                #Write exten/hint in phone registration context
        extenscontext.write(buildExtensionDial(provline[0]))
                
                #Write voicemail configuration
        voicemail.write(buildVoiceMailConfig(provline[2]
            ,provline[0],provline[1]))
            
        #Write polycom directory file/iSymphony extensions file
        name = provline[0].split(' ')
        if (len(name) > 1):
            directory.write(buildDirectory(p['templates.dir'] + os.sep
                + p['directory.template'],provline[2],name[0],name[1]))
            
            if (args.device == "mac"):
                isymphony.write(buildiSymphony(p['templates.dir'] + os.sep
                    + p['isymphony.template'],provline[2],name[0],name[1],provline[3],p['voicemail.context']))
            else:
                isymphony.write(buildiSymphony(p['templates.dir'] + os.sep
                    + p['isymphony.template'],provline[2],name[0],name[1],provline[2],p['voicemail.context']))
                    
        else:
            directory.write(buildDirectory(p['templates.dir'] + os.sep
                + p['directory.template'],provline[2],provline[0],""))
            
            if (args.device == "mac"):
                isymphony.write(buildiSymphony(p['templates.dir'] + os.sep
                    + p['isymphony.template'],provline[2],name[0]," ",provline[3],p['voicemail.context']))
            else:
                isymphony.write(buildiSymphony(p['templates.dir'] + os.sep
                    + p['isymphony.template'],provline[2],name[0]," ",provline[2],p['voicemail.context']))
        
    directory.write(p['directory.footer'])
    directory.close()
    globalcontext.close()
    extenscontext.close()
    voicemail.close()
    sip.close()      
    f.close()

if __name__=="__main__":
       main()
