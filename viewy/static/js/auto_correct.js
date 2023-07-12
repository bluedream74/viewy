'use strict'

// $(document).ready(function(){
//   $('#search').on('input',function(e){
//       $.ajax({
//           type: "GET",
//           url: '/posts/auto_correct/',
//           data: {
//               'search_text': $('#search').val()
//           },
//           success: function(data){
//               $('#search-results').empty();
//               for (let item of data) {
//                   let listItem;
//                   if (item.type === 'user') {
//                       listItem = $('<li><i class="fas fa-user"></i> ' + item.value + '</li>');
//                   } else {
//                       listItem = $('<li><i class="fas fa-hashtag"></i> ' + item.value + '</li>');
//                   }
//                   listItem.click(function() {
//                       $('#search').val(item.value);  // Set the search bar's value to the clicked item's value
//                   });
//                   $('#search-results').append(listItem);
//               }
//           }
//       });
//   });
// });

'use strict'

'use strict'

$(document).ready(function(){
  $('#search').on('input',function(e){
      $.ajax({
          type: "GET",
          url: '/posts/auto_correct/',
          data: {
              'search_text': $('#search').val()
          },
          success: function(data){
              $('#search-results').empty();
              for (let item of data) {
                  let listItem;
                  if (item.type === 'hashtag') {
                      listItem = $('<li><i class="fas fa-hashtag"></i> ' + item.value + '</li>');
                      listItem.click(function() {
                          $('#search').val(item.value);  // Set the search bar's value to the clicked item's value
                          $('.search-bar').submit();  // Automatically submit the form when an item is clicked
                      });
                      $('#search-results').append(listItem);
                  }
              }
          }
      });
  });
});


