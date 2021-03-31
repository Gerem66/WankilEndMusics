#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import youtube_dl
from ShazamAPI import Shazam
from urllib.parse import unquote_plus
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
from time import sleep
import subprocess

class YTVideos():
    def __init__(self):
        self.errors = []
        self.urls = []
        self.urls_size = 0
        self.urls_available = 0
        self.AudioDownload = 0
        self.AudioCrop = 0
        self.Recognition = 0
        self.connected = False
        self.username = None
        self.password = None
        self.songnames = []
    
    def Connect(self, username, password):
        self.connected = True
        self.username = username
        self.password = password
    
    def PlaylistToUrls(self, url):
        self.PrintAll()
        try:
            params = {
                'outtmpl': '%(id)s%(ext)s',
                'quiet': True,
                'ignoreerrors': True
            }
            if self.connected:
                params['username'] = self.username
                params['password'] = self.password
            
            ydl = youtube_dl.YoutubeDL(params)
            result = ydl.extract_info(url, download=False)

            if 'entries' in result:
                videos = result['entries']
                self.urls_size = len(videos)
                for i in range(len(videos)):
                    url = result['entries'][i]['webpage_url']
                    self.urls_available += 1
                    self.urls.append(url)
        # Error => Private video
        except (youtube_dl.utils.ExtractorError, youtube_dl.utils.DownloadError) as ex:
            self.errors.append(ex)
        except Exception as ex:
            self.errors.append(ex)
        os.system("cls || clear")
    
    def DownloadAllSongs(self):
        for URL in self.urls:
            ydl_opts = {
                'format': 'bestaudio/best',
                'quiet': True,
                'outtmpl': './audio/' + str(self.AudioDownload) + '.%(ext)s'
            }
            downloaded = False
            while not downloaded:
                try:
                    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([URL])
                    self.AudioDownload += 1
                    self.PrintAll()
                    downloaded = True
                except Exception as ex:
                    self.errors.append(ex)
                    self.PrintAll()
    
    def CropAllSong(self):
        path = './audio/'
        dirs = os.listdir(path)
        for file in dirs:
            duration = self.GetDuration('./audio/' + file)
            ffmpeg_extract_subclip('./audio/' + file, duration - 20, duration, './audio/_' + file)
            self.AudioCrop += 1
            self.PrintAll()

    def GetDuration(self, input_video):
        result = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', input_video], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return float(result.stdout)

    def RecognizeAllSong(self):
        path = './audio/'
        dirs = os.listdir(path)
        for file in dirs:
            if file[0] != '_': continue
            attempt = 20
            while attempt > 0:
                attempt -= 1
                mp3_file_content_to_recognize = open('./audio/' + file, 'rb').read()
                shazam = Shazam(mp3_file_content_to_recognize)
                recognize_generator = shazam.recognizeSong()
                try:
                    test = next(recognize_generator)
                    title = unquote_plus(test[1]['track']['urlparams']['{tracktitle}'])
                    artist = unquote_plus(test[1]['track']['urlparams']['{trackartist}'])
                    self.songnames.append([title, artist])
                    self.Recognition += 1
                    self.PrintAll()
                    attempt = -1
                except Exception as ex:
                    self.errors.append(ex)
                    self.PrintAll()


    def PrintAll(self):
        width = os.get_terminal_size().columns
        os.system("cls || clear")
        print("Urls\tAudio dl\tAudio crop\tRecognition\tErrors")
        print("{}\t{}\t\t{}\t\t{}\t\t{}".format(self.urls_available, self.AudioDownload, self.AudioCrop, self.Recognition, len(self.errors)))
        if (self.urls_size <= 0):
            print("\nUrls loading...")
        for i in self.songnames:
            print(i)

URL = ""
videos = YTVideos()
videos.PlaylistToUrls(URL)
videos.DownloadAllSongs()
videos.CropAllSong()
videos.RecognizeAllSong()