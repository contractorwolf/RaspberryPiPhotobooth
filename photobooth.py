#!/usr/bin/env python

# EXECUTE THIS FILE LIKE THIS:
# > sudo python photobooth.py

from time import sleep

import os
import os.path
import subprocess as sub
import datetime
import pygame
import pygbutton
import RPi.GPIO as GPIO
import glob
import sys

bounceMillis = 800 #waits 800 ms before noticing another button press
fps = 0; #frames per second
photos_taken = 0
index = 0
width = 1280
height = 980
continue_loop = True

image_name = ""
delay_time = .005
flash_time = .1
last_image_taken = ""
waiting_on_download = False #if this is true, look for last_image_taken 

current_image = 0
in_process = False
image_count = 0;
object_list = [] #list of preloaded images
change_ticks = 0
last_image_number = 0
last_preview = {}


#***************FUNCTIONS******************

def APressed(channel):
    print("A button pressed: " + str(index))
    TakePicture()
    
def BPressed(channel):
    print("B button pressed: " + str(index))    
    
    global change_ticks
    change_ticks = pygame.time.get_ticks() + 20000
    
    FlashLEDs(2)

    LastPicture()
    
def CPressed(channel):
    print("C button pressed: " + str(index))   
    
    global change_ticks
    change_ticks = pygame.time.get_ticks() + 20000

    PrevPicture()

def DPressed(channel):
    print("D button pressed: " + str(index))    
    
    global change_ticks
    change_ticks = pygame.time.get_ticks() + 20000
    
    NextPicture()


def RenderOverlay():
    #drow title and buttons
    
    #app name
    screen.blit(pygame.font.SysFont("freeserif",30,bold=0).render(app_name, 1, white),((width-350),10))

    #button
    take_pic_button.draw(screen)

    #button
    quit_button.draw(screen)

    pygame.display.update()

def LoadImageToObjectList(image_name):
    #load image by filename to the list of image objects for fast switching
    
    global object_list
    global image_count
    global last_image_number
    
    print "LoadImageToObjectList: " + image_name
    print "before load: " + str(pygame.time.get_ticks())
    load = pygame.image.load(image_name).convert_alpha()
    print "loaded: " + str(pygame.time.get_ticks())
    scale = pygame.transform.scale(load,(width,height))
    print "scaled: " + str(pygame.time.get_ticks())
    print "before append"
    object_list.append(scale)


    last_image_number = image_count
    
    image_count = image_count + 1

    
    print "after append" + str(pygame.time.get_ticks())
    print "added to object_list: " + str(len(object_list))
    print "end of LoadImageToObjectList"
    
    pygame.display.update()

    print "sent to google drive: " + image_name

    
def LoadImageObjectToScreen(image):
    #load the image object from the list to the screen
    
    print "begin LoadImageObjectToScreen"
    
    print "before load: " + str(pygame.time.get_ticks())
    screen.blit(image,(0,0))
    print "added to screen: " + str(pygame.time.get_ticks())
    pygame.display.update()
    
    print "end LoadImageObjectToScreen"
    

def FlashLEDs(iterations):
    #flashes LED for iterations
    index = 0

    while(index<iterations):
        print("flashing LEDs")
        GPIO.output(23,True)
        sleep(flash_time)
        GPIO.output(23,False)
        sleep(flash_time)
        index = index + 1

def DrawMetrics():
    #draws program metrics to the screen, to time how fast updating is going
    
    fps = float(index)/float(pygame.time.get_ticks()/1000)

    #text background layer, overwritten on every frame
    screen.blit(backgroundSurface,(5,(height-20)))

    #add fps text
    screen.blit(pygame.font.SysFont("freeserif",20,bold=0).render("{0:.2f}".format(fps) + " frames per second", 1, white),(10,(height-20)))

    #add index text
    screen.blit(pygame.font.SysFont("freeserif",20,bold=0).render("index: " + str(index), 1, white),(300,(height-20)))

    #add photos taken text
    screen.blit(pygame.font.SysFont("freeserif",20,bold=0).render("photos taken: " + str(photos_taken), 1, white),(450,(height-20)))# + ":" + str(take_a_picture)
                                                                                            
    pygame.display.update()

