'use strict'

const DEBOUNCE_TIME = 2000;
const HIDE_DELAY = 3000;
let updateTimeouts = {};
let clickCounts = {};
let lastEmoteClickTime = {};
let hideTimeouts = {};
let wasZeroClickedLast = false;
let initialEmoteCounts = {};

function getCookie(name) {
  let value = "; " + document.cookie;
  let parts = value.split("; " + name + "=");
  if (parts.length === 2) return parts.pop().split(";").shift();
}

function formatNumber(num) {
  return num >= 10000 ? `${(num / 1000).toFixed(1)}K` : num.toString();
}

function sendEmoteUpdate(postId, emoteIndex, countSpan, emote) {
  const currentCount = parseInt(countSpan.textContent, 10);
  const clickCount = clickCounts[emoteIndex] || 1;

  fetch(`/posts/emote_count/${postId}/${emoteIndex}/`, {
    method: 'POST',
    headers: {
      'X-CSRFToken': getCookie('csrftoken')
    },
    body: JSON.stringify({ clicks: clickCount })
  })
    .then(response => {
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      return response.json();
    })
    .then(data => {
      if (data.success) {
        // 1〜5のエモートインデックスの場合、K表記を使用せずにカウントをそのまま表示
        countSpan.textContent = emoteIndex > 0 && emoteIndex <= 5 ? data.new_count.toString() : formatNumber(data.new_count);
        clickCounts[emoteIndex] = 0;
        updateFirstEmoteCount(emote.closest('.emotes'));
      } else {
        console.error("Error updating emote count:", data.error);
        countSpan.textContent = formatNumber(data.new_count); // Restore original count on error
      }
    })
    .catch(error => {
      console.error("There was a problem with the fetch operation:", error.message);
      countSpan.textContent = currentCount; // Restore original count on fetch error
    });
}


function hideEmotesSequentially(emotesContainer) {
  const emotesToHide = Array.from(emotesContainer.querySelectorAll('.emote:not(.emote-icon)'));

  emotesToHide.reverse().forEach((emote, index) => {
    setTimeout(() => {
      emote.style.opacity = "0";
      emote.style.transform = "scale(0.5)";
      setTimeout(() => {
        emote.style.visibility = "hidden";
        emote.style.transform = "scale(1)";
      }, 300);  // After fading, then set visibility to hidden
    }, index * 25); // This staggers the hide animation
  });
}

document.querySelector('.screen').addEventListener('click', function (event) {
  const emote = event.target.closest('.emote');
  const emotesContainer = event.target.closest('.emotes');

  // 対応する.emotesのカウントを更新
  if (emotesContainer) {
    updateFirstEmoteCount(emotesContainer);
  }
  if (!emote || !emotesContainer) return;

  const postId = emote.closest('.post').getAttribute('data-post-id');
  const emoteIndex = Array.from(emotesContainer.querySelectorAll('.emote')).indexOf(emote);

  lastEmoteClickTime[emoteIndex] = Date.now();

  // 0番目のエモートがクリックされたときの動作
  if (emoteIndex === 0) {
    const hiddenEmotes = Array.from(emotesContainer.querySelectorAll('.hidden-emote')).slice(0, 5);
    if (wasZeroClickedLast) { // 追加: 最後のクリックが0番目のエモートであった場合のロジック
      wasZeroClickedLast = false;
      hideEmotesSequentially(emotesContainer);
      return; // 他のロジックをスキップ
    }
    hiddenEmotes.forEach((emote, index) => {
      setTimeout(() => {
        emote.style.visibility = "visible";
        emote.classList.add('bouncing');
        emote.style.opacity = "1";
        setTimeout(() => {
          emote.classList.remove('bouncing');
        }, 500);
      }, index * 50);
    });
    wasZeroClickedLast = true; // 0番目のエモートがクリックされたので、フラグをセット
  } else {
    wasZeroClickedLast = false; // 他のエモートがクリックされたので、フラグをリセット
  }

  // 1～5番目のエモートがクリックされた場合
  if (emoteIndex >= 0 && emoteIndex <= 5) {
    emote.classList.add('bouncing');
    setTimeout(() => {
      emote.classList.remove('bouncing');
    }, 500);
  }

  if (emoteIndex > 0) {
    const countSpan = emote.querySelector('.emote-count');
    // 修正: formatNumberを使わずに直接数値をインクリメント
    countSpan.textContent = (parseInt(countSpan.textContent, 10) + 1).toString();
    clickCounts[emoteIndex] = (clickCounts[emoteIndex] || 0) + 1;
    updateFirstEmoteCount(emotesContainer);

    if (updateTimeouts[emoteIndex]) {
      clearTimeout(updateTimeouts[emoteIndex]);
    }
    updateTimeouts[emoteIndex] = setTimeout(() => {
      sendEmoteUpdate(postId, emoteIndex, countSpan, emote);
    }, DEBOUNCE_TIME);
  }

  if (hideTimeouts[emoteIndex]) {
    clearTimeout(hideTimeouts[emoteIndex]);
  }
  hideTimeouts[emoteIndex] = setTimeout(() => {
    if (Date.now() - Math.max(...Object.values(lastEmoteClickTime)) >= HIDE_DELAY && emoteIndex >= 0) {
      hideEmotesSequentially(emotesContainer);
    }
  }, HIDE_DELAY);
});


function updateFirstEmoteCount(emotesContainer) {
  const totalCountSpan = emotesContainer.querySelector('.emote-icon .emote-count');
  if (!totalCountSpan) {
    console.warn('totalCountSpan not found!');
    return;
  }

  const emotesDataAttribute = emotesContainer.getAttribute('data-formatted-total-emote');

  // 初めてのクリックの場合、テンプレートからエモートの合計数を取得
  if (!initialEmoteCounts[emotesDataAttribute]) {
    initialEmoteCounts[emotesDataAttribute] = parseInt(emotesDataAttribute, 10);
  }

  // 全てのエモートの数を再計算せずに、差分だけを使って更新
  const allCounts = Array.from(emotesContainer.querySelectorAll('.emote:not(.emote-icon) .emote-count'))
    .map(span => parseInt(span.textContent.trim(), 10) || 0);

  const diff = allCounts.reduce((a, b) => a + b, 0) - initialEmoteCounts[emotesDataAttribute];
  const totalCount = initialEmoteCounts[emotesDataAttribute] + diff;

  totalCountSpan.textContent = formatNumber(totalCount);
}

