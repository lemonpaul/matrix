var modal = document.getElementById("myModal");

var class_show = function(class_name, class_id, length)
{
    xhttp = new XMLHttpRequest();

    w = Math.ceil(Math.sqrt(length))
    h = Math.ceil(length/w)

    height_ = 114 * h;
    width_ = 95 * w;

    left_ = event.pageX + 10;
    top_ = event.pageY - 10 - height_;

    xhttp.onreadystatechange = function() {
        if (this.readyState === XMLHttpRequest.DONE) {
            modal.setAttribute("style", "left: "+left_+"px; top: "+top_+"px; width:"+width_+"px; height: "+height_+"px;");
            modal.innerHTML = this.response;
            modal.style.display = "block";
            MathJax.typeset();
        }
    };
    xhttp.open("GET", "/explore/"+class_name+"/"+class_id+"?width="+w+"&height="+h+"&size="+length, true);
    xhttp.send();
}

var class_hide = function()
{
    modal.style.display = "none";
}

var toggle = function(id) 
{
    var element = document.getElementById(id);
    if (element.style.display === "none") 
    {
        element.removeAttribute("style");
    }
    else 
    {
        element.style.display = "none";
    }
}
