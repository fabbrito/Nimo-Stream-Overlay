# -*- coding: utf-8 -*-
"""
Created on Sun Feb 10 09:23:52 2019

@author: fabbr
"""
import tkinter as tk
from tkinter import ttk, font
from requests_html import HTMLSession
import psutil
import re
import os
import time


class StreamOverlayAPP(tk.Tk):

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        self.animtext = ''
        self.url = ''
        self.obj = 0
        self.followers = 0
        self.savedfollowers = 0
        self.errors = []
        self.resolution = ["1920", "1080"]

        self.ReadConfigFile()

        topf = ttk.Frame()
        bottomf = ttk.Frame()
        topf.pack(expand=True, fill=tk.BOTH, side=tk.TOP)
        bottomf.pack(expand=True, fill=tk.BOTH, side=tk.TOP)

        self.generalfont = font.Font(family='Helvetica', size=10)
        self.overlayfont = font.Font(family='Helvetica', size=14)

        self.button = ttk.Button(
            topf, text='start', command=self.start, state='enabled')
        self.button.pack(side=tk.RIGHT)
        self.animation_label = ttk.Label(topf, text='', font=self.generalfont)
        self.animation_label.pack(side=tk.LEFT)
        self.errors_label = ttk.Label(topf, text='', font=self.generalfont)
        self.errors_label.pack(side=tk.BOTTOM)
        if len(self.errors) > 0:
            self.button['state'] = 'disabled'
            self.errors_label['text'] = '\n'.join(e for e in self.errors)
            # print('\n'.join('>> ' + e for e in self.errors))

        self.style = ttk.Style(self)
        self.style.theme_use('winnative')
        self.style.layout('text.Horizontal.TProgressbar',
                          [('Horizontal.Progressbar.trough',
                            {'children': [('Horizontal.Progressbar.pbar',
                                           {'side': 'left', 'sticky': 'ns'})],
                             'sticky': 'nswe'}),
                              ('Horizontal.Progressbar.label', {'sticky': ''})])
        self.style.configure('text.Horizontal.TProgressbar', font=self.overlayfont,
                             text='0 / 0', thickness=int(self.resolution[1]) // 40)
        self.progress = ttk.Progressbar(bottomf, orient="horizontal", length=int(self.resolution[0]) // 4,
                                        mode="determinate", style='text.Horizontal.TProgressbar')
        self.progress.pack()

    def start(self):
        self.progress["value"] = 0
        self.progress["maximum"] = self.obj
        self.getNimoTVFollowers()

    def ReadConfigFile(self):
        try:
            with open('stream_overlay.conf') as config_file:
                data = config_file.read()
        except FileNotFoundError:
            self.errors.append('File \"stream_overlay.conf\" not found!')
        try:
            line = re.findall(r"url ?= ?[\/\"\'.:\-\w%&?]+", data)[0]
            self.url = re.findall(
                r"https?://(?:[-\w.]|\/|(?:%[\da-fA-F]{2}))+", line)[0]
        except IndexError:
            self.errors.append('Missing nimo.tv url in configuration file!')
        try:
            line = re.findall(r"obj ?= ?\d+", data)[0]
            self.obj = int(re.findall(r"\d+", line)[0])
        except IndexError:
            self.errors.append('Missing objective in configuration file!')
        try:
            line = re.findall(r"resolution ?= ?\d+x\d+", data)[0]
            self.resolution = re.findall(r"\d+", line)
        except IndexError:
            self.errors.append('Missing resolution in configuration file!')

    def getNimoTVFollowers(self):
        if len(self.animtext) < 10:
            self.animtext += ':'
        else:
            self.animtext = ''
        self.animation_label['text'] = self.animtext

        session = HTMLSession()

        r = session.get(self.url)
        r.html.render()
        page_source = str(r.html.html.encode('utf-8'))

        self.savedfollowers = self.followers
        try:
            crop = re.findall(
                r"nimo-rm_followers[\"\w><\\\/ =.:]+followers:[\"\w><\\\/ =.:]+\d+", page_source)
            self.followers = int(re.findall(r"\d+", crop[0])[0])
            self.errors_label['text'] = ''
        except:
            self.errors_label['text'] = 'Unable to retrieve the number of followers!'
            self.followers = self.savedfollowers

        session.close()
        self.progress["value"] = self.followers
        self.style.configure('text.Horizontal.TProgressbar',
                             text='{0} / {1}'.format(self.followers, self.obj))

        if self.followers < self.obj:
            self.after(10000, self.getNimoTVFollowers)


if __name__ == '__main__':
    p = psutil.Process(os.getpid())
    p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)

    app = StreamOverlayAPP()
    app.title('Stream Overlay')
    app.mainloop()
