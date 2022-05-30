<style>
   h2 {
      margin-top: 26pt;
   }
</style>
# resizecbz-rf (rotate fork)
Python script to resize all images inside a CBZ (Comic Book Zip).\
This fork comes with some additions and defaults to better suit my iRiver Story HD.

The iRiver Story HD has a resolution of 768x1024. It does not allow for the landscape images (full spread of a book or magazine) in a CBZ to be rotated dynamically. (It will split the image in two pages, screwing with the page order if you read a comic printed from right to left.) This addition lets you rotate the landscape pages either left (ccw) or right (cw).

1. [Usage](#usage)
2. [Install and Dependencies](#install-and-dependencies)
3. [Configuration](#configuration)
4. [FAQ](#faq)

## Usage
---
```man
resizecbz [-w resolution] [-r rotation] [-d directory] [-e ext] [-u] [file ...]
```
`file` can contain wildcards such as ***.cbz**, **abc?.cbz**, etc.\
For example: `resizecbz collection1/*.cbz collection2/xyz*.cbz`

Any error will be logged into the file `resizecbz.error.log`

### Optional Arguments
` -w, --resolution` in the form of `768x1024`, `1024x768` or `1024` (providing only one value will set both horizontal and vertical maximum resolution to that value, use with readers capable of rotating images)\
` -r, --rotation` valid options are `right`, `left` or `none` (anything else than `right` or `left` translates to none, defaults to `right`)\
` -d, --directory` name of the directory to put the resized CBZ files in\
` -e, --extension` this string will be added to the filename before the CBZ extension\
` -u, --unsafe` do not check the file extension, use if your CBZ files are not ending in CBZ or ZIP

## Install and Dependencies
---
The script requires python 3 and the pillow module.

### macOS with [Homebrew](https://brew.sh)🍺
```shell
brew install python
python pip install pillow
```

I prefer put it somewhere in `$PATH` so I can invoke it as an ordinary command wherever.\
On macOS and BSD you can use `install(1)` to put it under `/usr/local/bin/` or similar.
```shell
sudo install -m 755 -o $USER -g bin resizecbz.py /usr/local/bin/resizecbz
```

## Configuration
---
You can control the maximum size of the images, the destination directory, and the extesion of the resized file via a configuration file.  A sample configuration file `resizecbz.cfg.sample` will be created the first time you run the script without any parameters. You can edit this file and then rename it to `resizecbz.cfg` and it will be loaded by the script.  You can put `resizecbz.cfg` in the directory where you run the script (so you can have a different resize parameters for each directory), the same directory as the script, in your home directory, or in `~/config/resizecbz`.

By default the maximum width in landscape mode is 768, and the maximum height in portrait mode is 1024, the directory is a subdirectory `resized` underneath the source directory, and the default extension is `rs.cbz`.

The program will only attempt to resize images in files that have the extension `.zip` or `.cbz`. All other files will be ignore. If you have a zip file with an extension other than `.zip` or `.cbz` then you have to either rename the file to have the right extension, or edit the config file and set `ext_zip_or_cbz = 0`.  But if you do that then you have to ensure that you only specify files that are actually zip files, else many errors will be generated when the script attemp to open files as a zip when you specify a general wildcard like `*.*`

## FAQ
---
### What differentiates this fork from the original?
Mostly minor details due to personal preference.
* `rotate_landscape = orientation` valid orientations are `right`, `left` and `none`. 
* removed the leading period in the config file name
* removed the txt extension on the log file
* adjusted default resolution to `768x1024` (iRiver Story HD)
* set default rotation to `right` (90° clockwise)
* added shebang to make script executable (I prefer to put it somewhere in `$PATH`)
* added flags to change settings at runtime