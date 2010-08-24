

import com.mojang.minecraft.level.Level;
import java.util.zip.*;
import java.io.*;
import java.lang.*;

// This class implements a thin layer to read and write the original level
// files, which are serialized Java objects. It uses stdin and stdout for 
// transferring the unserialised data.

class OrigFormat {
    
    public static void load ( String filename, String outdir ) {
        // Decompress and open the file
        Level map;
        try {
            GZIPInputStream gzin = new GZIPInputStream(new FileInputStream(filename));
            // Much thanks to the Omen code for inspiration here.
            // Check the first bytes of the file to see if it's valid.
            byte[] arrayOfByte = new byte[5];
            gzin.read(arrayOfByte, 0, arrayOfByte.length);
            if ((arrayOfByte[0] != 39) || (arrayOfByte[1] != 27) || (arrayOfByte[2] != -73) || (arrayOfByte[3] != -120)) {
                System.err.println("Invalid level file.");
                return;
            }
            if (arrayOfByte[4] > 2) {
                System.err.println("Unknown level format version!");
                return;
            }
            // Alright, unserialise the map object
            ObjectInputStream obin = new ObjectInputStream(gzin);
            map = ((Level)obin.readObject());
            gzin.close();
            obin.close();
        } catch (FileNotFoundException e) {
            System.err.println("Cannot open file! (not found)");
            return;
        } catch (IOException e) {
            System.err.println("Cannot open file! (IOError)");
            return;
        } catch (ClassNotFoundException e) {
            System.err.println("Cannot find the Minecraft libraries.");
            return;
        }
        try {
            // Make the world directory
            (new File(outdir)).mkdir();
            // Let's write out those raw bytes, baby.
            DataOutputStream dout = new DataOutputStream(new GZIPOutputStream(new FileOutputStream(outdir + "/blocks.gz")));
            dout.writeInt(map.blocks.length);
            dout.write(map.blocks, 0, map.blocks.length);
            dout.close();
            // Also, write out the meta
            FileWriter mout = new FileWriter(outdir + "/world.meta");
            mout.write("[size]\nx = " + map.width + "\ny = " + map.depth + "\nz = " + map.height + "\n\n");
            mout.write("[spawn]\nx = " + map.xSpawn + "\ny = " + map.ySpawn + "\nz = " + map.zSpawn + "\nh = 0\n\n");
            mout.close();
        } catch (FileNotFoundException e) {
            System.err.println("Cannot save myne files! (not found)");
            return;
        } catch (IOException e) {
            System.err.println("Cannot save myne files! (IOError)");
            return;
        }
    }
    
    public static void save ( String filename ) {
    }
    
    public static void main ( String[] args ) {
        if ( args.length < 3 ) {
            System.err.println("Please pass a mode, a filename, and a world directory name.");
            return;
        }
        if ( args[0].equals("load") ) {
            // We're loading a file
            load(args[1], args[2]);
        } else if ( args[0].equals("save") ) {
            // We're saving a file
            save(args[1]);
        } else {
            System.err.println("The first argument should be load or save.");
        }
    }
}