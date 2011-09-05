# blockBox is copyright 2009-2011 the Arc Team, the blockBox Team and other contributors.
# blockBox is licensed under the BSD 3-Clause Modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the blockBox Package.

VERSION = "v1.0.0 RBB (Really Buggy Beta) 1"

FORMAT_LENGTHS = {
    "b": 1,
    "a": 1024,
    "s": 64,
    "h": 2,
    "i": 4,
}

from format import Format

TYPE_INITIAL = 0
TYPE_KEEPALIVE = 1
TYPE_PRECHUNK = 2
TYPE_CHUNK = 3
TYPE_LEVELSIZE = 4
TYPE_BLOCKCHANGE = 5
TYPE_BLOCKSET = 6
TYPE_SPAWNPOINT = 7
TYPE_PLAYERPOS = 8
TYPE_NINE = 9
TYPE_TEN = 10
TYPE_PLAYERDIR = 11
TYPE_PLAYERLEAVE = 12
TYPE_MESSAGE = 13
TYPE_ERROR = 14
TYPE_SMP = 255

TYPE_FORMATS = {
    TYPE_INITIAL: Format("bssb"),
    TYPE_KEEPALIVE: Format(""),
    TYPE_PRECHUNK: Format(""),
    TYPE_CHUNK: Format("hab"),
    TYPE_LEVELSIZE: Format("hhh"),
    TYPE_BLOCKCHANGE: Format("hhhbb"),
    TYPE_BLOCKSET: Format("hhhb"),
    TYPE_SPAWNPOINT: Format("bshhhbb"),
    TYPE_PLAYERPOS: Format("bhhhbb"),
    TYPE_NINE: Format("bbbbbb"),
    TYPE_TEN: Format("bbbb"),
    TYPE_PLAYERDIR: Format("bbb"),
    TYPE_PLAYERLEAVE: Format("b"),
    TYPE_MESSAGE: Format("bs"),
    TYPE_ERROR: Format("s"),
    TYPE_SMP: Format(""),
}

TASK_BLOCKSET = 1
TASK_PLAYERPOS = 2
TASK_MESSAGE = 3
TASK_NEWPLAYER = 4
TASK_PLAYERLEAVE = 5
TASK_PLAYERDIR = 6
TASK_WORLDCHANGE = 7
TASK_ADMINMESSAGE = 8
TASK_WORLDMESSAGE = 9
TASK_ACTION = 10
TASK_SERVERMESSAGE = 11
TASK_PHYSICSON = 12
TASK_PHYSICSOFF = 13
TASK_FLUSH = 14
TASK_BLOCKGET = 15
TASK_STOP = 16
TASK_PLAYERCONNECT = 17
TASK_UNFLOOD = 18
TASK_FWATERON = 19
TASK_FWATEROFF = 20
TASK_PLAYERRESPAWN = 21
TASK_SERVERURGENTMESSAGE = 22
TASK_STAFFMESSAGE = 23
TASK_IRCMESSAGE = 24
TASK_AWAYMESSAGE = 25

COLOUR_BLACK = "&0"
COLOUR_DARKBLUE = "&1"
COLOUR_DARKGREEN = "&2"
COLOUR_DARKCYAN = "&3"
COLOUR_DARKRED = "&4"
COLOUR_DARKPURPLE = "&5"
COLOUR_DARKYELLOW = "&6"
COLOUR_GREY = "&7"
COLOUR_DARKGREY = "&8"
COLOUR_BLUE = "&9"
COLOUR_GREEN = "&a"
COLOUR_CYAN = "&b"
COLOUR_RED = "&c"
COLOUR_PURPLE = "&d"
COLOUR_YELLOW = "&e"
COLOUR_WHITE = "&f"

