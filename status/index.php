<?PHP
/* 
*************************************************************
************** Copyright 2010 Public-Craft.com **************
************ Made by Andrew Horn (aka "AndrewPH") ***********
*************************************************************
*/
?>
<html>
<head>
<style>
#herp				{ display:block; width:500px; top:auto; margin-right:auto; margin-left:auto;}
#button				{ height:20px; float:left; background:#222; width:250px; text-align:center; color:#eee;}
#button:hover		{ height:20px; float:left; display:inline; background:#555; width:250px; text-align:center; color:#eee;}
#button2:hover		{ height:20px; float:left; display:inline; background:#555; width:250px; text-align:center; color:#eee;}
#button:hover		{ height:20px; float:left; display:inline; background:#555; width:250px; text-align:center; color:#eee;}
#abutton			{ height:20px; float:left; display:inline; background:#555; width:250px; text-align:center; color:#eee;}
#button a			{ display:inline; color:#eee; text-decoration:none; font:18px/18px impact; }
#button2 a			{ display:inline; color:#eee; text-decoration:none; font:18px/18px impact; }
#abutton a			{ display:inline; color:#eee; text-decoration:none; font:18px/18px impact; }
#main				{ display:block; color:#eee; padding-top:10px; padding-bottom:10px; padding-left:10px; width:500px; background:#555; list-style:none; font: 14px/14px helvetica, sans-serif; margin-right:auto; margin-left:auto;}
body 				{ background:#000; }
</style>	
<?PHP
// Basic stuff first.
include('./config.php');

echo "<title>".$sitename."</title>";
?>
</head>
<br />
<body>
<?PHP
include('./resource/content.php');
?>
</body>
</html>
