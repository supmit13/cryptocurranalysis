function showcoinbase(){
}


function showloginscreen(urlprefix){
    logindiv = document.getElementById('logindiv');
    var xmlhttp;
    if (window.XMLHttpRequest){
        xmlhttp=new XMLHttpRequest();
    }
    else{
        xmlhttp=new ActiveXObject("Microsoft.XMLHTTP");
    }
    xmlhttp.onreadystatechange = function(){
        //alert(xmlhttp.status);
        if(xmlhttp.readyState == 4 && xmlhttp.status==200){
	    logindiv.style.display = "";
	    logindiv.innerHTML = xmlhttp.responseText;
	    //alert(xmlhttp.responseText);
        }
    };
    geturl = urlprefix + "/cryptocurry/auth/showlogin/";
    xmlhttp.open('GET', geturl, true);
    xmlhttp.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8');
    xmlhttp.setRequestHeader("X-CSRFToken", document.cryptoanalysis.csrfmiddlewaretoken.value);
    //alert(geturl);
    logindiv.style.display = "";
    xmlhttp.send();
}


function dologin(urlprefix){
    username = document.loginform.username.value;
    password = document.loginform.password.value;
    keepmesignedin = false;
    logindiv = document.getElementById('logindiv');
    if(document.loginform.keepmesignedin.checked == true){
        keepmesignedin = true
    }
    data = "username=" + username + "&password=" + password + "&keepmesignedin=";
    if(keepmesignedin){
        data += "1"
    }
    data += "&csrfmiddlewaretoken=" + document.loginform.csrfmiddlewaretoken.value;
    var xmlhttp;
    if (window.XMLHttpRequest){
        xmlhttp=new XMLHttpRequest();
    }
    else{
        xmlhttp=new ActiveXObject("Microsoft.XMLHTTP");
    }
    xmlhttp.onreadystatechange = function(){
        //alert(xmlhttp.status);
        if(xmlhttp.readyState == 4 && xmlhttp.status==200){
	    logindiv.style.display = "";
	    logindiv.innerHTML = xmlhttp.responseText;
	    //alert(xmlhttp.responseText);
        }
    };
    posturl = urlprefix + "/cryptocurry/auth/login/";
    //alert(posturl);
    xmlhttp.open('POST', posturl, true);
    xmlhttp.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8');
    xmlhttp.setRequestHeader("X-CSRFToken", document.loginform.csrfmiddlewaretoken.value);
    logindiv.style.display = "";
    //alert(data);
    xmlhttp.send(data);
}


function showregisterscreen(){
}




