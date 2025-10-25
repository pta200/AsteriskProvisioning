#!/usr/local/bin/python
import sys, string, os, re, time, shutil
from os import urandom
from random import choice

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
                 
class Properties(object):
    """ A Python replacement for java.util.Properties """
    
    def __init__(self, props=None):

        # Note: We don't take a default properties object
        # as argument yet

        # Dictionary of properties.
        self._props = {}
        # Dictionary of properties with 'pristine' keys
        # This is used for dumping the properties to a file
        # using the 'store' method
        self._origprops = {}

        # Dictionary mapping keys from property
        # dictionary to pristine dictionary
        self._keymap = {}
        
        self.othercharre = re.compile(r'(?<!\\)(\s*\=)|(?<!\\)(\s*\:)')
        self.othercharre2 = re.compile(r'(\s*\=)|(\s*\:)')
        self.bspacere = re.compile(r'\\(?!\s$)')
        
    def __str__(self):
        s='{'
        for key,value in self._props.items():
            s = ''.join((s,key,'=',value,', '))

        s=''.join((s[:-2],'}'))
        return s

    def __parse(self, lines):
        """ Parse a list of lines and create
        an internal property dictionary """

        # Every line in the file must consist of either a comment
        # or a key-value pair. A key-value pair is a line consisting
        # of a key which is a combination of non-white space characters
        # The separator character between key-value pairs is a '=',
        # ':' or a whitespace character not including the newline.
        # If the '=' or ':' characters are found, in the line, even
        # keys containing whitespace chars are allowed.

        # A line with only a key according to the rules above is also
        # fine. In such case, the value is considered as the empty string.
        # In order to include characters '=' or ':' in a key or value,
        # they have to be properly escaped using the backslash character.

        # Some examples of valid key-value pairs:
        #
        # key     value
        # key=value
        # key:value
        # key     value1,value2,value3
        # key     value1,value2,value3 \
        #         value4, value5
        # key
        # This key= this value
        # key = value1 value2 value3
        
        # Any line that starts with a '#' is considerered a comment
        # and skipped. Also any trailing or preceding whitespaces
        # are removed from the key/value.
        
        # This is a line parser. It parses the
        # contents like by line.

        lineno=0
        i = iter(lines)

        for line in i:
            lineno += 1
            line = line.strip()
            # Skip null lines
            if not line: continue
            # Skip lines which are comments
            if line[0] == '#': continue
            # Some flags
            escaped=False
            # Position of first separation char
            sepidx = -1
            # A flag for performing wspace re check
            flag = 0
            # Check for valid space separation
            # First obtain the max index to which we
            # can search.
            m = self.othercharre.search(line)
            if m:
                first, last = m.span()
                start, end = 0, first
                flag = 1
                wspacere = re.compile(r'(?<![\\\=\:])(\s)')        
            else:
                if self.othercharre2.search(line):
                    # Check if either '=' or ':' is present
                    # in the line. If they are then it means
                    # they are preceded by a backslash.
                    
                    # This means, we need to modify the
                    # wspacere a bit, not to look for
                    # : or = characters.
                    wspacere = re.compile(r'(?<![\\])(\s)')        
                start, end = 0, len(line)
                
            m2 = wspacere.search(line, start, end)
            if m2:
                # print 'Space match=>',line
                # Means we need to split by space.
                first, last = m2.span()
                sepidx = first
            elif m:
                # print 'Other match=>',line
                # No matching wspace char found, need
                # to split by either '=' or ':'
                first, last = m.span()
                sepidx = last - 1
                # print line[sepidx]
                
                
            # If the last character is a backslash
            # it has to be preceded by a space in which
            # case the next line is read as part of the
            # same property
            while line[-1] == '\\':
                # Read next line
                nextline = i.next()
                nextline = nextline.strip()
                lineno += 1
                # This line will become part of the value
                line = line[:-1] + nextline

            # Now split to key,value according to separation char
            if sepidx != -1:
                key, value = line[:sepidx], line[sepidx+1:]
            else:
                key,value = line,''

            self.processPair(key, value)
            
    def processPair(self, key, value):
        """ Process a (key, value) pair """

        oldkey = key
        oldvalue = value
        
        # Create key intelligently
        keyparts = self.bspacere.split(key)
        # print keyparts

        strippable = False
        lastpart = keyparts[-1]

        if lastpart.find('\\ ') != -1:
            keyparts[-1] = lastpart.replace('\\','')

        # If no backspace is found at the end, but empty
        # space is found, strip it
        elif lastpart and lastpart[-1] == ' ':
            strippable = True

        key = ''.join(keyparts)
        if strippable:
            key = key.strip()
            oldkey = oldkey.strip()
        
        oldvalue = self.unescape(oldvalue)
        value = self.unescape(value)
        
        self._props[key] = value.strip()

        # Check if an entry exists in pristine keys
        if self._keymap.has_key(key):
            oldkey = self._keymap.get(key)
            self._origprops[oldkey] = oldvalue.strip()
        else:
            self._origprops[oldkey] = oldvalue.strip()
            # Store entry in keymap
            self._keymap[key] = oldkey
        
    def escape(self, value):

        # Java escapes the '=' and ':' in the value
        # string with backslashes in the store method.
        # So let us do the same.
        # newvalue = value.replace(':','\:')
        # newvalue = newvalue.replace('=','\=')

        return value

    def unescape(self, value):

        # Reverse of escape
        # newvalue = value.replace('\:',':')
        # newvalue = newvalue.replace('\=','=')

        return value
        
    def load(self, stream):
        """ Load properties from an open file stream """
        
        # For the time being only accept file input streams
        if type(stream) is not file:
            raise TypeError('Argument should be a file object!')
        # Check for the opened mode
        if stream.mode != 'r':
            raise ValueError('Stream should be opened in read-only mode!')

        try:
            lines = stream.readlines()
            self.__parse(lines)
        except IOError as e:
            raise

    def getProperty(self, key):
        """ Return a property for the given key """
        
        return self._props.get(key,'')

    def setProperty(self, key, value):
        """ Set the property for the given key """

        if type(key) is str and type(value) is str:
            self.processPair(key, value)
        else:
            raise TypeError('both key and value should be strings!')

    def propertyNames(self):
        """ Return an iterator over all the keys of the property
        dictionary, i.e the names of the properties """

        return self._props.keys()

    def list(self, out=sys.stdout):
        """ Prints a listing of the properties to the
        stream 'out' which defaults to the standard output """

        out.write('-- listing properties --\n')
        for key,value in self._props.items():
            out.write(''.join((key,'=',value,'\n')))

    def store(self, out, header=""):
        """ Write the properties list to the stream 'out' along
        with the optional 'header' """

        if out.mode[0] != 'w':
            raise ValueError('Steam should be opened in write mode!')

        try:
            out.write(''.join(('#',header,'\n')))
            # Write timestamp
            tstamp = time.strftime('%a %b %d %H:%M:%S %Z %Y', time.localtime())
            out.write(''.join(('#',tstamp,'\n')))
            # Write properties from the pristine dictionary
            for prop, val in self._origprops.items():
                out.write(''.join((prop,'=',self.escape(val),'\n')))
                
            out.close()
        except IOError as e:
            raise

    def getPropertyDict(self):
        return self._props

    def __getitem__(self, name):
        """ To support direct dictionary like access """

        return self.getProperty(name)

    def __setitem__(self, name, value):
        """ To support direct dictionary like access """

        self.setProperty(name, value)
        
    def __getattr__(self, name):
        """ For attributes not found in self, redirect
        to the properties dictionary """

        try:
            return self.__dict__[name]
        except KeyError:
            if hasattr(self._props,name):
                return getattr(self._props, name)

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

