document.addEventListener("DOMContentLoaded", function () {
  let previewButton = document.querySelector("[name='preview_button']");
  let url = document.querySelector(".url");
  url.style.display = "none";

  if (previewButton) {
    previewButton.addEventListener("click", function (event) {
      event.preventDefault();

      // すべての<video>要素を削除
      let existingVideos = document.querySelectorAll("video");
      existingVideos.forEach(video => {
        video.remove();
        console.log("既存の<video>を削除しました。");
      });

      let visualsInput = document.querySelector("input[type='file']");  // <-- 追加
      // visualsInputの存在をチェック
      if (!visualsInput) {
        console.error('File inputが見つかりませんでした!');
        return;
      }

      if (visualsInput.files && visualsInput.files.length > 0) {
        let file = visualsInput.files[0];
        if (file.type.match('video.*')) {
          let reader = new FileReader();

          reader.onload = function (e) {
            let newPreview = document.createElement("video");
            newPreview.setAttribute("controls", "controls");
            newPreview.setAttribute("width", "200px");
            newPreview.setAttribute("height", "400px");
            newPreview.setAttribute("src", e.target.result);
            newPreview.className = "post-video";

            let previewBlock = document.querySelector(".post");
            let spinnerElement = previewBlock.querySelector(".spinner");
            if (spinnerElement) {
              spinnerElement.insertAdjacentElement('afterend', newPreview);
              console.log("spinnerの後に新しい<video>を追加しました。");
            }
          };
          reader.readAsDataURL(file);
        } else {
          console.log("選択されたファイルはビデオではありません。");
        }
      }

      let adInformationFields = Array.from(document.querySelectorAll(".fieldWrapper input, .fieldWrapper select, .fieldWrapper textarea"));
      let adInformation = {};
      adInformationFields.forEach(field => {
        adInformation[field.name] = field.value;
      });

      // Post Details
      let title = document.querySelector(".title input");
      let url = document.querySelector(".url-set input");
      let hashtags = [
        document.querySelector(".hashtag1 input"),
        document.querySelector(".hashtag2 input"),
        document.querySelector(".hashtag3 input"),
      ];

      let caption = document.querySelector(".caption textarea");

      // Update the preview:
      let previewBlock = document.querySelector(".post");
      if (title && title.value) {
        previewBlock.querySelector(".title").textContent = title.value;
      }
      if (url && url.value) {
        previewBlock.querySelector(".url a").href = url.value;
        previewBlock.querySelector(".url").style.display = "inline"; // 追加
      } else {
        previewBlock.querySelector(".url").style.display = "none"; // 追加
      }
      if (caption && caption.value) {
        previewBlock.querySelector(".caption").textContent = caption.value;
      }

      let hashtagElements = previewBlock.querySelectorAll(".hashtag a");

      hashtags.forEach((hashtagInput, index) => {
        if (hashtagInput && hashtagInput.value && hashtagElements[index]) {
          hashtagElements[index].textContent = "#" + hashtagInput.value;
          hashtagElements[index].parentNode.style.display = "inline"; // 追加
        } else {
          hashtagElements[index].parentNode.style.display = "none"; // 追加
        }
      });

    });
  }
});