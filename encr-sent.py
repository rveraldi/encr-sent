#!/bin/env python3.7

import os
import subprocess
import time
import tempfile
import shutil
import inotify.adapters
import getpass
import daemon
import signal

sent_folder="/Maildir/.Sent"
sent=sent_folder+"/cur"
domain="infn.cc"

def shutdown(signum, frame):
	sys.exit(0)

def _main():
	homedir = os.path.expanduser("~")
	sentpath=homedir+sent+"/"
	mailtemp=homedir+"/MailTemp"
	rcpt=getpass.getuser()+'@'+domain
	i = inotify.adapters.Inotify()
	i.add_watch(sentpath)
	for event in i.event_gen(yield_nones=False):
		(_, type_names, path, filename) = event
		if(type_names[0] == 'IN_MOVED_TO'):
			time.sleep(1)
			tempfile.tempdir=mailtemp
			with open(path+filename,"r") as ct, tempfile.NamedTemporaryFile(mode='w', delete=False)  as et:
				gpgit=subprocess.Popen(["/usr/local/bin/gpgit.pl",rcpt], stdin=ct, stdout=et)
				try:
    					outs, errs = gpgit.communicate(timeout=15)
				except TimeoutExpired:
    					gpgit.kill()
    					outs, errs = gpgit.communicate()
				orig_name=et.name
				et.close()
				shutil.copyfile(orig_name, path+filename)
				try:
					os.remove(orig_name)
				except OSError as e:
					print("Error: %s - %s." % (e.filename, e.strerror))

#if __name__ == '__main__':
with daemon.DaemonContext(
	chroot_directory=None,working_directory=os.path.expanduser("~"),
        signal_map={ signal.SIGTERM: shutdown, signal.SIGTSTP: shutdown }):
	_main()
