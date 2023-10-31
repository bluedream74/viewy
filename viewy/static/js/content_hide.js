'use strict';

document.addEventListener('DOMContentLoaded', () => {

  let timeoutIds = new Map();

  function toggleVisibility(contentElement, labelElement) {
    const input = labelElement ? labelElement.querySelector('.hide-input') : null;

    if (contentElement.style.opacity === '0') {
      contentElement.style.opacity = '1';
      setTimeout(() => {
        contentElement.style.pointerEvents = 'auto';
      }, 200);
      if (labelElement) {
        labelElement.classList.replace('fa-angle-up', 'fa-angle-down');
        if (input) input.checked = false;
      }
    } else {
      contentElement.style.opacity = '0';
      setTimeout(() => {
        contentElement.style.pointerEvents = 'none';
      }, 200);
      if (labelElement) {
        labelElement.classList.replace('fa-angle-down', 'fa-angle-up');
        if (input) input.checked = true;
      }
    }
  }

  function autoHide(element) {

    if (element.dataset.isAdvertisement === 'True') {
      return;
    }

    let timeoutId = setTimeout(() => {
      const contentElement = element.querySelector('.content');
      const labelElement = element.querySelector('.hide-label');
      if (!element.wasClicked && element.querySelector('.book') && contentElement.style.opacity !== '0') {
        toggleVisibility(contentElement, labelElement);
      }
      element.wasClicked = false; // Reset the flag here
      timeoutIds.delete(element); // Remove the timeoutId when it's executed
    }, 3000);

    timeoutIds.set(element, timeoutId); // Save the timeoutId
  }

  function handleIntersection(entries) {
    entries.forEach(entry => {
      const element = entry.target;

      if (entry.isIntersecting) {
        // If the element is an advertisement, do not apply autoHide
        if (element.dataset.isAdvertisement === 'True') {
          return;
        }

        // If the post has been viewed previously, ensure the content is visible
        if (element.dataset.viewed === "true") {
          const contentElement = element.querySelector('.content');
          const labelElement = element.querySelector('.hide-label');
          if (contentElement.style.opacity === '0') {
            toggleVisibility(contentElement, labelElement);
          }
        } else {
          autoHide(element);
        }

        // Mark the post as viewed
        element.dataset.viewed = 'true';
      }
    });
  }

  function handleClick(event) {

    const element = event.currentTarget;

    // data-is-advertisement attribute
    if (element.dataset.isAdvertisement === 'True') {
      return;
    }

    clearTimeout(timeoutIds.get(element)); // Clear the timeout
    const contentElement = element.querySelector('.content');
    const labelElement = element.querySelector('.hide-label');
    element.wasClicked = true; // Set the flag here

    // Check if the clicked element is the label or its associated input
    if (event.target.matches('.hide-input')) {
      return;
    }

    if (event.target.closest('.content')) {
      return;
    }

    // Only toggle visibility when the label is clicked
    if (event.target === labelElement || event.target.closest('.hide-label')) {
      toggleVisibility(contentElement, labelElement);
      event.stopPropagation();
      return;
    }

    const bookElement = element.querySelector('.book');
    if (!bookElement) {
      return;
    }

  }

  document.addEventListener('click', function (e) {
    const clickedPost = e.target.closest('.post');

    if (!e.target.closest('.post') || e.target.closest('.hide-label') || e.target.closest('.content')|| clickedPost.dataset.isAdvertisement === 'True') {
      return;
    }

    if (!clickedPost.querySelector('.book')) {
      return;
    }

    const clickedContent = clickedPost.querySelector('.content');
    const clickedLabel = clickedPost.querySelector('.hide-label');

    if (clickedContent) {
      toggleVisibility(clickedContent, clickedLabel);
    }

    if (e.target.closest('.hide-label')) {
      e.stopPropagation();
    }
  });

  const observer = new IntersectionObserver(handleIntersection, {
    threshold: 1.0
  });

  function observeTargets(newTargets) {
    newTargets.forEach(target => {
      observer.observe(target);
      target.addEventListener('click', handleClick);

    });
  }

  const mutationObserver = new MutationObserver(mutationsList => {
    for (let mutation of mutationsList) {
      if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
        mutation.addedNodes.forEach(node => {
          if (node instanceof HTMLElement) {
            let newTargets = Array.from(node.querySelectorAll('.post'));
            if (node.matches('.post')) {
              newTargets.push(node);
            }
            observeTargets(newTargets);
          }
        });
      }
    }
  });

  const screenContainer = document.querySelector('.screen');
  mutationObserver.observe(screenContainer, { childList: true, subtree: true });

  const initialTargets = document.querySelectorAll('.post');
  observeTargets(initialTargets);

}, true);