# blockBox is Copyright 2009-2010 of the Archives Team, the iCraft Team, and the blockBox team.
# blockBox is licensed under the Creative Commons by-nc-sa 3.0 UnPorted,
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

from twisted.internet import reactor
from blockbox.plugins import ProtocolPlugin
from blockbox.decorators import *
from blockbox.constants import *
import math
from random import choice

class LinePlugin(ProtocolPlugin):
	
	commands = {
		"lbook": "commandLbook",
		"rec_axiom": "commandRec_Axiom",
		"rec_production": "commandRec_Production",
		"lsystem":"commandLsystem",
	}

	def gotClient(self):
		self.var_production = {}

	@info_list
	def commandLbook(self, parts, byuser, overriderank):
		"/lbook pagenumber - Guest\nExplains lsystem in book form."
		if len(parts) > 1:
			if parts[1].lower() == "1":
				self.client.sendServerMessage("lbook [Page 1 of 12]")
				self.client.sendSplitServerMessage("lsystem is a command system that makes use of a virtual drawer that is commanded by a series of characters. It theoretically can build anything.")
			elif parts[1].lower() == "2":
				self.client.sendServerMessage("lbook [Page 2 of 12]")
				self.client.sendSplitServerMessage("F: makes the drawer move forward while drawing a line of blocks; A: also makes the drawer move forward while drawing a line of blocks; B: makes the drawer move backward while drawing a line of blocks; G: makes the drawer move forward without drawing a line of blocks; V: makes the drawer move backward without drawing a line of blocks")
			elif parts[1].lower() == "3":
				self.client.sendServerMessage("lbook [Page 3 of 12]")
				self.client.sendSplitServerMessage("+ and -: rotates the drawer in different directions in the zx plane (plane parallel to the ground); < and >: rotates the drawer in different directions in the yz plane; { and }: rotates the drawer in different directions in the xy plane")
			elif parts[1].lower() == "4":
				self.client.sendServerMessage("lbook [Page 4 of 12]")
				self.client.sendSplitServerMessage("T : changes the block to the block indicated by the integer (from 0 to 49) that follows (example T13); N and M : these dont do anything, they are only used in replacement")
			elif parts[1].lower() == "5":
				self.client.sendServerMessage("lbook [Page 5 of 12]")
				self.client.sendSplitServerMessage("You type '/rec_axiom' then a phrase of the characters to record the phrase the drawer will reference. (example: '/rec_axiom FGF+F') This initial phrase is called the axiom. You place two blocks, the first determines where the drawer starts and the second determines where it will be aimed toward at first.")
			elif parts[1].lower() == "6":
				self.client.sendServerMessage("lbook [Page 6 of 12]")
				self.client.sendSplitServerMessage("This is the system that allows you to replace characters in the reference phrase in order to create fractals, this includes trees. To give the system a phrase to replace a certain character with you type '/rec_production item productionrecipe' the item is the character to replace and the productionrecipe is the phrase to replace it with. (example: '/rec_production N F+FN')")
			elif parts[1].lower() == "7":
				self.client.sendServerMessage("lbook [Page 7 of 12]")
				self.client.sendSplitServerMessage("You can repeat this for any other characters you want replaced. Only the T character and numbers  can not be replaced. You can of course reassign characters to different replacements individually, but, for convienience, you can type '/rec_production reset' to clear all entries.")
			elif parts[1].lower() == "8":
				self.client.sendServerMessage("lbook [Page 8 of 12]")
				self.client.sendSplitServerMessage("You type '/lsystem blocktype standarddistance zxrotation yzrotation xyrotation level' to make the lsystem. The standarddistance is the distance (1 = the distance for an edge of a block) that the drawer travels for each F,A,B,G,V (it can be a decimal too, like 2.5 or 0.25).")
			elif parts[1].lower() == "9":
				self.client.sendServerMessage("lbook [Page 9 of 12]")
				self.client.sendSplitServerMessage("For the rotation entries each refers to how far each +,-,<,>,{,} rotates the drawer in it's respective plane. Finally the level is an integer from 0 to 5, it specifies how many times to run the replacements of the production on the reference phrase.")
			elif parts[1].lower() == "10":
				self.client.sendServerMessage("lbook [Page 10 of 12]")
				self.client.sendSplitServerMessage("(example If you had an axiom of F, and a productionrecipe for F of FF, a level of zero would yeild a reference phrase F, one: FF, two: FFFF). If entered properly the lsystem will start being made. A level of five, depending on the production, could take awile.")
			elif parts[1].lower() == "11":
				self.client.sendServerMessage("lbook [Page 11 of 12]")
				self.client.sendSplitServerMessage("You can use '//rec_axiom' to extend an existing axiom phrase. (example You have an axiom phrase of FGF, you use //rec_axiom {GT16F, this makes it FGF{GT16F)")
			elif parts[1].lower() == "12":
				self.client.sendServerMessage("lbook [Page 12 of 12]")
				self.client.sendSplitServerMessage("In production recipies you have the option of giving multiple phrases for an item(character), to do so you can do a '/rec_production item phrase,phrase,etc' and use '//rec_production item phrase,phrase,etc' to add more phrases for it. The lsystem will randomly choose between these phrases for each replacement of the character.")
			else:
				self.client.sendServerMessage("There's no page for that.")
		else:
			self.client.sendServerMessage("You forgot to specify a page number.")

	@build_list
	@op_only
	def commandRec_Axiom(self, parts, byuser, overriderank):
		"/rec_axiom axiom - Op\nRecords an axiom for lsystems."
		if len(parts) != 2:
			self.client.sendSplitServerMessage("Please enter an axiom to save (use //rec_axiom to add to an existing axiom)")
		else:
			for item in parts[1]:
				if item != 'F' and item != 'B' and item != '[' and item != ']' and item != '+' and item != '-' and item != '<' and item != '>' and item != 'G' and item != 'V' and item != 'N' and item != 'M' and item != '{' and item != '}' and item != 'A' and not item.isdigit() and item != 'T':
					self.client.sendServerMessage("Please use only the characters F,A,B,[,],+,-,<,>,G,V,N,M,{,},T or numbers")
					return
			if parts[0] == '//rec_axiom':
				try:
					self.client.var_axiom = self.client.var_axiom + parts[1]
				except:
					self.client.sendServerMessage("You have not started recording an axiom yet")
					return
			else:
				self.client.var_axiom = parts[1]
			var_divisions64 = int(len(self.client.var_axiom)/64)
			self.client.sendServerMessage("The axiom has been recorded as:")
			for i in range(var_divisions64):
				self.client.sendServerMessage(self.client.var_axiom[i*64:(i+1)*64])
			self.client.sendServerMessage(self.client.var_axiom[var_divisions64*64:])

	@build_list
	@op_only
	def commandRec_Production(self, parts, byuser, overriderank):
		"/rec_production item production - Op\nRecords production recipes for lsystems."
		if len(parts) != 3:
			if len(parts) == 2:
				if parts[1] == 'reset':
					self.var_production = {}
					self.client.sendServerMessage("Your production recipes have been cleared")
					return
			self.client.sendServerMessage("Please enter an item and a production recipe for it to be")
			self.client.sendServerMessage("replaced with (type in 'reset' to reset all the recipes).")
			self.client.sendServerMessage("Use //rec_production to add additional recipe choices for")
			self.client.sendServerMessage("the item.")
		else:
			keyitem = parts[1]
			if keyitem != 'F' and keyitem != 'B' and keyitem != '[' and keyitem != ']' and keyitem != '+' and keyitem != '-' and keyitem != '<' and keyitem != '>' and keyitem != 'G' and keyitem != 'V' and keyitem != 'N' and keyitem != 'M' and keyitem != '{' and keyitem != '}' and keyitem != 'A':
					self.client.sendServerMessage("Please use only the characters F,B,A,[,],+,-,<,>,G,V,N,M,{,} for the key")
					return
			for item in parts[2]:
				if item != 'F' and item != 'B' and item != '[' and item != ']' and item != '+' and item != '-' and item != '<' and item != '>' and item != 'G' and item != 'V' and item != 'N' and item != 'M' and item != '{' and item != '}' and item != 'A' and not item.isdigit() and item != 'T' and item != ',':
					self.client.sendServerMessage("Please use only the characters F,B,A,[,],+,-,<,>,G,V,N,M,{,},T or numbers")
					self.client.sendServerMessage("(use commas between phrases to have it select randomly from them)")
					return
			if parts[0] == "//rec_production":
				self.var_production[keyitem] = self.var_production[keyitem] + parts[2].split(",")
			else:
				self.var_production[keyitem] = parts[2].split(",")
			self.client.sendServerMessage("The production recipe has been recorded as:")
			item_list = []
			for key in self.var_production:
				item_list.append(key + " : " + str(self.var_production[key]))
			self.client.sendServerList(item_list)

	@build_list
	@op_only
	def commandLsystem(self, parts, byuser, overriderank):
		"/lsystem blocktype standarddistance\nzxrotation yzrotation xyrotation level [x y z x2 y2 z2] - Op\nDraws an lsystem."
		try:
			axiom = self.client.var_axiom
			production = self.var_production
		except:
			self.client.sendServerMessage("Please use /rec_axiom first (and /rec_production if you")
			self.client.sendServerMessage("want to make a fractal.")
			return
		if len(parts) < 13 and len(parts) != 7:
			self.client.sendServerMessage("Please enter a blocktype, standarddistance(which is how far")
			self.client.sendServerMessage("the drawer will go per F, B, G, or V), the rotations are how")
			self.client.sendServerMessage("many degrees the drawer will rotate for each +,-,>,<,{,} along")
			self.client.sendServerMessage("it's respective axis and finally the level")
			self.client.sendServerMessage("(an integer between 0 and 5) which determines")
			self.client.sendServerMessage("how many times the characters in the production will be")
			self.client.sendServerMessage("replaced with their respective productionrecipe phrases.")
			self.client.sendServerMessage("Note that you must place two blocks.")
			self.client.sendServerMessage("The first block you place will determine where the drawer starts")
			self.client.sendServerMessage("and the second will determine where it initially points toward.")
		else:
			# Try getting the standarddistance
			try:
				standarddistance = float(parts[2])
			except:
				self.client.sendServerMessage("The standarddistance must be a real number")
				return
			# Try getting the zxrotation
			try:
				zxrotation = int(parts[3])
			except:
				self.client.sendServerMessage("The zxrotation must be an integer")
				return
			if zxrotation > 360 or zxrotation < 0:
				self.client.sendServerMessage("The zxrotation must be between 0 and 360 degrees")
				return
			# Try getting the yzrotation
			try:
				yzrotation = int(parts[4])
			except:
				self.client.sendServerMessage("The yzrotation must be an integer")
				return
			if yzrotation > 360 or yzrotation < 0:
				self.client.sendServerMessage("The yzrotation must be between 0 and 360 degrees")
				return
			# Try getting the xzrotation
			try:
				xyrotation = int(parts[5])
			except:
				self.client.sendServerMessage("The xyrotation must be an integer")
				return
			if xyrotation > 360 or xyrotation < 0:
				self.client.sendServerMessage("The xyrotation must be between 0 and 360 degrees")
				return
			# Try getting the level
			try:
				level = int(parts[6])
			except:
				self.client.sendServerMessage("The level must be an integer")
				return
			if level < 0 or level > 5:
				self.client.sendServerMessage("The level must be between 0 and 5")
				return
			# If they only provided the type argument, use the last two block places
			if len(parts) == 7:
				try:
					x, y, z = self.client.last_block_changes[1]
					x2, y2, z2 = self.client.last_block_changes[0]
				except IndexError:
					self.client.sendServerMessage("You have not clicked two corners yet.")
					return
			else:
				try:
					x2 = int(parts[7])
					y2 = int(parts[8])
					z2 = int(parts[9])
					x = int(parts[10])
					y = int(parts[11])
					z = int(parts[12])
				except ValueError:
					self.client.sendServerMessage("All parameters must be integers")
					return

			finalsequence = axiom
			for i in range(level):
				for key in production:
					numproductionsadded = 0
					for index in range(len(axiom)):
						productionchoice = choice(production[key])
						lengthofproduction = len(productionchoice)-1
						item = axiom[index]
						if item == key:
							finalsequence = finalsequence[:index+numproductionsadded*lengthofproduction] + productionchoice + finalsequence[index+numproductionsadded*lengthofproduction+1:]
							numproductionsadded += 1
					axiom = finalsequence

			num_movements = 0
			for item in finalsequence:
				if item == "F" or item == "B":
					num_movements += 1
					
					
			if self.client.isOwner():
				limit = 1000000000
			elif self.client.isSuperAdmin():
				limit = 7077888
			elif self.client.isAdmin():
				limit = 2097152
			elif self.client.isMod():
				limit = 262144
			elif self.client.isOp():
				limit = 21952
			else:
				limit = 4062
			# Stop them doing silly things
			if num_movements*standarddistance > limit:
				self.client.sendServerMessage("Sorry, that area is too big for you to use an lsystem on.")
				return
			world = self.client.world
			def generate_changes():
				# Try getting the block as a direct integer type.
				try:
					block = chr(int(parts[1]))
				except ValueError:
					# OK, try a symbolic type.
					try:
						block = chr(globals()['BLOCK_%s' % parts[1].upper()])
					except KeyError:
						self.client.sendServerMessage("'%s' is not a valid block type." % parts[1])
						return
				
				# Check the block is valid
				if ord(block) > 49:
					self.client.sendServerMessage("'%s' is not a valid block type." % parts[1])
					return
				pointsseparation = math.sqrt(math.pow((x2-x),2)+math.pow((y2-y),2)+math.pow((z2-z),2))
				drawer_orientationvector = ((x2-x)/pointsseparation,(y2-y)/pointsseparation,(z2-z)/pointsseparation)
				drawer_location = (float(x),float(y),float(z))
				savedlocations = []
				for index in range(len(finalsequence)):
					item = finalsequence[index]
					if item == "F":
						targetlocation = (drawer_location[0]+drawer_orientationvector[0]*standarddistance,drawer_location[1]+drawer_orientationvector[1]*standarddistance,drawer_location[2]+drawer_orientationvector[2]*standarddistance)
						var_x,var_y,var_z = drawer_location
						var_x2,var_y2,var_z2 = targetlocation
						drawer_location = targetlocation

						var_x = int(round(var_x))
						var_y = int(round(var_y))
						var_z = int(round(var_z))
						var_x2 = int(round(var_x2))
						var_y2 = int(round(var_y2))
						var_z2 = int(round(var_z2))
						try:
							steps = int(((var_x2-var_x)**2+(var_y2-var_y)**2+(var_z2-var_z)**2)**0.5)
							mx = float(var_x2-var_x)/steps
							my = float(var_y2-var_y)/steps
							mz = float(var_z2-var_z)/steps

							coordinatelist1 = []
							for t in range(steps+1):
								coordinatelist1.append((int(round(mx*t+var_x)),int(round(my*t+var_y)),int(round(mz*t+var_z))))
							coordinatelist2 = []
							for coordtuple in coordinatelist1:
								if coordtuple not in coordinatelist2:
									coordinatelist2.append(coordtuple)
						except:
							coordinatelist2 = []
						
						for coordtuple in coordinatelist2:
							i,j,k = coordtuple
							try:
								if not self.client.AllowedToBuild(i, j, k):
									self.client.sendServerMessage("You do not have permision to build here.")
									return
							except:
								pass
							var_override = True
							try:
								world[i, j, k] = block
								var_override = False
							except AssertionError:
								pass
							if not var_override:
								self.client.queueTask(TASK_BLOCKSET, (i, j, k, block), world=world)
								self.client.sendBlock(i, j, k, block)
							yield

					elif item == "A":
						targetlocation = (drawer_location[0]+drawer_orientationvector[0]*standarddistance,drawer_location[1]+drawer_orientationvector[1]*standarddistance,drawer_location[2]+drawer_orientationvector[2]*standarddistance)
						var_x,var_y,var_z = drawer_location
						var_x2,var_y2,var_z2 = targetlocation
						drawer_location = targetlocation

						var_x = int(round(var_x))
						var_y = int(round(var_y))
						var_z = int(round(var_z))
						var_x2 = int(round(var_x2))
						var_y2 = int(round(var_y2))
						var_z2 = int(round(var_z2))
						
						try:
							steps = int(((var_x2-var_x)**2+(var_y2-var_y)**2+(var_z2-var_z)**2)**0.5)
							mx = float(var_x2-var_x)/steps
							my = float(var_y2-var_y)/steps
							mz = float(var_z2-var_z)/steps

							coordinatelist1 = []
							for t in range(steps+1):
								coordinatelist1.append((int(round(mx*t+var_x)),int(round(my*t+var_y)),int(round(mz*t+var_z))))
							coordinatelist2 = []
							for coordtuple in coordinatelist1:
								if coordtuple not in coordinatelist2:
									coordinatelist2.append(coordtuple)
						except:
							coordinatelist2 = []
						
						for coordtuple in coordinatelist2:
							i,j,k = coordtuple
							try:
								if not self.client.AllowedToBuild(i, j, k):
									self.client.sendServerMessage("You do not have permision to build here.")
									return
							except:
								pass
							var_override = True
							try:
								world[i, j, k] = block
								var_override = False
							except AssertionError:
								pass
							if not var_override:
								self.client.queueTask(TASK_BLOCKSET, (i, j, k, block), world=world)
								self.client.sendBlock(i, j, k, block)
							yield
							
					elif item == "B":
						targetlocation = (drawer_location[0]-drawer_orientationvector[0]*standarddistance,drawer_location[1]-drawer_orientationvector[1]*standarddistance,drawer_location[2]-drawer_orientationvector[2]*standarddistance)
						var_x,var_y,var_z = drawer_location
						var_x2,var_y2,var_z2 = targetlocation
						drawer_location = targetlocation

						var_x = int(round(var_x))
						var_y = int(round(var_y))
						var_z = int(round(var_z))
						var_x2 = int(round(var_x2))
						var_y2 = int(round(var_y2))
						var_z2 = int(round(var_z2))
						
						try:
							steps = int(((var_x2-var_x)**2+(var_y2-var_y)**2+(var_z2-var_z)**2)**0.5)
							mx = float(var_x2-var_x)/steps
							my = float(var_y2-var_y)/steps
							mz = float(var_z2-var_z)/steps

							coordinatelist1 = []
							for t in range(steps+1):
								coordinatelist1.append((int(round(mx*t+var_x)),int(round(my*t+var_y)),int(round(mz*t+var_z))))
							coordinatelist2 = []
							for coordtuple in coordinatelist1:
								if coordtuple not in coordinatelist2:
									coordinatelist2.append(coordtuple)
						except:
							coordinatelist2 = []
						
						for coordtuple in coordinatelist2:
							i,j,k = coordtuple
							try:
								if not self.client.AllowedToBuild(i, j, k):
									self.client.sendServerMessage("You do not have permision to build here.")
									return
							except:
								pass
							var_override = True
							try:
								world[i, j, k] = block
								var_override = False
							except AssertionError:
								pass
							if not var_override:
								self.client.queueTask(TASK_BLOCKSET, (i, j, k, block), world=world)
								self.client.sendBlock(i, j, k, block)
							yield
					
					elif item == "G":
						drawer_location = (drawer_location[0]+drawer_orientationvector[0]*standarddistance,drawer_location[1]+drawer_orientationvector[1]*standarddistance,drawer_location[2]+drawer_orientationvector[2]*standarddistance)

					elif item == "V":
						drawer_location = (drawer_location[0]-drawer_orientationvector[0]*standarddistance,drawer_location[1]-drawer_orientationvector[1]*standarddistance,drawer_location[2]-drawer_orientationvector[2]*standarddistance)

					elif item == "+":
						rad_rotation = math.radians(zxrotation)
						drawer_orientationvector = (drawer_orientationvector[0]*math.cos(rad_rotation) - drawer_orientationvector[2]*math.sin(rad_rotation),drawer_orientationvector[1],drawer_orientationvector[0]*math.sin(rad_rotation) + drawer_orientationvector[2]*math.cos(rad_rotation))

					elif item == "-":
						rad_rotation = math.radians(-zxrotation)
						drawer_orientationvector = (drawer_orientationvector[0]*math.cos(rad_rotation) - drawer_orientationvector[2]*math.sin(rad_rotation),drawer_orientationvector[1],drawer_orientationvector[0]*math.sin(rad_rotation) + drawer_orientationvector[2]*math.cos(rad_rotation))

					elif item == ">":
						rad_rotation = math.radians(yzrotation)
						drawer_orientationvector = (drawer_orientationvector[0],drawer_orientationvector[1]*math.cos(rad_rotation) - drawer_orientationvector[2]*math.sin(rad_rotation),drawer_orientationvector[1]*math.sin(rad_rotation) + drawer_orientationvector[2]*math.cos(rad_rotation))
						
					elif item == "<":
						rad_rotation = math.radians(-yzrotation)
						drawer_orientationvector = (drawer_orientationvector[0],drawer_orientationvector[1]*math.cos(rad_rotation) - drawer_orientationvector[2]*math.sin(rad_rotation),drawer_orientationvector[1]*math.sin(rad_rotation) + drawer_orientationvector[2]*math.cos(rad_rotation))

					elif item == "[":
						savedlocations.append((drawer_location,drawer_orientationvector,block))
						
					elif item == "]":
						try:
							drawer_location,drawer_orientationvector,block = savedlocations.pop()
						except:
							print str(finalsequence)
							self.client.sendServerMessage("No saved location error ('[' but no ']')")
							return
					elif item == "N":
						pass
					elif item == "M":
						pass
					elif item == "{":
						rad_rotation = math.radians(xyrotation)
						drawer_orientationvector = (drawer_orientationvector[0]*math.cos(rad_rotation) - drawer_orientationvector[1]*math.sin(rad_rotation),drawer_orientationvector[0]*math.sin(rad_rotation) + drawer_orientationvector[1]*math.cos(rad_rotation),drawer_orientationvector[2])
					elif item == "}":
						rad_rotation = math.radians(-xyrotation)
						drawer_orientationvector = (drawer_orientationvector[0]*math.cos(rad_rotation) - drawer_orientationvector[1]*math.sin(rad_rotation),drawer_orientationvector[0]*math.sin(rad_rotation) + drawer_orientationvector[1]*math.cos(rad_rotation),drawer_orientationvector[2])
					elif item == "T":
						num = 0
						try:
							part1 = finalsequence[index+1]
						except:
							self.client.sendServerMessage("T must be followed by a number from 0 to 49.")
							return
						if not part1.isdigit():
							self.client.sendServerMessage("T must be followed by a number from 0 to 49.")
							return
						part2 = ""
						try:
							subpart2 = finalsequence[index+2]
							if subpart2.isdigit():
								part2 = subpart2
						except:
							pass
						num = int(part1 + part2)
						if not 0<=num<=49:
							self.client.sendServerMessage("T must be followed by a number from 0 to 49.")
							return
						block = chr(num)
					else:
						pass
			# Now, set up a loop delayed by the reactor
			block_iter = iter(generate_changes())
			def do_step():
				# Do 10 blocks
				try:
					for x in range(10):#1 blocks at a time, 10 blocks per tenths of a second, 100 blocks a second
						block_iter.next()
					reactor.callLater(0.01, do_step)  #This is how long(in seconds) it waits to run another 10 blocks
				except StopIteration:
					if byuser:
						self.client.sendServerMessage("Your lsystem just completed.")
					pass
			do_step()
