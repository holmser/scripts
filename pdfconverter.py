#!/usr/bin/env python
#
# Chris Holmes
# chris@holmser.net
#
# the purpose of this script is to convert all .tif files sent to pdfconverter@holmser.net
# and send them back.


import email, getpass, imaplib, os, smtplib, subprocess
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email import Encoders

detach_dir = '.'
user = "pdfconverter@holmser.net"
pwd = "**********"

class msg_content:
   def __init__(self, filename,address):
      self.filename = filename
      self.address = address
   def convert(self): 
      subprocess.call(["convert " +self.filename+ " PDF:"+self.filename[0:-3]+"pdf"], shell=True)
   	  #send the mail message
      mail(self.address,"TIFF to PDF conversion complete",self.filename[0:-3]+"pdf"+ " has been attached for your convenience", self.filename.replace('.TIF','.pdf'))
   def reject(self):
      mail(self.address,"Conversion failed", self.filename+" is not a valid .tif file.  Please check the format and try again.", self.filename)
   def isvalid(self):
      print(self.filename[-3:-1])
      if (self.filename[-3:-1] == "tif" or self.filename[-3:-1] == "TIF"):
         return True
      else:
         return False

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

    resp, items = m.search(None, "ALL") # you could filter using the IMAP rules here (check http://www.example-code.com/csharp/imap-search-critera.asp)
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
                info  = msg_content(filename, email_addy) 
                if (info.isvalid() == True):
                   info.convert()
                else:
                   info.reject()
                #mail("holmser171@gmail.com","Your Converted PDF","Your Converted PDF", "test.pdf")

get_mail()
