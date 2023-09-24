document.addEventListener("DOMContentLoaded", function () {
  let previewButton = document.querySelector("[name='preview_button']");
  let url = document.querySelector(".url");
  url.style.display = "none";

  if (previewButton) {
    previewButton.addEventListener("click", function (event) {
      event.preventDefault();

      // Ad Information
      let visualsInput = document.querySelector("input[type='file']");
      // visualsInputの存在をチェック
      if (!visualsInput) {
        console.error('File inputが見つかりませんでした!');
        return;
      }
      console.log(visualsInput);
      if (visualsInput.files && visualsInput.files.length > 0) {
        console.log("選択されたファイル:", visualsInput.files[0]);  // これで、選択された最初のファイルが表示されます。
      }
      if (visualsInput.files && visualsInput.files.length > 0) {
        // すべての.manga-pageを削除
        let existingPreviews = document.querySelectorAll(".manga-page");
        existingPreviews.forEach(page => {
          page.remove();
          console.log("既存の.manga-pageを削除しました。");
        });
        Array.from(visualsInput.files).forEach(file => {
          let reader = new FileReader();

          reader.onload = function (e) {

            // 新しいプレビューを追加
            let newPreview = document.createElement("img");
            newPreview.setAttribute("class", "page-content");
            newPreview.setAttribute("src", e.target.result);
            console.log("新しいプレビュー画像を作成しました。");

            let mangaPage = document.createElement("div");
            mangaPage.setAttribute("class", "manga-page");
            mangaPage.appendChild(newPreview);
            console.log("新しい.manga-pageを作成し、新しいプレビューを追加しました。");

            let book = document.querySelector(".book");
            if (book) {
              book.appendChild(mangaPage);
              console.log(".bookに.manga-pageを追加しました。");
            }
          }

          reader.readAsDataURL(file);
        });
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