def buildPhoneConfig(macTemplate, mac, name, extension, address, password):
	# build Polycom line key configuration file so single MAC address
    print(mac)
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
        with open(mac, "w") as file:
            f.write(contents)

    except:
        print("unable to write file" + mac)
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
	print(address)
	
	return "m" + fixname  + "=" + extension + "\ns" + fixname + "=" + "SIP/" + address + "\n"  

def buildExtensionDial(name):
	# Build extension dialplan dial statment
	fixname = "".join(name.split())
	print(fixname)
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
	if (flag == "-m"): return 0
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


def main():
	
    # Check all paramaters are passed
    if len(sys.argv) < 5:
        print("Usage: GentTaukConf.py [-e extension] | [-m MAC] [-p password] | [-np no password]  <properties file> <extension file>\n")
        print("Extension File CSV Format:")
        print("First Last Name,Email,Extension,MAC Address\n")
        print("Example:")
        print("Foo Bar,fbar@specailai.com,8186,0004F214B68B")
        sys.exit()

    # open java stile properties file related to config build
    p = Properties()
    p.load(open(sys.argv[3]))

    # clear gen directory
    if os.path.exists(p['gen.dir']):
        shutil.rmtree(p['gen.dir'])        
    os.mkdir(p['gen.dir'])

    # open extension provisioning spread sheet
    f = openFiles(sys.argv[4],"r")

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
            provline = string.splitfields(line.strip(),',')

        # lower case MAC address
        provline[3] = provline[3].lower()

        #gen password if flag is set
        if (sys.argv[2] == "-p"):
            secret = generate_pass(8)
        else:
            secret = ""			

        # Write tauk polycom phone config & sip configuration
        PhoneSipConfig(sys.argv[1],p,provline,secret,sip)

        #Write vars in global context
        if (sys.argv[1] == "-m"):
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
        name = string.splitfields(provline[0],' ')
        if (len(name) > 1):
            directory.write(buildDirectory(p['templates.dir'] + os.sep
                + p['directory.template'],provline[2],name[0],name[1]))
            
            if (sys.argv[1] == "-m"):
                isymphony.write(buildiSymphony(p['templates.dir'] + os.sep
                    + p['isymphony.template'],provline[2],name[0],name[1],provline[3],p['voicemail.context']))
            else:
                isymphony.write(buildiSymphony(p['templates.dir'] + os.sep
                    + p['isymphony.template'],provline[2],name[0],name[1],provline[2],p['voicemail.context']))
                    
        else:
            directory.write(buildDirectory(p['templates.dir'] + os.sep
                + p['directory.template'],provline[2],provline[0],""))
            
            if (sys.argv[1] == "-m"):
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
