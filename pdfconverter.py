#!/usr/bin/env python
#
# pdfconverter.py
# Chris Holmes
# chris@holmser.net
#
# the purpose of this script is to convert all .tif files sent to pdfconverter@holmser.net
# and send them back.  It uses imagemagick for the conversion, and python for the rest.  It
# is designed to be run as a cron job and run in the background. 
#
########################################################################################### 


import email, getpass, imaplib, os, smtplib, subprocess, imghdr
import datetime
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email import Encoders

path = "/home/holmser/.pdfconverter/"
config_file = "pdfconverter.conf"
#############################################
class Config:
	def __init__(self, path, config_file):
		if not os.path.exists(path):
			os.makedirs(path)
		f = open(path+config_file, 'r')
		self.user = f.readline()
		self.pwd = f.readline()
	def print_user(self):
		print(self.user.rstrip())
		return (self.user.rstrip())
	def print_pwd(self):
		return (self.pwd.rstrip())

##############################################

class Action_log:
	def __init__(self):
		self.logfile = open(path+"pcv.log", 'a')
		
	def write_log(self, email, filename, success):
		now = datetime.datetime.now()
		if (success):
			self.logfile.append(now.strftime("%Y-%m-%d %H:%M:%S")
				+ "Conversion successful: " + email + " "+filename)
		else: 
			self.logfile.append(now.strftime("%Y-%m-%d %H:%M:%S") + "FAILURE: "+email+" "+filename)

	#def failure(email, filename)

##############################################
		
		
cred = Config(path, config_file)
detach_dir = '.'
user = cred.print_user()
pwd = cred.print_pwd()

class Msg_content:
	def __init__(self, filename,address):
		self.filename = filename
		self.address = address
		self.log = Action_log()
		if (self.filename.endswith("tiff")):
			offset = 4
		elif (self.filename.endswith("tif")):
			offset = 3
   # Convert .tif to .pdf and email it back
	def convert(self): 
		subprocess.call(["convert " 
			+self.filename+ " PDF:"
			+self.filename[0:-offset]+"pdf"], 
			shell=True)
   	  # send the mail message
		mail(self.address,
				"TIFF to PDF conversion complete",
				self.filename[0:-offset]+"pdf"+ 
				" has been attached for your convenience", self.filename[0:-3]+"pdf")
		self.log.write_log(self.filename, self.address, True)

   # Send rejection response mail
	def reject(self):
		mail(self.address,"Conversion failed", self.filename+" is not a valid .tif file.  Please check the format and try again.", self.filename)
   		self.log.write_log(self.filename, self.address, False)
   # Determine if the attachment is a valid tif file (filename)
	def isvalid(self):
		if (imghdr.what(self.filename) == 'tiff'):
			return True
		else:
			return False
   # Delete processed attachments
	def cleanup(self):
		subprocess.call(["rm "+ self.filename[0:-3]+"*"], shell=True) 

def mail(to, subject, text, attach):
	msg = MIMEMultipart()

	msg['From'] = user
	msg['To'] = to
	msg['Subject'] = subject

	msg.attach(MIMEText(text))

	part = MIMEBase('application', 'octet-stream')
	part.set_payload(open(attach, 'rb').read())
	Encoders.encode_base64(part)
	part.add_header('Content-Disposition',
		'attachment; filename="%s"' % os.path.basename(attach))
	msg.attach(part)

	mailServer = smtplib.SMTP("smtp.gmail.com", 587)
	mailServer.ehlo()
	mailServer.starttls()
	mailServer.ehlo()
	mailServer.login(user, pwd)
	mailServer.sendmail(user, to, msg.as_string())
   # Should be mailServer.quit(), but that crashes...
	mailServer.close()


# connecting to the gmail imap server
def get_mail():
	m = imaplib.IMAP4_SSL("imap.gmail.com")
	m.login(user,pwd)
	m.select("INBOX") # here you a can choose a mail box like INBOX instead
    # use m.list() to get all the mailboxes

	resp, items = m.search(None, "UNSEEN") # you could filter using the IMAP rules here (check http://www.example-code.com/csharp/imap-search-critera.asp)
	items = items[0].split() # getting the mails id

	for emailid in items:
		resp, data = m.fetch(emailid, "(RFC822)") # fetching the mail, "`(RFC822)`" means "get the whole stuff", but you can ask for headers only, etc
		email_body = data[0][1] # getting the mail content
		mail = email.message_from_string(email_body) # parsing the mail content to get a mail object

        #Check if any attachments at all
		if mail.get_content_maintype() != 'multipart':
			continue

        #print "["+mail["From"]+"] :" + mail["Subject"]
        #print mail["From"]
		email_addy = mail["From"]

        # we use walk to create a generator so we can iterate on the parts and forget about the recursive headach
		for part in mail.walk():
        # multipart are just containers, so we skip them
			if part.get_content_maintype() == 'multipart':
				continue

            # is this part an attachment ?
			if part.get('Content-Disposition') is None:
				continue

			filename = part.get_filename()
			print(filename)
			counter = 1

            # if there is no filename, we create one with a counter to avoid duplicates
			if not filename:
				filename = 'part-%03d%s' % (counter, 'bin')
				counter += 1

			att_path = os.path.join(detach_dir, filename)

            #Check if its already there
			if not os.path.isfile(att_path) :
                # finally write the stuff
				fp = open(att_path, 'wb')
				fp.write(part.get_payload(decode=True))
				fp.close()
				info  = Msg_content(filename, email_addy) 
				if (info.isvalid() == True):
					info.convert()
				else:
					info.reject()
					info.cleanup()

get_mail()

