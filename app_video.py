'''
Refer to https://huggingface.co/spaces/dt/ascii-art/blob/main/app.py
'''

# Python code to convert an image to ASCII image.
import sys, random, argparse
import numpy as np
import math
import base64
from PIL import Image, ImageFont, ImageDraw
from moviepy.editor import *
from tqdm.auto import tqdm

import gradio as gr

# 70 levels of gray
gscale1 = "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\|()1{}[]?-_+~<>i!lI;:,\"^`'. "
 
# 10 levels of gray
gscale2 = '@%#*+=-:. '

font = ImageFont.load_default()
 
def getAverageL(image):
 
    """
    Given PIL Image, return average value of grayscale value
    """
    # get image as numpy array
    im = np.array(image)
    # get shape
    w,h = im.shape
 
    # get average
    return np.average(im.reshape(w*h))
 
def covertImageToAscii(input_img, cols, scale, moreLevels):
    """
    Given Image and dims (rows, cols) returns an m*n list of Images
    """
    # declare globals
    global gscale1, gscale2
 
    # open image and convert to grayscale
    image = input_img.convert('L')
 
    # store dimensions
    # store dimensions
    W, H = image.size[0], image.size[1]
 
    # compute width of tile
    w = W/cols
 
    # compute tile height based on aspect ratio and scale
    h = w/scale
 
    # compute number of rows
    rows = int(H/h)
 
    # check if image size is too small
    if cols > W or rows > H:
        print("Image too small for specified cols!")
        exit(0)
 
    # ascii image is a list of character strings
    aimg = []
    # generate list of dimensions
    for j in range(rows):
        y1 = int(j*h)
        y2 = int((j+1)*h)
 
        # correct last tile
        if j == rows-1:
            y2 = H
 
        # append an empty string
        aimg.append("")
 
        for i in range(cols):
 
            # crop image to tile
            x1 = int(i*w)
            x2 = int((i+1)*w)
 
            # correct last tile
            if i == cols-1:
                x2 = W
 
            # crop image to extract tile
            img = image.crop((x1, y1, x2, y2))
 
            # get average luminance
            avg = int(getAverageL(img))
 
            # look up ascii char
            if moreLevels:
                gsval = gscale1[int((avg*69)/255)]
            else:
                gsval = gscale2[int((avg*9)/255)]
 
            # append ascii char to string
            aimg[j] += gsval
     
    # return txt image
    return aimg


def colorizeTextImage(input_img, text_img):
    input_img = np.asarray(input_img)
    input_img = input_img.reshape((
        input_img.shape[0]//11, 
        11, 
        input_img.shape[1]//6, 
        6,
        3
    ))
    input_img = np.float32(input_img)
    text_img = np.asarray(text_img)
    text_img = text_img.reshape((
        input_img.shape[0], 
        11, 
        input_img.shape[2], 
        6, 
        3
    ))
    alpha = np.float32(text_img)[...,:1] / 255
    alpha[alpha < 0.125] = 0
    alpha[alpha >= 0.125] = 1
    out_img = input_img * alpha
    out_colors = out_img.sum((1,3), keepdims=True) / (alpha.sum((1,3), keepdims=True) + 1e-12)
    out_img = out_colors * alpha
    out_img = out_img.reshape((
        out_img.shape[0] * out_img.shape[1],
        out_img.shape[2] * out_img.shape[3],
        3
    ))
    out_img = np.clip(out_img, 0, 255)
    out_img = np.uint8(out_img)

    return out_img
 

def sepia(input_img, no_colors=False):
    input_img = Image.fromarray(input_img).convert('RGB')
    aimg = covertImageToAscii(input_img, 200, 6/11, True)
    blank_image = Image.new(mode="RGB", size=(len(aimg[0])*6, len(aimg)*11), color=(0, 0, 0))

    my_image = blank_image.copy()
    image_editable = ImageDraw.Draw(my_image)
    
    image_editable.text((0, 0), "\n".join(aimg), (255, 255, 255), font=font, spacing=0)
    if no_colors:
        return np.asarray(my_image)

    input_img_resize = input_img.resize((len(aimg[0])*6, len(aimg)*11), Image.BICUBIC)
    w, h = input_img.size
    scale = 200 * 6 / w
    w = 200 * 6
    h = int(round(h*scale))
    input_img = input_img.resize((200 * 6, h), Image.BICUBIC)
    input_img_resize.paste(input_img, (0, 0, w, h))
    input_img = input_img_resize

    my_image = colorizeTextImage(input_img, my_image)

    return my_image


def sepia_video(video_file, no_colors=False):
    clip = VideoFileClip(video_file)
    audioclip = clip.audio
    frames = int(clip.fps * clip.duration)
    imgs = []
    for i in tqdm(range(frames)):
        imgs.append(sepia(clip.get_frame(i/clip.fps), no_colors))
    video = ImageSequenceClip(imgs, fps=clip.fps)
    video = video.set_audio(audioclip)
    video.write_videofile("out.mp4", fps=clip.fps)

    return "out.mp4"

iface = gr.Interface(sepia_video, 
                     [gr.Video(format=None), gr.Checkbox(label="No Colors")], 
                     "video",
                     title = "Colorful ASCII Art",
                     description = "Convert an image to colorful ASCII art based on ascii character density. Click the first output text to download the generated svg.")

iface.launch()
