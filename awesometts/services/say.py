# -*- coding: utf-8 -*-

from PyQt4 import QtGui,QtCore
import re, subprocess
from anki.utils import stripHTML, isMac
from urllib import quote_plus
import awesometts.config as config
import awesometts.util as util
from subprocess import Popen, PIPE, STDOUT

if isMac:

	vlist = subprocess.check_output("say -v ? |sed 's/  .*//'", shell=True)

	voicelist = vlist.split('\n')
	voicelist.pop()

	def playOSXsayTTS(text, voice):
		text = re.sub("\[sound:.*?\]", "", stripHTML(text.replace("\n", "")).encode('utf-8'))
		subprocess.Popen(['say', '-v', voice, text], stdin=PIPE, stdout=PIPE, stderr=STDOUT).communicate()


	def playfromtagOSXsayTTS(fromtag):
		print fromtag
		for item in fromtag:
			match = re.match("(.*?):(.*)", item, re.M|re.I)
			playOSXsayTTS(match.group(2), match.group(1))

	def recordOSXsayTTS(text, voice):
		text = re.sub("\[sound:.*?\]", "", stripHTML(text.replace("\n", "")).encode('utf-8'))
		filename_aiff = util.generateFileName(text, 'say', 'iso-8859-1', '.aiff')
		filename_mp3 = util.generateFileName(text, 'say', 'iso-8859-1', '.mp3')
		subprocess.Popen(['say', '-v', voice, '-o', filename_aiff, text], stdin=PIPE, stdout=PIPE, stderr=STDOUT).wait()
		subprocess.Popen(['lame', '--quiet', filename_aiff, filename_mp3], stdin=PIPE, stdout=PIPE, stderr=STDOUT).wait()
		subprocess.Popen(['rm', filename_aiff], stdin=PIPE, stdout=PIPE, stderr=STDOUT).wait()
		return filename_mp3.decode('utf-8')

	def filegenerator_layout(form):
		verticalLayout = QtGui.QVBoxLayout()
		textEditlabel = QtGui.QLabel()
		textEditlabel.setText("Voice:")
		form.comboBoxSay = QtGui.QComboBox()
		form.comboBoxSay.addItems(voicelist)

		verticalLayout.addWidget(textEditlabel)
		verticalLayout.addWidget(form.comboBoxSay)
		return verticalLayout

	def recordOSXsayTTS_form(form, text):
		return recordOSXsayTTS(text, voicelist[form.comboBoxSay.currentIndex()])

	def filegenerator_run(form):
		return recordOSXsayTTS(unicode(form.texttoTTS.toPlainText()), voicelist[form.comboBoxSay.currentIndex()])

	def filegenerator_preview(form):
		return playOSXsayTTS(unicode(form.texttoTTS.toPlainText()), voicelist[form.comboBoxSay.currentIndex()])

	TTS_service = {'say' : {
	'name': 'OSX Say',
	'play' : playOSXsayTTS,
	'playfromtag' : playfromtagOSXsayTTS,
	'record' : recordOSXsayTTS_form,
	'filegenerator_layout': filegenerator_layout,
	'filegenerator_preview': filegenerator_preview,
	'filegenerator_run': filegenerator_run}}


