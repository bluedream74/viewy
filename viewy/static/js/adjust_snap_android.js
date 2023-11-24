// Androidだったら.screenに.android属性を付けて、その中の.postにscroll-snap-stop等をつけれるようにする
document.addEventListener('DOMContentLoaded', function () {
  var isAndroid = navigator.userAgent.toLowerCase().indexOf("android") > -1;

  // Androidかどうかをコンソールに出力
  console.log("Is this device Android? " + isAndroid);

  if (isAndroid) {
      document.querySelector('.screen').classList.add("android");
  }
});