def DrawPreview():
    # draws the preview image from the camera onto the screen
    global last_preview
    
    p = sub.Popen(get_preview_command,stdout=sub.PIPE,stderr=sub.PIPE,shell=True)
    
    p.wait()#must wait until the image returns or the images never get fully loaded
    
    image = pygame.image.load("preview.jpg").convert_alpha()

    #position lower right preview image
    screen.blit(image,((width-320),(height - 240)))
    
    pygame.display.update()

    last_preview = image#stores last to make transitions look less choppy 
        
def PrevPicture():
    #draws the prev picture in the list from the object list
    global current_image
    global in_process

    print "PrevPicture"

    if not in_process:
        in_process = True

        FlashLEDs(1)

        current_image = current_image - 1
        
        if current_image < 0:
            current_image = (len(object_list)-1)

        DrawCenterMessage("LOADING PREV IMAGE: " + str(current_image),550,70,((width/2)-220),((height)-100))

        LoadImageObjectToScreen(object_list[current_image])

        RenderOverlay()
        
        in_process = False

    print "end PrevPicture"

def NextPicture():
    #draws the prev picture in the list from the object list
    global current_image
    global in_process

    print "NextPicture"

    if not in_process:
        in_process = True

        FlashLEDs(1)

        current_image = current_image + 1
        
        if current_image > (len(object_list)-1):
            current_image = 0

        DrawCenterMessage("LOADING NEXT IMAGE: " + str(current_image),550,70,((width/2)-220),((height)-100))
            
        LoadImageObjectToScreen(object_list[current_image])

        screen.blit(last_preview,((width-320),(height - 240)))

        RenderOverlay()

        in_process = False

    print "end NextPicture"

def LastPicture():
    #draws the last picture in the list to the screen
    global current_image
    global in_process

    print "LastPicture"

    if not in_process:
        in_process = True

        FlashLEDs(1)

        DrawCenterMessage("LOADING LAST TAKEN: " +str(last_image_number),600,70,((width/2)-220),((height)-100))

        LoadImageObjectToScreen(object_list[last_image_number])

        RenderOverlay()

        in_process = False
    
    print "end LastPicture"
    

def GetDateTimeString():
    #format the datetime for the time-stamped filename
    dt = str(datetime.datetime.now()).split(".")[0]
    clean = dt.replace(" ","_").replace(":","_")
    return clean

def DrawCenterMessage(message,width,height,x,y):
    #displays notification messages onto the screen

    backgroundCenterSurface = pygame.Surface((width,height))#size
    backgroundCenterSurface.fill(black)

    screen.blit(backgroundCenterSurface,(x,y))#position
    screen.blit(pygame.font.SysFont("freeserif",40,bold=1).render(message, 1, white),(x+10,y+10))
    pygame.display.update()
    

def FlashLEDs(max_iterations):
    #flash red led (GPIO pin 23)
    index = 0
    
    while(index<max_iterations):
        print("flashing LEDs")
        GPIO.output(23,True)
        sleep(flash_time)
        GPIO.output(23,False)
        sleep(flash_time)
        index = index + 1

def LoadNewImage():
    # after new image has been downloaded from the camera
    # it must be loaded into the object list and displayed on the screen
    global waiting_on_download
    global image_count
    global last_image_number
    global current_image

    DrawCenterMessage("TRANFERRING PICTURE",550,70,((width/2)-220),((height/2)-2))

    FlashLEDs(1)

    print "start LoadNewImage: " + str(pygame.time.get_ticks())
    capture = pygame.transform.scale(pygame.image.load(last_image_taken).convert_alpha(),(width,height))
    print "capture transformed: " + str(pygame.time.get_ticks())

    DrawCenterMessage("LOADING IMAGE",550,70,((width/2)-220),((height/2)-2))
    
    screen.blit(capture,(0,0))
    object_list.append(capture)

    last_image_number = image_count
    current_image = last_image_number
    image_count = image_count + 1

    print "capture added to screen: " + str(pygame.time.get_ticks())

    #-------------------------------------------------------------
    # ONLY UNCOMMENT THE NEXT LINE OF CODE IF YOU HAVE CONFIGURED 
    # upload.py TO WORK WITH YOUR GOOGLE DRIVE ACCOUNT
    #os.system("sudo python upload.py " + last_image_taken)
    #-------------------------------------------------------------
    
    FlashLEDs(1)

    waiting_on_download = False
        

