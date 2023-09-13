'use strict'

const DEBOUNCE_TIME = 2000;
const HIDE_DELAY = 3000;
let updateTimeouts = {};
let clickCounts = {};
let lastEmoteClickTime = {};
let hideTimeouts = {};

function getCookie(name) {
  let value = "; " + document.cookie;
  let parts = value.split("; " + name + "=");
  if (parts.length === 2) return parts.pop().split(";").shift();
}

function formatNumber(num) {
  if (num >= 10000) {
      return (num / 1000).toFixed(1) + 'K';
  } else {
      return num.toString();
  }
}

function sendEmoteUpdate(postId, emoteIndex, countSpan) {
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
        countSpan.textContent = formatNumber(data.new_count);
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

// function updateFirstEmoteCount(emotesContainer) {
//   const totalCountSpan = emotesContainer.querySelector('.first-emote .emote-count');
//   const allCounts = Array.from(emotesContainer.querySelectorAll('.emote-count'))
//     .slice(1)
//     .map(span => parseInt(span.textContent, 10) || 0);
//   const totalCount = allCounts.reduce((a, b) => a + b, 0);
//   totalCountSpan.textContent = totalCount;
// }

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

document.querySelector('.screen').addEventListener('click', function(event) {
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
      countSpan.textContent = parseInt(countSpan.textContent, 10) + 1;
      clickCounts[emoteIndex] = (clickCounts[emoteIndex] || 0) + 1;
      updateFirstEmoteCount(emotesContainer);

      if (updateTimeouts[emoteIndex]) {
          clearTimeout(updateTimeouts[emoteIndex]);
      }
      updateTimeouts[emoteIndex] = setTimeout(() => {
          sendEmoteUpdate(postId, emoteIndex, countSpan);
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
  const allCounts = Array.from(emotesContainer.querySelectorAll('.emote:not(.emote-icon) .emote-count'))
    .map(span => parseInt(span.textContent.trim(), 10) || 0);

  const totalCount = allCounts.reduce((a, b) => a + b, 0);
  totalCountSpan.textContent = formatNumber(totalCount);
}

document.addEventListener('DOMContentLoaded', () => {
  function updateAllEmoteCounts() {
    document.querySelectorAll('.emotes').forEach(updateFirstEmoteCount);
  }

  updateAllEmoteCounts();

  const observer = new MutationObserver(mutations => {

    mutations.forEach(mutation => {
      if (mutation.addedNodes.length) {
        mutation.addedNodes.forEach(node => {
          if (node.nodeType === Node.ELEMENT_NODE) {
            if (node.matches('.emotes')) {

            } else {
              const emoteContainer = node.querySelector('.emotes');
              if (emoteContainer) {
                updateAllEmoteCounts();
                handleEmotesContainer(emoteContainer);
              }
            }
          }
        });
      }
    });
  });

  function handleEmotesContainer(emotesNode) {

    const innerObserver = new MutationObserver(innerMutations => {
      innerMutations.forEach(innerMutation => {
        if (innerMutation.target.classList.contains('emote-count')) {
          updateFirstEmoteCount(emotesNode);
        }
      });
    });

    innerObserver.observe(emotesNode, { childList: true, subtree: true });
    setTimeout(() => {
      innerObserver.disconnect();
    }, 1000);
  }

  const screenElement = document.querySelector('.screen');
  observer.observe(screenElement, { childList: true, subtree: true });
});

