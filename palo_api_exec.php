<?PHP

$apiwords=$argc-1; // to start, assume all cli "words" are part of the api command, aside from the program name itself
$lastIsVal=false; // Assume the last arg is not a value modifier... we'll check later
$cmd="";
$verbose=false;


function palo_get_api_key($host,$user, $pass){
        $arrContextOptions=
                array(
                        "ssl"=>array(
                                "verify_peer"=>false,
                                "verify_peer_name"=>false,
                        ),
                        "http"=>array(
                                'timeout' => 15,
                        )
                );
        $url="https://$host/api/?type=keygen&user=$user&password=$pass";
        $contents = @file_get_contents($url, false, stream_context_create($arrContextOptions));
        $len=strlen($contents);
        if($len>0){
                $badChars=array("<", "/");
                $raw=explode("key>", $contents);
                $key=trim(str_replace($badChars,"", $raw[1]));
                return($key);
        }else{
                return("AuthFail");
        }

}


// Build the API command in XML form....
if($argc>2){
        $final=trim($argv[$argc-1]);
        if($argv[1]=="-v"){
				$apiwords--;
                $verbose=true;
                $fwname=trim($argv[2]);
                $firstcmdarg=3; // We got the verbose arg, so shift our fwname and cmd args by one
        }else{
                $fwname=trim($argv[1]);
                $firstcmdarg=2; // No verbose arg, so first cmd word (arg) is 2, not 3
        }
        if( stristr($final,"-") || stristr($final,".") || $final=="all" ){
                $lastIsVal=true;
                $apiwords--; // The last cli arg is a "value" to modify the api command such as "show arp all" the all is a value modifier, not part of the api cmd, so reduce the number of api cmd words by one
        }
        if(!stristr($fwname,"lan")&&!stristr($fwname,"wan")){
                 die("\"$fwname\" is not a valid firewall name.");
        }
        if($verbose){
                echo "\nAPI_Cmd_words: $apiwords  |  FWName: $fwname  |  LastIsVal=$lastIsVal \n";
        }

		// For each of the actual api cmd words, create the xml tags around the word...
        for($a=$firstcmdarg; $a<=($apiwords); $a++){

                $cmd.="<" . trim($argv[$a]) . ">";
        }
		// If the last cli arg is a value modifier, add it to the string without xml tags around it
        if($lastIsVal){
                $cmd.="$final";
        }
		// Now add the corresponding closing xml tags to match the api command words in reverse, per XML standard
        for($a=$apiwords; $a>1; $a--){
                $cmd.="</" . trim($argv[$a]) . ">";
        }
}else{
        die("Syntax: $argv[0] [-v] fwName cmdWord1 {cmdWord2 ...}\n\n");
}




// Read the values for "user" and "pass" from a config file local to the script, so they don't have to be stored in the script 
$user= // read from .creds file
$pass= // Same...

$key=palo_get_api_key($fwname, $user, $pass, $verbose);

if($verbose){
        echo "\n\nAPICMD: $cmd \n\n";
        echo "KEY:  $key \n";
        echo "\n\nCMD: $cmd \n";
}

$output=curlCall($fwname, $key, $cmd, $verbose);

function curlCall($host, $key, $cmd, $verbose){
        $curlCMD="curl -H \"X-PAN-KEY:$key\" -sk 'https://$host/api/?type=op&cmd=$cmd'";
        if($verbose){
                echo "\n\n CMD: $curlCMD \n";
        }
        $curlOut=trim(`$curlCMD`);
        #$ref1=str_replace("<","     ",$curlOut);
        #$ref2=str_replace(">","     ",$ref1);
        #echo "$ref2 \n\n"; exit;
        var_dump($curlOut); exit;
}

echo "\n\n";
?>
