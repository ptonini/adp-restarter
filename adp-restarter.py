#!/usr/bin/python

__author__ = 'ptonini'

# Modules
import sys
import argparse
import os
import re
import smtplib
import zipfile
import subprocess
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import formatdate
from email import encoders
import platform

# Main()
def main():

    # Command line argument parsing
    parser = argparse.ArgumentParser(description='ADP Restarter')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 1.0')
    parser.add_argument('-d', dest='dir', type=str, default='/dados/xml/data', help='Directory to monitor')
    parser.add_argument('-p', dest='pattern', type=str, default='', help='File match pattern')
    parser.add_argument('-c', dest='crit', type=int, default=400, help='Restart threshold')
    parser.add_argument('-f', dest='logfile', type=str, default='logs.zip', help='Log archive')
    args = parser.parse_args(sys.argv[1:])

    count = 0
    for root, path, files in os.walk(args.dir):
        for file in files:
            if re.match(args.pattern, file):
                count += 1

    if count > args.crit:

        zf = zipfile.ZipFile('/tmp/' + args.logfile, mode='w')
        zf.write('/var/log/m2m-adapter.log', compress_type=zipfile.ZIP_DEFLATED)
        zf.write('/var/log/syslog', compress_type=zipfile.ZIP_DEFLATED)
        zf.write('/var/log/mongos.log', compress_type=zipfile.ZIP_DEFLATED)
        zf.close()

        dest = ['hosting@m2msolutions.com.br',
                'tiago.braga@m2msolutions.com.br',
                'leandro.braga@m2msolutions.com.br',
                'claudia.ladeira@m2msolutions.com.br',
                'atendiment@m2msolutions.com.br']

        msg = MIMEMultipart()
        msg['From'] = 'adapterm2m@m2msolutions.com.br'
        msg['To'] = 'M2M'
        msg['Date'] = formatdate(localtime = True)
        msg['Subject'] = 'ADP-RESTARTER - ' + platform.node()
        msg.attach (MIMEText('O M2M Adapter em ' + platform.node() + 'foi reiniciado por acumulo de xmls'))

        attach = open('/tmp/' + args.logfile, 'rb')
        part = MIMEBase('application', "octet-stream")
        part.set_payload(attach.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="' + args.logfile + '"')
        msg.attach(part)

        try:
            server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
            server.ehlo()
            server.login(msg['From'], 'm2msolutions')
            server.sendmail(msg['From'], dest, str(msg))
            server.close()
            print 'successfully sent the mail'
        except Exception, e:
            print e

        subprocess.call(['/etc/init.d/m2m-adapter restart'], shell=True)

if __name__ == '__main__':
    main()