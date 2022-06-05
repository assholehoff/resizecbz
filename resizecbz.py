#!/usr/bin/env python3

"""Resize images inside CBZ (Comic Book Zip) files so that the file is smaller.
As a bonus the images should also load faster in your favorite CBZ reader"""

import os
import sys
import io
import glob
import argparse
import configparser
import zipfile
from PIL import Image

def appendToErrorLog(text):
    """Append text to error log file"""
    # https://stackoverflow.com/questions/230751/how-can-i-flush-the-output-of-the-print-function-unbuffer-python-output
    print(text, flush=True)
    # Must open in text mode or there will be an error:
    # TypeError: a bytes-like object is required, not 'str'
    #
    # https://docs.python.org/3/library/functions.html#open
    # When writing output to the stream if newline is None, any '\n' characters
    # written are translated to the system default line separator, os.linesep.
    # If newline is '' or '\n', no translation takes place.
    with open("resizecbz.error.log", 'at',
              newline='', encoding='utf8') as output:
        output.write(text)
        output.write('\n')

def resize(inputZip, outputZip, resizeLandscape, resizePortrait, rotateLandscape):
    """Resize images inside inputZip and save the new images into outputZip"""
    infoList = inputZip.infolist()
    i = 1
    total = len(infoList)

    if rotateLandscape.lower() == 'left':
        angle = 90
        resizeLandscape = resizePortrait
    elif rotateLandscape.lower() == 'right':
        angle = 270
        resizeLandscape = resizePortrait
    elif rotateLandscape.lower() == 'none':
        angle = 0
    else:
        angle = 0

    for info in infoList:
        filename = info.filename
        _, ext = os.path.splitext(filename)
        if not ext.lower() in (".jpg", ".jpeg", ".png", ".gif", ".webp"):
            outputZip.writestr(info, inputZip.read(filename))
            continue

        with Image.open(inputZip.open(filename)) as img:
            # https://stackoverflow.com/questions/29367990/what-is-the-difference-between-image-resize-and-image-thumbnail-in-pillow-python
            # Note: No shrinkage will occur unless ONE of the dimension is
            #       bigger than 1080. Aspect ratio is always kept
            #
            # https://pillow.readthedocs.io/en/stable/handbook/concepts.html#concept-filters
            #           Performance    Downscale Quality
            # BOX       ****           *
            # BILINEAR  ***            *
            # HAMMING   ***            **
            # BICUBIC   **             ***
            # LANCZOS   *              ****
            #
            # ANTIALIAS is a alias for LANCZOS for backward compatibility
            if img.size[0] > img.size[1]:
                out = img.rotate(angle, expand=True, fillcolor=None)
                out.thumbnail(resizeLandscape, Image.Resampling.LANCZOS)
                # out.show()
            else:
                out = img
                out.thumbnail(resizePortrait, Image.Resampling.LANCZOS)
            print(f"{i}/{total} {img.format} {img.size}->{out.size} {filename}")
            i = i + 1
            buffer = io.BytesIO()
            out.save(buffer, format=img.format)
            outputZip.writestr(info, buffer.getvalue())
            sys.stdout.flush()
            # output.getvalue()
            # img.show()


def resizeZippedImages(inputPath, outputPath, configParameters):
    """Resize images in file inputPath and save the new images in outputPath"""
    print(f"Resizing: {inputPath} -> {outputPath}")
    value = int(configParameters['resize_landscape'])
    resizeLandscape = (value, value)
    value = int(configParameters['resize_portrait'])
    resizePortrait = (value, value)
    rotateLandscape = configParameters['rotate_landscape']
    tempPath = outputPath + ".0bd15818604b995cd9c00825a4c692d5d.temp"
    try:
        directory, _ = os.path.split(outputPath)
        if directory and not os.path.isdir(directory):
            os.makedirs(directory)
        with zipfile.ZipFile(inputPath) as inZip:
            with zipfile.ZipFile(tempPath, 'w', zipfile.ZIP_STORED) as outZip:
                resize(inZip, outZip, resizeLandscape, resizePortrait, rotateLandscape)
            os.rename(tempPath, outputPath)
    except ValueError as err:
        appendToErrorLog(f"{inputPath}: {err}")
    except BaseException as err:
        # stackoverflow.com/questions/7160983/catching-all-exceptions-in-python
        #
        # https://docs.python.org/3/whatsnew/3.8.html
        # f-strings support = for self-documenting expressions and debugging
        # An f-string such as f'{expr=}' will expand to the text of the expr,
        # an equal sign, then the representation of the evaluated expression
        appendToErrorLog(f"{inputPath}: Unexpected {err}, {type(err)}")
        if os.path.exists(tempPath):
            os.remove(tempPath)
        if os.path.exists(outputPath):
            os.remove(outputPath)
        raise

