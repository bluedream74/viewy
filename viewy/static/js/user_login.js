'use strict'

document.addEventListener('DOMContentLoaded', function() {
  let specialUserContainer = document.getElementById('specialUserContainer');
  let isSpecialUser = specialUserContainer ? specialUserContainer.dataset.isSpecialUser === 'true' : false;

  if (isSpecialUser) {
    document.getElementById('okButton').addEventListener('click', function () {
      document.getElementById('invitedMessage').style.display = 'none';
    });
  }
});