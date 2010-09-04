<?php
/* 
*************************************************************
************** Copyright 2010 Public-Craft.com **************
************ Made by Andrew Horn (aka "AndrewPH") ***********
*************************************************************
*/
	include('./config.php');
	$socketdie = "No information avaliable";
	function runcmd($cmd, $data = NULL ){
	global $socket;
	$jsondata = json_encode(array ('password'=>$spass,'command'=>$cmd, $data[0]=>$data[1]))."\r\n";
	socket_send($socket, $jsondata, strlen($jsondata),0);
	if (($bytes = socket_recv($socket, $buf, 16384, NULL)) == false) die($socketdie);
	//echo "raw data = ".$buf."<br>";
	return json_decode($buf);
	}
	?>
 <div id="main">
	<?
	if(($socket = socket_create(AF_INET, SOCK_STREAM, SOL_TCP))== false) die($socketdie);
	if(socket_connect($socket, $sip, $sport) == false) die($socketdie);
	if (!$_GET['p'] || $_GET['p'] != "stat" && $_GET['p'] != "lists")
	{
		$page = "stat";
	} else {
		$page = $_GET['p'];
	};
	include("./stats/". $page .".php");
	?>
</div>