<?
/* 
*************************************************************
************** Copyright 2010 Public-Craft.com **************
************ Made by Andrew Horn (aka "AndrewPH") ***********
*************************************************************
*/
		$admins = array();
		$owner = array();
		$directors = array();
		$mods = array();
		
 		foreach (runcmd("mods")->mods as $n => $name)
			switch($name){
				default: $mods[$name] = 1; break;
			}
 
 		foreach (runcmd("directors")->directors as $n => $name)
			switch($name){
				default: $directors[$name] = 1; break;
			}
			
		foreach (runcmd("owner")->directors as $n => $name)
			switch($name){
				default: $owner[$name] = 1; break;
			}
			
		foreach (runcmd("admins")->admins as $n => $name)
			switch($name){
				default: $admins[$name] = 1; break;
			}
			foreach ($mods as $mname => $n);
			foreach ($admins as $aname => $n);
			foreach ($directors as $dname => $n);
			foreach ($owner as $oname => $n);
			
			echo "<h3>Owner</h3>\n";
			echo "<ul>\n";
				$n = 0;
				foreach($owner as $name => $stat){
					echo "<li>" . $name ."</li>\n";
				}
				$n++;
			echo "</ul>\n";
			
			echo "<h3>Directors</h3>\n";
			echo "<ul>\n";
				$n = 0;
				foreach($directors as $name => $stat){
					echo "<li>" . $name ."</li>\n";
				}
				$n++;
			echo "</ul>\n";
 
			echo "<h3>Admins</h3>\n";
			echo "<ul>\n";
				$n = 0;
				foreach($admins as $name => $stat){
					echo "<li>" . $name ."</li>\n";
				}
				$n++;
			echo "</ul>\n";
 
 			echo "<h3>Mods</h3>\n";
			echo "<ul>\n";
				$n = 0;
				foreach($mods as $name => $stat){
				echo "<li>" . $name ."</li>\n";
				}
				$n++;
			echo "</ul>\n";
?>
 