BLOCK_NOTHING = 0
BLOCK_NONE = 0
BLOCK_EMPTY = 0
BLOCK_AIR = 0
BLOCK_BLANK = 0
BLOCK_CLEAR = 0
BLOCK_ROCK = 1
BLOCK_ROCKS = 1
BLOCK_GRASS = 2
BLOCK_SOIL = 3
BLOCK_DIRT = 3
BLOCK_MUD = 3
BLOCK_BROWN = 3
BLOCK_GROUND = 3
BLOCK_STONE = 4
BLOCK_STONES = 4
BLOCK_COBBLESTONE = 4
BLOCK_COBBLESTONES = 4
BLOCK_COBBLE = 4
BLOCK_WOOD = 5
BLOCK_PLANK = 5
BLOCK_PLANKS = 5
BLOCK_BOARD = 5
BLOCK_BOARDS = 5
BLOCK_PLANT = 6
BLOCK_PLANTS = 6
BLOCK_SHRUB = 6
BLOCK_SHRUBS = 6
BLOCK_TREE = 6
BLOCK_TREES = 6
BLOCK_SAPPLING = 6
BLOCK_SAPLING = 6
BLOCK_SAPPLINGS = 6
BLOCK_SAPLINGS = 6
BLOCK_ADMINIUM = 7
BLOCK_OPCRETE = 7
BLOCK_ADMINCRETE = 7
BLOCK_DENSE = 7
BLOCK_HARDROCK = 7
BLOCK_HARDROCKS = 7
BLOCK_DENSE = 7
BLOCK_HARDEN = 7
BLOCK_ADMINBLOCK = 7
BLOCK_ADMINBLOCKS = 7
BLOCK_ADMIN_BLOCK = 7
BLOCK_ADMIN_BLOCKS = 7
BLOCK_HARD_ROCK = 7
BLOCK_HARD_ROCKS = 7
BLOCK_HARDROCK = 7
BLOCK_HARDROCKS = 7
BLOCK_GROUND_ROCKS = 7
BLOCK_GROUND_ROCK = 7
BLOCK_GROUNDROCKS = 7
BLOCK_GROUNDROCK = 7
BLOCK_SOLID = 7
BLOCK_SOLIDS = 7
BLOCK_GROUNDSTONE = 7
BLOCK_HARDSTONE = 7
BLOCK_ADMINSTONE = 7
BLOCK_GROUNDSTONES = 7
BLOCK_HARDSTONES = 7
BLOCK_ADMINSTONES = 7
BLOCK_GROUND_STONE = 7
BLOCK_HARD_STONE = 7
BLOCK_ADMIN_STONE = 7
BLOCK_GROUND_STONES = 7
BLOCK_HARD_STONES = 7
BLOCK_ADMIN_STONES = 7
BLOCK_WATER = 8
BLOCK_REALWATER = 8
BLOCK_REAL_WATER = 8
BLOCK_H2O = 8
BLOCK_STILLH2O = 9
BLOCK_STILL_H2O = 9
BLOCK_STILL_WATER = 9
BLOCK_STILLWATER = 9
BLOCK_WATERVATOR = 9
BLOCK_LAVA = 10
BLOCK_REAL_WATER = 9
BLOCK_REALWATER = 9
BLOCK_STILL_LAVA = 11
BLOCK_STILLLAVA= 11
BLOCK_STILL_FIRE = 11
BLOCK_LAVAVATOR = 11
BLOCK_SAND = 12
BLOCK_GRAVEL = 13
BLOCK_GOLD_ORE = 14
BLOCK_GOLDORE = 14
BLOCK_GOLDROCK = 14
BLOCK_GOLD_ORES = 14
BLOCK_GOLDORES = 14
BLOCK_GOLDROCKS = 14
BLOCK_COPPER_ORE = 15
BLOCK_COPPERORE = 15
BLOCK_IRON_ORE = 15
BLOCK_IRONORE = 15
BLOCK_COPPERROCK = 15
BLOCK_IRONROCK = 15
BLOCK_COAL_ORE = 16
BLOCK_COPPER_ORES = 15
BLOCK_COPPERORES = 15
BLOCK_IRON_ORES = 15
BLOCK_IRONORES = 15
BLOCK_COPPERROCKS = 15
BLOCK_IRONROCKS = 15
BLOCK_COAL_ORES = 16
BLOCK_COALORES = 16
BLOCK_COALORE = 16
BLOCK_COAL_ORE = 16
BLOCK_COAL = 16
BLOCK_COALS = 16
BLOCK_ORE = 16
BLOCK_ORES = 16
BLOCK_OIL_ORES = 16
BLOCK_OIL = 16
BLOCK_BLACK_ORES = 16
BLOCK_BLACKORES = 16
BLOCK_BLACK_ORE = 16
BLOCK_BLACKORE = 16
BLOCK_LOG = 17
BLOCK_TREE = 17
BLOCK_LOGS = 17
BLOCK_TREES = 17
BLOCK_TRUNK = 17
BLOCK_STUMP = 17
BLOCK_TRUNKS = 17
BLOCK_STUMPS = 17
BLOCK_TREETRUNK = 17
BLOCK_TREESTUMP = 17
BLOCK_TREETRUNKS = 17
BLOCK_TREESTUMPS = 17
BLOCK_LEAVES = 18
BLOCK_LEAF = 18
BLOCK_FOLIAGE = 18
BLOCK_SPONGE = 19
BLOCK_SPONGES = 19
BLOCK_GLASS = 20
BLOCK_RED_CLOTH = 21
BLOCK_RED = 21
BLOCK_ORANGE_CLOTH = 22
BLOCK_ORANGE = 22
BLOCK_YELLOW_CLOTH = 23
BLOCK_YELLOW = 23
BLOCK_LIME_CLOTH = 24
BLOCK_LIME = 24
BLOCK_GREENYELLOW = 24
BLOCK_GREENYELLOW_CLOTH = 24
BLOCK_LIGHTGREEN = 24
BLOCK_LIGHTGREEN_CLOTH = 24
BLOCK_GREEN_YELLOW = 24
BLOCK_GREEN_YELLOW_CLOTH = 24
BLOCK_LIGHT_GREEN = 24
BLOCK_LIGHT_GREEN_CLOTH = 24
BLOCK_GREEN_CLOTH = 25
BLOCK_GREEN = 25
BLOCK_TURQUOISE_CLOTH = 26
BLOCK_TURQUOISE = 26
BLOCK_AQUA = 26
BLOCK_TEAL = 26
BLOCK_AQUAGREEN = 26
BLOCK_AQUAGREEN_CLOTH = 26
BLOCK_AQUA_GREEN = 26
BLOCK_AQUA_GREEN_CLOTH = 26
BLOCK_AQUA_CLOTH = 26
BLOCK_TEAL_CLOTH = 26
BLOCK_SPRINGGREEN_CLOTH = 26
BLOCK_SPRINGGREEN = 26
BLOCK_CYAN_CLOTH = 27
BLOCK_CYAN = 27
BLOCK_BLUE_CLOTH = 28
BLOCK_BLUE = 28
BLOCK_PURPLE_CLOTH = 29
BLOCK_PURPLE = 29
BLOCK_DARKBLUE = 29
BLOCK_DARKBLUE_CLOTH = 29
BLOCK_DARK_BLUE = 29
BLOCK_DARK_BLUE_CLOTH = 29
BLOCK_INDIGO_CLOTH = 30
BLOCK_INDIGO = 30
BLOCK_VIOLET_CLOTH = 31
BLOCK_VIOLET = 31
BLOCK_MAGENTA_CLOTH = 32
BLOCK_MAGENTA = 32
BLOCK_PINK_CLOTH = 33
BLOCK_PINK = 33
BLOCK_DARKGREY_CLOTH = 34
BLOCK_DARKGREY = 34
BLOCK_DARKGRAY_CLOTH = 34
BLOCK_DARKGRAY = 34
BLOCK_DARK_GREY_CLOTH = 34
BLOCK_DARK_GREY = 34
BLOCK_DARK_GRAY_CLOTH = 34
BLOCK_DARK_GRAY = 34
BLOCK_BLACK = 34
BLOCK_BLACK_CLOTH = 34
BLOCK_GREY_CLOTH = 35
BLOCK_GRAY_CLOTH = 35
BLOCK_GREY = 35
BLOCK_GRAY = 35
BLOCK_WHITE_CLOTH = 36
BLOCK_WHITE = 36
BLOCK_YELLOW_FLOWER = 37
BLOCK_YELLOWFLOWER = 37
BLOCK_YELLOW_FLOWERS = 37
BLOCK_YELLOWFLOWERS = 37
BLOCK_RED_FLOWER = 38
BLOCK_REDFLOWER = 38
BLOCK_RED_FLOWERS = 38
BLOCK_REDFLOWERS = 38
BLOCK_BROWN_MUSHROOM = 39
BLOCK_BROWN_SHROOM = 39
BLOCK_SHROOM = 39
BLOCK_BROWN_SHROOMS = 39
BLOCK_SHROOMS = 39
BLOCK_MUSHROOM = 39
BLOCK_BROWN_MUSHROOMS = 39
BLOCK_MUSHROOMS = 39
BLOCK_RED_MUSHROOM = 40
BLOCK_TOADSTOOL = 40
BLOCK_RED_MUSHROOMS = 40
BLOCK_TOADSTOOLS = 40
BLOCK_RED_SHROOM = 40
BLOCK_RED_SHROOMS = 40
BLOCK_GOLD = 41
BLOCK_STEEL = 42
BLOCK_IRON = 42
BLOCK_SILVER = 42
BLOCK_METAL = 42
BLOCK_DOUBLE_STAIR = 43
BLOCK_DOUBLESTEP = 43
BLOCK_DOUBLE_STEP = 43
BLOCK_DOUBLESTAIR = 43
BLOCK_DOUBLE_STAIRS = 43
BLOCK_DOUBLESTEPS = 43
BLOCK_DOUBLE_STEPS = 43
BLOCK_DOUBLESTAIRS = 43
BLOCK_DOUBLESLAB = 43
BLOCK_DOUBLESLABS = 43
BLOCK_DOUBLE_SLAB = 43
BLOCK_DOUBLE_SLABS = 43
BLOCK_SLAB = 44
BLOCK_SLABS = 44
BLOCK_STAIR = 44
BLOCK_STEP = 44
BLOCK_STAIRS = 44
BLOCK_STEPS = 44
BLOCK_BRICK = 45
BLOCK_BRICKS = 45
BLOCK_TNT = 46
BLOCK_DYNAMITE = 46
BLOCK_EXPLOSIVE = 46
BLOCK_EXPLOSIVES = 46
BLOCK_BOOKCASE = 47
BLOCK_BOOKSHELF = 47
BLOCK_SHELF = 47
BLOCK_BOOKCASES = 47
BLOCK_BOOKSHELVES = 47
BLOCK_SHELVES = 47
BLOCK_BOOKS = 47
BLOCK_MOSSY_COBBLESTONE = 48
BLOCK_MOSS = 48
BLOCK_MOSSY = 48
BLOCK_MOSSYCOBBLESTONE = 48
BLOCK_MOSSY_STONE = 48
BLOCK_MOSSYSTONE = 48
BLOCK_BOOKCASES = 47
BLOCK_BOOKSHELVES = 47
BLOCK_MOSSY_COBBLESTONES = 48
BLOCK_MOSSYCOBBLESTONES = 48
BLOCK_MOSSY_STONES = 48
BLOCK_MOSSYSTONES = 48
BLOCK_MOSSY_ROCKS = 48
BLOCK_MOSSY_ROCK = 48
BLOCK_MOSSYROCKS = 48
BLOCK_MOSSYROCK = 48
BLOCK_OBSIDIAN = 49
BLOCK_OPSIDIAN = 49