def resizeCbz(path, configParameters):
    """resize the CBZ path with configuration specified in configParameters"""
    if not os.path.isfile(path):
        raise ValueError(f"{path} is not a file")

    name, ext = os.path.splitext(path)
    if int(configParameters['ext_zip_or_cbz']) != 0:
        if ext.lower() not in (".cbz", ".zip"):
            # Just print a warning without calling appendToErrorLog,
            # so that user can specify directory/* to resize
            # all the .cbz and .zip files in there.
            print(f"{path} does not have extension .cbz or .zip")
            return

    resizedFileExt = configParameters['resized_file_ext']
    if not resizedFileExt.startswith('.'):
        resizedFileExt = '.' + resizedFileExt
        #raise ValueError(f"resized_file_ext({resizedFileExt}) " +
        #                 "does not start with period")
    resizedFileExt = resizedFileExt + ext

    if path.endswith(resizedFileExt):
        raise ValueError(f"{path} has extension same ext({resizedFileExt})")

    outputPath = name + resizedFileExt
    outputDirectory = configParameters['output_directory']
    if outputDirectory:
        outputPath = os.path.join(outputDirectory,
                                  os.path.basename(outputPath))

    if os.path.exists(outputPath):
        # Not an error, just give a warning
        print(f"output {outputPath} already exists")
    else:
        resizeZippedImages(path, outputPath, configParameters)

def readConfigurationFile(arg0):
    """Read configuration file from a series of possible directories"""
    cmdDirectory, _ = os.path.split(arg0)
    home = os.path.expanduser("~")
    homeConfig = os.path.join(home, ".config")
    homeConfigApp = os.path.join(homeConfig, "resizecbz")
    configFilename = "resizecbz.cfg"
    path = None

    # print(f"cmdDirectory({cmdDirectory})")
    config = configparser.ConfigParser()
    configParameters = None
    for directory in os.curdir, homeConfigApp, homeConfig, home, cmdDirectory:
        path = os.path.abspath(os.path.join(directory, configFilename))
        # print(f"Trying to open config file {path}")
        if os.path.exists(path):
            with open(path, encoding='utf8') as file:
                config.read_file(file)
                configParameters = config['resize.cbz']
                # print(f'Reading parameters from "{path}": ')
                break

    if not configParameters:
        # Create a sample config file so that user can change it
        config['resize.cbz'] = {}
        configParameters = config['resize.cbz']
        # Output directory can be an absolute or relative path.
        # If set to None or '' then the resized files will be
        # in the same directory as the source
        configParameters['output_directory'] = 'resized'

        # Play around with these two parameters to to get the size that is most
        # pleasing for your eyes with the display.  In general you want them
        # to be a bit larger than your display so that there is no upscaling.
        #
        # If you are using a tablet (or any device that can be rotated to
        # display in # portrait mode) then you should set both of them to
        # the same value.
        # For example, on a older tablet with only a 1080x768 resolution both
        # values should be set to (1080, 1080) or (1366, 1366).
        # Obviously larger values means a larger file size
        #
        # Iriver Story HD has a resolution of 1024x768
        configParameters['resize_landscape'] = '768'
        configParameters['resize_portrait'] = '1024'

        # Rotate landscape (double) pages; RIGHT (CW), LEFT (CCW) or NONE
        configParameters['rotate_landscape'] = 'right'

        # Can be anything, but must start with '.' and must end with '.cbz'
        configParameters['resized_file_ext'] = '.rs'
        # By default, will only process files with extension ".zip" or ".cbz"
        configParameters['ext_zip_or_cbz'] = '1'

        if os.name == 'nt':
            # For Windows, create sample in the app's directory
            parentDir = cmdDirectory
        else:
            # For Linux/Mac, create in ~/config/xxx if it exits, else in ~/
            if os.path.isdir(homeConfig):
                parentDir = homeConfigApp
            else:
                parentDir = home

        # print(f"configuration file parent: {parent}")
        if parentDir and not os.path.isdir(parentDir):
            os.makedirs(parentDir)
        samplePath = os.path.abspath(os.path.join(parentDir,
                                                  configFilename + ".sample"))
        print(f'samplePath: "{samplePath}"')
        if not os.path.exists(samplePath):
            print(f"Create sample config file {samplePath}")
            with open(samplePath, 'w', encoding='utf8') as output:
                config.write(output)
        print(f"Rename {samplePath} to {configFilename}\n" +
              "and edit it if you want to change the default values\n" +
              "Flags always override config file parameters.")

    return configParameters, path

