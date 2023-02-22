# png_to_gif.py
#
# A python script run OUTSIDE of Fusion 360 by a shell call during
# gif.createGif().  See notes in gif.py about how and why I use
# an external python interpreter for this.


import os, sys
import imageio.v2 as imageio

png_folder = ''
remove_pngs = False

#-------------------------------
# process command line arguments
#--------------------------------

if len(sys.argv) < 2 or len(sys.argv) > 3:
	print("\nerror: incorrect number of arguments\n")
	count = 0
	for arg in sys.argv:
		print("arg[" + str(count) + ']="' + sys.argv[count] + '"')
		count += 1
	sys.exit()
png_folder = sys.argv[1]
if len(sys.argv) > 2:
	remove_pngs = (sys.argv[2] == 'remove_pngs')
print("png_to_gif(" + png_folder + ")  remove_pngs = " + str(remove_pngs))


#-----------------------------------
# find all the pngs in the folder
#-----------------------------------
# exit if none found

highest_gif = -1
pngs = []

with os.scandir(png_folder) as entries:
	for entry in entries:
		if entry.is_file():
			# print(entry.name)
			if entry.name.endswith('.png'):
				pngs.append(png_folder + "\\" + entry.name)
			elif entry.name.endswith('.gif'):
				# print("gif " + entry.name)
				num = int(entry.name[:6])
				if num > highest_gif:
					highest_gif = num

if not len(pngs):
	print("\nerror: No png files found in " + png_folder + "\n")
	sys.exit()

print("found " + str(len(pngs)) + " pngs  highest_gif=" + str(highest_gif))


#----------------------------------
# create gif filename
#----------------------------------

highest_gif += 1
gif_filename = str(highest_gif)
i = len(gif_filename)
while i<6:
	i += 1
	gif_filename = '0' + gif_filename
gif_filename = png_folder + "\\" + gif_filename + ".gif"
print("gif_filename=" + gif_filename)


#--------------------------------------
# open the images and create the gif
#--------------------------------------

images = []
pngs.sort()
for png in pngs:
	# print("png=" + png)
	rslt = imageio.imread(png)
	images.append(rslt)
imageio.mimsave(gif_filename, images, duration = 0.04)


#--------------------------------------
# remove the pngs
#--------------------------------------

if remove_pngs:
	for png in pngs:
		os.unlink(png)

print("success: png_to_gif.py proccessed " + str(len(pngs)) + " pngs into " + gif_filename)
