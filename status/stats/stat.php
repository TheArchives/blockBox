<?
/* 
*************************************************************
************** Copyright 2010 Public-Craft.com **************
************ Made by Andrew Horn (aka "AndrewPH") ***********
*************************************************************
*/
		$admins = array();
		$directors = array();
		$mods = array();
		$worlds = runcmd("userworlds");
		
 		foreach (runcmd("mods")->mods as $n => $name)
			switch($name){
				default: $mods[$name] = 1; break;
			}
 
 		foreach (runcmd("directors")->directors as $n => $name)
			switch($name){
				default: $directors[$name] = 1; break;
			}
			
		foreach (runcmd("admins")->admins as $n => $name)
			switch($name){
				default: $admins[$name] = 1; break;
			}
 
			foreach (runcmd("users")->users as $n => $name) $users[$name] = 1;
			$adminsonline = array();
			foreach ($users as $name => $n)
			foreach ($mods as $mname => $n)
			foreach ($admins as $aname => $n) 
			foreach ($directors as $dname => $n)
			if($name == $aname && $aname != $dname) {$adminsonline =1;} else {$adminsonline = 0;};
			if($name == $dname) $directorsonline[$dname] =1;
			if($name == $mname) $modsonline[$mname] =1;
			sort($worlds->worlds);
 
			ksort($users);
			ksort($mods);
			ksort($admins);
			ksort($directors);
 
			echo "<h2>Statistics</h2>\n";
			echo "<ul>\n";
				echo "<li>" . count($worlds->worlds) . " worlds online </li>\n";
				if(count($users)) echo "<li>" . count($users) . " user" . (count($users) > 1 ? "s":"") . "</li>\n";
			echo "</ul>\n";
 
			echo "<h2>Users</h2>\n";
			echo "<ul>\n";
				$n = 0;
				foreach($users as $name => $stat){
					if(!$admins[$name] && !$directors[$name] && !$mods[$name]){
						echo "<li>" . $name . "</li>\n";
					}
					$n++;
				}
			echo "</ul>\n";
			
			echo "<h3>Directors</h3>\n";
			echo "<ul>\n";
				$n = 0;
				foreach($directors as $name => $stat){
									if(!$owners[$name] && $users[$name]) {
					echo "<li>" . $name . ($directorsonline[$name] ? " (online)" : "") . "</li>\n";
				}
				$n++;
				}
			echo "</ul>\n";
 
			echo "<h3>Admins</h3>\n";
			echo "<ul>\n";
				$n = 0;
				foreach($admins as $name => $stat){
					if(!$directors[$name] && $users[$name]) {
					echo "<li>" . $name . ($adminsonline[$name] ? " (online)" : "") . "</li>\n";
				}
				$n++;
				}
			echo "</ul>\n";
 
 			echo "<h3>Mods</h3>\n";
			echo "<ul>\n";
				$n = 0;
				foreach($mods as $name => $stat){
					if(!$admins[$name] && !$directors[$name] && $users[$name]) {
				echo "<li>" . $name . ($modsonline[$name] ? " (online)" : "") . "</li>\n";
				}
				$n++;
				}
			echo "</ul>\n";
 
			echo "<h3>Worlds</h3>\n";
				$bgphase = 0;
 
				foreach ($worlds->worlds as $n => $worldinfo){
					$userinfo = array();
					if(!$bgphase) $bgphase=1;
					else $bgphase=0;
					$info = $worldinfo[2];
					echo "<b>".$worldinfo[0]."</b>\n".
					($info->private ? "(Private)" : "(Public)").
					($info->locked ? "(Locked)" : "").
					($info->physics ? "(Physics)" : "")."\n<br>\n";
 
					foreach ($info->writers as $n => $value) $userinfo[$value] = "Writer: ";
					foreach ($info->ops as $n => $value) $userinfo[$value] = "Op: ";
 
					sort($worldinfo[1]);
 
					echo "<ul>\n";
					foreach ($worldinfo[1] as $n => $name){
						echo "<li>";
						if(!$admins[strtolower($name)] && !$directors[strtolower($name)] && !$mods[strtolower($name)]) {echo ($userinfo[$name]? $userinfo[$name]: "Viewer: ");
						}elseif (!$directors[strtolower($name)] && !$mods[strtolower($name)]) { echo "Admin: "; 
						}elseif (!$admins[strtolower($name)] && !$directors[strtolower($name)]) { echo "Mod: ";
						}elseif (!$mods[strtolower($name)] && !$admins[strtolower($name)]) { echo "Director: "; }
 
						echo $name."</li>\n";
			 		}
					echo "</ul>\n";
				}
					socket_close($socket);
 
	?>