def makeWide(formatter, width=120, hmax=20):
    """Return a wider HelpFormatter, if possible."""
    # https://stackoverflow.com/questions/5462873/control-formatting-of-the-argparse-help-argument-list
    try:
        args = {'width': width, 'max_help_position': hmax}
        formatter(None, **args)
        return lambda prog: formatter(prog, **args)
    except TypeError:
        warnings.warn("argparse help formatter failed, falling back")
        return formatter

def parseArguments(args, configParameters):
    """Parse arguments for flags and filenames, show help"""
    newConfigParameters = configParameters
    parser = argparse.ArgumentParser(
                        formatter_class=makeWide(argparse.HelpFormatter, width=120, hmax=28),
                        prog = 'resizecbz',
                        description = 'Resize all pages in a CBZ. Optionally rotate landscape images.',
                        epilog = 'filename can contain wildcards, such as * or ?'
    )
    parser.add_argument('-w', '--resolution', help='maximum resolution to scale down to, can be a single value or a resolution in the form \'1024x768\' or \'768x1024\'', metavar='res')
    parser.add_argument('-r', '--rotation', choices=['left', 'right', 'none'], help='rotate landscape images 90°, valid values are \'right\', \'left\' or \'none\'', metavar='rot')
    parser.add_argument('-d', '--directory', help='the directory to put resized files in', metavar='dir')
    parser.add_argument('-e', '--extension', help='will be appended to the filename before the extension \'filename.ext.cbz\'', metavar='ext')
    parser.add_argument('-u', '--unsafe', action='store_true', help='disable file extension check')
    parser.add_argument('filename', nargs='*', help='file(s) to process')

    args = parser.parse_args()
    filename = args.filename
    # print('filename:', args.filename)

    if not args.resolution is None:
        if not args.resolution.isdigit():
            res = args.resolution.split('x')
            if int(res[0]) > int(res[1]):
                newConfigParameters['resize_portrait'] = res[0]
                newConfigParameters['resize_landscape'] = res[1]
            else:
                newConfigParameters['resize_portrait'] = res[1]
                newConfigParameters['resize_landscape'] = res[0]
        else:
            newConfigParameters['resize_portrait'] = args.resolution
            newConfigParameters['resize_landscape'] = args.resolution

    if not args.rotation is None:
        newConfigParameters['rotate_landscape'] = args.rotation

    if not args.directory is None:
        newConfigParameters['output_directory'] = args.directory

    if not args.extension is None:
        newConfigParameters['resized_file_ext'] = args.extension

    if args.unsafe:
        newConfigParameters['ext_zip_or_cbz'] = '0'

    return newConfigParameters, filename

def printConfig(configfile, configParameters):
    if os.path.exists(configfile):
        print(f"Using parameters from {configfile}:")
        for key in configParameters:
            print(f"{key} = {configParameters[key]}")
    else:
        print(f"No configuration file found. Using default parameters:")

if __name__ == '__main__':

    def main(argv):
        """main(arg)"""
        # Turn off "DecompressionBombWarning:
        # Image size (xxxxpixels) exceeds limit..."
        Image.MAX_IMAGE_PIXELS = None
        arg0 = argv[0]
        configParameters, configfile = readConfigurationFile(arg0)
        configParameters, filename = parseArguments(argv, configParameters)
        printConfig(configfile, configParameters)

        # for key in configParameters:
        #     print(f"{key}={configParameters[key]}")

        if len(filename) > 0:
            for x in filename[0:]:
                for path in glob.glob(x) if '*' in x or '?' in x else [x]:
                    try:
                        resizeCbz(path, configParameters)
                    except ValueError as err:
                        appendToErrorLog(f"{path}: {err}")
        else:
            cmd = os.path.basename(arg0)
            print(f"\nRun {cmd} --help for more information.")

main(sys.argv)