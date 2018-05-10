function makeExpandingArea(container) {
  var area = container.getElementsByTagName('textarea')[0] ;
  var span = container.getElementsByTagName('span')[0] ;
  if (area.addEventListener) {
    area.addEventListener('input', function() {
      span.textContent = area.value;
    }, false);
    span.textContent = area.value;
  } else if (area.attachEvent) {
    area.attachEvent('onpropertychange', function() {
      var html = area.value.replace(/\n/g,'<br/>');
      span.innerText = html; 
    });
    var html = area.value.replace(/\n/g,'<br/>');
    span.innerText = html;
  }
  if(window.VBArray && window.addEventListener) { //IE9
    area.attachEvent("onkeydown", function() {
      var key = window.event.keyCode;
      if(key == 8 || key == 46) span.textContent = area.value;
    });
    area.attachEvent("oncut", function(){
      span.textContent = area.value;
    });//处理粘贴
  }
  container.className += " active";
}

function initTextareas()
{
  var divs=document.getElementsByClassName("text-expand");
  for (var i=0; i<divs.length;i++)
  {
    makeExpandingArea(divs[i]);
  }
}

window.onload=function(){
  initTextareas();
};
