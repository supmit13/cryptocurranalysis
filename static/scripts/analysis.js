function showcoinbase(){
}


function displayplots(indexval, urlprefix){
    selectbox = document.getElementById(indexval);
    selectedvalue = selectbox.value;
    //alert(indexval);
    //alert(selectedvalue);
    postdata = "csrfmiddlewaretoken=" + document.cryptoanalysis.csrfmiddlewaretoken.value;
    plotdiv = document.getElementById('plotimage');
    var xmlhttp;
    if (window.XMLHttpRequest){
        xmlhttp=new XMLHttpRequest();
    }
    else{
        xmlhttp=new ActiveXObject("Microsoft.XMLHTTP");
    }
    xmlhttp.onreadystatechange = function(){
        if(xmlhttp.readyState == 4 && xmlhttp.status==200){
	    plotdiv.style.display = "block";
	    //plotdiv.innerHTML = "";
	    waittag = document.getElementById('waitprocess');
 	    waittag.parentNode.removeChild(waittag);
	    imgtag = document.createElement('img');
	    imgtag.setAttribute('src', xmlhttp.responseText);
	    plotdiv.appendChild(imgtag);
        }
    };
    posturl = urlprefix + "/cryptocurry/analyze/visual/" + indexval + "/" + selectedvalue + "/";
    xmlhttp.open('POST', posturl, true);
    xmlhttp.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8');
    xmlhttp.setRequestHeader("X-CSRFToken", document.cryptoanalysis.csrfmiddlewaretoken.value);
    //alert(posturl);
    plotdiv.style.display = "block";
    imgtag = document.createElement('img');
    imgtag.setAttribute('src', 'static/images/loading_big.gif');
    imgtag.setAttribute('id', 'waitprocess');
    imgtag.setAttribute('title', 'This may take a while depending on the amount of data it needs to crunch. Please be patient.');
    plotdiv.appendChild(imgtag);
    xmlhttp.send(postdata);
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