def TakePicture():
    # executes the gphoto2 command to take a photo and download it from the camera
    global change_ticks
    global take_a_picture
    global photos_taken
    global last_image_taken
    global waiting_on_download

    FlashLEDs(1)
    take_a_picture = False
    
    print "taking picture"

    DrawCenterMessage("TAKING PICTURE",400,70,((width/2)-220),((height/2)-2))

    last_image_taken = "images/capture" + GetDateTimeString() + ".jpg"
    
    take_pic_command = "gphoto2 --capture-image-and-download --filename " + last_image_taken + " --force-overwrite"

    print "command given: " + str(pygame.time.get_ticks())

    #executes command below
    p = sub.Popen(take_pic_command,stdout=sub.PIPE,stderr=sub.PIPE,shell=True)

    DrawCenterMessage("SMILE :)",400,70,((width/2)-220),((height/2)-2))

    #starts looking for the saved downloading image name
    waiting_on_download = True

    photos_taken = photos_taken + 1
    
    change_ticks = pygame.time.get_ticks() + 30000 #sets a 30 second timeout before the slideshow continues
    


#***************END FUNCTIONS******************

# drops other possible connections to the camera
# on every restart just to be safe

os.system("sudo pkill gvfs")
os.environ['SDL_VIDEO_WINDOW_POS'] = "0,0"

app_name = "Raspberry Pi Photobooth v3"

print app_name + " started"

sleep(2)


GPIO.setmode(GPIO.BCM)

#INPUT FROM RECEIVER
GPIO.setup(17,GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(22,GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(24,GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(25,GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
#LED
GPIO.setup(23,GPIO.OUT, False)

FlashLEDs(1)

GPIO.add_event_detect(22,GPIO.RISING,callback=DPressed,bouncetime=bounceMillis)
GPIO.add_event_detect(17,GPIO.RISING,callback=CPressed,bouncetime=bounceMillis)
GPIO.add_event_detect(24,GPIO.RISING,callback=BPressed,bouncetime=bounceMillis)
GPIO.add_event_detect(25,GPIO.RISING,callback=APressed,bouncetime=bounceMillis)

white = pygame.Color(255,255,255)
black = pygame.Color(0,0,0)

pygame.init()
pygame.display.set_caption(app_name)

#screen = pygame.display.set_mode((width,height))#NOT FULLSCREEN
screen = pygame.display.set_mode((width,height),pygame.FULLSCREEN)#FULLSCREEN

#button
take_pic_button = pygbutton.PygButton(((width-80),50,80,30), "take pic")

#button
quit_button = pygbutton.PygButton(((width-160),50,80,30), "quit")


#bottom level, to cover previous frames
backgroundSurface = pygame.Surface(((width-650),28))
backgroundSurface.fill(black)

#bottom level, to cover previous frames
backgroundCenterSurface = pygame.Surface((400,70))#size
backgroundCenterSurface.fill(black)

get_preview_command = "gphoto2 --capture-preview --filename preview.jpg --force-overwrite"

DrawPreview()

file_list = glob.glob("/home/pi/photobooth/images/*.jpg")

print "files in folder: " + str(len(file_list))

index = 0
for file in file_list:
    print file
    DrawCenterMessage("LOADING: " + str(index + 1) + "/" +str(len(file_list)),500,70,((width/2)-220),((height)-100))

    #REMOVE THIS RESTRICTION AFTER TESTING
    if index < 20: #REMOVE LATER<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
        LoadImageToObjectList(file)
        NextPicture()
    
    index = index+1

print "START LOOP"

try:
    while(continue_loop):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                print "quiting..."
                continue_loop = False

            if 'click' in take_pic_button.handleEvent(event):
                TakePicture()
                
            if 'click' in quit_button.handleEvent(event):
                print "quiting..."
                continue_loop = False

        if waiting_on_download and os.path.isfile(last_image_taken):
            print "found file: " + last_image_taken

            LoadNewImage()

        if change_ticks  < pygame.time.get_ticks():
            print "Change"
            NextPicture()

            change_ticks = pygame.time.get_ticks() + 10000 #10 seconds and then flip to the next image

        #preview
        DrawPreview()
        DrawMetrics()

        index = index +1

        sleep(delay_time)
        
except:
    GPIO.cleanup()
    print "EXCEPTION"

print "process complete"
pygame.quit()
GPIO.cleanup()




