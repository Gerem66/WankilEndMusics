#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Libs
import os
from time import sleep
import threading
import subprocess
from urllib.parse import unquote_plus
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip

# Apis
import youtube_dl
from ShazamAPI import Shazam

class Music(object):
    def __init__(self, title, artist):
        self.title = title
        self.artist = artist

class Video(object):
    def __init__(self, ID, url, name, ext):
        self.ID = ID
        self.url = url
        self.name = name
        self.ext = ext
        self.filename = ""
        self.downloaded = False
        self.croped = False
        self.analyzed = False
        self.musics = []

class MusicFinder():
    # str?, bool, float, float, int
    def __init__(self, clearCache = True, start = 0, end = 0, max_attemps = 10, max_thread = 4):
        self.errors = []
        self.videos = []

        self.__connected = False
        self.__username = None
        self.__password = None

        self.__start = float(start)
        self.__end = float(end)
        self.__clearCache = clearCache
        self.__max_thread = max_thread
        self.__max_attemps = max_attemps

        if not os.path.isdir('./audio'):
            os.mkdir('./audio')

    def __SaveData(self):
        f = open("result.txt", "a")
        for v in self.videos:
            #f.write("[{}] {} song(s) found\n".format(v.name, len(v.musics)))
            for s in v.musics:
                f.write("{} - {}\n".format(s.title, s.artist))
        f.close()
    
    def AddVideo(self, ID, url, name, ext):
        v = Video(ID, url, name, ext)
        self.videos.append(v)
    
    def Connect(self, username, password):
        self.__connected = True
        self.__username = username
        self.__password = password
    
    def GetVideosFromUrl(self, url):
        params = {
            'format': 'bestaudio/best',
            'quiet': True,
            'ignoreerrors': True
        }
        if self.__connected:
            params['username'] = self.__username
            params['password'] = self.__password
        
        Attempt = self.__max_attemps
        while Attempt > 0:
            Attempt -= 1
            try:
                youtube = youtube_dl.YoutubeDL(params)
                result = youtube.extract_info(url, download=False)

                if 'entries' in result:
                    videos = result['entries']
                    for video in videos:
                        self.AddVideo(video['id'], video['webpage_url'], video['title'], video['ext'])
                else:
                    print(result['ext'])
                    self.AddVideo(result['id'], result['webpage_url'], result['title'], result['ext'])
                Attempt = 0
            except Exception as ex:
                self.errors.append(ex)

    def Processing(self):
        for videoIndex in range(len(self.videos)):
            started = False
            while not started:
                if threading.active_count() < self.__max_thread:
                    threading.Thread(target=self.__Process, args=(videoIndex,)).start()
                    started = True
                self.__Print()
                sleep(.5)
        while threading.active_count() > 1:
            self.__Print()
            sleep(.5)
        self.__SaveData()

    def __Process(self, index):
        video = self.videos[index]
        tmp_filename = './audio/{}.{}'.format(video.ID, video.ext)

        # Download
        dl = self.__Download(video.url, tmp_filename)
        if dl: self.videos[index].downloaded = True

        # Crop
        cr = self.__Crop(tmp_filename)
        if cr: self.videos[index].croped = True

        # Analyse
        song = self.__Recognize(tmp_filename)
        if song != None:
            self.videos[index].musics.append(song)
        self.videos[index].analyzed = True

        # Clear cache
        if self.__clearCache: os.remove(tmp_filename)
        else: os.rename(tmp_filename, './audio/' + video.name + '.' + video.ext)
    
    def __Download(self, Url, filename):
        ydl_opts = {
            'outtmpl': filename,
            'format': 'bestaudio/best',
            'quiet': True,
            'ignoreerrors': True
        }
        status = False
        Attempt = self.__max_attemps
        while Attempt > 0:
            Attempt -= 1
            try:
                with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([Url])
                Attempt = 0
                status = True
            except Exception as ex:
                self.errors.append(ex)
        return status
    
    def __GetDuration(self, filename):
        result = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', filename], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return float(result.stdout)
    
    def __Crop(self, file):
        status = True
        start = self.__start
        end = self.__end
        duration = self.__GetDuration(file)

        if abs(start) > duration: start = 0
        if abs(end) > duration: end = 0
        if start < 0: start = duration + start
        if end <= 0: end = duration + end
        if end < start: return

        try:
            cropFile = '.'.join(file.split('.')[:-1]) + '_crop.' + file.split('.')[-1]
            ffmpeg_extract_subclip(file, start, end, cropFile)
            os.remove(file)
            os.rename(cropFile, file)
        except Exception as ex:
            status = False
            self.errors.append(ex)
        return status
    
    def __Recognize(self, file):
        Attempt = self.__max_attemps
        song = None
        while Attempt > 0:
            Attempt -= 1
            mp3_file_content_to_recognize = open(file, 'rb').read()
            shazam = Shazam(mp3_file_content_to_recognize)
            recognize_generator = shazam.recognizeSong()
            try:
                read = next(recognize_generator)
                title = unquote_plus(read[1]['track']['urlparams']['{tracktitle}'])
                artist = unquote_plus(read[1]['track']['urlparams']['{trackartist}'])
                song = Music(title, artist)
                Attempt = 0
            except Exception as ex:
                self.errors.append(ex)
        return song
    
    def __Print(self):
        os.system("cls || clear")

        nb_music = len(self.videos)
        nb_downloaded = 0
        nb_croped = 0
        nb_analyzed = 0
        nb_musics = 0
        nb_errors = len(self.errors)
        for v in self.videos:
            if v.downloaded: nb_downloaded += 1
            if v.croped: nb_croped += 1
            if v.analyzed: nb_analyzed += 1
            nb_musics += len(v.musics)
        
        align = 30
        print("Music Finder\n\n")
        print("{}{}".format("Nombre total de vidéos".ljust(align), nb_music))
        print("{}{}".format("Téléchargées".ljust(align), nb_downloaded))
        print("{}{}".format("Cropées".ljust(align), nb_croped))
        print("{}{}".format("Analysées".ljust(align), nb_analyzed))
        print("{}{}".format("Musiques trouvées".ljust(align), nb_musics))
        print("{}{}".format("Nombre d'erreurs".ljust(align), nb_errors))

clearCache = True
start = -20
end = 0
max_attemps = 10
pa = MusicFinder(clearCache, start, end, max_attemps)

pa.GetVideosFromUrl('https://www.youtube.com/watch?v=ffABmp2Eucs&list=PLBA4C51FC5D585478')
pa.Processing()