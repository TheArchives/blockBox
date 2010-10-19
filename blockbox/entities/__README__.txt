To those interested in developing entities:

Entities can be excluded from being creatable by player by being added to the unselectableentities list in _init.py.

Try to avoid defining any functions or using the return statment in any of your entity files. Return statments cause errors, and functions won't use variables like you might expect.

All files with the .py extension and no _ are considered entities. The events that occur at selection (when you type /entity <entityname>) can be set to something other than default (entityselected = entityname) with a file named yourentity_select.py (yourentity being any entity you have defined with a file like yourentity.py). This for if you want to set up an input structure like with var or neon entities. You can also set the creation events to something other than default (entitylist.append([self.var_entityselected,(x,y,z),8,8])
self.client.sendServerMessage("entity created") through a file named yourentity_create.py.

Aliases can be set with files named yourentity_aliases.txt. These will be set to point to the same logic, but they can use their own select and create code. Note that as a result, they will not use the base entities create and select .py files.

Finally, try to avoid huge amounts of block placements or complex operations for each logic pass of your entity, otherwise your entity could cause lag. Also, you can try to prevent some lag by increasing the delay between logic passes (in the creation line (ex: entitylist.append([self.var_entityselected,(x,y,z),8,8])) change the third and fourth variables (where the 8's are in the example) to a larger number).