BlockList = []
while len(BlockList) != 50:
    BlockList.append('')
BlockList[0]="air"
BlockList[1]="rock"
BlockList[2]="grass"
BlockList[3]="dirt"
BlockList[4]="stone"
BlockList[5]="wood"
BlockList[6]="plant"
BlockList[7]="adminblock"
BlockList[8]="water"
BlockList[9]="still water"
BlockList[10]="lava"
BlockList[11]="still lava"
BlockList[12]="sand"
BlockList[13]="gravel"
BlockList[14]="goldore"
BlockList[15]="ironore"
BlockList[16]="coal"
BlockList[17]="log"
BlockList[18]="leaves"
BlockList[19]="sponge"
BlockList[20]="glass"
BlockList[21]="red"
BlockList[22]="orange"
BlockList[23]="yellow"
BlockList[24]="lime"
BlockList[25]="green"
BlockList[26]="turquoise"
BlockList[27]="cyan"
BlockList[28]="blue"
BlockList[29]="indigo"
BlockList[30]="violet"
BlockList[31]="purple"
BlockList[32]="magenta"
BlockList[33]="pink"
BlockList[34]="black"
BlockList[35]="grey"
BlockList[36]="white"
BlockList[37]="yellow flower"
BlockList[38]="red flower"
BlockList[39]="brown mushroom"
BlockList[40]="red mushroom"
BlockList[41]="gold"
BlockList[42]="iron"
BlockList[43]="step"
BlockList[44]="doublestep"
BlockList[45]="brick"
BlockList[46]="tnt"
BlockList[47]="bookcase"
BlockList[48]="moss"
BlockList[49]="obsidian"

