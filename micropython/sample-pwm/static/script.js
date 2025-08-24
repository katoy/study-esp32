function updateStatus() {
  fetch('/status').then(r => r.json()).then(function(data) {
    document.getElementById('xval').textContent = data.x;
    document.getElementById('yval').textContent = data.y;
    document.getElementById('wval').textContent = data.w;
    document.getElementById('xbar').style.width = (data.x/4095*300) + 'px';
    document.getElementById('ybar').style.width = (data.y/4095*300) + 'px';
    // 2Dグラフ上に点を表示
    var gx = Math.round(data.y/4095*300);
    var gy = Math.round((1 - data.x/4095)*300);
    var dot = document.getElementById('dot');
    dot.style.left = (gx-6) + 'px';
    dot.style.top = (gy-6) + 'px';
    dot.style.background = (data.w === 0) ? "black" : "red";
  });
}
setInterval(updateStatus, 300);
window.onload = updateStatus;
