# -*- coding: utf-8 -*-
"""
Created on Sun Feb 10 09:23:52 2019

@author: fabbr
"""
import tkinter as tk
from tkinter import ttk, font
import requests_html
import psutil
import re
import os
import string
import time
import logging


class StreamOverlayAPP(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        logging.basicConfig(filename='errors.log', level=logging.ERROR,
                            format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

        self.animtext = ["(~‾▿‾)~", "~(‾▿‾~)"]
        self.animq = 0
        self.animdir = 0
        self.followers = 0
        self.savedfollowers = 0

        self.ReadConfigFile()

        self.generalfont = font.Font(
            family=self.configs['general']['fontfamily'], size=self.configs['general']['fontsize'])
        self.overlayfont = font.Font(
            family=self.configs['overlay']['fontfamily'], size=self.configs['overlay']['fontsize'])

        # Top frame
        topf = ttk.Frame()
        topf.pack(expand=True, fill=tk.BOTH, side=tk.TOP)
        self.button_stop = ttk.Button(
            topf, text='Stop', command=self.stop, state='disabled')
        self.button_stop.pack(side=tk.RIGHT)
        self.button_start = ttk.Button(
            topf, text='Start', command=self.start, state='enabled')
        self.button_start.pack(side=tk.RIGHT)
        self.button_save = ttk.Button(
            topf, text='Save', command=self.save, state='enabled')
        self.button_save.pack(side=tk.RIGHT)
        self.animation_label = ttk.Label(
            topf, text='', font=self.generalfont)
        self.animation_label.pack(side=tk.LEFT)

        # Middle frame
        midf = ttk.Frame()
        midf.pack(expand=True, fill=tk.BOTH, side=tk.TOP)

        self.url_label = ttk.Label(midf, text='URL: ', font=self.generalfont)
        self.url_label.pack(side=tk.LEFT)
        self.urlentry = ttk.Entry(midf, width=40, font=self.generalfont)
        self.urlentry.insert(tk.INSERT, self.configs['save']['url'])
        self.urlentry.pack(side=tk.LEFT)
        self.objentry = ttk.Entry(midf, width=5, font=self.generalfont)
        self.objentry.insert(tk.INSERT, self.configs['save']['objective'])
        self.objentry.pack(side=tk.RIGHT)
        self.obj_label = ttk.Label(midf, text='OBJ: ', font=self.generalfont)
        self.obj_label.pack(side=tk.RIGHT)

        # Bottom frame
        botf = ttk.Frame()
        botf.pack(expand=True, fill=tk.BOTH, side=tk.TOP)
        self.style = ttk.Style(self)
        self.style.theme_use('winnative')
        self.style.layout('text.Horizontal.TProgressbar', [('Horizontal.Progressbar.trough', {'children': [('Horizontal.Progressbar.pbar', {
                          'side': 'left', 'sticky': 'ns'})], 'sticky': 'nswe'}), ('Horizontal.Progressbar.label', {'sticky': ''})])
        self.style.configure('text.Horizontal.TProgressbar', font=self.overlayfont, text='0 / 0',
                             thickness=self.configs['overlay']['progressbarthikness'], foreground=self.configs['overlay']['foregroundcolor'],
                             background=self.configs['overlay']['backgroundcolor'], troughcolor=self.configs['overlay']['troughcolor'])
        self.progress = ttk.Progressbar(botf, orient="horizontal", length=self.configs['overlay']['progressbarlength'],
                                        mode="determinate", style='text.Horizontal.TProgressbar')
        self.progress.pack()

    def save(self):
        self.readInput()
        data = ''
        for name, dict_ in self.configs.items():
            for name_, dict__ in dict_.items():
                data += '{0}.{1}={2}\n'.format(name, name_, dict__)
            data += '\n'

        with open('stream_overlay.conf', 'w') as config_file:
            config_file.write(data)
        logging.info('Saved changes to the configurations file!')

    def readInput(self):
        self.configs['save']['url'] = re.findall(
            r"https?://(?:[-\w.]|\/|(?:%[\da-fA-F]{2}))+", self.urlentry.get())[0]
        self.configs['save']['objective'] = int(
            re.findall(r"\d+", self.objentry.get())[0])

    def stop(self):
        self.urlentry['state'] = 'enabled'
        self.objentry['state'] = 'enabled'
        self.button_start['state'] = 'enabled'
        self.button_stop['state'] = 'disabled'
        self.button_save['state'] = 'enabled'
        self.after_cancel(self.job_main)
        self.after_cancel(self.job_sec)

    def start(self):
        self.readInput()
        self.progress["value"] = 0
        self.progress["maximum"] = self.configs['save']['objective']
        self.urlentry['state'] = 'disabled'
        self.objentry['state'] = 'disabled'
        self.button_start['state'] = 'disabled'
        self.button_stop['state'] = 'enabled'
        self.button_save['state'] = 'disabled'
        self.getNimoTVFollowers()
        self.animation()

    def ReadConfigFile(self):
        try:
            with open('stream_overlay.conf') as config_file:
                data = config_file.read()
        except FileNotFoundError:
            logging.error('Configurations file not found!')

        self.configs = {'general': {}, 'overlay': {}, 'save': {}}
        for configtype in ['general', 'overlay', 'save']:
            crop_configs = re.findall(
                configtype + r'.\w+ ?= ?[\"\w><\\\/ =.:#]+', data)
            for conf in crop_configs:
                try:
                    config_name = re.split(r' ?= ?', conf)[
                        0][len(configtype) + 1:]
                    config_value = re.split(r' ?= ?', conf)[1]
                    if all(c in string.digits for c in config_value):
                        config_value = int(config_value)
                    self.configs[configtype][config_name] = config_value
                except:
                    logging.error(
                        'Problem while loading the configurations file!')

    def animation(self):
        if self.animdir == 0:
            aux_str = ' ' * self.animq
            self.animq += 1
        else:
            aux_str = ' ' * self.animq
            self.animq -= 1
        self.animation_label['text'] = aux_str + self.animtext[self.animdir]
        if self.animq == 0:
            self.animdir = 0
        elif self.animq > 15:
            self.animdir = 1
        self.job_sec = self.after(500, self.animation)

    def getNimoTVFollowers(self):
        with requests_html.HTMLSession() as session:
            resp = session.get(self.configs['save']['url'], timeout=15)
            time.sleep(1)
            resp.html.render(wait=1, timeout=15)
            time.sleep(1)
            page_source = str(resp.html.html.encode('utf-8'))

        try:
            crop = re.findall(
                r"nimo-rm_followers[\"\w><\\\/ =.:]+followers:[\"\w><\\\/ =.:]+\d+", page_source)
            self.followers = int(re.findall(r"\d+", crop[0])[0])
            if self.followers == 0:
                self.followers = self.savedfollowers
            else:
                self.savedfollowers = self.followers
        except:
            logging.error('Unable to retrieve the number of followers!')
            self.followers = self.savedfollowers

        self.progress['value'] = self.followers
        self.style.configure('text.Horizontal.TProgressbar',
                             text='{0} / {1}'.format(self.followers, self.configs['save']['objective']))
        timeinterval = self.configs['overlay']['timeintervals']
        if timeinterval == 0 or timeinterval > 3600:
            timeinterval = 10
        if self.followers < self.configs['save']['objective']:
            self.job_main = self.after(
                timeinterval * 1000, self.getNimoTVFollowers)


if __name__ == '__main__':
    p = psutil.Process(os.getpid())
    p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)

    app = StreamOverlayAPP()
    app.title('Stream Overlay')
    app.mainloop()