VIPS = [
    # Mojang staff (current or retired)
    "c418",
    "dock",
    "ez",
    "jeb_",
    "kappe",
    "mollstam",
    "notch",
    # Founders of blockBox or other products before blockBox
    "aera",
    "andrewgodwin",
    "pixeleater",
    # Developers/contributors of blockBox
    "fizyplankton",
    "tyteen4a03",
    "uberfox",
    "opticalza",
    # Code contributors to products before blockBox
    "099",
    "adam01",
    "andrewph",
    "destroyerx1",
    "dwarfy",
    "erronjason",
    "gdude2002",
    "goober",
    "gothfox",
    "kelraider",
    "notmeh",
    "revenant",
    "willempiee",
    "varriount",
    # Others we give our bows to.
    "fragmer",
    "pyropyro", 
    "tktech"
    ]

class ServerFull(Exception):
    pass

class NotConfigured(Exception):
    """Raised when configuration files are missing."""
    def __init__(self):
        self.msg = "blockBox is not configured. Read the installation guide if you wish to proceed."

    def __str__(self):
        return self.msg

class StoringMethodNotSupported(Exception):
    """Raised when the storing method supplied is not supported."""
    def __init__(self):
        self.msg = "blockBox currently does not support the storing method supplied. Please refer to the installation guide about storing methods blockBox supports."

    def __str__(self):
        return self.msg

class WorldFileDoesNotExist(Exception):
    pass
